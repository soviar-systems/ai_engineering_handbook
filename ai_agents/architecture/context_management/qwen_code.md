---
title: "Context Management \u2014 Qwen-Code"
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-04-05'
description: "Deep dive into Qwen-Code's context management \u2014 autocompact buffer,\
  \ /compress command, token limits registry, and JSONL-backed session history reconstruction."
tags:
- architecture
- agents
options:
  version: 1.0.0
  birth: '2026-04-05'
  type: guide
  token_size: 2053
---

# Context Management — Qwen-Code

**Agent version:** v0.14.0 (commit `e8552294`)
**Analysis date:** 2026-04-05

:::{note}
This document focuses on Qwen-Code's **context window management** — the `/compress` mechanism, autocompact buffer, token limits, and history reconstruction. For the JSONL session format, file storage, and session management mechanics, see [Session History in Qwen Code](/ai_agents/architecture/session_history_management/session_history_in_qwen_code.md).
:::

## Architecture Overview

Qwen-Code maintains a `Content[]` history array in memory. On every API call, the **full curated history** is sent via `generateContentStream()`. There is no chunking, no delta-based updates, and no server-side session persistence.

The flow:
1. User message added to history
2. `getHistory(true)` returns the **curated history** — cleaned version with invalid/empty model outputs filtered out
3. Full history sent via `generateContentStream()` with `contents: requestContents`

**Key file:** `packages/core/src/core/geminiChat.ts` (lines ~340–365)

## History Curation: `extractCuratedHistory`

```typescript
function extractCuratedHistory(comprehensiveHistory: Content[]): Content[] {
  const curatedHistory: Content[] = []
  const length = comprehensiveHistory.length
  let i = 0
  while (i < length) {
    if (comprehensiveHistory[i].role === 'user') {
      curatedHistory.push(comprehensiveHistory[i])
      i++
    } else {
      const modelOutput: Content[] = []
      let isValid = true
      while (i < length && comprehensiveHistory[i].role === 'model') {
        modelOutput.push(comprehensiveHistory[i])
        if (isValid && !isValidContent(comprehensiveHistory[i])) {
          isValid = false
        }
        i++
      }
      if (isValid) {
        curatedHistory.push(...modelOutput)
      }
    }
  }
  return curatedHistory
}
```

Filters out invalid/empty model outputs, keeps clean user messages.

**Key file:** `packages/core/src/core/geminiChat.ts` (lines ~170–195)

## Context Window Sizes

Context windows defined via regex pattern matching on model names:

- Qwen3-coder-plus/flash: 1M tokens
- Qwen3-coder-*: 256K tokens
- Claude: 200K tokens
- GPT-5: 272K input (400K total − 128K output)
- Default fallback: 131,072 (128K)

```typescript
export const DEFAULT_TOKEN_LIMIT: TokenCount = 131_072  // 128K (power-of-two)
```

These are also overridable per-model in settings (`contextWindowSize` config field).

**Key file:** `packages/core/src/core/tokenLimits.ts`

## The Autocompact Buffer

```typescript
const DEFAULT_COMPRESSION_THRESHOLD = 0.7  // triggers compression at 70%

const autocompactBuffer = Math.round((1 - compressionThreshold) * contextWindowSize)
```

This reserves ~30% of the context window as a buffer to prevent the model from hitting the hard limit.

**Key file:** `packages/cli/src/ui/commands/contextCommand.ts` (lines ~33, ~219)

## Context Overhead Accounting

The `/context` command breaks down usage into categories:

1. **System prompt** tokens
2. **Tool declarations** (all tools: built-in, MCP, skills) — JSON schema tokens
3. **Memory files** (user memory content)
4. **Skills** (tool definition + loaded skill bodies)
5. **Messages** (conversation history tokens = total − overhead)
6. **Free space** = contextWindowSize − totalTokens − autocompactBuffer

## Compression: `/compress` Command

**Key file:** `packages/core/src/services/chatCompressionService.ts`

### Constants

```typescript
COMPRESSION_TOKEN_THRESHOLD = 0.7    // triggers at 70%
COMPRESSION_PRESERVE_THRESHOLD = 0.3 // keeps last 30%
MIN_COMPRESSION_FRACTION = 0.05      // minimum compressible content
```

