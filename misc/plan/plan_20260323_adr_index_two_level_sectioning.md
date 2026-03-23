---
title: "ADR Index Two-Level Sectioning and Tag Vocabulary Audit"
date: 2026-03-23
---

# Plan: ADR Index Two-Level Sectioning and Tag Vocabulary Audit

## Context

Brainstorming (2026-03-23, A-26012) identified that the ADR index is a flat list of 22+
entries per status section — hard to scan. The `architecture` tag appears on 75% of ADRs,
making it tautological. Analysis produced a two-level index design (status × primary tag)
and identified 7 ADRs needing re-tagging.

**Prerequisite:** `misc/plan/plan_20260320_ecosystem_governance_model_config_architecture.md`
step 7 must be complete (configs migrated to `.vadocs/types/`, JSON format).

## Steps

### 1. Re-tag 7 ADRs that only have `[architecture]`

Update frontmatter `tags:` field — change first (primary) tag to the meaningful one:

| ADR | Current tags | New tags |
|-----|-------------|----------|
| 26009 | [architecture] | [devops] |
| 26010 | [architecture] | [testing] |
| 26011 | [architecture] | [governance] |
| 26012 | [architecture] | [governance] |
| 26013 | [architecture] | [workflow] |
| 26014 | [architecture] | [documentation] |
| 26015 | [architecture] | [ci] |

### 2. Audit remaining ADRs — demote `architecture` from first position

For ADRs where `architecture` is first tag but a more specific tag exists, move
`architecture` to secondary position. Examples:

- `[architecture, context_management]` → `[context_management, architecture]`
- `[architecture, git]` → `[git]` (git is specific enough)
- `[architecture, devops]` → `[devops]`
- `[architecture, model, workflow]` → `[model, workflow]`

Keep `architecture` only where the ADR is genuinely about system structure
(e.g., ADR-26020 hub-and-spoke, ADR-26043 package boundary).

### 3. Split Historical Context into Rejected and Superseded

Update `.vadocs/types/adr.conf.json` sections mapping:

```
Before:
  "Historical Context": ["rejected", "superseded", "deprecated"]

After:
  "Active Architecture": ["accepted"],
  "Evolutionary Proposals": ["proposed"],
  "Rejected": ["rejected"],
  "Superseded": ["superseded"],
  "Deprecated": ["deprecated"]
```

### 4. Add primary tag convention to adr.conf.json

Add a `primary_tag_sectioning` key (or similar) that tells check_adr.py to
sub-group entries by first tag within each status section.

### 5. Update check_adr.py index generation (TDD)

- Modify `build_index()` / `generate_index()` to produce two-level output
- Each status section contains tag sub-sections with `### tag_name (N)` headers
- Each sub-section is a MyST `{glossary}` block
- Empty sections/sub-sections omitted
- Tag sub-sections sorted alphabetically within each status section

Tests:
- Index generation with two-level structure
- Empty sub-sections omitted
- Primary tag extraction (first tag in list)
- ADRs with no tags produce error

### 6. Document the convention

- Add note to `adr_index.md` header explaining: first tag = primary, determines sub-section
- Update `adr_template.md` comment: first tag should be the most specific domain
- Update `architecture_decision_workflow_guide.md` tagging guidance
- Update CLAUDE.md

### 7. Run full verification

- `uv run tools/scripts/check_adr.py --fix` regenerates two-level index
- `uv run pytest tools/tests/test_check_adr.py` passes
- `uv run tools/scripts/check_broken_links.py` passes
- Visual review of generated `adr_index.md`
