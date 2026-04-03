---
title: "Session History in Qwen Code"
type: guide
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
description: Technical reference on Qwen Code's JSONL-based session history format — data structures, write mechanisms, compression, and session management.
tags: [workflow, architecture]
date: 2026-04-03
options:
  version: 0.1.0
  birth: 2026-04-03
---

# Session History in Qwen Code

**Version:** Qwen Code v0.14.1

## Format: JSONL (JSON Lines)

One JSON object per line, append-only. Crash-safe by design — records are never rewritten.

**File path:**
```
~/.qwen/tmp/projects/<sanitized-cwd-hash>/chats/{sessionId}.jsonl
```

**File naming:** `{sessionId}.jsonl` where `sessionId` is a 32-36 char hex UUID.

---

## Data Structure: `ChatRecord`

Each line is a `ChatRecord` object (defined in `packages/core/src/services/chatRecordingService.ts`):

```typescript
interface ChatRecord {
  uuid: string;                    // unique message ID
  parentUuid: string | null;       // parent link → TREE structure (enables branching/checkpointing)
  sessionId: string;               // groups records into a session
  timestamp: string;               // ISO 8601
  type: 'user' | 'assistant' | 'tool_result' | 'system';
  subtype?: 'chat_compression' | 'slash_command' | 'ui_telemetry' | 'at_command';
  cwd: string;
  version: string;                 // CLI version
  message?: Content[];             // full API Content object (role + parts)
  usageMetadata?: GenerateContentResponseUsageMetadata;
  model?: string;
  contextWindowSize?: number;
  toolCallResult?: ToolCallResponseInfo;
  systemPayload?: ...;             // compression metrics, slash command data, etc.
}
```

**Key insight:** It's a tree, not a linear log. `uuid`/`parentUuid` links enable future checkpointing and branching. Session loading reconstructs the linear chain by walking `parentUuid` backward from the last record.

---

## Write Mechanism: Immediate, Append-Only

Records are written **immediately on every turn** — not on exit, not on a timer. Uses `fs.appendFileSync()` via `jsonl-utils.ts`:

```typescript
fs.appendFileSync(filePath, `${JSON.stringify(data)}\n`, 'utf8');
```

**When records are written:**

| Event | Triggered From | Record Type |
|-------|---------------|-------------|
| User sends a query | `client.ts` (line ~530) | `user` |
| Model responds | `geminiChat.ts` (line ~721) | `assistant` |
| Tool executes | `coreToolScheduler.ts` (line ~1639) | `tool_result` |
| `/compress` succeeds | `client.ts` (line ~933) | `system` (subtype: `chat_compression`) |
| Slash command runs | `client.ts` | `system` (subtype: `slash_command`) |
| `@file` reference used | `client.ts` | `system` (subtype: `at_command`) |
| Telemetry events | `client.ts` | `system` (subtype: `ui_telemetry`) |

---

## The `/compress` Command

When you run `/compress`:

1. `ChatCompressionService` sends the full chat history to the LLM with a prompt asking it to summarize
2. On success, a `system` record with subtype `chat_compression` is appended to the JSONL file
3. It includes a `compressedHistory` field — a snapshot of the new `Content[]` the model should see going forward
4. **Original UI history records are NOT mutated** — the compression checkpoint allows session resumption to reconstruct the compressed model-facing history

This is an important design pattern: the JSONL is an **immutable append-only event log**. Compression adds a checkpoint record rather than rewriting history.

---

## Session Management: `SessionService`

Located in `packages/core/src/services/sessionService.ts`:

- **`listSessions()`** — scans all `.jsonl` files in the chats dir, reads only the *first line* of each for efficiency
- **`loadSession()`** — reads all records, reconstructs linear history by following `parentUuid` chains backward from the last record
- **`removeSession()`** — deletes the `.jsonl` file

---

## Configuration

```jsonc
// ~/.qwen/settings.json
{
  "general": {
    "chatRecording": true  // default: true; set false to disable
  }
}
```

Disabling this also breaks `--continue` and `--resume` CLI flags.

---

## File Storage: Where Session Files Live

### Full Path Construction

Session files are stored under:

```
<runtime_base_dir>/tmp/projects/<sanitized-cwd>/chats/{sessionId}.jsonl
```

Where each path segment is constructed as follows:

#### 1. Runtime Base Directory (`<runtime_base_dir>`)

Resolved with the following priority:

1. `QWEN_RUNTIME_DIR` environment variable
2. `Storage.setRuntimeBaseDir()` — programmatic override
3. `Storage.getGlobalQwenDir()` → `~/.qwen` (default)

