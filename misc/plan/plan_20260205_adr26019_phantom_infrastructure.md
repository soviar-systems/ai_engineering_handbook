# Follow-up: ADR-26019 Describes Phantom Infrastructure

## Finding

ADR-26019 ("Mirroring YAML Metadata to Document Body for Human Verification") specifies an HTML comment anchor mechanism (`<!-- meta -->...<!-- /meta -->`) for a "Reflection Block" synced from YAML via pre-commit hooks. **This mechanism was never implemented.** Zero files in the repo contain these anchors.

## What Actually Exists

Every content article uses a manual, pre-ADR pattern:

```
+++

---

Owner: Vadim Rudakov
Version: 0.2.3
Birth: 2025-10-19
Last Modified: 2026-02-01

---

+++
```

This is MyST `+++` cell breaks wrapping hand-written prose lines between `---` thematic breaks. There is:
- No YAML frontmatter for `owner`/`version`/`birth` fields (only the Jupytext header exists)
- No HTML comment anchors
- No pre-commit hook syncing metadata from YAML to body
- No automated validation of metadata consistency

## Two Conflated Concerns in ADR-26019

1. **The goal is valid**: Human-readable metadata mirroring from a machine-readable source (YAML) prevents "Metadata Drift" during peer review. This is a real problem.

2. **The solution is phantom**: HTML comment anchors + pre-commit hook was specified but never built. The articles don't even have the YAML source fields that would feed the mirror.

## Dependency Chain

ADR-26018 (YAML frontmatter mandate) is the prerequisite — content articles need actual YAML `owner`/`version`/`status` fields before any mirroring can happen. ADR-26019 should be sequenced *after* ADR-26018 is implemented, not in parallel.

## Proposed Action

1. **Supersede ADR-26019** with a new ADR that:
   - Acknowledges the valid goal (human-readable metadata in non-rendering environments)
   - Drops the HTML anchor mechanism (never validated, adds parsing complexity)
   - Proposes a simpler approach: the existing `---` / prose / `---` pattern IS the reflection block — just automate its generation from YAML frontmatter via pre-commit
   - Explicitly sequences after ADR-26018 implementation

2. **Alternative**: Mark ADR-26019 as `deprecated` and fold the mirroring concern into ADR-26018's implementation plan, since they're tightly coupled.

## Context

Discovered during execution of the content lifecycle plan (ADR-26021). The `llm_usage_patterns.md` reference in ADR-26019 line 36 was the entry point — it cited a now-deleted file as an example of `---` thematic break collisions, which is the entire justification for HTML anchors.
