# Analytical Summary: Gherkin/BDD/DDD/TDD Conversations

**Date:** 2026-02-17
**Sources:**
1. `code_generation_from_specifications.html` — Gemini conversation on MDD, DSLs, OpenAPI, Gherkin, code generators vs. LLMs
2. `ddd_bdd_and_tdd_explained.html` — Gemini conversation on DDD/BDD/TDD stack, System Analysis, Three Amigos
3. `new_profession_description.md` — AI Code Generation Engineer role definition — verification pipeline, AST/CST core competency, secure execution

---

## 1. Inventory of Ideas & Concepts

### A. Specification-Driven Development (SDD)

| # | Idea | Source | Category |
|---|------|--------|----------|
| A1 | Specifications (OpenAPI, JSON Schema, Gherkin) as single source of truth | Conv 1 | Architecture |
| A2 | Traditional code generators are deterministic template engines (100% reproducible) | Conv 1 | Tooling |
| A3 | LLMs are probabilistic code generators (creative but unreliable) | Conv 1 | AI Engineering |
| A4 | **Hybrid approach**: LLM writes the spec → deterministic generator produces code | Conv 1 | AI Engineering |
| A5 | DSLs (SQL, HTML, OpenAPI) are "constrained human languages" for specific domains | Conv 1 | Foundational |
| A6 | OpenAPI can generate full server stubs, client SDKs, and documentation simultaneously | Conv 1 | Tooling |
| A7 | Gherkin is a testing specification, not a coding specification — it generates test skeletons, not production code | Conv 1 | Key Distinction |

### B. BDD in the AI Era

| # | Idea | Source | Category |
|---|------|--------|----------|
| B1 | Gherkin as "mathematical boundary" constraining AI agents | Conv 1 | AI Engineering |
| B2 | **Agentic BDD**: AI agent reads Gherkin → writes step definitions → runs in sandbox → iterates until green | Conv 1 | AI Engineering |
| B3 | Multi-agent architecture: spec-writer agent + code-generator agent + test-validator agent | Conv 1 | Architecture |
| B4 | AST/CST analysis as architectural guardrails for AI-generated code | Conv 1 | AI Engineering |
| B5 | Emerging tools: Tessl, Spec-kit, Agentic BDD systems | Conv 1 | Tooling |
| B6 | "Red-Green-Refactor" loop applied to AI agents in sandboxes | Conv 1 | Process |
| B7 | Gherkin becomes the human-AI interface for software engineering | Conv 1 | Vision |

### C. The DDD/BDD/TDD Stack

| # | Idea | Source | Category |
|---|------|--------|----------|
| C1 | DDD = strategic design (bounded contexts, ubiquitous language) — "The Map" | Conv 2 | Architecture |
| C2 | BDD = requirements as executable specs (Given/When/Then) — "The Directions" | Conv 2 | Process |
| C3 | TDD = tactical code quality (Red-Green-Refactor) — "The Mechanics" | Conv 2 | Process |
| C4 | System Analysis is distributed across all three, not a separate phase | Conv 2 | Key Insight |
| C5 | In DDD: SA = strategic analysis (event storming, bounded contexts) | Conv 2 | Roles |
| C6 | In BDD: SA = requirement analysis (turning vague requests into scenarios) | Conv 2 | Roles |
| C7 | In TDD: SA = technical analysis (micro-analysis of function I/O) | Conv 2 | Roles |

### D. Business Analysis vs. System Analysis

| # | Idea | Source | Category |
|---|------|--------|----------|
| D1 | BA = "Why & What" (problem space, ROI, business rules) | Conv 2 | Roles |
| D2 | SA = "How & With What" (solution space, data flow, integrations) | Conv 2 | Roles |
| D3 | BA identifies subdomains; SA defines bounded contexts and aggregates | Conv 2 | DDD Application |
| D4 | BA leads discovery; SA defines edge cases and technical constraints | Conv 2 | BDD Application |
| D5 | Modern analysis: continuous, iterative, team-based vs. traditional upfront/siloed | Conv 2 | Paradigm Shift |

### E. Three Amigos Process

