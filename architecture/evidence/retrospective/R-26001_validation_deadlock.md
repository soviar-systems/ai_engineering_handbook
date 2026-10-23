---
id: R-26001
title: Validation Deadlock during Frontmatter Migration
authors:
- name: Qwen Code
  email: agent@qwen.ai
description: A global blocking validation gate met a large legacy backlog and froze
  all commits; the emergency fix worked, but its legacy mode was never given an exit
  criterion.
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
  token_size: 1167
---
# Retrospective: Validation Deadlock during Frontmatter Migration

## Executive Summary

The project entered a state in which no commit could land. The `check-frontmatter` and `check-adr-index` hooks validated the entire repository and exited non-zero on any violation, so a large backlog of files that predated ADR-26042 blocked every change, including compliant ones.

The deadlock was broken by replacing the global gate with a **commit-scoped filter**: staged files are validated strictly, while violations elsewhere in the repository are reported as `[LEGACY]` warnings that exit 0.

That fix was correct as an emergency response, and it did unblock the project. It also introduced a second-order problem this record did not originally name: the legacy mode had **no exit criterion**. Nothing required the warning count to fall, so a temporary transition state became the permanent operating mode of the repository.

## Introduction

This retrospective was written on 2026-06-27, during the frontmatter migration that followed ADR-26042 (Common Frontmatter Standard). It records why the repository became uncommittable and what was changed in response.

The scope is the validation architecture: the pre-commit hooks, the scripts they invoke, and the way those scripts decided whether to block a commit.

## Technical Diagnosis

### Symptom

Every `git commit` attempt was blocked, regardless of the change being made. The blocking hooks were `check-frontmatter` and `check-adr-index`.

The symptom was insensitive to the content of the commit. A commit touching a single compliant file failed exactly as a commit touching twenty non-compliant files did, because the outcome did not depend on the staged set at all.

### Contributing Factors

1. **Strict new standards.** ADR-26042 imposed rules on frontmatter field ordering, naming, and namespaces.
2. **Global scanning.** The hooks were configured with `pass_filenames: false`, which forced every script to run a full repository scan on every execution.
3. **Legacy debt.** A significant volume of pre-existing files did not comply with the new standard.

## Root Cause

The deadlock was the intersection of the three factors above, not any one of them.

A strict standard alone is harmless if violations are fixed as they are introduced. Global scanning alone is harmless if the repository is compliant. Legacy debt alone is harmless if validation is scoped to the change set. Together, they made the gate unsatisfiable: compliance was required of the whole repository before any part of it could move, and the whole repository was not compliant.

The structural error was the choice of **unit of validation**. Validating the repository on every commit meant the gate's failure condition was a property of the entire history rather than of the change under review, so the gate could only be satisfied by a bulk migration that the gate itself prevented.

## Impact Assessment

Work stopped. No commit could land, so the frontmatter migration could not proceed through the mechanism that was supposed to enforce it.

The more consequential impact is the one that outlived the incident. Because the new mode reported violations without blocking, "the hook passed" stopped being a statement about compliance and became a statement about scope. The repository could be described as green while carrying a growing list of `[LEGACY]` violations, and nothing in the system made that list need to shrink.

## Corrective Actions

The validation strategy shifted from a **global quality gate** to a **commit-scoped filter**:

- **Staged files** are validated strictly. Any violation in a file currently being committed results in exit 1.
- **Other files** are validated for visibility. Violations outside the current commit are reported as `[LEGACY]` warnings and result in exit 0.

This allowed the project to resume movement while retaining a visible list of legacy errors to be cleaned up incrementally.

## Preventive Measures

- **Avoid global blocking gates.** Never introduce a global blocking gate for a new standard without either a transition period or a scoped mechanism.
- **Prefer scoped validation.** In a large repository, a hook should govern the files it is meant to govern within the current change set.
- **Technical debt visibility is not blocking.** Debt should be reported and tracked without preventing the deployment of new, correct code.
- **Every non-blocking mode needs an exit criterion.** A legacy/warning mode is a transition state. It must carry a condition under which it ends — a target count, a date, or a scoped migration checklist — or it becomes the permanent architecture. This record's own fix was missing that clause, which is why the warning count continued to grow after the deadlock was resolved.

## References

- [AI Engineering Book — README](/README.md)
- [ADR-26042 — Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md)
- [Post-Mortem: Sunset of the AI Engineering Book](/architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md)
