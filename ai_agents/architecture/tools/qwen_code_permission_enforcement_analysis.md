---
title: Qwen Code Permission Enforcement Analysis
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-27
description: "Source-level analysis of the L3-L4-L5 permission flow and the 'Implicit Trust' risk in Qwen Code."
tags:
- architecture
- agents
- security
options:
  version: 1.0.0
  birth: 2026-04-27
  type: guide
  token_size: 1534
---

# Qwen Code Permission Enforcement Analysis

This document provides a source-level analysis of how Qwen Code enforces tool access and filesystem permissions.

## Architectural Overview

Permission enforcement is implemented as a decoupled two-stage process:
1.  **Requestor (LLM)**: Decides *which* tool and *which* target (path/command) to use based on the task.
2.  **Gatekeeper (Agent Wrapper)**: Decides *if* the request is permitted based on a hierarchical rule evaluation.

The Gatekeeper operates independently of the LLM's intent, evaluating requests through a three-layer flow: **L3 (Tool Default) $\rightarrow$ L4 (User Settings) $\rightarrow$ L5 (Approval Mode)**.

---

## 1. Layer 3: Tool-Level Defaults (Inherent Risk)

The system assigns a default risk level to every tool invocation. For shell commands (`run_shell_command`), this is determined via AST analysis.

### Implementation
In `packages/core/src/permissions/permission-manager.ts`, the `resolveDefaultPermission` function defines the fallback logic:

```typescript
// packages/core/src/permissions/permission-manager.ts

private async resolveDefaultPermission(command: string): Promise<'allow' | 'ask' | 'deny'> {
  // Security: command substitution ($(), ``, <(), >()) → deny
  if (detectCommandSubstitution(command)) {
    return 'deny';
  }

  // AST-based read-only detection
  try {
    const isReadOnly = await isShellCommandReadOnlyAST(command);
    if (isReadOnly) {
      return 'allow';
    }
  } catch {
    // AST check failed, fall back to 'ask'
  }

  return 'ask';
}
```

**L3 Defaults Summary:**
- **`allow`**: Read-only operations (e.g., `ls`, `cat`, `grep`) as verified by `isShellCommandReadOnlyAST`.
- **`ask`**: State-changing operations (e.g., `rm`, `mkdir`).
- **`deny`**: Security violations (e.g., command substitution).

---

## 2. Layer 4: PermissionManager Override (User Settings)

The `PermissionManager` evaluates requests against rules defined in `settings.json`.

### Rule Hierarchy and Priority
The system uses a strict priority cascade. If multiple rules match, the most restrictive decision wins.

```typescript
// packages/core/src/permissions/permission-manager.ts

const DECISION_PRIORITY: Readonly<Record<PermissionDecision, number>> = {
  deny: 3,
  ask: 2,
  default: 1,
  allow: 0,
};
```

Evaluation order in `evaluateSingle`:
1. **Deny Rules**: Checked first; if any match, the result is immediately `deny`.
2. **Ask Rules**: Checked second.
3. **Allow Rules**: Checked third.
4. **Default**: Returned if no rules match.

### Meta-Categories (Rule Grouping)
To simplify configuration, Qwen Code groups multiple tools into "meta-categories" using sets defined in `packages/core/src/permissions/rule-parser.ts`.

```typescript
// packages/core/src/permissions/rule-parser.ts

const READ_TOOLS = new Set([
  'read_file',
  'grep_search',
  'glob',
  'list_directory',
]);

const EDIT_TOOLS = new Set(['edit', 'write_file']);
```

A rule defined as `"Read"` is automatically applied to all tools in `READ_TOOLS` via `toolMatchesRuleToolName`.

### Global vs. Scoped Access
Rules are parsed by `parseRule`. If a rule lacks a specifier (e.g., `"Read"`), it is treated as a global grant/restriction for that tool category.

```typescript
// packages/core/src/permissions/rule-parser.ts

export function parseRule(raw: string): PermissionRule {
  const openParen = normalized.indexOf('(');
  if (openParen === -1) {
    // Simple tool name rule (no specifier) → Global Access
    const canonicalName = resolveToolName(normalized);
    return { raw: trimmed, toolName: canonicalName };
  }
  // ... scoped rules with specifiers
}
```

---

## 3. Layer 5: Final Decision (Approval Mode)

The final outcome is the result of the L3/L4 evaluation modified by the current `ApprovalMode` (configured in `settings.json`).

### Decision Matrix
Implemented in `packages/core/src/core/coreToolScheduler.ts`:

| L3/L4 Result | Approval Mode | Final Outcome | Logic |
| :--- | :--- | :--- | :--- |
| `allow` | Any | **Proceed** | Tool is inherently safe or explicitly allowed. |
| `deny` | Any | **Block** | Security violation or explicit deny. |
| `ask` | `YOLO` | **Proceed** | User has opted into auto-approving risky tools. |
| `ask` | `PLAN` / `DEFAULT` | **Ask User** | Requires manual confirmation. |

---

## 4. Virtual Operation Analysis (Shell Jail-break Prevention)

To prevent the LLM from bypassing path restrictions by using shell commands (e.g., using `cat` instead of `read_file`), the agent employs **Virtual Operations**.

### Implementation
In `packages/core/src/permissions/permission-manager.ts`, the `evaluateSingle` function triggers a secondary check for shell commands:

```typescript
// packages/core/src/permissions/permission-manager.ts

if (toolName === 'run_shell_command' && command !== undefined) {
  const virtualDecision = this.evaluateShellVirtualOps(
    extractShellOperations(command, cwd),
    pathCtx,
  );
  if (
    virtualDecision !== 'default' &&
    DECISION_PRIORITY[virtualDecision] > DECISION_PRIORITY[baseDecision]
  ) {
    return virtualDecision;
  }
}
```

**Mechanism:**
1. The `extractShellOperations` utility parses the command string to identify filesystem or network operations.
2. Each operation is mapped to a `virtualTool` (e.g., `cat` $\rightarrow$ `read_file`).
3. The `PermissionManager` re-evaluates the request as if it were a direct call to that virtual tool.
4. If the virtual operation is more restrictive (e.g., a `deny` rule exists for `Read` but not for `Bash`), the more restrictive decision wins.

## Summary of "Implicit Trust"
Because `READ_TOOLS` are marked as `allow` at Layer 3, and most users have no `deny` rules in `settings.json` (Layer 4), the agent operates with **Implicit Trust**. The LLM is free to request any file on the system, and the Gatekeeper will permit the operation as long as the OS user has the required permissions.
