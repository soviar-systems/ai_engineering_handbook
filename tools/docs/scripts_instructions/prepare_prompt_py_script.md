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

# Instruction on prepare_prompt.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.1.0
Birth: 2026-01-25
Last Modified: 2026-01-25

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/prepare_prompt.py) prepares prompt JSON files for LLM consumption by removing metadata, stripping special characters, and converting to a YAML-like output format.

This tool is designed to transform structured prompt files into clean, readable formats suitable for copying into LLM interfaces or automated prompt injection.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `json`, `sys`, `pathlib`), ensuring it runs on any system with Python installed.
* **Bash Compatibility**: Output matches the original `prepare_prompt.sh` script behavior.
* **Multiple Output Formats**: Supports YAML-like (default) and plain text extraction.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. JSON Processing

The script performs:

| Operation | Description |
|-----------|-------------|
| **Metadata Removal** | Removes the `metadata` field from JSON objects |
| **Character Stripping** | Removes `*`, `'`, `"`, `` ` ``, `#` from output |
| **YAML Conversion** | Converts JSON structure to YAML-like indented format |
| **Plain Text Extraction** | Optionally extracts only text values |

+++

### B. Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `yaml` (default) | YAML-like key: value structure | Copying to LLM interfaces |
| `plain` | Text values only, newline-separated | Automated processing |

+++

## **3. Technical Architecture**

+++

The script is organized into specialized classes:

| Class | Responsibility |
|-------|----------------|
| `JsonHandler` | Parse JSON, remove metadata, convert to output formats |
| `Reporter` | Output formatting and exit code handling |
| `PreparePromptCLI` | Argument parsing and main orchestration |

+++

## **4. Operational Guide**

+++

### Configuration Reference

+++

* **Primary Script**: `tools/scripts/prepare_prompt.py`
* **Pre-commit Config**: `.pre-commit-config.yaml`
* **CI Config**: `.github/workflows/quality.yml`

+++

### Command Line Interface

+++

```bash
prepare_prompt.py <file> [--format yaml|plain] [--stdin] [--verbose]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `file` | Path to prompt JSON file | (required unless --stdin) |
| `--format` | Output format: yaml or plain | `yaml` |
| `--stdin` | Read input from stdin | `False` |
| `--verbose` | Show processing details | `False` |

**Exit Codes:**
- `0` = Success
- `1` = Error (file not found, invalid JSON, etc.)

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
|------|---------|
| **Basic usage** | `uv run tools/scripts/prepare_prompt.py prompt.json` |
| **Plain text output** | `uv run tools/scripts/prepare_prompt.py prompt.json --format plain` |
| **Stdin input** | `cat prompt.json \| uv run tools/scripts/prepare_prompt.py --stdin` |
| **Verbose mode** | `uv run tools/scripts/prepare_prompt.py prompt.json --verbose` |

+++

### Examples

```{code-cell}
cd ../../../
ls
```

1. Process a prompt file (YAML-like output):

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/prepare_prompt.py ai_system/3_prompts/consultants/devops_consultant.json 2>/dev/null | head -20
```

2. Extract plain text values only:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/prepare_prompt.py ai_system/3_prompts/consultants/devops_consultant.json --format plain 2>/dev/null | head -20
```

3. Process with verbose output:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/prepare_prompt.py ai_system/3_prompts/consultants/devops_consultant.json --verbose 2>&1 | head -5
```

## **5. Validation Layers**

+++

### Layer 1: Logic Tests Pre-commit Hook

+++

A meta-check ensures the script logic remains sound:

```yaml
- id: test-prepare-prompt
  name: Test Prepare Prompt script
  entry: uv run --active pytest tools/tests/test_prepare_prompt.py
  language: python
  files: ^tools/(scripts/prepare_prompt\.py|scripts/paths\.py|tests/test_prepare_prompt\.py)$
  pass_filenames: false
```

This triggers whenever the script, its tests, or shared configuration change.

+++

### Layer 2: GitHub Action (Continuous Integration)

+++

The CI pipeline in `quality.yml` runs the test suite when relevant files change:

```yaml
prepare-prompt:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v3
    - name: Get changed files
      id: changed
      uses: tj-actions/changed-files@v45
      with:
        files_yaml: |
          logic:
            - tools/scripts/prepare_prompt.py
            - tools/tests/test_prepare_prompt.py
            - tools/scripts/paths.py
    - name: Run Logic Tests
      if: steps.changed.outputs.logic_any_changed == 'true'
      run: uv run pytest tools/tests/test_prepare_prompt.py
```

+++

## **6. Test Suite Documentation**

+++

The script is accompanied by a comprehensive test suite (`test_prepare_prompt.py`) that ensures reliability.

+++

### Test Classes and Coverage

| Test Class | Purpose |
|------------|---------|
| `TestJsonHandler` | JSON parsing, metadata removal, format conversion, character stripping |
| `TestJsonHandlerVerbose` | Verbose output verification |
| `TestReporter` | Exit codes, output formatting |
| `TestPreparePromptCLI` | Integration tests for CLI modes and arguments |
| `TestPreparePromptCLIComplexJson` | Tests with realistic nested structures |

+++

### Key Test Scenarios

- **Valid JSON**: Objects, arrays, nested structures
- **Invalid JSON**: Syntax errors, empty files
- **Metadata Removal**: Verification that metadata is stripped
- **Character Stripping**: Special characters removed from output
- **Stdin Mode**: Reading from stdin
- **Format Modes**: Both yaml and plain output
- **Error Handling**: File not found, invalid JSON

+++

### Running the Tests

To run the full suite, execute from the repository root:

```bash
$ uv run pytest tools/tests/test_prepare_prompt.py
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_prepare_prompt.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_prepare_prompt.py --cov=. --cov-report=term-missing -q
```
