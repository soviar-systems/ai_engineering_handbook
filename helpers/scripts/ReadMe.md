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
Version: 0.2.0
Birth: 2025-12-20
Last Modified: 2025-12-30

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

1. **Locate the Scripts Directory**:
    - Determine the absolute path of the `helpers/scripts` directory.

    ```bash
    pwd
    ```

2. **Edit Your Shell Configuration File**:
    - Open your shell configuration file (e.g., `.bashrc` or `.bash_profile`) in a text editor.

    ```bash
    vim ~/.bashrc
    ```

4. **Add the Scripts Directory to PATH**
    - Add the following line to the end of your shell configuration file, replacing `/path/to/your/project/helpers/scripts` with the absolute path you obtained in step 1.

    ```bash
    export PATH=${PATH}:/path/to/your/project/helpers/scripts
    ```

4. **Apply the Changes**:
    - Reload your shell configuration file to apply the changes.

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

This script performs fast, local-only validation of relative file links (Markdown, image, etc.) within a directory and its subdirectories. It is built using the **Smallest Viable Architecture (SVA)** principle, relying exclusively on Python's standard library (`pathlib`, `re`, `sys`, `argparse`, `tempfile`) for maximum portability and zero external dependencies.

This tool is designed to serve as a high-quality diagnostic step in **AI Agent workflows** (like `aider` or custom SLMs), providing clear, parsable feedback to automate documentation maintenance.

**Features:**

* **Local-Only Policy:** Excludes external URLs (e.g., `https://` or `domain.com`) from checks, focusing only on local file integrity.
* **Intelligent Skipping:** Ignores non-file links such as bare word anchors (`[link](args)`) and internal fragments (`[section](#anchor)`).
* **Path Handling:** Correctly resolves relative paths (`./..`), absolute paths (relative to project root `/`), and handles platform differences transparently (thanks to `pathlib`).
* **Directory & File Exclusion:** Supports excluding specific directories (e.g., `drafts`) and files (e.g., `README.md`). Users can update default exclusions in the script itself.
* **Clear Reporting:** Outputs broken links with their source file path and link string, exiting with a non-zero status code on failure, ideal for CI/CD and automation.

+++

### Usage

+++

Synopsis:

```bash
check_broken_links.py [directory] [file_pattern] [options]
```

- **Required Arguments (Optional when using defaults)**:
  - `directory`: The root directory to start the search. Default is `.`.
  - `file_pattern`: The glob pattern to match Markdown files. Default is `*.md`.

- **Options**:
  - `--exclude-dirs`: Directory names to exclude from the check (e.g., `drafts temp`). Can list multiple names.
  - `--exclude-files`: Specific file names to exclude from the check (e.g., `README.md`). Can list multiple names.
  - `--verbose`: Enable verbose mode for more output information.

+++

### Default Exclusions

+++

You can update the default exclusions directly in the script. Open `check_broken_links.py` and modify the following lines:

```python
# Argument for Directory Exclusion
parser.add_argument(
    "--exclude-dirs",
    nargs="*",
    default=["in_progress", "pr", ".venv"],  # Add '.venv' here
    help="Directory names to exclude from the check (e.g., in_progress drafts temp)",
)

# Argument for File Exclusion
parser.add_argument(
    "--exclude-files",
    nargs="*",
    default=[".aider.chat.history.md"],
    help="Specific file names to exclude from the check (e.g., README.md LICENSE.md)",
)
```

Add or remove directory and file names as needed.

+++

### Examples

+++

1. Check all `*.md` files in the current directory and subdirectories:
    ```bash
    check_broken_links.py
    ```

2. Check all `*.txt` files recursively from the `./docs` directory:
    ```bash
    check_broken_links.py ./docs "*.txt"
    ```

3. Use verbose mode:
    ```bash
    check_broken_links.py --verbose
    ```

4. Use exclusions (if not updated in the script):
    ```bash
    check_broken_links.py --exclude-dirs drafts temp --exclude-files README.md
    ```

+++

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
