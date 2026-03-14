# Plan: Analysis of Gherkin/BDD/DDD/TDD Conversations + New Extraction Tool

## Context

Two Gemini conversations were saved as HTML in `misc/gherkin_tmp/`. The goal is to:
1. Produce a detailed analytical summary of ideas, concepts, methods, and approaches
2. Add peer review assessing which ideas are genuinely valuable for AI-era development
3. Create a better HTML extraction script (the current one struggles with JS-rendered SPAs)

The summary will be used for discussion and potential RFC (Request for Comments) development.

---

## Part 1: Analytical Summary (output file: `misc/gherkin_tmp/analysis_summary.md`)

### Source Conversations

1. **`code_generation_from_specifications.html`** — Deep exploration of MDD, DSLs, OpenAPI, Gherkin/BDD, code generators vs. LLMs, and the future of Spec-Driven Development in AI-agent environments
2. **`ddd_bdd_and_tdd_explained.html`** — High-level comparison of DDD, BDD, TDD; role of System Analysis and Business Analysis; Three Amigos workflow; reading list

### Summary Structure

The analysis document will contain:

1. **Inventory of Ideas & Concepts** — every distinct idea extracted, categorized
2. **Method/Approach Evaluation Matrix** — structured comparison
3. **Relevance to AI Engineering** — which ideas matter for this project specifically
4. **Peer Review** — critical assessment of claims, identifying what's genuinely valuable vs. hype
5. **RFC Candidates** — concrete proposals worth formalizing

### Key Themes to Cover

#### A. Specification-Driven Development (SDD)
- Specs (Gherkin, OpenAPI, JSON Schema) as the "source of truth"
- Traditional code generators (deterministic, template-based) vs. LLM generation (probabilistic)
- The Hybrid approach: LLM writes spec → generator produces code
- Claim: "Gherkin becomes the human-AI interface for software engineering"

#### B. BDD in the AI Era
- Gherkin as "mathematical boundary" constraining AI agents
- Agentic BDD: AI agent reads Gherkin → writes step definitions → runs in sandbox → iterates
- Multi-agent architecture: spec-writer agent, code-generator agent, test-validator agent
- AST/CST analysis as architectural guardrails for AI-generated code

#### C. The DDD/BDD/TDD Stack
- DDD = strategic design (bounded contexts, ubiquitous language)
- BDD = requirements as executable specs (Given/When/Then)
- TDD = tactical code quality (Red-Green-Refactor)
- System Analysis distributed across all three (not a separate phase)

#### D. The Three Amigos Process
- BA + SA + Dev/Tester collaborative discovery
- Structured meeting template: Why → Discovery → Gherkin → System Constraints → Definition of Ready
- Living documentation that never goes stale

#### E. Practical Toolchain
- behave (Python BDD), Cucumber, bats (Bash)
- openapi-generator, FastAPI, pydantic
- Emerging: Tessl, Spec-kit, Agentic BDD systems

### Peer Review Sections

For each major idea, provide:
- **Validity**: Is the claim technically sound?
- **Novelty**: Is this genuinely new or repackaged?
- **Applicability**: Does it apply to THIS project (AI Engineering Book, hybrid LLM+SLM)?
- **RFC-worthiness**: Should we formalize this into an ADR/RFC?

---

## Part 2: New Extraction Script (`tools/scripts/extract_gemini_html.py`)

### Problem
- `extract_html_text.py` works for standard HTML and `.mhtml` files
- Fails on JS-rendered SPAs (Gemini pages saved without "complete webpage" option)
- Need a more robust tool that can also handle quoted-printable encoding in `.mhtml`

### Approach
- Create `extract_gemini_html.py` that:
  1. Detects if input is `.mhtml` (multipart) and extracts the HTML part
  2. Decodes quoted-printable encoding
  3. Falls back to `extract_html_text.py` behavior for plain HTML
  4. Strips SVG paths, base64 images, and other noise
  5. Outputs clean, readable conversation text

### Implementation
- Follow the mandatory script suite convention (ADR-26011)
- Use `pathlib.Path`, top-down design
- TDD: write tests first in `tools/tests/test_extract_gemini_html.py`
- Reuse `extract_html_text.py::extract_text()` as the core HTML parser
- Add `quopri` (stdlib) for quoted-printable decoding
- Add `email` (stdlib) for MIME multipart parsing

### Files to Create/Modify
- **Create**: `tools/scripts/extract_gemini_html.py`
- **Create**: `tools/tests/test_extract_gemini_html.py`
- **No changes** to existing `extract_html_text.py`

---

## Verification

1. Run new script against both HTML files, confirm clean output
2. Run `uv run pytest tools/tests/test_extract_gemini_html.py`
3. Review analysis summary for completeness and accuracy
