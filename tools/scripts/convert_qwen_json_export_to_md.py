#!/usr/bin/env python3
"""
Convert Qwen chat export JSON to S-YYNNN evidence source artifacts.

Scope: Parses Qwen/Open WebUI chat export JSON, reconstructs conversation
thread order, extracts user and assistant content, generates a markdown
source file with YAML frontmatter conforming to evidence.conf.json.

Does NOT validate the generated frontmatter (that is check_evidence.py's job).
Does NOT process multiple chats from a single export (uses first chat only).

Public interface:
    parse_export(data) — parse raw JSON list into ParsedChat
    generate_frontmatter(parsed, artifact_id, title_override) — YAML block
    generate_markdown(parsed) — dialogue body
    generate_source_file(parsed, artifact_id, title_override) — full output
    main(argv) — CLI entry point

Exit codes:
    0: Success (file written, or dry-run output printed)
    1: Error (missing file, invalid JSON, parse failure)

Dependencies:
    - json, argparse, pathlib (stdlib only — no third-party deps)
    - tools.scripts.git (detect_repo_root, get_historical_paths)
    - tools.scripts.paths (get_config_path)
    - tools.scripts.format_string (format_string) — slug generation
    - .vadocs/types/evidence.conf.json — sources directory path

Key design decisions:
    - Thread order from parentId/childrenIds chain, not dict iteration order
    - Assistant content from content_list[phase="answer"], NOT top-level content
      (which is always empty in Qwen exports — see format docs in test file)
    - Slug generation delegates to format_string.py (C5: Reuse Before Invention)
    - Sources directory resolved from evidence config, not hardcoded
    - Next S-YYNNN ID from git history (deleted sources still count)
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants — resolved from .vadocs/types/evidence.conf.json
# ---------------------------------------------------------------------------
# Same config-driven pattern as check_evidence.py.
# Loaded once at import time. Falls back to defaults outside the repo.

_EVIDENCE_DIR_DEFAULT = "architecture/evidence"
_SOURCES_SUBDIR_DEFAULT = "sources"

try:
    from tools.scripts.git import detect_repo_root
    from tools.scripts.paths import get_config_path

    REPO_ROOT: Path = detect_repo_root()
    _config_path = get_config_path(REPO_ROOT, "evidence")
    with open(_config_path, encoding="utf-8") as _f:
        _evidence_config = json.load(_f)
    EVIDENCE_DIR: str = _evidence_config.get("evidence_dir", _EVIDENCE_DIR_DEFAULT)
    SOURCES_SUBDIR: str = (
        _evidence_config.get("artifact_types", {})
        .get("source", {})
        .get("directory_name", _SOURCES_SUBDIR_DEFAULT)
    )
except Exception:
    REPO_ROOT = Path(".")
    EVIDENCE_DIR = _EVIDENCE_DIR_DEFAULT
    SOURCES_SUBDIR = _SOURCES_SUBDIR_DEFAULT

SOURCES_DIR_REL: str = f"{EVIDENCE_DIR}/{SOURCES_SUBDIR}"
SOURCES_DIR: Path = REPO_ROOT / SOURCES_DIR_REL


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised when the Qwen export JSON has invalid or missing structure."""


@dataclass
class Attachment:
    """File attachment on a user message."""

    name: str
    file_type: str


