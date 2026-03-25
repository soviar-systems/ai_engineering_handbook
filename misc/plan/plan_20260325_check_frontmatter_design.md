# Design: check_frontmatter.py — Config-Driven Frontmatter Validator

## Overview

A hub-level frontmatter validation script that enforces ADR-26042 (Common
Frontmatter Standard) by reading the `.vadocs/` config chain and validating
all governed markdown files. Replaces frontmatter validation currently
duplicated across `check_adr.py` and `check_evidence.py`, and extends
coverage to all 10 document types defined in `conf.json`.

**Evidence:** [A-26015](/architecture/evidence/analyses/A-26015_frontmatter_validator_architecture.md)
(Approach C — config-driven module with CLI, WRC 0.90).

## Architecture

### Role: full frontmatter ownership

`check_frontmatter.py` owns all frontmatter validation: field presence, format,
and allowed values — for both hub-level rules (blocks, field registry) and
spoke-level rules (type-specific required fields, statuses, severity).

Domain scripts (`check_adr.py`, `check_evidence.py`) retain:

| Concern | Owner |
|---|---|
| Structural: sections, section order, conditional sections | domain scripts |
| Naming: filename patterns, ID format | domain scripts |
| Index: generation, glossary, sectioning | `check_adr.py` |
| Auto-fix: `status_corrections` | `check_adr.py` |

### Dual interface: importable module + CLI

**Module interface** — domain scripts import and delegate:

```python
from tools.scripts.check_frontmatter import (
    validate_frontmatter,
    parse_frontmatter,
    load_config_chain,
)
```

**CLI interface** — pre-commit hook and manual runs:

```
uv run tools/scripts/check_frontmatter.py [PATHS...] [--format {md,ipynb}]
```

## Input Modes

Three modes determined by arguments:

| Arguments | Behavior |
|---|---|
| None | Scan entire repo — walk from repo root, respecting exclusions |
| File path(s) | Validate each file directly |
| Directory path(s) | Scan directory recursively, respecting exclusions |

Mixed file and directory arguments are allowed in a single invocation.

### `--format` flag

- `md` (default) — glob for `*.md` files when scanning directories/repo
- `ipynb` — glob for `*.ipynb` files when scanning directories/repo

When validating explicit file paths, the flag is ignored (extension comes from
the path itself).

**ipynb parsing:** `.ipynb` files are JSON. Frontmatter lives in the first
markdown cell as YAML between `---` fences (Jupytext convention — same as `.md`
pairs). `parse_frontmatter` detects the file extension: for `.md` files, parse
directly; for `.ipynb`, extract the first markdown cell's source text, then
parse YAML fences from that.

### Directory exclusion

Reuse `VALIDATION_EXCLUDE_DIRS` from `tools/scripts/paths.py`. Directories
matching this set are skipped during recursive scans. This constant is the
existing SSoT for excluded directories and is already used by other validation
scripts.

## Validation Pipeline

For each file:

```
1. Read file content
2. Parse YAML frontmatter → raw dict (or skip: no frontmatter)
3. Read options.type → determine document type
   - Missing options.type with frontmatter present → WARNING (not error)
   - Missing options.type without frontmatter → skip silently
   - Unrecognized options.type → ERROR
4. Load hub config (conf.json) — cached per run
5. Resolve block composition for this type → required fields from blocks
6. Load spoke config if it exists (.vadocs/types/<type>.conf.json) — cached
7. Merge required fields from three sources (see Config Merge Semantics below)
8. Validate:
   a. Required field presence (merged required set)
   b. Date format (date, birth fields against hub date_format regex)
   c. Tags against hub tag vocabulary
   d. Status against spoke allowed statuses (if spoke defines them)
   e. Severity against spoke allowed values (if spoke defines them)
   f. Authors format: list of {name, email} objects (hub field_registry)
   g. Non-myst_native fields not under options.* → WARNING (not error)
      # Promote to error after Phase 1.15 migration restructures frontmatter.
      # Until then, existing files have id/status/produces etc. at top level.
```

### Config merge semantics

