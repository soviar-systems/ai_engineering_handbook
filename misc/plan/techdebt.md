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

### TD-003: ADR deprecation workflow not formalized (2026-03-02)

- **Location:** `architecture/adr/adr_config.yaml` (status `deprecated`), `architecture/adr/adr_template.md`, `tools/scripts/check_adr.py`
- **Context:** The `deprecated` status is defined in `adr_config.yaml` and mapped to the "Historical Context" index section, but unlike `rejected` (which has a conditional `Rejection Rationale` section and template support), deprecation has no template guidance, no conditional section, and no validation rules in `check_adr.py`. No ADRs have used this status yet.
- **Current state:** Provisional guidance documented in [Architecture Decision Workflow](/architecture/architecture_decision_workflow_guide.md). The guide marks the deprecation section as "not yet formalized."
- **Migration path:** When the first ADR needs deprecation: (1) add a conditional `Deprecation Rationale` section to `adr_template.md`, (2) add validation rules to `adr_config.yaml` and `check_adr.py`, (3) remove the "not yet formalized" caveat from the guide.
- **Introduced by:** plan_20260302_adr_writing_guide.md

## Resolved
