---
id: 26019
title: "Mirroring YAML Metadata to Document Body for Human Verification"
date: 2026-02-01
status: proposed
superseded_by: null
tags: [governance, documentation, context_management]
---

# ADR-26019: Mirroring YAML Metadata to Document Body for Human Verification

## Title

Mirroring YAML Metadata to Document Body for Human Verification

## Date

2026-02-01

## Status

proposed

## Context

Following the mandate for universal YAML frontmatter (ADR-26018), we face a critical usability gap for human engineers. While YAML is the Single Source of Truth (SSoT) for machines and AI agents, it is often rendered invisible or difficult to parse in standard CLI environments (e.g., `cat`), raw Git diffs, and basic Markdown viewers.

Relying solely on YAML delimiters (`---`) for metadata creates a "blackout" during manual peer reviews or terminal-based navigation. Without a visible reflection of this state in the document body, the risk of "Metadata Drift" increases: a human may assume a document is current based on prose, while the machine-hidden YAML marks it as `superseded` or `deprecated`.

## Decision

We will implement an automated **Mirroring Pattern** that projects structured YAML metadata into a human-readable "Reflection Block" using specific HTML anchors to differentiate from standard Markdown thematic breaks.

1. **YAML Delimiters**: We continue to use standard `---` triple-dashes for the YAML frontmatter block to maintain compatibility with `python-frontmatter` and MyST.
2. **Reflection Anchors**: For the body-mirror, we will use HTML comments `and`.
* **Why**: Unlike `---`, which is commonly used for thematic breaks in content (e.g., in `llm_usage_patterns.md`), HTML anchors provide a unique, collision-free namespace for automation scripts.


3. **Automated Sync**: A `pre-commit` hook will parse the YAML and overwrite the content between these HTML anchors.
4. **UI/UX Standard**: The mirrored block must be formatted as a human-friendly header (e.g., a bold list or blockquote) to serve as the primary UI for manual verification.

## Consequences

### Positive

* **Visual Integrity**: Engineers can instantly verify "owner" and "status" in any environment, including Fedora/Debian terminals.
* **Deterministic Ingestion**: By using HTML anchors, the RAG/Vector DB ingestion pipeline can easily identify and *strip* the redundant mirror block to optimize the **Signal-to-Noise Ratio (SNR)**.
* **AI Efficiency**: Prevents "Context Contamination" in vector embeddings by ensuring only the technical logic is vectorized while metadata is stored in DB fields.

### Negative / Risks

* **Anchor Fragility**: If an engineer deletes the HTML comments, the sync script will fail. **Mitigation**: The `pre-commit` hook will validate anchor presence in all non-ADR artifacts.
* **Sync Overhead**: Requires local Python dependencies (`python-frontmatter`) and Jupytext for paired notebooks.

## Alternatives

* **Standard Markdown Breaks (`---`) for Mirroring**: Rejected. Causes parsing collisions with existing content separators in handbooks.
* **Prose-only Metadata**: Rejected. Prevents the deterministic machine-readability required for AI agents like `aider`.

## References

* [ADR-26014: Semantic Notebook Pairing Strategy]
* [ADR-26016: Metadata-Driven Architectural Records Lifecycle]
* [ADR-26017: ADR Format Validation Workflow]
* [ADR-26018: Universal YAML Frontmatter Adoption for Machine-Readable Documentation]

## Participants

1. Vadim Rudakov
2. Principal Software Engineer (Gemini)
