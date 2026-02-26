# Plan: Architecture Knowledge Base Taxonomy — Tooling (Batch 2)

## Context

Batch 1 (implemented) created the ADRs, directory structure, configs, and inaugural analysis for the Architecture Knowledge Base taxonomy. Batch 2 adds the validation tooling and CI integration.

## Prerequisites

- Batch 1 committed (ADR-26035, ADR-26036, A-26001, configs, directories)
- `architecture/evidence/evidence.config.yaml` defines artifact types, naming patterns, sections
- `architecture/architecture.config.yaml` defines shared tags
- `pyproject.toml` has `[tool.check-evidence]` config pointer

## Implementation Steps

### Step 1: Write tests for check_evidence.py (TDD)

Create `tools/tests/test_check_evidence.py` following existing patterns from `test_check_adr.py`:

- Behavior-based testing, semantic assertions, parameterized inputs
- Load config from real `evidence.config.yaml` SSoT (not hardcoded values)
- Test helper functions: `create_analysis_file()`, `create_retrospective_file()`, `create_source_file()`
- Test classes covering contracts:
  - **Frontmatter validation:** required fields per type, valid statuses, valid severity, valid tags (from parent config)
  - **Naming convention:** valid/invalid filenames against regex patterns from config
  - **Orphaned source detection:** sources with `extracted_into: null` older than threshold
  - **CLI exit codes:** exit 0 on valid artifacts, exit 1 on validation errors
  - **Config loading:** reads config path from `pyproject.toml [tool.check-evidence]`, resolves `parent_config`
  - **Section validation:** required sections present, no unexpected sections (required + optional = allowed)

### Step 2: Implement check_evidence.py

Create `tools/scripts/check_evidence.py` — make all tests pass.

- Top-down design, `pathlib.Path`, exit codes 0/1
- Config loading: read path from `pyproject.toml [tool.check-evidence]` via `tomllib`
- Parent config resolution: read `parent_config` path, load shared tags
- CLI arguments: `--verbose`, `--check-staged` (for pre-commit delta mode)
- Validation functions:
  - `validate_frontmatter()` — check required fields, valid values
  - `validate_naming()` — filename matches regex from config
  - `validate_sections()` — required sections present, no unexpected sections
  - `detect_orphaned_sources()` — warn on sources with null `extracted_into` past threshold
- Discovery: scan `evidence/` subdirectories based on `artifact_types[*].directory_name` from config

### Step 3: Create script instruction doc

Create `tools/docs/scripts_instructions/check_evidence_py_script.md` per ADR-26011 format:

- MyST markdown with frontmatter (Owner, Version, Birth, Last Modified)
- Sections: Architectural Overview, Key Capabilities, Technical Architecture, Operational Guide, Validation Layers, Test Suite
- Reference ADR-26035, ADR-26036, evidence.config.yaml

### Step 4: Integrate into pre-commit hooks

Add to `.pre-commit-config.yaml` following existing patterns:

```yaml
- id: check-evidence
  name: Validate evidence artifacts
  entry: uv run --active tools/scripts/check_evidence.py --check-staged
  language: system
  pass_filenames: false
  files: ^architecture/evidence/

- id: test-check-evidence
  name: Test check_evidence
  entry: uv run --active pytest tools/tests/test_check_evidence.py
  language: system
  pass_filenames: false
  files: ^(tools/scripts/check_evidence\.py|tools/tests/test_check_evidence\.py|tools/scripts/paths\.py|architecture/evidence/evidence\.config\.yaml)$
```

### Step 5: Integrate into CI

Add to `.github/workflows/quality.yml` following existing job patterns:

- Job `evidence-validation` with `logic` and `docs` file groups
- Logic triggers: check_evidence.py, test file, paths.py, evidence.config.yaml changes
- Docs triggers: `architecture/evidence/**/*.md` changes
- Runs tests when logic changes, runs full validation when evidence docs change

### Step 6: Update ADR index

Run `uv run tools/scripts/check_adr.py --fix` to add ADR-26035 and ADR-26036 to the index.

### Step 7: Verify end-to-end

1. `uv run pytest tools/tests/test_check_evidence.py` — all tests pass
2. `uv run tools/scripts/check_evidence.py --verbose` — validates A-26001 successfully
3. `uv run pytest tools/tests/test_check_adr.py` — existing ADR tests still pass
4. `uv run tools/scripts/check_adr.py --fix` — index updated with ADR-26035, ADR-26036
5. `uv run tools/scripts/check_broken_links.py --pattern "*.md"` — no broken links

## Files to Create

- `tools/scripts/check_evidence.py`
- `tools/tests/test_check_evidence.py`
- `tools/docs/scripts_instructions/check_evidence_py_script.md`

## Files to Modify

- `.pre-commit-config.yaml` — add check-evidence and test-check-evidence hooks
- `.github/workflows/quality.yml` — add evidence-validation job
- `architecture/adr_index.md` — auto-updated by check_adr.py --fix

## Design Decisions to Carry Forward

- check_evidence.py reads config path from `pyproject.toml [tool.check-evidence]` (ADR-26036 pattern)
- Parent config (tags) resolved via `parent_config` repo-root-relative path
- Cross-reference validation deferred — not in scope for this batch
- `date_format` hardcoded in script until repo-wide frontmatter standard exists
