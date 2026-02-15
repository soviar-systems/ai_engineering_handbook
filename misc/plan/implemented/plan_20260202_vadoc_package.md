# Plan: Documentation Validation Engine (Standalone Package)

## Summary

Create a **reusable documentation validation engine** as a standalone Python package called `vadoc`. Extract logic from `check_adr.py`, add bi-directional sync feature, and establish a pattern for complex tooling that exceeds ADR-26011 script suite scope.

---

## Implementation Status (v0.1.0 Simplified)

### Completed (2026-02-03)

**Phase 1: Clean Up** ✅
- Deleted `registry.py` (plugin discovery deferred to v0.2.0)
- Deleted `cli/` directory (CLI deferred to v0.2.0)
- Deleted `tests/test_registry.py`
- Updated `pyproject.toml` - removed entry points and CLI script

**Phase 2: Direct Imports API** ✅
- Updated `vadoc/__init__.py` with direct exports of all validators/fixers
- Updated `vadoc/validators/__init__.py` - exports AdrValidator, FrontmatterValidator, MystGlossaryValidator, AdrTermValidator
- Updated `vadoc/fixers/__init__.py` - exports AdrFixer, SyncFixer
- Updated `vadoc/core/__init__.py` - added extract_section_content

**Phase 3: Verify Core Tests** ✅
- All 26 existing tests pass (test_models.py, test_parsing.py)
- Import verification successful

**Phase 4: Validator Tests** 🔄 In Progress
- Created `tests/validators/test_adr.py` (comprehensive tests for AdrValidator)
- Created `tests/validators/test_frontmatter.py` (comprehensive tests for FrontmatterValidator)
- Created `tests/validators/test_myst_glossary.py` (tests for AdrTermValidator)

### Pending

**Phase 5: Fixer Tests**
- `tests/fixers/test_adr_fixer.py`
- `tests/fixers/test_sync_fixer.py`

**Phase 6: Root Dependency**
- Add vadoc as local dependency to root `pyproject.toml`

**Phase 7: README** ✅
- Created with Documentation-as-Code motivation
- Includes product goals and target users

### Current Package Structure

```
packages/vadoc/
├── pyproject.toml          # Simplified - no entry points, no CLI
├── README.md               # With motivation and target users
├── src/vadoc/
│   ├── __init__.py         # Direct exports of all validators/fixers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py       # Document, ValidationError, SyncField, SyncResult
│   │   └── parsing.py      # parse_frontmatter, extract_status, extract_section_content
│   ├── validators/
│   │   ├── __init__.py     # Exports all validators
│   │   ├── base.py         # Validator ABC
│   │   ├── adr.py          # AdrValidator
│   │   ├── frontmatter.py  # FrontmatterValidator
│   │   └── myst_glossary.py # MystGlossaryValidator, AdrTermValidator
│   └── fixers/
│       ├── __init__.py     # Exports all fixers
│       ├── base.py         # Fixer ABC
│       ├── adr_fixer.py    # AdrFixer
│       └── sync_fixer.py   # SyncFixer
└── tests/
    ├── conftest.py
    ├── core/
    │   ├── test_models.py      ✅ 12 tests passing
    │   └── test_parsing.py     ✅ 14 tests passing
    ├── validators/
    │   ├── test_adr.py         📝 Written, needs run
    │   ├── test_frontmatter.py 📝 Written, needs run
    │   └── test_myst_glossary.py 📝 Written, needs run
    └── fixers/
        └── (pending)
```

### Decisions Made

| Aspect | Original Plan | v0.1.0 Simplified |
|--------|---------------|-------------------|
| Plugin discovery | Entry points (importlib.metadata) | Direct imports |
| CLI | Subcommands (validate, fix, list-plugins) | No CLI - library only |
| Registry | registry.py with discover_*() | Removed |
| Entry points | pyproject.toml [project.entry-points] | None |

