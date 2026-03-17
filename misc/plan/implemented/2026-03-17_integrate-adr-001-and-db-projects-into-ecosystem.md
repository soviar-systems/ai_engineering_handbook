# Plan: Integrate adr_001 and DB Projects into soviar-systems Ecosystem

## Status

In progress. ADR writing deferred to roadmap plan section 1.12 (numbers 26049–26053).
Remaining work: CLAUDE.md refactoring only (Steps 5–8 below).

---

## What Was Done

| Item | Status |
|---|---|
| S-26012 created from adr_001 content | ✅ done |
| `architecture_decision_workflow_guide.md` — Rule 4 added (capability vs tool) | ✅ done |
| DB ADRs 26049–26053 scoped and added to roadmap plan section 1.12 | ✅ done |
| `adr_26044_database_access_conventions.md` (conflicting number) | ✅ deleted |

## What Was Deferred

ADR writing for 26049 (context distribution), 26050 (safe DB communication), 26051
(schema namespacing), 26052 (logging), 26053 (secrets management) moved to roadmap plan
section 1.12. Numbers 26044–26048 were already reserved for other ADRs in that plan.

---

## Remaining Steps

The ADR-26049 principle is clear enough to act on without the ADR being formally written.
Execute the CLAUDE.md refactoring now, referencing section 1.12 of the roadmap for content.

### Step 5: Delete adr_001 from soviar-systems root

Delete `soviar-systems/adr_001_database_ecosystem_design_principles.md`.
Content is preserved as S-26012.

### Step 6: Refactor `soviar-systems/CLAUDE.md`

**Add at top:**
```
<!-- Local convenience layer — NOT authoritative per ADR-26049 (planned).
     Each repo's CLAUDE.md is the canonical source. -->
```

**Replace the Projects table** (current one lists old `databases/` projects):

| Directory | Type | Description |
|---|---|---|
| `ai_engineering_book/` | Hub | Ecosystem ADRs, documentation tooling |
| `postgres_connector/` | DB library | Shared PostgreSQL access layer |
| `un_votes/` | DB project | UN General Assembly vote records |
| `vadocs/` | Tool | Documentation validation engine |
| `mentor_generator/` | AI tool | LLM-based mentor generation |
| `research/` | Research | Volatile experimental projects |

**Add ecosystem architecture pointer:**
```markdown
## Ecosystem Architecture

Ecosystem-wide ADRs live in `ai_engineering_book/architecture/adr/`.
Entry point: `ai_engineering_book/architecture/adr/adr_index.md`
```

