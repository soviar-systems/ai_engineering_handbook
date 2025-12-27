-----

Version: 0.2.2
Birth: 2025-10-19
Modified: 2025-12-27

-----

# About

This repository provides a **systematized, AI-engineered knowledge base** for building production-grade AI systems using **Small Language Models (SLMs)**. All content is **generated, validated, and versioned through a controlled Language Model (LM) workflow**—treated as code, not prose.

> **Mission**: Enable MLOps engineers and AI architects to construct **reliable, maintainable, and auditable** AI infrastructure by treating documentation as executable, testable artifacts.

This is not a prompt repository. It addresses the **full stack** required to deploy and sustain LM-powered systems: execution, model, prompt, orchestration, context, and security layers.

> NOTE! The .ipynb files and some .md files use [myst](https://mystmd.org/) syntax. GitHub does not render this syntax (yet), do not consider such snippets as bugs.

---

## Authorship & Licensing

This is a **practitioner-focused engineering repository**, not academic literature. Therefore:

- **No bibliographic references** are included.
- **Provenance is encoded** in system prompts (e.g., [`slm_system_consultant.json`](./helpers/ai_consultants/slm_system_consultant.json)), which capture reasoning patterns used during generation. These prompts are open for inspection and serve as traceable “concept lineage” artifacts.
- **I do not claim originality of ideas**—only of the **generation methodology**, **validation protocol**, and **structural design**.

> I am the architect of the knowledge-generation system. The ideas flow from public technical discourse; the synthesis, cross-validation, and organization are my engineered contribution.

The repository is licensed under **GPLv3** for its core assets—**directory structure, system prompts, validation rules, and generation pipelines**—which are **software artifacts**, not static documents. This enforces the *documentation-as-code* principle. The article content is licensed under **CC-BY-SA 4.0**.

---

## Coverage

Content is organized around the six layers of LLM systems:

1. **Execution & Optimization**: CPU/GPU hybrid pipelines, memory (VRAM/RAM) management, NVIDIA tuning
2. **Model Development**: SLM selection, tokenization, embedding, security hardening
3. **Prompt Engineering**: Modular design, XML schemas, template lifecycle
4. **Orchestration**: RAG, workflow chaining, structured output control
5. **Context Management**: Vector stores, hybrid retrieval, indexing strategies
6. **Security & Quality**: Bias detection, access control, validation templates  (spread across all other layers)

All materials are **LM-generated**, then **cross-validated by multiple models**, and deeply **reviewed before promotion** from draft to final by me. The production of one handbook may take tens of manual and AI-backed iterations before I am ready to put it into the main branch, but I understand it can still have problems, so feel free to leave issues.

---

## Repository Structure

```text
ai-systems-engineering/
├── 0_intro/               # Foundational principles & communication styles
├── 1_execution/          # Execution strategies and hardware-aware tuning
├── 2_model/              # Model lifecycle: selection, security, embedding
├── 3_infrastructure/     # Prompt modularity, templates, and management
├── 4_orchestration/      # Workflow engines, chaining
├── 5_context/            # Retrieval, vector DBs
├── helpers/
│   ├── ai_consultants/     # System prompts for AI-generated content
│   ├── scripts/            # Utility scripts for various tasks
│   └── website/            # Configuration files for the repo's website
├── mlops/                # Versioning, CI/CD, deployment guardrails
├── pr/                   # Public Relations directory
├── research/
│   └── slm_from_scratch/  # Research and development of Small Language Models
├── tools/                # Tools for AI development & deployment
│   ├── ai_agents/
│   └── languages/
└── website/              # Website configuration files for the repo's website
```

### Research & Foundations (`/research`)

While the core layers of this repository focus on the **systemic orchestration** of AI, the `research/` directory is dedicated to the **first principles** of Small Language Models. We treat the transition from a single neuron to a production-grade Transformer not as a "black box," but as a verifiable engineering stack.

In this repository, "Research" is not academic—it is **forensic**. By building the model from scratch:
1. **Security is Hardened**: We understand exactly how data flows through the weights, making it easier to identify points of failure for prompt injection or data leakage.
2. **Optimization is Precise**: Hardware-aware tuning (Layer 1) is more effective when you understand the computational graph of the model (Research Layer).
3. **Validation is Absolute**: We use manual gradient checks in research to ensure that our automated validation protocols in the MLOps layer are mathematically sound.

#### SLM From Scratch

The primary initiative within this directory is the **bottom-up construction of SLM architectures**. This phase-based research ensures that every higher-level optimization (like KV-caching or Quantization) is grounded in a deep understanding of the underlying calculus.

### Public Relations directory

`pr` directory is the collection of the informational telegram posts. These posts should not be considered as authoritative or comprehensive documentation.

---

## Generation Workflow

All content follows a reproducible LM pipeline, mirroring software CI/CD:

1. **Idea elaboration:** [slm_system_consultant.json](/helpers/ai_consultants/slm_system_consultant.json) explores and stress-tests concepts
2. **Draft generation**: [handbook_consultant.json](/helpers/ai_consultants/handbook_consultant.json) produces articles, diagrams, and code
3. **Cross-validation:** Multiple models critique and refine outputs
4. **Version control:** Every file is tracked, diffed, and tested like source code
5. **Human review:** Final sanity check before promotion to published directories

> In this paradigm: prompts = source code, articles = build artifacts, reviews = QA gates.

```mermaid
graph TD
A[Start] --> B[Idea elaboration: slm_system_consultant.json]
B --> C[Draft generation: handbook_consultant.json]
C --> D[Cross-validation by multiple models]
D --> E[Version control]
E --> F[Human review]
F --> G[Promotion to published directories]
G --> H[End]

style A fill:#f96,stroke:#333,stroke-width:4px
style B fill:#fff,stroke:#333,stroke-width:2px
style C fill:#fff,stroke:#333,stroke-width:2px
style D fill:#fff,stroke:#333,stroke-width:2px
style E fill:#fff,stroke:#333,stroke-width:2px
style F fill:#fff,stroke:#333,stroke-width:2px
style G fill:#fff,stroke:#333,stroke-width:2px
style H fill:#f96,stroke:#333,stroke-width:4px
```

---

## Motivation

My final goal is to build AI solutions that I can maintain as ordinary software, like a calculator. This goal - if achievable - can be achieved only with the strong methodology behind it. MLOps, Devsecops, models fine-tuning, context management, and so on. You can easily prototype almost anything
with the little help from AI, but the question is whether you can build a reliable, production level system.

Every problem documented here is one I’ve confronted while developing local SLM stacks under resource constraints. Since I learn by doing—and my primary collaborator is the AI itself—I share this repository publicly to:

- Invite technical critique on my understanding of AI systems
- Offer a methodologically consistent alternative to ad-hoc prompt hacking
- Demonstrate that documentation can be engineered, not just written