### v0.2.0 Roadmap (Deferred)
- Entry point plugin discovery
- CLI with subcommands
- Third-party plugin support
- Publish to PyPI

---

## Needs Analysis Before Continuing

User requested pause for deeper analysis. Key questions to resolve:

1. **Integration with check_adr.py**: How should the thin wrapper work?
2. **Config loading**: Should vadoc load config or expect it passed in?
3. **Error reporting format**: Current format vs. more structured output?
4. **Fixer behavior**: In-place modification vs. returning modified content?

---

## Part 1: Package Architecture

### Vision

A general-purpose Python package for validating structured documentation:
- **ADR validation** (current use case)
- **YAML frontmatter sync** (new feature)
- **Extensible** for other doc types (RFCs, design docs, changelogs)

### Package Name: `vadoc`

Short, memorable, implies "validation + documentation."

### Package Location

```
packages/
└── vadoc/
    ├── pyproject.toml
    ├── README.md
    ├── src/
    │   └── vadoc/
    │       ├── __init__.py         # Public API
    │       ├── core/
    │       │   ├── __init__.py
    │       │   ├── models.py       # Base data classes (ValidationError, etc.)
    │       │   ├── parsing.py      # YAML/Markdown parsing utilities
    │       │   └── sync.py         # Bi-directional sync engine
    │       ├── validators/
    │       │   ├── __init__.py
    │       │   ├── base.py         # Abstract Validator class
    │       │   ├── adr.py          # ADR-specific validation
    │       │   ├── frontmatter.py  # Generic frontmatter validation
    │       │   └── myst.py         # MyST term reference validation
    │       ├── fixers/
    │       │   ├── __init__.py
    │       │   ├── base.py         # Abstract Fixer class
    │       │   ├── adr_fixer.py    # ADR auto-fix logic
    │       │   └── sync_fixer.py   # Sync operations
    │       └── cli/
    │           ├── __init__.py
    │           └── main.py         # CLI entry point
    └── tests/
        ├── conftest.py
        ├── core/
        │   ├── test_models.py
        │   ├── test_parsing.py
        │   └── test_sync.py
        ├── validators/
        │   ├── test_adr.py
        │   └── test_frontmatter.py
        └── test_cli.py
```

### Integration with Current Repo

After creating the package:

```python
# tools/scripts/check_adr.py becomes a thin wrapper:
from vadoc.validators.adr import AdrValidator
from vadoc.cli import run_validation

config = load_local_config("architecture/adr/adr_config.yaml")
validator = AdrValidator(config)
sys.exit(run_validation(validator, args))
```

```toml
# pyproject.toml
[project]
dependencies = [
    "vadoc @ file:packages/vadoc",  # Local path during development
]
```

### ADR-26011 Compliance

- **Package** is outside script suite scope (not a single script)
- **Thin wrapper** `check_adr.py` remains ADR-26011 compliant
- Create **ADR-26020** to document the pattern for internal packages

---

## Part 2: Bi-Directional Sync Feature

### Fields to Synchronize

| YAML Field | Markdown Location | Direction |
|------------|-------------------|-----------|
| `id` | `# ADR-{id}: {title}` header | YAML → MD |
| `title` | Header + `## Title` section | Bi-directional |
| `date` | `## Date` section | Bi-directional |
| `status` | `## Status` section | Bi-directional |
| `superseded_by` | `## Status` (if superseded) | YAML → MD |

### Sync Logic

```
IF only YAML exists:
    → Generate markdown sections from YAML

ELIF only markdown exists:
    → Generate YAML frontmatter from markdown

ELIF both exist but mismatch:
    → Report error (user chooses direction with --sync-direction)

ELIF both absent:
    → Report error: "No source data"

ELSE (both match):
    → No action
```

### CLI Arguments

```
--sync              Enable bi-directional sync
--sync-direction    auto | yaml-to-md | md-to-yaml
--dry-run           Preview without modifying
```

### Core Functions (in `vadoc/core/sync.py`)

