# Plan: Mandate File Paths in Structured Commit Body Bullets

## Context

The user identified a traceability gap in ADR-26024's structured commit body format. The current spec defines:

```
- <Verb>: <target> — <why/impact>
```

But `<target>` is **never defined** — it could be a file path, a concept, a description, or nothing at all. The result: developers reading the generated CHANGELOG see actions without knowing which files were affected.

### Evidence from Real Commits

The examples in `01_production_git_workflow_standards.md:231-268` **already use file paths** as targets:
```
- Created: `tools/docs/website/01_github_pages_deployment.(md|ipynb)` — ...
- Deleted: `tools/docs/git/github_pages_setup.md` — ...
- Refactored: `02_self_hosted_deployment.md` — ...
```

But real commits diverge because the format spec doesn't mandate this:

| Commit | Target quality | Example |
|--------|---------------|---------|
| `3e652bc` (docs: restructure) | File paths in backticks | `tools/docs/website/01_github_pages_deployment.(md\|ipynb)` |
| `57b38c6` (feat: formalize) | File paths without verb prefix | `architecture/adr/adr_26025...md — Fat ADR` |
| `9a25cd4` (docs: ADR-26024 Phase A) | **Empty targets** | `Created:  — codifies the Rich-Body Squash...` |
| `5d839d8` (docs: update CLAUDE.md) | Descriptions, not paths | `Content Frontmatter section under Critical Conventions` |
| `62976e6` (docs: update Plan 2) | Descriptions, not paths | `complex commit example in structured commit bodies plan` |

The convention's own adoption commit (`9a25cd4`) has empty targets — the file paths are literally missing.

### Root Cause

The format template `- <Verb>: <target>` treats `<target>` as freeform text. Without a definition, contributors fill it with whatever feels natural — sometimes file paths, sometimes descriptions, sometimes nothing.

## Proposed Change

Define `<target>` as a **file path** (relative to repo root), wrapped in backticks. Update the format to:

```
- <Verb>: `<file-path>` — <what/why>
```

### Terminology Choice: `<what/why>` over `<why/impact>`

This is a **CHANGELOG**, not just release notes. A changelog entry should explain **what** changed in that file and **why**. The verb + file-path gives the action and location; the description completes the picture with the substance and motivation.

### Rules for `<file-path>`

1. **Single file**: `` `tools/scripts/check_adr.py` ``
2. **Glob/pair**: `` `tools/docs/website/01_github_pages_deployment.(md|ipynb)` ``
3. **Multiple related files** (same verb, same reason): `` `adr_26001.md`, `adr_26002.md`, `adr_26003.md` `` — or use a glob `` `architecture/adr/adr_260{01,02,03}.md` ``
4. **Rename/move**: `` `old_name.py` → `new_name.py` ``
5. **Every change lives in a file** — always use the nearest file path. Dependencies → `` `pyproject.toml` ``, CI variables → `` `deploy.yml` ``, config keys → `` `myst.yml` ``. No conceptual/abstract targets allowed.

### Changelog Output Comparison

**Before** (current — ambiguous targets):
```
* ADR Validation Toolchain:
    - Created: ADR formalization document — codifies the Rich-Body Squash strategy
    - Updated: production git workflow guide — resolved 8 contradictions
```

**After** (file paths mandatory):
```
* ADR Validation Toolchain:
    - Created: `architecture/adr/adr_26024...md` — codifies the Rich-Body Squash strategy
    - Updated: `tools/docs/git/01_production_git_workflow_standards.md` — resolved 8 contradictions
```

A developer reading the second version knows exactly where to look.

## Files to Modify

1. **`architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md`** — Update the format definition in Section 1 ("Mandate structured bullet bodies") to define `<target>` as a file path in backticks. Add a brief "Target Rules" subsection. Change `<why/impact>` → `<what/why>`.

2. **`tools/docs/git/01_production_git_workflow_standards.md`** — Update the Body Convention format (line 208) and Rules section (line 216+) to include `<target>` definition. Change `<why/impact>` → `<what/why>`. The examples (lines 231-268) already comply — no changes needed there.

3. **`CLAUDE.md`** — Update the commit conventions bullet from `- <Verb>: <target> — <why/impact>` to `- <Verb>: \`<file-path>\` — <what/why>` with a brief note on what constitutes a valid target.

## Verification

- Read all three modified files to confirm consistency
- Check that existing compliant examples (like `3e652bc`) still match the updated format
- The change is documentation-only; no scripts or hooks need modification (the `validate_commit_msg.py` regex checks for bullet presence, not target format — file-path validation can be a separate future enhancement)
