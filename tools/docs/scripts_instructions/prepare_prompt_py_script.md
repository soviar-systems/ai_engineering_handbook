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
Version: 0.3.0
Birth: 2026-01-25
Last Modified: 2026-01-26

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/prepare_prompt.py) prepares prompt files (["Layer 3: Prompts-as-Infrastructure"](/ai_system/3_prompts/)) for LLM consumption by removing metadata, stripping special characters, and converting to a YAML-like output format.

This tool is designed to transform structured prompt files into clean, readable formats suitable for copying into LLM interfaces or automated prompt injection. It supports multiple input formats with automatic detection based on file extension.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Minimal Dependencies**: Uses Python standard library plus `pyyaml` for YAML parsing.
* **Multi-Format Support**: Handles JSON, YAML, TOML, Markdown (with frontmatter), and plain text.
* **Auto-Detection**: Automatically detects input format from file extension.
* **Multiple Output Formats**: Supports YAML-like (default) and plain text extraction.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. Supported Input Formats

The script auto-detects format from file extension:

| Extension | Format | Parser |
|-----------|--------|--------|
| `.json` | JSON | `json.loads()` |
| `.yaml`, `.yml` | YAML | `yaml.safe_load()` |
| `.toml` | TOML | `tomllib.loads()` (stdlib) |
| `.md` | Markdown | YAML frontmatter + body extraction |
| `.txt` | Plain Text | Pass-through wrapper |

+++

### B. Processing Operations

| Operation | Description |
|-----------|-------------|
| **Metadata Removal** | Removes the `metadata` field/table from structured data |
| **Character Stripping** | Removes `*`, `'`, `"`, `` ` ``, `#` from output (preserves `*` in math expressions) |
| **YAML Conversion** | Converts data structure to YAML-like indented format |
| **Plain Text Extraction** | Optionally extracts only text values |

+++

### C. Math Expression Preservation

The script uses context-aware character stripping to preserve multiplication operators in mathematical expressions:

| Pattern | Example | Preserved |
|---------|---------|-----------|
| `var * num` | `E * 0.35` | ✓ |
| `num * var` | `0.35 * E` | ✓ |
| `num * num` | `0.35 * 0.25` | ✓ |

This ensures formulas like `WRC = (E * 0.35) + (A * 0.25)` remain meaningful rather than becoming `WRC = (E  0.35) + (A  0.25)`.

Formatting characters (`**bold**`, `` `code` ``) are still stripped as they are visual noise for LLM consumption.

+++

### D. Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `yaml` (default) | YAML-like key: value structure | Copying to LLM interfaces |
| `plain` | Text values only, newline-separated | Automated processing |

+++

## **3. Technical Architecture**

+++

The script uses a handler-based architecture with format auto-detection:

| Class | Responsibility |
|-------|----------------|
| `FormatDetector` | Detect input format from file extension or explicit flag |
| `InputHandler` (ABC) | Base class with shared output methods (`to_yaml_like`, `to_plain_text`) |
| `JsonHandler` | Parse JSON input |
| `YamlHandler` | Parse YAML input |
| `TomlHandler` | Parse TOML input |
| `MarkdownHandler` | Extract YAML frontmatter and body from Markdown |
| `PlainTextHandler` | Pass-through for plain text |
| `HandlerFactory` | Create appropriate handler based on format |
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
prepare_prompt.py <file> [--input-format FORMAT] [--output-format yaml|plain] [--stdin] [--verbose]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `file` | Path to prompt file (JSON, YAML, TOML, Markdown, or text) | (required unless --stdin) |
| `--input-format` | Input format: json, yaml, toml, markdown, text | Auto-detected from extension |
| `--output-format` | Output format: yaml or plain | `yaml` |
| `--stdin` | Read input from stdin (defaults to JSON) | `False` |
| `--verbose` | Show processing details | `False` |

**Exit Codes:**
- `0` = Success
- `1` = Error (file not found, invalid format, etc.)

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
|------|---------|
| **JSON file** | `uv run tools/scripts/prepare_prompt.py prompt.json` |
| **YAML file** | `uv run tools/scripts/prepare_prompt.py config.yaml` |
| **TOML file** | `uv run tools/scripts/prepare_prompt.py config.toml` |
| **Markdown file** | `uv run tools/scripts/prepare_prompt.py doc.md` |
| **Plain text output** | `uv run tools/scripts/prepare_prompt.py prompt.json --output-format plain` |
| **Override detection** | `uv run tools/scripts/prepare_prompt.py data.txt --input-format yaml` |
| **Stdin (JSON)** | `cat prompt.json \| uv run tools/scripts/prepare_prompt.py --stdin` |
| **Stdin (YAML)** | `cat config.yaml \| uv run tools/scripts/prepare_prompt.py --stdin --input-format yaml` |
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
env -u VIRTUAL_ENV uv run tools/scripts/prepare_prompt.py ai_system/3_prompts/consultants/devops_consultant.json --output-format plain 2>/dev/null | head -20
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
| `TestFormatDetector` | Extension detection, explicit format override |
| `TestInputHandler` | Abstract base class verification |
| `TestJsonHandler` | JSON parsing, metadata removal, format conversion |
| `TestJsonHandlerVerbose` | Verbose output verification |
| `TestYamlHandler` | YAML parsing, metadata removal |
| `TestTomlHandler` | TOML parsing, metadata removal |
| `TestMarkdownHandler` | Frontmatter extraction, metadata removal |
| `TestPlainTextHandler` | Pass-through behavior |
| `TestHandlerFactory` | Handler creation for each format |
| `TestReporter` | Exit codes, output formatting |
| `TestPreparePromptCLI` | Integration tests for CLI modes |
| `TestPreparePromptCLIComplexJson` | Tests with realistic nested structures |
| `TestPreparePromptCLIInputFormats` | Multi-format integration tests |
| `TestMathPreservation` | Math operator preservation, formatting stripping |

+++

### Key Test Scenarios

- **Format Detection**: Auto-detect from extension, explicit override
- **All Input Formats**: JSON, YAML, TOML, Markdown, plain text
- **Invalid Input**: Syntax errors for each format
- **Metadata Removal**: Verification across all formats
- **Character Stripping**: Special characters removed from output
- **Math Preservation**: Multiplication operators preserved in formulas (`E * 0.35`)
- **Stdin Mode**: Reading from stdin with format specification
- **Output Formats**: Both yaml and plain output
- **Error Handling**: File not found, invalid format

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
