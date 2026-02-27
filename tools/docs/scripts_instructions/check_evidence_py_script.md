---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

---
title: Instruction on check_evidence.py script
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-27
options:
  version: 0.1.0
  birth: 2026-02-27
---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_evidence.py) validates evidence artifacts (analyses, retrospectives, sources) in `architecture/evidence/` against the schema defined in [`evidence.config.yaml`](/architecture/evidence/evidence.config.yaml).

It ensures:
- **Required Frontmatter**: Common fields (`id`, `title`, `date`) and type-specific fields are present
- **Valid Statuses**: Status values match allowed values per artifact type
- **Valid Severity**: Severity levels match allowed values (retrospectives)
- **Valid Tags**: Tags are from the shared vocabulary in [`architecture.config.yaml`](/architecture/architecture.config.yaml) (resolved via `parent_config` pointer)
- **Naming Convention**: Filenames match regex patterns from config (e.g., `A-26001_slug`, `R-26001_slug`, `S-26001_slug`)
- **Date Format**: Date field matches YYYY-MM-DD (ISO 8601)
- **Required Sections**: Document contains required `##` headers per type
- **Section Whitelist**: Only required + optional sections are permitted; unexpected `##` headers are flagged
- **Code Fence Awareness**: `##` headers inside fenced code blocks are ignored during section extraction
- **Orphaned Source Detection**: Sources with null `extracted_into` older than configurable threshold produce warnings

All validation rules are defined in [`evidence.config.yaml`](/architecture/evidence/evidence.config.yaml) (Single Source of Truth), with shared tags inherited from the parent config.

Governed by: [ADR-26035](/architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md) (Architecture Knowledge Base Taxonomy), [ADR-26036](/architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) (Config File Location and Naming Conventions).

:::{hint} **SVA = right tool for the job**
:class: dropdown
It adheres to the **Smallest Viable Architecture (SVA)** principle.

SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Minimal External Dependencies**: Uses Python standard library (`argparse`, `re`, `subprocess`, `sys`, `pathlib`, `tomllib`) plus `pyyaml` for config parsing.
* **Config-Driven Validation**: All rules, field lists, and patterns live in YAML config — no hardcoded values in the script.
* **Git Integration**: Optional `--check-staged` mode for pre-commit delta validation.
* **Two-Level Config Resolution**: `pyproject.toml [tool.check-evidence]` → `evidence.config.yaml` → `parent_config` pointer → `architecture.config.yaml`.
:::

+++

## **2. Quick Reference**

+++

### Command Cheat Sheet

| Task | Command |
|------|---------|
| Validate all evidence | `uv run tools/scripts/check_evidence.py` |
| Verbose validation | `uv run tools/scripts/check_evidence.py --verbose` |
| Check staged only | `uv run tools/scripts/check_evidence.py --check-staged` |
| Run tests | `uv run pytest tools/tests/test_check_evidence.py -v` |
| Run tests + coverage | `uv run pytest tools/tests/test_check_evidence.py --cov=tools.scripts.check_evidence` |

+++

### Typical Workflow

```bash
# 1. Create evidence artifact
# Copy from existing artifact or write from scratch

# 2. Validate
uv run tools/scripts/check_evidence.py --verbose

# 3. Fix any reported issues in frontmatter, sections, or filename

# 4. Commit
git add architecture/evidence/
git commit -m "docs: Add analysis A-26002"
```

+++

### Key Files

| File | Purpose |
|------|---------|
| `tools/scripts/check_evidence.py` | Main validation script |
| `tools/tests/test_check_evidence.py` | Test suite (75 tests) |
| `architecture/evidence/evidence.config.yaml` | SSoT for validation rules |
| `architecture/architecture.config.yaml` | Parent config (shared tags) |
| `pyproject.toml` | Config pointer (`[tool.check-evidence]`) |

+++

## **3. Key Capabilities & Logic**

+++

### A. Config Resolution Chain

The script resolves its configuration through a two-level pointer chain:

| Step | Source | Resolves |
|------|--------|----------|
| **1. pyproject.toml** | `[tool.check-evidence].config` | Relative path to `evidence.config.yaml` |
| **2. evidence.config.yaml** | `parent_config` | Relative path to `architecture.config.yaml` |
| **3. architecture.config.yaml** | `tags` | Shared architectural vocabulary |

This allows the evidence config to inherit shared tags without duplication, following the ADR-26036 convention.

+++

### B. Artifact Discovery

The script discovers evidence artifacts by:

| Step | Description |
|------|-------------|
| **Config scan** | Iterates over `artifact_types` keys in config |
| **Directory resolution** | Each type's `directory_name` → subdirectory under `evidence/` |
| **Pattern filter** | Filenames matched against `naming_patterns[type]` regex |
| **Frontmatter parse** | YAML frontmatter extracted between `---` delimiters |
| **Sort** | Artifacts returned sorted by `artifact_id` |

+++

### C. Validation Rules

**Frontmatter Errors:**

| Error Type | Description |
|------------|-------------|
| `missing_field` | Required field missing (common or type-specific) |
| `invalid_status` | Status not in allowed list from config |
| `invalid_severity` | Severity not in allowed list from config |
| `invalid_tag` | Tag not in parent config's tag vocabulary |
| `invalid_date` | Date doesn't match YYYY-MM-DD format |

**Naming Errors:**

| Error Type | Description |
|------------|-------------|
| `naming` | Filename doesn't match regex pattern from config |

**Section Errors:**

| Error Type | Description |
|------------|-------------|
| `missing_section` | Required `##` section not found |
| `unexpected_section` | `##` header not in required + optional whitelist |

**Warnings:**

| Warning Type | Description |
|------------|-------------|
| `orphan` | Source with null `extracted_into` older than `orphan_warning_days` threshold |

+++

### D. Artifact Type Definitions

Each artifact type in `evidence.config.yaml` specifies:

| Field | Purpose |
|-------|---------|
| `directory_name` | Leaf directory under `evidence/` |
| `id_prefix` | Namespace prefix (e.g., `A`, `R`, `S`) |
| `required_fields` | Type-specific frontmatter fields |
| `optional_fields` | Allowed but not required fields |
| `statuses` | Valid lifecycle states (empty = no lifecycle) |
| `required_sections` | Mandatory `##` headers |
| `optional_sections` | Additional allowed `##` headers |

The script computes:
- `all_required_fields = common_required_fields + required_fields`
- `all_allowed_sections = required_sections + optional_sections`

+++

### E. Orphaned Source Detection

Sources follow the three-commit workflow (ADR-26035 §5):
1. Commit source to `evidence/sources/`
2. Write analysis referencing source, update source's `extracted_into`
3. Delete source file (git preserves it)

The script detects sources that may have been forgotten:
- `extracted_into` is null (not yet processed)
- `date` is older than `lifecycle.orphan_warning_days` (default: 30 days)
- These are reported as **warnings**, not errors (exit code stays 0)

+++

## **4. Operational Guide**

+++

### CLI Options

| Option | Description |
|--------|-------------|
| `--verbose` | Show detailed output including artifact names and counts |
| `--check-staged` | Only validate files staged in git (for pre-commit delta mode) |

+++

### Basic Usage

```{code-cell}
cd ../../../
```

```{code-cell}
# Validate all evidence artifacts (default)
env -u VIRTUAL_ENV uv run tools/scripts/check_evidence.py
```

```{code-cell}
# Verbose output
env -u VIRTUAL_ENV uv run tools/scripts/check_evidence.py --verbose
```

```{code-cell}
# Check only staged files (for pre-commit)
env -u VIRTUAL_ENV uv run tools/scripts/check_evidence.py --check-staged --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All evidence artifacts are valid (or none exist) |
| `1` | One or more validation errors found |

+++

## **5. Validation Layers**

+++

### Pre-commit Hook

The script runs automatically via pre-commit when evidence files change:

```yaml
- id: check-evidence
  name: Validate evidence artifacts
  entry: uv run --active tools/scripts/check_evidence.py --check-staged
  language: system
  pass_filenames: false
  files: ^architecture/evidence/
```

A companion hook runs the test suite when the script or its tests change:

```yaml
- id: test-check-evidence
  name: Test check_evidence
  entry: uv run --active pytest tools/tests/test_check_evidence.py
  language: system
  pass_filenames: false
  files: ^(tools/scripts/check_evidence\.py|tools/tests/test_check_evidence\.py|tools/scripts/paths\.py|architecture/evidence/evidence\.config\.yaml)$
```

+++

### GitHub Actions

The script runs in CI via the `evidence-validation` job in `quality.yml`:

```yaml
evidence-validation:
  runs-on: ubuntu-latest
  steps:
    - name: Run Evidence Validation
      run: uv run tools/scripts/check_evidence.py --verbose
