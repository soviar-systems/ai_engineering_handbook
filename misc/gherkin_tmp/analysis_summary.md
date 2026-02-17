# Analytical Summary: Gherkin/BDD/DDD/TDD Conversations

**Date:** 2026-02-17
**Sources:**
1. `code_generation_from_specifications.html` — Gemini conversation on MDD, DSLs, OpenAPI, Gherkin, code generators vs. LLMs
2. `ddd_bdd_and_tdd_explained.html` — Gemini conversation on DDD/BDD/TDD stack, System Analysis, Three Amigos

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

---

## 2. Method/Approach Evaluation Matrix

| Approach | Automation Level | Reliability | Scope | Best For |
|----------|-----------------|-------------|-------|----------|
| **OpenAPI + Generator** | Full (infra code) | 100% deterministic | APIs, data models, client SDKs | Standard plumbing |
| **Gherkin + behave** | Partial (test skeleton) | 100% deterministic | Behavior verification | Custom business logic |
| **LLM code generation** | Full (any code) | Variable (hallucination risk) | Any domain | Prototyping, creative coding |
| **Hybrid: LLM → spec → generator** | Full | High (spec is validated) | API-centric systems | Production with AI speed |
| **Agentic BDD** | Full (agent loop) | Medium-high (sandbox validates) | Complex features | AI-era development |
| **AST/CST guardrails** | N/A (validation layer) | High | Architecture compliance | Post-generation validation |

---

## 3. Relevance to AI Engineering Book

### Directly Applicable

- **A4 (Hybrid approach)**: This is the core thesis of the AI Engineering Book's methodology — LLM+SLM hybrid. The "LLM writes spec → generator produces code" pattern directly maps to "LLM handles creative/ambiguous tasks, deterministic tools handle precision."
- **B1 (Gherkin as mathematical boundary)**: Relevant to Chapter 3 (Prompts-as-Infrastructure). Gherkin scenarios can serve as structured prompts constraining AI agent behavior.
- **B3 (Multi-agent architecture)**: Directly relevant to Chapter 4 (Orchestration). The spec-writer/code-generator/test-validator agent trio is a concrete workflow pattern.
- **B4 (AST/CST guardrails)**: Relevant to quality assurance of AI-generated code in the book's CI/CD pipeline.
- **C4 (Distributed system analysis)**: Matches the book's approach where documentation, tests, and code are one system (Jupytext, pre-commit hooks, ADRs).

### Indirectly Applicable

- **E2 (Three Amigos template)**: Could inform how we structure ADR discovery sessions.
- **F2 (Integration testing pattern)**: Reinforces the book's TDD-first approach — steps should test real programs, not mock logic.
- **A7 (Gherkin is testing, not coding)**: Important clarification to include when discussing specification-driven approaches.

### Not Applicable

- **A6 (OpenAPI full generation)**: The book is not building web APIs; it's building a knowledge base.
- **B5 (Tessl, Spec-kit)**: Too nascent/unverified to recommend in production guidance.

---

## 4. Peer Review

### A4: Hybrid Approach (LLM writes spec → generator produces code)

- **Validity**: ✅ Technically sound. This is already practiced (e.g., using ChatGPT to draft OpenAPI specs, then running `openapi-generator`). The key insight — separating creative ambiguity (LLM) from deterministic precision (generator) — is architecturally correct.
- **Novelty**: ⚠️ Medium. The idea isn't new (discussed in AI engineering circles since 2023), but Gemini articulates it clearly as a deliberate architecture pattern rather than an accidental workflow.
- **Applicability**: ✅ High. Directly mirrors the book's LLM+SLM philosophy.
- **RFC-worthiness**: ✅ Yes — formalize as an ADR on "Spec-as-Interface between LLM and deterministic tools."

### B1: Gherkin as "Mathematical Boundary" for AI Agents

- **Validity**: ⚠️ Partially valid. Gherkin provides *structured constraints*, but calling it "mathematical" overstates it. Gherkin scenarios are natural language with syntax sugar — they don't provide formal verification. The boundary is behavioral (pass/fail on execution), not mathematical (provable correctness).
- **Novelty**: ⚠️ Medium. The reframing of BDD as an AI constraint mechanism is interesting but largely a relabeling of existing test-driven validation.
- **Applicability**: ✅ High. Even without formal guarantees, Gherkin-as-acceptance-criteria for AI agents is practical.
- **RFC-worthiness**: ⚠️ Maybe — worth discussing, but needs a more precise formulation. "Executable specification as AI agent acceptance criteria" is more accurate than "mathematical boundary."

