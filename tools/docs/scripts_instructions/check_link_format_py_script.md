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

# Instruction on check_link_format.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.1.0
Birth: 2026-01-24
Last Modified: 2026-01-26

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_link_format.py) validates link format in Markdown files, ensuring **ipynb priority** when a Jupytext pair exists.

When a `.md` file has a paired `.ipynb` file, links should point to the `.ipynb` version because `myst.yml` only renders `.ipynb` files. Links to `.md` files cause downloads instead of opening as web pages.

:::{important} **This Script Does NOT Check If Links Exist**
This script only validates link **format** — it checks whether `.md` links should be `.ipynb` when a Jupytext pair exists. It does **NOT** verify that link targets actually exist or are valid.

* **check_link_format.py** → validates link **format** (ipynb priority when pair exists)
* **check_broken_links.py** → validates link targets **exist**

Use both scripts for complete link validation.
:::

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero Dependencies**: Uses only the Python standard library (`pathlib`, `re`, `sys`, `argparse`, `tempfile`), ensuring it runs on any system with Python installed.
* **Check and Fix Modes**: Can validate without modification (check-only) or automatically fix detected issues.
* **High Portability**: Designed for local-only validation, making it ideal for air-gapped or high-security environments.
:::

+++

## **2. Key Capabilities & Logic**

+++

### Core Validation Logic

The script checks every link in `.md` files and flags an error when:

1. The link points to a `.md` file (e.g., `[Guide](path/to/file.md)`)
2. A paired `.ipynb` file exists (e.g., `path/to/file.ipynb`)

**Example:**
```text
# In source.md

[Guide](path/to/file.md)     # ERROR if path/to/file.ipynb exists
[Guide](path/to/file.ipynb)  # OK - correct format
[Readme](valid.md)           # OK if valid.ipynb does NOT exist
```

### Link Types Handled

**A. Markdown Links**

Standard syntax: `[text](link)` or `![alt](image)`.

* **Regex**: `r"\[[^\]]*\]\(([^)]+)\)"`

**B. MyST Include Directives**

Used for file transclusion:

