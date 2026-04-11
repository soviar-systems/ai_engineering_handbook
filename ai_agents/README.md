# ai_agents — Real-World Agent Framework Analysis

This directory consolidates source code of external AI coding agents for comparative study, paired with analysis notebooks organized by topic.

:::{note}
**Why this is at the repo root:** `ai_system_layers/` is the engine parts catalog (execution → context). Agents are not a layer — they're the assembled product. **ai_system/ is the engine parts catalog. ai_agents/ is the car.** Future agent-level research (multi-agent systems, agent identity, etc.) won't fit the six-layer framework. This directory lives at the root to resolve that category error permanently.
:::

## Structure

```
ai_agents/
├── README.md                  ← this file
├── context_management/        ← source-level analysis of context window strategies
├── session_history_management/ ← analysis notebooks on context/memory patterns
├── skills/                     ← analysis notebooks on skill/prompt systems
└── tooling/                    ← analysis notebooks on tool architectures
```

External agent source code is cloned into `research/ai_coding_agents/` (nested git repos).

### Source Code (`research/ai_coding_agents/`)

Each subdirectory is an independent git repository, excluded from the parent repo's `.gitignore` and from script checks (`check_broken_links`, `check_link_format`, etc.) via `tools/scripts/paths.py`.

| Agent | Source | Type | Key Architecture |
|-------|--------|------|------------------|
| [aider](/ai_agents/research/ai_coding_agents/aider/) | [aider.chat](https://aider.chat/) | Python CLI | Repo map, git-autocommit, IDE watch mode |
| [claude-code-main](/ai_agents/research/ai_coding_agents/claude-code-main/) | (leaked source) | TypeScript CLI | 5-tier context management, server-side cache editing, session memory agent |
| [kilocode](/ai_agents/research/ai_coding_agents/kilocode/) | [Kilo-Org/kilo](https://github.com/Kilo-Org/kilo) | TypeScript CLI (Bun) | OpenCode fork, Agent Manager (VS Code multi-session panel with git worktrees), Turborepo monorepo |
| [openclaw](/ai_agents/research/ai_coding_agents/openclaw/) | [openclaw/openclaw](https://github.com/openclaw/openclaw) | TypeScript CLI | Personal AI assistant — multi-channel (WhatsApp, Telegram, Slack, etc.), speaks/listens, Gateway as control plane |
| [openclaude](/ai_agents/research/ai_coding_agents/openclaude/) | [GitLawB/OpenClaude](https://github.com/GitLawB/OpenClaude) | TypeScript CLI (Node.js) | Claude Code fork with OpenAI-compatible provider shim |
| [opencode](/ai_agents/research/ai_coding_agents/opencode/) | [anomalyco/opencode](https://github.com/anomalyco/opencode) | TypeScript CLI (Bun) | Open source coding agent — Bun workspaces, parallel tool execution, Turborepo monorepo (upstream of KiloCode) |
| [qwen-code](/ai_agents/research/ai_coding_agents/qwen-code/) | [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code) | TypeScript CLI (Node.js) | Gemini CLI fork, JSONL session history, Skills + SubAgents |
| [superpowers](/ai_agents/research/ai_coding_agents/superpowers/) | [obra/superpowers](https://github.com/obra/superpowers) | Plugin for coding agents (16 Markdown skills) | Behavioral operating system for agents — skills auto-trigger based on context; includes subagent-driven development with 3-role review (implementer → spec reviewer → code quality reviewer) |

### Analysis Notebooks

Findings from studying these agents are saved as MyST notebooks (`.md` + `.ipynb` pairs) in topic directories:

| Topic | Location | What's Studied |
|-------|----------|----------------|
| Context management | `context_management/` | Source-level analysis: full history pattern, compaction strategies, token budgets across 6 agents |
| Session history | `session_history_management/` | How agents manage context, memory, crash recovery |
| Skills | `skills/` | Skill discovery, indexing, triggering patterns |
| Tooling | `tooling/` | Tool architectures, shell execution, sandboxing |

## Workflow

### Managing Source Code Repositories

Use [tools/scripts/manage_external_repos.py](/tools/scripts/manage_external_repos.py) for managing external research repos. Run with `--help` for current usage patterns:

```bash
uv run tools/scripts/manage_external_repos.py --help
```

Common operations: `update` (pre-session refresh), `list` (see all repos and status), `list --dirs` (show registered directories), `setup` (clone new project), `register` (add new research directory), `unregister` (remove from registry).

:::{tip}
Run `update` before starting any analysis session — agent architectures evolve fast, and a stale checkout can lead to wrong conclusions about how a feature works.
:::

### Research Process

1. **Study** code in-place — use `git log`, `git diff`, and navigation within each nested repo
2. **Save analysis** as MyST notebooks in a topic subdirectory (create one if needed)
3. **Sync** notebooks: `uv run jupytext --sync`

## Key Learnings Across Agents

### Session History / Context Management

- **All agents** send the full conversation history on every API call — no chunking, no delta updates. Context grows unboundedly until compaction kicks in. See [context_management/overview.md](context_management/overview.md) for the full analysis.
- **Qwen Code** uses append-only JSONL event logs (`{sessionId}.jsonl`) with tree-structured `uuid`/`parentUuid` links — crash-safe by design, supports `/compress` without mutating history.
- **Claude Code** has the most sophisticated system: 5-tier compaction from microcompact (server-side cache editing) through session memory (background agent maintaining a markdown summary file) to full compaction with PTL retry.
- **Aider** relies on git history as the session record — every change is a commit, making the codebase itself the memory. Async background summarization doesn't block the main loop.
- **Superpowers** avoids session history sharing entirely — subagents get fresh context per task to prevent context pollution.
- **KiloCode** uses an Agent Manager (VS Code extension) for multi-session orchestration — each session gets its own git worktree, with the extension coordinating `kilo serve` processes via HTTP + SSE.
- **OpenClaw** is a personal assistant — not a coding agent. Uses a Gateway as control plane with persistent session state across channels (WhatsApp, Telegram, etc.).

### Tool Systems

- **Qwen Code:** All tools extend `BaseDeclarativeTool` in TypeScript (`packages/core/src/tools/`).
- **Aider:** Python-based tool definitions with strong git integration.
- **OpenClaude:** Inherits Claude Code's tool set (bash, file ops, grep, glob, agents, MCP) with provider-agnostic routing.
- **KiloCode / OpenCode:** Fork lineage — OpenCode is the upstream, KiloCode adds the Agent Manager. Both enforce parallel tool execution (`ALWAYS USE PARALLEL TOOLS WHEN APPLICABLE`).

### Skill / Prompt Systems

- **Superpowers:** 16 Markdown skills (`SKILL.md` + frontmatter) that auto-trigger based on agent context. Skills are *code, not prose* — behavior-shaping instructions tuned through adversarial pressure testing. Priority system: user instructions > superpowers skills > default system prompt.
- **Qwen Code:** Markdown + YAML skill definitions discovered and invoked during conversation.
- **Aider:** Instruction files (`.aider.model.metadata.json`, `.aider.input.history`) and per-model configuration.

### Multi-Agent Orchestration

- **Superpowers** is a plugin, not an agent — but its `subagent-driven-development` skill implements a 3-role review pipeline: a controller (the host agent) dispatches fresh subagents sequentially (Implementer → Spec Reviewer → Code Quality Agent), each with curated context to avoid pollution.
- **Qwen Code** has a SubAgents system with configuration stored as Markdown + YAML frontmatter.
- **KiloCode** implements multi-session orchestration via its Agent Manager in VS Code — each session gets a git worktree and its own `kilo serve` process.
