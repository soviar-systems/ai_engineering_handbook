# Qwen Code CLI Session Resume Analysis

## Overview
This analysis examines how the Qwen Code CLI reads and reconstructs session data when running `qwen --resume <sessionId>`.

## Core Session Loading Logic

### 1. `packages/core/src/services/sessionService.ts`
- **`loadSession()`** - Main session loading function
- **`getResumePromptTokenCount()`** - Token counting for resume
- **Session data retrieval logic**

### 2. `packages/core/src/core/client.ts`
- **`getResumedSessionData()`** - Retrieves resumed session data
- **`buildApiHistoryFromConversation()`** - Converts session to API history
- **Session reconstruction logic**

### 3. `packages/core/src/services/chatRecordingService.ts`
- Chat recording for replay on resume
- Session data storage format
- UI telemetry event recording for replaying metrics on resume

## CLI Resume Command Implementation

### 4. `packages/cli/src/ui/commands/resumeCommand.ts`
- Resume command definition and action
- Dialog handling for session picker

### 5. `packages/cli/src/ui/hooks/useResumeCommand.ts`
- Hook for resume command execution
- Session selection logic

### 6. `packages/cli/src/ui/utils/resumeHistoryUtils.ts`
- **`buildResumedHistoryItems()`** - Converts session data to UI history
- History reconstruction utilities

## Configuration & Validation

### 7. `packages/cli/src/config/config.ts`
- Resume flag parsing (`argv.resume`)
- Session ID validation
- Error handling for missing sessions
- Validation: Cannot use both `--continue` and `--resume` together
- Validation: Cannot use `--session-id` with `--continue` or `--resume`
- Error: Invalid `--resume` must be a valid UUID

## UI Components

### 8. `packages/cli/src/ui/components/SessionSummaryDisplay.tsx`
- Session summary display for resume
- Shows resume command suggestion
- Only shows resume message if there were messages in the session AND chat recording is enabled

## Transport Layer

### 9. `packages/sdk-typescript/src/transport/ProcessTransport.ts`
- Passes `--resume` flag to subprocess
- Session ID forwarding

## Session Data Format (CRITICAL)

### 10. Actual session JSONL files
- Need to determine where they are stored
- Need to examine what fields are included
- Need to understand how conversation history is structured
- Need to identify what metadata is preserved during resume

## Key Observations from Grep Output

### Session Sources
- Session events tracked: `startup`, `resume`, `clear`, `compact`
- Hook matchers: `^(startup|resume)$` - Only match startup and resume sources

### Session ID Handling
- Session ID format: UUID (e.g., "123e4567-e89b-12d3-a456-426614174000")
- CLI rejects using `--session-id` with `--resume` or `--continue`
- SDK TypeScript accepts `resume?: string` option equivalent to CLI's `--resume` flag

### Chat Recording Dependency
- Chat recording must be enabled for `--resume` to work
- Config toggle: `{ "general": { "chatRecording": true } }`
- Disabling breaks `--continue` and `--resume`

### MCP Server Integration
- Session resumption connects to specified MCP servers
- Streams entire conversation history back to client via notifications
- Requires `loadSession` capability from agent

## Files to Add for Complete Analysis

1. `packages/core/src/services/sessionService.ts`
2. `packages/core/src/core/client.ts`
3. `packages/core/src/services/chatRecordingService.ts`
4. `packages/cli/src/ui/commands/resumeCommand.ts`
5. `packages/cli/src/ui/hooks/useResumeCommand.ts`
6. `packages/cli/src/ui/utils/resumeHistoryUtils.ts`
7. `packages/cli/src/config/config.ts`
8. `packages/cli/src/ui/components/SessionSummaryDisplay.tsx`
9. `packages/sdk-typescript/src/transport/ProcessTransport.ts`
10. Sample session JSONL files (if available)

## Next Steps

Once the above files are added, I can:
- Analyze the exact JSONL file format
- Trace the complete session reconstruction flow
- Identify all metadata preserved during resume
- Understand how agent context is restored
- Document the complete session resume mechanism