**Default:** `~/.qwen`

#### 2. Sanitized CWD (`<sanitized-cwd>`)

The project's current working directory is transformed into a safe directory name via `sanitizeCwd()` in `packages/core/src/utils/paths.ts`:

- All non-alphanumeric characters are replaced with hyphens: `/home/user/my-project` → `-home-user-my-project`
- On Windows, the path is lowercased first (case-insensitive filesystems)

This sanitized CWD is used as a **project identifier** for directory naming.

#### 3. Project Hash (for cross-project disambiguation)

A separate SHA-256 hash of the raw CWD is computed via `getProjectHash()` — also in `paths.ts`:

```typescript
crypto.createHash('sha256').update(normalizedPath).digest('hex');
```

This hash is used for:
- Filtering session files by project (records store `cwd`, not hash — hash is computed at read time)
- Temp directories, history directories, and other project-scoped artifacts

#### 4. Final File Path

Putting it all together for a typical Linux setup:

```
~/.qwen/tmp/projects/-home-user-my-project/chats/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jsonl
```

### Directory Creation

Directories are created **lazily** on first write:

```typescript
// chatRecordingService.ts — ensureChatsDir()
const chatsDir = path.join(projectDir, 'chats');
fs.mkdirSync(chatsDir, { recursive: true });
```

The `chats/` directory and all parent directories are created with `recursive: true` — no pre-creation during init.

### File Naming Convention

