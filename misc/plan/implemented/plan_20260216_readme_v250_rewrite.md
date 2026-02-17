# Plan: Rewrite README.md to v2.5.0 — Documentation as Source Code for AI

## Context

The README.md (v2.4.0, last updated 2026-02-06) no longer reflects the repo's architectural identity or its foundational purpose. 16 active ADRs now define a mature Documentation-as-Code methodology, a hub-and-spoke ecosystem, and tool-agnostic principles — none of which the current README communicates. The README still references Aider, specific model names, a deleted `research/` directory, and a non-existent `tools/prompt_helpers/` path.

**The "Why"**: In the new era of AI-backed development, documentation IS the source code that AI systems consume. RAG pipelines, coding agents, and AI assistants don't read your codebase — they read your docs. Stale documentation produces buggy AI outputs. Unstructured metadata makes filtering impossible. This repo exists to build a **new-era documentation system** where docs are treated with the same rigor as production code: versioned, tested, validated, lifecycle-managed, and machine-readable — because they are the primary input for AI systems.

**Central thesis**: This repo is a **Documentation-as-Code hub** — documentation is source code for AI, ADRs are the development backbone, content has a lifecycle, and validation is automated.

## User Decisions

- Bump to **v2.5.0**
- **Full structural rewrite** (not surgical edits)
- **Documentation-as-Code** is the central framing
- **Hub-and-spoke** as the ecosystem model
- **Fully tool-agnostic** (no Aider, no specific model names)
- **ADRs emphasized** as the main context for development
- **"What's New"** section stays at top but content **untouched** (updated separately)
- **"Research & Foundations"** section removed entirely
- Contact email → `rudakow.wadim@gmail.com`
- Only **active ADRs** used as references (not evolutionary/historical)

## File Modified

- `README.md`

## New Section Structure

### 1. Header

```
Version: 2.5.0
Birth: 2025-10-19
Last Modified: 2026-02-16
```

### 2. Mission (rewrite — must answer "why does this exist?")

Open with the **foundational why**: In the AI-backed development era, AI systems (RAG, agents, coding assistants) consume documentation as their primary input. Poor documentation = poor AI outputs. This repo pioneers a **new-era documentation system** where docs are treated as production source code.

Key ideas for the paragraph:
- Documentation IS source code for AI — not a byproduct of development
- The rigor (versioning, testing, lifecycle, metadata) exists because AI systems depend on it
- Hybrid LLM methodology orchestrates the content generation pipeline
- ADRs govern all architectural decisions — machine-readable for AI filtering

Quote block: mission statement focusing on building **reliable, machine-readable documentation infrastructure** that AI systems can trust as authoritative input.

### 3. What's New (UNTOUCHED)

Keep existing v2.4.0, v2.3.0, v2.2.0 content exactly as-is. Position stays near top for visibility.

### 4. Live Documentation Site (NEW)

Brief callout with link to GitHub Pages site (ADR-26022). Frame as "rendered knowledge base" vs GitHub as "source of truth."

### 5. Documentation as Source Code for AI (NEW section — the philosophical core)

This is the section that answers **why** the repo exists and why it's built with such rigor. Frame it around the paradigm shift:

**The paradigm shift**: Traditional documentation is written for humans to read after the fact. In AI-backed development, documentation is the **primary input** that AI systems (RAG pipelines, coding agents, AI assistants) consume to produce outputs. This makes documentation quality a **first-class engineering concern** — stale docs = buggy AI, unstructured metadata = blind retrieval, missing lifecycle = noise accumulation.

**How this repo implements the paradigm** (grounded in active ADRs):
- **Docs = source code**: versioned, diffed, tested via Jupytext pairing (ADR-26014)
- **Metadata = API contract**: MyST-native frontmatter makes every document machine-queryable (ADR-26023, ADR-26016)
- **Lifecycle = garbage collection**: superseded content is deleted to prevent RAG noise; ADRs are never deleted as negative knowledge (ADR-26021)
- **ADRs = development backbone**: every major decision is an ADR; proposed ADRs serve as living RFCs (ADR-26025)
- **Reviews = QA gates**: human review mandatory before promotion
- **CI/CD = deployment**: automated validation, sync-guard, broken-link checks (ADR-26015)

Reference **ADR-26030** (proposed) which formalizes this principle. Cite Sean Grove's "The New Code" (OpenAI) as external validation of the approach.

### 6. Architectural Governance (NEW section, prominent position)

ADRs as the **main context for development** — this is what the user emphasized:
- 16 active ADRs govern the repo (link to `architecture/adr_index.md`)
- RFC→ADR workflow: proposed = living RFC, accepted = authoritative (ADR-26025)
- Metadata-driven lifecycle with machine-readable YAML frontmatter (ADR-26016, ADR-26017)
- Automated validation: `check_adr.py` enforces format, sections, term references (ADR-26017)
- Content lifecycle policy: asymmetric — articles deleted when superseded, ADRs preserved as negative knowledge (ADR-26021)

### 7. Hub-and-Spoke Ecosystem (NEW section)

- This repo = **standards hub** (conventions, specifications, ecosystem ADRs) (ADR-26020)
- Extracted packages (e.g., vadocs) = **independent spokes** with own implementation decisions
- Research extracted to dedicated monorepo (ADR-26026) — knowledge distillation pattern: only insights retained
- Hub holds the "why"; spokes hold the "how"

### 8. Methodology (rewrite, fold in Generation Workflow)

