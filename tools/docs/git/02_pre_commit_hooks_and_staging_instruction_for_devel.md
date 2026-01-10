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

# Pre-Commit Hooks and Staging: Instruction for Developers

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.1  
Birth: 2026-01-04  
Last Modified: 2026-01-09

---

+++

## **1. Philosophy**

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

## **2. Installation and Configuration**

+++

We use a Python package `pre-commit` for handling local hooks (see ["ADR 0002: Adoption of the Pre-commit Framework"](/architecture/adr/adr_0002_adoption_of_pre_commit_framework.md)).

The `.pre-commit-config.yaml` file is already configured in the repo, so the developer needs to install pre-commit and install the config to `.git/hooks` repo: 

```bash
$ uv add pre-commit
$ uv run pre-commit install
```

```{code-cell}
ls ../../../.git/hooks | grep 'pre-commit$'
```

Run the [repo configuration script](/tools/scripts/configure_repo.sh), it will automatically handle this.

+++

## **3. Testing**

+++

```bash
$ uv run pre-commit [<hook_id>] [--all-files]
```
