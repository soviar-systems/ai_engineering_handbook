---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Agentic RAG and Standardized Automation for AI Engineering

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2026-01-13  
Last Modified: 2026-01-13

---

+++

This handbook outlines the architectural standards for local development workflows, specifically focusing on the transition from passive retrieval to **Agentic RAG** (Retrieval-Augmented Generation) and the standardization of infrastructure through **Object-Oriented Python**.

:::{seealso}
> ["ADR 0004: Implementation of Agentic RAG for Autonomous Research"](/architecture/adr/adr_0004_implementation_of_agentic_rag_for_autonom.md)
:::

+++

## 1. Architectural Justification: The "Pre-Flight" Pattern

+++

In industrial AI systems (aligned with **SWEBOK** and **ISO 29148**), we are moving from a **Passive Retrieval** model to an **Active (Agentic) Retrieval** model. A "workaround" fixes a bug; an "architectural pattern" addresses a fundamental requirement. Our requirement is **Zero-Human-Setup** for knowledge bases (KB) exceeding 1M+ tokens.

* **The Problem:** Standard RAG (e.g., within `aider` or Open WebUI) faces "Context Overload." 1M tokens exceed the functional window of local models like `qwen2.5-coder`, leading to noise and hallucinations.
* **The Solution:** An **Agentic RAG "Pre-Flight" Wrapper** (the `aidx` pattern). This decouples "Knowledge Retrieval" from "Code Generation".

+++

## 2. Core Methodology: Research-Apply Pipeline

+++

The implementation utilizes a two-stage pipeline to bridge the gap between a high-volume Global KB and a task-specific Coding Agent.

| Stage | Component | Action |
| --- | --- | --- |
| **Stage 1** | **The Researcher** | A lightweight agent (e.g., `ministral`) queries a local vector DB (**Qdrant** or **PostgreSQL/pgvector**). |
| **Stage 2** | **The Code Agent** | `aider` is launched with retrieved snippets injected via `--message-file` or `--read`. |

**Namespace Partitioning:** To ensure precision, the RAG uses separate namespaces for "Global_Workflows" and "Project_Specific" data.

+++

## 3. Engineering Standards: ADR 0001 Compliance

+++

To prevent "Orchestration Debt," all wrappers and Git hooks must follow the standards defined in [**ADR 0001**](/architecture/adr/adr_0001_use_of_python_and_oop_for_git_hook_scripts.md).

* **Language:** Python 3.13+ is the mandatory standard.
* **Paradigm:** **Object-Oriented Programming (OOP)**. Logic must be encapsulated in classes to allow `pytest` integration into the workflow.
* **Validation:** Every hook and tool must have a corresponding `pytest` suite to simulate Git states (e.g., detached HEAD, merge conflicts).

+++

## 4. Validation Gap Analysis

+++

Evaluating the transition from Passive to Agentic retrieval based on **SWEBOK Quality-2.1** standards:

| Concept | Status | Architectural Justification |
| --- | --- | --- |
| **Separation of Concerns** | **Justified** | Decouples "finding truth" from "applying code changes". |
| **State Management** | **Justified** | Using a global DB maintains a "Single Source of Truth" across projects. |
| **Cognitive Load** | **Justified** | Eliminates human-in-the-loop for context gathering (ISO 29148 Efficiency). |

+++

## 5. Potential Technical Debt & Mitigations

+++

* **Execution Latency:** Python startup (~100ms) and RAG research (2–5s) add overhead.
    * *Mitigation:* Defer heavy imports; active research is faster than manual searching.

* **Embedding Drift:** If the KB isn't updated, the Researcher will retrieve outdated advice.
    * *Mitigation:* Automated re-indexing triggers upon KB changes.
