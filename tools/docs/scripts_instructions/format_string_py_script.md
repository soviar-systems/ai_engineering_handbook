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

# Instruction on format_string.py script

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.1.0  
Birth: 2026-01-07  
Last Modified: 2026-01-07

---

+++

This script formats a given input string by applying several transformations to make it URL-safe and filesystem-friendly. The transformations include converting to lowercase, replacing specific special characters, removing unwanted words, and truncating the string if necessary.

## Synopsis

```bash
format_string.py 'Your Input String'
```

## Transformation Logic

1. **Convert to Lowercase**: All characters in the input string are converted to lowercase.
2. **Replace & with and**: The ampersand (`&`) is replaced with the word "and".
3. **Remove Special Symbols**: Certain special symbols (e.g., "the ", "(", ")", "# ", "#", "`", "~", "$", "%", "@") are removed from the string.
4. **Replace Special Symbols with Underscores**: Other special symbols (e.g., ".", ",", ";", ":", "!", "?", "-", "/", "\\", "|", "<", ">", "*") are replaced with underscores (`_`).
5. **Remove Multiple Underscores**: Any sequence of multiple underscores is reduced to a single underscore.
6. **Replace Spaces with Underscores**: All spaces in the string are replaced with underscores.
7. **Truncate Long Strings**: If the resulting string exceeds 50 characters, it is truncated to 50 characters.
8. **Remove Trailing Underscore**: If the final character of the string is an underscore, it is removed.

## Examples

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