| # | Idea | Source | Category |
|---|------|--------|----------|
| E1 | BA + SA + Dev/Tester collaborative discovery session | Conv 2 | Process |
| E2 | Meeting template: Why → Discovery → Gherkin → System Constraints → Definition of Ready | Conv 2 | Template |
| E3 | "Example Mapping" technique (Matt Wynne) using colored index cards | Conv 2 | Technique |
| E4 | Living documentation that never goes stale (tests = docs) | Conv 2 | Principle |

### F. BDD-to-Production Pipeline

| # | Idea | Source | Category |
|---|------|--------|----------|
| F1 | Gherkin → step definitions (skeleton) → fill with business logic → refactor into standalone program | Conv 1 | Workflow |
| F2 | Steps should call the real program (integration testing), not contain embedded logic | Conv 1 | Best Practice |
| F3 | Add scenario → run (fail) → implement → run (pass) = the BDD development loop | Conv 1 | Process |

### G. Verification & Execution Infrastructure

| # | Idea | Source | Category |
|---|------|--------|----------|
| G1 | Multi-layered verification: static analysis + property-based testing + AST validation + sandbox execution | Source 3 | AI Engineering |
| G2 | AST/CST as **core infrastructure** for code generation pipelines, not just a guardrail | Source 3 | Architecture |
| G3 | Secure execution environments (Docker, Firecracker, gVisor) for AI-generated code | Source 3 | Infrastructure |
| G4 | **"Never trust, always verify"** — generated code is untrusted until structurally proven correct | Source 3 | Principle |
| G5 | Software engineering rigor first, LLM awareness second (inverted priority) | Source 3 | Philosophy |
| G6 | LLMs as unreliable components requiring constraint and correction | Source 3 | AI Engineering |

---

## 2. Method/Approach Evaluation Matrix

| Approach | Automation Level | Reliability | Scope | Best For |
|----------|-----------------|-------------|-------|----------|
| **OpenAPI + Generator** | Full (infra code) | 100% deterministic | APIs, data models, client SDKs | Standard plumbing |
| **Gherkin + behave** | Partial (test skeleton) | 100% deterministic | Behavior verification | Custom business logic |
| **LLM code generation** | Full (any code) | Variable (hallucination risk) | Any domain | Prototyping, creative coding |
| **Hybrid: LLM → spec → generator** | Full | High (spec is validated) | API-centric systems | Production with AI speed |
| **Agentic BDD** | Full (agent loop) | Medium-high (sandbox validates) | Complex features | AI-era development |
| **AST/CST + Static Analysis Pipeline** | Partial (validation layer) | High (deterministic) | Any generated code | Post-generation correctness enforcement |

---

## 3. Relevance to AI Engineering Book

### Directly Applicable

- **A4 (Hybrid approach)**: This is the core thesis of the AI Engineering Book's methodology — LLM+SLM hybrid. The "LLM writes spec → generator produces code" pattern directly maps to "LLM handles creative/ambiguous tasks, deterministic tools handle precision."
- **B1 (Gherkin as mathematical boundary)**: Relevant to Chapter 3 (Prompts-as-Infrastructure). Gherkin scenarios can serve as structured prompts constraining AI agent behavior.
- **B3 (Multi-agent architecture)**: Directly relevant to Chapter 4 (Orchestration). The spec-writer/code-generator/test-validator agent trio is a concrete workflow pattern.
- **B4 + G2 (AST/CST as core infrastructure)**: Not just guardrails — AST/CST manipulation is the core infrastructure for validating any AI-generated code in the project. Source 3 elevates this from a quality check to a first-class competency (parsing, safe refactoring, metaprogramming via `libcst`, `tree-sitter`, `ast-grep`).
- **G4 ("Never trust, always verify")**: The philosophical foundation of the book's LLM+SLM methodology. Generated code is untrusted until structurally proven correct through automated verification. This operationalizes the book's stance that LLMs handle creativity while deterministic tools enforce correctness.
- **C4 (Distributed system analysis)**: Matches the book's approach where documentation, tests, and code are one system (Jupytext, pre-commit hooks, ADRs).

### Indirectly Applicable

- **E2 (Three Amigos template)**: Could inform how we structure ADR discovery sessions.
- **F2 (Integration testing pattern)**: Reinforces the book's TDD-first approach — steps should test real programs, not mock logic.
- **A7 (Gherkin is testing, not coding)**: Important clarification to include when discussing specification-driven approaches.
- **G3 (Secure execution environments)**: Relevant when the book covers AI agent workflows in Chapter 4 (Orchestration) — sandboxed execution of AI-generated code via Docker, Firecracker, or gVisor.

