# Plan: ADR-26029 — pyproject.toml as Tool Configuration Hub

## Context

Scripts in `tools/scripts/` need shared configuration (e.g., valid commit types, CHANGELOG section mappings). Previously these were hardcoded constants duplicated across scripts. We moved them to `pyproject.toml [tool.commit-convention]` and need an ADR to formalize this pattern for the repo and future spoke packages.

## Decision to document

`pyproject.toml [tool.X]` sections are the canonical location for machine-readable tool configuration in this repository and its spoke packages. This applies to repo-internal scripts and any Python package that needs configurable behavior.

### Why pyproject.toml

- **stdlib support**: `tomllib` since Python 3.11, no external deps
- **Package portability**: config travels with the package when extracted to a spoke repo (ADR-26020)
- **Ecosystem convention**: `black`, `ruff`, `pytest`, `mypy`, `commitizen` all use `[tool.X]`
- **TOML preserves key order**: enables ordered mappings (e.g., CHANGELOG section ordering)
- **Single file**: avoids proliferating config files (`adr_config.yml`, `commit_convention.yml`, etc.)

### What NOT to put in pyproject.toml

- Path constants → `tools/scripts/paths.py` (Python-native, imports cleanly)
- Build/CI config → `.pre-commit-config.yaml`, `quality.yml` etc.
- MyST config → `myst.yml` (MyST-specific toolchain)
- ADR validation rules → `adr_config.yaml` (already established, YAML-native)

### First use

`[tool.commit-convention]` — valid types, ArchTag-required types, type→section mapping. Consumed by `validate_commit_msg.py` and `generate_changelog.py`.

## Steps

### 1. Write ADR-26029

**File**: `architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md`

Sections per template:
- **Context**: scripts need shared config; hardcoded constants drift; spoke packages need portable config
- **Decision**: `pyproject.toml [tool.X]` for all repo tool config. Loaded via `tomllib` (stdlib). Scripts expose loaded values as module-level constants for testability.
- **Consequences positive**: single source of truth, package-portable, stdlib-only, IDE support
- **Consequences negative**: TOML is less expressive than YAML for deeply nested config. **Mitigation**: keep sections flat.
- **Alternatives**:
  - Dedicated YAML files (e.g., `commit_convention.yml`) — rejected: proliferates config files, needs `pyyaml` dependency
  - `paths.py` extension — rejected: mixes path constants with domain config
  - `.commitlintrc.yml` — rejected: implies commitlint toolchain (Node.js, ADR-26003 rejected)
- **References**: ADR-26020 (hub-spoke), ADR-26024 (structured commits), Production Git Workflow Standards

### 2. Cross-reference from Production Git Workflow Standards

Already done — added `:::{tip}` boxes in `01_production_git_workflow_standards.md` pointing to `pyproject.toml [tool.commit-convention]`.

## Verification

1. ADR follows template structure from `architecture/adr/adr_template.md`
2. Cross-references resolve (ADR-26020, ADR-26024, workflow standards)
3. `pyproject.toml` config block has comment pointing back to the ADR
