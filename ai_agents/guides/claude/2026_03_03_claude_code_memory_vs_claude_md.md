# Claude Code: MEMORY.md vs CLAUDE.md

**Date:** 2026-03-03

## CLAUDE.md

- Lives **in the git repo** (committed with code)
- Shared with **anyone** who clones the repo and uses Claude Code
- Contains project-wide instructions: coding conventions, build commands, architecture notes
- Can exist at multiple levels: repo root, subdirectories, `~/.claude/CLAUDE.md` (global)
- Think of it as **documentation for the AI**, similar to how `.editorconfig` is documentation for editors

How Claude Code hierarchical loading works (the native mechanism)

When Claude Code opens a session in /soviar-systems/un_votes/, it reads CLAUDE.md files from:
1. `/home/commi/...` (home, if exists)
2. `/home/commi/Yandex.Disk/it_working/projects/soviar-systems/CLAUDE.md` (parent)
3. `/home/commi/Yandex.Disk/it_working/projects/soviar-systems/un_votes/CLAUDE.md` (project)

## MEMORY.md (auto memory)

- Lives **outside the repo** in `~/.claude/projects/<project-path>/memory/`
- **Personal** — not committed, not shared
- Claude reads it automatically at conversation start and updates it when told to remember things
- Good for personal preferences, machine-specific facts, in-progress notes
- Think of it as **Claude's personal notebook** about working with you on a specific project

## When to use which

| Use case | Where |
|---|---|
| "Always use ruff for linting" (team convention) | `CLAUDE.md` |
| "This machine uses qdbus6, not qdbus" (machine-specific) | `MEMORY.md` |
| "Postmortem filenames use YYYY_MM_DD_ prefix" (personal preference) | Either — `MEMORY.md` if personal, `CLAUDE.md` if team |
| "Don't auto-commit" (workflow preference) | `MEMORY.md` |

## How to use memory in daily work

- **Tell Claude to remember:** "remember that we always use qdbus6 on this machine"
- **Tell Claude to forget:** "stop remembering X"
- **Project-scoped:** each project directory gets its own memory
- **`MEMORY.md`** is the main file, always loaded into context. Detailed topics go into separate files linked from there.
