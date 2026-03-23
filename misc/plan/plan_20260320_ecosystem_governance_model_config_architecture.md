# Plan: Ecosystem Governance Model + Config Architecture

## Context

This session discovered two unplanned architectural decisions:

1. **Ecosystem Standard vs Implementation Boundary** — ai_engineering_book is the "POSIX
   standard" defining what conforming implementations must do. vadocs is an implementation
   of those standards. This distinction determines where ADRs live and prevents coupling
   ecosystem standards to specific tool implementations.

2. **Config file organization** — went through three iterations during brainstorming:
   scattered co-location (ADR-26036 original) → monolithic (ADR-26045, created and to be
   deleted) → `.vadocs/` directory (sudoers.d pattern). A-26010 analysis identified the
   decision boundary; needs refinement with the sudoers.d scope-isolation case.

## Steps

### 1. Write ADR-26045: Ecosystem Standard vs Implementation Boundary

- New ADR: `architecture/adr/adr_26045_ecosystem_standard_vs_implementation_boundary.md`
- Core decision:
  - Hub repo (ai_engineering_book) defines standards — the "what" and "why"
  - Implementation repos (vadocs, mentor_generator) implement — the "how"
  - The test: if the implementing tool were replaced, would this decision still apply?
    Yes → hub ADR. No → implementation repo ADR.
  - Implementation repos reference hub standards via ecosystem ADR index
- References: ADR-26043 (package boundary), ADR-26022 (hub publishing)
- Context: emerged from config ADR discussion — needed to determine where config
  conventions live before writing them

### 2. Delete the wrong ADR-26045 (centralized config)

- Delete: `architecture/adr/adr_26045_centralized_governance_configuration.md`
- Delete: `vadocs.config.yaml` at repo root (created earlier, wrong approach)

### 3. Revert ADR-26036 rejection, revise in-place

- File: `architecture/adr/adr_26036_config_file_location_and_naming_conventions.md`
- Revert `status: rejected` → `status: proposed`
- Remove `## Rejection Rationale` section
- Revise Decision: `.vadocs/` directory at repo root
  - `.vadocs/conf.yaml` — hub (shared vocabulary, field registry, blocks, types)
  - `.vadocs/<domain>.conf.yaml` — domain operational rules
  - Registered in `pyproject.toml [tool.vadocs]`
- Reference ADR-26045 (new one) for why config conventions live in hub, not vadocs

### 4. Revise A-26010

- File: `architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md`
- Add sudoers.d as third pattern: scope isolation under reviewed composition
- Refine conclusion: centralized directory with hub file (not purely monolithic)
- Update `produces` field: ADR-26036 revision (not deleted ADR-26045)

### 5. Revert ADR-26042 section 6 edits

- File: `architecture/adr/adr_26042_common_frontmatter_standard.md`
- Update section 6: reference revised ADR-26036 (not deleted ADR-26045)
- Describe `.vadocs/conf.yaml` as the hub config location

### 6. Create `.vadocs/conf.yaml` (hub config)

- Flat field registry with full metadata (key, maintenance, required, description)
- Block definitions referencing field names
- Type registry (blocks + type-specific fields referencing field registry)
- Shared tags vocabulary (migrated from `adr_config.yaml`)
- Date format

### 7. Migrate tags from `adr_config.yaml`

- Remove `tags:` section from `architecture/adr/adr_config.yaml`
- Add `parent_config` pointer to `.vadocs/conf.yaml`
- Update `tools/scripts/check_adr.py` to load tags from hub config
- Assess `architecture/architecture.config.yaml` — likely absorbed into hub

### 8. Update memory

- ADR-26045 = Ecosystem Standard vs Implementation Boundary (not config)
- Config pattern: `.vadocs/` directory (ADR-26036 revised)
- Ephemeral file lifecycle shifts to next available number

## Verification

- `uv run tools/scripts/check_adr.py --fix` passes (tags loaded from hub)
- `uv run pytest tools/tests/test_check_adr.py` passes
- `uv run tools/scripts/check_evidence.py` passes (no regression)
- `uv run tools/scripts/check_broken_links.py` passes (no stale links)

## Critical files

- `architecture/adr/adr_26045_ecosystem_standard_vs_implementation_boundary.md` (create)
- `architecture/adr/adr_26045_centralized_governance_configuration.md` (delete)
- `architecture/adr/adr_26036_config_file_location_and_naming_conventions.md` (revert + revise)
- `architecture/adr/adr_26042_common_frontmatter_standard.md` (revise section 6)
- `architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md` (refine)
- `vadocs.config.yaml` (delete)
- `.vadocs/conf.yaml` (create)
- `architecture/adr/adr_config.yaml` (migrate tags out)
- `architecture/architecture.config.yaml` (assess absorption)
- `tools/scripts/check_adr.py` (update tag loading)
- `tools/tests/test_check_adr.py` (update tests)
