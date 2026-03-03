# Plan: Save Evidence Artifacts for Pre-Commit Hook Stage Analysis

## Context

The file `architecture/evidence/sources/gemini-3-flash-post-commit-hook.md` contains a Gemini-3-Flash dialogue transcript advising against using `post-commit` hooks for validation (it should use `commit-msg` instead). We need to:
1. Evaluate whether the current hook pipeline follows this advice
2. Save the source and analysis as proper evidence artifacts
3. Decide: ADR vs docs update

## Analysis Result

**No strategy change needed.** The current implementation already follows the recommended approach:

| Hook | Stage | Blocking? | Correct? |
|------|-------|-----------|----------|
| `validate-commit-msg` | `commit-msg` | Yes — aborts commit on failure | Yes |
| `changelog-preview` | `post-commit` | No — informational only | Yes |
| All content validators | `pre-commit` | Yes — aborts before message | Yes |

The Gemini source **validates** the existing architecture rather than revealing a gap. The doc `tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.md` already describes both hooks correctly (Sections 4 and 5), though it doesn't explicitly state the *rationale* for the stage assignments.

## Decision: No ADR Needed

An ADR records a **new** architectural decision. Here, no decision is being changed — we're confirming an existing one. The appropriate artifacts are:
- **Evidence source** (S-26003): Capture the raw Gemini dialogue
- **Evidence analysis** (A-26004): Document the hook stage rationale and validation
- **Docs update**: Add explicit stage rationale to Section 4 of `02_pre_commit_hooks_and_staging_instruction_for_devel.md`

## Steps

### Step 1: Rename and format source → `S-26003`

- **From:** `architecture/evidence/sources/gemini-3-flash-post-commit-hook.md`
- **To:** `architecture/evidence/sources/S-26003_gemini_post_commit_hook_stage_advice.md`
- Add proper frontmatter:
  ```yaml
  ---
  id: S-26003
  title: "Gemini 3 Flash — Post-Commit Hook Stage Advice"
  date: 2026-03-03
  model: gemini-3.0-flash
  extracted_into: A-26004
  ---
  ```
- Keep the existing transcript content unchanged below the frontmatter

### Step 2: Create analysis → `A-26004`

- **File:** `architecture/evidence/analyses/A-26004_hook_stage_assignment_rationale.md`
- **Required sections:** Problem Statement, References
- **Content:** Document the three-stage hook model (`pre-commit` → `commit-msg` → `post-commit`), why each hook is assigned to its current stage, and the conclusion that the current architecture is sound
- Frontmatter:
  ```yaml
  ---
  id: A-26004
  title: "Hook Stage Assignment Rationale"
  date: 2026-03-03
  status: active
  tags: [git, governance]
  sources: [S-26003]
  produces: []
  ---
  ```

### Step 3: Update docs — add stage rationale

- **File:** `tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.md`
- Add a brief rationale paragraph to the beginning of Section 4 explaining **why** `commit-msg` (not `post-commit`) is the correct stage for validation
- Bump version to `1.3.0` (minor — new content), update date
- Cross-reference A-26004

### Step 4: Delete the original unformatted file

- `git rm architecture/evidence/sources/gemini-3-flash-post-commit-hook.md` (content moved to S-26003)

## Verification

1. `uv run tools/scripts/check_evidence.py` — validates S-26003 and A-26004 frontmatter/sections
2. `uv run tools/scripts/check_broken_links.py --pattern "*.md"` — validates any new cross-references
3. `uv run pytest tools/tests/test_check_evidence.py` — ensures no regressions

## Files Modified

- `architecture/evidence/sources/S-26003_gemini_post_commit_hook_stage_advice.md` (new)
- `architecture/evidence/analyses/A-26004_hook_stage_assignment_rationale.md` (new)
- `tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.md` (edit)
- `architecture/evidence/sources/gemini-3-flash-post-commit-hook.md` (delete — replaced by S-26003)