@dataclass
class Message:
    """A single message extracted from the Qwen thread."""

    role: str
    content: str
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class ParsedChat:
    """Fully parsed chat ready for source file generation."""

    title: str
    messages: list[Message]
    model: str
    date: datetime  # date object (from earliest timestamp)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Convert Qwen chat export JSON to S-YYNNN source artifact."
    )
    parser.add_argument("input_file", help="Path to Qwen export JSON file")
    parser.add_argument(
        "--id",
        dest="artifact_id",
        default=None,
        help="S-YYNNN ID (auto-detected from existing sources if omitted)",
    )
    parser.add_argument("--title", default=None, help="Override chat title")
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Output directory (default: {SOURCES_DIR_REL}/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output to stdout instead of writing a file",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    try:
        raw_data = json.loads(input_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error("Failed to parse JSON from %s: %s", input_path, exc)
        return 1

    try:
        parsed = parse_export(raw_data)
    except ParseError as exc:
        logger.error("Invalid Qwen export structure: %s", exc)
        return 1

    artifact_id = args.artifact_id
    if artifact_id is None:
        artifact_id = _next_source_id()
        logger.info("Auto-detected next ID: %s", artifact_id)

    output = generate_source_file(
        parsed, artifact_id=artifact_id, title_override=args.title
    )

    if args.dry_run:
        print(output)
        return 0

    output_dir = Path(args.output_dir) if args.output_dir else SOURCES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    title_for_slug = args.title or parsed.title
    slug = _slugify(title_for_slug)
    output_path = output_dir / f"{artifact_id}_{slug}.md"

    output_path.write_text(output, encoding="utf-8")
    logger.info("Written: %s", output_path)
    return 0


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_export(data: list[dict]) -> ParsedChat:
    """Parse Qwen export JSON into a structured ParsedChat.

    Args:
        data: The raw JSON data (must be a list with at least one chat object).

    Returns:
        ParsedChat with title, ordered messages, model name, and date.

    Raises:
        ParseError: If the data structure is invalid or missing required fields.
    """
    if not isinstance(data, list) or len(data) == 0:
        raise ParseError(
            "Empty or non-list export. "
            "Qwen export root must be a JSON array with at least one chat object."
        )

    chat_obj = data[0]

    if "chat" not in chat_obj:
        raise ParseError(
            f"Missing 'chat' key in export object. "
            f"Available keys: {list(chat_obj.keys())}. "
            f"Expected Qwen export structure: [{{chat: {{history: ...}}}}]"
        )

    chat = chat_obj["chat"]
    if "history" not in chat:
        raise ParseError(
            f"Missing 'history' key in chat object. "
            f"Available keys: {list(chat.keys())}. "
            f"IMPORTANT: Use chat.history.messages (full content), "
            f"NOT chat.messages (summary view with empty assistant content)."
        )

    title = chat_obj.get("title", "Untitled Chat")
    messages_dict = chat["history"].get("messages", {})

    ordered_messages = _reconstruct_thread(messages_dict)
    model = _detect_model(ordered_messages, messages_dict)
    date = _extract_date(messages_dict)

    return ParsedChat(
        title=title,
        messages=ordered_messages,
        model=model,
        date=date,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_frontmatter(
    parsed: ParsedChat,
    artifact_id: str,
    title_override: str | None = None,
) -> str:
    """Generate YAML frontmatter block for an S-YYNNN source file."""
    title = title_override or parsed.title
    date_str = parsed.date.isoformat() if parsed.date else "unknown"
    lines = [
        "---",
        f"id: {artifact_id}",
        f'title: "{title}"',
        f"date: {date_str}",
        f"model: {parsed.model}",
        "extracted_into: null",
        "---",
    ]
    return "\n".join(lines) + "\n"


def generate_markdown(parsed: ParsedChat) -> str:
    """Generate dialogue body as markdown with ### User / ### Assistant sections."""
    parts = []
    for msg in parsed.messages:
        header = f"### {'User' if msg.role == 'user' else 'Assistant'}"
        parts.append(header)
        parts.append("")

        if msg.attachments:
            for att in msg.attachments:
                parts.append(f"> Attached: {att.name} ({att.file_type})")
            parts.append("")

        if msg.content:
            parts.append(msg.content)
        parts.append("")

    return "\n".join(parts)


def generate_source_file(
    parsed: ParsedChat,
    artifact_id: str,
    title_override: str | None = None,
) -> str:
    """Generate complete S-YYNNN source file: frontmatter + dialogue body."""
    frontmatter = generate_frontmatter(parsed, artifact_id, title_override)
    body = generate_markdown(parsed)
    return frontmatter + "\n" + body


# ---------------------------------------------------------------------------
# Thread reconstruction helpers
# ---------------------------------------------------------------------------


def _reconstruct_thread(messages_dict: dict) -> list[Message]:
    """Walk parentId/childrenIds chain to produce ordered message list.

    Finds root message (parentId=None), then follows childrenIds[0]
    until no more children. Each message is converted to a Message dataclass.
    """
    if not messages_dict:
        return []

    # Find root: the message with parentId=None
    root_id = None
    for msg_id, msg in messages_dict.items():
        if msg.get("parentId") is None:
            root_id = msg_id
            break

    if root_id is None:
        # Fallback: use first message in dict (shouldn't happen in valid exports)
        root_id = next(iter(messages_dict))
        logger.warning(
            "No root message (parentId=None) found. Using first message: %s", root_id
        )

    ordered = []
    current_id = root_id
    visited = set()

    while current_id and current_id in messages_dict:
        if current_id in visited:
            logger.warning("Cycle detected in thread at message %s", current_id)
            break
        visited.add(current_id)

        raw_msg = messages_dict[current_id]
        message = _extract_message(raw_msg)
        ordered.append(message)

        children = raw_msg.get("childrenIds", [])
        current_id = children[0] if children else None

    return ordered


def _extract_message(raw_msg: dict) -> Message:
    """Convert a raw Qwen message dict to a Message dataclass."""
    role = raw_msg.get("role", "unknown")

    if role == "assistant":
        content = _extract_assistant_content(raw_msg)
    else:
        content = raw_msg.get("content", "")

    attachments = _extract_attachments(raw_msg)

    return Message(role=role, content=content, attachments=attachments)


def _extract_assistant_content(raw_msg: dict) -> str:
    """Extract content from assistant message's content_list.

    Only includes items where phase="answer". Skips "thinking_summary"
    and "web_search" phases. Concatenates multiple answer items with
    double newline separator.
    """
    content_list = raw_msg.get("content_list", [])
    answer_parts = []

    for item in content_list:
        phase = item.get("phase", "")
        # Only include answer-phase content; skip thinking_summary, web_search
        if phase == "answer":
            text = item.get("content", "")
            if text:
                answer_parts.append(text)

    return "\n\n".join(answer_parts)


def _extract_attachments(raw_msg: dict) -> list[Attachment]:
    """Extract file attachments from a user message's files array."""
    files = raw_msg.get("files", [])
    attachments = []
    for f in files:
        name = f.get("name", "unknown")
        file_type = f.get("file_type", "unknown")
        attachments.append(Attachment(name=name, file_type=file_type))
    return attachments


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------


def _detect_model(ordered_messages: list[Message], messages_dict: dict) -> str:
    """Detect model name from first assistant message in the raw dict.

    Prefers modelName (human-readable), falls back to model (API ID).
    Returns 'unknown' if no assistant messages found.
    """
    for raw_msg in messages_dict.values():
        if raw_msg.get("role") == "assistant":
            model_name = raw_msg.get("modelName")
            if model_name:
                return model_name
            model_id = raw_msg.get("model")
            if model_id:
                return model_id
    return "unknown"


def _extract_date(messages_dict: dict) -> datetime:
    """Extract date from earliest timestamp across all messages."""
    timestamps = [
        msg.get("timestamp", float("inf"))
        for msg in messages_dict.values()
        if msg.get("timestamp") is not None
    ]
    if not timestamps:
        return datetime.now(tz=timezone.utc).date()

    earliest = min(timestamps)
    return datetime.fromtimestamp(earliest, tz=timezone.utc).date()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert title text to a filename-safe slug.

    Delegates to format_string.format_string() with truncation enabled.
    Falls back to simple regex if format_string is not importable.
    """
    try:
        from tools.scripts.format_string import format_string

        return format_string(text, trunc=True)
    except ImportError:
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        return slug.strip("_")


def _next_source_id() -> str:
    """Auto-detect next S-YYNNN ID from git history + filesystem.

    Uses git.get_historical_paths() to find all S-YYNNN filenames that ever
    existed (including deleted sources — Evidence Source Hygiene means the
    filesystem alone would miss retired IDs and cause collisions).
    Also checks uncommitted files on the filesystem.
    """
    from tools.scripts.git import get_historical_paths

    historical = get_historical_paths(SOURCES_DIR_REL)

    # Also check current filesystem for uncommitted files
    current = set()
    if SOURCES_DIR.exists():
        current = {p.name for p in SOURCES_DIR.glob("S-*")}

    all_names = {Path(p).name for p in historical} | current

    # Extract numeric IDs: S-26018 → 26018
    max_num = 0
    for fname in all_names:
        match = re.search(r"S-(\d+)", fname)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    next_num = max_num + 1
    return f"S-{next_num}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
