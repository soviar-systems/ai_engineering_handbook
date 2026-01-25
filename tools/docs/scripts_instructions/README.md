---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# The Scripts That Help

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.2.0
Birth: 2026-01-26
Last Modified: 2026-01-26

---

+++

## **Different Scripts for Different Tasks**

+++

The scripts in `tools/scripts/` are aimed to lower the cognitive overhead of the engineer working with the repo, prompts, documentation:

Some scripts automate the validation of the files you commit and push (see ["Pre-commit Hooks and CI Validation System"](/tools/docs/git/03_precommit_ci_validation_system.ipynb)) for
- [broken cross links](/tools/docs/scripts_instructions/check_broken_links_py_script.ipynb),
- the [cross-link format](/tools/docs/scripts_instructions/check_link_format_py_script.ipynb) we use,
- the [broken JSON file](/tools/docs/scripts_instructions/check_json_files_py_script.ipynb), or
- the [script suite completeness](/tools/docs/scripts_instructions/check_script_suite_py_script.ipynb) (script + test + doc).

Other scripts help you automate some routine tasks like 
- [preparing the prompt before feeding to LLM](/tools/docs/scripts_instructions/prepare_prompt_py_script.ipynb) or 
- [convert the string](/tools/docs/scripts_instructions/format_string_py_script.ipynb) to another string, ready for renaming your new doc file.

The first group of scripts is completely in automation work (after the correct setup of your system, see ["Onboarding"](/0_intro/00_onboarding.ipynb)), you do not need to set them additionally up. But the other group is of your own choice, and it is good to know how to make the work with them easier and more comfortable, so read the next section.

+++

## **Script and its Suite**

+++

Every script comes with its own suite consisted of:
- the Python script itself in `tools/scripts/`,
- the Pytest test suite in `tools/tests/`,
- ipynb/md documentation in `tools/docs/scripts_instructions/`.

The validation scripts are used in [pre-commit hook](/.pre-commit-config.yaml) and [GitHub action workflow](/.github/workflows/quality.yml).

:::{important}
When the new script is developed, it must be accompanied by the entire suite. We automate these checks, so you will be informed if you miss anything before you even commit.
:::

+++

### Why We Enforce Suite Completeness

+++

Documentation drift is a common problem: code changes but documentation stays stale. This leads to:
- Developers following outdated instructions
- Inconsistent behavior between what docs say and what code does
- Reduced trust in documentation quality

The [`check_script_suite.py`](/tools/docs/scripts_instructions/check_script_suite_py_script.ipynb) script enforces a simple policy:

1. **Naming convention**: Each script must have a test (`test_<name>.py`) and doc (`<name>_py_script.md`) with matching names
2. **Co-staging**: When you change a script or its test, you must also stage the documentation
3. **Rename tracking**: When documentation is renamed, config files must be updated

This ensures documentation is always reviewed when code changes, keeping the suite synchronized.

+++

(how-to-use-scripts)=
## **How to use scripts on GNU/Linux**

+++

Each script in this directory is written in Python and can be executed from the GNU/Linux command line. Below are the general steps to make a script executable and how to run it, along with specific instructions for each script.

```{code-cell} ipython3
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

Read details on each script in its own doc.

+++

### Troubleshooting

+++

- **Permission Denied**: If you encounter a "Permission denied" error when trying to run the script, ensure that you have made it executable using the `chmod 0755` command.

- **Syntax Errors**: If you encounter syntax errors, make sure that your Python environment is correctly set up and that the script is compatible with your version of Python.
