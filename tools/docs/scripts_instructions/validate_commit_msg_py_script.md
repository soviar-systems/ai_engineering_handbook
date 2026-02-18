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
date: 2026-02-18
options:
  version: 1.0.1
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
2. **Structured body** — must contain at least one changelog bullet (`- Verb: target — description`).
3. **ArchTag presence** — required for `refactor:`, `perf:`, and breaking change (`!`) commits (Tier 3 justification).

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

- Created: auth/login.py — new login page
- Updated: auth/urls.py — added login route
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
- Updated: model_loader.py — reduced complexity
```

ArchTag-required types are loaded from `pyproject.toml [tool.commit-convention].archtag-required-types`.

+++

## **3. Technical Architecture**

+++

The script is organized into focused functions:

* **`validate_subject()`** — CC format regex matching, type validation
* **`validate_body()`** — bullet detection with ArchTag/trailer exclusion
* **`validate_archtag()`** — Tier 3 ArchTag presence check
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
| 0 | Valid message |
| 1 | Validation failure |

+++

### Manual Execution

```bash
# Validate a commit message file
uv run tools/scripts/validate_commit_msg.py .git/COMMIT_EDITMSG

# Test with a custom message
echo -e "feat: add login\n\n- Created: login.py — new" > /tmp/msg
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

The script is accompanied by a test suite (`test_validate_commit_msg.py`) with 63 tests covering:

* **Subject validation**: All valid types, scope, breaking `!`, missing/invalid components
* **Body validation**: Bullet detection, prose-only rejection, trailer/ArchTag exclusion
* **ArchTag validation**: Required types, breaking changes, non-required types
* **Formerly-skipped commit rejection**: WIP, Merge, fixup, squash commits → exit 1
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

## **7. Post-Mortem: Removal of `is_skip_commit()`**

+++

:::{admonition} Post-mortem structure
Follows the formalized post-mortem structure from ADR-26006: required sections, evidence over narrative, failed fixes mandatory, numbered principles, chain validation.
:::

+++

### Executive Summary

A `WIP: test` commit (4d8502f, 2026-02-16) passed all pre-commit hooks while violating ADR-26024 — invalid type prefix, prose body without structured bullets, 9 files undocumented. Root cause: `is_skip_commit()` bypassed all three validation layers for four commit prefixes based on the assumption that Squash-and-Merge would eliminate them. Resolution: function deleted; `--no-verify` is the only escape hatch.

+++

### The Architecture Before (The Validator at v1.0.0)

- `validate_commit_msg.py` enforced three validation layers: subject format, structured body, ArchTag presence
- `is_skip_commit()` (lines 144-156) bypassed ALL three layers for: `Merge `, `fixup! `, `squash! `, `WIP:`
- Docstring rationale: "transient — they will be eliminated by Squash-and-Merge and don't need structured bodies"
- The function was tested (7 tests in `TestIsSkipCommit`), documented, and intentional
- CLI integration tests verified skip behavior (`test_merge_commit_skipped`, `test_fixup_commit_skipped`)

+++

### What Went Wrong

**Evidence:** The actual commit message:

```
WIP: test

testing commit messages validation
```

**Concrete violations against ADR-26024:**

1. `WIP` is not in valid types (loaded from `pyproject.toml [tool.commit-convention].valid-types`)
2. Body is prose — no structured bullet `- Verb: target — description`
3. 9 files changed, none documented in the body

**Hook output:** Exit 0 (pass). The hook never reached validation — `is_skip_commit("WIP: test")` returned `True` on line 233, causing immediate return.

+++

### Failed Fixes / Investigation

What was examined before the decision to remove the skip function entirely:

1. **"Tighten the WIP skip"** — considered keeping skips but removing WIP specifically. Rejected because `fixup!` and `squash!` have the same problem: they're developer-initiated workarounds that can bypass the body requirement.

