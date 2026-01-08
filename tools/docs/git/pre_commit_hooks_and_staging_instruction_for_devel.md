---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Pre-Commit Hooks and Staging: Instruction for Developers

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.0  
Birth: 2026-01-04  
Last Modified: 2026-01-08

---

+++

## Philosophy

+++

**Never stage files in a `pre-commit` hook that the user didn’t already explicitly `git add`.**

Git’s staging area reflects the developer’s intentional choice about what belongs in the next commit. Your `pre-commit` hook must **respect that intent**—not override it.

+++

### ✅ What you *can* do

+++

(e.g., auto-formatting a file the user added.)
- Apply **safe, deterministic, non-semantic changes**: formatting, lint fixes, license headers.
- Use established tooling like [`pre-commit`](https://pre-commit.com/)—it handles partial staging correctly by stashing unstaged changes, running hooks, then restoring them.

+++

### ❌ What you *must not* do

+++

- **Stage new files** (e.g., build artifacts, config files, logs) that weren’t already in the index.
- Silently add files the user never touched or reviewed.
- Mix unstaged and staged changes by formatting a file only partially added (unless you handle it like `pre-commit` does).

+++

### ⚠️ Why it matters

+++

- Auto-staging unknown files risks **committing secrets, temp files, or unintended changes**.
- It breaks trust: developers expect `git commit` to include *only* what they staged.
- Debugging becomes harder when commits contain “mystery” changes.

+++

### 🔧 Better alternatives

+++

- If a file *must* be up to date (e.g., `package-lock.json`), **fail the commit** and ask the user to run a script or add it manually.
- Enforce correctness in **CI**, not by silently altering the commit contents.
- Use wrapper scripts (e.g., `./commit.sh`) for workflows that require pre-staging—keep automation **explicit**.

---

> **Golden Rule**:  
> A `pre-commit` hook may *refine* what’s staged—but never *expand* it.  
> Preserve user agency. Respect the index.

+++

## Installation

+++

```bash
$ uv add pre-commit
$ uv run pre-commit install
```

+++

## Testing Config

+++

```bash
$ uv run pre-commit [<hook_id>] [--all-files]
```
