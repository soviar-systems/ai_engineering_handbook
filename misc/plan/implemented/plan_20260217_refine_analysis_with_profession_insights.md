# Plan: Refine analysis_summary.md with AI Code Generation Engineer Insights

## Context

The `misc/gherkin_tmp/analysis_summary.md` analyzes two Gemini conversations on BDD/DDD/TDD and specification-driven development. A separate document (`new_profession_description.md`) describes the "AI Code Generation Engineer" role — a profession built around verified AI code generation pipelines. The profession document adds three missing dimensions to the analysis: multi-layered verification, secure execution, and an explicit "never trust, always verify" philosophy. This plan integrates those insights surgically.

## File Location Decision

The refined analysis stays in `misc/gherkin_tmp/analysis_summary.md` for now. This content is about AI-era development workflow — bigger than an ADR, not a layer of the AI system. When 2-3 more files of this type accumulate, consider creating a dedicated section (e.g., `ai_system/6_workflow/` or a `methodology/` directory).

## Terminology

- Use **ADR candidates (proposed)** instead of "RFC" — per project conventions, all architectural proposals use the ADR format with `proposed` status tag.

## Changes to `misc/gherkin_tmp/analysis_summary.md`

### 1. Add Source 3 to header
- Add `new_profession_description.md` as Source 3 in the Sources list
- Label: "AI Code Generation Engineer role definition — verification pipeline, AST/CST core competency, secure execution"

### 2. Add Section "G. Verification & Execution Infrastructure" to Idea Inventory (§1)
New table with ideas from Source 3:
- G1: Multi-layered verification (static analysis + property-based testing + AST validation + sandbox)
- G2: AST/CST as core infrastructure, not just a guardrail
- G3: Secure execution environments (Docker, Firecracker, gVisor) for AI-generated code
- G4: "Never trust, always verify" — generated code is untrusted until structurally proven correct
- G5: Software engineering rigor first, LLM awareness second (inverted priority)
- G6: LLMs as unreliable components requiring constraint and correction

### 3. Update Evaluation Matrix (§2)
Add one row:
- **AST/CST + Static Analysis Pipeline**: Automation=Partial (validation layer), Reliability=High (deterministic), Scope=Any generated code, Best For=Post-generation correctness enforcement

### 4. Update Relevance to AI Engineering Book (§3)
- Move B4 (AST/CST guardrails) from brief mention to **Directly Applicable** with expanded rationale: not just guardrails but core infrastructure for validating any AI-generated code in the project
- Add G4 ("Never trust, always verify") as a directly applicable principle — it's the philosophical foundation of the book's LLM+SLM methodology
- Add G3 (Secure execution) as **Indirectly Applicable** — relevant when the book covers AI agent workflows in Chapter 4

### 5. Add Peer Review entries for new ideas (§4)
Review G1-G6 with same rigor as existing reviews:
- G2 (AST/CST as core): ✅ Valid, high applicability — but note that AST manipulation requires specialized expertise, which may narrow the audience
- G3 (Secure execution): ✅ Valid — but may be over-scoped for a book about AI engineering methodology vs. a platform engineering book
- G4 ("Never trust, always verify"): ✅ Valid and valuable — but risk of being a truism. Needs concrete operationalization (what does "verify" mean? static analysis? tests? formal proof?)
- G5 (SE rigor first): ✅ Valid — directly aligns with the book's stance. But devil's advocate: if LLMs improve dramatically (o3-level reasoning), does the "unreliable component" framing age poorly?
- G6 (LLMs as unreliable): ⚠️ Time-sensitive claim. True today, may not be in 2-3 years. Frame as a *current engineering constraint*, not a permanent truth

### 6. Add Devil's Advocate section (new §4.5 or expand §4)
- **On the profession document itself**: It's a Gemini output, not a validated industry standard. The "AI Code Generation Engineer" title doesn't appear in major job boards (as of 2026). Risk of circular reasoning: AI describes an AI-adjacent profession.
- **On tool lists**: Tessl, Spec-kit (from analysis), and some tools in the profession doc may be hallucinated. Verification needed before citing.
- **On scope creep**: Merging profession definition into a BDD/DDD analysis risks diluting the original focus. Integration should be surgical, not wholesale.
- **On temporal validity**: Both documents assume LLMs are fundamentally unreliable. This is correct today but may not hold. The analysis should acknowledge this as a snapshot, not a permanent truth.

### 7. Rename "RFC Candidates" → "ADR Candidates (proposed)" in §5 and update numbering
Add ADR Candidate 4:
- **ADR Candidate 4: Verification Pipeline for AI-Generated Code**
- **Proposal**: Define a multi-layered verification standard: (1) AST/CST structural validation, (2) static analysis (type checking, linting), (3) property-based testing, (4) sandbox execution. All AI-generated code must pass all layers before integration.
- **Rationale**: Operationalizes "never trust, always verify" with concrete, automatable steps.
- **Priority**: High — directly supports the book's methodology and project's pre-commit pipeline.

### 8. Update Reading List (Appendix)
Add under "Deep Dives":
- **"Crafting Interpreters"** — Robert Nystrom (AST/parsing foundations, relevant to understanding code manipulation)

## Files Modified
- `misc/gherkin_tmp/analysis_summary.md` — all changes above

## Verification
- Re-read the final document for internal consistency
- Verify no existing sections are contradicted by new additions
- Ensure all new claims are properly attributed to Source 3
- Check that the devil's advocate section challenges both the original analysis AND the new additions fairly