2. **"Add CI hard gate for WIP in PR history"** — the git workflow doc already specifies a CI step that fails PRs containing `^WIP:` in commit history. Considered implementing it. Rejected because it addresses the symptom, not the cause: the validator shouldn't give free passes in the first place. CI should run the same script, not compensate for the script's exemptions.

3. **"Keep Merge skip only"** — since `git merge` auto-generates the message. Rejected because the team standardizes on rebase workflow; merge commits are avoidable, not inevitable.

+++

### Root Cause Analysis

The validator delegated enforcement responsibility to a downstream workflow step (squash-and-merge). This created an implicit dependency chain:

```
is_skip_commit() assumes → squash-and-merge will happen → which assumes → PR workflow is followed → which assumes → GitHub merge policy is configured correctly
```

Each assumption in the chain is a potential failure point:

- `--no-verify` bypasses local hooks (developer can create WIP locally — that's fine, it's intentional)
- But the validator also skips WIP even WITHOUT `--no-verify` — the developer gets no signal that their commit is non-conforming
- If merge policy changes, or someone force-pushes, or the repo moves platforms, the exemptions become vulnerabilities

**The deeper issue:** The skip function confused two different concerns:

- **Trunk history quality** (controlled by merge strategy) — an *output* policy
- **Individual commit validity** (controlled by the validator) — an *input* policy

The skip function made the input validator aware of the output policy. This coupling meant the validator's correctness depended on external configuration it couldn't verify.

**Parallel to check_adr.py desync pattern** (documented in Section 5): the same class of error occurs when `--fix` mode has different validation coverage than `--verbose` mode. The fix was identical: ensure validation runs the same gates regardless of mode. Here, the fix is: validate regardless of commit type.

+++

### The Solution

- Delete `is_skip_commit()` entirely (function + tests + docs)
- All commits go through all three validation layers
- `--no-verify` is the only escape hatch — explicit, intentional, visible
- Git workflow standards updated: WIP commits require `--no-verify`; rebase is standard (not merge)

**Analysis of each removed skip type:**

| Type | Git-native? | Auto-eliminated? | Why skip was unnecessary |
|------|-------------|------------------|--------------------------|
| `WIP:` | No (convention only) | No (requires human action) | No lifecycle; relies on discipline |
| `Merge ` | Yes (git-generated) | N/A | Avoidable by standardizing on rebase |
| `fixup!` | Yes (--fixup flag) | Yes, via autosquash rebase | Redundant with squash-and-merge |
| `squash!` | Yes (--squash flag) | Yes, via autosquash rebase | Redundant + potential ADR-26024 bypass |

+++

### Principles Extracted

**P1: Validation tools validate unconditionally.**
Opt-out must be explicit (`--no-verify`), never implicit (skip functions). Implicit skips are invisible — the developer gets no signal that validation was bypassed. Explicit opt-out requires a conscious decision.

**P2: Each layer enforces its own contract independently.**
Don't assume downstream safeguards exist. The validator's job is to validate the commit message at its layer. Whether squash-and-merge will clean up later is irrelevant — and unknowable from inside the hook.

**P3: Implicit bypasses are architectural debt.**
`is_skip_commit()` was tested, documented, and intentional — but it was still an invisible escape hatch. The function accumulated four bypass patterns over time. Each pattern was individually justified ("transient commit") but collectively they created a class of commits that could violate any project convention without detection.

**P4: Input policy and output policy are separate concerns.**
Squash-and-merge is an *output* policy (controls trunk history). Commit validation is an *input* policy (controls individual commit quality). Coupling them — making the input validator aware of the output policy — creates a fragile dependency that breaks when either policy changes independently.

+++

### Relationship to Previous Post-Mortems

This is the first post-mortem in the `ai_engineering_book` script documentation. No chain validation needed yet.

However, it relates to the `check_adr.py` pre-commit/CI desync pattern insight (same repo): both are instances of **validation layers with inconsistent coverage** — one mode validates everything, another mode silently skips checks, and the gap only surfaces when a non-conforming input happens to take the skipped path.

+++

### Document History

- 2026-02-16: Initial version created during `is_skip_commit()` removal
