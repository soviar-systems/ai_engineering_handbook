---
id: 26036
title: "Config File Location and Naming Conventions"
date: 2026-02-27
status: proposed
superseded_by: null
tags: [governance, architecture]
---

# ADR-26036: Config File Location and Naming Conventions

## Date
2026-02-27

## Status
proposed

## Context

As the repository's tooling grows, validation scripts need configuration files. Without a convention for where configs live and how they're named, engineers face three problems:

1. **Discoverability:** Where is the config for a given script? Which directory? What filename?
2. **Naming inconsistency:** No pattern exists to predict a config file's name from its script or domain.
3. **Duplication:** Shared fields (e.g., tags) get copied between configs because there's no inheritance mechanism.

{term}`ADR-26029` established [pyproject.toml](/pyproject.toml) as the tool configuration hub for configs expressible in TOML. But complex domain configs — deeply nested structures, conditional rules, correction mappings — need YAML. ADR-26029 does not specify where those YAML files live, how to name them, or how scripts discover them.

## Decision

Establish a three-layer config convention: naming, location, and discoverability. Plus a parent-child inheritance mechanism for shared fields.

### 1. Naming Convention

Config files follow the pattern: **`<domain>.config.yaml`**

- **Dot-separated namespace:** `<domain>.config` reads as "the config for domain"
- **`.yaml` extension:** The [official extension](https://yaml.org/faq.html) recommended by yaml.org
- **Lowercase domain:** matches the directory or artifact type it governs

Examples from our ecosystem: `adr.config.yaml`, `evidence.config.yaml`, `architecture.config.yaml`, `.mentor.generator.config.yaml`.

### 2. Location Convention

**Config files live next to the artifacts they govern.**

The rule: if you're in a directory with validated artifacts, look for a `*.config.yaml`. The config travels with its artifacts if directories are renamed or moved.

### 3. Discoverability via pyproject.toml Pointer Registry

Every YAML config consumed by a script is registered in [pyproject.toml](/pyproject.toml) under its script's tool section:

```toml
[tool.check-adr]
config = "architecture/adr/adr.config.yaml"

[tool.check-evidence]
config = "architecture/evidence/evidence.config.yaml"
```

Scripts read their config path from [pyproject.toml](/pyproject.toml) via `tomllib`, not from hardcoded constants. When directories rename, only the [pyproject.toml](/pyproject.toml) pointers change.

### 4. Parent-Child Config Inheritance

Configs form a hierarchy. Shared fields are defined once in a parent config; child configs inherit them.

```
architecture/
├── architecture.config.yaml       ← parent (shared tags)
├── adr/adr.config.yaml            ← child (ADR-specific rules)
└── evidence/evidence.config.yaml  ← child (evidence-specific rules)
```

Child configs declare their parent via a repo-root-relative path:

```yaml
# evidence.config.yaml
parent_config: "architecture/architecture.config.yaml"
```

The validation script resolves this at runtime:
1. Read its own config path from [pyproject.toml](/pyproject.toml)
2. Read the `parent_config` path from its config
3. Load shared fields (e.g., tags) from the parent
4. Merge with its own domain-specific fields

One source of truth for tags. Adding a new tag to the parent config automatically applies to all child configs.

### 5. Complexity Threshold

When to use `pyproject.toml` inline vs. a separate YAML file:

- **Inline in pyproject.toml:** shallow nesting, few lines, no conditional logic
- **Separate YAML with pyproject.toml pointer:** deeply nested structures, conditional rules, domain-specific complexity

## Consequences

### Positive
- **Predictable discovery:** Any engineer can find any config via [pyproject.toml](/pyproject.toml) or by looking next to the governed artifacts
- **No duplication:** Shared fields have one source of truth via parent config inheritance
- **Rename-safe:** Directory renames only require updating [pyproject.toml](/pyproject.toml) pointers
- **Consistent naming:** `<domain>.config.yaml` is predictable across the repository

### Negative / Risks
- **Migration overhead:** Renaming existing [adr_config.yaml](/architecture/adr/adr_config.yaml) → `adr.config.yaml` requires script and test updates. **Mitigation:** Deferred to a future PR alongside other path changes.
- **Runtime resolution cost:** Scripts must load [pyproject.toml](/pyproject.toml), resolve pointers, and merge shared fields. **Mitigation:** Extract a shared `load_config()` utility that all validation scripts use.
- **Two places to look:** Config content is in YAML, pointers are in [pyproject.toml](/pyproject.toml). **Mitigation:** The convention is simple: "[pyproject.toml](/pyproject.toml) tells you where, YAML tells you what."

## Alternatives

- **Option A: Everything in pyproject.toml.** Inline all config as TOML tables. **Rejection Reason:** TOML is painful for deeply nested structures. Domain-specific validation configs with conditional rules, status corrections, and section mappings become unreadable in flat TOML format.

- **Option B: Central config directory.** Move all configs to a single `config/` directory. **Rejection Reason:** Separates config from the artifacts it governs. Engineers navigating artifact directories would have to look elsewhere for validation rules. Co-location is more intuitive.

- **Option C: No convention.** Let each script hardcode its own config location. **Rejection Reason:** Does not scale. Without a naming or location pattern, every new config becomes a discovery problem.

## References
- {term}`ADR-26029` — pyproject.toml as Tool Configuration Hub
- {term}`ADR-26035` — Architecture Knowledge Base Taxonomy
- [YAML FAQ — Recommended filename extension](https://yaml.org/faq.html)
- [Script instruction docs](/tools/docs/scripts_instructions/README.md)

## Participants
1. Vadim Rudakov
2. Claude (AI Systems Architect)
