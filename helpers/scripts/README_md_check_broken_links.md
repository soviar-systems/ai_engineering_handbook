# README: Markdown Local Link Checker

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-16  
Last Modified: 2025-12-16

-----

## Overview

This script performs fast, local-only validation of relative file links (Markdown, image, etc.) within a directory of Markdown files. It is built using the **Smallest Viable Architecture (SVA)** principle, relying exclusively on Python's standard library (`pathlib`, `re`, `sys`, `argparse`, `tempfile`) for maximum portability and zero external dependencies.

This tool is designed to serve as a high-quality diagnostic step in **AI Agent workflows** (like `aider` or custom SLMs), providing clear, parsable feedback to automate documentation maintenance. 

## Features

* **Local-Only Policy:** Excludes external URLs (e.g., `https://` or `domain.com`) from checks, focusing only on local file integrity.
* **Intelligent Skipping:** Ignores non-file links such as bare word anchors (`[link](args)`) and internal fragments (`[section](#anchor)`).
* **Path Handling:** Correctly resolves relative paths (`./..`), absolute paths (relative to project root `/`), and handles platform differences transparently (thanks to `pathlib`).
* **Directory & File Exclusion:** Supports excluding specific directories (e.g., `drafts`) and files (e.g., `README.md`).
* **Clear Reporting:** Outputs broken links with their source file path and link string, exiting with a non-zero status code on failure, ideal for CI/CD and automation.

## Usage

Run the script from your project's root directory:

```bash
python3 helpers/md_check_broken_links.py [directory] [file_pattern] [options]
````

Real example:

```
$ python3 helpers/md_check_broken_links.py
Found 25 markdown files in /home/user/ai_engineering_book

❌ 4 Broken links found:
BROKEN LINK: File '4_orchestration/workflows/release_notes_generation/slm_backed_release_documentation_pipeline_architecture.md' contains broken link: ./images/ai_assisted_doc_flow_1.png
BROKEN LINK: File '4_orchestration/workflows/release_notes_generation/post-mortem_slm_non-determinism_in_commit_generation.md' contains broken link: ./git_production_workflow_standards.md
BROKEN LINK: File '4_orchestration/workflows/release_notes_generation/post-mortem_slm_non-determinism_in_commit_generation.md' contains broken link: ./tools_commit_and_changelog_tooling_for_release_pipelines.md
BROKEN LINK: File '4_orchestration/workflows/release_notes_generation/post-mortem_slm_non-determinism_in_commit_generation.md' contains broken link: ./production_git_workflow_standards.md
```

### Required Arguments (Optional when using defaults)

| Argument | Default | Description |
| :--- | :--- | :--- |
| `directory` | `.` | The root directory to start the search. |
| `file_pattern` | `*.md` | The glob pattern to match markdown files (e.g., `*.md`, `**.txt`). |

### Examples

| Command | Description |
| :--- | :--- |
| `python3 helpers/md_check_broken_links.py` | Check all `*.md` files in the current directory and subdirectories. |
| `python3 helpers/md_check_broken_links.py ./docs` | Check all `*.md` files inside the `./docs` directory. |
| `python3 helpers/md_check_broken_links.py . "*.txt"` | Check all `*.txt` files recursively from the current directory. |

## Options

### 1\. Exclusion Options

Use these options to prevent checking files or directories you know contain incomplete work or are not meant for link validation.

| Option | Shorthand | Default | Description |
| :--- | :--- | :--- |
| `--exclude-dirs` | N/A | `in_progress pr` | Directory names to exclude (e.g., `drafts temp`). Can list multiple names. |
| `--exclude-files` | N/A | `.aider.chat.history.md` | Specific file names to exclude (e.g., `LICENSE.md`). Can list multiple names. |

**Example using exclusions:**

```bash
python3 helpers/md_check_broken_links.py --exclude-dirs drafts temp --exclude-files README.md
```

### 2\. Verbose Mode

| Option | Shorthand | Default | Description |
| :--- | :--- | :--- |
| `--verbose` | N/A | `False` | Prints every file checked, every link skipped, and every successful link resolution (`OK: link -> target`). Highly recommended for debugging. |

**Example using verbose mode:**

```bash
python3 helpers/md_check_broken_links.py --verbose
```

## Exit Codes

| Code | Status | Description |
| :--- | :--- | :--- |
| `0` | Success | `✅ All links are valid!` |
| `1` | Failure | `❌ [N] Broken links found:` (Followed by detailed report) |
