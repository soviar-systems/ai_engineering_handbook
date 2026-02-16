# Plan: Remove `is_skip_commit()` from `validate_commit_msg.py`

## Context

A `WIP: test` commit (4d8502f) passed all pre-commit hooks while violating ADR-26024 (no valid CC type, no structured body bullets). Investigation revealed that `is_skip_commit()` intentionally skips validation for `WIP:`, `Merge `, `fixup!`, and `squash!` prefixed commits, assuming squash-and-merge would eliminate them.

The user's position: **validation should be the same everywhere**. The only escape hatch for non-conforming commits is `--no-verify`. With squash-and-merge as the mandatory merge strategy, none of the skip types need special treatment:

- `Merge ` — standardize on rebase workflow instead
- `fixup!` / `squash!` — redundant when squash-and-merge already consolidates history
- `WIP:` — no git-native lifecycle; relies entirely on human discipline

## TDD Approach

Per CLAUDE.md: **write tests FIRST, then implement**.

### Step 1: Update tests (`tools/tests/test_validate_commit_msg.py`)

**Remove:**
- `TestIsSkipCommit` class (lines 280-304)
- `is_skip_commit` from imports (line 39)
- `test_merge_commit_skipped` (line 397-402) — merge commits now fail
- `test_fixup_commit_skipped` (line 404-409) — fixup commits now fail

**Update module docstring** (line 16): Remove "Merge, fixup, squash, and WIP commits are skipped" and lines 22-23 referencing `is_skip_commit`.

**Add new test class** `TestFormerlySkippedCommitsFail`:
```
Contract: WIP, Merge, fixup, squash commits → exit 1 (no longer skipped).
```
Tests (parametrized where possible):
- `test_wip_commit_fails_validation` — `WIP: work in progress` → SystemExit(1)
- `test_merge_commit_fails_validation` — `Merge branch 'feature' into main` → SystemExit(1)
- `test_fixup_commit_fails_validation` — `fixup! feat: add login` → SystemExit(1)
- `test_squash_commit_fails_validation` — `squash! feat: add login` → SystemExit(1)

Each creates a tmp file and runs `ValidateCommitMsgCLI().run()`, asserting `SystemExit` with code 1.

### Step 2: Run tests — confirm RED

```bash
uv run pytest tools/tests/test_validate_commit_msg.py -v
```

New tests should fail (skip logic still exists). Old skip tests should be gone.

### Step 3: Update script (`tools/scripts/validate_commit_msg.py`)

**Remove:**
- `is_skip_commit()` function (lines 144-156)
- Skip check in `run()` method (lines 232-233: `if is_skip_commit(subject): return`)
- Module docstring line 9: "Merge, fixup, squash, and WIP commits are skipped (exit 0)."

### Step 4: Run tests — confirm GREEN

```bash
uv run pytest tools/tests/test_validate_commit_msg.py -v
```

All tests should pass. Run coverage to verify no dead code:

```bash
uv run pytest tools/tests/test_validate_commit_msg.py --cov=tools.scripts.validate_commit_msg --cov-report=term-missing -q
```

### Step 5: Update script docs (`tools/docs/scripts_instructions/validate_commit_msg_py_script.md`)

**Remove:**
- "Skip Logic" section (lines 117-128)
- `is_skip_commit()` reference in Technical Architecture (line 139)
- "Merge, fixup, squash, and `WIP:` commits are skipped" in Section 1 (line 45)
- "or skipped commit type" from exit code table (line 173)
- "Skip detection" from test suite list (line 232)

**Add new section** (after Section 6 "Test Suite", before code cells):

### Section 7: Post-Mortem — Removal of `is_skip_commit()`

Follows the formalized post-mortem structure from `mentor_generator/docs/adr/adr_26006_postmortem_as_validated_knowledge_chain.md` (ADR-26006: required sections, evidence over narrative, failed fixes mandatory, numbered principles, chain validation).

**Required Sections (per ADR-26006):**

#### Executive Summary
A `WIP: test` commit (4d8502f, 2026-02-16) passed all pre-commit hooks while violating ADR-26024 — invalid type prefix, prose body without structured bullets, 9 files undocumented. Root cause: `is_skip_commit()` bypassed all three validation layers for four commit prefixes based on the assumption that Squash-and-Merge would eliminate them. Resolution: function deleted; `--no-verify` is the only escape hatch.

#### The Architecture Before (The Validator at v1.0.0)
- `validate_commit_msg.py` enforced three validation layers: subject format, structured body, ArchTag presence
- `is_skip_commit()` (lines 144-156) bypassed ALL three layers for: `Merge `, `fixup! `, `squash! `, `WIP:`
- Docstring rationale: "transient — they will be eliminated by Squash-and-Merge and don't need structured bodies"
- The function was tested (7 tests in `TestIsSkipCommit`), documented, and intentional
- CLI integration tests verified skip behavior (`test_merge_commit_skipped`, `test_fixup_commit_skipped`)

#### What Went Wrong
**Evidence:** The actual commit message:
```
WIP: test

testing commit messages validation
```

