# Plan: Consolidate all agent content under `ai_agents/`

**Date:** 2026-04-11
**Status:** Proposed → Implemented

## Rationale

Three locations cover AI agent topics:
- `tools/docs/ai_agents/` — how to use agents as developer tools (setup guides, workflows)
- `ai_agents/` — how agents work internally (architecture research, design patterns)
- `research/` — external cloned repos consumed only by `ai_agents/` content

Consolidating into a single `ai_agents/` directory creates one source of truth, eliminates the semantically odd `tools/docs/` location, and moves `research/` closer to its consumer.

## Target Structure

```
ai_agents/
├── README.md
├── research/                        ← moved from repo root
│   ├── ai_coding_agents/            ← 8 nested git repos (aider, claude, etc.)
│   └── ai_infrastructure/           ← mempalace, open-webui
├── architecture/                    ← renamed from current subdirs
│   ├── context_management/
│   ├── session_history_management/
│   ├── skills/
│   └── tooling/
└── guides/                          ← merged from tools/docs/ai_agents/
    ├── vim_and_aider/
    │   ├── 01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.{md,ipynb}
    │   └── 03_vim_ollama_llm_tab_completion_nuances.{md,ipynb}
    ├── aider/
    │   ├── 02_aider_commands_handout.{md,ipynb}
    │   └── 04_connect_to_capable_llms_using_api_keys.{md,ipynb}
    ├── kilocode/
    │   └── 05_kilocode_cli_setup.{md,ipynb}
    ├── comparing_cli_agents.{md,ipynb}
    ├── claude/
    └── images/
```

## Implementation

### Commit 1: Move `research/` under `ai_agents/`

1. `mv research ai_agents/research` (physical move before registry update)
2. Relocate both entries via `manage_external_repos.py relocate`:
   - `research/ai_coding_agents` → `ai_agents/research/ai_coding_agents`
   - `research/ai_infrastructure` → `ai_agents/research/ai_infrastructure`
3. Fix 14 symlinks in `~/.qwen/skills/` (retarget `research/` → `ai_agents/research/`)
4. Update `myst.yml`: `"research/ai_infrastructure/*"` → `"ai_agents/research/ai_infrastructure/*"`
5. Update `ai_agents/README.md` research links: `/research/` → `/ai_agents/research/`

### Commit 2: Move content into `ai_agents/`

1. Move architecture subdirs:
   - `context_management/`, `session_history_management/`, `skills/`, `tooling/` → `ai_agents/architecture/`

2. Move guides from `tools/docs/ai_agents/`:
   - `01_vim_in_ai_era...` + `03_vim_ollama...` → `ai_agents/guides/vim_and_aider/`
   - `02_aider_commands_handout` + `04_connect_to_capable_llms...` → `ai_agents/guides/aider/`
   - `05_kilocode_cli_setup` → `ai_agents/guides/kilocode/`
   - `comparing_cli_agents` → `ai_agents/guides/`
   - `claude/`, `images/` → `ai_agents/guides/`

3. Update links (~8 active cross-references):
   - `0_intro/00_onboarding.{md,ipynb}` → `/ai_agents/guides/vim_and_aider/01_...`
   - Internal guide cross-refs → new absolute paths
   - `ai_agents/architecture/skills/skill_discovery_across_platforms.md` → `/ai_agents/research/ai_coding_agents/superpowers/...`
   - `ai_agents/README.md` → update directory tree + all internal links

4. Remove empty `tools/docs/ai_agents/` and `tools/docs/` (if empty)

## Files NOT to touch (historical records)

- `CHANGELOG` — historical record
- `RELEASE_NOTES.md` — historical record
- `misc/pr/tg_channel_ai_learning/` — historical Telegram post
- `misc/plan/implemented/plan_20260314_release_preparation_adr_alignment.md` — completed plan
- `.aider.chat.history.md` — ephemeral session log

## Validation

1. `ls -la ~/.qwen/skills/` — all 14 symlinks resolve
2. `uv run jupytext --sync`
3. `uv run tools/scripts/check_broken_links.py`
4. `uv run tools/scripts/check_link_format.py`
5. `uv run python -m tools.scripts.check_frontmatter ai_agents/guides/`
