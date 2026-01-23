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

# Instruction on check_broken_links.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com  
Version: 0.4.1  
Birth: 2026-01-07  
Last Modified: 2026-01-24

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_broken_links.py) performs fast validation of relative file links within a directory and its subdirectories. While optimized for Markdown files (`.md`), it can scan any file containing Markdown-style links (e.g., `.ipynb`). 

This tool is designed to serve as a high-quality diagnostic step in CI/CD, providing clear, parsable feedback to automate documentation maintenance.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
SVA isn’t about minimal *code* — it’s about **minimal *cognitive and operational overhead***.

* **Zero Dependencies**: Uses only the Python standard library (`pathlib`, `re`, `sys`, `argparse`, `tempfile`), ensuring it runs on any system with Python installed.
* **Idempotency**: Operates on a "Check vs. Fix" logic—validating state without modifying existing files.
* **High Portability**: Designed for local-only validation of relative filesystem links, making it ideal for air-gapped or high-security environments.
:::

+++

### Key Architectural Improvements in v0.4.0

+++

The script handles the MyST type of links:

````{include} path/to/file.md ````

+++

## **2. Key Capabilities & Logic**

+++

The script identifies and validates three distinct types of references:

**A. Markdown Links**

Standard syntax: `[text](link)` or `![alt](image)`.

* **Regex**: `r"\[[^\]]*\]\(([^)]+)\)"`

**B. MyST Include Directives**

Used for file transclusion. The script identifies targets within MyST code blocks.

