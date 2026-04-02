# .vadocs/ — Governance Configuration Directory

Configuration hub for document validation across the ecosystem.
Designed for extraction into the vadocs standalone package.

## Quick Start

- **Entry point**: `pyproject.toml [tool.vadocs].config_dir` points here. Scripts discover configs via `paths.get_config_path()`.
- **Add a tag**: add to `conf.json` → `tags` (alphabetical). The description defines scope.
- **Add a document type**: add to `conf.json` → `types`, create `types/<doc_type>.conf.json`.
- **Child configs** inherit from `conf.json` via `parent_config` — they add constraints, never remove.

## Directory Layout

```
conf.json              Hub — shared vocabulary (fields, blocks, types, tags)
conf.schema.json       JSON Schema for hub config and frontmatter validation
types/                 Child configs (one per governed document type)
validation/            Operational rules for validation scripts
```

## Why JSON?

Governance configs use JSON + JSON Schema (not YAML). Rationale in
[A-26013](/architecture/evidence/analyses/A-26013_json_as_governance_config_format.md).
Document frontmatter stays YAML (embedded in Markdown, parsed by MyST).

## Design Decisions

- [ADR-26036](/architecture/adr/adr_26036_config_file_location_and_naming_conventions.md) — `.vadocs/` directory, scope-isolated pattern
- [ADR-26042](/architecture/adr/adr_26042_common_frontmatter_standard.md) — Composable frontmatter blocks, type registry
- [A-26010](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md) — Why scope-isolated over monolithic or drop-in
- ADR-26054 (pending) — JSON as governance config format
