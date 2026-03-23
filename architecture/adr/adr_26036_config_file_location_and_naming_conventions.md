---
id: 26036
title: "Config File Location and Naming Conventions"
date: 2026-02-27
status: proposed
superseded_by: null
tags: [governance, architecture]
---

<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26036: Config File Location and Naming Conventions

## Date
2026-02-27

## Status
proposed

## Context

As the repository's tooling grows, validation scripts need configuration files. Without a
convention for where configs live and how they're named, engineers face three problems:

1. **Discoverability:** Where is the config for a given script? Which directory? What filename?
2. **Naming inconsistency:** No pattern exists to predict a config file's name from its script
   or validation scope.
3. **Duplication:** Shared fields (e.g., tags) get copied between configs because there's no
   inheritance mechanism.

{term}`ADR-26029` established `pyproject.toml` as the tool configuration hub for configs
expressible in TOML. But complex validation configs — deeply nested structures, conditional
rules, correction mappings — need YAML. {term}`ADR-26029` does not specify where those YAML
files live, how to name them, or how scripts discover them.

## Decision

Adopt a **centralized config directory** at the project root with scope-isolated files per
concern.

### 1. Config Directory

All governance configs live in a single directory at the project root. The directory name is
determined by the governance package (currently `.vadocs/` per {term}`ADR-26043`). Any engineer
or agent knows where to look without scanning the directory tree.

### 2. Shared and Scoped Files

The directory contains two kinds of config files:

- **Shared config** (`conf.yaml`) — cross-cutting definitions used by all validation scripts:
  field registry, block composition, type registry, tag vocabulary, date format.
- **Doc type configs** (`<doc_type>.conf.yaml`) — operational rules for one doc type: ADR
  section structure and status transitions, evidence artifact naming and lifecycle, ephemeral
  file thresholds. Each doc type config declares a `parent_config` pointer to the shared config
  to inherit common vocabulary.

Doc type configs do not reference each other — only the shared config. This is the `sudoers.d`
pattern: each file governs a different scope, files are independently testable, the shared
config provides the common foundation.

### 3. Naming Convention

Config files follow the pattern `<doc_type>.conf.yaml` where the doc type matches the validation
concern (e.g., `adr`, `evidence`, `ephemeral`). The shared config uses `conf.yaml`. The
`.yaml` extension follows the [yaml.org recommendation](https://yaml.org/faq.html).

## Consequences

### Positive

- **Single discovery location**: all governance config in one directory — no scanning
  artifact directories to find scattered configs.
- **No duplication**: shared vocabulary defined once in the shared config, inherited by doc
  type configs via `parent_config`.
- **Scope isolation**: each doc type file is independently readable and testable. Adding a
  new governance concern means adding a file, not editing a growing monolith.
- **Cross-cutting concerns have a home**: frontmatter schema and ephemeral lifecycle rules
  live in the shared config, not awkwardly co-located with one arbitrary artifact directory.
- **Consistent naming**: `<doc_type>.conf.yaml` is predictable across the ecosystem.

### Negative / Risks

- **Migration overhead**: existing configs must move to the new directory and adopt the naming
  convention. **Mitigation:** one-time cost; a shared `load_config()` utility in vadocs
  `core/` ({term}`ADR-26043`) absorbs the resolution logic.
- **Directory name is tool-coupled**: the directory name (e.g., `.vadocs/`) ties the config
  location to the current governance tool. **Mitigation:** per the manifesto's replacement
  test, the directory pattern is the standard; the name is an implementation detail that
  changes with the tool.

## Alternatives

- **Co-located configs**: Each config lives next to its governed artifacts. **Rejected:**
  creates maintenance overhead — configs scattered across the directory tree with no single
  place to see the governance state. Volatile under refactoring: renaming or restructuring
  artifact directories forces config moves. Fails entirely for cross-cutting concerns
  (frontmatter, ephemeral) that span multiple directories.

- **Single monolithic config file**: All concerns in one YAML file with sections. **Rejected:**
  ADR operational rules alone are 170 lines; a combined file exceeds 500 lines and becomes
  difficult to navigate. Scope isolation is lost — editing ephemeral rules risks merge
  conflicts with ADR rules. See
  [A-26010](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md).

- **Everything in pyproject.toml**: Inline all config as TOML tables. **Rejected:**
  {term}`ADR-26029` established that complex validation configs need YAML. TOML is painful for
  deeply nested structures with conditional rules and correction mappings.

- **No convention**: Let each script hardcode its own config location. **Rejected:** does not
  scale. Without a naming or location pattern, every new config becomes a discovery problem.

## References

- [A-26010: Config File Distribution Patterns](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md) — monolithic vs directory analysis, sudoers.d scope-isolation pattern
- {term}`ADR-26029` — pyproject.toml as Tool Configuration Hub
- {term}`ADR-26043` — vadocs package boundary (governance tool that implements this convention)
- {term}`ADR-26042` — common frontmatter standard (hub config's primary consumer)
- {term}`ADR-26035` — Architecture Knowledge Base Taxonomy
- [YAML FAQ — Recommended filename extension](https://yaml.org/faq.html)

## Participants
1. Vadim Rudakov
2. Claude Opus 4.6 (AI Engineering Advisor)