### B2: Agentic BDD (Agent reads Gherkin → writes code → sandbox validates)

- **Validity**: ✅ Sound in principle. This is essentially what Claude Code and similar tools already do — read a spec (issue/plan), generate code, run tests, iterate. The Gherkin layer adds structure to the "spec" part.
- **Novelty**: ⚠️ Low-medium. SWE-Bench and similar agent benchmarks already operate this way. The contribution is framing it in BDD terminology, which aids understanding.
- **Applicability**: ✅ High. This is literally what we do: plan → implement → test → iterate.
- **RFC-worthiness**: ✅ Yes — formalize as a workflow pattern: "BDD-Driven AI Agent Development Loop."

### B3: Multi-Agent Architecture (spec-writer + code-gen + test-validator)

- **Validity**: ⚠️ Conceptually sound but oversimplified. In practice, separating these roles into distinct agents creates coordination overhead. Current state-of-the-art (Claude Code, Cursor) uses a single agent that switches roles contextually.
- **Novelty**: ❌ Low. Standard multi-agent pattern. The Gemini conversation doesn't add implementation detail.
- **Applicability**: ⚠️ Low for this project. Our architecture uses single-agent with tool delegation, not multi-agent.
- **RFC-worthiness**: ❌ No — not aligned with current project architecture.

### C4: System Analysis Distributed Across DDD/BDD/TDD

- **Validity**: ✅ Sound. This is the established Agile perspective. The "analysis is the oxygen" metaphor is apt.
- **Novelty**: ❌ Low. Well-established in Agile literature since the 2000s.
- **Applicability**: ✅ High. Reinforces our Documentation-as-Code approach.
- **RFC-worthiness**: ❌ No — already embodied in our practices.

### A7: Gherkin is Testing, Not Coding

- **Validity**: ✅ Correct and important. Many newcomers conflate specification languages with code generation. The conversation does a good job clarifying this.
- **Novelty**: ❌ Low. Well-known distinction.
- **Applicability**: ✅ High for educational content in the book.
- **RFC-worthiness**: ❌ No — educational content, not an architectural decision.

### E2: Three Amigos Meeting Template

- **Validity**: ✅ Sound. The template structure (Why → Discovery → Gherkin → Constraints → Definition of Ready) is practical and actionable.
- **Novelty**: ⚠️ Low-medium. Three Amigos is standard; the specific 5-section template is a useful formalization.
- **Applicability**: ⚠️ Medium. Useful if we adopt BDD formally; currently we use ADR-based decision-making.
- **RFC-worthiness**: ⚠️ Maybe — could adapt as an "ADR Discovery Session Template."

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

## 5. RFC Candidates

### RFC-1: Spec-as-Interface Pattern for AI-Assisted Development

**Proposal:** Formalize the pattern where LLMs generate structured specifications (OpenAPI, JSON Schema, Gherkin) that are then processed by deterministic tools (generators, validators, test runners).

**Rationale:** This separates the creative/ambiguous (LLM) from the precise/deterministic (tooling), mirroring the book's LLM+SLM philosophy.

**Scope:** ADR defining when to use this pattern in the project's development workflow.

**Priority:** High

### RFC-2: BDD-Driven AI Agent Development Loop

**Proposal:** Formalize the workflow: Write Gherkin acceptance criteria → AI agent implements → automated tests validate → iterate. This is what we already practice informally (plan → implement → test), but formalizing it with Gherkin syntax adds structure.

**Rationale:** Provides a reproducible, verifiable workflow for AI-assisted development. Gherkin scenarios become the "Definition of Done" for AI agent tasks.

**Scope:** ADR or workflow document.

**Priority:** Medium — useful but not blocking. Our current plan/ADR-based approach works. Consider when scaling to more contributors.

### RFC-3: ADR Discovery Session Template (adapted Three Amigos)

**Proposal:** Adapt the Three Amigos meeting template for ADR discovery: Context → Options Discovery → Decision Criteria → Constraints → Definition of Ready.

**Rationale:** Our ADR process would benefit from a structured discovery format, especially for complex architectural decisions.

**Scope:** Addition to the ADR workflow guidelines.

**Priority:** Low — nice to have, not urgent.

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

### Techniques
- **Example Mapping** (Matt Wynne) — rapid Gherkin discovery with index cards
- **Event Storming** (Alberto Brandolini) — DDD domain modeling with sticky notes