Required fields come from three sources. The merge rule is **union** (additive
inheritance, per ADR-26042):

```
required = union(
    hub_block_fields,       # conf.json → blocks → expand field names for this type's blocks
    hub_type_required,      # conf.json → types.<type>.required (e.g. ["id", "status"])
    spoke_required_fields,  # <type>.conf.json → required_fields (e.g. ["id", "title", "date", "status", "tags"])
)
```

Overlaps are harmless — union deduplicates. The spoke's `required_fields` may
repeat fields already in hub blocks or hub type required; this is by design
(spokes are self-contained operational configs that predate the hub type system).

For field lookup during validation, the search order is:
1. Top-level frontmatter key (e.g., `title`, `date`, `tags`)
2. `options.<field>` (e.g., `options.type`, `options.birth`)

A field is "present" if found at either level. This accommodates the current
pre-migration state where non-myst_native fields like `id` and `status` are
still at top level.

### Type discovery

The file's `options.type` field is the sole type discriminator. No directory
mapping needed — files are self-describing. This field is read from the parsed
frontmatter dict before type-specific validation begins.

Types without a spoke config (tutorial, guide, policy, package_spec,
script_instruction, service) are validated against hub rules only — block
composition and field registry. This still covers identity, discovery, and
lifecycle blocks.

### Config chain loading

```python
def load_config_chain(repo_root: Path, doc_type: str | None = None
                      ) -> tuple[dict, dict | None]:
    """Load hub config and optional spoke config.

    Uses paths.get_config_path() for discovery.
    Returns (hub_config, spoke_config_or_None).
    """
```

Both configs are cached after first load (module-level dict keyed by doc_type).
In tests, the cache is cleared or monkeypatched.

## Error Reporting

### FrontmatterError dataclass

```python
@dataclass
class FrontmatterError:
    file_path: Path
    error_type: str      # e.g. "missing_field", "invalid_value", "invalid_format"
    field: str | None     # which field failed (None for file-level errors)
    message: str          # agent-friendly: what's wrong + what would fix it
    config_source: str    # which config defines the rule
```

### Agent-friendly message format

Every error message includes:

1. **File path** — absolute or repo-relative
2. **Field name** — which frontmatter field
3. **Expected** — what the config requires (allowed values, format, type)
4. **Actual** — what was found (or "missing")
5. **Config source** — which config file defines the rule

Example:

```
architecture/adr/adr_26038.md: field 'status' has value 'draft'
  expected: one of [proposed, accepted, rejected, superseded, deprecated]
  defined in: .vadocs/types/adr.conf.json → statuses
```

```
ai_system/3_prompts/some_doc.md: missing required field 'description'
  required by: block 'discovery' for type 'guide'
  defined in: .vadocs/conf.json → blocks.discovery
```

### Warnings

Files with YAML frontmatter but no `options.type` produce a warning (printed
to stderr), not an error. These do not affect the exit code. This serves as a
migration progress indicator — warnings clear as `options.type` gets added to
governed files in Phase 1.15.

### Exit codes

- `0` — all validated files pass (warnings may still be printed)
- `1` — one or more validation errors found

## Module API

### Public functions

```python
def parse_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown/notebook content.

    Returns parsed dict, or None if no frontmatter found.
    """

def resolve_type(frontmatter: dict) -> str | None:
    """Read options.type from parsed frontmatter.

    Returns type string, or None if not present.
    """

def load_config_chain(repo_root: Path, doc_type: str | None = None
                      ) -> tuple[dict, dict | None]:
    """Load hub config and optional spoke config for a document type.

    Uses paths.get_config_path() for config discovery.
    Returns (hub_config, spoke_config_or_None).
    Configs are cached per doc_type after first load.
    """

def validate_frontmatter(file_path: Path, repo_root: Path
                         ) -> list[FrontmatterError]:
    """Validate a single file's frontmatter against hub + spoke rules.

    Orchestrates: read file → parse → resolve type → load configs → check all rules.
    Returns empty list if valid or if file has no frontmatter.
    """

def validate_parsed_frontmatter(frontmatter: dict, file_path: Path,
                                repo_root: Path) -> list[FrontmatterError]:
    """Validate already-parsed frontmatter dict against hub + spoke rules.

    For use by domain scripts that have already parsed frontmatter.
    Skips file reading and parsing — starts from resolve type.
    """

def scan_paths(paths: list[Path], repo_root: Path, fmt: str = "md"
               ) -> list[Path]:
    """Resolve input paths to file list.

    Files are returned as-is. Directories are walked recursively,
    filtered by format extension and VALIDATION_EXCLUDE_DIRS.
    """

def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Parse args, scan, validate, report, return exit code.

    When no args provided, resolves to [repo_root] for full-repo scan.
    """
```

