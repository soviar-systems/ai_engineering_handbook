---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Instruction on check_broken_links.py script

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.1.0  
Birth: 2026-01-07  
Last Modified: 2026-01-07

---

+++

This script performs fast, local-only validation of relative file links within a directory and its subdirectories. While optimized for Jupyter Notebooks (`.ipynb`), it can scan any Markdown-style links. 

This tool is designed to serve as a high-quality diagnostic step in CI/CD, providing clear, parsable feedback to automate documentation maintenance.

It adheres to the **Smallest Viable Architecture (SVA)** principle, using only the Python standard library.

:::{hint} **SVA = right tool for the job**
SVA isn’t about minimal *code* — it’s about **minimal *cognitive and operational overhead***.

- Our users already have Python.
- They can **edit the script directly** to tweak regex or logic.
- No build system, no dependencies, no virtual envs needed (you use only stdlib!).
- **CI/CD Ready**: Provides clear, parsable feedback and uses exit codes (`0` for success, `1` for failure) to integrate into automated pipelines.
:::

**Features:**

* **Local-Only Policy**: It intentionally ignores external `http/https` links to focus strictly on the integrity of local repository file paths.
* **Git Root Awareness**: The script attempts to find the Git project root using `git rev-parse --show-toplevel`. This allows it to correctly resolve "root-absolute" links (e.g., `/docs/images/logo.png`) relative to the repository base.
* **Intelligent Link Filtering**:
    * Skips internal fragments/anchors that don't point to other files (e.g., `[Go to top](#top)`).
    * Automatically handles URL escape characters and fragments in paths.
* **Directory & File Exclusion:** Automatically skips common noise directories like `.venv` and `.ipynb_checkpoints`.

+++

## Command Line Interface

+++

```bash
check_broken_links.py [paths] [--pattern PATTERN] [options]

```

| Argument | Description | Default |
| --- | --- | --- |
| `paths` | One or more directories to search or specific file paths. | `.` (Current Dir) |
| `--pattern` | Glob pattern for files to scan. | `*.ipynb` |
| `--exclude-dirs` | List of directory names to ignore. | `in_progress`, `pr`, `.venv` |
| `--exclude-files` | List of specific filenames to ignore. | `.aider.chat.history.ipynb` |
| `--verbose` | Shows detailed logs of skipped URLs and valid links. | `False` |

+++

### Default Exclusions

+++

You can update the default exclusions directly in the `LinkCheckerCLI` class within the script:

```python
class LinkCheckerCLI:
    DEFAULT_EXCLUDE_DIRS = ["in_progress", ".venv"]
    DEFAULT_EXCLUDE_FILES = [".aider.chat.history.md"]
```

+++

## Technical Architecture

+++

The script is organized into specialized classes to maintain clarity:

* **`FileFinder`**: Traverses the filesystem to collect files while respecting exclusion rules.
* **`LinkExtractor`**: Uses regular expressions (`r"\[[^\]]*\]\(([^)]+)\)"`) to identify Markdown links within file content.
* **`LinkValidator`**: Resolves link paths relative to the source file or the Git root and verifies their existence.
* **`Reporter`**: Aggregates findings and generates a final report, exiting with status code `1` if any broken links are found.

+++

## Examples

+++

1. Check all `*.md` files in the current directory and subdirectories:

```{code-cell}
check_broken_links.py
```

2. Check all `*.txt` files recursively from the `./docs` directory:

```{code-cell}
check_broken_links.py . --pattern "*.md"
```

3. Use exclusions (if not updated in the script):

```{code-cell}
check_broken_links.py --exclude-dirs drafts temp --exclude-files ReadMe.ipynb
```

4. Check the given file:

```{code-cell}
cd ../../
ls
```

```{code-cell}
check_broken_links.py 0_intro/00_onboarding.ipynb
```

4. Use verbose mode:

    ```bash
    check_broken_links.py --verbose
    ```

+++

Broken links output looks like this:

```{code-cell}
check_broken_links.py
```

## Test Suite

+++

The script is accompanied by a comprehensive test suite (`test_check_broken_links.py`) that ensures reliability across different file structures and link types.

The test suite for `check_broken_links.py` is a robust validation layer designed to ensure the script accurately identifies broken local references while ignoring external URLs and specific environment-related directories. It uses **pytest** and focuses on unit testing core logic and end-to-end CLI behavior.

+++

### Core Components Tested

+++

* **Link Extraction:** Verifies that Markdown-style links `[text](link)` and image links `![alt](image)` are correctly identified, including edge cases like empty files or files with encoding issues.
* **Validation Logic:**
* **Relative & Absolute Paths:** Ensures links like `file.ipynb` and `/project/root/file.ipynb` resolve correctly.
* **Directory Indexing:** Validates that links to a directory (e.g., `docs/`) are considered valid only if an `index.ipynb` or `README.ipynb` exists within it.
* **Exclusions:** Confirms that external URLs (`https://...`) and internal fragments (`#section`) are safely skipped.

* **File Discovery:**
* Tests the recursive search functionality.
* Ensures excluded directories (like `.venv` or `in_progress`) and auto-save folders (like `.ipynb_checkpoints`) are ignored.

* **CLI & Environment:**
* **Git Integration:** Mocks Git environments to test how the script determines the project root.
* **Cross-Platform Behavior:** Tests case-sensitivity (critical for Linux environments).
* **Exit Codes:** Ensures the script returns `0` for success and `1` when broken links are found, making it CI/CD friendly.

+++

### Running the Tests

+++

To run the full suite, ensure you have `pytest` installed and execute the following in your terminal:

```bash
pytest test_check_broken_links.py
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest . -q
```

### Key Test Scenarios Covered

+++

| Category | Scenario | Expected Result |
| --- | --- | --- |
| **Success** | Valid relative link to `.ipynb` or `.py` | Pass |
| **Success** | Link to directory containing `README.ipynb` | Pass |
| **Failure** | Link to a missing file | Fail (Broken Link detected) |
| **Failure** | Link to a directory without an index file | Fail (Broken Link detected) |
| **Edge Case** | Files with spaces in the name (un-encoded) | Handled via literal match |
| **Edge Case** | Binary or non-UTF-8 files | Skipped with warning |
