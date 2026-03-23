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

---
title: Instruction on git.py module
type: doc
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
description: Shared git utilities module — repo root detection and staged file queries
tags: [git, ci]
date: 2026-03-23
options:
  birth: 2026-03-23
  version: 0.1.0
---

+++

## **1. Purpose**

+++

[git.py](/tools/scripts/git.py) is a shared utility module providing git operations for validation scripts.

It consolidates two operations previously duplicated across multiple scripts:
- **Repository root detection** via `git rev-parse --show-toplevel` with `Path(__file__)` fallback
- **Staged file listing** via `git diff --cached --name-only`

On vadocs package extraction, this module becomes `vadocs.git` or `vadocs.vcs`.

+++

## **2. Public Interface**

+++

| Function | Returns | Description |
|---|---|---|
| `detect_repo_root()` | `Path` | Resolved repo root; falls back to `__file__`-based path |
| `get_staged_files()` | `set[str]` | Repo-relative paths of staged files; empty set on failure |

+++

## **3. Usage**

+++

```{code-cell} bash
:tags: [skip-execution]

# From another script:
# from tools.scripts.git import detect_repo_root, get_staged_files
#
# REPO_ROOT = detect_repo_root()
# staged = get_staged_files()
```

+++

## **4. Scripts Using This Module**

+++

| Script | Uses |
|---|---|
| [check_evidence.py](/tools/scripts/check_evidence.py) | `detect_repo_root`, `get_staged_files` |
| [check_adr.py](/tools/scripts/check_adr.py) | `detect_repo_root` (migration pending) |
| [check_broken_links.py](/tools/scripts/check_broken_links.py) | `detect_repo_root` (migration pending) |
| [check_link_format.py](/tools/scripts/check_link_format.py) | `detect_repo_root` (migration pending) |
| [check_script_suite.py](/tools/scripts/check_script_suite.py) | `get_staged_files` (migration pending) |

+++

## **5. Test Suite**

+++

```{code-cell} bash
:tags: [skip-execution]

uv run pytest tools/tests/test_git.py -v
```

8 tests covering: git success/failure/not-installed for `detect_repo_root`, normal/empty/blank-lines/failure for `get_staged_files`.
