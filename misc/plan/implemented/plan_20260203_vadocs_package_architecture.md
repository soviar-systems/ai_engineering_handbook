# Critical Analysis: vadocs Package Architecture

## Executive Summary

After reviewing the existing vadocs plans, ADR-26012, current scripts, and infrastructure, I've identified significant **scope ambiguity** and **architectural gaps** that need resolution before proceeding. This analysis examines whether vadocs can achieve its goals while preserving all current functionality.

---

## Current State Assessment

### vadocs Package (packages/vadocs/)
- **Version**: 0.1.0 (Alpha, library-only)
- **Features**: Document model, basic parsing, validator/fixer base classes
- **Tests**: 26 passing (core models + parsing)
- **Missing**: CLI, config loading, index parsing, most validation logic

### tools/scripts/ (What Must Be Preserved)
| Script | Lines | Complexity | Notes |
|--------|-------|------------|-------|
| check_adr.py | 1260 | High | Full ADR ecosystem |
| check_broken_links.py | ~300 | Medium | Link validation |
| jupytext_sync.py | ~200 | Medium | Notebook sync |
| check_api_keys.py | ~150 | Low | Secret detection |
| check_link_format.py | ~100 | Low | Format validation |
| check_json_files.py | ~80 | Low | JSON validation |
| check_script_suite.py | ~200 | Medium | Workflow enforcement |

### Integration Points
- Pre-commit hooks (11 local hooks)
- CI/CD (9 parallel jobs in quality.yml)
- ADR documentation (20 ADRs)
- 1:1:1 script:test:doc ratio enforcement

---

## Critical Issues Identified

### Issue 1: Competing Visions

**vadocs plan** focuses on ADR validation + bi-directional sync.

**ADR-26012** proposes `docs-validation-engine` covering ALL scripts.

These are fundamentally different scopes:
- vadocs v0.1.0: ~500 lines of focused ADR logic
- Full extraction: ~2500+ lines across all validators

**Question**: Which vision should we pursue?

### Issue 2: Functionality Gap

check_adr.py has extensive logic not yet in vadocs:

```
Missing in vadocs:
├── Index parsing (glossary blocks, sections)
├── Duplicate detection
├── Status → Section mapping
├── Status corrections (typo handling)
├── Date format validation
├── Tag validation
├── Section validation
├── Title mismatch detection
├── Term reference validation
├── Legacy ADR migration
├── Full --fix workflow
└── --check-staged mode (pre-commit)
```

**Current state**: vadocs has ~20% of check_adr.py functionality.

### Issue 3: Configuration Complexity

Current check_adr.py loads config at module level:
```python
_config = load_adr_config()  # From adr_config.yaml
VALID_STATUSES = set(_config.get("statuses", []))
STATUS_SECTIONS = _build_status_sections(_config)
# ... 10+ derived constants
```

For reusability across repos, vadocs needs:
1. Config schema definition
2. Multiple config sources (pyproject.toml, YAML, passed-in)
3. Defaults for repos without custom config

### Issue 4: Pre-commit Integration

Scripts return exit codes and accept specific arguments:
```bash
uv run tools/scripts/check_adr.py --fix
uv run tools/scripts/check_broken_links.py --verbose
uv run tools/scripts/jupytext_sync.py file1.md file2.ipynb
```

If vadocs provides these, it must:
- Support identical CLI interfaces
- Return identical exit codes
- Handle file patterns identically

### Issue 5: Testing Standards

ADR-26011 mandates 1:1:1 ratio for scripts. For a package:
- Package has its own test suite
- Thin wrappers in tools/scripts/ need tests
- Consuming repos need integration tests

This is 3x testing complexity, not 1x.

---

## Architecture Options

### Option A: Focused ADR Engine (Current vadocs Direction)

**Scope**: ADR validation + sync only

**Structure**:
```
vadocs/
├── validators/adr.py     # Full ADR validation
├── fixers/adr_fixer.py   # Full fix capabilities
├── fixers/sync_fixer.py  # Bi-directional sync
└── core/parsing.py       # ADR-specific parsing
```

**Integration**:
- tools/scripts/check_adr.py becomes thin wrapper importing vadocs
- Other scripts remain unchanged
- Other repos can use vadocs for ADR validation

**Pros**:
- Focused scope
- Easier to complete
- Less testing complexity
- Can ship v1.0 sooner

**Cons**:
- Doesn't address ADR-26012 vision
- Other scripts still need manual copy
- Limited reusability

### Option B: Full Docs Validation Engine (ADR-26012 Vision)

**Scope**: All validation scripts as plugins

