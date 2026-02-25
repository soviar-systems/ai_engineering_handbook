---
id: 26034
title: "Agentic OS Paradigm: Skills as Composable Applications"
date: 2026-02-25
status: proposed
superseded_by: null
tags: [architecture, context_management]
---

# ADR-26034: Agentic OS Paradigm: Skills as Composable Applications

## Date
2026-02-25

## Status
proposed

## Context
In the search for a viable, composable, and production-level architecture for a spoke repo "Mentor Generator," we must recognize that the paradigm has shifted from **monolithic prompting** to a **layered ["Agentic OS"](https://www.youtube.com/watch?v=CEvIs9y1uog) strategy**.

A production-grade agent is not just an LLM with a long system message; it is a system of **portable, versioned, and executable expertise**. 

Adopt the 3 Tier Architecture: LLM, Agent, Skills.

### 1. The 3-Tier Architecture of Expertise

Instead of a single JSON blob, we now treat the agent's brain as a stack of three distinct, decoupled layers. This separation prevents the "role confusion" and "state drift" identified in mentor generator experiments (see mentor_generator/docs/architecture/ docs).

* **Skills (The "How"):** Procedural, versioned knowledge. These are the "apps" of the Agentic OS. By moving these to a code-accessible `skills/` directory, we ensure they are **executable** and **testable** independently of the agent's specific subject matter.
* **Projects/Context (The "What"):** Grounding data. This includes the knowledge base, docs, databases, etc. This is the RAG - the **state** that the OS manages, kept distinct from the logic to avoid cognitive overload.
* **Orchestration (The "Universal Interface"):** The "Code is the universal interface" principle - the agent interacts with its environment—and its own memory—through typed, versioned tool calls (MCP, filesystem scripts, etc.) rather than loose narrative instructions.

### 2. From Instructions to Constraints

Our core insight from the mentor generator experiments is that **predictability comes from constraints, not instructions**.

* **The Template as Jail:** In "Mentor Generator," we moved from telling the LLM to "be a good teacher" to forcing it to fill a strictly validated 30-line YAML template. The template acts as the hardware spec of the Agentic OS.

### 3. Portability via "Code as Interface"

The goal of making expertise "portable" means a Skill created in this repository should be executable by any agentic system (Claude Code, a local Ollama instance, or a production RAG pipeline) because it adheres to a standard folder structure:

* `SKILL.md`: The procedural logic.
* `tools/`: The executable scripts (Python/Bash).
* `tests/`: Golden-file fixtures that verify the skill's logic with zero API calls.

## Decision
Adopt the **Agentic OS Paradigm** for agents built by the our organization:
1. **The Processor:** The LLM (Reasoning or Agentic class).
2. **The OS:** The Agent Runtime (file system, Python interpreter, MCP).
3. **The Skills:** Atomic folders containing `SKILL.md` and `/scripts`.

## Consequences

### Positive
- **Transferability:** Skills can be maintained and distributed via `uv` packages across the org.

## Alternatives
- **Instruction-Only Agents (The Status Quo):** Relying on massive system prompts to explain domain logic. **Rejection Reason:** Non-deterministic. As logic becomes complex (e.g., tax law), prompts fail where code succeeds. Leads to "Cognitive Overload" noted in mentor generator's post-mortem analyses.
- **Tool-Calling Without Procedural Code:** Using only external APIs (MCP) for all logic. **Rejection Reason:** Requires an active server for every small task. Local scripts in a "Skill" folder are more resilient and faster for deterministic data transformation.

## References
- Mentor Generator: Problem Catalog v0.41.0 - docs/architecture/research/v0.41.0/problem_catalog_v0.41.md
- [Don't Build Agents, Build Skills Instead – Barry Zhang & Mahesh Murag, Anthropic](https://www.youtube.com/watch?v=CEvIs9y1uog) - Video

## Participants
1. Vadim Rudakov
2. Gemini (Principal Systems Architect)
