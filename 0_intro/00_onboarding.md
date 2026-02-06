---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Onboarding

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.4.0  
Birth: 2026-01-03  
Last Modified: 2026-01-26

---

+++

General fast way to understand the architecture and workflows is to follow this docs workflow:

```
ADR -> tools -> workflow directories
```

+++

## **Step 1. Setup Your Environment**

+++

Run this scripts in your GNU/Linux terminal:

```bash
bash ./tools/scripts/configure_repo.sh
```

(in development) Configure JupyterLab for working with the files in this repo.

+++

## **Step 2. Read Most Important Materials**

+++

### Arthicture

+++

1. ["A Multi-Layered AI System Architecture"](/0_intro/a_multi_layered_ai_system_architecture.ipynb) to understand the repo structure.
2. Series on how we work with Git in `/tools/docs/git/`.
3. ADRs in `/architecture/adr` to understand our choices and our stack.

+++

### Working with the Repository

+++

1. [Setup Jupytext and git hooks](/tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb)
1. ["Production Git Workflow Standards"](/tools/docs/git/01_production_git_workflow_standards.ipynb)
1. ["The Scripts That Help"](/tools/docs/scripts_instructions/README.ipynb)

+++

### Document Metadata Conventions

+++

Every content article must include a **YAML frontmatter** block and a **reflected metadata block** (the first cell after the H1 title). The reflection block makes ownership and freshness visible on the rendered static site, where custom YAML fields are otherwise ignored by `myst build --html`.

1. ["YAML Frontmatter for AI-Enabled Engineering"](/ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.ipynb) — the frontmatter schema and why it matters for RAG
1. ["The Reflected Metadata Pattern"](/ai_system/5_context/reflected_metadata_pattern.ipynb) — how to project YAML metadata into the document body
1. {term}`ADR-26018` — the mandate for universal YAML frontmatter
1. {term}`ADR-26019` — the positional convention for the reflection block

+++

### Your AI Tools

+++

1. ["The aidx Industrial AI Orchestration Framework"](/ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.ipynb) - the high level description of our agentic approach. 
1. ["General Purpose (Abstract Synthesis) vs Agentic (Instruction Adherence) Models"](/ai_system/2_model/selection/general_purpose_vs_agentic_models.ipynb) - what models to use for different types of tasks, see the aidx description above for more details.
1. ["VIM in AI Era: Hybrid Setup with Ollama and Aider"](/tools/docs/ai_agents/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)

+++

## **Keep Your Work Clean**

+++

This repository contains the very different types of files - docs, configs, code. Before commit and push to the repository all you have done must be tested and validated for not breaking what is already built, like cross-links, scripts for internal use, etc.

The most of validation is done for you by automatic checks (or will be done for you as soon as possible) via [pre-commit hooks](/tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.ipynb) and GitHub actions. But some validation should be done by you manually - it concerns publishing new `.ipynb` docs in the first hand.

Before commiting, run the MyST server locally from your terminal 

```bash
uv run myst start
```

and:
- analyze the stdout messages for any errors,
- take a look at your new articles or modified files by opening `localhost:3000` in your web browser.

Fix what you can fix or ask for help from the peers before Pull Request.