```python
def extract_section_content(content: str, section: str) -> str | None
def extract_sync_fields(content: str, frontmatter: dict) -> dict[str, SyncField]
def sync_yaml_to_markdown(doc: Document, dry_run: bool) -> SyncResult
def sync_markdown_to_yaml(doc: Document, dry_run: bool) -> SyncResult
def auto_sync(doc: Document, dry_run: bool) -> SyncResult
```

---

## Part 3: Plugin Architecture

### Entry Point System

Validators and fixers are discovered via Python entry points:

```toml
# packages/vadoc/pyproject.toml
[project.entry-points."vadoc.validators"]
adr = "vadoc.validators.adr:AdrValidator"
frontmatter = "vadoc.validators.frontmatter:FrontmatterValidator"
myst = "vadoc.validators.myst:MystTermValidator"

[project.entry-points."vadoc.fixers"]
adr = "vadoc.fixers.adr_fixer:AdrFixer"
sync = "vadoc.fixers.sync_fixer:SyncFixer"
```

### Plugin Interface

```python
# vadoc/validators/base.py
from abc import ABC, abstractmethod
from typing import Protocol

class ValidatorProtocol(Protocol):
    """Protocol for validator plugins."""
    name: str

    def validate(self, document: Document, config: dict) -> list[ValidationError]: ...
    def supports(self, document: Document) -> bool: ...

class Validator(ABC):
    """Base class for validators."""
    name: str = "base"

    @abstractmethod
    def validate(self, document: Document, config: dict) -> list[ValidationError]:
        """Run validation on document."""

    @abstractmethod
    def supports(self, document: Document) -> bool:
        """Return True if this validator can handle this document type."""
```

### Plugin Discovery

```python
# vadoc/registry.py
from importlib.metadata import entry_points

def discover_validators() -> dict[str, type[Validator]]:
    """Discover all registered validator plugins."""
    validators = {}
    eps = entry_points(group="vadoc.validators")
    for ep in eps:
        validators[ep.name] = ep.load()
    return validators

def discover_fixers() -> dict[str, type[Fixer]]:
    """Discover all registered fixer plugins."""
    fixers = {}
    eps = entry_points(group="vadoc.fixers")
    for ep in eps:
        fixers[ep.name] = ep.load()
    return fixers
```

### Third-Party Plugin Example

A third-party package `vadoc-rfc` could register:

```toml
# vadoc-rfc/pyproject.toml
[project.entry-points."vadoc.validators"]
rfc = "vadoc_rfc:RfcValidator"
```

---

## Part 4: PyPI Publishing Strategy

### Package Metadata

