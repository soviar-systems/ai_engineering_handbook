---
id: A-26011
title: "vadocs as Structural Type Checker — The Lean Analogy for Documentation"
author: Vadim Rudakov, rudakow.wadim@gmail.com
description: "Evaluates whether vadocs occupies the same architectural slot as Lean (proof assistant) but for documentation. Maps the analogy across verification mode, reward signal quality, and pipeline role. Identifies where the parallel holds (binary verification, config-as-spec) and where it breaks (semantic depth, auto-fix capability)."
tags: [architecture, governance]
date: 2026-03-21
status: active
sources: [S-26013]
produces: []
options:
  type: analysis
  birth: 2026-03-21
  version: 1.0.0
---

# A-26011: vadocs as Structural Type Checker — The Lean Analogy for Documentation

+++

## Problem Statement

S-26013 analyzes the symbiosis between Lean (dependent type theory proof assistant) and GRPO (Group Relative Policy Optimization), identifying **deterministic binary verification** as the property that makes Lean a perfect reward function for RL training. The question: does vadocs — the ecosystem's documentation validation engine — occupy the same architectural slot as Lean, but for the documentation domain?

## Key Insights

### The Structural Mapping

vadocs and Lean occupy the same position in their respective pipelines: **binary verification gate driven by a formal specification**.

| Property | Lean (for proofs) | vadocs (for docs) |
|---|---|---|
| **What it checks** | Type-theoretic propositions | Document structure, frontmatter, cross-refs, sections |
| **Verification mode** | Binary: compiles or doesn't | Binary: validates or returns `ValidationError[]` |
| **Reward signal quality** | Perfect (SNR = ∞) | Near-perfect within its schema scope |
| **Role in pipeline** | Compiler / proof checker | Pre-commit validator / CI gate |
| **Specification language** | Lean's type system | YAML config files (`frontmatter.config.yaml`, `adr.config.yaml`, `evidence.config.yaml`) |
| **Auto-fix capability** | None (proofs must be constructed) | Yes — `fixers/` can auto-correct structural issues |

### Where the Analogy Holds

The core property S-26013 identifies in Lean — **infinite Signal-to-Noise Ratio** in verification — maps directly to vadocs:

1. **Binary certainty.** A document either has valid frontmatter or it doesn't. An ADR either contains all required sections or it doesn't. A `{term}` reference either resolves in the glossary or it doesn't. A link either points to an existing file or it doesn't. There is no "probably valid."

2. **Config-as-spec.** Lean's type system is the specification; vadocs' YAML config hierarchy (`frontmatter.config.yaml` hub → domain spoke configs) is the specification. Both are machine-readable, deterministic, and version-controlled.

3. **Pre-commit-as-compiler.** The `tools/scripts/` suite (future vadocs CLI) runs in pre-commit hooks as a binary gate: commit passes or fails. This is the same architectural role as `lean --check` in a CI pipeline. No "flaky tests," no probabilistic evaluation.

4. **Eliminates the critic.** S-26013 notes that Lean removes the need for a learned "Critic Model" in RLHF. Similarly, vadocs removes the need for human editorial review of structural compliance — the config is the critic, and it's deterministic.

### Where the Analogy Breaks

**1. Semantic depth — type checker, not proof assistant.**

Lean verifies *logical truth*: the content of the proof is checked against axioms. vadocs verifies *structural correctness*: it confirms an ADR has a "Decision" section, but cannot verify that the decision is *sound* or that it contradicts another ADR.

This places vadocs closer to a **type checker** (catches `undefined variable`) than a **proof assistant** (catches `invalid proof step`). It ensures documents are well-formed, not that they are correct.

**2. The Proof Gap manifests differently.**

S-26013 warns: "Lean guarantees consistency with the spec, not alignment with reality." For vadocs, the spec is the config hierarchy. If `evidence.config.yaml` defines wrong required sections, vadocs enforces wrong rules perfectly. Same structural risk as Lean, but the blast radius is documentation quality rather than mathematical truth.

**3. Auto-fix goes beyond Lean.**

Lean cannot write proofs for you. vadocs *can* fix frontmatter, sync YAML↔Markdown bidirectionally, and update indices. This makes vadocs more like a **compiler with auto-correction** — closer to `rustfmt` + `rustc` fused — than a pure verifier.

**4. Composability differs.**

Lean proofs compose: a proven lemma can be reused in a theorem. vadocs validations do not compose in this way — validating one ADR says nothing about the consistency of the ADR corpus as a whole. Cross-document consistency (e.g., "ADR-26040 supersedes ADR-26031") requires a different class of validation not yet implemented.

### The Formal-Guided Hybrid Pattern

S-26013 recommends **"Formal-Guided Hybrid Generation"** (WRC 0.89) as the production-viable methodology: generate in a familiar language, verify with formal specs.

The ecosystem already implements this pattern for documentation:

- Authors write in **MyST Markdown** (the familiar language)
- vadocs + `tools/scripts/` **verify against formal config schemas** (the formal spec)
- Pre-commit hooks enforce the gate **before content reaches trunk** (the CI compiler)

This is the documentation-domain instantiation of the same architecture S-26013 recommends for code.

### Depth Classification

| Verification Level | Lean Equivalent | vadocs Status |
|---|---|---|
| **Lexical** — file exists, has frontmatter | Syntax check | Implemented |
| **Structural** — required fields, sections, valid values | Type checking | Implemented |
| **Referential** — links resolve, `{term}` refs exist | Import resolution | Implemented (`check_broken_links.py`, `myst_glossary.py`) |
| **Cross-document** — status transitions valid, no contradictions | Proof checking | Not implemented (future: corpus-level consistency) |
| **Semantic** — decision is sound, evidence supports conclusion | Theorem proving | Out of scope (requires human or AI reviewer) |

vadocs currently covers levels 1–3. Level 4 is architecturally feasible (config-driven status transition rules exist in `adr_config.yaml`). Level 5 is the "proof gap" — it requires understanding intent, which is outside the scope of a structural validator.

## References

- `S-26013` — Lean as GRPO Verifier — Formal-Guided Hybrid Generation Analysis (Claude Opus 4.6 research)
- [A-26009: Compass — Realistic State of Agentic AI 2026](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md)
- [A-26005: Doc Type Interfaces — Unified Validation](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md)
