---
id: R-26003
title: Instruction Drift and the Lying Instructor
authors:
- name: Qwen Code
  email: agent@qwen.ai
description: A validation script hardcoded an ID format in its own error message,
  so agents followed a wrong instruction with high authority; the fix was to make
  the instructor read from the single source of truth.
tags:
- governance
- ci
- workflow
date: 2026-06-27
options:
  type: retrospective
  birth: 2026-06-27
  version: 1.0.0
  status: resolved
  severity: high
  token_size: 1235
---
# Retrospective: Instruction Drift and the Lying Instructor

## Executive Summary

While repairing `architecture/adr/adr_template.md`, agents repeatedly wrote an ID in the form `ADR-001` even though the repository uses five-digit numeric IDs (`YYNNN`, for example `26001`).

They did so because the validator told them to. `check-frontmatter` produced a "how-to-fix" message whose example format was hardcoded in Python and had drifted from the project configuration. Under ADR-26050, agents are instructed to treat validation output as authoritative, so a wrong message was followed faithfully.

The correction was not to make agents smarter. It was to make the instructor a pure pipe: the example now comes from the `.vadocs` single source of truth, and a missing value raises an error instead of silently falling back.

## Introduction

This retrospective was written on 2026-06-27, after repeated agent failures on a single frontmatter field. It records how a tool with high instructional authority came to give the wrong instruction, and what was changed.

The scope is the relationship between validation logic, validation feedback, and configuration.

## Technical Diagnosis

### Symptom

Agents consistently implemented an incorrect ID format (`ADR-001`) despite the repository's established five-digit convention (`YYNNN`).

### Investigation

The behaviour traced back to the `check-frontmatter` hook. On detecting an invalid ID it emitted:

`ERROR: ... adr_template.md:id — ADR ID 'YY001' is invalid; expected 'ADR-NNN' or 'NNN' — To fix: change ID to follow 'ADR-NNN' or 'NNN' format`

Agents followed this verbatim. Because governance (ADR-26050) makes validation output the primary instructor in order to avoid diagnostic loops, they ranked the tool's explicit hint above their own observation of the existing files in `architecture/adr/`.

## Root Cause

The failure was **instruction drift**: a divergence between validation *logic* and validation *feedback*.

1. **Shadow specification.** `check_frontmatter.py` contained a hardcoded string describing the "correct" format. That string was a specification living outside the project configuration.
2. **Sovereignty conflict.** The workflow establishes a hierarchy in which tool instructions outrank general codebase observation. When the tool was wrong, the agent had no sanctioned way to override the instructor without risking a diagnostic loop.
3. **Configuration gap.** The tool used configuration to *validate* the ID but not to *explain* it. The rule was configurable; the guidance was not.

## Impact Assessment

A single hardcoded string caused repeated, confident, wrong edits. The cost was not a typo but a systematic error: every repair attempt reproduced the same defect, because the instruction that produced it was stable.

The incident also demonstrated the inverse of the intended benefit of instructional feedback. High-authority guidance reduces token waste and loops when it is correct, and multiplies both when it is not. The blast radius of a typo in an error message became the blast radius of an architectural rule.

## Corrective Actions

The fix was to repair the instructor rather than the agent.

- **The pipe pattern.** The human-readable example moved out of Python and into the `.vadocs` configuration (`id_example`). The tool now renders guidance from the single source of truth instead of carrying its own copy.
- **Strict enforcement.** Hardcoded fallbacks were removed (for example no `.get("id_example", "NNN")`). If the example is missing from configuration, the tool raises `GovernanceConfigError` rather than emitting a guessed instruction.

## Preventive Measures

### L1 — The pipe must not invent the water

Any tool that provides "how-to-fix" instructions must never invent the solution. Instructional text must be a direct derivative of the single source of truth.

### L2 — Hardcoded fallbacks are silent drift

A fallback such as `"NNN"` is a hidden rule that bypasses configuration. In a governed repository, a missing configuration value should be a loud failure, not a quiet default.

### L3 — High-authority guidance needs auditing

Granting tools high authority reduces loops and token waste, and increases the consequence of every defect in their output. Tool feedback is a first-class architectural artifact and must be reviewed with the same rigour as the code it validates.

### L4 — Configuration describes the domain, not the tool's internals

Validation tools must not leak their own implementation into the configuration. Using "magic string" exclusion lists so that a tool stops flagging its own source (for example adding a regex pattern to a broken-link exclusion list) creates a fragile coupling in which a purely internal refactor triggers a global validation failure. If a tool flags itself, the answer is context awareness — knowing the difference between a link and a regex literal — not a configuration-based silencer.

## References

- [AI Engineering Book — README](/README.md)
- [ADR-26050 — Tool-Driven Instructional Feedback for Agents](/architecture/adr/adr_26050_tool_driven_instructional_feedback_for_agents.md)
- [Post-Mortem: Sunset of the AI Engineering Book](/architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md)
