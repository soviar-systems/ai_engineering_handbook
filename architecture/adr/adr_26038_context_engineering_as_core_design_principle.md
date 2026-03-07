---
id: 26038
title: "Context Engineering as Core Design Principle"
date: 2026-03-08
status: proposed
superseded_by: null
tags: [architecture, context_management, governance]
---

<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26038: Context Engineering as Core Design Principle

## Date
2026-03-08

## Status

proposed

## Context

The Agentic OS concept ({term}`ADR-26034`, [A-26002: Agentic OS, Tiered Cognitive Memory, and Package-Driven Infrastructure](/architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md)) positions documentation as a filesystem and skills as composable applications. However, a comprehensive landscape analysis ([S-26007: Compass — The Realistic State of Agentic AI Architectures in Early 2026](/architecture/evidence/sources/S-26007_compass_realistic_state_of_agentic_ai_2026.md), Claude Opus 4.6 research work) reveals a consistent pattern across production deployments: **context engineering, not architectural sophistication, determines agent success**.

Key evidence from S-26007:

1. **Vercel's text-to-SQL agent**: Stripping from 15+ tools to 2 improved success rate from 80% to 100%, reduced tokens by 40%. Their conclusion: "We were doing the model's thinking for it."

2. **UC Berkeley MAST taxonomy** (NeurIPS 2025): Analysis of 1,600+ traces across 7 frameworks found multi-agent system correctness as low as 25%. Best-effort interventions yielded only +14% improvement.

3. **Cognition (Devin, $73M ARR)**: Published "Don't Build Multi-Agents" — multi-agent systems are inherently fragile due to context isolation between sub-agents.

4. **Galileo AI estimate**: "In 80% of cases, a well-crafted single agent with thoughtful context management outperforms a multi-agent system."

5. **Claude Code ($1B run-rate)**: Fundamentally a single-agent tool-use loop — LLM + tools in a loop, not elaborate orchestration.

6. **NVIDIA RULER benchmark**: Effective context is only 50-65% of advertised window size. Llama 3.1-70B accuracy drops from 96.5% at 4K tokens to 66.6% at 128K.

7. **MIT/Kellogg finding**: 80% of work in production agent projects is data engineering, governance, and workflow integration — not the AI itself.

The ecosystem's Agentic OS design has been evolving toward increasing architectural complexity (VFS layers, Virtual Relational Layers, document type registries). This ADR establishes the constraint that prevents over-engineering: **context engineering is the core primitive, and every architectural addition must justify its existence by improving context management**.

### The Catalyst: Mentor Generator