### Not Applicable

- **A6 (OpenAPI full generation)**: The book is not building web APIs; it's building a knowledge base.
- **B5 (Tessl, Spec-kit)**: Too nascent/unverified to recommend in production guidance.

---

## 4. Peer Review

### A4: Hybrid Approach (LLM writes spec → generator produces code)

- **Validity**: ✅ Technically sound. This is already practiced (e.g., using ChatGPT to draft OpenAPI specs, then running `openapi-generator`). The key insight — separating creative ambiguity (LLM) from deterministic precision (generator) — is architecturally correct.
- **Novelty**: ⚠️ Medium. The idea isn't new (discussed in AI engineering circles since 2023), but Gemini articulates it clearly as a deliberate architecture pattern rather than an accidental workflow.
- **Applicability**: ✅ High. Directly mirrors the book's LLM+SLM philosophy.
- **ADR-worthiness**: ✅ Yes — formalize as an ADR on "Spec-as-Interface between LLM and deterministic tools."

### B1: Gherkin as "Mathematical Boundary" for AI Agents

- **Validity**: ⚠️ Partially valid. Gherkin provides *structured constraints*, but calling it "mathematical" overstates it. Gherkin scenarios are natural language with syntax sugar — they don't provide formal verification. The boundary is behavioral (pass/fail on execution), not mathematical (provable correctness).
- **Novelty**: ⚠️ Medium. The reframing of BDD as an AI constraint mechanism is interesting but largely a relabeling of existing test-driven validation.
- **Applicability**: ✅ High. Even without formal guarantees, Gherkin-as-acceptance-criteria for AI agents is practical.
- **ADR-worthiness**: ⚠️ Maybe — worth discussing, but needs a more precise formulation. "Executable specification as AI agent acceptance criteria" is more accurate than "mathematical boundary."

### B2: Agentic BDD (Agent reads Gherkin → writes code → sandbox validates)

- **Validity**: ✅ Sound in principle. This is essentially what Claude Code and similar tools already do — read a spec (issue/plan), generate code, run tests, iterate. The Gherkin layer adds structure to the "spec" part.
- **Novelty**: ⚠️ Low-medium. SWE-Bench and similar agent benchmarks already operate this way. The contribution is framing it in BDD terminology, which aids understanding.
- **Applicability**: ✅ High. This is literally what we do: plan → implement → test → iterate.
- **ADR-worthiness**: ✅ Yes — formalize as a workflow pattern: "BDD-Driven AI Agent Development Loop."

### B3: Multi-Agent Architecture (spec-writer + code-gen + test-validator)

- **Validity**: ⚠️ Conceptually sound but oversimplified. In practice, separating these roles into distinct agents creates coordination overhead. Current state-of-the-art (Claude Code, Cursor) uses a single agent that switches roles contextually.
- **Novelty**: ❌ Low. Standard multi-agent pattern. The Gemini conversation doesn't add implementation detail.
- **Applicability**: ⚠️ Low for this project. Our architecture uses single-agent with tool delegation, not multi-agent.
- **ADR-worthiness**: ❌ No — not aligned with current project architecture.

### C4: System Analysis Distributed Across DDD/BDD/TDD

- **Validity**: ✅ Sound. This is the established Agile perspective. The "analysis is the oxygen" metaphor is apt.
- **Novelty**: ❌ Low. Well-established in Agile literature since the 2000s.
- **Applicability**: ✅ High. Reinforces our Documentation-as-Code approach.
- **ADR-worthiness**: ❌ No — already embodied in our practices.

### A7: Gherkin is Testing, Not Coding

- **Validity**: ✅ Correct and important. Many newcomers conflate specification languages with code generation. The conversation does a good job clarifying this.
- **Novelty**: ❌ Low. Well-known distinction.
- **Applicability**: ✅ High for educational content in the book.
- **ADR-worthiness**: ❌ No — educational content, not an architectural decision.

### E2: Three Amigos Meeting Template

- **Validity**: ✅ Sound. The template structure (Why → Discovery → Gherkin → Constraints → Definition of Ready) is practical and actionable.
- **Novelty**: ⚠️ Low-medium. Three Amigos is standard; the specific 5-section template is a useful formalization.
- **Applicability**: ⚠️ Medium. Useful if we adopt BDD formally; currently we use ADR-based decision-making.
- **ADR-worthiness**: ⚠️ Maybe — could adapt as an "ADR Discovery Session Template."