**Structure**:
```
vadocs/
├── validators/
│   ├── adr.py
│   ├── broken_links.py
│   ├── link_format.py
│   ├── jupytext.py
│   ├── api_keys.py
│   └── json_files.py
├── fixers/
│   ├── adr_fixer.py
│   ├── jupytext_fixer.py
│   └── api_keys_fixer.py
├── cli/main.py           # Unified CLI
└── config/loader.py      # pyproject.toml loader
```

**Integration**:
- All tools/scripts/*.py become thin wrappers
- Pre-commit uses vadocs entry points
- Other repos install vadocs + configure

**Pros**:
- Single source of truth for all validation
- Full ADR-26012 compliance
- Maximum reusability
- Community potential

**Cons**:
- Large scope (2500+ lines)
- Complex migration
- Higher risk
- Longer timeline

### Option C: Incremental Extraction (Recommended)

**Strategy**: Start with Option A, evolve toward Option B.

**Phase 1 (v0.1.0)**: ADR validation library
- Complete current vadocs with full check_adr.py logic
- No CLI (library only)
- check_adr.py imports vadocs internally
- Tests in both vadocs and tools/tests/

**Phase 2 (v0.2.0)**: Add CLI + config loading
- vadocs CLI entry point
- pyproject.toml configuration
- check_adr.py becomes true thin wrapper

**Phase 3 (v0.3.0+)**: Extract additional validators
- broken_links
- link_format
- jupytext (may need separate package due to jupytext dependency)

**Phase 4 (v1.0.0)**: PyPI release
- Entry point plugins
- Full documentation
- Stable API guarantee

---

## Key Design Decisions Required

### 1. Configuration Strategy

**Option 1a**: Config passed at runtime (current vadocs approach)
```python
validator = AdrValidator()
errors = validator.validate(doc, config)  # Config passed in
```

**Option 1b**: Config loaded from pyproject.toml
```python
validator = AdrValidator.from_project()  # Loads [tool.vadocs]
errors = validator.validate(doc)
```

**Option 1c**: Both (recommended)
```python
# Library use: pass config
validator = AdrValidator(config)

# CLI use: auto-load
validator = AdrValidator.auto_configure()
```

### 2. CLI Architecture

**Option 2a**: Subcommands per validator
```bash
vadocs adr validate
vadocs adr fix
vadocs links check
```

**Option 2b**: Unified with type detection
```bash
vadocs validate path/to/file.md  # Auto-detects ADR
vadocs fix --type adr
```

**Option 2c**: Separate entry points (ADR-26012 style)
```bash
vadocs-adr --fix
vadocs-links --verbose
```

### 3. Thin Wrapper Pattern

**Option 3a**: Wrapper imports vadocs and runs
```python
# tools/scripts/check_adr.py
from vadocs import AdrValidator, AdrFixer
from vadocs.config import load_local_config

config = load_local_config("architecture/adr/adr_config.yaml")
validator = AdrValidator(config)
# ... CLI logic stays here
```

**Option 3b**: Wrapper just calls vadocs CLI
```python
# tools/scripts/check_adr.py
from vadocs.cli import run_adr
sys.exit(run_adr(sys.argv[1:]))
```

**Recommendation**: Option 3a gives more control, Option 3b is simpler.

### 4. Error Reporting Format

Current check_adr.py output:
```
architecture/adr_index.md is out of sync with ADR files:
  - ADR 26001 missing required field: 'tags'
  - ADR 26002 has invalid status: 'Proposed'
```

Should vadocs standardize output format?
- Same format (backward compatible)
- Structured format (JSON/YAML for CI)
- Configurable format

---

## Feasibility Assessment

**Is it possible to achieve the goals?**

Yes, but with caveats:

1. **Preserving functionality**: ✅ Achievable
   - All check_adr.py logic can move to vadocs
   - Thin wrapper maintains CLI compatibility
   - Pre-commit integration unchanged

2. **Making it reusable**: ✅ Achievable with effort
   - Requires configuration layer
   - Requires abstraction of repo-specific paths
   - Must handle different ADR conventions

3. **Maintaining test standards**: ⚠️ Increases complexity
   - vadocs needs its own comprehensive tests
   - tools/scripts/ wrappers need integration tests
   - Testing effort approximately doubles

4. **Maintaining doc standards**: ⚠️ Changes required
   - vadocs has README.md (done)
   - ADR-26020 documents internal package pattern (pending)
   - tools/docs/ for thin wrapper instructions

5. **Enabling additional features**: ✅ Achievable
   - Plugin architecture supports extensions
   - Entry points allow third-party validators

---

## Recommended Path Forward

### Immediate Actions (This Session)

1. **Decide on scope**: Option A, B, or C?
2. **Decide on configuration**: How should vadocs load config?
3. **Decide on thin wrapper pattern**: How much logic in wrapper?
4. **Decide on error format**: Backward compatible or improved?

### Phase 1 Implementation (v0.1.0)

1. Complete vadocs core with full check_adr.py validation logic
2. Add comprehensive tests mirroring test_check_adr.py
3. Document configuration requirements
4. Keep check_adr.py working with vadocs as internal import

### Future Phases

- v0.2.0: CLI, pyproject.toml config
- v0.3.0: Additional validators (if Option B/C)
- v1.0.0: PyPI release, stable API

---

## Decisions Made

1. **Scope**: Option C - Incremental (start focused, evolve toward full engine)
2. **First Feature**: YAML frontmatter validation (test the concept)
3. **Integration**: Agile - validate concept before full migration

---

## Configuration Architecture Proposal

Based on your concerns (pre-commit compatibility, no duplication, reusability), here's the proposed design:

### Configuration Hierarchy (Priority Order)

```
1. Explicit config dict (passed to validator)     ← Library use, testing
2. --config flag path                             ← CLI use, pre-commit
3. [tool.vadocs] in pyproject.toml                 ← Standard Python pattern
4. Default config file (vadocs.yaml, adr_config.yaml) ← Repo convention
5. Built-in defaults                              ← Works out of box
```

### Config Loading Strategy

```python
class ConfigLoader:
    """Find and load configuration from multiple sources."""

    def load(
        self,
        explicit_config: dict | None = None,
        config_path: Path | None = None,
        project_root: Path | None = None,
    ) -> Config:
        # Priority 1: Explicit config (testing, library use)
        if explicit_config:
            return Config.from_dict(explicit_config)

        # Find project root if not provided
        if project_root is None:
            project_root = self._find_project_root()

        # Priority 2: Explicit config path (CLI --config flag)
        if config_path:
            return self._load_file(config_path)

        # Priority 3: pyproject.toml [tool.vadocs]
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            config = self._load_pyproject(pyproject)
            if config:
                return config

        # Priority 4: Default config files
        for name in ["vadocs.yaml", "adr_config.yaml"]:
            path = project_root / name
            if path.exists():
                return self._load_file(path)

        # Priority 5: Built-in defaults
        return Config.defaults()

    def _find_project_root(self) -> Path:
        """Find project root by looking for markers."""
        markers = ["pyproject.toml", ".git", "setup.py"]
        # Walk up from CWD until marker found
        ...
```

### Pre-commit Compatibility

Pre-commit hooks run from repo root, so CWD is predictable. But to be safe:

```yaml
# .pre-commit-config.yaml
- id: vadocs-frontmatter
  entry: uv run python -m vadocs validate --type frontmatter
  args: ["--config", "architecture/adr/adr_config.yaml"]  # Explicit path
```

vadocs resolves paths relative to project root, not CWD:
```python
def _resolve_path(self, path: str, project_root: Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return project_root / p
```

### No Duplication - Configuration Unification

**Current Duplication Problem**:
```
paths.py:
  BROKEN_LINKS_EXCLUDE_DIRS = {".git", ".venv", "node_modules", ...}
  JUPYTEXT_EXCLUDE_DIRS = BROKEN_LINKS_EXCLUDE_DIRS  # Same!
  API_KEYS_EXCLUDE_FILES = {...}

adr_config.yaml:
  statuses: [proposed, accepted, ...]
  required_fields: [id, title, ...]

myst.yml:
  # MyST-specific config
```

**Solution: pyproject.toml as Single Source of Truth**

pyproject.toml is the natural choice because:
- Already defines uv, jupytext, pytest config
- Standard Python pattern ([tool.X] sections)
- vadocs users already have it

**Proposed Structure**:
```toml
[tool.vadocs]
# Global exclusions (used by all validators)
exclude_dirs = [".git", ".venv", "node_modules", "__pycache__", "build", "dist", "misc"]
exclude_files = [".aider.chat.history.md"]

[tool.vadocs.adr]
# ADR-specific config
config_file = "architecture/adr/adr_config.yaml"  # Or inline:
# statuses = ["proposed", "accepted", "deprecated", "superseded"]
# required_fields = ["id", "title", "date", "status", "tags"]
# ...

[tool.vadocs.links]
# Link validation config
exclude_link_strings = ["example.com", "placeholder"]

[tool.vadocs.api_keys]
# API key scanning config
placeholder_indicators = ["[", "<", "${", "{{", "example", "placeholder"]
```

**Migration Path**:

**Phase 1 (v0.1.0)**: Hybrid approach
- vadocs reads [tool.vadocs] from pyproject.toml
- adr_config.yaml remains SSoT for ADR-specific rules
- paths.py stays but is marked as deprecated

**Phase 2 (v0.2.0)**: Full migration
- Move paths.py content to [tool.vadocs] in pyproject.toml
- Update all scripts to read from pyproject.toml via vadocs
- paths.py becomes a thin compatibility layer

**Phase 3 (v0.3.0)**: Consolidation
- adr_config.yaml content optionally moves to [tool.vadocs.adr]
- Or stays as reference: `config_file = "architecture/adr/adr_config.yaml"`
- Remove paths.py compatibility layer

**Note**: myst.yml stays separate - it's MyST's config, not vadocs's

### Reusability - Schema with Defaults

```python
@dataclass
class FrontmatterConfig:
    """Configuration for frontmatter validation."""
    required_fields: list[str] = field(default_factory=lambda: ["id", "title", "date", "status"])
    optional_fields: list[str] = field(default_factory=lambda: ["tags", "superseded_by"])
    valid_statuses: set[str] = field(default_factory=lambda: {"proposed", "accepted", "deprecated", "superseded"})
    date_format: str = r"^\d{4}-\d{2}-\d{2}$"
    valid_tags: set[str] | None = None  # None = any tags allowed

    @classmethod
    def from_dict(cls, d: dict) -> "FrontmatterConfig":
        return cls(
            required_fields=d.get("required_fields", cls.required_fields),
            valid_statuses=set(d.get("statuses", cls.valid_statuses)),
            # ... merge with defaults
        )
```

Different repos override only what they need:
```yaml
# Repo A: Strict ADR convention
required_fields: [id, title, date, status, tags]
valid_tags: [architecture, security, testing]

# Repo B: Minimal convention
required_fields: [title, status]
# Uses defaults for everything else
```

---

## Proposed v0.1.0 Scope (Minimal Viable Package)

### What to Build

1. **FrontmatterValidator** - Complete YAML frontmatter validation
   - Required fields check
   - Valid status check
   - Date format check
   - Tag validation (optional)

2. **ConfigLoader** - Find and merge configuration
   - Explicit config support
   - Config file loading
   - Sensible defaults

3. **Core Models** (already done)
   - Document, ValidationError

### What NOT to Build (Yet)

- CLI (library-only in v0.1.0)
- Fixers (validation only)
- Index sync validation
- Term reference validation
- pyproject.toml support (defer to v0.2.0)

### Integration Pattern

```python
# tools/scripts/check_adr.py (modified)
from vadocs import FrontmatterValidator
from vadocs.config import ConfigLoader

def validate_frontmatter_via_vadocs(adr_file: AdrFile) -> list[ValidationError]:
    """Use vadocs for frontmatter validation."""
    loader = ConfigLoader()
    config = loader.load(config_path=ADR_CONFIG_PATH)

    validator = FrontmatterValidator(config.frontmatter)
    doc = Document(
        path=adr_file.path,
        content=adr_file.content,
        frontmatter=adr_file.frontmatter,
        doc_type="adr"
    )
    return validator.validate(doc)
```

check_adr.py keeps all its existing logic but delegates frontmatter validation to vadocs. If vadocs works well, we gradually migrate more.

---

## Test Strategy for Concept Validation

### vadocs Package Tests (packages/vadocs/tests/)

```python
class TestFrontmatterValidator:
    """Validate FrontmatterValidator contract."""

    def test_missing_required_field_returns_error(self):
        """Missing required field produces ValidationError."""
        config = FrontmatterConfig(required_fields=["id", "title"])
        doc = Document(frontmatter={"id": 1})  # Missing title

        errors = FrontmatterValidator(config).validate(doc)

        assert len(errors) == 1
        assert errors[0].error_type == "missing_field"

    def test_invalid_status_returns_error(self):
        """Status not in valid_statuses produces error."""
        ...

    def test_valid_document_returns_no_errors(self):
        """Fully valid document passes validation."""
        ...
```

### Integration Test (tools/tests/test_check_adr.py)

```python
def test_vadocs_integration():
    """Verify vadocs produces same results as native implementation."""
    adr_files = get_adr_files()

    for adr in adr_files:
        native_errors = validate_frontmatter_fields(adr)  # Current impl
        vadocs_errors = validate_frontmatter_via_vadocs(adr)  # vadocs impl

        # Same error count and types
        assert len(native_errors) == len(vadocs_errors)
        assert {e.error_type for e in native_errors} == {e.error_type for e in vadocs_errors}
```

---

## Success Criteria for Concept Validation

Before expanding vadocs scope, these must be true:

1. ✓ FrontmatterValidator passes all unit tests
2. ✓ Integration test shows parity with native implementation
3. ✓ check_adr.py works with vadocs for frontmatter validation
4. ✓ Pre-commit hook passes
5. ✓ CI passes
6. ✓ Config loading works from adr_config.yaml

If any fail, we identify the issue and fix before adding more features.

---

## Implementation Roadmap

### Phase 0: Standalone Repo Setup

**Goal**: Create vadocs as an independent, installable package.

**New Repository**: `github.com/<username>/vadocs`

**Repository Structure**:
```
vadocs/                      # Standalone repo
├── .github/
│   └── workflows/
│       ├── tests.yml       # Run tests on push/PR
│       └── publish.yml     # Publish to PyPI on tag
├── pyproject.toml          # Package metadata, [tool.vadocs] schema
├── README.md
├── CHANGELOG.md
├── src/vadocs/
│   ├── __init__.py
│   ├── core/
│   │   ├── models.py       # Document, ValidationError, ValidationContext
│   │   └── parsing.py
│   ├── config/
│   │   ├── loader.py
│   │   └── models.py       # FrontmatterConfig, etc.
│   └── validators/
│       ├── base.py         # Validator ABC
│       └── frontmatter.py
└── tests/
```

**ai_engineering_book Integration**:
```toml
# ai_engineering_book/pyproject.toml
[project]
dependencies = [
    # During development: GitHub URL
    "vadocs @ git+https://github.com/<username>/vadocs.git@v0.1.0",
    # After PyPI publish:
    # "vadocs>=0.1.0",
]

[tool.vadocs]
# Config for this repo
exclude_dirs = [".git", ".venv", "node_modules"]

[tool.vadocs.adr]
config_file = "architecture/adr/adr_config.yaml"
```

### Phase 1: v0.1.0 - Frontmatter Validation (Concept Validation)

**Goal**: Prove vadocs architecture works AND installability before expanding scope.

**Files to Create in vadocs repo**:
```
vadocs/
├── src/vadocs/
│   ├── __init__.py         # Public API exports
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py       # Document, ValidationError, ValidationContext
│   │   └── parsing.py      # parse_frontmatter, extract_status
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py       # ConfigLoader class
│   │   └── models.py       # FrontmatterConfig dataclass
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base.py         # Validator ABC with scope declaration
│   │   └── frontmatter.py  # FrontmatterValidator
│   └── scaffold/
│       ├── __init__.py     # ProjectScaffold class
│       └── templates/      # Template files
│           └── adr/
│               ├── adr_config.yaml
│               ├── adr_template.md
│               ├── adr_00001_example.md
│               └── adr_index.md
└── tests/
    ├── conftest.py
    ├── core/
    │   ├── test_models.py
    │   └── test_parsing.py
    ├── config/
    │   └── test_loader.py
    ├── validators/
    │   └── test_frontmatter.py
    └── scaffold/
        └── test_init.py    # Test project initialization
```

**Files to Modify in ai_engineering_book**:
```
pyproject.toml              # Add vadocs dependency + [tool.vadocs]
tools/scripts/check_adr.py  # Import vadocs for frontmatter validation
tools/tests/test_check_adr.py  # Add integration test
```

**IMPORTANT: Non-destructive Integration**

When testing vadocs on the real repo:
- **DO NOT** overwrite `.pre-commit-config.yaml`
- **ADD** vadocs hooks alongside existing hooks (or test separately)
- **KEEP** existing `check_adr.py` working - just use vadocs internally
- **PRESERVE** all current functionality - vadocs augments, doesn't replace

Example safe integration:
```yaml
# .pre-commit-config.yaml - ADD these hooks, don't replace existing
repos:
  # ... existing hooks remain unchanged ...

  # New vadocs hooks (added, not replacing)
  - repo: local
    hooks:
      - id: vadocs-frontmatter
        name: "[vadocs] Validate frontmatter"
        entry: uv run python -c "from vadocs import ...; ..."
        language: system
        files: ^architecture/adr/adr_.*\.md$
        # Initially disabled until vadocs is proven
        stages: [manual]
```

**Implementation Steps**:

**Step 1: Create standalone vadocs repo**
```bash
mkdir vadocs && cd vadocs
git init
# Create structure, pyproject.toml, README.md
```

**Step 2: Define core models** (core/models.py)
- Document dataclass
- ValidationError dataclass
- ValidatorScope enum (SINGLE_FILE, FILE_SET, PROJECT)

**Step 3: Define config schema** (config/models.py)
- FrontmatterConfig dataclass with defaults
- Type hints and validation

**Step 4: Implement ConfigLoader** (config/loader.py)
- Load from explicit dict
- Load from YAML file path
- Load from pyproject.toml [tool.vadocs]
- Merge with defaults

**Step 5: Implement Validator base** (validators/base.py)
- Validator ABC with scope declaration
- ValidatorScope enum

**Step 6: Implement FrontmatterValidator** (validators/frontmatter.py)
- Accept FrontmatterConfig
- Validate required fields
- Validate status values
- Validate date format
- Validate tags (optional)

**Step 7: Write comprehensive tests**
- Config loading tests (test_loader.py)
- Validator behavior tests (test_frontmatter.py)
- Edge cases (missing frontmatter, empty fields, etc.)

**Step 8: Set up CI** (.github/workflows/tests.yml)
- Run tests on push/PR
- Python 3.11, 3.12, 3.13 matrix

**Step 9: Integrate with ai_engineering_book**
- Add vadocs as git dependency in pyproject.toml
- Add [tool.vadocs] section
- Modify check_adr.py to import vadocs for frontmatter validation
- Add integration test

**Step 10: Verify end-to-end**
- Run vadocs tests in vadocs repo
- Run check_adr.py --verbose in ai_engineering_book
- Verify pre-commit hooks still pass
- Verify CI still passes

### Phase 2: v0.2.0 - CLI + More Validators

- Add vadocs CLI entry point
- Add status validation
- Add date format validation
- Add tag validation
- Full pyproject.toml config support

### Phase 3: v0.3.0 - Index Sync + Fixers

- Index parsing (glossary blocks)
- Index sync validation
- AdrFixer implementation
- SyncFixer implementation

### Phase 4: v0.4.0+ - Additional Validators

- Term reference validation
- Broken links validator
- Link format validator
- Consider jupytext integration

### Phase 5: v1.0.0 - Production Release

- Stable API guarantee
- PyPI publishing
- Entry point plugins
- Full documentation

---

## Verification Plan

### After v0.1.0 Implementation

1. **Unit tests pass**:
   ```bash
   cd packages/vadocs && uv run pytest tests/ -v
   ```

2. **Integration test passes**:
   ```bash
   uv run pytest tools/tests/test_check_adr.py -v -k vadocs
   ```

3. **check_adr.py works**:
   ```bash
   uv run tools/scripts/check_adr.py --verbose
   ```

4. **Pre-commit passes**:
   ```bash
   uv run pre-commit run check-adr-index --all-files
   ```

5. **CI passes**: Push branch and verify GitHub Actions

### Success Metrics

- vadocs unit test coverage ≥ 90%
- Zero regressions in check_adr.py behavior
- Pre-commit execution time unchanged (±10%)
- CI execution time unchanged (±10%)

---

## Critical Files Summary

### To Create
- `packages/vadocs/src/vadocs/config/__init__.py`
- `packages/vadocs/src/vadocs/config/loader.py`
- `packages/vadocs/src/vadocs/config/models.py`
- `packages/vadocs/tests/config/test_loader.py`

### To Modify
- `packages/vadocs/src/vadocs/__init__.py` - Export config module
- `packages/vadocs/src/vadocs/validators/frontmatter.py` - Enhanced validator
- `packages/vadocs/tests/validators/test_frontmatter.py` - More tests
- `pyproject.toml` - Add [tool.vadocs] section
- `tools/scripts/check_adr.py` - Integrate vadocs
- `tools/tests/test_check_adr.py` - Integration test

### To Preserve (SSoT)
- `architecture/adr/adr_config.yaml` - ADR rules (vadocs reads this)

### Future Deprecation
- `tools/scripts/paths.py` - Move content to [tool.vadocs] over time

---

## Architectural Solution: Scope-Based Validators (Pre-Commit Model)

### Research Findings

Analyzed how similar tools handle heterogeneous validation scopes:
- **Pre-commit**: Explicit scope declaration via `pass_filenames` flag
- **Pytest**: Fixture scopes (session, module, function)
- **Ruff/ESLint**: Hierarchical config with glob patterns
- **MkDocs**: Event-based hooks at different build stages

**Best fit for vadocs**: Pre-commit model (explicit scope declaration per validator)

### Recommended Architecture

```
┌─────────────────────────────────────────────────────┐
│  Validator Registry                                  │
│                                                     │
│  Each validator declares:                           │
│  - scope: SINGLE_FILE | FILE_SET | PROJECT          │
│  - file_pattern: glob to match (e.g., "*.md")       │
│  - pass_filenames: bool                             │
└─────────────────────────────────────────────────────┘
         │
         ├─────────────────┬─────────────────┬──────────────
         ▼                 ▼                 ▼
   SINGLE_FILE         FILE_SET          PROJECT
   (api_keys,          (adr_index,       (broken_links,
    frontmatter)        jupytext)         term_refs)
```

### Implementation

```python
from enum import Enum

class ValidatorScope(Enum):
    SINGLE_FILE = "single_file"   # Receives one file at a time
    FILE_SET = "file_set"         # Receives list of matched files
    PROJECT = "project"           # Receives project root, discovers files itself

class Validator(ABC):
    """Base validator with explicit scope declaration."""

    name: str
    scope: ValidatorScope = ValidatorScope.SINGLE_FILE
    file_pattern: str = "*.md"  # Glob pattern

    @abstractmethod
    def validate(self, context: ValidationContext, config: dict) -> list[ValidationError]:
        """Run validation. Context contents depend on scope."""

@dataclass
class ValidationContext:
    """Context provided to validators based on their scope."""
    project_root: Path

    # For SINGLE_FILE scope
    file: Path | None = None

    # For FILE_SET scope
    files: list[Path] = field(default_factory=list)

    # Cached resources (shared across validators)
    cache: dict = field(default_factory=dict)
```

### Scope Mapping for Validators

| Validator | Scope | file_pattern | Receives |
|-----------|-------|--------------|----------|
| Frontmatter | SINGLE_FILE | `*.md` | One file at a time |
| API Keys | SINGLE_FILE | `*` | One file at a time |
| ADR Index | FILE_SET | `architecture/adr/*.md` | List of ADR files |
| Jupytext | FILE_SET | `*.md, *.ipynb` | Paired files |
| Broken Links | PROJECT | `*.md` | Project root (self-discovers) |
| Term Refs | PROJECT | `*.md` | Project root (self-discovers) |

---

## How vadocs Works as a Pure Library

### Python Package Basics

A Python package is code that lives in one place (PyPI or GitHub) and gets installed into other projects:

```bash
# Install from PyPI (after publishing)
uv add vadocs

# Install from GitHub (during development)
uv add "vadocs @ git+https://github.com/username/vadocs.git"
```

After installation, the package code lives in your virtual environment (`.venv/lib/python3.x/site-packages/vadocs/`), NOT in your project directory. You just `import vadocs` and use it.

### Current Approach vs. vadocs Approach

**Current (tools/ directory)**:
```
ai_engineering_book/
├── tools/
│   ├── scripts/
│   │   ├── check_adr.py        # 1260 lines of validation logic
│   │   ├── check_broken_links.py
│   │   └── paths.py
│   └── tests/
│       ├── test_check_adr.py
│       └── test_check_broken_links.py
├── .pre-commit-config.yaml     # Calls tools/scripts/*.py
└── pyproject.toml
```
- All scripts live IN each project
- Copy scripts to new project → duplication
- Update script → must update in each project

**vadocs Approach (pure library)**:
```
ai_engineering_book/
├── .pre-commit-config.yaml     # Calls vadocs directly
└── pyproject.toml              # [tool.vadocs] config + vadocs dependency
```
- NO scripts in project directory
- All validation logic lives in vadocs package
- Update vadocs → all projects get the update

### User Experience

**1. Install vadocs**:
```bash
cd my-docs-project
uv add vadocs
```

**2. Configure in pyproject.toml**:
```toml
[project]
dependencies = ["vadocs>=0.1.0"]

[tool.vadocs]
exclude_dirs = [".git", ".venv", "node_modules"]

[tool.vadocs.adr]
config_file = "architecture/adr/adr_config.yaml"
# OR inline config:
statuses = ["proposed", "accepted", "deprecated", "superseded"]
required_fields = ["id", "title", "date", "status", "tags"]
```

**3. Set up pre-commit** (optional but recommended):
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: vadocs-frontmatter
        name: Validate frontmatter
        entry: uv run vadocs validate --type frontmatter
        language: system
        files: \.md$

      - id: vadocs-adr-index
        name: Validate ADR index
        entry: uv run vadocs validate --type adr-index
        language: system
        files: ^architecture/adr/
```

**4. Run validation**:
```bash
# Via CLI
uv run vadocs validate                    # Run all validators
uv run vadocs validate --type frontmatter # Run specific validator
uv run vadocs validate path/to/file.md    # Validate specific file

# Via pre-commit
uv run pre-commit run --all-files

# Via Python (for custom integration)
from vadocs import FrontmatterValidator, ConfigLoader

config = ConfigLoader().load()
validator = FrontmatterValidator(config.frontmatter)
errors = validator.validate(doc)
```

### Where's the Logic?

| Component | Current Location | vadocs Location |
|-----------|-----------------|----------------|
| Validation logic | `tools/scripts/check_adr.py` | `vadocs/validators/adr.py` (in package) |
| Tests | `tools/tests/test_check_adr.py` | `vadocs/tests/` (in package repo) |
| Configuration | `architecture/adr/adr_config.yaml` | `pyproject.toml [tool.vadocs]` OR YAML file |
| Pre-commit hooks | `.pre-commit-config.yaml` | `.pre-commit-config.yaml` (calls vadocs CLI) |

### Benefits

1. **Single Source of Truth**: Fix a bug once, all projects benefit
2. **Versioning**: Pin `vadocs==0.1.0` for stability, upgrade when ready
3. **Less Maintenance**: No scripts to maintain in each project
4. **Easier Onboarding**: `uv add vadocs` instead of copying 12 scripts + tests

### What About Custom Validation?

If a project needs custom validation beyond what vadocs provides:

**Option A**: Thin wrapper script (like current check_adr.py after migration)
```python
# tools/scripts/check_custom.py
from vadocs import FrontmatterValidator

# Use vadocs + add custom logic
validator = FrontmatterValidator(config)
errors = validator.validate(doc)

# Add project-specific checks
if doc.frontmatter.get("custom_field") is None:
    errors.append(...)
```

**Option B**: Custom validator class (future - plugin system)
```python
# .vadocs/custom/my_validator.py
from vadocs import Validator, ValidationContext

class MyCustomValidator(Validator):
    name = "my_custom"
    scope = ValidatorScope.SINGLE_FILE

    def validate(self, context, config):
        # Custom logic
        ...
```

---

## New Requirement: Project Scaffolding

### Capability

vadocs must be able to **initialize a new project** with recommended structure:

```bash
vadocs init                    # Initialize in current directory
vadocs init my-docs-project    # Initialize in new directory
vadocs init --template adr     # Initialize with ADR structure
```

### Generated Structure (ADR template)

```
my-docs-project/
├── pyproject.toml            # With [tool.vadocs] section
├── architecture/
│   ├── adr/
│   │   ├── adr_config.yaml   # ADR configuration
│   │   ├── adr_template.md   # Template for new ADRs
│   │   └── adr_00001_use_vadocs.md  # Example ADR
│   └── adr_index.md          # Auto-generated index
├── .pre-commit-config.yaml   # Pre-commit hooks using vadocs
└── README.md
```

### Templates

vadocs should support multiple templates:
- **adr**: Architecture Decision Records
- **docs**: General documentation with frontmatter
- **jupytext**: MyST notebooks with Jupytext pairing
- **full**: All of the above combined

### Implementation

```python
# vadocs/scaffold/__init__.py
class ProjectScaffold:
    """Initialize new documentation projects."""

    templates = ["adr", "docs", "jupytext", "full"]

    def init(self, path: Path, template: str = "adr") -> None:
        """Create project structure from template."""
        ...

    def add_component(self, path: Path, component: str) -> None:
        """Add component to existing project (e.g., add ADR to docs project)."""
        ...
```

### CLI

```bash
vadocs init [PATH] [--template TEMPLATE]
vadocs add adr                 # Add ADR structure to existing project
vadocs new adr "Title Here"    # Create new ADR from template
```

---

## Revised PoC Success Criteria

The PoC must validate:

1. ✅ **Installability**: vadocs can be installed as uv dependency
2. ✅ **Single-file validation**: FrontmatterValidator works
3. ✅ **Scope architecture**: Design supports SINGLE_FILE, FILE_SET, PROJECT
4. ✅ **Project init**: `vadocs init --template adr` creates correct structure
5. ✅ **Config loading**: Reads [tool.vadocs] from pyproject.toml
6. ✅ **Integration**: check_adr.py can use vadocs for frontmatter validation

---

## Revised Architectural Requirements

The vadocs architecture must:

1. **Support single-document validation** (frontmatter, api_keys)
2. **Support multi-document validation** (ADR index sync)
3. **Support project-wide scanning** (broken_links)
4. **Support paired files** (jupytext sync)
5. **Be installable as a uv dependency** (standalone repo)
6. **Have sensible defaults with overridable config**

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| vadocs config loading fails in pre-commit | High | Extensive testing, fallback to defaults |
| Performance regression in check_adr.py | Medium | Benchmark before/after, keep hot paths efficient |
| Config schema doesn't cover all use cases | Medium | Start minimal, extend based on real needs |
| Breaking change in check_adr.py output | Low | Integration test ensures parity |
| Test maintenance burden increases | Medium | Clear test organization, DRY fixtures |
| **Single-document design too narrow** | **High** | **Plan for ValidationContext from start** |
| **Standalone repo adds complexity** | **Medium** | **Clear versioning, CI/CD for both repos** |

---

## Summary of Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Scope** | Option C: Incremental | Start small, expand based on real usage |
| **First Feature** | Frontmatter validation | Simple, testable, proves concept |
| **Package Location** | Standalone repo | Must prove installability as uv dependency |
| **Operational Model** | Pure library | No scripts in consuming projects, updates via package |
| **Config Source** | pyproject.toml | Natural fit for uv/jupytext stack |
| **Integration** | Non-destructive | Add vadocs alongside existing tools, don't replace |

## Topics to Discuss Later

1. **Validator scope architecture**: SINGLE_FILE vs FILE_SET vs PROJECT - defer until frontmatter validator works
2. **Project scaffolding (vadocs init)**: Defer to v0.2.0 after validation proves out
3. **paths.py consolidation**: Plan exists, implement after vadocs is stable

## Open Questions for Future

1. Should vadocs eventually replace check_adr.py entirely, or should thin wrappers always exist?
2. How to handle validators that need external dependencies (e.g., jupytext)?
3. Should vadocs support custom validators via entry points in v1.0?
4. What's the PyPI package naming strategy if "vadocs" is taken?
5. Should vadocs have its own test suite that runs against real-world repos?