```toml
# packages/vadoc/pyproject.toml
[project]
name = "vadoc"
version = "0.1.0"
description = "Documentation validation engine with YAML frontmatter sync"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Vadim Rudakov"}]
keywords = ["documentation", "validation", "adr", "frontmatter", "yaml"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff"]

[project.scripts]
vadoc = "vadoc.cli.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Versioning Strategy

- **Semantic versioning**: MAJOR.MINOR.PATCH
- **Initial release**: 0.1.0 (alpha)
- **1.0.0**: When API is stable and production-tested

### Release Workflow

```yaml
# .github/workflows/publish-vadoc.yml
name: Publish vadoc to PyPI
on:
  push:
    tags: ['vadoc-v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build packages/vadoc
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: packages/vadoc/dist/
```

### Local Development Workflow

During development, use local path dependency:

```toml
# ai_engineering_book/pyproject.toml
[project]
dependencies = [
    "vadoc @ file:packages/vadoc",  # Local during dev
]
```

After publishing:

```toml
dependencies = [
    "vadoc>=0.1.0",  # From PyPI
]
```

---

## Part 5: Implementation Plan

### Phase 1: Package Scaffold with Plugin Architecture
1. Create `packages/vadoc/` directory structure
2. Write `pyproject.toml` with entry points
3. Implement `Validator` and `Fixer` protocols/base classes
4. Implement plugin discovery in `registry.py`
5. Write tests for plugin discovery

### Phase 2: Core Models and Parsing (TDD)
1. Write tests for `Document`, `ValidationError`, `SyncField`, `SyncResult`
2. Implement data classes in `vadoc/core/models.py`
3. Write tests for YAML/markdown parsing
4. Implement parsing utilities in `vadoc/core/parsing.py`

### Phase 3: Built-in Validators (TDD)
1. Write tests for `AdrValidator`
2. Extract and adapt ADR validation logic from `check_adr.py`
3. Write tests for `FrontmatterValidator`
4. Implement generic frontmatter validation
5. Write tests for `MystTermValidator`
6. Implement MyST term reference validation

### Phase 4: Sync Feature (TDD)
1. Write tests for section extraction
2. Implement `extract_section_content()`
3. Write tests for `sync_yaml_to_markdown()`
4. Implement YAML → markdown sync
5. Write tests for `sync_markdown_to_yaml()`
6. Implement markdown → YAML sync
7. Write tests for `auto_sync()`
8. Implement auto-detection logic

### Phase 5: Built-in Fixers (TDD)
1. Write tests for `AdrFixer`
2. Extract and adapt fix logic from `check_adr.py`
3. Write tests for `SyncFixer`
4. Implement sync operations

### Phase 6: CLI
1. Write tests for CLI argument parsing
2. Implement `vadoc/cli/main.py`
3. Support config file loading (YAML/TOML)
4. Support plugin selection via CLI

### Phase 7: Integration with ai_engineering_book
1. Update `tools/scripts/check_adr.py` to be thin wrapper
2. Add vadoc as local dependency
3. Verify all existing tests pass
4. Add integration tests

### Phase 8: Documentation & Release Prep
1. Write comprehensive README.md
2. Add CHANGELOG.md
3. Create ADR-26020 for internal package pattern
4. Set up GitHub Actions for publishing
5. Tag and publish 0.1.0 to PyPI

---

## Critical Files

### To Create (Package)
- `packages/vadoc/pyproject.toml`
- `packages/vadoc/README.md`
- `packages/vadoc/CHANGELOG.md`
- `packages/vadoc/src/vadoc/__init__.py`
- `packages/vadoc/src/vadoc/core/models.py`
- `packages/vadoc/src/vadoc/core/parsing.py`
- `packages/vadoc/src/vadoc/core/sync.py`
- `packages/vadoc/src/vadoc/validators/base.py`
- `packages/vadoc/src/vadoc/validators/adr.py`
- `packages/vadoc/src/vadoc/fixers/base.py`
- `packages/vadoc/src/vadoc/fixers/sync_fixer.py`
- `packages/vadoc/src/vadoc/registry.py`
- `packages/vadoc/src/vadoc/cli/main.py`
- `packages/vadoc/tests/` (full test suite)

### To Create (Repo)
- `architecture/adr/adr_26020_internal_python_packages.md`
- `.github/workflows/publish-vadoc.yml`

### To Modify
- `pyproject.toml` - Add vadoc dependency
- `tools/scripts/check_adr.py` - Convert to thin wrapper
- `tools/tests/test_check_adr.py` - Update for integration testing

### To Preserve
- `architecture/adr/adr_config.yaml` - Keep as repo-specific config

---

## Verification Plan

1. **Package tests**: `uv run pytest packages/vadoc/tests/`
2. **Integration tests**: `uv run pytest tools/tests/test_check_adr.py`
3. **CLI test**: `uv run python -m vadoc --help`
4. **Sync dry-run**: `uv run python -m tools.scripts.check_adr --sync --dry-run`
5. **Real ADR test**: Apply sync to `adr_26001` (has known mismatches)
6. **Pre-commit**: Verify `--check-staged` still works
7. **CI**: Ensure `quality.yml` passes
