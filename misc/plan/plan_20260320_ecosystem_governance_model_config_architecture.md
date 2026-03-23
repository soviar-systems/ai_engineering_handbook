# Plan: Ecosystem Governance Model + Config Architecture

## Context

This session discovered two unplanned architectural decisions:

1. **Ecosystem Standard vs Implementation Boundary** — ai_engineering_book is the "POSIX
   standard" defining what conforming implementations must do. vadocs is an implementation
   of those standards. Formalized in `architecture/manifesto.md` (Hub row, replacement test).

2. **Config file organization** — went through three iterations during brainstorming:
   scattered co-location (ADR-26036 original) → monolithic (rejected) → `.vadocs/` directory
   (sudoers.d scope-isolation pattern). A-26010 analysis identified the decision boundary.

## Steps

### 1. ~~Formalize POSIX standard / implementation boundary~~ DONE

- Updated `architecture/manifesto.md` line 43 — replacement test added to Hub row
- Originally planned as ADR-26045, but this is a principle (manifesto), not a decision (ADR)

### 2. ~~Delete wrong files~~ DONE (prior session)

- Deleted `architecture/adr/adr_26045_centralized_governance_configuration.md`
- Deleted `architecture/adr/adr_26045_ecosystem_standard_vs_implementation_boundary.md`
- Deleted `vadocs.config.yaml` at repo root

### 3. ~~Revise ADR-26036 in-place~~ DONE

- `.vadocs/` directory at project root (per ADR-26043)
- `conf.yaml` (shared) + `<doc_type>.conf.yaml` (scoped)
- sudoers.d pattern: scope isolation under reviewed composition
- Four alternatives: co-located, monolithic, pyproject.toml only, no convention

### 4. ~~Revise A-26010~~ DONE

- Three Linux config usage patterns: monolithic, runtime drop-in, scope-isolated
- sudoers.d: lexicographic ordering, intent is scope isolation not drop-in
- vadocs conclusion: scope-isolated pattern with shared config
- `produces: [ADR-26036]`

### 5. ~~Revise ADR-26042 section 6~~ DONE

- References ADR-26036 (not deleted ADR-26045)
- `author` → `authors` (MyST-native plural per mystmd.org/guide/frontmatter)
- Removed hardcoded field name lists from prose — tables are SSoT, prose references tables

### 6. ~~Create `.vadocs/conf.yaml`~~ DONE

- Flat field registry with myst_native flags (verified against mystmd.org spec)
- Block definitions: identity, discovery, lifecycle
- Type registry: 10 types with block composition + type-specific fields
- Tags with inline descriptions (no separate policy doc)
- Date format

### 7. Migrate scripts to load tags from `.vadocs/conf.yaml` — NEXT SESSION

This step involves code changes (TDD required) and should start in a fresh context.

- Remove `tags:` from `architecture/adr/adr_config.yaml` (keep as `adr.conf.yaml` candidate)
- Add `parent_config: ../../.vadocs/conf.yaml` to `adr_config.yaml`
- Update `tools/scripts/check_adr.py` to load tags from shared config
- Update `tools/scripts/check_evidence.py` similarly (currently loads from `architecture.config.yaml`)
- Assess `architecture/architecture.config.yaml` — likely fully absorbed into `.vadocs/conf.yaml`
- Rename `adr_config.yaml` → `adr.conf.yaml`, `evidence.config.yaml` → `evidence.conf.yaml`
- Update all `parent_config` pointers and `pyproject.toml` references
- Tests: `test_check_adr.py`, `test_check_evidence.py`

### 8. ~~Update memory~~ DONE

## Verification (for step 7)

- `uv run tools/scripts/check_adr.py --fix` passes (tags loaded from `.vadocs/conf.yaml`)
- `uv run pytest tools/tests/test_check_adr.py` passes
- `uv run tools/scripts/check_evidence.py` passes (no regression)
- `uv run pytest tools/tests/test_check_evidence.py` passes
- `uv run tools/scripts/check_broken_links.py` passes (no stale links)