* **Syntax**: ````{include} path/to/file.md ````
* **Regex**: `r"```\{include\}([^`\n]+)"`

### What Gets Skipped

* **External URLs**: `https://...`, `http://...`
* **Internal Fragments**: `#section`
* **Non-.md Links**: `image.png`, `data.json`, etc.
* **Excluded Link Strings**: Configured in `paths.py`

### Path Resolution

* **Git Root Awareness**: Uses `git rev-parse --show-toplevel` to resolve root-absolute links (e.g., `/docs/guide.md`)
* **Relative Paths**: Resolved relative to the source file
* **Root-Relative Paths**: Resolved from the Git root directory

+++

## **3. Technical Architecture**

+++

The script is organized into specialized classes:

* **`LinkFormatCLI`**: Main orchestrator. Handles argument parsing and execution flow.
* **`LinkExtractor`**: Scans file content line-by-line using regex to capture Markdown and MyST links.
* **`LinkFormatValidator`**: The core engine. Checks if `.md` links have paired `.ipynb` files.
* **`FileFinder`**: Handles recursive file traversal with exclusion logic.
* **`Reporter`**: Collects errors and handles exit codes.

+++

## **4. Operational Guide**

+++

### Configuration Reference

+++

* **Primary Script**: `tools/scripts/check_link_format.py`
* **Exclusion Logic**: Managed via `tools/scripts/paths.py` (reuses `BROKEN_LINKS_EXCLUDE_*` constants)
* **Pre-commit Config**: `.pre-commit-config.yaml`
* **CI Config**: `.github/workflows/quality.yml`

+++

### Command Line Interface

+++

```bash
check_link_format.py [--paths PATH] [--pattern PATTERN] [--fix | --fix-all] [options]

```

| Argument | Description | Default |
| --- | --- | --- |
| `--paths` | One or more directories or specific file paths to scan. | `.` (Current Dir) |
| `--pattern` | Glob pattern for files to scan. | `*.md` |
| `--exclude-dirs` | List of directory names to ignore. | `in_progress`, `pr`, `.venv` |
| `--exclude-files` | List of specific filenames to ignore. | `.aider.chat.history.md` |
| `--verbose` | Shows detailed logs of skipped URLs and valid links. | `False` |
| `--fix` | Interactive fix mode - asks for confirmation before fixing each file. | `False` |
| `--fix-all` | Automatic fix mode - fixes all errors without prompts. | `False` |

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
| --- | --- |
| **Full Repo Audit** | `uv run tools/scripts/check_link_format.py` |
| **Scan Specific Directory** | `uv run tools/scripts/check_link_format.py --paths ai_system/` |
| **Verbose Mode** | `uv run tools/scripts/check_link_format.py --verbose` |
| **Interactive Fix** | `uv run tools/scripts/check_link_format.py --fix` |
| **Automatic Fix All** | `uv run tools/scripts/check_link_format.py --fix-all` |

+++

### Examples

```{code-cell}
cd ../../../
```

1. Check all `*.md` files in the current directory and subdirectories:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/check_link_format.py 2>&1 | tail -15
```

2. Check a specific directory with verbose output:

```bash
env -u VIRTUAL_ENV uv run tools/scripts/check_link_format.py --paths tools/docs --verbose 2>&1 | head -20
```

+++

3. Check a specific file:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/check_link_format.py --paths README.md
```

## **5. Validation Layers**

+++

### Layer 1: Local Pre-commit Hook

+++

The first line of defense runs automatically during the `git commit` process.

* **Scope**: All `.md` files are validated to ensure consistent link format across the repository.
* **Efficiency**: Fast execution ensures no significant delay in the developer's workflow.
* **Logic Tests**: Includes a meta-check (`test-check-link-format`) that triggers whenever the script itself or its tests change.

+++

### Layer 2: GitHub Action (Continuous Integration)

+++

The CI pipeline in `quality.yml` validates **ALL** `.md` files when any documentation changes.

* **Full Repository Scan**: When any `.md` file changes, the workflow scans ALL `.md` files.
* **Trigger Optimization**: Uses `tj-actions/changed-files` to detect when docs change.
* **Environment Parity**: Utilizes `uv` for high-performance dependency management.
* **Failure Isolation**: Separates logic tests from format validation.

:::{tip} `quality.yml` Implementation:
```yaml
link-format:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        enable-cache: true
    - name: Get changed files
      id: changed
      uses: tj-actions/changed-files@v45
      with:
        files_yaml: |
          logic:
            - tools/scripts/check_link_format.py
            - tools/tests/test_check_link_format.py
            - tools/scripts/paths.py
          docs:
            - "**/*.md"
        safe_output: true
    - name: Run Logic Tests
      if: steps.changed.outputs.logic_any_changed == 'true'
      run: uv run pytest tools/tests/test_check_link_format.py
    - name: Run Link Format Check on All Files
      if: steps.changed.outputs.docs_any_changed == 'true'
      run: uv run tools/scripts/check_link_format.py --verbose
```
:::

+++

### Layer 3: Manual Checks

+++

Used for deep repository audits or post-refactoring cleanup.

* **Full Scan**: Can be executed manually to scan the entire repository.
* **Custom Patterns**: Supports custom file patterns and exclusion lists.

+++

## **6. Error Output Format**

+++

When errors are found, the script outputs:

```
LINK FORMAT ERROR: File 'docs/guide.md:15' links to 'intro.md' but paired .ipynb exists.
  Suggested fix: Change to 'intro.ipynb'
```

The error message includes:
* **Source file and line number**: Where the problematic link is located
* **Current link**: The `.md` link that should be changed
* **Suggested fix**: The correct `.ipynb` link to use

+++

## **7. Auto-Fix Functionality**

+++

The script can automatically fix detected link format issues using two modes:

### Interactive Mode (`--fix`)

Prompts for confirmation before fixing each file:

```
File: ai_system/2_model/selection/choosing_model_size.md
  Line 33: /ai_system/4_orchestration/patterns/llm_usage_patterns.md → .ipynb

Fix this file? [y/n/q] (q=quit):
```

* **y**: Fix all issues in this file
* **n**: Skip this file
* **q**: Quit and stop processing remaining files

### Automatic Mode (`--fix-all`)

Fixes all errors without prompts - useful for CI pipelines or batch processing:

```bash
uv run tools/scripts/check_link_format.py --fix-all
```

### Fix Output

After fixing, the script reports:
* Total fixes applied
* Files modified
* Any skipped files (in interactive mode)

```
✅ Fixed all 5 link format errors.
```

or in interactive mode:

```
✓ Fixed 3/5 link format errors.
  Skipped: 2
```

+++

## **8. Test Suite**

+++

The script is accompanied by a comprehensive test suite (`test_check_link_format.py`) with 42 tests covering:

* **Link Extraction**: Verifies Markdown and MyST links are correctly identified
* **Format Validation**: Tests the core logic for detecting `.md` links with `.ipynb` pairs
* **File Discovery**: Tests recursive search and exclusion logic
* **CLI Integration**: End-to-end tests for command-line behavior
* **Fix Functionality**: Tests for `LinkFixer` class and fix modes (`--fix`, `--fix-all`)
* **Edge Cases**: External URLs, fragments, excluded paths

+++

### Running the Tests

+++

```bash
# Run all tests
uv run pytest tools/tests/test_check_link_format.py

# Run with coverage
uv run pytest tools/tests/test_check_link_format.py --cov=tools.scripts.check_link_format --cov-report=term-missing
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_link_format.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_link_format.py --cov=. --cov-report=term-missing -q
```
