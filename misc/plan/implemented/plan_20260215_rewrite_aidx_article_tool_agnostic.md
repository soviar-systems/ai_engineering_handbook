# Future Plan: Rewrite aidx Article as Tool-Agnostic Multi-Phase Pipeline

## Context

During the ADR-26004..26008 triage, the `aidx_industrial_ai_orchestration_framework.md` article was identified as violating ADR-26021 (Content Lifecycle Policy). The article prescribes `aidx`/`aider` as the orchestration backbone, but the methodology has evolved toward tool-agnostic principles.

Per ADR-26021: stale content articles should be **deleted** (git history is the archive), not deprecated. However, two unique concepts need extraction first.

## Unique Value to Extract

1. **Research-Apply pipeline (5-phase model)**: Research → Planning → Execution → Validation → Review. This general pattern (decouple knowledge retrieval from code generation) is not fully documented elsewhere in tool-agnostic form.

2. **Namespace partitioning for RAG**: Splitting retrieval into `Global_Workflows` and `Project_Specific` collections for precision. This is a general RAG best practice not covered in other content articles.

## Already Covered Elsewhere

- Model taxonomy (Reasoning/Agentic/Thinking) → ADR-26027 + `general_purpose_vs_agentic_models.md`
- Phase 0 intent synthesis → ADR-26028
- VRAM isolation / KV cache gating → `choosing_model_size.md`
- Engineering standards (pre-commit, gitlint) → ADR-26001/26002/26003

## Proposed Changes

1. Create a new tool-agnostic article (e.g., `ai_system/4_orchestration/workflows/multi_phase_ai_pipeline.md`) that documents the Research-Apply pipeline and namespace partitioning without tool coupling
2. Delete `aidx_industrial_ai_orchestration_framework.md` and its `.ipynb` pair
3. Update all cross-references to point to the new article
4. Run `check_broken_links.py` to catch dangling references

## Files Affected

| File | Action |
|------|--------|
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` | Delete |
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.ipynb` | Delete |
| New tool-agnostic article | Create |
| Cross-referencing files | Update links |
