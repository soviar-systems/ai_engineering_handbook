---
id: R-26004
title: 'Post-Mortem: Sunset of the AI Engineering Book'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Final post-mortem on the AI Engineering Book (2025-2026) — what it achieved,
  how its governance layer outgrew the knowledge it governed, and why archival is
  the correct end state.
tags:
- governance
- documentation
- workflow
date: 2026-10-24
options:
  type: retrospective
  birth: 2026-10-24
  version: 1.0.0
  status: resolved
  severity: high
  token_size: 4660
---
# Post-Mortem: Sunset of the AI Engineering Book

## Executive Summary

The AI Engineering Book ran from **2025-10-19 to 2026-10-24**: 686 commits, one author, 15 releases, 532 tracked files, 19 MB of Git history, and a published MyST site. It succeeded as a knowledge artifact and failed as a *sustaining system*. Those are different verdicts, and only the second one justifies archiving.

Three measured facts carry the decision:

1. **Ratio inversion.** 369 governance and support files against 140 knowledge files. 72% of the tracked repository exists to govern the remaining 28%. The framework outgrew the book.
2. **Enforcement decay.** The three blocking validators (`check_frontmatter`, `check_adr`, `check_broken_links`) report 130, 6, and 18 errors respectively and **all exit 0**. The repository has been "green" for months while violating its own rules.
3. **Structural entanglement.** The candidate successor lived untracked *inside* the predecessor and generated 45% of the frontmatter errors (58/130) and 72% of the broken links (13/18) that the predecessor reported against itself. It was separated from the repository immediately before the freeze.

None of these are reasons to delete the work. All three are reasons to stop maintaining it. The repository has been de facto dormant since June 2026 — 18 commits in June, **zero** in July, August, and September. Archiving does not end the project; it acknowledges an end that already happened, and converts a decaying asset into a stable, citable reference.

Decision: **complete freeze**. The repository is archived read-only at a permanent tag, with no content migrated into a successor, no handoff package, and no ongoing obligation. It becomes a closed legacy record to be consulted later for insight, not a component of anything that follows it.

This is the narrowest of the available decisions, and deliberately so. Maintaining a proportional archive costs the same attention that maintaining a live repository costs; the only sustainable end state for a project with no maintenance capacity is one where the artifact is preserved and nothing about it is expected to run.

## Introduction

### What the Project Was

The AI Engineering Book was a *Documentation-as-Code* hub for building production-grade AI systems using a hybrid LLM+SLM methodology. Its content was organized around a five-layer architecture — execution, model, prompts, orchestration, context — with real-world agent analysis in a sixth track. Content was authored as MyST Markdown paired with Jupyter notebooks via Jupytext, and published as a static site.

Its distinguishing thesis was that documentation should be governed like production code: versioned, validated, machine-readable, and lifecycle-managed. Architecture Decision Records were the *Primary Source of Truth*; frontmatter carried machine-readable identity, discovery, and lifecycle blocks so that agents could budget attention before reading a document.

That thesis was correct. The mechanisms built to enforce it were not proportionate to the artifact they governed, and this post-mortem is chiefly about that disproportion.

### Lifecycle and Timeline

| Period | Commits | Character of the work |
|---|---|---|
| 2025-10 | 28 | Bootstrap: layer taxonomy, first notebooks |
| 2025-11 | 41 | Content expansion, first tooling |
| 2025-12 | 124 | ADR system, frontmatter v1, first release cycle |
| 2026-01 | 176 | Peak: validation scripts, commit conventions, changelog generation |
| 2026-02 | 96 | Script suite formalization, evidence artifacts |
| 2026-03 | 62 | Hub-and-spoke config, ADR-26042/26045/26036 |
| 2026-04 | 82 | Frontmatter migration, JIT instructional feedback |
| 2026-05 | 56 | ADR governance consolidation begins |
| 2026-06 | 18 | Freeze declarations, frontmatter normalization |
| 2026-07 → 2026-09 | 0 | Dormant |
| 2026-10 | 3 | Gitignore and cleanup only |

The shape is diagnostic: the peak of activity is not content production but **tooling construction** (January–April 2026). The final three months of activity produced no new knowledge.

### Method of This Post-Mortem

All figures were measured on 2026-10-24 at commit `8b8c90b` on branch `release/3.2.0`, using the repository's own scripts and Git metadata. No numbers are estimated. Two things could not be verified and are therefore **not claimed**: the GitHub repository's visibility settings and the health of the deployed Pages site (the `gh` CLI returned HTTP 401 during analysis, and no build was executed).

## Technical Diagnosis