```

+++

## **6. Test Suite**

+++

The [test suite](/tools/tests/test_check_evidence.py) provides 75 tests with config-driven, non-brittle design:

| Test Class | Coverage |
|------------|----------|
| `TestConfigLoading` | Config resolution from pyproject.toml, parent config tags, error handling |
| `TestValidateNaming` | Valid/invalid filenames per type against regex patterns from config |
| `TestValidateFrontmatter` | Required fields (common + type-specific), valid statuses, severity, tags, date format |
| `TestValidateSections` | Required sections present, optional sections allowed, unexpected sections flagged, free-form types |
| `TestDetectOrphanedSources` | Extracted sources not flagged, recent sources not flagged, old unextracted sources flagged |
| `TestDiscoverArtifacts` | Per-type discovery, sorted by ID, empty directories, non-matching files ignored |
| `TestCli` | Exit 0 on valid, exit 1 on errors, exit 0 on empty, --verbose and --check-staged flags |

**Design principles:**
- All constants derived from production configs (SSoT chain: `pyproject.toml` → `evidence.config.yaml` → `architecture.config.yaml`)
- Single module import: `import tools.scripts.check_evidence as _module`
- Heuristic field resolver (`_resolve_field_default`) generates valid test values without hardcoding field names
- Semantic assertions: test contracts (exit codes, error presence) not message strings

Run tests with:

```bash
uv run pytest tools/tests/test_check_evidence.py -v
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_evidence.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_evidence.py --cov=tools.scripts.check_evidence --cov-report=term-missing -q
```

## **7. Common Scenarios**

+++

### Scenario 1: Adding a New Analysis

**Goal**: Create a new analysis and validate it.

```bash
# 1. Create the analysis file
# Filename must match pattern: A-YYXXX_slug.md (e.g., A-26002_llm_evaluation.md)

# 2. Add required frontmatter:
# ---
# id: A-26002
# title: LLM Evaluation Framework
# date: 2026-02-27
# status: active
# tags: [model]
# ---

# 3. Add required sections: Problem Statement, References
# Add optional sections as needed: Approach Evaluation, Key Insights, etc.

# 4. Validate
uv run tools/scripts/check_evidence.py --verbose

# 5. Stage and commit
git add architecture/evidence/analyses/A-26002_llm_evaluation.md
```

+++

### Scenario 2: Adding a Retrospective

**Goal**: Document a post-mortem or failure analysis.

```bash
# 1. Create the retrospective file
# Filename: R-YYXXX_slug.md (e.g., R-26001_deployment_failure.md)

# 2. Required frontmatter includes severity:
# ---
# id: R-26001
# title: Deployment Failure Analysis
# date: 2026-02-27
# status: active
# severity: high
# tags: [devops]
# ---

# 3. Required sections: Executive Summary, References

# 4. Validate and commit
uv run tools/scripts/check_evidence.py --verbose
```

+++

### Scenario 3: Processing a Source (Three-Commit Workflow)

**Goal**: Capture a dialogue transcript and extract insights.

```bash
# Commit 1: Add source
git add architecture/evidence/sources/S-26001_claude_discussion.md
git commit -m "docs: Add source S-26001"

# Commit 2: Write analysis, update source's extracted_into
# In S-26001: set extracted_into: A-26002
# Create A-26002_insights.md referencing the source
git add architecture/evidence/
git commit -m "docs: Add analysis A-26002 from source S-26001"

# Commit 3: Delete source (git preserves history)
git rm architecture/evidence/sources/S-26001_claude_discussion.md
git commit -m "chore: Remove processed source S-26001"
```

+++

### Scenario 4: Adding a New Tag

**Goal**: Use a tag that's not in the shared vocabulary.

```bash
# 1. Validation shows invalid tag
uv run tools/scripts/check_evidence.py --verbose
# Output: Invalid tags: ['new_tag'] (valid: [...])

# 2. Add the tag to the parent config
# Edit architecture/architecture.config.yaml:
# tags:
#   - ...
#   - new_tag

# 3. Re-validate
uv run tools/scripts/check_evidence.py --verbose
```

+++

### Scenario 5: Pre-commit Validation

**Goal**: Validate evidence before committing.

```bash
# The pre-commit hook runs automatically when evidence files change
git add architecture/evidence/analyses/A-26002_new_analysis.md
git commit -m "docs: Add analysis A-26002"

# If validation fails:
# Validate evidence artifacts...Failed
# Fix the reported issues and retry

# For staged-only validation (faster):
uv run tools/scripts/check_evidence.py --check-staged --verbose
```