Tool-agnostic cognitive model approach:
- **Model taxonomy**: reasoning-class (synthesis, requirements) vs. agentic-class (execution, structure) (ADR-26027)
- **Phase 0: Intent Synthesis** — human-led discovery with reasoning-class model before any automated execution (ADR-26028)
- **Generation pipeline** (folded-in mermaid diagram, tool-agnostic labels):
  1. Phase 0: Intent synthesis (consultant prompts)
  2. Draft generation + cross-validation
  3. Human review
  4. CI/CD gates → promotion
- Consultant prompts in `ai_system/3_prompts/consultants/` encode methodology (ADR-26013: JIT transformation)
- Paradigm quote: "prompts = source code, articles = build artifacts, reviews = QA gates"

### 9. Coverage (clean up existing)

Keep the 5-layer architecture. Fixes:
- Security is a cross-cutting concern woven into all layers, not a separate layer 6
- Fix wording to match actual directory contents

### 10. Repository Structure (rewrite tree)

Corrected tree reflecting actual state:
- **Remove**: `research/` (gone per ADR-26026), `tools/prompt_helpers/` (doesn't exist)
- **Add**: `tools/configs/`, `misc/plan/`
- **Fix**: `security/` at root level — note as placeholder or remove
- **Fix typos**: "Wrokflow" → "Workflow", "mitigationtools" → "mitigation tools"

### 11. Toolchain & CI/CD (NEW consolidated section)

Consolidate from scattered references:
- Python hooks in OOP style (ADR-26001), pre-commit framework (ADR-26002)
- Jupytext semantic pairing + sync-guard (ADR-26014, ADR-26015)
- `pyproject.toml` as tool config hub (ADR-26029)
- CI/CD: quality.yml + deploy.yml pipelines
- Validation scripts: `check_adr.py`, `check_broken_links.py`, `validate_commit_msg.py`

### 12. Authorship & Contact (rewrite + fix)

- Rewrite: remove all tool/model names. Frame as "Systems Engineer and AI Methodology Architect"
- Keep: "The Architect" role, "Institutional Resilience" point
- Replace: Aider/model-specific "Hybrid Synergy" → tool-agnostic cognitive roles
- Email: `rudakow.wadim@gmail.com`
- License: keep GPLv3 + CC-BY-SA 4.0

## What Gets Deleted

- "Research & Foundations" section (entire)
- "Generation Workflow" standalone section (folded into Methodology)
- "Motivation" standalone section (key points absorbed into Mission and Hub-and-Spoke)
- All references to Aider, Gemini 3 Flash, Qwen 2.5 Coder
- Incorrect directory entries (research/, tools/prompt_helpers/)

## Writing Approach

This is a **content rewrite, not code**. I will:
1. Draft the full new README as a single Write operation
2. Preserve the existing "What's New" section verbatim
3. Use the same markdown style (headers, bullet lists, blockquotes, mermaid)
4. Reference ADR numbers inline where they add credibility
5. Keep the document scannable — no section longer than ~15 lines of prose

## Step 1: Create ADR-26030 (proposed status)

**File**: `architecture/adr/adr_26030_documentation_as_source_code_for_ai.md`

**ADR-26030: Documentation as Source Code for AI-Consumed Repositories**

Frontmatter:
```yaml
id: 26030
title: "Documentation as Source Code for AI-Consumed Repositories"
date: 2026-02-16
status: proposed
tags: [architecture, methodology, ai]
superseded_by: null
```

**Context**: In the era of AI-backed development, AI systems (RAG pipelines, coding agents, AI assistants) consume documentation as their primary input. Traditional documentation practices — static prose, unversioned, no lifecycle — produce unreliable AI outputs. Sean Grove (OpenAI, "The New Code") articulates this as: "code is a lossy projection from the specification" — discarding specifications while keeping generated code is like "shredding the source and version-controlling the binary."

**Decision**: All content in this repository is treated as production source code — versioned, tested, lifecycle-managed, and machine-readable — because it is the primary input for AI systems.

**Rationale / How existing ADRs implement this principle**:
- ADR-26014 (Jupytext pairing): docs are diffable, mergeable, testable like source code
- ADR-26016, ADR-26023 (metadata): machine-readable frontmatter = API contract for AI consumers
- ADR-26021 (content lifecycle): garbage collection — stale content deleted to prevent RAG noise
- ADR-26025 (RFC→ADR): ADRs as living RFCs with status-based RAG filtering
- ADR-26015 (sync-guard): CI/CD validates documentation integrity before deployment
- ADR-26020 (hub-spoke): hub holds authoritative specs; spokes hold implementation

**Key reference**: Sean Grove, "The New Code" (OpenAI) — https://www.youtube.com/watch?v=8rABwKRsec4

**Alternatives considered**: (to be filled per ADR-26025 promotion gate: ≥2 alternatives required)

After creating ADR-26030, run `uv run tools/scripts/check_adr.py --fix` to update the index.

## Step 2: Rewrite README.md referencing ADR-26030

## Verification

1. **Visual review**: Read the final README.md end-to-end for coherence
2. **Link check**: `uv run tools/scripts/check_broken_links.py --pattern "README.md"`
3. **Directory accuracy**: Spot-check every path in the tree via `ls`
4. **No tool names**: Grep README.md for "Aider", "aider", "Gemini", "Qwen" — expect zero matches
5. **Mermaid syntax**: Confirm diagram renders correctly
6. **ADR references**: Every cited ADR number exists in `architecture/adr_index.md` Active section