**Remove entirely** (project-level, belongs in each project's own CLAUDE.md):
- Rules 1–6 (postgres_connector, psycopg, schema format, namespacing, logging, no pexpect)
- Testing rules 9–11
- Python conventions section
- "Starting a new project" template

**Keep** (truly universal — applies to all projects):
- Commit conventions
- Safe git commands
- Podman-only, uv-only rules
- Plan management (misc/plan/ structure)
- Contract docstrings section
- Design principles

### Step 7: Create `postgres_connector/CLAUDE.md`

New file. No existing one to reference. Structure per ADR-26049 principle:

```markdown
# CLAUDE.md

## Project Overview

postgres_connector — shared PostgreSQL access library for the soviar-systems ecosystem.
Provides `PostgresConnector` (DDL + DML), `ensure_schema()`, and `MyQuery` (optional,
pandas-dependent). Published to PyPI; all DB projects install it as a dependency.

## Governing Ecosystem Rules

<!-- Inline summaries — no links to parent dirs (standalone cloning compatibility) -->

### Commits (ADR-26024)
<type>: <subject ≤50 chars>

- <Verb>: <file-path> — <what and why>

Verbs: Created, Updated, Deleted, Renamed, Fixed, Moved, Added, Removed, Refactored, Configured

### Package manager
`uv` only. Never call `pip` directly.

### Containers (ADR-26040)
Podman only. Kube YAML manifests via `podman play kube`. Runnable via `systemctl --user`.
Never Docker, never Docker Compose, never Podman Compose.

### Safe git commands
- `git restore <file>` — never `git checkout -- <file>`
- `git restore --staged <file>` — never `git reset HEAD <file>`
- `git switch <branch>` — never `git checkout <branch>`
- Never `git reset --hard`, `git push --force`, or `git clean -f` without explicit request

### Plan management
Save plans to `misc/plan/YYYY-MM-DD_<slug>.md` before starting. Move to
`misc/plan/implemented/` when done. Track tech debt in `misc/plan/techdebt.md`.

### Contract docstrings (all files)
Every module opens with a docstring covering: scope/responsibility (one sentence + hard
boundaries), public interface (mark internals private), key design decisions (the why),
dependencies (imports, env vars, external services). Test files additionally: what belongs
here vs what does not, naming convention in use.

### TDD
Red → Green → Refactor. Pure-logic tests in `test_<module>.py` (no DB, runs anywhere).
Integration tests in `test_integration.py` (requires live PostgreSQL, mark
`@pytest.mark.integration`, skip unless `TEST_DB_URL` is set).

### Non-brittle tests
Test contracts, not implementation details. Assert on exit codes, return types, side
effects — not exact message strings. Use semantic assertions (`assert len(errors) > 0`).
Parameterize varied scenarios. Each test class must have a docstring stating the contract
it verifies.

### SVA check (ADR-26037)
Before adding anything: is this proportionate to the goal? Reuse before writing. If the
implementation seems disproportionate, step back and look for a simpler approach.

### DB access (ADR-26050, planned)
This package IS the shared DB access layer. All DB projects install it as a PyPI dep;
local re-implementation of DB access logic in downstream projects is prohibited.
All parameterised SQL uses psycopg's `sql` module — no f-string SQL.
Exception: DDL where every interpolated value comes from `schemata.py` and passes through
the appropriate `sql` wrapper.

### Schema namespacing (ADR-26051, planned)
Each DB project uses its own PostgreSQL schema. Schema name via `DB_SCHEMA` env var.
All SQL uses two-part `sql.Identifier(schema, table)`. `ensure_schema()` creates the
schema before any table DDL.

### Logging
`logging.getLogger(__name__)` in every module. No `print()` in production code.

### Secrets (ADR-26053, planned)
No credentials in code or committed env files. CLI tools receive secrets via env vars
injected by the secrets manager (Ansible Vault) at runtime. No `pexpect`.

## Ecosystem ADR Index

https://soviar-systems.github.io/ai_engineering_book/architecture/adr_index.html

## Architecture

Implementation decisions live in `architecture/adr/`. Spoke ADR for schema definition
format (`_is_constraint()`, tuple format, `create_attributes_dict()`) is planned as
`architecture/adr/adr_001_schema_definition_format.md` — to be written with ADR-26050.

## Commands

\`\`\`bash
uv sync                  # install deps
uv run pytest            # run tests
uv run pytest -m "not integration"  # skip DB tests
uv build                 # build package
\`\`\`
```

### Step 8: Update `un_votes/CLAUDE.md`

Replace the current `## Ecosystem Context` section (has broken relative links `../CLAUDE.md`
and `../architecture/adr/adr_001_...`) with `## Governing Ecosystem Rules` following the
same inline structure as `postgres_connector/CLAUDE.md` above.

DB-specific rules to include inline:
- All DB access via `postgres_connector` (PyPI dep) — no local re-implementation
- psycopg `sql` module for all parameterised SQL; no f-string SQL
- Schema `un` — set via `DB_SCHEMA` env var in `info.py`; all SQL uses `sql.Identifier(schema, table)`
- `logging.getLogger(__name__)` everywhere; no `print()`
- No `pexpect`; `PGPASSWORD` env var for CLI tools in `start.sh`

All other sections (Project Overview, Commands, Architecture, Container Deployment,
Deployment Strategy) remain unchanged — already well-structured.

---

## Verification

1. `grep -r "postgres_connector\|psycopg\|schemata" soviar-systems/CLAUDE.md` → no matches
2. `grep "\.\.\/" un_votes/CLAUDE.md` → no matches (no relative parent links)
3. `grep "\.\.\/" postgres_connector/CLAUDE.md` → no matches
4. `ls soviar-systems/adr_001*` → file not found
5. `ls ai_engineering_book/architecture/evidence/sources/S-26012*` → file exists

---

## Out of Scope

- `mentor_generator/CLAUDE.md` has a wrong `../architecture/adr/adr_001_...` reference
  (mentor_generator is not a DB project). Fix when working on mentor_generator.
- `vadocs/CLAUDE.md` "Testing Standards (from parent project)" framing — fix when working
  on vadocs.
- `postgres_connector/architecture/adr/adr_001_schema_definition_format.md` (spoke ADR) —
  write alongside ADR-26050 per roadmap section 1.12.
- `adr_index.md` update — no new ADRs to add until 26049+ are written.
