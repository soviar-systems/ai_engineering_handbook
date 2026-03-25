---
id: S-26014
title: "DevOps Consultant Assessment — Frontmatter Validator Architecture and Scope"
date: 2026-03-25
model: claude-opus-4-6
extracted_into: A-26015
---

# S-26014: DevOps Consultant Assessment — Frontmatter Validator Architecture and Scope

System prompt: `devops_consultant.json` v0.3.0 (SVA methodology, WRC scoring).

Two assessments conducted in one session, both feeding A-26015.

+++

## Assessment 1: Implementation Architecture

**Input:** Three approaches to hub-level frontmatter validation — (A) library
module, (B) standalone validator, (C) config-driven module with CLI entry point.

### Critical Diagnosis

The problem is config-code divergence, not code sharing. Hub config (`conf.json`)
defines a complete type system (10 types, block composition, 16 fields) that
nothing enforces. Two domain scripts independently implement partial subsets.
Six types have zero validation.

### SVA Audit Results

- **Approach A** — C5 violation (hub type system not authoritative, domain scripts
  interpret rules independently), C6 violation (O(n) per type, new types need
  new scripts).
- **Approach B** — No violations. Config drives validation, O(1) per type.
- **Approach C** — No violations. Same as B with incremental migration path.

### WRC Scores

| Approach | E | A | P_raw | SVA penalty | P_final | WRC | Classification |
|---|---|---|---|---|---|---|---|
| A: Library module | 0.85 | 0.80 | 0.75 | −0.20 | 0.55 | 0.72 | PoC-only |
| B: Standalone validator | 0.90 | 0.85 | 0.88 | 0.00 | 0.88 | 0.88 | Production-adaptable |
| C: Module + CLI | 0.90 | 0.85 | 0.92 | 0.00 | 0.92 | 0.90 | Production-ready |

**Recommendation:** Approach C. Methodology rerouting triggered because A and B
were below 0.89. C generated as hybrid combining B's config-driven architecture
with incremental migration.

### Calibration Note

Approach A's C5 violation is slightly harsh — it does reuse hub config, but
through domain-script interpretation rather than direct hub-driven validation.
The violation is weaker than ignoring the hub entirely, but still allows silent
divergence between hub and scripts.

+++

## Assessment 2: Scope Boundary

**Input:** Should `check_frontmatter.py` validate hub-level rules only, or also
load spoke configs and validate spoke-level fields and allowed values?

### Options Evaluated

- **X: Hub-only** — validate blocks + field registry + format only
- **Y: Presence yes, values no** — check field existence from hub+spoke, value
  validation stays in domain scripts
- **Z: Full frontmatter** — load spoke config via `options.type`, validate all
  frontmatter: presence, format, and allowed values

### Root Cause

Current spoke configs mix two concerns already separated in config structure:
(1) frontmatter rules (`required_fields`, `statuses`, `severity`) and
(2) structural rules (`required_sections`, `conditional_sections`, `naming_patterns`).

### SVA Audit Results

- **Option X** — C5 violation (domain scripts still implement spoke frontmatter
  logic), C6 violation (new types need domain scripts).
- **Option Y** — C4 violation (splits one concern across two scripts), C5 and C6
  violations.
- **Option Z** — No violations. Spoke configs already contain everything needed.

### WRC Scores

| Option | E | A | P_raw | SVA penalty | P_final | WRC | Classification |
|---|---|---|---|---|---|---|---|
| X: Hub-only | 0.80 | 0.75 | 0.70 | −0.20 | 0.50 | 0.67 | PoC-only |
| Y: Presence/values split | 0.70 | 0.60 | 0.65 | −0.30 | 0.35 | 0.54 | Rejected |
| Z: Full frontmatter | 0.90 | 0.90 | 0.92 | 0.00 | 0.92 | 0.91 | Production-ready |

**Recommendation:** Option Z. Full frontmatter ownership. The resulting scope
boundary:

| Concern | Owner |
|---|---|
| Frontmatter: field presence, format, allowed values | `check_frontmatter.py` |
| Structural: sections, section order, conditional sections | domain scripts |
| Naming: filename patterns, ID format | domain scripts |
| Index: generation, glossary, sectioning | `check_adr.py` |
| Auto-fix: `status_corrections` | `check_adr.py` (mutates file, not validation) |
