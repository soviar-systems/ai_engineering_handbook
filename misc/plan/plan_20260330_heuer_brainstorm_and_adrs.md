# Plan: Heuer Brainstorm + ADRs (Phases 3-6)

Continuation of `misc/plan/plan_20260329_heuer_wrc_qwen_parser.md`. Phases 1-2 complete.

## Context

[A-26019](/architecture/evidence/analyses/A-26019_heuer_methodology_integration_for_consultant_prompts.md) extracted 7 insights from `S-26019` (Qwen 3.5 dialogue on Heuer methodology). Key findings:

1. Heuer = instructions not RAG (procedural enforcement vs informational retrieval)
2. Transformer satisficing ≈ human satisficing (Chapter 4) — **research hypothesis, not established fact** (see analytical note in Insight #2)
3. ACH maps to existing Methodology Comparison table — gap is diagnosticity
4. Disconfirmation > Confirmation (Popperian logic)
5. Linchpin Analysis for assumption identification (impact column needed)
6. Heuer structures human consumption of AI output, not AI cognition
7. Qwen's refined prompt in A-26019 Appendix provides concrete integration blueprint

Open research question: "transformer satisficing under token pressure" — does instruction-following degrade with context length, and is this mechanistically parallel to human satisficing?

## Phase 3: Brainstorm Session

Conduct a brainstorm session by directly utilizing the consultant system prompts in `ai_system_layers/3_prompts/consultants/` (selecting the most relevant archetype, e.g., the hybrid consultant) to stress-test A-26019 conclusions.

### Challenge Questions

1. Is Heuer cargo-cult reasoning for transformers, or genuinely useful structuring?
2. Does the token cost of Heuer instructions (~200-300 tokens) justify the output quality improvement?
3. Are there lighter alternatives — just ACH, skip the rest?
4. Does Heuer help equally across consultant archetypes (hybrid vs devops vs local)?
5. Is "transformer satisficing" a real mechanistic parallel or a misleading analogy?
6. The Qwen refined prompt (A-26019 Appendix) — what would we change before adopting it?

### Inputs for Brainstorm

- [A-26019](/architecture/evidence/analyses/A-26019_heuer_methodology_integration_for_consultant_prompts.md) — the analysis to challenge
- `ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json` — current production prompt
- A-26019 Appendix — Qwen's refined prompt with Heuer integration

## Phase 4: ADRs (parallel, after brainstorm)

### WS-2: Heuer Integration ADR

- Number: assigned dynamically via `check_adr.py`
- Decision: Embed Heuer tradecraft as procedural instructions in WRC-bearing consultant prompts via a shared common block
- Common block: `ai_system/3_prompts/consultants/blocks/heuer_tradecraft.json` — SSoT
- Key content: `tradecraft_standards`, `bias_check_protocol` (4-step), `ach_mandatory`, `heuristics_mitigation`
- Evidence: A-26019, brainstorm findings
- Token budget: measure block cost, set ceiling

### WS-3: WRC Formalization ADR

- Number: assigned dynamically
- Decision: Formalize WRC as ecosystem evaluation metric
- Formula: `WRC = 0.35*E + 0.25*A + 0.40*P`
- Thresholds: >=0.89 production-ready, P<0.70 after SVA = PoC-only
- SVA relationship: `P_final = P_raw - (violations * 0.10)`
- Resolves: TD-006

## Phase 5: prepare_prompt.py `_includes` Block Composition

- Prerequisite: WS-2 accepted (block format defined)
- Add `_includes` resolution step to prepare_prompt.py
- Tests: 0 includes (no-op), 1 include, 2 includes, missing file (exit 1)

## Phase 6: Cleanup

1. Resolve TD-006 in `techdebt.md`
2. Update TD-007 — note A-26019 as related evidence
3. Run validation suite: `check_evidence.py`, `check_adr.py --fix`, `check_broken_links.py`, `check_json_files.py`
4. Pre-commit hooks pass

## Critical Files

| File | Role |
|---|---|
| `architecture/evidence/analyses/A-26019_heuer_methodology_integration_for_consultant_prompts.md` | Analysis to challenge in brainstorm |
| `architecture/evidence/analyses/A-26023_heuer_brainstorm_stress_test.md` | Brainstorm results and agentic pipeline proposal |
| `ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json` | Primary WRC prompt, Heuer target |
| `ai_system/3_prompts/consultants/local_ai_systems_consultant.json` | WRC prompt #2 |
| `ai_system/3_prompts/consultants/devops_consultant.json` | WRC prompt #3 |
| `tools/scripts/prepare_prompt.py` | Needs `_includes` resolution |
| `misc/plan/techdebt.md` | TD-006 (WRC), TD-007 (format-as-contract) |
