# Technical Debt Register

Traceable record of intentional shortcuts. Each entry has a date, location, and migration path.

## Open

### TD-001: common_required_fields in evidence.config.yaml (2026-02-27)

- **Location:** `architecture/evidence/evidence.config.yaml` → `common_required_fields`, `date_format`
- **Context:** All evidence artifact types share common frontmatter fields (`id`, `title`, `date`) and a date format. These belong in a repo-wide central frontmatter standard that doesn't exist yet.
- **Current state:** Defined directly in `evidence.config.yaml` so that `check_evidence.py` and its tests have a single SSoT instead of hardcoded values.
- **Migration path:** When a central frontmatter standard config is created, remove these keys from `evidence.config.yaml` and replace with a pointer (like `parent_config` does for tags).
- **Introduced by:** plan_20260227_architecture_knowledge_base_taxonomy_tooling.md (Batch 2)

### TD-002: Technical Debt Register has no formal governance (2026-02-27)

- **Location:** `misc/plan/techdebt.md` (this file)
- **Context:** This register was created ad-hoc to track intentional shortcuts. There is no ADR, config, or script governing its format, naming convention, ID scheme, or lifecycle (when entries move from Open to Resolved).
- **Current state:** Free-form markdown in `misc/plan/`. Not validated by CI, not referenced by any ADR.
- **Migration path:** Write an ADR formalizing the tech debt tracking convention (format, ownership, review cadence). Optionally add a validation script and pre-commit hook following the ADR-26011 script suite pattern.
- **Introduced by:** plan_20260227_architecture_knowledge_base_taxonomy_tooling.md (Batch 2)

## Resolved
