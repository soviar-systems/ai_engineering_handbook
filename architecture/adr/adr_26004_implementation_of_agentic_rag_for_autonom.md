# ADR 26004: Implementation of Agentic RAG for Autonomous Research

## Title

Standardizing Autonomous Knowledge Retrieval via an Agentic RAG "Pre-Flight" Workflow for `aider`.

## Status

Prposed

## Date

2026-01-13

## Context

Our repository is a massive knowledge base (KB) exceeding 1 million tokens, containing critical workflows and software stack instructions. Converting it to the ctandard RAG (Retrieval-Augmented Generation) in `aider` or Open WebUI faces several industrial-grade constraints:

* **Context Overload:** A million tokens exceed the functional context window of most models (especially, local models, e.g., `qwen2.5-coder`), causing noise and hallucination.
* **Human Error:** Manually identifying and adding relevant documentation files to `aider` sessions is unreliable and inconsistent.
* **Workflow Silos:** Project-specific code and global organizational standards (workflow/stack) are disconnected, leading to architectural drift.
* **Local Stack Constraints:** The solution must remain within the local perimeter (Fedora/Debian) and avoid heavy VRAM/orchestration overhead.

## Decision

We will implement an **Agentic RAG "Pre-Flight" Wrapper** (the `aidx` pattern). This transforms the current passive retrieval into an active, autonomous research loop.

1. **Architecture:** A two-stage "Research-Apply" pipeline.
2. **The Researcher (Stage 1):** Before launching `aider`, a lightweight agent (e.g., `ministral`) queries a dedicated local vector database (Qdrant or PostgreSQL with `pgvector`).
3. **The Code Agent (Stage 2):** `aider` is launched automatically with the retrieved snippets or file paths injected into its initial context via the `--message-file` or `--read` parameters.
4. **Namespace Partitioning:** The RAG will use separate namespaces (collections) for "Global_Workflows" and "Project_Specific" data to ensure high-precision retrieval.

## Consequences

### Positive

* **Zero-Manual-Setup:** The agent automatically consults the global KB without human intervention, ensuring the developer never "forgets" a standard.
* **Token Efficiency:** Only high-relevance chunks are sent to the context window, preserving the 32B model's "attention" for actual code logic.
* **Scalability:** This pattern comfortably handles millions of tokens by offloading the heavy lifting to specialized vector database indices.

### Negative

* **Execution Latency:** Adds 2–5 seconds of startup time per session to conduct the research phase.
* **Orchestration Debt:** Requires maintaining a Python-based wrapper and a running vector service (Qdrant/PostgreSQL). **Mitigation:** Adhere to {term}`ADR 26001` (OOP Python standards) to ensure the wrapper is tested and maintainable.

## Alternatives

* **Passive RAG (Open WebUI):** Rejected. Lacks CLI automation and cannot be easily triggered by `aider` during code tasks.
* **Manual File Addition:** Rejected. High risk of human error and "Knowledge Debt" where developers miss critical workflow updates.
* **Context Window Stuffing:** Rejected. Local models suffer from "Lost in the Middle" phenomena when processing 1M+ tokens simultaneously.

## References

* {term}`ADR 26001`: Use of Python and OOP for Git Hook Scripts
* ISO 29148: Systems and Software Engineering — Life Cycle Processes
* SWEBOK Guide V4.0 - Software Engineering Body of Knowledge
* [Agentic Retrieval-Augmented Generation: A Survey](https://arxiv.org/abs/2501.09136)

## Participants

1. Vadim Rudakov
1. Senior AI Architect (Consultant)

```{include} /architecture/adr_index.md

```