These patterns emerged from building [Mentor Generator](https://github.com/soviar-systems/mentor_generator), the first application on this OS. Mentor Generator is an AI-powered system that creates personalized learning courses: it interviews a user about their goals and background, researches contemporary sources on the chosen topic, assembles a structured curriculum with a teaching persona (tone, Socratic questioning style, strictness level), and then conducts interactive learning sessions. The project uses litellm for provider-agnostic LLM connectivity (any API, any model).

During the v0.31.0-v0.41.0 evolution (documented in [A-26002](/architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md)), three systemic failures became undeniable: Cognitive Overload (monolithic prompt causing Instruction Drift), Context Tax (reference data competing with procedural logic for the finite context window), and Distribution Friction (no versioned, testable unit of expertise). These are not Mentor-specific — they apply to any agent that must combine domain expertise with structured output generation.

The production mentor requires:
- A single agent dispatching skills (interview, research, generation, mentoring)
- Shared RAG backed by a vector store for semantic memory (vector store standardization is a separate architectural decision)
- Proactive context window management with token counting
- Session persistence via course_history (episodic memory)

This is a context engineering problem, not an orchestration problem.

## Decision

We adopt **context engineering as the core design principle** for the Agentic OS ecosystem. This means:

1. **Single-agent architecture with skill dispatch.** The agent is one process that loads skills on demand (progressive disclosure). Skills are injected instructions, not separate agents. This follows the SKILL.md pattern validated by Anthropic and OpenAI cross-vendor convergence (S-26007).

2. **Three-tier memory as the primary abstraction.**
   - **Working memory**: Current context window, managed by token-aware budget tracking (litellm.token_counter per provider)
   - **Episodic memory**: Session history (course_history), persisted to disk, paged in on demand
   - **Semantic memory**: Long-term knowledge in a vector store (books, articles, research), retrieved via hybrid search (vector + keyword)

3. **Context budget as a first-class constraint.** Every document, skill, and tool output has a token cost. The signal-to-noise ratio of prompt delivery format is itself an architectural decision — see [Format as Architecture: Signal-to-Noise in Prompt Delivery](/ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) for the detailed analysis and empirical measurements. The agent tracks cumulative context usage and acts proactively:
   - (a) Context almost full: summarize and continue (page fault → swap)
   - (b) User stops: graceful save of session state (SIGTERM → checkpoint)
   - (c) Goals complete: fill session log template (exit(0) → write result)

4. **Architectural additions require context engineering justification.** Any new layer, abstraction, or component must demonstrate that it improves the agent's ability to manage, retrieve, or budget context. If a feature does not make context management better, it is rejected as over-engineering. This operationalizes {term}`ADR-26037` (Smallest Viable Architecture) for the agent runtime.

5. **Tool minimalism.** Fewer, well-chosen tools outperform many specialized tools (Vercel evidence). The agent starts with a minimal tool set (RAG retrieval, web search, file I/O) and tools are added only when a concrete use case proves the existing set insufficient.

## Consequences

### Positive

- Prevents the "Agentic OS as grand architecture" trap identified in S-26007 — the system grows from a working runtime, not top-down design
- Aligns with every production success story in the compass analysis (Claude Code, Cursor, Vercel, Devin)
- Token budget awareness prevents the cost explosion documented in S-26007 (agentic apps re-send context 10-50x per session)
- Skills as injected instructions (not sub-agents) eliminate the context isolation problem that kills multi-agent systems
- Three-tier memory maps directly to Mentor Generator's existing architecture (context window / course_history / books in RAG)
- Format-aware context delivery maximizes instructional signal per attention-weighted token. [Format as Architecture](/ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) demonstrates up to 21% token cost difference between formats on identical content (2,306 vs 2,798 tokens), and Mentor Generator post-mortems (v0.40.0 → v0.41.0) confirmed that switching from JSON to YAML improved compiler fidelity from catastrophic drift to ~95% adherence on the same model (Qwen3-Max)

### Negative / Risks

- Single-agent architecture may hit scaling limits for truly independent parallel tasks. **Mitigation:** The constraint says "start single-agent" — it does not prohibit adding concurrency when proven necessary, but the burden of proof is on the proposer
- Token counting accuracy varies across providers (not all expose exact counts). **Mitigation:** litellm.token_counter provides best-effort estimates; design for approximate budgets with safety margins
- Progressive disclosure requires good metadata (descriptions, tags, token_size) on all documents and skills. **Mitigation:** A common frontmatter standard (currently tracked as TD-001 in [Technical Debt Register](/misc/plan/techdebt.md)) will establish these fields; vadocs validates compliance

## Alternatives

- **Multi-agent orchestration (CrewAI, AutoGen pattern).** Multiple specialized agents with delegation. **Rejection Reason:** Empirically fragile — Berkeley MAST taxonomy shows 25% correctness floor, context isolation between agents causes incompatible decisions (Cognition). CrewAI consumes 3x tokens for simple tasks (AIMultiple benchmark).

- **Framework-heavy approach (LangGraph state machines).** Model the agent as a graph with typed state passing and checkpointing. **Rejection Reason:** 45% of LangChain users never deployed to production, 23% who deployed eventually removed it (Adaline analysis). Adds abstraction layers that obscure prompts and responses (Anthropic's "Building Effective Agents" warning).

- **Architecture-first OS design.** Build the full VFS, VRL, Document Type Registry, then write applications on top. **Rejection Reason:** S-26007 concludes the winner will "emerge from a working runtime that accretes capabilities because developers keep needing one more thing." The [GEMM Engineering Standard](/ai_system/1_execution/algebra_gemm_engineering_standard.ipynb) documents how the BLAS interface survived 50+ years of implementation changes — not because it was designed top-down, but because it was extracted from working LINPACK code (a production linear algebra library written at Argonne National Laboratory in the 1970s). The interface became the standard precisely because it codified patterns that were already proven in practice. The same principle applies here: extract the OS primitives from the working Mentor Generator runtime, don't design them in isolation.

## References

- [S-26007: Compass — The Realistic State of Agentic AI Architectures in Early 2026](/architecture/evidence/sources/S-26007_compass_realistic_state_of_agentic_ai_2026.md) — primary evidence base (Claude Opus 4.6 research)
- [A-26005: Agentic OS Filesystem Architecture](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) — VFS boundary and document type system (used as compass for extraction, not as implementation target)
- [A-26002: Agentic OS, Tiered Cognitive Memory, and Package-Driven Infrastructure](/architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md) — tiered memory model, Mentor Generator catalyst
- [Format as Architecture: Signal-to-Noise in Prompt Delivery](/ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb) — token-level analysis of format impact on LLM behavior, Mentor Generator post-mortem evidence
- [GEMM: The Engineering Standard](/ai_system/1_execution/algebra_gemm_engineering_standard.ipynb) — BLAS Interface/API/ABI hierarchy, "the interface is the asset" principle, LINPACK extraction precedent
- {term}`ADR-26034` — Agentic OS Paradigm: Skills as Composable Applications (refined by this ADR: single-agent emphasis)
- {term}`ADR-26037` — Smallest Viable Architecture Constraint Framework (operationalized by this ADR for the agent runtime)
- [Ecosystem Roadmap](/misc/plan/plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md) — implementation plan

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
