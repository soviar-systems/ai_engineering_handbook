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

# How to use scripts on GNU/Linux

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.3.0  
Birth: 2025-12-20  
Last Modified: 2026-01-07

---

+++

This directory contains various utility scripts designed to automate common tasks within the AI Engineering Handbook project. Each script is written in Python and can be executed from the GNU/Linux command line. Below are the general steps to make a script executable and how to run it, along with specific instructions for each script.

```{code-cell}
grep -i 'pretty' /etc/os-release
```

## Make a Script Executable

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

## Add Scripts to `PATH`

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

## Run a Script

+++

Once the script is executable and added to your `PATH`, you can run it from any directory by providing any necessary arguments as required by the script.

```bash
script_name.py [arguments]
```

Replace `script_name.py` with the actual name of your script and `[arguments]` with any required or optional arguments.

+++

## Troubleshooting

+++

- **Permission Denied**: If you encounter a "Permission denied" error when trying to run the script, ensure that you have made it executable using the `chmod 0755` command.

- **Syntax Errors**: If you encounter syntax errors, make sure that your Python environment is correctly set up and that the script is compatible with your version of Python.
