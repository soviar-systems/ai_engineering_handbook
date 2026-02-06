# Plan: Finish Two 5_context Companion Articles

## Overview

Rewrite two content articles in `ai_system/5_context/` to align with the just-revised ADR-26018 and ADR-26019. Both are currently untracked (never committed).

| Article | Companion ADR | Assessment |
|---------|---------------|------------|
| `yaml_frontmatter_for_ai_enabled_engineering.md` | ADR-26018 | **Moderate rewrite** — content is mostly solid, needs metadata block, ADR refs, real examples |
| `reflected_metadata_pattern.md` | ADR-26019 | **Complete rewrite** — entirely built on rejected HTML anchor mechanism |

---

## Step 1: Rewrite `reflected_metadata_pattern.md` (complete rewrite)

The entire article is built on the phantom HTML anchor mechanism (`<!-- meta -->`) that ADR-26019 explicitly rejected. It even labels the existing `---` pattern as "Incorrect" — the exact opposite of the revised ADR.

### Structure (6 sections, keep skeleton, rewrite all content):

**Header:** Keep Jupytext header as-is.

**Title + metadata block + intro + seealso:** Add standard reflection block after title. Rewrite intro paragraph to introduce the pattern as a **positional projection** of YAML frontmatter using the established `+++`/`---`/prose/`---`/`+++` convention. Add `:::{seealso}` linking to ADR-26019 (governing), ADR-26018 (prerequisite), and the yaml_frontmatter companion article.

**Section 1 "The Architecture of Transparency":** Rewrite. Problem: YAML is invisible in CLI/diffs. Solution: positional convention — first cell after H1 title is reserved for human-readable mirror. No new syntax — formalizes existing pattern used across 20+ articles.

**Section 2 "Implementation: The Positional Convention":** Complete inversion. Show the `+++`/`---`/prose/`---`/`+++` pattern as CORRECT (with target-state example from ADR-26019). Show HTML anchors as the REJECTED alternative with reasoning from ADR-26019.

**Section 3 "Automation: The `sync_metadata.py` Pre-Commit Hook":** Rewrite for planned tool at `tools/scripts/sync_metadata.py`. Steps: Parse YAML → Locate first post-title cell → Validate format → Format from YAML values → Replace → jupytext sync. Show pre-commit config using `uv run`. Add `:::{important}` note: script does not yet exist, planned per ADR-26019, will follow ADR-26011 script suite convention.

**Section 4 "CI Integration: Validation Gates":** Rewrite. Drop hash-check and anchor-presence. Reference existing infrastructure: `jupytext-verify-pair` hook, `check_broken_links.py`, `check_adr.py`. Planned: reflection block presence/format validation.

**Section 5 "RAG Integration: Stripping the First Post-Title Cell":** Moderate rewrite. Keep the 3-step ingestion strategy (Extract YAML → Strip mirror → Result) and comparison table — just replace HTML anchor mechanism with positional convention. Table column: "Reflected Block (Positional)" instead of "(Anchored)".

**Section 6 "Technical Debt & Pitfalls":** Rewrite. Three pitfalls:
1. Jupytext Drift (keep from current) — always modify metadata in `.md`
2. Positional Fragility (new, from ADR-26019) — content inserted between title and reflection block breaks sync
3. Prerequisite Dependency on ADR-26018 (new) — pattern is inert until YAML fields exist

Remove the placeholder prompt line at the end.

---

## Step 2: Rewrite `yaml_frontmatter_for_ai_enabled_engineering.md` (moderate rewrite)

Content is largely sound. Main work: add metadata block, add ADR refs, replace fictional example with real one.

### Changes:

**Add metadata reflection block** after title (Owner/Version/Birth/Last Modified in standard `+++`/`---` pattern).

**Add `:::{seealso}`** after intro paragraph: ADR-26018 (governing), ADR-26019 (companion), link to reflected_metadata_pattern article.

**Section 1-2:** Keep as-is. Executive Summary and RAG/SNR rationale are solid.

**Section 3 "Practical Implementation":** Replace fictional "Neural Network Pruning Strategies" example with real example based on `aidx_industrial_ai_orchestration_framework.md`. Show the target state: Jupytext header + ADR-26018 mandatory fields (`owner`, `version`, `birth`, `last_modified`) + reflection block below title. Add note about Jupytext hooks (`jupytext-sync`, `jupytext-verify-pair`).

**Section 4:** Keep comparison table as-is.

**Section 5 "Pitfalls":** Keep existing 3 items. Add 4th: Positional Fragility (from ADR-26019). Update Metadata Drift mitigation to reference planned `sync_metadata.py`.

**Section 6 "Actionable Strategy":** Make concrete to this repo: reference ADR-26018 mandatory fields, actual pre-commit hooks, ADR-26021 content lifecycle.

---

## Step 3: Sync and verify

```bash
uv run jupytext --sync ai_system/5_context/reflected_metadata_pattern.md
uv run jupytext --sync ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md
uv run tools/scripts/check_broken_links.py --pattern "ai_system/5_context/*.md"
```

---

## Step 4: Atomic commits

1. `docs: Rewrite reflected_metadata_pattern to align with revised ADR-26019`
2. `docs: Update yaml_frontmatter_for_ai_enabled_engineering with ADR refs and real examples`

---

## Critical files

| File | Role |
|------|------|
| `ai_system/5_context/reflected_metadata_pattern.md` | Complete rewrite target |
| `ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md` | Moderate rewrite target |
| `architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md` | Authoritative source for reflected metadata decisions |
| `architecture/adr/adr_26018_universal_yaml_frontmatter_adoption.md` | Authoritative source for YAML frontmatter decisions |
| `ai_system/2_model/selection/choosing_model_size.md` | Quality-bar reference (newest article) |
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` | Real example for Section 3 of yaml_frontmatter article |
