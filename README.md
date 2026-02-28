---
title: "AI Engineering Handbook"
author: rudakow.wadim@gmail.com
date: 2026-02-28
options:
  version: 2.6.0
  birth: 2025-10-19
---

# AI Engineering Handbook


This repository is a **Documentation-as-Code hub** for building production-grade AI systems. In the era of AI-backed development, AI systems — RAG pipelines, coding agents, AI assistants — consume documentation as their primary input. Poor documentation produces poor AI outputs. This repository treats documentation with the same rigor as production source code: versioned, tested, lifecycle-managed, and machine-readable.

Content is **generated through a hybrid LLM methodology**, **cross-validated by multiple models**, and **reviewed by a human** before promotion. Architectural decisions are governed by ADRs with machine-readable YAML frontmatter, enabling AI agents to filter and retrieve decisions by status, date, and scope.

> **Mission**: To build reliable, machine-readable documentation infrastructure that AI systems can trust as authoritative input — while enabling MLOps engineers and AI architects to construct audit-ready AI systems using a hybrid LLM+SLM methodology.


## What's new?

v2.6.0 — "The Cognitive Architecture"
* **Skills Architecture**: Three ADRs (26032–26034) define how AI agents should organize knowledge and capabilities — tiered cognitive memory, virtual monorepo for package-driven ecosystems, and the Agentic OS paradigm where skills are composable applications discovered at runtime.
* **Architecture Knowledge Base**: ADR-26035/26036 formalize a taxonomy for evidence artifacts (analyses, sources, retrospectives) with `check_evidence.py` enforcing it automatically (75 tests). The ecosystem now documents how it documents.
* **Ecosystem Scaling**: ADR-26030 (stateless JIT context injection) eliminates context accumulation across agent sessions; ADR-26031 (prefixed namespaces) ensures ADR identifiers stay unique across spoke repositories.
* **7 Open RFCs**: All new ADRs enter as proposed — open for review and feedback before promotion to accepted standards.

v2.5.0 — "The Self-Documenting System"
* **Automated CHANGELOG**: `validate_commit_msg.py` enforces structured commits at commit time; `generate_changelog.py` transforms that history into hierarchical CHANGELOG entries — no manual curation needed.
* **Tool-Agnostic Architecture**: ADR-26004..26008 (tool-specific) superseded by ADR-26027/26028 (cognitive roles); `aidx` rewritten as the generic Multi-Phase AI Pipeline.
* **Promotion Gate**: ADR-26025 formalizes RFC→ADR workflow; `check_adr.py` enforces promotion criteria. 6 ADRs promoted to accepted.
* **Ecosystem Cleanup**: Research extracted to dedicated monorepo (ADR-26026); `pyproject.toml` formalized as tool config SSoT (ADR-26029).