### Internal helpers

```python
def _get_required_fields(doc_type: str, hub_config: dict,
                         spoke_config: dict | None) -> set[str]:
    """Merge hub block fields + spoke required_fields for a type."""

def _validate_field_value(field: str, value: Any, hub_config: dict,
                          spoke_config: dict | None) -> FrontmatterError | None:
    """Check a single field's value against config rules."""

def _check_options_namespace(frontmatter: dict, hub_config: dict
                             ) -> list[FrontmatterError]:
    """Warn when non-myst_native fields are not under options.*

    Returns warnings (not errors) until Phase 1.15 migration.
    """
```

## Script structure

Following the project convention (top-down design):

```
docstring (contract)
imports
dataclasses (FrontmatterError)
configuration (module-level config loading, cache)
main()
scan_paths()
validate_frontmatter()
_get_required_fields()
_validate_field_value()
_check_options_namespace()
parse_frontmatter()
resolve_type()
load_config_chain()
if __name__ == "__main__"
```

## Test strategy

TDD — tests first, then implementation.

### Test file

`tools/tests/test_check_frontmatter.py`

### Fixtures

- `frontmatter_env` — isolated temp directory with `.vadocs/conf.json`,
  `.vadocs/types/adr.conf.json`, `.vadocs/types/evidence.conf.json` copied from
  real configs (SSoT). Monkeypatches module-level config constants.

### Test classes (contracts)

| Class | Contract |
|---|---|
| `TestParseFrontmatter` | Extracts YAML dict from markdown; returns None when absent |
| `TestResolveType` | Reads `options.type`; returns None when missing |
| `TestLoadConfigChain` | Loads hub; loads hub+spoke for known types; returns None spoke for unknown types |
| `TestGetRequiredFields` | Merges block fields + spoke fields correctly; handles types without spoke |
| `TestValidateFieldPresence` | Detects missing required fields; passes when all present |
| `TestValidateDateFormat` | Accepts YYYY-MM-DD; rejects other formats |
| `TestValidateTags` | Accepts known tags; rejects unknown; handles empty |
| `TestValidateStatus` | Accepts spoke-defined statuses; rejects invalid |
| `TestValidateAuthors` | Accepts list of {name, email}; rejects malformed |
| `TestOptionsNamespace` | Non-myst_native fields not under options.* produce warnings (not errors) |
| `TestWarningNoType` | Files with frontmatter but no options.type produce warning |
| `TestScanPaths` | File args returned as-is; directories walked with exclusions; format filter applied |
| `TestMainExitCodes` | Exit 0 on valid; exit 1 on errors; warnings don't affect exit code |
| `TestErrorMessages` | FrontmatterError dataclass fields (file_path, error_type, field, config_source) are populated — test structure, not message wording |

### Test patterns

- Config-driven: import real configs, derive test data from them
- Semantic assertions: test error types and field names, not exact message strings
- Monkeypatching for isolation (module-level config cache)
- Parametrize across document types from hub config `types` registry

## Pre-commit hooks

```yaml
- id: check-frontmatter
  name: Validate frontmatter (ADR-26042)
  entry: uv run --active python -m tools.scripts.check_frontmatter
  language: system
  pass_filenames: true
  files: \.md$
  stages: [pre-commit, manual]

- id: test-check-frontmatter
  name: Test check_frontmatter
  entry: uv run --active pytest tools/tests/test_check_frontmatter.py
  language: system
  pass_filenames: false
  files: ^(tools/scripts/(check_frontmatter|git|paths)\.py|tools/tests/test_check_frontmatter\.py|\.vadocs/(conf\.json|types/(adr|evidence)\.conf\.json))$
```

