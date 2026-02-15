# Plan: Triage ADR-26004..26008 — From Tool-Specific to Tool-Agnostic

## Context

Five proposed ADRs (26004–26008) formalize an `aider`/`aidx`-specific AI development pipeline. They were never accepted. The methodology has since evolved: the repo aims to teach **tool-agnostic** AI engineering principles, and the author plans to build custom agentic systems. Binding the methodology to any specific tool (aider, Claude Code, or otherwise) contradicts this goal.

The ADRs contain two layers: (1) tool-specific tooling prescriptions (outdated), and (2) valuable conceptual frameworks (model taxonomy, phase separation) that are tool-agnostic and should be preserved.

## Changes

### 1. Reject ADR-26004 and ADR-26005 (tool-specific tooling)

Both prescribe aider/aidx as the orchestration backbone. Reject because tool-specific prescriptions don't belong in a tool-agnostic methodology.

**Files:**
- `architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md` — `status: rejected`
- `architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md` — `status: rejected`

**Each file gets:**
- YAML: `status: proposed` → `status: rejected`
- Body: Status section updated + `## Rejection Rationale` section added (no existing rejected ADRs in the repo — this establishes the pattern, placed after Status like supersession notes in ADR-26018/26019)
- Rationale framing: methodology must remain tool-agnostic; concepts like the Research-Apply pipeline and Hybrid Bridge remain valid patterns documented elsewhere, but mandating a specific tool contradicts the repo's goals

### 2. Supersede ADR-26006 and ADR-26008 → new ADR-26027

Both contain the Reasoning-Class vs. Agentic-Class model taxonomy — valuable, tool-agnostic knowledge — but bind it to aidx phases.

**Files to update:**
- `architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md` — `status: superseded`, `superseded_by: ADR-26027`
- `architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md` — `status: superseded`, `superseded_by: ADR-26027`

**New file:**
- `architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md` — `status: proposed`

ADR-26027 key points:
- Extracts the Reasoning/Agentic taxonomy as a **selection heuristic**, not a phase mandate
- Two axes: Reasoning-Class (abstract synthesis, GPQA ceiling) vs. Agentic-Class (instruction adherence, tool-use precision)
- Acknowledges modern models can combine both axes — no rigid one-model-per-phase coupling
- References the existing notebook: `ai_system/2_model/selection/general_purpose_vs_agentic_models.ipynb`
- No tool names — framework applies to any orchestration approach

### 3. Supersede ADR-26007 → new ADR-26028

ADR-26007's Phase 0 concept is valid, but the ADR is tightly coupled to `aidx` pipeline and cannot be modified in place (ADR immutability). Supersede it with a new tool-agnostic ADR.

**File to update:**
- `architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md` — `status: superseded`, `superseded_by: ADR-26028`

**New file:**
- `architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md` — `status: accepted`

ADR-26028 key points:
- Preserves the Phase 0 principle: human-led discovery with a reasoning-class model before automated execution
- Tool-agnostic framing — no specific CLI tool mandated
- **Primary implementation**: The repo's `ai_system/3_prompts/consultants/` JSON prompts (e.g., `local_ai_systems_consultant.json`, `handbook_consultant.json`) are the recommended Phase 0 interface. These prompts encode the repo's methodology (WRC scoring, Simplest Viable Architecture, peer review) and are designed for use with capable reasoning-class models in any web chat interface
- References ADR-26027 for model selection guidance (reasoning-class for Phase 0)
- Supersedes ADR-26007

### 4. Update ADR index

**File:** `architecture/adr_index.md`

- Add ADR-26027 to Evolutionary Proposals
- Add ADR-26028 to Active Architecture (status: accepted)
- Move ADR-26004, 26005, 26006, 26007, 26008 to Historical Context (with rejected/superseded annotations)

### 5. Update cross-referencing content notebooks

**Blast radius** (found by Plan agent):

| File | References | Action |
|------|-----------|--------|
| `ai_system/2_model/selection/general_purpose_vs_agentic_models.md` | ADR-26006, ADR-26008 heavily | Replace with ADR-26027 refs, generalize aidx language |
| `ai_system/2_model/selection/choosing_model_size.md` | ADR-26005, ADR-26006 | Replace with ADR-26027 refs |
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` | ADR-26004, 26005, 26006 | Add `:::{warning}` deprecation notice (aidx-specific tooling no longer primary; concepts remain valid) |
| `RELEASE_NOTES.md` | Historical mentions | No changes (factual history) |

All paired `.md` files need `uv run jupytext --sync` after editing.

## Order of Operations

1. Create ADR-26027 (must exist before 26006/26008 can point to it)
2. Create ADR-26028 (must exist before 26007 can point to it)
3. Update ADR-26006 → superseded by 26027
4. Update ADR-26008 → superseded by 26027
5. Update ADR-26007 → superseded by 26028
6. Update ADR-26004 → rejected
7. Update ADR-26005 → rejected
8. Update `adr_index.md`
9. Update content notebooks (3 files)
10. Run `uv run jupytext --sync` on modified paired files
11. Run verification (broken links, ADR validation, pre-commit)

## Progress (as of 2026-02-15)

- [x] Task 1: Create ADR-26027
- [x] Task 2: Create ADR-26028
- [x] Task 3: ADR-26006 → superseded by 26027
- [x] Task 4: ADR-26008 → superseded by 26027
- [x] Task 5: ADR-26007 → superseded by 26028
- [x] Task 6: ADR-26004 → rejected + rejection rationale
- [x] Task 7: ADR-26005 → rejected + rejection rationale
- [x] ADR template updated with conditional `## Rejection Rationale`
- [x] Task 8: Update `adr_index.md` (via `check_adr.py --fix`)
- [x] Task 9: Update content notebooks (2 of 3 — aidx article deferred to separate plan)
- [x] Task 10: Run `jupytext --sync`
- [x] Task 11: Verification (all green)
- [x] ADR-26027 promoted to `accepted` status
- [x] ADR-26028 broken links fixed (directory → specific JSON files)

### Deferred

- aidx article rewrite → see `plan_20260215_rewrite_aidx_article_tool_agnostic.md`

## Verification

1. `uv run tools/scripts/check_broken_links.py --pattern "architecture/adr/*.md"`
2. `uv run tools/scripts/check_broken_links.py --pattern "ai_system/**/*.md"`
3. `uv run jupytext --sync` on modified paired notebooks
4. `myst build --html` — verify no cross-reference errors
5. Pre-commit hooks will validate ADR format, links, and jupytext sync on commit