### What Worked

A post-mortem that only lists failures teaches nothing. The following survived contact with reality and remain the most durable parts of the archive:

- **56 ADRs** forming a durable, filterable decision record. Several are genuinely reusable methodology (Smallest Viable Architecture, Common Frontmatter Standard, Tool-Driven Instructional Feedback, Modular Knowledge Pull).
- **The frontmatter standard** (ADR-26042) with a discovery block and `token_size`: an early and correct answer to context-budget-aware documentation.
- **The prompt compiler** (`prepare_prompt.py`): recursive `_includes` resolution turning consultant prompts into thin manifests over shared blocks — 117 tests, correct architecture, no equivalent in most prompt repositories.
- **32 skills** in `.qwen/skills/`: hard-won, task-specific SOPs (validation deadlock recovery, YAML structural hardening, Jupytext dual-block frontmatter, pre-commit triage). This is the highest-value asset in the repository.
- **1379 passing tests in 2.5 seconds.** The tooling was real engineering, not aspiration.
- **Dual-format publishing** (MyST + Jupytext pairs) with CI verification of pair synchronization.

### Failure 1 — Ratio Inversion

Of 532 tracked files, 369 are governance or support (`.vadocs`, `tools`, `architecture`, `.qwen`, `misc`) and 140 are knowledge (`ai_system_layers`, `ai_agents` content, `0_intro`, `security`). The repository reached a state where **maintaining the rules cost more than producing the content** — 23 scripts, 1379 tests, 56 ADRs, 32 skills, and 52 plans (8 open, 44 shipped) to govern 140 documents.

This is the primary failure, and the others are its symptoms. A governance layer that is larger than its artifact cannot be sustained by one person writing in their spare time; it will either stop growing (dormancy) or start consuming the artifact (meta-work).

### Failure 2 — Enforcement Decay

`check_frontmatter`, `check_adr`, and `check_broken_links` currently report errors and exit 0. Every offending line is tagged `[LEGACY]`, meaning "reported, not blocking."

The origin of this mode is documented honestly in [R-26001](/architecture/evidence/retrospective/R-26001_validation_deadlock.md): a global blocking gate plus a large migration created a deadlock in which no commit could land. Commit-scoped validation was the correct emergency response. Its own lesson — *"technical debt visibility is not blocking"* — was correct. The failure was that the **emergency became the permanent state**. No exit criterion was ever defined for the legacy mode, so the "shame list" never had to shrink.

The deeper problem is that health was measured by **exit code**, not by **error count**. Once exit 0 became normal, 130 violations became invisible noise, and 1379 green tests created a false impression of system health — because those tests validated the governance layer, never the book.

### Failure 3 — Structural Entanglement

The candidate successor, `soviar_toolkit`, was developed **untracked inside** the repository it supersedes. Consequences:

- 25 MB of a different project, with its own `pyproject.toml`, tests, ADRs, and skills, sat in the working tree of a repository whose validators scanned it under the *wrong* schema. 58 of 130 frontmatter errors and 13 of 18 broken links originated there.
- Its ADR namespace (`26001`–`26009`) collides numerically with the legacy namespace (`26001`–`26059`). Any future attempt to fold its ADRs into this corpus would silently create duplicate identifiers.
- Links inside the successor were already broken by the nesting itself: `../ai_engineering_book` from `ai_engineering_book/soviar_toolkit/` resolves to a non-existent nested directory.

Two projects, one working tree, one validation schema. Neither could be reasoned about cleanly.

The freeze resolved this the only way that migrates nothing: the candidate was **moved out** to a sibling directory immediately before the write lock. It took its own files and nothing else, and the archive gained nothing from it. Separation is not salvage — the direction of travel is outward, and the archive is smaller afterwards, not larger.

### Failure 4 — Configuration Rot

`myst.yml` excluded `ai_system/**/*.md` — a directory renamed to `ai_system_layers/` long before. The replacement tree was never added to the exclusion list, so a site build would ingest the Jupytext `.md` duplicates of every notebook. The same file pinned `github:` to `lefthand67/ai_engineering_handbook` while both Git remotes point at `soviar-systems/ai_engineering_handbook`.

This rot survived precisely because the publishing pipeline stopped being exercised. Configuration is validated by use, not by inspection.

### Failure 5 — Freeze Accumulation

`misc/plan/freeze.md` accumulated four freeze declarations, last verified 2026-06-28. Re-verification on 2026-10-24 found two of its entries already stale: ADR-26057 and A-26026 were listed as uncommitted but had been committed, while the promised ADR-26058 was never created.

