---
title: Archive Notice — AI Engineering Book
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Status, known issues, and disposition of an archived knowledge base on
  building production-grade AI systems.
tags:
- governance
- documentation
date: 2026-10-24
options:
  type: guide
  birth: 2026-10-24
  version: 1.0.0
  token_size: 1061
---
# Archive Notice

**Status:** archived and read-only since 2026-10-24.
**Lifetime:** 2025-10-19 → 2026-10-24 · 686 commits · 15 releases (final published: v3.1.0).
**Final tag:** `archive-2026-10-24`.
**Post-mortem:** [R-26004](/architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md).

## Why it was archived

The repository succeeded as a knowledge artifact and became unsustainable as a system. Its governance and support layer (369 tracked files) grew larger than the knowledge it governed (140 files); its validators reported errors while exiting 0; and a candidate successor was being built untracked inside it. Activity stopped in June 2026 and never resumed.

Archiving keeps everything readable while ending the maintenance obligation. No archive content was copied into a successor: the archive is the reference. The one directory that left — the candidate successor — left because a closed project cannot contain a live one, not because the archive had anything to hand on. The post-mortem contains the full diagnosis and eight preventive measures written for whatever comes next.

## How to use this archive

Read it for insight, then build independently. It is a closed record, not a dependency.

- **Methodology** — 56 ADRs on documentation engineering, prompt compilation, context budgeting, and AI-native development.
- **Reference implementations** — the prompt compiler (`tools/scripts/prepare_prompt.py`), the frontmatter validator, the broken-link checker, and 1379 tests that document their intended behaviour.
- **Debugging patterns** — the tracked skills under `.qwen/skills/` and the retrospectives under `architecture/evidence/retrospective/`.
- **A negative result worth reading** — how a well-intentioned governance system consumes the artifact it governs.

Do not import this repository's schema, ADR identifiers, or scripts into new work. Its ADR namespace was already colliding with a nested project's before the freeze, and the governance model it documents is the one the post-mortem argues against.

## Known issues, deliberately unrepaired

Do not read a green pipeline as compliance. At the moment of archiving:

- `check_frontmatter` reports 62 errors and **exits 0** (`[LEGACY]` mode).
- `check_adr` reports 6 errors and **exits 0**.
- `check_broken_links` reports 5 errors and **exits 0**.
- `tools/docs/jupyter_and_markdown/Untitled.md` contains malformed YAML frontmatter.
- ADR-26055 (Modular Knowledge Pull Architecture) was accepted and never implemented; `AGENTS.md` remains a 22 KB entry point symlinked four times.
- `misc/plan/freeze.md` contains stale entries: ADR-26057 and A-26026 are listed as uncommitted but were committed, and the promised ADR-26058 was never written.
- `release/3.2.0` was never released as v3.2.0; it was fast-forwarded into `main` as the archive baseline.

These are recorded rather than fixed. Fixing them would repeat the disproportion that caused the archive.

## What is not here

- `ai_agents/research/` — 4.2 GB of 15 external repositories across three registered directories, excluded from version control. The freeze left the working copy in place instead of reclaiming the disk, so it is still present on the archiving machine but is not part of this archive and will not appear in a clone. A local build renders it, which is why a local build reports errors that CI does not. Re-clonable from the upstream URLs registered in `.vadocs/inventory/manage_external_repos.json`.
- The candidate successor that was being built inside this directory (`soviar_toolkit/`, 61 source files). It was separated from the repository immediately before the freeze and continues outside it, in its own directory with its own history. It is not part of this archive and was not derived from it; this repository is not a dependency of it.
- Skill directories under `.qwen/skills/` that were never tracked (`.qwen/` is gitignored; 9 of 32 directories are present in history).
- Virtual environments, caches, and agent session logs.

## Licensing

Code is covered by `LICENSE-CODE`; documentation is covered by `LICENSE-DOCS`. Archived content remains available under those terms.
