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

### 7. Migrate configs to JSON, establish `.vadocs/` subdirectory structure, migrate scripts — IN PROGRESS

This step involves config format migration, directory restructuring, and code changes (TDD required).

**7a. YAML → JSON migration (A-26013, ADR-26054):**

Brainstorming (2026-03-23) identified that YAML governance configs are hitting their
limits: no native schema validation, ambiguous parsing, custom format invention needed
for complex fields (authors, tags). JSON + JSON Schema is the standard solution:
- `json` module is Python stdlib (zero dependencies vs PyYAML)
- JSON Schema validates both config files and the frontmatter they govern
- Field format definitions (authors, dates, statuses) become standard JSON Schema
- Descriptions live in the schema itself — comments unnecessary

Analysis: A-26013 (YAML → JSON config format migration)
ADR: ADR-26054 (JSON as Governance Config Format)

- Convert `.vadocs/conf.yaml` → `.vadocs/conf.json`
- Create `.vadocs/conf.schema.json` defining the hub config structure
- Convert spoke configs to JSON during move (7b)
- Update all scripts from `yaml.safe_load` → `json.load` for config loading
- Note: document frontmatter stays YAML (embedded in markdown) — only `.vadocs/` configs migrate

**7b. Establish `.vadocs/` subdirectory structure:**

Brainstorming (2026-03-23) concluded that `.vadocs/` must use subdirectories by concern,
anticipating vadocs package extraction (Phase 1.3). Flat layout rejected — mixes governance
vocabulary with operational rules and won't scale to plugins.

Target layout:
```
.vadocs/
  conf.json                  # hub — shared vocabulary (fields, blocks, types, tags)
  conf.schema.json           # JSON Schema for hub config
  types/
    adr.conf.json            # spoke — ADR operational rules
    evidence.conf.json       # spoke — evidence operational rules
  validation/
    excludes.conf.json       # operational — paths.py content (separate task)
```

- Create `.vadocs/types/` directory
- Move `adr_config.yaml` → `.vadocs/types/adr.conf.json` (convert to JSON)
- Move `evidence.config.yaml` → `.vadocs/types/evidence.conf.json` (convert to JSON)
- Delete `architecture/architecture.config.yaml` (fully absorbed into `conf.json`)
- Delete `.vadocs/conf.yaml` (replaced by `conf.json`)
- ADR-26036 revision needed: update from flat YAML to subdirectory JSON structure

**7c. Config content migration:**

- Remove `tags:` from adr spoke config (now in `conf.json`)
- Remove `date_format:` from both spoke configs (now in `conf.json`)
- Add `parent_config: .vadocs/conf.json` to both spoke configs
- Define `authors` format in JSON Schema: array of `{name, email}` objects

**7d. Script migration (TDD):**

- Update `tools/scripts/check_adr.py`: `yaml.safe_load` → `json.load`, load tags from
  shared config via parent_config (tags in hub are dict with descriptions → extract keys)
- Update `tools/scripts/check_evidence.py` similarly
- Update `pyproject.toml` pointers: `.vadocs/types/adr.conf.json`, `.vadocs/types/evidence.conf.json`
- Update `.pre-commit-config.yaml` file patterns
- Tests: `test_check_adr.py`, `test_check_evidence.py`

**7e. Documentation and ADR updates:**

- Write ADR-26054 (JSON as Governance Config Format)
- Revise ADR-26036 (update from flat YAML to subdirectory JSON)
- Update `adr_template.md` comment (config path)
- Update `tools/docs/scripts_instructions/` for both scripts
- Update `CLAUDE.md` config hierarchy description

**Deferred to separate task:**

- Migrate `paths.py` → `.vadocs/validation/excludes.conf.json`

### 8. ~~Update memory~~ DONE

## Verification (for step 7)

- `uv run tools/scripts/check_adr.py --fix` passes (tags loaded from `.vadocs/conf.json`)
- `uv run pytest tools/tests/test_check_adr.py` passes
- `uv run tools/scripts/check_evidence.py` passes (no regression)
- `uv run pytest tools/tests/test_check_evidence.py` passes
- `uv run tools/scripts/check_broken_links.py` passes (no stale links)
- `.vadocs/conf.json` validates against `.vadocs/conf.schema.json`
