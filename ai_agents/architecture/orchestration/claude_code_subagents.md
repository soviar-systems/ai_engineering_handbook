---
title: "Claude Code: Subagent Implementation Analysis"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: 2026-04-26
description: "Analysis of Claude Code's forking mechanism and subagent isolation."
tags: [agents, architecture]
token_size: "~1000"
options:
  type: guide
  birth: 2026-04-26
  version: 1.0.0
---

# Claude Code: Subagent Implementation Analysis

## Overview
Claude Code implements a "Forked Agent" pattern to execute isolated sub-tasks. This mechanism allows the main agent to delegate work to specialized workers (e.g., session memory maintenance, prompt suggestions) without polluting the main session history or risking unstable state mutations.

## Core Implementation
The primary logic resides in `src/utils/forkedAgent.ts`.

### 1. Calling Mechanism
The `runForkedAgent` function is the entry point for initiating a subagent.

```typescript
export async function runForkedAgent({
  promptMessages,
  cacheSafeParams,
  canUseTool,
  querySource,
  forkLabel,
  overrides,
  maxOutputTokens,
  maxTurns,
  onMessage,
  skipTranscript,
  skipCacheWrite,
}: ForkedAgentParams): Promise<ForkedAgentResult> {
  // ...
  const isolatedToolUseContext = createSubagentContext(
    toolUseContext,
    overrides,
  )
  // ...
  for await (const message of query({
    messages: initialMessages,
    systemPrompt,
    userContext,
    systemContext,
    canUseTool,
    toolUseContext: isolatedToolUseContext,
    querySource,
    maxOutputTokensOverride: maxOutputTokens,
    maxTurns,
    skipCacheWrite,
  })) {
    // ...
  }
}
```

### 2. Context Isolation & Sharing
Claude Code employs a strict isolation strategy by default, with an explicit opt-in for sharing.

#### Isolation via `createSubagentContext`
The `createSubagentContext` function ensures that mutable state is not accidentally shared between the parent and child:

- **File State**: `readFileState` is cloned using `cloneFileStateCache`.
- **Abort Logic**: A new `AbortController` is created via `createChildAbortController`, ensuring parent aborts propagate downward, but child aborts are local.
- **State Mutations**: Callbacks like `setAppState` and `setResponseLength` are replaced with no-ops (`() => {}`) unless `shareSetAppState` or `shareSetResponseLength` is true in `SubagentContextOverrides`.
- **Identity**: Every subagent is assigned a unique `agentId` via `createAgentId()`.

#### Prompt Cache Optimization
To avoid the high cost of re-sending large contexts, Claude Code uses `CacheSafeParams`. This object captures the exact parameters (`systemPrompt`, `userContext`, `systemContext`, `toolUseContext`, `forkContextMessages`) required to hit the Anthropic API prompt cache.

### 3. Tracking and Logging
Subagents are tracked as "sidechains" to keep the main conversation clean.

- **Sidechain Transcripts**: Subagent messages are recorded using `recordSidechainTranscript`, storing them separately from the main session.
- **Telemetry**: The `logForkAgentQueryEvent` function logs a `tengu_fork_agent_query` event, capturing:
    - `forkLabel`: The role of the subagent (e.g., `'session_memory'`).
    - `cacheHitRate`: Calculated based on `cache_read_input_tokens` vs total input.
    - `durationMs` and `messageCount`.

## Architectural Pattern: Supervisor-Worker
Claude Code follows a **Supervisor-Worker** pattern. The primary agent acts as the supervisor, dispatching worker agents for specific tasks. The worker executes in a "forked" environment—inheriting a snapshot of the parent's state but operating independently—and returns a final result to the supervisor.

| Feature | Implementation |
| :--- | :--- |
| **Isolation** | Clone-on-fork with no-op mutation callbacks |
| **Context Sharing** | Exact parameter matching for prompt cache hits |
| **History** | Sidechain recording (separate from main session) |
| **Lifecycle** | Short-lived, result-oriented loops |
