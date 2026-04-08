---
title: "How Subagents Actually Work: The Myth of Process Spawning"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-04-08"
description: "Debunks the misconception that subagent spawning = OS fork/exec. Three real patterns: separate API calls, prompt-based role orchestration, and HTTP process management — with source code evidence."
tags: [architecture, agents, prompts]
token_size: "~800"
options:
  version: "1.0.0"
  birth: "2026-04-08"
  type: guide
jupyter:
  jupytext:
    cell_metadata_filter: -all
    formats: md,ipynb
    main_language: python
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
---

# How Subagents Actually Work: The Myth of Process Spawning

## The Misconception

When developers hear "subagent spawning," they think of OS-level `fork()` or `child_process.spawn()`. **This is wrong.** In every major AI coding agent analyzed (Claude Code, OpenCode, Qwen Code, OpenClaw, Superpowers), "spawning a subagent" is **not a process operation** — it is a **prompt engineering pattern**.

The term "forked agent" (used in Claude Code's source code) does not mean a forked OS process. It means a **separate LLM API call** with a different system prompt.

## The Three Real Patterns

### Pattern 1: Separate LLM API Calls (Most Common)

A new API call with different system prompts and curated context. No process spawning. No separate runtime.

**Used by:** Claude Code (compaction, session memory), OpenCode (compaction agent), Qwen Code (compression), OpenClaw (summarization)

The mechanism is always the same:

```
Client code:
  1. Build messages = [newSystemPrompt, ...conversationHistory, instruction]
  2. Call LLM API → response = summary text only
  3. Save response to file / database
  4. Resume main conversation with: [originalSystemPrompt, {role: user, content: summary}]
```

:::{seealso}
For the detailed breakdown of how the API contract works — why system prompts don't mix, what the response actually contains, and how the summary replaces history — see [The Compaction API Contract](/ai_agents/context_management/compaction_api_contract.ipynb).
:::

**OpenCode compaction agent** — the most explicit example:

```typescript
// packages/opencode/src/session/compaction.ts
compaction: {
  name: "compaction",
  mode: "primary",
  native: true,
  hidden: true,
  prompt: PROMPT_COMPACTION,  // ← entirely different system prompt
  permission: Permission.merge(
    defaults,
    Permission.fromConfig({ "*": "deny" }),  // ← ALL TOOLS DENIED
    user
  ),
  options: {},
}
```

This is a **new agent definition** with a different system prompt and all tools denied. When context overflows, the runtime makes a separate API call using this agent definition. The conversation history is sent as-is (user/assistant messages), but the system prompt is `PROMPT_COMPACTION`, not the normal agent system prompt.

The compact prompt template produces a structured summary:

```
Provide a detailed prompt for continuing our conversation above.
Focus on information that would be helpful for continuing the conversation,
including what we did, what we're doing, which files we're working on,
and what we're going to do next.

Stick to this template:
---
## Goal
[What goal(s) is the user trying to accomplish?]

## Instructions
- [What important instructions did the user give you?]

## Discoveries
[What notable things were learned during this conversation?]

## Accomplished
[What work has been completed, in progress, and left?]

## Relevant files / directories
[Construct a structured list of relevant files.]
---
```

**Qwen Code compression** — the same pattern, different API:

```typescript
const summaryResponse = await config.getContentGenerator().generateContent({
  model,
  contents: [
    ...historyToCompress,
    {
      role: 'user',
      parts: [{
        text: 'First, reason in your scratchpad. Then, generate the <state_snapshot>.',
      }],
    },
  ],
  config: {
    systemInstruction: getCompressionPrompt(),  // ← different system prompt
  },
})
```

After the API returns the summary, the old history is **replaced** (not appended to):

```typescript
extraHistory = [
  { role: 'user', parts: [{ text: summary }] },
  { role: 'model', parts: [{ text: 'Got it. thanks for the additional context!' }] },
  ...historyToKeep,  // The last 30% of conversation
]
```

### Pattern 2: Prompt-Based Role Orchestration

The same LLM session is instructed to sequentially adopt different roles, each with fresh context. No separate API call — just careful prompt design within the same conversation.

**Used by:** Superpowers (subagent-driven development)

Superpowers implements a **3-role subagent orchestration pipeline**:

1. **Implementer** — receives curated task context and executes
2. **Spec Reviewer** — receives fresh context (not the implementer's full history) to verify spec compliance
3. **Code Quality Reviewer** — receives fresh context to check SOLID principles, test coverage, maintainability

:::{note}
The SKILL.md files define prompt templates that the host LLM is instructed to use. There is **no framework code** — just carefully crafted Markdown instructions.
:::

| File | Purpose |
|------|---------|
| `skills/subagent-driven-development/SKILL.md` | Three-role orchestration instructions |
| `skills/subagent-driven-development/implementer-prompt.md` | Implementer dispatch template |
| `skills/subagent-driven-development/spec-reviewer-prompt.md` | Spec compliance review template |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | Code quality review template |

The host agent (controller) is told to:

1. Copy the prompt template from the appropriate `.md` file
2. Fill in task-specific context (relevant code, requirements, specs)
3. Make a **new API call** with that system prompt + curated context
4. Read the response and decide whether to proceed to the next role or send back for fixes

:::{warning}
**There is no orchestration framework.** The skills are carefully crafted prompts that program the LLM to behave as an orchestrator. The "subagent dispatch" is the LLM following instructions to make separate API calls with different prompts — it is not programmatic orchestration like you'd find in a traditional multi-agent system (e.g., AutoGen, CrewAI).
:::

The honest assessment from the source analysis:

> **"It's prompt engineering at scale.** The best available techniques (explicit counters, rationalization tables, commitment devices, hard gates, two-stage review) make it more robust than naive prompting — but it's still fundamentally probabilistic. The system reduces failure rates through empirical testing rather than eliminating them through guarantees."

:::{seealso}
For a deep dive into how agents fight LLM drift and instruction non-compliance, see [Stability Against LLM Drift](stability_against_llm_drift.ipynb).
:::

### Pattern 3: HTTP Process Management (Actual Processes)

This is the **only pattern** that involves real OS processes. KiloCode's Agent Manager (VS Code extension) manages multiple `kilo serve` HTTP server processes, one per session.

**Used by:** KiloCode (Agent Manager)

The architecture:

- Each session gets its own **git worktree**
- The VS Code extension coordinates `kilo serve` processes via **HTTP + SSE** (Server-Sent Events)
- Each session has its own independent SQLite database and context budget
- Session lifecycle: **create, pause, resume, delete**

This is actual process spawning — the VS Code extension spawns and manages multiple `kilo serve` processes. But this is **session isolation**, not "subagent spawning" within a single session. Each process is a fully independent agent instance.

## The Universal Pattern: Full History, One System Prompt

All agents (except KiloCode's multi-session setup) follow the same fundamental pattern:

```
API Call N:
├─ System Prompt              (always present — exactly ONE per call)
├─ Conversation History       (turns 1..N-1)  ← GROWS each turn
├─ Tool Results               (if any)
└─ User Message               (turn N)
```

Each API call sends the full conversation history. The LLM has no memory between calls. When a "subagent" is "spawned," it is simply a new API call with:

1. A **different system prompt** (compaction, review, summarization)
2. The **same or curated conversation history**
3. A **specific instruction** (e.g., "generate the state snapshot")

The response contains **only the new assistant message** — not the input history. This is how LLM APIs work: stateless request/response.

:::{seealso}
For the detailed API contract explanation — why system prompts don't mix, what the response contains, and how history replacement works — see [The Compaction API Contract](/ai_agents/context_management/compaction_api_contract.ipynb).
:::

## Summary Table

| Pattern | Mechanism | Is it OS processes? | Agents |
|---------|-----------|-------------------|--------|
| **Separate API call** | New API call with different system prompt + full/curated history | ❌ No | Claude Code, OpenCode, Qwen Code, OpenClaw |
| **Prompt role orchestration** | Same conversation, new API call with role-specific prompt template | ❌ No | Superpowers |
| **HTTP process management** | VS Code extension manages multiple `kilo serve` processes via HTTP+SSE | ✅ Yes (session isolation) | KiloCode Agent Manager |

## Key Takeaway

**"Subagent spawning" in AI coding agents is almost always a misnomer.** It is a **separate LLM API call** with a different system prompt. The LLM doesn't "mix" system prompts because each API call receives exactly one. The term "forked agent" in source code (e.g., Claude Code) refers to this separate API call pattern, not to an OS `fork()`.

The only exception is KiloCode's Agent Manager, which manages actual HTTP server processes — but this is for **multi-session isolation**, not for spawning subagents within a single conversation.