Pre-commit passes changed `.md` files as arguments (file path mode). The hook
validates only changed files, not the entire repo. The test hook runs when the
script, its tests, shared modules, or config files change.

## Migration path

### Phase 1: Standalone (this design)

`check_frontmatter.py` runs as its own pre-commit hook. Domain scripts continue
their own frontmatter validation unchanged. Temporary double-validation is
acceptable — errors should be identical since both read the same configs.

### Phase 2: Domain script delegation

`check_adr.py` and `check_evidence.py` import `validate_parsed_frontmatter()`
and remove their own frontmatter validation code. This is done incrementally,
one script at a time. Also consolidates `FRONTMATTER_PATTERN` regex and
`parse_frontmatter()` — domain scripts import from `check_frontmatter` instead
of maintaining their own copies.

### Phase 3: vadocs extraction (Phase 1.3 of roadmap)

Module boundary maps to `vadocs.core`:
- `parse_frontmatter()` → `vadocs.core.parse_frontmatter()`
- `validate_frontmatter()` → `vadocs.core.validate_frontmatter()`
- `load_config_chain()` → `vadocs.core.load_config()`
- CLI → `vadocs docs check-frontmatter`

## Dependencies

- `tomllib` (stdlib) — pyproject.toml parsing via `paths.py`
- `json` (stdlib) — config loading
- `yaml` (PyYAML) — frontmatter parsing
- `pathlib` (stdlib) — all path operations
- `tools/scripts/paths.py` — `get_config_path()`, `VALIDATION_EXCLUDE_DIRS`
- `tools/scripts/git.py` — `detect_repo_root()`

## Implementation Results

- **67 tests**: 66 passed, 1 skipped (spoke-only field fallback — no such field exists in current config)
- **97% coverage**: uncovered L396-400 (`_find_field_block` hub types.required fallback, config-dependent), L675 (`__main__`)
- **Design gap found**: severity validation (L496-503) is unreachable — `load_config_chain("retrospective")` finds no `retrospective.conf.json`; severity rules live inside `evidence.conf.json` under `artifact_types.retrospective`. Marked `pragma: no cover`. Fix: Phase 2 config chain enhancement mapping sub-types to parent spokes.
- **Integration test**: ADRs produce warnings only (no `options.type` yet), evidence analyses with `options.type` validated correctly, real errors found (missing `authors`, `token_size` in older analyses)

## Implementation Steps

TDD throughout: write tests → run (red) → implement → run (green) → refactor.

### Step 1: Scaffold and infrastructure ✓

Create `tools/scripts/check_frontmatter.py` with contract docstring, imports,
`FrontmatterError` dataclass, and empty function signatures. Create
`tools/tests/test_check_frontmatter.py` with contract docstring, fixture
skeleton (`frontmatter_env`), and empty test classes.

**Verify:** both files import without error.

### Step 2: Config loading (TDD) ✓

### Step 3: Frontmatter parsing (TDD) ✓

### Step 4: Type resolution (TDD) ✓

### Step 5: Required fields merge (TDD) ✓

### Step 6: Field validation (TDD) ✓

### Step 7: Orchestration (TDD) ✓

### Step 8: File scanning (TDD) ✓

### Step 9: CLI and error reporting (TDD) ✓

### Step 10: Integration test against real repo ✓

### Step 11: Pre-commit hook ✓

### Step 12: Commit

## Out of scope

- `--fix` mode (deferred to Phase 1.15)
- Migration of `VALIDATION_EXCLUDE_DIRS` to `.vadocs/validation/excludes.conf.json`
- Refactoring domain scripts to delegate (Phase 2 of migration)
- JSON Schema validation of config files themselves
- Script instruction doc in `tools/docs/scripts_instructions/` — TD-004 recommends
  relaxing the triad to dyad; contract docstring in the script is sufficient
