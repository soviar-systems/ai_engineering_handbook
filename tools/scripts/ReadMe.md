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

# Instructions for Scripts in `helpers/scripts`

+++

-----

Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.2.1
Birth: 2025-12-20
Last Modified: 2026-01-05

-----

+++

## Overview

+++

This directory contains various utility scripts designed to automate common tasks within the AI Engineering Handbook project. Each script is written in Python and can be executed from the GNU/Linux command line. Below are the general steps to make a script executable and how to run it, along with specific instructions for each script.

+++

## How to use scripts on GNU/Linux

```{code-cell}
grep -i 'pretty' /etc/os-release
```

### Make a Script Executable

+++

1. **Navigate to the Directory**: Open your terminal and navigate to the directory where the script is located.

```bash
cd path/to/your/project/helpers/scripts
```

2. **Make the Scripts Executable**: Run the following command to make all the scripts in this directory and its children executable.

```bash
find . -type f -name '*.py' -exec chmod 0755 {} +
```

This approach ensures that all Python scripts in the directory tree are made executable with the appropriate permissions (`0755`).

+++

### Add Scripts to `PATH`

+++

1. **Locate the Scripts Directory**: Obtain the absolute path using `pwd`.
1. **Edit Your Shell Configuration**: Open your `.bashrc` or `.bash_profile`.
1. **Add to PATH**: Add the following line:
    ```bash
    export PATH=${PATH}:/path/to/your/project/helpers/scripts
    ```

1. **Apply the Changes**: Reload your shell configuration file to apply the changes.
    ```bash
    source ~/.bashrc
    ```

+++

### Run a Script

+++

Once the script is executable and added to your `PATH`, you can run it from any directory by providing any necessary arguments as required by the script.

```bash
script_name.py [arguments]
```

Replace `script_name.py` with the actual name of your script and `[arguments]` with any required or optional arguments.

+++

### Troubleshooting

+++

- **Permission Denied**: If you encounter a "Permission denied" error when trying to run the script, ensure that you have made it executable using the `chmod 0755` command.

- **Syntax Errors**: If you encounter syntax errors, make sure that your Python environment is correctly set up and that the script is compatible with your version of Python.

+++

## 1. check_broken_links.py

+++

This script performs fast, local-only validation of relative file links within a directory and its subdirectories. While optimized for Jupyter Notebooks (`.ipynb`), it can scan any Markdown-style links. 

This tool is designed to serve as a high-quality diagnostic step in CI/CD, providing clear, parsable feedback to automate documentation maintenance.

It adheres to the **Smallest Viable Architecture (SVA)** principle, using only the Python standard library.

:::{hint} **SVA = right tool for the job**
SVA isn’t about minimal *code* — it’s about **minimal *cognitive and operational overhead***.

- Our users already have Python.
- They can **edit the script directly** to tweak regex or logic.
- No build system, no dependencies, no virtual envs needed (you use only stdlib!).
:::

**Features:**

* **Local-Only Policy:** Excludes external `http/https` URLs to focus on local repository integrity.
* **Git Root Awareness:** Automatically detects the Git project root to resolve absolute paths (e.g., `/docs/image.png`).
* **Intelligent Skipping:** Ignores internal anchors and fragments that do not contain path separators.
* **Directory & File Exclusion:** Automatically skips common noise directories like `.venv` and `.ipynb_checkpoints`.

+++

### Usage

+++

Synopsis:

```bash
check_broken_links.py [paths] [--pattern PATTERN] [options]
```

* **Arguments**:
* `paths`: The directory or specific file to search. Default is `.`.
* `--pattern`: The glob pattern to match files. **Default is `*.ipynb**`.


* **Options**:
* `--exclude-dirs`: Directories to skip (default: `in_progress`, `pr`, `.venv`).
* `--exclude-files`: Specific files to skip (default: `.aider.chat.history.ipynb`).
* `--verbose`: Shows detailed logs of skipped URLs and valid links.

+++

### Default Exclusions

+++

You can update the default exclusions directly in the `LinkCheckerCLI` class within the script:

```python
class LinkCheckerCLI:
    DEFAULT_EXCLUDE_DIRS = ["in_progress", "pr", ".venv"]
    DEFAULT_EXCLUDE_FILES = [".aider.chat.history.ipynb"]
```

+++

### Examples

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

## 2. format_string.py

+++

This script formats a given input string by applying several transformations to make it URL-safe and filesystem-friendly. The transformations include converting to lowercase, replacing specific special characters, removing unwanted words, and truncating the string if necessary.

### Usage

Synopsis:

```bash
format_string.py 'Your Input String'
```

### Transformation Logic

1. **Convert to Lowercase**: All characters in the input string are converted to lowercase.
2. **Replace & with and**: The ampersand (`&`) is replaced with the word "and".
3. **Remove Special Symbols**: Certain special symbols (e.g., "the ", "(", ")", "# ", "#", "`", "~", "$", "%", "@") are removed from the string.
4. **Replace Special Symbols with Underscores**: Other special symbols (e.g., ".", ",", ";", ":", "!", "?", "-", "/", "\\", "|", "<", ">", "*") are replaced with underscores (`_`).
5. **Remove Multiple Underscores**: Any sequence of multiple underscores is reduced to a single underscore.
6. **Replace Spaces with Underscores**: All spaces in the string are replaced with underscores.
7. **Truncate Long Strings**: If the resulting string exceeds 50 characters, it is truncated to 50 characters.
8. **Remove Trailing Underscore**: If the final character of the string is an underscore, it is removed.

### Examples

```{code-cell}
format_string.py 'Agents4Science Conference Paper Digest: How Agents Are "Doing" Science Right Now'
```

```{code-cell}
format_string.py '# Post-Mortem: Architectural Flaws in the `nbdiff`-Centric Jupyter Version Control Handbook'
```

```{code-cell}
format_string.py 'Feedforward Neural Networks in Depth, Part 3 Cost Functions | I, Deep Learning.pdf'
```

```{code-cell}
format_string.py 'From Concepts to Code: Introduction to Data Science (2024)'
```

```{code-cell}
format_string.py 'Quiz - Special Applications: Face Recognition & Neural Style Transfer'
```
