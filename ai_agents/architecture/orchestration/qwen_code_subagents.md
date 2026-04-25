---
title: "Qwen Code: Subagent Implementation Analysis"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: 2026-04-26
description: "Analysis of Qwen Code's hybrid subagent system and cache optimization."
tags: [agents, architecture]
token_size: "~1000"
options:
  type: guide
  birth: 2026-04-26
  version: 1.0.0
---

# Qwen Code: Subagent Implementation Analysis

## Overview
Qwen Code implements a sophisticated subagent system that supports both specialized worker agents and "forked" agents. The architecture focuses on maximizing prompt cache efficiency (via DashScope) and providing rich real-time feedback to the user.

## Core Implementation
The primary interface is the `AgentTool` located in `packages/core/src/tools/agent/agent.ts`.

### 1. Calling Mechanism
The `AgentTool` is a declarative tool that allows the primary agent to delegate tasks. It uses an `AgentToolInvocation` to handle the lifecycle and an `AgentEventEmitter` to track progress.

For "forked" agents (which share the parent's context), the `createForkSubagent` method is used:

```typescript
private async createForkSubagent(agentConfig: Config): Promise<{
  subagent: AgentHeadless;
  taskPrompt: string;
}> {
  // ...
  const generationConfig = geminiClient?.getChat().getGenerationConfig();
  if (generationConfig?.systemInstruction) {
    const parentToolDecls: FunctionDeclaration[] =
      (generationConfig.tools as Array<{
        functionDeclarations?: FunctionDeclaration[];
      }>)?.flatMap((t) => t.functionDeclarations ?? []) ?? [];
    
    // Inherits parent's system prompt and tools verbatim to share DashScope cache prefix
    promptConfig = { ... };
    toolConfig = { ... };
  }
  // ...
}
```

### 2. Context Isolation & Sharing
Qwen Code differentiates between specialized subagents and forked agents.

#### Forked Agents (Context Sharing)
Forked agents are designed for "context-sharing extensions." They inherit:
- **System Instruction**: The exact system prompt of the parent.
- **Tool Declarations**: The exact set of tools available to the parent.
- **History**: A modified version of the parent's history (processed via `buildForkedMessages`).
This verbatim inheritance is critical for hitting the **DashScope prompt cache**, reducing latency and cost.

:::{note}
**DashScope Prompt Caching**: The provider (DashScope) optimizes inference by caching the KV (Key-Value) state of the prompt prefix. If the sequence of system prompts, tool declarations, and messages (the "prefix") is identical to a previous request, the model skips re-processing those tokens. This drastically reduces Time to First Token (TTFT) and lowers token costs for large contexts.
:::

#### Specialized Agents (Isolation)
Specialized agents are loaded via the `SubagentManager` and `BuiltinAgentRegistry`. They operate with their own defined capabilities and toolsets.

#### Governance & Permissions
The `resolveSubagentApprovalMode` function governs the autonomy of subagents:
- **Inheritance**: Permissive modes (`YOLO`, `AUTO_EDIT`) from the parent always win.
- **Autonomy**: In trusted folders, subagents default to `AutoEdit` to ensure they can complete complex tasks without constant user interruption.

### 3. Governance & Logging
Qwen Code provides deep observability into subagent execution.

- **Event-Driven Tracking**: `AgentToolInvocation` listens for `AgentEventType` events:
    - `START`, `TOOL_CALL`, `TOOL_RESULT`, `FINISH`, `ERROR`.
- **Real-time UI Updates**: The system maintains a `currentDisplay` state (status, active tool calls, accumulated tokens) that is pushed to the UI, allowing the user to see exactly what the subagent is doing in real-time.
- **Usage Metrics**: `USAGE_METADATA` events track token consumption (`candidatesTokenCount`) per round.

## Architectural Pattern: Hybrid Supervisor-Worker
Qwen Code utilizes a hybrid approach:

1.  **Specialized Worker Pattern**: For well-defined roles (e.g., a "test-runner"), using a `subagent_type` with a restricted toolset.
2.  **Forked Extension Pattern**: For tasks requiring the full context of the parent but separate execution logic, maximizing prompt cache hits.

| Feature | Forked Agent | Specialized Agent |
| :--- | :--- | :--- |
| **Context** | Shared (Parent Mirror) | Isolated / Specialized |
| **Cache** | High Hit Rate (Verbatim) | Lower / Fresh |
| **Tools** | Parent's Toolset | Defined by `subagent_type` |
| **Execution** | Result-oriented fork | Role-oriented worker |