A freeze document that is not re-verified is not a status report; it is a fifth stale artifact. Freeze declarations must expire or be re-checked, otherwise they manufacture the same drift they were written to prevent.

### Failure 6 — Instruction Bloat

`AGENTS.md` is 22,478 bytes (approximately 5.6k tokens) and is symlinked as `QWEN.md`, `CLAUDE.md`, and `CONVENTIONS.md` — 89,912 bytes of on-disk instruction for every agent that opens the repository. ADR-26055 diagnosed the "token bomb" and the needle-in-a-haystack failure mode, proposed a constitution/operational split, and was never implemented. The freeze document records the conflict (symlinks preserve single-source maintenance but inflate every prompt) and no resolution.

## Root Cause

### The Self-Referential Loop

The failure mechanism is a loop, not a series of mistakes:

1. A new rule is written to prevent a class of error.
2. The rule creates new surface area for violations.
3. Violations require a validation script to detect.
4. The script requires a schema, and the schema requires migration.
5. Migration produces debt, which is recorded as a problem needing governance.
6. Governance produces a new rule. Return to step 1.

Knowledge grew linearly with writing effort; governance grew superlinearly with rule count. Nothing in the loop had a **sunset clause**, a **retirement budget**, or a **ratio cap**, so the loop had no equilibrium other than exhaustion.

### Why Nobody Noticed

Because the repository reported success. Tests passed. Hooks ran. Releases shipped. The one number that would have exposed the problem — violations against rules — was rendered non-blocking and therefore non-actionable. The system measured *whether the gate ran*, never *whether the gate held*.

There is a second-order cause worth naming: every rule felt locally justified. Each individual validation script, ADR, and skill solved a real problem. The failure was emergent, which is why it could not be caught by reviewing any single decision. It can only be caught by measuring the aggregate ratio, which no artifact in the repository did.

## Impact Assessment

### What Was Lost

- **Four months of momentum** (July–September 2026), and the context that went with it.
- **Roughly two months of effort** (roughly February–April 2026) that produced governance rather than knowledge — defensible at the time, disproportionate in retrospect.
- **The credibility of "green."** A future reader who trusts exit codes would conclude the repository was compliant; it was not.

### What Was Preserved

Everything material: 532 files, 19 MB of history, 15 releases, 56 ADRs, 32 skills, the compiled prompt architecture, the validation scripts, and a permanent tag. Archiving changes write access, not content. The published site remains available as a frozen reference.

## Corrective Actions

### The Decision

**Complete freeze**, decided on 2026-10-24 after three shapes were weighed:

| Shape | Verdict |
|---|---|
| **Complete freeze** — archive read-only, copy nothing forward, consult later | **Chosen.** Zero ongoing obligation; the archive is the reference. |
| *Salvage-then-freeze* — copy skills, standards, and scripts into the successor before freezing | Rejected. It converts an ending into a migration project, and migration is maintenance under another name. The material stays readable in the archive; copying it forward would have created a second corpus to keep in sync. |
| *Split content from governance* into a new repository | Rejected. The best long-term shape, but the most disruptive: it breaks permalinks and spends effort proportional to the debt being escaped. |

The deciding constraint was capacity, not architecture. A project that cannot maintain itself cannot maintain its own succession either. Archiving closes the loop; salvaging would have reopened it.

### What Was Extracted

Nothing was copied out. This is the deliberate part of the decision, and it is worth stating explicitly because it is the opposite of the usual archival instinct.

- The 32 skills, the 56 ADRs, the 23 scripts, the prompt compiler, and the 1379 tests remain **in the archive, in place, and readable**. Anyone — including this author — can open them at the permanent tag. That is the extraction mechanism.
- No files were copied into a successor, no identifiers were renumbered, no handoff package was assembled. A reference that is never copied cannot drift from its own source.
- **One directory left, and it was not archive material.** `soviar_toolkit/` — the candidate successor — was moved out immediately before the freeze, because a closed project cannot contain a live one. It was never part of this repository's content: it was a second project squatting in the first one's working tree, and it produced 58 of the 130 frontmatter errors and 13 of the 18 broken links this repository reported against itself. It took its own files and nothing else; the archive gained nothing from it.

The distinction between moving a squatter out and hand-picking material to carry forward is the whole difference between this decision and the rejected one. Separation shrinks the predecessor. Salvage loads it onto the successor.

The transferable content is the diagnosis in this document, not the tooling described by it. The tooling embodies a governance model this post-mortem argues against.

### The Freeze

