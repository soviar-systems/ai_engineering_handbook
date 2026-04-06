---
title: "Restructure repo: ai_system_layers + ai_agents"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-04-05"
description: "Rename ai_system/ to ai_system_layers/, move 6_agents/ to repo root as ai_agents/, add agents tag, update all cross-references. Breaking change — major version bump."
tags: [architecture, documentation]
options:
  version: "1.0.0"
  birth: "2026-04-05"
---

# Plan: Restructure repo — ai_system_layers + ai_agents

## Background

The six-layer `ai_system/` directory was always a component catalog (execution → context). The `6_agents/` directory was the awkward "layer 6" — but agents are not a component, they're the assembled product. As explored:

> **ai_system/ is the engine parts catalog. ai_agents/ is the car.**

Future agent-level research (multi-agent systems, agent identity, etc.) won't fit the six-layer framework. The rename resolves the category error permanently.

Full analysis with Heuer-style alternative hypothesis testing: [A-26022](/architecture/evidence/analyses/A-26022_agents_break_the_layer_model.md).

**This is a breaking change.** Every path reference to `ai_system/` across the repo becomes stale. The next release requires a **major version increment**.

## Changes

### 1. Rename `ai_system/` → `ai_system_layers/`

- `git mv ai_system/ ai_system_layers/`
- This preserves the numbered layer convention: `1_execution/` through `5_context/`

### 2. Move `6_agents/` → `ai_agents/` (repo root)

- `git mv ai_system_layers/6_agents/ ai_agents/`
- Remove the `6_` prefix — it's no longer a layer number
- `ai_agents/context_management/` files stay as-is

### 3. Update `ai_agents/README.md`

- Add rationale: agents are products, not components (car vs engine parts analogy)
- Update structure diagram — remove `6_` prefix
- Update internal links to reflect new root-level position
- Keep `context_management/` reference intact

### 4. Create `ai_system_layers/README.md`

- Was missing before — now needed at new location
- Describe the six-layer framework purpose

### 5. Add `agents` tag to `.vadocs/conf.json`

```json
"agents": {
  "description": "Source-level analysis of external AI coding agents"
}
```

### 6. Update frontmatter on all `ai_agents/context_management/` files

- Change `tags: [architecture, agents]`
- Add `token_size` field to each file (was missing, blocked commit)

### 7. Update cross-references across the repo

| File | What to update |
|------|---------------|
| `README.md` (repo root) | `ai_system/` → `ai_system_layers/`, `ai_system/6_agents/` → `ai_agents/` |
| `AGENTS.md` | Same as above + add migration notice (see §8) |
| `QWEN.md` | Same as above |
| `.vadocs/validation/` (excludes) | Any paths referencing `ai_system/` |
| CI/CD workflows | Any path filters for `ai_system/` |
| All ADRs with links to `ai_system/` | Update paths |

### 8. Add migration notice to `AGENTS.md`

Since this is a **breaking rename of the central directory**, `AGENTS.md` must include a visible notice for a transition period:

```markdown
:::{note}
**Breaking change (vX.0.0):** `ai_system/` was renamed to `ai_system_layers/`.
`6_agents/` was moved to repo root as `ai_agents/`.
All internal links updated. External references to the old paths are stale.
:::
```

This notice should remain for at least 2-3 release cycles, then can be removed once the old path is no longer referenced anywhere.

### 9. Update `ai_agents/` files for new location

Relative paths within `ai_agents/` are unchanged (moved as a unit).
Cross-references from `ai_agents/` to `ai_system_layers/` need updating — search for `../1_execution/`, `../2_model/`, etc.

### 10. Verify and commit

- Run `uv run tools/scripts/check_frontmatter` on all changed files
- Run `uv run tools/scripts/check_broken_links.py`
- Run `uv run jupytext --sync` if any notebooks are affected
- Commit with descriptive message

## Execution Order

1. Write plan (this file) → DONE
2. Add `agents` tag to `.vadocs/conf.json` (unblocks commit)
3. Rename + move directories
4. Add migration notice to `AGENTS.md`
5. Update all cross-references (scripts, docs, ADRs)
6. Update frontmatter on `context_management/` files (add `token_size`)
7. Verify: frontmatter, links, jupytext sync
8. Commit

## Risks

- **Broken internal links**: Every relative path from any file into `ai_system/` breaks. Need comprehensive search across all markdown files.
- **Script paths**: `tools/scripts/paths.py` exclusion constants may reference `ai_system/6_agents/agents_source_code/`.
- **CI/CD**: GitHub Actions path filters may reference `ai_system/`.
- **ADR references**: Persistent artifacts reference `ai_system/` paths via markdown links — must update all.
