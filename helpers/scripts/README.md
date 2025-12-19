# Instructions for Scripts in `helpers/scripts`

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-20  
Last Modified: 2025-12-20

-----

## Overview

This directory contains various utility scripts designed to automate common tasks within the AI Engineering Book project. Each script is written in Python and can be executed from the GNU/Linux command line. Below are the general steps to make a script executable and how to run it, along with specific instructions for each script.

## Make a Script Executable

1. **Navigate to the Directory**: Open your terminal and navigate to the directory where the script is located.

```bash
cd path/to/your/project/helpers/scripts
```

2. **Make the Scripts Executable**: Run the following command to make all the scripts executable.

```bash
find . -type f -name '*.py' -exec chmod 0755 {} +
```

This approach ensures that all Python scripts in the directory tree are made executable with the appropriate permissions (`0755`).

## Add Scripts to `PATH`

1. **Locate the Scripts Directory**: Determine the absolute path of the `helpers/scripts` directory.

```bash
pwd
```

2. **Edit Your Shell Configuration File**: Open your shell configuration file (e.g., `.bashrc` or `.bash_profile`) in a text editor.

```bash
vim ~/.bashrc
```

3. **Add the Scripts Directory to PATH**: Add the following line to the end of your shell configuration file, replacing `/path/to/your/project/helpers/scripts` with the absolute path you obtained in step 1.

```bash
export PATH=${PATH}:/path/to/your/project/helpers/scripts
```

4. **Apply the Changes**: Reload your shell configuration file to apply the changes.

```bash
source ~/.bashrc
```

## Run a Script

1. **Execute the Script**: Once the script is executable and added to your `PATH`, you can run it from any directory by providing any necessary arguments as required by the script.

```bash
script_name.py [arguments]
```

Replace `script_name.py` with the actual name of your script and `[arguments]` with any required or optional arguments.

## Script-Specific Instructions

### 1. `md_check_broken_links.py`

**Purpose**: This script performs fast, local-only validation of relative file links (Markdown, image, etc.) within a directory and its subdirectories. It is built using the **Smallest Viable Architecture (SVA)** principle, relying exclusively on Python's standard library (`pathlib`, `re`, `sys`, `argparse`, `tempfile`) for maximum portability and zero external dependencies.

This tool is designed to serve as a high-quality diagnostic step in **AI Agent workflows** (like `aider` or custom SLMs), providing clear, parsable feedback to automate documentation maintenance. 

**Features:**

* **Local-Only Policy:** Excludes external URLs (e.g., `https://` or `domain.com`) from checks, focusing only on local file integrity.
* **Intelligent Skipping:** Ignores non-file links such as bare word anchors (`[link](args)`) and internal fragments (`[section](#anchor)`).
* **Path Handling:** Correctly resolves relative paths (`./..`), absolute paths (relative to project root `/`), and handles platform differences transparently (thanks to `pathlib`).
* **Directory & File Exclusion:** Supports excluding specific directories (e.g., `drafts`) and files (e.g., `README.md`).
* **Clear Reporting:** Outputs broken links with their source file path and link string, exiting with a non-zero status code on failure, ideal for CI/CD and automation.

#### Usage

```bash
md_check_broken_links.py [directory] [file_pattern] [options]
```

- **Required Arguments (Optional when using defaults)**:
- `directory`: The root directory to start the search. Default is `.`.
- `file_pattern`: The glob pattern to match Markdown files. Default is `*.md`.

- **Options**:
- `--exclude-dirs`: Directory names to exclude from the check (e.g., `drafts temp`). Can list multiple names.
- `--exclude-files`: Specific file names to exclude from the check (e.g., `README.md`). Can list multiple names.
- `--verbose`: Enable verbose mode for more output information.

#### Examples

1. Check all `*.md` files in the current directory and subdirectories:

    ```bash
    md_check_broken_links.py
    ```

1. Check all `*.txt` files recursively from the `./docs` directory:

    ```bash
    md_check_broken_links.py ./docs "*.txt"
    ```
    
1. Usr verbose mode:

    ```bash
    md_check_broken_links.py --verbose
    ```
    
1. Use exclusions:

    ```bash
    md_check_broken_links.py --exclude-dirs drafts temp --exclude-files README.md
    ```

### 2. `format_string.py`

**Purpose**: This script formats a given input string by removing colons, double quotes, replacing spaces with underscores, and converting to lowercase. This can be particularly useful for standardizing text formats, such as creating file names or identifiers that follow specific naming conventions.

#### Usage

```bash
format_string.py 'Your Input String'
```

- **Example**:

```bash
format_string.py 'Agents4Science Conference Paper Digest: How Agents Are "Doing" Science Right Now'
```

- **Output**:

```
agents4science_conference_paper_digest_how_agents_are_doing_science_right_now
```

## Troubleshooting

- **Permission Denied**: If you encounter a "Permission denied" error when trying to run the script, ensure that you have made it executable using the `chmod 0755` command.

- **Syntax Errors**: If you encounter syntax errors, make sure that your Python environment is correctly set up and that the script is compatible with your version of Python.
