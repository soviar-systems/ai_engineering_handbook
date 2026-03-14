---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  display_name: Bash
  language: bash
  name: bash
---

---
title: Instruction on format_string.py script
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-03-14
options:
  version: 0.3.0
  birth: 2026-01-07
---

+++

This script formats a given input string by applying several transformations to make it URL-safe and filesystem-friendly. The transformations include converting to lowercase, replacing specific special characters, removing unwanted words, and optionally truncating the string.

## Synopsis

```bash
format_string.py 'Your Input String'
format_string.py --trunc 'Your Input String'
format_string.py --trunc --trunc-len 30 'Your Input String'
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--trunc` | Enable truncation | Off |
| `--trunc-len N` | Maximum length when truncation is enabled | 50 |

## Transformation Logic

1. **Strip File Extensions**: Known file extensions (`.pdf`, `.epub`, `.html`, `.txt`, `.md`, `.ipynb`, `.doc`, `.json`, `.yaml`, `.png`, `.jpg`, `.mp4`, archives like `.tar.gz`, `.zip`, etc.) are removed. Compound extensions (`.tar.gz`, `.tar.bz2`) are stripped as a unit.
2. **Convert to Lowercase**: All characters in the input string are converted to lowercase.
3. **Replace & with and**: The ampersand (`&`) is replaced with the word "and".
4. **Remove Special Symbols**: Certain special symbols (e.g., "the ", "(", ")", "# ", "#", "`", "~", "$", "%", "@") are removed from the string.
5. **Replace Special Symbols with Underscores**: Other special symbols (e.g., ".", ",", ";", ":", "!", "?", "-", "–", "—", "/", "\\", "|", "<", ">", "*") are replaced with underscores (`_`).
6. **Remove Multiple Underscores**: Any sequence of multiple underscores is reduced to a single underscore.
7. **Replace Spaces with Underscores**: All spaces in the string are replaced with underscores.
8. **Truncate Long Strings** (optional): When `--trunc` is passed, strings exceeding `--trunc-len` (default 50) are truncated. Truncation is off by default.
9. **Remove Trailing Underscore**: If the final character of the string is an underscore, it is removed.

## Examples

### Basic usage — article and book titles

```{code-cell}
cd ../../../
ls
```

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py 'From Concepts to Code: Introduction to Data Science (2024)'
```

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py 'Quiz - Special Applications: Face Recognition & Neural Style Transfer'
```

### Stripping file extensions

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py 'Feedforward Neural Networks in Depth, Part 3 Cost Functions | I, Deep Learning.pdf'
```

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py 'research_paper_draft.epub'
```

### Handling markdown and code formatting

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py '# Post-Mortem: Architectural Flaws in the `nbdiff`-Centric Jupyter Version Control Handbook'
```

### Long titles with special characters

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py 'Agents4Science Conference Paper Digest: How Agents Are "Doing" Science Right Now'
```

### Truncation

```{code-cell}
# 50 symbols is the default
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py --trunc 'Agents4Science Conference Paper Digest: How Agents Are "Doing" Science Right Now'
```

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/format_string.py --trunc --trunc-len 30 'From Concepts to Code: Introduction to Data Science (2024)'
```

## Test Suite

The [test suite](/tools/tests/test_format_string.py) covers all transformation rules:

| Test Area | Coverage |
|-----------|----------|
| Extension stripping | `.pdf`, `.epub`, `.tar.gz`, compound extensions |
| Case conversion | Lowercase transformation |
| Symbol replacement | `&`, punctuation, dashes (–, —), slashes, etc. |
| Symbol removal | Parentheses, quotes, special chars |
| Underscore handling | Collapsing, stripping |
| Truncation | Optional, configurable length |

Run tests with:

```bash
uv run pytest tools/tests/test_format_string.py -v
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_format_string.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_format_string.py --cov=tools.scripts.format_string --cov-report=term-missing -q
```
