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

# Instruction on check_script_suite.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.1.0
Birth: 2026-01-26
Last Modified: 2026-01-26

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_script_suite.py) validates that each script in `tools/scripts/` has a complete suite: the script itself, a test file, and documentation.

It enforces the naming convention:
- Script: `tools/scripts/<name>.py`
- Test: `tools/tests/test_<name>.py`
- Doc: `tools/docs/scripts_instructions/<name>_py_script.md`

This tool is designed to serve as a quality gate in CI/CD, ensuring documentation stays synchronized with code changes.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `subprocess`, `sys`, `pathlib`).
* **Pattern-Based Detection**: Derives documentation paths from script names automatically—no mapping configuration needed.
* **Git Integration**: Detects staged files and renames using git commands.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. Naming Convention Validation

The script checks that each Python file in `tools/scripts/` (except excluded files) has:

| Required File | Pattern |
|--------------|---------|
| **Test suite** | `tools/tests/test_<name>.py` |
| **Documentation** | `tools/docs/scripts_instructions/<name>_py_script.md` |

+++

### B. Co-staging Validation

When a script or test file is staged for commit, the corresponding documentation must also be staged:

| Trigger | Required |
|---------|----------|
| `tools/scripts/<name>.py` staged | `<name>_py_script.md` must be staged |
| `tools/tests/test_<name>.py` staged | `<name>_py_script.md` must be staged |

+++

### C. Rename Tracking

When a documentation file is renamed, the configuration files must be updated:

| Trigger | Required |
|---------|----------|
| `*_py_script.md` renamed | `.pre-commit-config.yaml` must be staged |
| `*_py_script.md` renamed | `.github/workflows/quality.yml` must be staged |

+++

### D. Excluded Scripts

These scripts are excluded from suite validation:

| Script | Reason |
|--------|--------|
| `paths.py` | Shared configuration, no dedicated documentation |
| `__init__.py` | Package marker, no documentation needed |

+++

## **3. Operational Guide**

+++

### Basic Usage

```bash
# Check naming convention and staging (default)
uv run tools/scripts/check_script_suite.py

# Verbose output
uv run tools/scripts/check_script_suite.py --verbose

# Only check naming convention (skip staging checks)
uv run tools/scripts/check_script_suite.py --check-convention-only
```

+++

### CLI Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Show detailed output including successful checks |
| `--check-convention-only` | Only validate naming convention, skip git staging checks |

+++

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | One or more validation errors found |

+++

## **4. Validation Layers**

+++

### Pre-commit Hook

The script runs automatically via pre-commit when script, test, or doc files change:

```yaml
- id: check-script-suite
  name: Check Script Suite (script + test + doc)
  entry: uv run --active tools/scripts/check_script_suite.py
  language: python
  files: ^tools/(scripts/.*\.py|tests/test_.*\.py|docs/scripts_instructions/.*_py_script\.md)$
```

+++

### GitHub Actions

The script runs in CI via the `script-suite` job in `quality.yml`:

```yaml
script-suite:
  runs-on: ubuntu-latest
  steps:
    - name: Run Script Suite Check
      run: uv run tools/scripts/check_script_suite.py --verbose
```

+++

## **5. Test Suite**

+++

The [test suite](/tools/tests/test_check_script_suite.py) covers:

| Test Class | Coverage |
|------------|----------|
| `TestScriptNameToPaths` | Path derivation from script names |
| `TestGetStagedFiles` | Git staged file detection |
| `TestGetRenamedFiles` | Git rename detection |
| `TestGetAllScripts` | Script discovery and exclusions |
| `TestCheckNamingConvention` | Suite completeness validation |
| `TestCheckDocStaged` | Co-staging enforcement |
| `TestCheckDocRename` | Rename tracking |
| `TestMain` | CLI integration |

Run tests with:

```bash
uv run pytest tools/tests/test_check_script_suite.py -v
```
