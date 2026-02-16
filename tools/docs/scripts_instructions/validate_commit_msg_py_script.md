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
title: "Instruction on validate_commit_msg.py script"
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-16
options:
  version: 1.0.0
  birth: 2026-02-16
---

# Instruction on validate_commit_msg.py script

+++

:::{important} Configuration source
This script reads its configuration — valid commit types, ArchTag-required types — from `pyproject.toml [tool.commit-convention]`. That section is the single source of truth shared with `generate_changelog.py`. The rules themselves are defined in [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb).
:::

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/validate_commit_msg.py) is a pre-commit hook (`commit-msg` stage) that validates commit messages against the project's Conventional Commits convention with structured body bullets ({term}`ADR-26024`).

It enforces three validation layers:

1. **Subject format** — must match `type[(scope)][!]: description` where type is one of the recognized Conventional Commits types.
2. **Structured body** — must contain at least one changelog bullet (`- Verb: \`target\` — description`).
3. **ArchTag presence** — required for `refactor:`, `perf:`, and breaking change (`!`) commits (Tier 3 justification).

Merge, fixup, squash, and `WIP:` commits are skipped — they are transient and eliminated by Squash-and-Merge.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `re`, `sys`, `tomllib`, `pathlib`).
* **Configuration from pyproject.toml**: Valid types, ArchTag rules, and section mappings are loaded from `pyproject.toml [tool.commit-convention]` — a single source of truth shared with `generate_changelog.py`.
* **High Portability**: No external tools required. Runs on any system with Python 3.11+.
:::

+++

## **2. Key Capabilities & Logic**

+++

### Validation Layer 1: Subject Format

The subject line must match the Conventional Commits format:

```
type[(scope)][!]: description
```

| Check | Pass | Fail |
|-------|------|------|
| Valid type prefix | `feat: add login` | `unknown: something` |
| Colon + space separator | `fix: correct bug` | `fix:no space` |
| Non-empty description | `docs: update README` | `docs: ` |
| Optional scope | `feat(auth): add login` | — |
| Breaking change `!` | `feat!: breaking change` | — |

Valid types are loaded from `pyproject.toml [tool.commit-convention].valid-types`.

+++

### Validation Layer 2: Structured Body

The body must contain at least one changelog bullet — a line matching `^\s*- .+`:

```
feat: add login page

- Created: `auth/login.py` — new login page
- Updated: `auth/urls.py` — added login route
```

Lines that do **NOT** count as bullets:
* Prose context lines
* ArchTag lines (`ArchTag:TAG-NAME`)
* Git trailers (`Co-Authored-By: ...`)
* Blank lines

+++

### Validation Layer 3: ArchTag (Tier 3)

For `refactor:` and `perf:` types, and any commit with `!` (breaking change), an ArchTag line is required as the first body line:

```
refactor: simplify model loading

ArchTag:TECHDEBT-PAYMENT
- Updated: `model_loader.py` — reduced complexity
```

ArchTag-required types are loaded from `pyproject.toml [tool.commit-convention].archtag-required-types`.

+++

### Skip Logic

These transient commit types bypass validation entirely (exit 0):

| Pattern | Example |
|---------|---------|
| `Merge ...` | `Merge branch 'feature' into main` |
| `fixup! ...` | `fixup! feat: add login` |
| `squash! ...` | `squash! feat: add login` |
| `WIP: ...` | `WIP: work in progress` |

+++

## **3. Technical Architecture**

+++

The script is organized into focused functions:

* **`validate_subject()`** — CC format regex matching, type validation
* **`validate_body()`** — bullet detection with ArchTag/trailer exclusion
* **`validate_archtag()`** — Tier 3 ArchTag presence check
* **`is_skip_commit()`** — merge/fixup/WIP detection
* **`ValidateCommitMsgCLI`** — argument parsing, file reading, error reporting

Configuration is loaded at module import time from `pyproject.toml` via `tomllib` (stdlib).

+++

## **4. Operational Guide**

+++

### Configuration Reference

* **Script**: `tools/scripts/validate_commit_msg.py`
* **Configuration**: `pyproject.toml [tool.commit-convention]`
* **Standards**: [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb)
* **Pre-commit Config**: `.pre-commit-config.yaml`

+++

### Command Line Interface

```bash
validate_commit_msg.py MSG_FILE
```

| Argument | Description |
|----------|-------------|
| `MSG_FILE` | Path to the commit message file (provided by git's commit-msg hook) |

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Valid message (or skipped commit type) |
| 1 | Validation failure |

+++

### Manual Execution

```bash
# Validate a commit message file
uv run tools/scripts/validate_commit_msg.py .git/COMMIT_EDITMSG

# Test with a custom message
echo -e "feat: add login\n\n- Created: \`login.py\` — new" > /tmp/msg
uv run tools/scripts/validate_commit_msg.py /tmp/msg
```

+++

## **5. Validation Layers**

+++

### Layer 1: Local Pre-commit Hook

Runs automatically at `commit-msg` stage during `git commit`:

```yaml
- id: validate-commit-msg
  name: Validate Commit Body
  entry: uv run --active tools/scripts/validate_commit_msg.py
  language: python
  stages: [commit-msg]
  pass_filenames: true
```

### Layer 2: CI

The `quality.yml` workflow runs the test suite when the script, tests, or `pyproject.toml` change:

```yaml
validate-commit-msg:
  # Triggered by changes to script, tests, or pyproject.toml
  - name: Run Logic Tests
    run: uv run pytest tools/tests/test_validate_commit_msg.py
```

A future enhancement can repeat the validation on the PR's squash commit candidate to catch messages modified during the merge process.

+++

## **6. Test Suite**

+++

The script is accompanied by a test suite (`test_validate_commit_msg.py`) with 68 tests covering:

* **Subject validation**: All valid types, scope, breaking `!`, missing/invalid components
* **Body validation**: Bullet detection, prose-only rejection, trailer/ArchTag exclusion
* **ArchTag validation**: Required types, breaking changes, non-required types
* **Skip detection**: Merge, fixup, squash, WIP commits
* **CLI integration**: Valid/invalid messages, file reading, exit codes

+++

### Running the Tests

```bash
# Run all tests
uv run pytest tools/tests/test_validate_commit_msg.py

# Run with coverage
uv run pytest tools/tests/test_validate_commit_msg.py --cov=tools.scripts.validate_commit_msg --cov-report=term-missing
```

```{code-cell}
cd ../../../
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_validate_commit_msg.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_validate_commit_msg.py --cov=tools.scripts.validate_commit_msg --cov-report=term-missing -q
```