v2.4.0 — "The Governed Architecture"
* **ADR Governance**: All 24 ADRs now carry machine-readable YAML frontmatter (status, date, tags), making the decision history searchable by AI agents and filterable in RAG pipelines. 7 new ADRs (26016–26022) formalize decisions from metadata-driven lifecycle to GitHub Pages hosting.
* **Content Lifecycle**: Superseded articles are now deleted rather than left to mislead RAG retrieval (ADR-26021). `llm_usage_patterns` retired; `choosing_model_size` rewritten as a VRAM budgeting guide.
* **Hub-Spoke Ecosystem**: This repo is now the standards hub; extracted packages like [vadocs](https://github.com/lefthand67/vadocs) are independent spokes with their own implementation decisions (ADR-26020).
* **Validation Toolchain**: `check_adr.py` replaces `check_adr_index.py` — config-driven validation of frontmatter, sections, term references, and index partitioning (110 tests, 98% coverage).


## Live Documentation Site

The rendered knowledge base is published on GitHub Pages (ADR-26022). GitHub is the **source of truth**; the site is the **rendered view** for reading.


## Documentation as Source Code for AI

Traditional documentation is written for humans to read after the fact. In AI-backed development, documentation is the **primary input** that AI systems consume to produce outputs. This makes documentation quality a first-class engineering concern: stale docs produce hallucinations, unstructured metadata makes retrieval blind, missing lifecycle allows noise to accumulate.

This repository implements the Documentation-as-Code paradigm:

- **Docs = source code**: versioned, diffed, tested via Jupytext pairing (ADR-26014)
- **Metadata = API contract**: MyST-native frontmatter makes every document machine-queryable (ADR-26023, ADR-26016)
- **Lifecycle = garbage collection**: superseded content is deleted to prevent RAG noise; ADRs are preserved as negative knowledge (ADR-26021)
- **Structure = architecture**: repository layout is deliberate design, not accumulation; restructuring is governed by ADRs like refactoring is governed by tests (ADR-26020, ADR-26026)
- **ADRs = development backbone**: every major decision is an ADR; proposed ADRs serve as living RFCs (ADR-26025)
- **CI/CD = deployment**: automated validation, sync-guard, broken-link checks (ADR-26015)

This stands in direct opposition to pre-AI knowledge bases — collections of articles with no enforced structure, no traceability, and no automated verification.

See the full rationale in [architecture/manifesto.md](/architecture/manifesto.md).

> In this paradigm: prompts = source code, articles = build artifacts, reviews = QA gates.


## Architectural Governance

ADRs are the **main context for development** in this repository. Every structural, methodological, or tooling decision is recorded as an ADR before implementation.

- **16 active ADRs** govern the repo — see the full list in [architecture/adr_index.md](/architecture/adr_index.md)
- **RFC→ADR workflow**: proposed ADRs serve as living RFCs; accepted ADRs are authoritative (ADR-26025)
- **Machine-readable metadata**: YAML frontmatter with status, date, tags enables AI filtering (ADR-26016, ADR-26017)
- **Automated validation**: `check_adr.py` enforces format, required sections, term references, and index partitioning (ADR-26017)
- **Asymmetric lifecycle**: articles are deleted when superseded; ADRs are preserved as negative knowledge — decision history is never lost (ADR-26021)


## Hub-and-Spoke Ecosystem

This repository is the **standards hub** — it holds conventions, specifications, and ecosystem ADRs (ADR-26020). Implementation lives in independent spokes:

- **Extracted packages** (e.g., [vadocs](https://github.com/lefthand67/vadocs)) are independent spokes with their own implementation decisions
- **Research** is extracted to a dedicated monorepo (ADR-26026) — only distilled insights are retained in the hub
- The hub holds the **"why"**; spokes hold the **"how"**


## Methodology

Content generation follows a tool-agnostic, cognitive-model approach:

- **Model taxonomy**: reasoning-class models (synthesis, requirements) vs. agentic-class models (execution, structure) — selected by capability, not by name (ADR-26027)
- **Phase 0: Intent Synthesis**: human-led discovery with a reasoning-class model before any automated execution (ADR-26028)
- **Consultant prompts** in `ai_system/3_prompts/consultants/` encode methodology as JIT-transformable JSON (ADR-26013)

```mermaid
graph LR
A[Phase 0: Intent synthesis] --> B[Draft generation]
B --> C[Cross-validation by multiple models]
C --> D[Human review]
D --> E[CI/CD gates]
E --> F[Promotion to published directories]

style A fill:#fff,stroke:#333,stroke-width:2px
style B fill:#fff,stroke:#333,stroke-width:2px
style C fill:#fff,stroke:#333,stroke-width:2px
style D fill:#fff,stroke:#333,stroke-width:2px
style E fill:#fff,stroke:#333,stroke-width:2px
style F fill:#fff,stroke:#333,stroke-width:2px
```


## Coverage

Content is organized around five layers of AI systems. Security is a **cross-cutting concern** woven into all layers, not a separate layer.

1. **Execution & Optimization**: CPU/GPU hybrid pipelines, VRAM/RAM management, NVIDIA tuning
2. **Model Development**: SLM selection, tokenization, embeddings
3. **Prompt Engineering**: Modular design, XML schemas, template lifecycle, consultant prompts
4. **Orchestration**: RAG, workflow chaining, agent specialization, structured output
5. **Context Management**: Vector stores, hybrid retrieval, indexing strategies

Read more in [A Multi-Layered AI System Architecture](/0_intro/a_multi_layered_ai_system_architecture.ipynb).


## Repository Structure

```text
.
├── 0_intro/                # Introductory material, high-level overviews
├── ai_system/              # Core content organized by layer
│   ├── 1_execution/        # CPU/GPU optimization, CUDA, VRAM management
│   ├── 2_model/            # Model selection, tokenization, embeddings
│   ├── 3_prompts/          # Prompt-as-Infrastructure: formatting, versioning, consultants
│   ├── 4_orchestration/    # Workflow, agent specialization, structured output
│   └── 5_context/          # RAG, knowledge bases, hybrid retrieval
├── architecture/           # Architectural governance
│   ├── adr/                # Formal ADR documents (YAML frontmatter, machine-readable)
│   ├── evidence/           # Architecture Knowledge Base (analyses, sources, retrospectives)
│   ├── packages/           # Spoke package documentation and PoCs
│   └── post-mortems/       # Retrospectives on failures and lessons learned
├── misc/                   # Non-core work
│   ├── in_progress/        # Drafts, experiments, work-in-progress
│   ├── plan/               # Implementation plans (saved between context switches)
│   └── pr/                 # Telegram channel posts, review checklists
├── mlops/                  # MLOps tooling and pipelines
│   ├── ci_cd/              # GitHub Actions, quality-gate scripts
│   └── security/           # Secret scanning, compliance checks
├── security/               # Centralized security policy hub (placeholder)
└── tools/                  # Supporting utilities
    ├── configs/            # Tool configuration files
    ├── docs/               # Documentation generation helpers, style guides
    ├── scripts/            # Automation: link checking, ADR validation, Jupytext sync
    └── tests/              # Test suites for scripts
```


## Toolchain & CI/CD

The repository uses automated validation to enforce documentation quality:

- **Pre-commit hooks** in OOP Python style (ADR-26001) within the pre-commit framework (ADR-26002)
- **Jupytext pairing** with sync-guard: `.ipynb` and `.md` files stay synchronized; CI blocks unsynced changes (ADR-26014, ADR-26015)
- **Tool configuration** centralized in `pyproject.toml [tool.X]` sections (ADR-26029)
- **CI/CD pipelines**: `quality.yml` (broken links, jupytext sync, script tests) + `deploy.yml` (GitHub Pages deployment)
- **Validation scripts**: `check_adr.py`, `check_evidence.py`, `check_broken_links.py`, `validate_commit_msg.py`, `check_link_format.py`


## Authorship & Contact

My name is Vadim Rudakov, I am a **Systems Engineer and AI Methodology Architect** from Sverdlovsk oblast, Russia. This repository solves a specific problem: the fragility of AI prototypes and the risk of institutional "tribal knowledge."

- **The Architect**: I design the knowledge-generation systems, validation protocols, and the Documentation-as-Code methodology.
- **Cognitive Roles**: Reasoning-class models handle architecture and planning; agentic-class models handle execution and structure. The tools change — the cognitive model stays.
- **Institutional Resilience**: Systems are documented so thoroughly that they survive staff turnover. The methodology is encoded in the system itself.

The repository is licensed under **GPLv3** for its core assets and **CC-BY-SA 4.0** for the article content.


## Contact Information

Vadim Rudakov, rudakow.wadim@gmail.com
