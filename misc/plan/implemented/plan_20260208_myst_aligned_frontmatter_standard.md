# Plan: MyST-Aligned Frontmatter Standard (ADR-26023)

## Context

ADR-26018 mandated YAML frontmatter with non-MyST field names (`owner`, `last_modified`). ADR-26019 proposed a reflection block script to render these custom fields on the static site. Investigation revealed that MyST natively renders `title`, `author`/`authors`, and `date` — making custom field names and reflection block scripts unnecessary for content articles. This plan aligns field names with the MyST frontmatter API and supersedes both ADRs.

The onboarding notebook (`0_intro/00_onboarding.ipynb`) already has the correct frontmatter format from earlier work. The "Document Metadata Conventions" section in onboarding still references the old ADRs and reflection block pattern — it needs updating.

---

## Step 0: Save plan to `misc/plan/`

**File:** `misc/plan/plan_20260208_myst_aligned_frontmatter_standard.md`

Copy this plan file content there for decision history.

---

## Step 1: Create ADR-26023

**New file:** `architecture/adr/adr_26023_myst_aligned_frontmatter_standard.md`

ADR frontmatter:
```yaml
---
id: 26023
title: "MyST-Aligned Frontmatter Standard"
date: 2026-02-08
status: accepted
superseded_by: null
tags: [governance, documentation, context_management]
---
```

Key sections:
- **Context**: ADR-26018 used non-MyST names; ADR-26019 proposed reflection scripts. MyST renders `title`, `author`, `date` natively, making both approaches obsolete for content articles.
- **Decision**: Adopt MyST-native field names. Two-block Jupytext structure required. `version`/`birth` go under `options.*` (not rendered by default theme — future custom template work). Reflection block scripts are eliminated for content articles. ADRs retain their own body/YAML sync needs per ADR-26016/26017.
- **Canonical schema**: `title`, `author`/`authors`, `date`, `options.version`, `options.birth`
- **Consequences**: Positive — native rendering, no custom scripts needed. Negative — `version`/`birth` not visible on site until custom template work.

---

## Step 2: Mark ADR-26018 as superseded

**File:** `architecture/adr/adr_26018_universal_yaml_frontmatter_adoption.md`

Changes:
- YAML: `status: superseded`, `superseded_by: ADR-26023`
- Body `## Status` section: `superseded` + `Superseded by: ADR-26023`

---

## Step 3: Mark ADR-26019 as superseded

**File:** `architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md`

Changes:
- YAML: `status: superseded`, `superseded_by: ADR-26023`
- Body `## Status` section: `superseded` + `Superseded by: ADR-26023`

---

## Step 4: Update companion article — yaml_frontmatter_for_ai_enabled_engineering.md

**File:** `ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md`

Changes:
- Replace old reflection block (`Owner/Version/Birth/Last Modified`) with MyST-aligned frontmatter block (second `---` block with `title`, `author`, `date`, `options`)
- Update seealso box: reference ADR-26023 instead of ADR-26018/26019
- Section 3 example: replace `owner`/`version`/`last_modified` with `author`/`date`/`options.*`
- Remove references to planned `sync_metadata.py` script (no longer needed)
- Section 5 (Pitfalls): remove "Metadata Drift" and "Positional Fragility" items about reflection blocks
- Section 6 (Onboarding): replace old instructions with new MyST-aligned schema instructions

Then sync: `uv run jupytext --sync ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md`

---

## Step 5: Update companion article — reflected_metadata_pattern.md

**File:** `ai_system/5_context/reflected_metadata_pattern.md`

Changes:
- Replace old reflection block with MyST-aligned frontmatter block
- Add a prominent `:::{admonition} Superseded` box at the top (after seealso) explaining: MyST renders `author`/`date` natively via ADR-26023; the reflection block pattern is no longer needed for content articles. This article is retained as historical reference.
- Update seealso box: reference ADR-26023
- Keep the article body largely intact as historical documentation of the pattern

Then sync: `uv run jupytext --sync ai_system/5_context/reflected_metadata_pattern.md`

---

## Step 6: Update 0_intro/00_onboarding.ipynb metadata section

**File:** `0_intro/00_onboarding.ipynb` — the "Document Metadata Conventions" section (cells `f3b6ecc0` and `3e913afc`)

Current text references ADR-26018, ADR-26019, and the reflection block pattern. Update to:
- Reference ADR-26023 as the governing standard
- Remove mention of reflection blocks
- Keep links to the two companion articles (they now contain updated/historical content)

Then sync: `uv run jupytext --sync 0_intro/00_onboarding.ipynb`

---

## Verification

1. `uv run jupytext --sync 0_intro/00_onboarding.md` — confirm two-block structure preserved in `.md`
2. `uv run jupytext --sync ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md` — sync succeeds
3. `uv run jupytext --sync ai_system/5_context/reflected_metadata_pattern.md` — sync succeeds
4. Visual check: all modified `.md` files have correct YAML structure