- Commit the outstanding artifacts so that the record is complete before the write lock is applied.
- Move the candidate successor out of the working tree, so the archive does not ship with a live project inside it.
- Fast-forward `main` to the final state of `release/3.2.0` (0 divergent commits, 21 ahead) so the default branch reflects reality.
- Tag the final commit `archive-2026-10-24` as a permanent citation point.
- Publish an archive notice, a README banner, and a closing release-notes entry that state what the archive is good for and what remains broken inside it.
- Correct the two `myst.yml` defects so that a future build of the frozen site is faithful.
- Archive the GitHub repository read-only; leave the last verified Pages deployment serving.
- Do **not** repair the remaining 62 legacy violations (72 at separation; ten belonged to the three retrospectives, repaired only because they were being committed for the first time). Documented known-issues are honest; a last-minute cleanup would be the disproportion that caused the archive, repeated one final time.
- Do **not** continue maintenance of any kind after the lock: no dependency updates, no link fixes, no schema migrations.

## Preventive Measures

These are obligations for whatever succeeds this project, not reflections on it.

- **M1 — One blocking gate.** At most one validation gate may block a merge at a time. A gate that exits 0 on error is not a gate; delete it or fix it.
- **M2 — Ratio budget.** Governance and support artifacts must not exceed 30% of knowledge or product artifacts. This repository reached 72%. Measure the ratio, do not estimate it.
- **M3 — Sunset clause.** Every rule carries an owner and a review date. Unreviewed rules are deleted, not grandfathered.
- **M4 — No successor inside a predecessor.** A project being superseded must not contain the project superseding it. Separate working trees, separate schemas, separate namespaces. This archive broke that rule twice, and both breaks are visible in its own validation logs. The freeze could no longer prevent the mistake, only undo it: the nested candidate was moved out before the tag.
- **M5 — Exit code is the only health signal.** Never report "green" from test counts when validators exit non-zero, and never normalize exit 0 to make progress possible. If progress requires silencing the gate, the gate's scope is wrong.
- **M6 — Cite the archive, do not depend on it.** A frozen reference may be read, quoted, and linked. The moment new work imports its schema, its identifiers, or its scripts, the archive has acquired a dependency and can no longer stay frozen. Read it for insight; reimplement from understanding.
- **M7 — Freeze documents expire.** A freeze entry must be re-verified on a stated date or deleted. Stale status documents are worse than none.
- **M8 — Isolate inherited identifiers.** Reference corpora keep their original IDs in a separate namespace; never renumber into a live sequence. The ADR numbering in this repository was already colliding with a nested project's before the freeze.

## Final Mandate

The AI Engineering Book proved that documentation can be engineered, that prompts can be compiled, and that agents can be governed by machine-readable rules. It also proved that governance without a retirement mechanism consumes the thing it governs.

It closes as a reference, not as a platform. Read it to learn what worked, and read the validation logs to learn what a green pipeline can hide. Then build something with one gate that actually blocks, and spend the rest of the effort on the artifact.

## References

- [AI Engineering Book — README](/README.md)
- [Freeze state at sunset](/misc/plan/freeze.md)
- [Technical debt register](/misc/plan/techdebt.md)
- [R-26001 — Validation deadlock during frontmatter migration](/architecture/evidence/retrospective/R-26001_validation_deadlock.md)
- [R-26002 — Link validation false positives](/architecture/evidence/retrospective/R-26002_link_validation_false_positives.md)
- [R-26003 — Instruction drift](/architecture/evidence/retrospective/R-26003_instruction_drift.md)
- [ADR-26055 — Modular Knowledge Pull Architecture](/architecture/adr/adr_26055_modular_knowledge_pull_architecture.md)
- [ADR-26042 — Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md)
- [ADR-26045 — AI-Native Development, Code as Primary Documentation](/architecture/adr/adr_26045_ai_native_development_code_as_primary_documentation.md)
- [ADR-26050 — Tool-Driven Instructional Feedback for Agents](/architecture/adr/adr_26050_tool_driven_instructional_feedback_for_agents.md)
- [S-26025 — SkillOpt adoption analysis](/architecture/evidence/sources/S-26025_skillopt_adoption_analysis.md)
- [A-26026 — SkillOpt adoption comparative analysis](/architecture/evidence/analyses/A-26026_skillopt_adoption_comparative_analysis.md)
- [ADR-26057 — Adoption of SkillOpt for Empirical Agent Skill Optimization](/architecture/adr/adr_26057_adoption_of_skillopt_for_empirical_agent_skill_optimization.md)
- [Archive execution plan](/misc/plan/plan_20261024_archive_ai_engineering_book.md)
