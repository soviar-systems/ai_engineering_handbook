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

# Instruction on jupytext_sync.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.1.0
Birth: 2026-01-26
Last Modified: 2026-01-26

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/jupytext_sync.py) synchronizes Markdown (.md) and Jupyter notebook (.ipynb) pairs using Jupytext.

It ensures that changes made to either file format are propagated to the other, maintaining consistency between human-readable markdown and executable notebooks.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library plus Jupytext (already a project dependency).
* **Flexible Modes**: Supports both sync mode and test mode for CI validation.
* **Directory Exclusions**: Automatically skips common directories like `.venv`, `node_modules`, etc.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. Sync Mode (Default)

Runs `jupytext --sync` to synchronize both files in a pair:
- If .md is newer, updates .ipynb
- If .ipynb is newer, updates .md

+++

### B. Test Mode

Runs `jupytext --to ipynb --test` to verify synchronization without making changes:
- Returns exit code 0 if files are in sync
- Returns exit code 1 if files differ

+++

### C. Batch Processing

The `--all` flag finds and processes all paired notebooks in the repository:
- Scans for .md files with matching .ipynb files
- Respects directory exclusions from `paths.py`

+++

## **3. Operational Guide**

+++

### Basic Usage

```bash
# Sync specific files
uv run tools/scripts/jupytext_sync.py file1.md file2.ipynb

# Test mode (CI validation)
uv run tools/scripts/jupytext_sync.py --test file1.md

# Sync all paired notebooks in repo
uv run tools/scripts/jupytext_sync.py --all

# Test all paired notebooks
uv run tools/scripts/jupytext_sync.py --all --test
```

+++

### CLI Options

| Option | Description |
|--------|-------------|
| `--test` | Run in test mode (verify sync without changes) |
| `--all` | Find and process all paired notebooks |
| `files` | Specific files to sync (optional with `--all`) |

+++

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All files synced/verified successfully |
| `1` | One or more files failed to sync/verify |

+++

## **4. Validation Layers**

+++

### Pre-commit Hook

```yaml
- id: jupytext-sync
  name: Jupytext Sync
  entry: uv run tools/scripts/jupytext_sync.py
  files: \.(md|ipynb)$
```

+++

### GitHub Actions

The script runs in the `jupytext` job in `quality.yml`.

+++

## **5. Test Suite**

+++

The [test suite](/tools/tests/test_jupytext_sync.py) covers:

| Test Area | Coverage |
|-----------|----------|
| File filtering | Valid extensions, exclusions |
| Sync execution | Subprocess calls, error handling |
| Batch mode | `find_all_paired_notebooks` function |

Run tests with:

```bash
uv run pytest tools/tests/test_jupytext_sync.py -v
```