### G2: AST/CST as Core Infrastructure (not just guardrails)

- **Validity**: ✅ Valid, high applicability. AST/CST manipulation is well-established in compiler tooling and static analysis. Reframing it as core infrastructure for AI code generation pipelines is a sound architectural insight.
- **Novelty**: ⚠️ Medium. The tools (`libcst`, `tree-sitter`) are mature; the novelty is positioning them as the verification backbone for LLM outputs.
- **Applicability**: ✅ High. Directly supports the project's pre-commit pipeline and code quality infrastructure.
- **Caveat**: AST manipulation requires specialized expertise (compiler design, program analysis), which may narrow the book's audience. Needs careful pedagogical framing.

### G3: Secure Execution Environments for AI-Generated Code

- **Validity**: ✅ Valid. Running untrusted AI-generated code in sandboxes (Docker, Firecracker, gVisor) is standard practice in agentic systems.
- **Novelty**: ❌ Low. Container isolation is established infrastructure. The contribution is contextualizing it for AI code generation.
- **Applicability**: ⚠️ Medium. May be over-scoped for a book about AI engineering methodology — this leans into platform engineering territory.
- **ADR-worthiness**: ⚠️ Maybe — relevant if the book covers agentic execution in Chapter 4, but not a core methodology decision.

### G4: "Never Trust, Always Verify"

- **Validity**: ✅ Valid and valuable. A clear philosophical stance that operationalizes distrust of LLM outputs.
- **Novelty**: ⚠️ Low as a general principle (zero-trust is decades old), but medium when applied specifically to AI-generated code as untrusted-until-verified.
- **Applicability**: ✅ High. This is the philosophical foundation of the book's LLM+SLM methodology.
- **Caveat**: Risk of being a truism without concrete operationalization. Must define what "verify" means: static analysis? property-based tests? formal proof? All four layers from G1?

### G5: Software Engineering Rigor First, LLM Awareness Second

- **Validity**: ✅ Valid. Directly aligns with the book's stance that AI is a tool within engineering discipline, not a replacement for it.
- **Novelty**: ⚠️ Medium. Contrarian in an industry that often leads with "AI-first" framing.
- **Applicability**: ✅ High. Reinforces the book's methodology.
- **Devil's advocate**: If LLMs improve dramatically (o3-level reasoning, formal verification capabilities), does the "unreliable component" framing age poorly? The book should position this as a *current engineering constraint*, not a permanent truth.

### G6: LLMs as Unreliable Components

- **Validity**: ⚠️ Time-sensitive claim. True today (2026), may not hold in 2-3 years as model capabilities improve.
- **Novelty**: ❌ Low. Well-known limitation, widely discussed since GPT-3.
- **Applicability**: ✅ High for current guidance, but frame as a snapshot — "as of 2026, LLMs are unreliable components" rather than "LLMs are inherently unreliable."
- **ADR-worthiness**: ❌ No — this is a contextual assumption, not an architectural decision. Document it as a foundational assumption that may be revisited.

---

### Devil's Advocate: Cross-Cutting Concerns

**On Source 3 provenance**: The profession document was generated by Qwen3-Max based on a discussion about a real vacancy at a major European bank. The role, competency requirements, and tool lists are grounded in actual industry demand. The Qwen3-Max layer structured this into the academic-letter format but did not invent the requirements.

**On tool lists across sources**: Source 3 tools (`libcst`, `tree-sitter`, `ast-grep`, `Semgrep`, `hypothesis`, Docker, Firecracker, gVisor) are all verifiable, real tools drawn from the original vacancy. In contrast, Tessl and Spec-kit (from Sources 1-2) may be Gemini hallucinations — verification is needed before citing them in published content.

**On scope creep**: Merging a profession definition into a BDD/DDD analysis risks diluting the original focus. The integration here is surgical (Section G, specific peer reviews) rather than wholesale — this is intentional.

**On temporal validity**: Sources 1-3 all assume LLMs are fundamentally unreliable. This is correct today but may not hold as models gain formal reasoning capabilities. This analysis is a **snapshot as of early 2026**, not a permanent truth. Revisit when model capabilities change materially.

