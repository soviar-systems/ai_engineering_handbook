# Plan: Architecture Knowledge Base Taxonomy — Foundation (Batch 1 — Implemented)

## Context

Research and analytical artifacts that support architectural decisions had no formal home. The upstream research pipeline — dialogues and analyses that produce ADRs — was undocumented and unmanaged.

## What Was Implemented

### ADRs

- **ADR-26035** (`architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md`) — Architecture Knowledge Base Taxonomy. Defines the three-category taxonomy (Decisions / Evidence / Governance) aligned with ISO 42010, directory structure, namespace conventions, frontmatter schemas, source lifecycle, and validation approach.

- **ADR-26036** (`architecture/adr/adr_26036_config_file_location_and_naming_conventions.md`) — Config File Location and Naming Conventions. Establishes `<domain>.config.yaml` naming, co-location with governed artifacts, `pyproject.toml` pointer registry for discoverability, and parent-child config inheritance.

### Analysis

- **A-26001** (`architecture/evidence/analyses/A-26001_architecture_knowledge_base_taxonomy.md`) — Inaugural analysis document. Covers problem statement, research pipeline model, three approaches evaluated, taxonomy design with ISO 42010 alignment, rejected ideas (status-based subdirectories), key insights, and portability design.

### Config Hierarchy

- **`architecture/architecture.config.yaml`** — Parent config with shared architectural vocabulary (tags). Date format deferred to future repo-wide frontmatter standard.

- **`architecture/evidence/evidence.config.yaml`** — Evidence artifact validation spec. Inherits tags from parent via `parent_config` key. Defines naming patterns, artifact types (analysis, retrospective, source), required/optional fields, statuses, severity levels, required/optional sections, and lifecycle rules.

- **`pyproject.toml`** — Added `[tool.check-adr]` and `[tool.check-evidence]` config pointer registry entries.

### Directory Structure

```
architecture/
├── architecture.config.yaml          # NEW — shared tags
├── evidence/                         # NEW
│   ├── evidence.config.yaml          # NEW — evidence validation spec
│   ├── analyses/                     # NEW
│   │   └── A-26001_architecture_knowledge_base_taxonomy.md
│   ├── retrospective/                # NEW (empty, populated in PR 2)
│   └── sources/                      # NEW
│       └── README.md                 # Source lifecycle + git archaeology
```

## Key Design Decisions Made During Implementation

| Decision | Rationale |
|---|---|
| `R-` prefix (not `PM-`) for retrospectives | Matches directory name `retrospective/`; consistent with `A-` → `analyses/`, `S-` → `sources/` |
| `evidence.config.yaml` (not `research.config.yaml`) | Matches directory name `evidence/` |
| Tags in `architecture.config.yaml` (not `pyproject.toml`) | Tags are architectural data, not repo-wide config |
| `date_format` deferred | Repo-level metadata — belongs in future common frontmatter standard |
| Cross-reference validation deferred | Sources are deleted; git history suffices. Add when artifacts accumulate. |
| `parent_config` uses repo-root-relative path | Simpler than routing through pyproject.toml indirection |
| ADR-26036 as separate ADR (not merged into ADR-26035) | Config conventions are a separate, reusable decision |
| All file references as markdown links | Enables validation via `check_broken_links.py` |
