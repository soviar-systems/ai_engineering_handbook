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

# Instruction on check_json_files.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com  
Version: 0.1.0  
Birth: 2026-01-21  
Last Modified: 2026-01-21

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_json_files.py) validates JSON files for syntax errors using Python's standard library json module.

This tool is designed to serve as a quality gate in CI/CD, preventing commits with malformed JSON files that could break configuration, data pipelines, or application behavior.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `json`, `sys`, `pathlib`), ensuring it runs on any system with Python installed.
* **Comprehensive Validation**: Checks for valid JSON syntax including brackets, quotes, commas, and UTF-8 encoding.
* **Line Number Reporting**: Reports the approximate line of syntax errors for easy debugging.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. JSON Syntax Validation

The script validates:

| Check | Description |
|-------|-------------|
| **Bracket Matching** | Verifies all `{` and `[` have matching `}` and `]` |
| **String Quoting** | Ensures strings use double quotes (not single quotes) |
| **Key Quoting** | Verifies all object keys are quoted strings |
| **Trailing Commas** | Detects invalid trailing commas in arrays/objects |
| **UTF-8 Encoding** | Validates files are properly UTF-8 encoded |

+++

### B. Directory Exclusions

When scanning directories, the script automatically excludes:

| Directory | Reason |
|-----------|--------|
| `.git` | Version control internals |
| `.venv`, `venv` | Python virtual environments |
| `__pycache__` | Python bytecode cache |
| `node_modules` | Node.js dependencies |
| `.ipynb_checkpoints` | Jupyter notebook checkpoints |
| `build`, `dist` | Build artifacts |

+++

## **3. Technical Architecture**

+++

The script is organized into specialized classes to maintain clarity:

| Class | Responsibility |
|-------|----------------|
| `JsonValidator` | Parse and validate JSON syntax using `json.loads()` |
| `FileFinder` | Recursive file discovery for `*.json` files |
| `Reporter` | Output formatting and exit code handling |
| `JsonValidatorCLI` | Argument parsing and main orchestration |
| `JsonError` | NamedTuple storing validation errors (file, line, message) |

+++

## **4. Operational Guide**

+++

### Configuration Reference

+++

* **Primary Script**: `tools/scripts/check_json_files.py`
* **Pre-commit Config**: `.pre-commit-config.yaml`
* **CI Config**: `.github/workflows/quality.yml`

+++

### Command Line Interface

+++

```bash
check_json_files.py [files...] [--verbose]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `files` | One or more JSON files to validate | Current directory (recursive) |
| `--verbose` | Shows detailed logs of validated files and results | `False` |

**Exit Codes:**
- `0` = All JSON files valid
- `1` = Validation errors found

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
|------|---------|
| **Check Specific Files** | `uv run tools/scripts/check_json_files.py file1.json file2.json` |
| **Full Directory Scan** | `uv run tools/scripts/check_json_files.py --verbose` |
| **Pre-commit Mode** | `uv run tools/scripts/check_json_files.py path/to/staged/file.json` |

+++

### Examples

```{code-cell}
cd ../../../
ls
```

1. Check specific files:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/check_json_files.py ai_system/3_prompts/consultants/devops_consultant.json
```

2. Check with verbose output:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/check_json_files.py --verbose ai_system/3_prompts/consultants/devops_consultant.json
```

## **5. Validation Layers**

+++

### Layer 1: Local Pre-commit Hook

+++

The first line of defense runs automatically during the `git commit` process to prevent malformed JSON from entering version control.

**Pre-commit Configuration:**
```yaml
- id: check-json-files
  name: Check JSON Files
  entry: uv run --active tools/scripts/check_json_files.py
  language: system
  files: \.json$
  pass_filenames: true
  exclude: ^(tools/tests/|\.vscode/)
```

* **Scope**: Validates all staged `.json` files
* **`pass_filenames: true`**: Receives file list from git, enabling targeted checking
* **Exclusion**: Test fixtures and VS Code settings are excluded

+++

### Layer 2: GitHub Action (Continuous Integration)

+++

The CI pipeline in `quality.yml` runs the test suite when relevant files change:

```yaml
- name: Get changed json-validation files
  id: changed-json-validation
  uses: tj-actions/changed-files@v45
  with:
    files: |
      tools/scripts/check_json_files.py
      tools/tests/test_check_json_files.py

- name: Run JSON Validation Tests
  if: steps.changed-json-validation.outputs.any_changed == 'true' || steps.changed-paths.outputs.any_changed == 'true'
  run: uv run pytest tools/tests/test_check_json_files.py
```

*Note: `paths.py` is detected separately because it's a shared dependency across multiple test suites.*

+++

### Layer 3: Logic Tests Pre-commit Hook

+++

A meta-check ensures the validation logic remains sound:

```yaml
- id: test-check-json-files
  name: Test JSON validation script
  entry: uv run --active pytest tools/tests/test_check_json_files.py
  language: system
  pass_filenames: false
  files: ^tools/(scripts/check_json_files\.py|scripts/paths\.py|tests/test_check_json_files\.py)$
```

This triggers whenever the script, its tests, or shared configuration change.

+++

## **6. Test Suite Documentation**

+++

The script is accompanied by a comprehensive test suite (`test_check_json_files.py`) that ensures reliability across different patterns and edge cases.

+++

### Test Classes and Coverage

| Test Class | Purpose |
|------------|---------|
| `TestJsonValidator` | Valid JSON, syntax errors, encoding errors, line number reporting |
| `TestFileFinder` | Recursive discovery, directory exclusion, nested files |
| `TestReporter` | Exit codes, output formatting, verbose mode |
| `TestJsonValidatorCLI` | Integration tests for CLI modes and arguments |

+++

### Key Test Scenarios

- **Valid JSON**: Objects, arrays, nested structures, Unicode content
- **Invalid JSON**: Missing brackets, trailing commas, single quotes, unquoted keys
- **Line Numbers**: Correct line reporting for multi-line files
- **Binary Files**: Gracefully handled with error message
- **Missing Files**: Warning issued, non-blocking
- **Empty Files**: Treated as valid (skipped)
- **Directory Exclusions**: `.git`, `node_modules`, `__pycache__`, etc.

+++

### Running the Tests

To run the full suite, execute from the repository root:

```bash
$ uv run pytest tools/tests/test_check_json_files.py
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_json_files.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_json_files.py --cov=. --cov-report=term-missing -q
```