### Algorithm

1. **Trigger**: When `originalTokenCount >= 0.7 * contextWindowSize` (or manual `/compress` command)

2. **Split the history**: Uses `findCompressSplitPoint()` to determine where to split, preserving the last 30% of the conversation (by character count, counting only user messages as valid split points)

3. **Summarize the old portion**: Sends the older history to the model with a compression prompt:
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
       systemInstruction: getCompressionPrompt(),
     },
   })
   ```

4. **Replace with summary**:
   ```typescript
   extraHistory = [
     { role: 'user', parts: [{ text: summary }] },
     { role: 'model', parts: [{ text: 'Got it. thanks for the additional context!' }] },
     ...historyToKeep,  // The last 30%
   ]
   ```

5. **Token math**: Uses model-reported token counts from the compression API call:
   ```typescript
   newTokenCount = Math.max(
     0,
     originalTokenCount - (compressionInputTokenCount - 1000) + compressionOutputTokenCount,
   )
   ```
   (The `-1000` accounts for the compression prompt and scratchpad instruction overhead.)

6. **Guards**:
   - Won't compress if compressible portion < 5% of total (futile)
   - Won't proceed if the summary is empty
   - Won't proceed if compression would increase token count
   - Won't re-attempt after a failed compression unless forced manually

### Compression Checkpoint in JSONL

On success, a `system` record with subtype `chat_compression` is appended to the JSONL file with a `compressedHistory` field — a snapshot of the new `Content[]` the model should see going forward.

**Original UI history records are NOT mutated** — the compression checkpoint allows session resumption to reconstruct the compressed model-facing history.

See [Session History in Qwen Code](/ai_agents/architecture/session_history_management/session_history_in_qwen_code.md) for the full JSONL format details.

## API History Reconstruction

When resuming a session, the model-facing history is built from the JSONL records:

```typescript
function buildApiHistoryFromConversation(records: ChatRecord[]): Content[] {
  // Find the latest compression checkpoint
  const lastCompression = findLast(records, r =>
    r.type === 'system' && r.subtype === 'chat_compression'
  )

  if (lastCompression?.systemPayload?.compressedHistory) {
    // Use the checkpoint as base, append everything after it
    const baseHistory = lastCompression.systemPayload.compressedHistory
    const postCompressionRecords = records.slice(
      records.indexOf(lastCompression) + 1
    )
    return [...baseHistory, ...recordsToContent(postCompressionRecords)]
  }

  // No compression — return full history
  return recordsToContent(records)
}
```

Optionally strip `thought: true` parts from the history (default: enabled).

See [Session History in Qwen Code](/ai_agents/architecture/session_history_management/session_history_in_qwen_code.md) for the full JSONL format details.

## Orphaned Entry Stripping

When a model crashes or the user interrupts, `stripOrphanedUserEntriesFromHistory()` cleans up trailing user entries that have no model response.

## Thought Filtering

`stripThoughtsFromHistory()` removes model thinking/reasoning parts (`thought: true`) from history before sending, since those are not part of the actual response content.

## Rate Limit Retries

Up to 10 retries with 60s delays for throttling errors (`RATE_LIMIT_RETRY_OPTIONS`).

## Transient Stream Anomaly Retries

Up to 2 retries with incremental delays for streams that end without a finish reason or with no response text.

## Key Files

| File | Role |
|------|------|
| `packages/core/src/core/geminiChat.ts` | Main chat API — `sendMessageStream()`, `getHistory()`, curation |
| `packages/core/src/core/tokenLimits.ts` | Per-model context window sizes via regex matching |
| `packages/core/src/services/chatCompressionService.ts` | `/compress` command — split, summarize, replace |
| `packages/cli/src/ui/commands/contextCommand.ts` | `/context` command — overhead accounting, autocompact buffer |
| `packages/core/src/services/sessionService.ts` | Session listing, loading, API history reconstruction |
| `packages/core/src/services/chatRecordingService.ts` | JSONL record writing (append-only) |