**Concrete violations against ADR-26024:**
1. `WIP` is not in valid types (`feat`, `fix`, `docs`, `ci`, `chore`, `refactor`, `perf`, `pr`, `test`)
2. Body is prose — no structured bullet `- Verb: \`target\` — description`
3. 9 files changed, none documented in the body

**Hook output:** Exit 0 (pass). The hook never reached validation — `is_skip_commit("WIP: test")` returned `True` on line 233, causing immediate return.

#### Failed Fixes / Investigation
(What was examined before the decision to remove the skip function entirely)

1. **"Tighten the WIP skip"** — considered keeping skips but removing WIP specifically. Rejected because `fixup!` and `squash!` have the same problem: they're developer-initiated workarounds that can bypass the body requirement.

2. **"Add CI hard gate for WIP in PR history"** — the git workflow doc (lines 329-336) already specifies a CI step that fails PRs containing `^WIP:` in commit history. Considered implementing it. Rejected because it addresses the symptom, not the cause: the validator shouldn't give free passes in the first place. CI should run the same script, not compensate for the script's exemptions.

3. **"Keep Merge skip only"** — since `git merge` auto-generates the message. Rejected because the team standardizes on rebase workflow; merge commits are avoidable, not inevitable.

#### Root Cause Analysis
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

**Parallel to check_adr.py desync pattern** (documented in `validate_commit_msg_py_script.md` Section 5): the same class of error occurs when `--fix` mode has different validation coverage than `--verbose` mode. The fix was identical: ensure validation runs the same gates regardless of mode. Here, the fix is: validate regardless of commit type.

#### The Solution
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

#### Principles Extracted

**P1: Validation tools validate unconditionally.**
Opt-out must be explicit (`--no-verify`), never implicit (skip functions). Implicit skips are invisible — the developer gets no signal that validation was bypassed. Explicit opt-out requires a conscious decision.

**P2: Each layer enforces its own contract independently.**
Don't assume downstream safeguards exist. The validator's job is to validate the commit message at its layer. Whether squash-and-merge will clean up later is irrelevant — and unknowable from inside the hook.

**P3: Implicit bypasses are architectural debt.**
`is_skip_commit()` was tested, documented, and intentional — but it was still an invisible escape hatch. The function accumulated four bypass patterns over time. Each pattern was individually justified ("transient commit") but collectively they created a class of commits that could violate any project convention without detection.

**P4: Input policy and output policy are separate concerns.**
Squash-and-merge is an *output* policy (controls trunk history). Commit validation is an *input* policy (controls individual commit quality). Coupling them — making the input validator aware of the output policy — creates a fragile dependency that breaks when either policy changes independently.

#### Relationship to Previous Post-Mortems
This is the first post-mortem in the `ai_engineering_book` script documentation. No chain validation needed yet.

However, it relates to the `check_adr.py` pre-commit/CI desync pattern insight (same repo): both are instances of **validation layers with inconsistent coverage** — one mode validates everything, another mode silently skips checks, and the gap only surfaces when a non-conforming input happens to take the skipped path.

#### Document History
- 2026-02-16: Initial version created during `is_skip_commit()` removal

### Step 6: Update git workflow standards (`tools/docs/git/01_production_git_workflow_standards.md`)

**Update WIP section** (lines 311-357):
- WIP commits are now **rejected** by the validator
- Developers use `--no-verify` for intentional WIP saves
- The guidance table (lines 349-353) remains useful — it still teaches when to use WIP vs standard types — but should note that `--no-verify` is required for WIP commits

**Update enforcement table** (lines 334-339):
- Remove the CI PR Status Check row that scans for `^WIP:` in PR history — no longer needed since the validator catches it at commit time
- Or update it to note that the validator itself is the gate

### Step 7: Sync Jupytext

```bash
uv run jupytext --sync tools/docs/scripts_instructions/validate_commit_msg_py_script.md
uv run jupytext --sync tools/docs/git/01_production_git_workflow_standards.md
```

## Files to Modify

| File | Action |
|------|--------|
| `tools/tests/test_validate_commit_msg.py` | Remove skip tests, add failure tests |
| `tools/scripts/validate_commit_msg.py` | Delete `is_skip_commit()`, remove skip check |
| `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` | Remove skip section, add post-mortem section |
| `tools/docs/git/01_production_git_workflow_standards.md` | Update WIP section and enforcement table |

## Verification

```bash
# 1. Tests pass
uv run pytest tools/tests/test_validate_commit_msg.py -v

# 2. Coverage check
uv run pytest tools/tests/test_validate_commit_msg.py --cov=tools.scripts.validate_commit_msg --cov-report=term-missing -q

# 3. Manual validation: WIP commit now fails
echo -e "WIP: test\n\ntesting" > /tmp/test_msg
uv run tools/scripts/validate_commit_msg.py /tmp/test_msg  # Should exit 1

# 4. Manual validation: valid commit still passes
echo -e "feat: add login\n\n- Created: \`login.py\` — new page" > /tmp/test_msg
uv run tools/scripts/validate_commit_msg.py /tmp/test_msg  # Should exit 0

# 5. Jupytext sync
uv run jupytext --sync tools/docs/scripts_instructions/validate_commit_msg_py_script.md
uv run jupytext --sync tools/docs/git/01_production_git_workflow_standards.md
```
