# Technical Debt Register

Traceable record of intentional shortcuts. Each entry has a date, location, and migration path.

## Open

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

### TD-004: Script suite triad doc requirement is redundant (2026-03-23)

- **Location:** ADR-26011, `tools/scripts/check_script_suite.py`, `tools/docs/scripts_instructions/`
- **Context:** ADR-26011 mandates script + test + doc triad. With contract docstrings now required in every module (CLAUDE.md convention) and tests documenting contracts by example, the per-script instruction docs duplicate what's already in the code. Docs fall out of sync on every config change (e.g., YAML→JSON migration required bulk doc updates). When vadocs is extracted as a package, API docs auto-generate from docstrings — per-script docs won't survive.
- **Current state:** Triad enforced by `check_script_suite.py` pre-commit hook. 15+ doc files in `tools/docs/scripts_instructions/`, each Jupytext-paired (.md + .ipynb).
- **Analysis:** [A-26014](/architecture/evidence/analyses/A-26014_script_suite_doc_redundancy.md)
- **Migration path:** (1) Supersede ADR-26011 with new ADR relaxing triad to script + test (doc optional), (2) update `check_script_suite.py` to drop doc requirement, (3) let existing docs age out, (4) new modules only need docstrings. Plan as dedicated task after step 7 completion.
- **Introduced by:** step 7 config migration session (2026-03-23)

### TD-005: check_frontmatter.py needed for hub-level validation (2026-03-23)

- **Location:** `.vadocs/conf.json` (field_registry, blocks), `check_adr.py`, `check_evidence.py`
- **Context:** Hub config defines block composition (identity, discovery, lifecycle), authors format, type registry, but no script validates these. Domain scripts only check spoke-level required_fields. Block enforcement, authors format validation, and type field checking are missing.
- **Current state:** Frontmatter validation is split across domain scripts, each implementing its own subset. Standardized frontmatter (ADR-26042) enables a single shared validator.
- **Migration path:** (1) Create `check_frontmatter.py` validating hub blocks + spoke rules for all .md files, (2) refactor domain scripts to delegate frontmatter checks, (3) add pre-commit hook. Plan exists conceptually — needs formal plan file.
- **Introduced by:** step 7 config migration session (2026-03-23)

### TD-006: WRC scoring has no governing ADR (2026-03-29)

- **Location:** `ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json`, `ai_system/3_prompts/consultants/devops_consultant.json`
- **Context:** WRC (Weighted Response Confidence) is a scoring metric embedded directly in two consultant prompts. It is referenced in ADR-26037 (SVA framework) and in release notes, but there is no ADR defining its scope, formula rationale, component weights, or lifecycle. It is currently an undocumented architectural decision — the metric exists and is in use, but its authority comes from the prompt JSON, not from a governed decision record.
- **Current state:** Formula and component definitions live in the `system_context` block of `ai_systems_consultant_hybrid.json`. ADR-26037 references WRC as an implementation detail of SVA penalties but does not define it.
- **Migration path:** Write ADR-260xx defining WRC as an ecosystem evaluation standard: formula, component definitions (E/A/P), weight rationale, threshold semantics (≥0.89 = production-ready), and relationship to SVA constraints. Update prompt JSONs to reference the ADR rather than embed the authoritative definition.
- **Introduced by:** v2.8.0 release notes session (2026-03-29)

### TD-007: Format as model-specific semantic contract — open research question (2026-03-29)

- **Location:** ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md, Section 4
- **Context:** If format response is learned from training corpus, the same format primes different cognitive modes in models trained on different corpora. Format becomes a hidden variable in cross-model instruction-following benchmarks.
- **Evidence needed:** Controlled experiment — same semantic content × multiple formats (JSON/YAML/Markdown) × multiple models (Claude, Qwen, GigaChat, Gemini) × behavioral outcome (instruction adherence rate, section survival, field preservation).
- **Collection opportunity:** Local AI community meetup presentation — audience uses multiple models across Cursor/Cline/LangFlow, can contribute informal observations.
- **Future artifact:** S-YYNNN (collected evidence) → A-26019 (analysis) → Section 4 update
- **Introduced by:** meetup talk brainstorming session (2026-03-29)

## Resolved

### TD-001: common_required_fields in evidence.config.yaml (2026-02-27)
- Resolved by ADR-26042 (Common Frontmatter Standard) — hub-and-spoke config replaces fragmented common_required_fields
- Resolved: 2026-03-11
