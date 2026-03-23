---
id: A-26010
title: "Config File Distribution Patterns — Monolithic, Drop-in, and Scope-Isolated"
author: Vadim Rudakov, rudakow.wadim@gmail.com
description: "Analysis of three config distribution patterns grounded in Linux ecosystem evidence. Decision boundary: integration model (runtime vs reviewed composition) and scope isolation needs. Identifies sudoers.d scope-isolated directory as the pattern for vadocs."
tags: [architecture, governance]
date: 2026-03-20
status: active
sources: []
produces: [ADR-26036]
options:
  type: analysis
  birth: 2026-03-19
  version: 1.0.0
---

# A-26010: Config File Distribution Patterns — Monolithic, Drop-in, and Scope-Isolated

+++

## Problem Statement

+++

A documentation governance tool (vadocs) needs a configuration strategy that works across
multiple projects in an ecosystem. The tool governs several orthogonal concerns — ADR
validation, evidence artifact lifecycle, frontmatter standards, ephemeral file cleanup — each
with its own configuration. Three patterns exist in the Linux ecosystem for organizing
such multi-concern configs: monolithic files, runtime drop-in directories, and scope-isolated
directories.

The existing approach ({term}`ADR-26036`, proposed) established a "co-locate config with
artifacts" rule: `adr_config.yaml` lives next to ADRs, `evidence.config.yaml` next to evidence
files. This works for single-domain configs but breaks down for cross-cutting concerns that
span multiple directories (ephemeral file lifecycle, frontmatter hub). The question: should the
tool centralize into one config file, split into a config directory, or preserve co-location?

+++

## Key Insights

+++

### Linux config files fall into three usage patterns

**Monolithic configs** — a single file with sections or directives covering all aspects of a
service:

- `/etc/sshd_config` — one file governs all SSH daemon behavior
- `/etc/fstab` — one file defines all filesystem mounts
- `/etc/postgresql/postgresql.conf` — one file controls all Postgres settings

**Runtime drop-in directories** — a directory where packages or plugins drop files that take
effect without central review:

- `/etc/logrotate.d/` — each installed package drops its own rotation config
- `/etc/udev/rules.d/` — device rules from multiple hardware drivers coexist without mutual
  awareness
- `/etc/fapolicyd/rules.d/` — numbered rule files where evaluation order is the primary
  semantic (`10-languages.rules`, `20-dracut.rules`)

**Scope-isolated directories** — a directory where each file governs a different concern,
all under the same review process:

- `/etc/sudoers.d/` — each file adds independent sudo rules for a different scope (user,
  group, application). All files go through the same administrative review. The directory
  exists not for runtime composition but for organizational clarity: each scope is
  independently readable and testable without risking edits to unrelated rules
- `/etc/rsyslog.d/` — each config file governs logging for a different facility or
  application. An administrator reviews all changes; the directory prevents a growing
  monolith where editing mail logging risks breaking kernel logging

+++

### The decision boundary is the integration model and scope isolation needs

The initial hypothesis — "single author → monolithic, multiple authors → directory" — is
incorrect. Many monolithic configs have multiple contributors (anyone can edit `sshd_config`),
and many directory configs are maintained by one team.

Two dimensions determine which pattern fits:

1. **Integration model** — how changes reach the running system:

| Integration model | Mechanism |
|---|---|
| **Runtime composition** — changes take effect without central review | Drop a file → service picks it up on reload/restart |
| **Reviewed composition** — changes require central approval before taking effect | Edit → review → merge → deploy |

2. **Scope isolation** — whether independent concerns benefit from file-level separation
   regardless of the integration model.

The runtime drop-in pattern emerged to support **package-driven composition**: when `nginx` is
installed, it drops `/etc/logrotate.d/nginx` automatically. No human reviews this individual
file — the package manager is the integration mechanism. The fapolicyd case extends this: it
uses numbered files (`10-languages.rules`, `20-dracut.rules`) because **rule evaluation order
is the primary semantic**.

The scope-isolated pattern serves a different purpose: `sudoers.d` files all go through the
same administrative review. The directory exists to separate concerns by scope — each file
governs a different user, group, or application. Like drop-in directories, files are read in
lexicographic order and later rules can override earlier ones (e.g., a broad password
requirement in `20-admin` can dismiss a `NOPASSWD` grant in `10-app`). The mechanism is
shared; what differs is **intent** — scope-isolated directories exist so an administrator can
organize related concerns into independently manageable files, not so that unrelated packages
can contribute without mutual awareness.

+++

### When each pattern fits

**Monolithic** — justified when all changes are reviewed, sections reference each other, and
atomic distribution matters (one file = one governance state):

- `/etc/sshd_config` — all SSH behavior in one place, one file to audit
- `/etc/postgresql/postgresql.conf` — settings cross-reference each other

**Runtime drop-in** — justified when unrelated packages or plugins contribute config without
mutual awareness, and changes take effect without central review:

- `/etc/logrotate.d/` — `nginx` package drops its own rotation config at install time
- `/etc/udev/rules.d/` — hardware drivers contribute rules independently

**Scope-isolated** — justified when an administrator wants to organize reviewed concerns into
independently manageable files. Changes still go through central review; the directory prevents
a growing monolith where editing one concern risks breaking another:

- `/etc/sudoers.d/` — each file governs a different scope (user, group, application)
- `/etc/rsyslog.d/` — each file governs logging for a different facility

+++

### Application to vadocs

vadocs is a documentation governance tool installed across multiple ecosystem projects. Its
configuration governs ADR validation, evidence artifacts, frontmatter standards, and ephemeral
file lifecycle.

| Property | vadocs ecosystem | Pattern implication |
|---|---|---|
| Change integration | PR-gated (reviewed composition) | Eliminates runtime drop-in |
| Scope isolation need | Each doc type has independent validation rules | Favors scope-isolated directory |
| Cross-cutting concerns | Shared tags, field registry, date format used by all doc types | Needs a shared config file alongside scoped files |
| Multiple doc type owners | Different people responsible for different doc types | Favors scope isolation — editing ADR rules should not risk evidence rules |
| Runtime drop-in plugins | Not supported — no third-party plugin model | Eliminates runtime drop-in |

vadocs fits the scope-isolated pattern: reviewed composition with independent concerns per doc
type. A shared config (`conf.yaml`) provides the cross-cutting vocabulary; doc type configs
(`<doc_type>.conf.yaml`) hold operational rules for their scope. This is the `sudoers.d`
model — each file governs a different concern, all under the same review process.

+++

## References

+++

### Internal

- {term}`ADR-26036` — config file location and naming conventions (informed by this analysis)
- {term}`ADR-26029` — pyproject.toml as tool configuration hub
- {term}`ADR-26042` — common frontmatter standard
- {term}`ADR-26043` — vadocs package boundary
- [A-26005: Document Type Interfaces and Unified Validation](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) — VFS model, runtime doc types

### External

- `/etc/sshd_config` — monolithic config for single-service governance
- `/etc/logrotate.d/` — package-driven runtime drop-in pattern
- `/etc/fapolicyd/rules.d/` — numbered rule files, lexicographic ordering
- `/etc/sudoers.d/` — scope-isolated directory under administrative review
- `/etc/rsyslog.d/` — scope-isolated logging config per facility
