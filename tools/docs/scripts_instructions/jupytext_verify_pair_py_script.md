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

# Instruction on jupytext_verify_pair.py script

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

This [script](/tools/scripts/jupytext_verify_pair.py) verifies that when one file of a Jupytext pair (.md or .ipynb) is staged for commit, the other file is also staged.

This prevents partial commits where only one file of a pair is committed, which would break synchronization.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library and git commands.
* **Git Integration**: Checks staging status via `git diff --cached`.
* **Pair Detection**: Automatically finds paired files by changing extensions.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. Pair Verification

For each staged .md or .ipynb file:
1. Find the paired file (swap extension)
2. Check if the pair exists on disk
3. Verify both files are staged together

+++

### B. Unstaged Changes Detection

If both files are staged, also checks for unstaged changes that might be missed.

+++

### C. Validation States

| State | Result |
|-------|--------|
| Neither staged | OK (skip) |
| Both staged, no unstaged changes | OK |
| One staged, other not | FAIL |
| Both staged, has unstaged changes | FAIL |

+++

## **3. Operational Guide**

+++

### Basic Usage

```bash
# Verify specific files
uv run tools/scripts/jupytext_verify_pair.py file1.md file2.ipynb

# Typically called by pre-commit with changed files
```

+++

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All pairs properly staged |
| `1` | One or more pairs incomplete |

+++

## **4. Validation Layers**

+++

### Pre-commit Hook

```yaml
- id: jupytext-verify-pair
  name: Jupytext Verify Pair
  entry: uv run tools/scripts/jupytext_verify_pair.py
  files: \.(md|ipynb)$
  pass_filenames: true
```

+++

### GitHub Actions

Runs as part of the `jupytext` job in `quality.yml`.

+++

## **5. Test Suite**

+++

The [test suite](/tools/tests/test_jupytext_verify_pair.py) covers:

| Test Area | Coverage |
|-----------|----------|
| Pair detection | `get_pair_path` function |
| Staging checks | `is_staged`, `has_unstaged_changes` |
| Validation logic | All state combinations |

Run tests with:

```bash
uv run pytest tools/tests/test_jupytext_verify_pair.py -v
```