- **Pattern:** `{sessionId}.jsonl`
- **Session ID:** A UUID generated per session (32-36 hex characters, e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- **Validation regex:** `/^[0-9a-fA-F-]{32,36}\.jsonl$/` — used during session listing to filter valid session files

### File Creation (Atomic)

New session files are created atomically to avoid TOCTOU (time-of-check-time-of-use) race conditions:

```typescript
// Use 'wx' flag — exclusive creation, fails if file already exists
fs.writeFileSync(conversationFile, '', { flag: 'wx', encoding: 'utf8' });
```

If the file already exists (concurrent process), the `EEXIST` error is caught and treated as expected.

---

## Session Management: How Sessions Are Managed

### SessionService Overview

Located in `packages/core/src/services/sessionService.ts`, the `SessionService` handles all session lifecycle operations:

- **`listSessions(options)`** — Paginated listing of sessions for the current project
- **`loadSession(sessionId)`** — Load and reconstruct a full conversation from a session file
- **`loadLastSession()`** — Convenience: load the most recent session
- **`removeSession(sessionId)`** — Delete a session file
- **`sessionExists(sessionId)`** — Check if a session file exists and belongs to the current project

### Session Listing (`listSessions`)

**Optimization:** Only reads the **first line** of each JSONL file to extract session metadata.

Process:
1. Scan `chats/` directory for files matching `SESSION_FILE_PATTERN`
2. `fs.statSync()` each file to get `mtime` (modification time)
3. Sort by `mtime` descending (most recent first)
4. Apply cursor-based pagination filter (`mtime < cursor`)
5. For each file, read first N lines via `jsonl.readLines(filePath, MAX_PROMPT_SCAN_LINES)` (default: 10)
6. Verify project ownership via `getProjectHash(firstRecord.cwd) === this.projectHash`
7. Count total messages via `countSessionMessages()` — scans entire file for unique UUIDs
8. Extract first user prompt text for display

**Pagination:**
- Default page size: 20 items
- Cursor-based (uses `mtime` as cursor)
- Safety limit: `MAX_FILES_TO_PROCESS = 10000` files per listing call
- Returns `ListSessionsResult` with `items`, `nextCursor`, and `hasMore` fields

**Why project hash filtering?** Different projects may share the same chats directory due to path sanitization collisions (e.g., two different CWDs that sanitize to the same string). The `cwd` → hash comparison ensures sessions are correctly scoped.

### Session Loading (`loadSession`)

1. Read **all** records from `{sessionId}.jsonl` via `jsonl.read<ChatRecord>()`
2. Verify project ownership (same hash check as listing)
3. **Reconstruct linear history** from tree-structured records:
   - Group records by `uuid` (multiple records can share the same UUID due to split writes — e.g., assistant turn split across `recordAssistantTurn` and `recordToolResult`)
   - Start from the last record (or optional `leafUuid` parameter)
   - Walk backward following `parentUuid` chain until reaching a root (`parentUuid === null`)
   - Detect cycles via `visited` Set
   - Reverse the chain to get chronological order
4. **Aggregate records** with the same UUID:
   - Merge `message` Content objects (combine `parts` arrays)
   - Take latest `usageMetadata`, `model`, `toolCallResult`
   - Update timestamp to latest
5. Return `ResumedSessionData` with reconstructed `ConversationRecord`, file path, and `lastCompletedUuid`

### Session Removal (`removeSession`)

1. Read first line of the target file to verify project ownership
2. If ownership check passes: `fs.unlinkSync(filePath)` — deletes the file
3. Returns `true` if removed, `false` if file not found or wrong project

### API History Construction (`buildApiHistoryFromConversation`)

When resuming a session, the model-facing history (`Content[]`) is built from the reconstructed conversation:

1. Find the **latest** `system`/`chat_compression` record
2. If found: use its `compressedHistory` snapshot as the base, then append all post-compression messages
3. If not found: return the full linear message list
4. Optionally strip `thought: true` parts from the history (default: enabled)

### UI Telemetry Replay (`replayUiTelemetryFromConversation`)

On session resume, stored UI telemetry events are replayed from `system`/`ui_telemetry` records to restore metrics state. The last prompt token count is also restored from either:
- The compression checkpoint's `newTokenCount` (preferred)
- The last assistant record's `usageMetadata` (fallback)

---

## Garbage Collection: Session File Lifecycle

### No Automatic Garbage Collection

**Session JSONL files accumulate on disk indefinitely.** There is no automatic garbage collection, scheduled cleanup, or staleness-based removal of old session files.

This is a deliberate design choice aligned with the append-only, immutable event log philosophy: if sessions can always be resumed from disk, they should never be silently deleted.

### What Does NOT Exist

| Mechanism | Status |
|-----------|--------|
| Automatic deletion of old sessions | **None** |
| Scheduled/periodic cleanup | **None** |
| TTL, max-age, or retention configuration | **None** |
| Max-sessions limit per project | **None** |
| Startup-time stale session scan | **None** |
| Session file size/age limits | **None** |

The closest settings are unrelated to retention:
- `maxSessionTurns` — limits turns **within a live session** (prevents infinite agent loops), not on-disk retention
- `sessionTokenLimit` — limits tokens in the **context window**, not stored sessions
- `chatRecording` — enables/disables recording entirely; disabling breaks `--continue`/`--resume`

### Manual Deletion Only

Sessions are removed only through **explicit user action**:

1. **`SessionService.removeSession(sessionId)`** — deletes the `.jsonl` file after verifying project ownership
2. **`/clear` slash command** — clears the current conversation (may trigger session removal depending on implementation)
3. **IDE-level delete** — VS Code companion (`QwenSessionReader.deleteSession()`, `QwenSessionManager.deleteSession()`) provides manual deletion via the editor UI
4. **Manual filesystem deletion** — users can always delete files directly from `~/.qwen/tmp/projects/<hash>/chats/`

### Safety Limits (Read-Time, Not Cleanup)

A `MAX_FILES_TO_PROCESS = 10000` limit in `SessionService.listSessions()` prevents performance degradation when the chats directory contains many session files. This is a **read-time guard**, not a cleanup mechanism — it caps how many files are scanned during a single listing call, but never deletes anything.

### Implications

- **Long-running projects** with many sessions will accumulate many `.jsonl` files in the `chats/` directory
- **Disk usage** grows unboundedly unless users manually prune sessions
- The `listSessions()` pagination with `MAX_FILES_TO_PROCESS` ensures the listing UI remains responsive even with thousands of files
- **No session is ever lost** to automatic cleanup — crash or restart always preserves all session data

### Design Trade-off

This is a conscious trade-off: **data durability over disk space efficiency**. The append-only, no-GC design guarantees that:
- No conversation is ever silently discarded
- Session resumption always works if the file exists on disk
- Compression checkpoints survive crashes (they're just appended records, not rewritten files)

The cost is that disk space grows unboundedly — a problem users must manage manually, or that a future version of Qwen Code may address with an explicit retention policy.

---

## Key Files

| File | Role |
|------|------|
| `packages/core/src/services/chatRecordingService.ts` | Main service — writes records to JSONL |
| `packages/core/src/services/sessionService.ts` | Lists, loads, removes session files; builds API history |
| `packages/core/src/utils/jsonl-utils.ts` | Low-level JSONL read/write (`appendFileSync`, mutex-locked) |
| `packages/core/src/core/client.ts` | Orchestrates recording calls |
| `packages/core/src/config/config.ts` | `getTranscriptPath()` — constructs file path |
| `packages/core/src/config/storage.ts` | `getProjectDir()` — builds project dir path; resolves runtime base dir |
| `packages/core/src/utils/paths.ts` | `sanitizeCwd()`, `getProjectHash()` — path hashing/sanitization |