---

### Overall Assessment of Gemini's Responses

**Strengths:**
- Clear pedagogical progression from fundamentals to advanced concepts
- Good at making distinctions (generator vs. LLM, testing spec vs. coding spec, BA vs. SA)
- The Hybrid approach articulation (A4) is the most valuable insight
- Practical examples (behave setup, step definitions) are correct and runnable

**Weaknesses:**
- Overstates novelty of well-established concepts (DDD/BDD/TDD stack is 15+ years old)
- "Mathematical boundary" claim (B1) is imprecise
- Multi-agent architecture (B3) is hand-wavy — no implementation detail
- Tool recommendations (Tessl, Spec-kit) are unverifiable — may not exist or may be Gemini hallucinations
- Reading list is standard (no surprises) but correctly curated for the target audience
- Some responses are verbose and repetitive ("Would you like me to..." patterns)

---

## 5. ADR Candidates (proposed)

### ADR Candidate 1: Spec-as-Interface Pattern for AI-Assisted Development

**Proposal:** Formalize the pattern where LLMs generate structured specifications (OpenAPI, JSON Schema, Gherkin) that are then processed by deterministic tools (generators, validators, test runners).

**Rationale:** This separates the creative/ambiguous (LLM) from the precise/deterministic (tooling), mirroring the book's LLM+SLM philosophy.

**Scope:** ADR defining when to use this pattern in the project's development workflow.

**Priority:** High

### ADR Candidate 2: BDD-Driven AI Agent Development Loop

**Proposal:** Formalize the workflow: Write Gherkin acceptance criteria → AI agent implements → automated tests validate → iterate. This is what we already practice informally (plan → implement → test), but formalizing it with Gherkin syntax adds structure.

**Rationale:** Provides a reproducible, verifiable workflow for AI-assisted development. Gherkin scenarios become the "Definition of Done" for AI agent tasks.

**Scope:** ADR or workflow document.

**Priority:** Medium — useful but not blocking. Our current plan/ADR-based approach works. Consider when scaling to more contributors.

### ADR Candidate 3: ADR Discovery Session Template (adapted Three Amigos)

**Proposal:** Adapt the Three Amigos meeting template for ADR discovery: Context → Options Discovery → Decision Criteria → Constraints → Definition of Ready.

**Rationale:** Our ADR process would benefit from a structured discovery format, especially for complex architectural decisions.

**Scope:** Addition to the ADR workflow guidelines.

**Priority:** Low — nice to have, not urgent.

### ADR Candidate 4: Verification Pipeline for AI-Generated Code

**Proposal:** Define a multi-layered verification standard: (1) AST/CST structural validation, (2) static analysis (type checking, linting), (3) property-based testing, (4) sandbox execution. All AI-generated code must pass all layers before integration.

**Rationale:** Operationalizes "never trust, always verify" (G4) with concrete, automatable steps. Grounded in real industry requirements (Source 3).

**Scope:** ADR defining the verification layers and their ordering for the project's pre-commit and CI pipeline.

**Priority:** High — directly supports the book's methodology and the project's existing pre-commit pipeline.

---

## Appendix: Reading List (curated from conversations)

### Essential (SA/Engineering audience)
1. **"Specification by Example"** — Gojko Adzic (BDD/requirements)
2. **"Domain-Driven Design Distilled"** — Vaughn Vernon (DDD quick start)
3. **"Test-Driven Development by Example"** — Kent Beck (TDD classic)

### Deep Dives
4. **"Implementing Domain-Driven Design"** — Vaughn Vernon (DDD tactical patterns)
5. **"BDD in Action" (2nd Ed)** — John Ferguson Smart (full BDD lifecycle)
6. **"The Cucumber Book"** — Matt Wynne & Aslak Hellesøy (Gherkin mastery)
7. **"Domain Storytelling"** — Stefan Hofer & Henning Schwentner (visual modeling)
8. **"Clean Architecture"** — Robert C. Martin (testable system design)
9. **"Crafting Interpreters"** — Robert Nystrom (AST/parsing foundations, relevant to understanding code manipulation)

### Techniques
- **Example Mapping** (Matt Wynne) — rapid Gherkin discovery with index cards
- **Event Storming** (Alberto Brandolini) — DDD domain modeling with sticky notes