* **Syntax**: ````{include} path/to/file.md ````
* **Regex**: `r"```\{include\}([^`\n]+)"`
* **Special Handling**: The script automatically strips a single leading space (common in MyST formatting) to ensure the path resolves correctly.

**C. Directory Resolution**

If a link points to a directory (e.g., `[Intro](./intro/)`), the validator marks it as **valid** only if the directory contains an index file:

1. `index.ipynb`
2. `README.ipynb`

**Other features:**

* **Git Root Awareness**: The script attempts to find the Git project root using `git rev-parse --show-toplevel`. This allows it to correctly resolve "root-absolute" links (e.g., `/docs/images/logo.png`) relative to the repository base.
* **Resolution Logic**:
    * **Relative Paths**: Resolved relative to the source file.
    * **Root-Relative Paths**: Resolved starting from the Git root directory.
* **Directory Links**: Validates that a directory exists and contains an index file (e.g., `README.ipynb`).
* **Skips**: Automatically ignores external URLs (`https://...`), email links (`mailto:`), and internal document fragments (`#anchor`).
* **Directory & File Exclusion:** Automatically skips common noise directories like `.venv` and `.ipynb_checkpoints`.

+++

## **3. Technical Architecture**

+++

The script is organized into specialized classes to maintain clarity:

* **`FileFinder`**: Handles recursive traversal. Implements exclusion logic for `.ipynb_checkpoints` and user-defined patterns.
* **`LinkExtractor`**: Scans file content line-by-line using regex. It captures both standard Markdown and `{include}` patterns.
* **`LinkValidator`**: The core engine. It determines if a link is an external URL, a fragment, or a local path, then resolves it against the filesystem.
* **`Reporter`**: Collects `BROKEN LINK` strings into a temporary file and exits with `code 1` if the file is non-empty.

+++

## **4. Operational Guide**

+++

### Configuration Reference

+++

* **Primary Script**: `tools/scripts/check_broken_links.py`
* **Exclusion Logic**: Managed via `tools/scripts/paths.py` (e.g., ignoring `.venv`, `in_progress/`, and `.ipynb_checkpoints`).
* **Pre-commit Config**: `.pre-commit-config.yaml`
* **CI Config**: `.github/workflows/quality.yml`

+++

### Command Line Interface

+++

```bash
check_broken_links.py [--paths PATH] [--pattern PATTERN] [options]

```

| Argument | Description | Default |
| --- | --- | --- |
| `--paths` | One or more directories or specific file paths to scan. | `.` (Current Dir) |
| `--pattern` | Glob pattern for files to scan. | `*.md` |
| `--exclude-dirs` | List of directory names to ignore. | `in_progress`, `pr`, `.venv` |
| `--exclude-files` | List of specific filenames to ignore. | `.aider.chat.history.ipynb` |
| `--verbose` | Shows detailed logs of skipped URLs and valid links. | `False` |

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
| --- | --- |
| **Full Repo Audit (all .md)** | `uv run tools/scripts/check_broken_links.py` |
| **Scan Specific Directories** | `uv run tools/scripts/check_broken_links.py --paths tools/docs/ architecture/` |
| **Scan Multiple Files** | `uv run tools/scripts/check_broken_links.py --paths file1.md file2.md` |
| **Notebook Audit** | `uv run tools/scripts/check_broken_links.py --pattern "*.ipynb"` |

+++

### Examples

```{code-cell}
cd ../../../
```

1. Check all `*.md` files in the current directory and subdirectories:

```{code-cell}
check_broken_links.py
```

2. Check all `*.ipynb` files recursively from the `tools/docs` directory:

```{code-cell}
check_broken_links.py --paths tools/docs --pattern "*.ipynb"
```

3. Use exclusions (default exclusion are overidden, so be careful):

```{code-cell}
check_broken_links.py --exclude-dirs 4_orchestration in_porgress --exclude-files README.ipynb | head -n 10
```

4. Check the given file:

```{code-cell}
check_broken_links.py --paths 0_intro/00_onboarding.ipynb
```

```{code-cell}
check_broken_links.py --paths 0_intro/00_onboarding.ipynb README.md
```

4. Use verbose mode:

    ```bash
    check_broken_links.py --verbose
    ```

+++

## **5. Validation Layers**

+++

### Layer 1: Local Pre-commit Hook (Delta Validation)

+++

The first line of defense runs automatically during the `git commit` process to prevent broken links from entering the history.

* **Scope**: All `.md` files are validated because if the developer changes their file name other files will not be able to reach it, so the developer must fix all the links they have broken.
* **Efficiency**: Fast execution ensures no significant delay in the developer's workflow.
* **Logic Tests**: Includes a meta-check (`test-check-broken-links`) that triggers whenever the script itself or its tests change, ensuring the tool's logic remains sound.

+++

### Layer 2: GitHub Action (Continuous Integration)

+++

The CI pipeline in `quality.yml` validates **ALL** `.md` files when any documentation changes, ensuring renamed or moved files don't break links across the repository.

* **Full Repository Scan**: When any `.md` file changes, the workflow scans ALL `.md` files — not just the changed ones. This catches broken links in unchanged files that reference renamed/moved files.
* **Trigger Optimization**: Uses `tj-actions/changed-files` to detect when docs change, but runs the full scan to ensure consistency with the pre-commit hook.
* **Environment Parity**: Utilizes `uv` for high-performance dependency and environment management, mirroring the local development stack.
* **Failure Isolation**: Separates logic tests from link validation to pinpoint exactly where a failure occurs.

:::{tip} `quality.yml` Implementation:
```yaml
      - name: Get changed files
        id: changed
        uses: tj-actions/changed-files@v45
        with:
          files_yaml: |
            logic:
              - tools/scripts/check_broken_links.py
              - tools/tests/test_check_broken_links.py
              - tools/scripts/paths.py
            docs:
              - "**/*.md"
          safe_output: true

      - name: Run Logic Tests
        if: steps.changed.outputs.logic_any_changed == 'true'
        run: uv run pytest tools/tests/test_check_broken_links.py

      - name: Run Link Check on All Files
        if: steps.changed.outputs.docs_any_changed == 'true'
        run: uv run tools/scripts/check_broken_links.py --verbose
```

*Note: The workflow triggers on doc changes but scans ALL files to match pre-commit behavior.*
:::

+++

### Layer 3: Manual Infrastructure Checks

+++

Used for deep repository audits or post-refactoring cleanup.

* **Full Scan**: Can be executed manually to scan the entire repository or specific directories.
* **Custom Patterns**: Supports custom file patterns (e.g., scanning `.md` or `.rst` files) and exclusion lists.

+++

### CI Workflow Diagram

+++

```mermaid
---
config:
  layout: dagre
  theme: redux
---
flowchart TB
 subgraph Local_Dev["Local Development (Developer Machine)"]
        B["Git Commit"]
        A["Edit .ipynb Files"]
        C{"test-check-broken-links"}
        D{"check-broken-links"}
        E["Git Push"]
        C_Fix["Fix Script Logic"]
        D_Fix["Fix Staged Links"]
  end
 subgraph Quality_Job_Steps["quality.yml: validate_broken_links (Sequential)"]
        G1["Step 1: Checkout"]
        G2["Step 2: Install uv"]
        G3["Step 3: Detect paths.py &<br>check_broken_links changes"]
        G4{"Step 4: Run Logic Tests<br>(if script/paths.py changed)"}
        G5["Step 5: Detect jupytext changes"]
        G6{"Step 6: Run Jupytext Tests<br>(if scripts/paths.py changed)"}
        G7["Step 7: Get Changed .md Files"]
        G8{"Step 8: Run Link Check<br>(on ALL .md files)"}
        H_Stop["Job Stops: Logic Regression"]
        J["PR Blocked / Red X"]
        K["PR Quality Check Green"]
  end
    A --> B
    B --> C
    C -- Pass --> D
    D -- Pass --> E
    C -- Fail --> C_Fix
    C_Fix --> B
    D -- Fail --> D_Fix
    D_Fix --> B
    E --> F["GitHub Repository"]
    G1 --> G2
    G2 --> G3
    G3 --> G4
    G4 -- Pass --> G5
    G4 -- Fail --> H_Stop
    G5 --> G6
    G6 -- Pass --> G7
    G6 -- Fail --> H_Stop
    G7 --> G8
    G8 -- Fail --> J
    G8 -- Pass --> K
    F --> G1

    B@{ shape: event}
    E@{ shape: event}
    G4@{ shape: decision}
    G6@{ shape: decision}
    G8@{ shape: decision}
    style D fill:#9f9,stroke:#333
    style E fill:#9f9,stroke:#333
    style C_Fix fill:#f96,stroke:#333
    style D_Fix fill:#f96,stroke:#333
    style G7 fill:#9f9,stroke:#333
    style H_Stop fill:#f96,stroke:#333
    style J fill:#f96,stroke:#333
    style K fill:#9f9,stroke:#333
```

+++

## **Test Suite**

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

To run the full suite, ensure you have `pytest` installed and execute the following in your terminal from the repo's root dir:

```bash
$ uv run pytest path/to/test_check_broken_links.py
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_broken_links.py -q
```
