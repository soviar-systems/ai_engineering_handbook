# Plan: v2.5.0 Release Deliverables

## Context

Release v2.5.0 is ready. The CHANGELOG is already written. The user needs 3 deliverables:
1. RELEASE_NOTES.md — prepend v2.5.0 section
2. README.md — update "What's new?" (keep 3 most recent)
3. Telegram post — Russian, product-focused

This release's notes use git diff output because commit conventions were adopted mid-release. Starting v2.6.0, `generate_changelog.py` will be the primary source.

**Release name: v2.5.0 "The Self-Documenting System"** — the system now validates its own commits, generates its own CHANGELOG, and installs its own hooks. Natural evolution from v2.4.0 "The Governed Architecture."

---

## Step 1: Write RELEASE_NOTES.md v2.5.0 section

**File:** `RELEASE_NOTES.md` — insert after `# Release Notes` heading, before `## release v2.4.0`

**Three product themes for Summary:**
1. **Automated Commit Governance** — `validate_commit_msg.py` + `generate_changelog.py` + auto-installed hook = self-documenting commit lifecycle
2. **Tool-Agnostic Architecture** — ADR-26004..26008 superseded by ADR-26027/26028 (cognitive roles, not tool names); `aidx` → generic Multi-Phase AI Pipeline
3. **Ecosystem Consolidation** — research extracted to monorepo (ADR-26026), promotion gate formalized (ADR-26025), 6 ADRs promoted, `pyproject.toml` as tool config SSoT (ADR-26029)

**New Features section** (product-level, `* **Category:**` style):
- Automated Commit Validation & CHANGELOG Generation (validate_commit_msg.py, generate_changelog.py, 68+56 tests)
- RFC-to-ADR Promotion Gate (ADR-26025)
- Tool-Agnostic Model Taxonomy (ADR-26027, ADR-26028)
- Format-as-Architecture v0.2.0 (empirical token measurements)
- ADR Section Whitelist Enforcement
- HTML/MHTML Text Extraction
- Superseded Annotation in ADR Index
- Documentation-as-Code Manifesto (architecture/manifesto.md)

**Updates section:**
- check_adr.py gains section validation + promotion gate (154 tests)
- configure_repo.py auto-installs commit-msg hook
- README rewritten, CLAUDE.md updated with new scripts/conventions
- deploy.yml gated to main; quality.yml gains new script test jobs
- 6 ADRs promoted from proposed to accepted

**Moved/Renamed table:**
- aidx → multi_phase_ai_pipeline.md (rewritten)
- slm_from_scratch → extracted to research monorepo
- BROKEN_LINKS_EXCLUDE_DIRS → VALIDATION_EXCLUDE_DIRS (10+ files)
- ADR-26004..26008 → superseded by ADR-26027, ADR-26028

---

## Step 2: Update README.md "What's new?"

**File:** `README.md` lines 22-38

- Prepend v2.5.0 entry (5 bullets: Automated CHANGELOG, Tool-Agnostic Architecture, Promotion Gate, Ecosystem Cleanup, Validation Expansion)
- Keep v2.4.0 and v2.3.0 entries as-is
- Remove v2.2.0 entry

---

## Step 3: Write Telegram post

**File:** `misc/pr/tg_channel_ai_learning/2026_02_17_release_announcement_v2_5_0.md`

Structure (following v2.4.0 post style):
- URL line → headline with version and name
- Opening: problem of ungoverned commits and manual CHANGELOG
- Section 1 (📝): Automated commit governance — validator, changelog generator, auto-installed hook, last manual release notes
- Section 2 (🏗): Tool-agnostic architecture — ADR triage, cognitive roles, Multi-Phase AI Pipeline
- Section 3 (🧹): Ecosystem cleanup — research monorepo, pyproject.toml SSoT, 6 ADRs promoted
- Personal note about this being the last manually-written release notes
- Link to GitHub release
- Hashtags: #ai_engineering_book #ADR #CHANGELOG #CommitConventions

**Language:** Russian, personal voice, product-focused

---

## Exclusions

- Gherkin/BDD analysis (internal research, not product feature)
- Individual file paths in release notes (product-level only)
- PR/telegram posts created during the cycle

## Verification

- RELEASE_NOTES.md has v2.5.0 before v2.4.0
- README.md "What's new?" has exactly 3 entries (v2.5.0, v2.4.0, v2.3.0)
- Telegram post follows established format from previous posts
- All content is product-focused, not implementation-focused
