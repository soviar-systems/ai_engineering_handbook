# Plan: Release Preparation — ADR Status Alignment + Cleanup

## Context

Preparing a release. ADR statuses must reflect reality (accept implemented, reject obsolete). Sources directory needs cleanup (extracted sources removed). Uncommitted changes need separate commits. Release artifacts (CHANGELOG, RELEASE_NOTES, README, TG post) come last, driven by the prompt in `ai_system/4_orchestration/workflows/release_notes_generation/prompt_draft.md`.

---

## Step 1: Accept 6 ADRs

Change `status: proposed` → `status: accepted` (frontmatter + `## Status` section):

| ADR | File glob | Rationale |
|-----|-----------|-----------|
| 26011 | `adr_26011*` | Script suite triad enforced via pre-commit |
| 26024 | `adr_26024*` | validate_commit_msg.py + generate_changelog.py active |
| 26036 | `adr_26036*` | Config conventions followed across configs |
| 26038 | `adr_26038*` | Core principle driving rejections of 26031/34 |
| 26040 | `adr_26040*` | CLAUDE.md mandates Podman; production templates exist |
| 26041 | `adr_26041*` | Client-side validation pipeline operational |

## Step 2: Reject ADR-26003

File: `architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md`

- Change status to `rejected`
- Add note: commit validation solved by custom `validate_commit_msg.py` (ADR-26024); branch naming (Tier 1) to be addressed in a future Git Three-Tier ADR as a vadocs-git plugin

## Step 3: Regenerate ADR Index

```bash
uv run tools/scripts/check_adr.py --fix
```

## Step 4: Delete Extracted Sources

Remove 5 extracted S-YYNNN files from `architecture/evidence/sources/`:
- `S-26006_gemini_agentic_os_design_review.md`
- `S-26008_gemini_langchain_agents_tools_memory.md`
- `S-26009_gemini_local_git_repo_rag_pgvector.md`
- `S-26010_gemini_stateless_jit_agentic_git_workflow.md`
- `S-26011_gemini_pgvector_viability_and_logic_locality.md`

Keep: README.md, raw unformatted files (gemini_3_terminal_agents_comparison.md, qwen3.5-terminal-agents-comparison.txt)

## Step 5: Update format_string.py Script Suite (triad)

Full script suite update (ADR-26011 triad: script + tests + docs):

**Script** (`tools/scripts/format_string.py`):
- Already done: en-dash (`–`) added to special symbols, truncation made optional (`trunc`, `trunc_len` params)
- TODO: Update `main()` to accept CLI flags: `--trunc` and `--trunc-len N`
- TODO: Update help/usage message to reflect new options

**Tests** (`tools/tests/test_format_string.py`):
- `test_truncates_long_strings` (line 87): Currently assumes truncation always happens → needs update for optional truncation
- `test_removes_trailing_underscore_after_truncation` (line 92): Same issue
- Add new tests: en-dash replacement, `trunc=True` behavior, `trunc=False` behavior (default), custom `trunc_len`

**Docs** (`tools/docs/scripts_instructions/format_string_py_script.md`):
- Update Synopsis to show new CLI flags
- Update Transformation Logic step 7: truncation is now optional (off by default)
- Add en-dash to the symbols list in step 4
- Bump `options.version` (0.2.2 → 0.3.0, minor for new feature) and update `date`

Own commit: `feat: Add optional truncation and en-dash support to format_string`

## Step 6: Commit misc/ Ephemeral Files

- `misc/insights.md` — new insights added
- `misc/todo.md` — new tasks added
- Own commit: `docs: Update insights and todo`

## Step 7: Gherkin — Move Plan to Implemented

- Move `misc/plan/plan_20260217_gherkin_analysis_and_extraction_tool.md` → `misc/plan/implemented/`
- Keep `misc/gherkin_tmp/` as future skill research input
- Own commit: `docs: Archive gherkin plan as implemented`

## Step 8: TG Channel Post — Leave Unfinished

- `misc/pr/tg_channel_ai_learning/2026_03_08_agentic_os_rise_and_fall.md` — user has not finished it, leave untracked

## Step 9: Update Ecosystem Roadmap

Add to `misc/plan/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md`:

1. **New ADR: Git Three-Tier Mechanics** — under Phase 1.1 item 10 (or after 26046). Document adopted three-tier git validation (branch naming, commit format, ArchTag) as vadocs-git plugin. Branch naming (Tier 1) is the unimplemented gap
2. **ADR-26042 enforcement script** — under Phase 1.2. Build the script suite governing common frontmatter format (hub config + validation)
3. **BDD/Gherkin skill** — under Phase 2.0 or 3.x. Research Gherkin as a composable skill for product development lifecycle formalization

## Step 10: Exclude from Release (leave untracked)

- `tools/docs/ai_agents/comparing_cli_agents.ipynb` + `.md` — drafts, not ready
- `ai_system/4_orchestration/workflows/release_notes_generation/prompt_draft.md` — meta-tool, commit separately
- `misc/pr/tg_channel_ai_learning/2026_03_08_agentic_os_rise_and_fall.md` — unfinished

## Step 11: Release Artifacts (LAST)

After all above commits are done, follow the workflow in `prompt_draft.md`:
1. Generate diff: `tools/scripts/release_notes_data.sh $(git describe --tags --abbrev=0) HEAD > diff1`
2. Write RELEASE_NOTES.md using template
3. Regenerate CHANGELOG.md
4. Update README.md (What's New section)
5. Write TG post for the release

---

## Files to Modify

**ADR status changes (Steps 1-3):**
- `architecture/adr/adr_26003*.md` — reject
- `architecture/adr/adr_26011*.md` — accept
- `architecture/adr/adr_26024*.md` — accept
- `architecture/adr/adr_26036*.md` — accept
- `architecture/adr/adr_26038*.md` — accept
- `architecture/adr/adr_26040*.md` — accept
- `architecture/adr/adr_26041*.md` — accept
- `architecture/adr/adr_index.md` — regenerated

**Deletions (Step 4):**
- 5 × `architecture/evidence/sources/S-26*.md`

**Commits (Steps 5-8):**
- `tools/scripts/format_string.py`
- `misc/insights.md`, `misc/todo.md`
- `misc/plan/plan_20260217_gherkin*.md` (move)
- `misc/pr/tg_channel_ai_learning/2026_03_08*.md`

**Roadmap update (Step 9):**
- `misc/plan/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md`

**Release artifacts (Step 11):**
- `CHANGELOG.md`, `RELEASE_NOTES.md`, `README.md`
- New TG post in `misc/pr/tg_channel_ai_learning/`

## Verification

```bash
uv run tools/scripts/check_adr.py --fix
uv run tools/scripts/check_broken_links.py
uv run tools/scripts/check_evidence.py
git status  # verify only excluded files remain untracked
```
