"""
Test suite for convert_qwen_json_export_to_md.py — Qwen JSON export to S-YYNNN markdown source.

Scope: Validates JSON parsing, thread reconstruction, content extraction,
frontmatter generation, and CLI behavior. Does NOT test actual file I/O
against the filesystem (uses tmp_path fixtures).

What belongs here: unit tests for the parser, formatter, and CLI.
What does NOT belong here: integration tests against real Qwen exports
(those would go in test_integration.py if needed), or tests for downstream
consumers (check_evidence.py validates the generated S-YYNNN files).

Naming convention: one test class per public function / concern area.

Contracts tested:
- TestQwenJsonParsing: parse_export() accepts Qwen JSON array, returns ParsedChat
- TestThreadReconstruction: messages ordered by parentId/childrenIds chain
- TestContentExtraction: user content from 'content', assistant from content_list
  answer phase, attachments from files[]
- TestModelDetection: model name from first assistant's modelName field
- TestDateExtraction: date from earliest message timestamp
- TestFrontmatterGeneration: generate_frontmatter() → valid YAML block
- TestMarkdownOutput: generate_markdown() → ### User / ### Assistant sections
- TestFullOutput: generate_source_file() → frontmatter + body combined
- TestCLI: main() exit codes, file creation, argument handling

Dependencies:
    - tools.scripts.convert_qwen_export (module under test)
    - pytest, tmp_path
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import tools.scripts.convert_qwen_json_export_to_md as _module


# ---------------------------------------------------------------------------
# Fixtures: minimal Qwen export structures
# ---------------------------------------------------------------------------
#
# Qwen chat export format (Open WebUI / Qwen Cloud):
#
# Root: list[dict] — each item is one chat session (usually 1)
#
# Chat object structure:
#   [0].title           — chat title (string)
#   [0].chat.history.messages — dict[UUID, MessageDict] (FULL content)
#   [0].chat.messages         — list[MessageDict] (SUMMARY — assistant content EMPTY)
#
# IMPORTANT: Always use chat.history.messages, never chat.messages.
# The history dict is UNORDERED — thread order comes from parentId/childrenIds.
#
# User message fields:
#   role: "user"
#   content: str              — the actual user text
#   files: list[FileDict]     — attachments (name, file_type, type, size, url)
#   parentId: str | None      — None for root message
#   childrenIds: list[str]    — UUIDs of child messages
#   timestamp: int            — Unix epoch seconds
#
# Assistant message fields:
#   role: "assistant"
#   content: str              — ALWAYS EMPTY STRING (Qwen quirk!)
#   content_list: list[dict]  — actual responses, each with:
#     .content: str           — the text (this is where the answer lives)
#     .phase: str             — "thinking_summary" | "answer" | "web_search"
#     .status: str            — "finished" etc.
#   modelName: str            — human-readable model name (e.g., "Qwen3.5-Plus")
#   model: str                — model ID (e.g., "qwen3.5-plus")
#   parentId: str             — UUID of parent (always set for assistants)
#   childrenIds: list[str]    — UUID of next message
#   timestamp: int            — Unix epoch seconds
#
# Thread reconstruction: find root (parentId=None), follow childrenIds[0].


def _make_message(
    msg_id,
    role,
    content="",
    parent_id=None,
    children_ids=None,
    model_name=None,
    model=None,
    content_list=None,
    files=None,
    timestamp=1774807312,
):
    """Build a minimal Qwen message dict.

    Mirrors the real Qwen export structure. Only includes fields that the
    parser actually reads — see format docs above for the full field set.
    """
    msg = {
        "id": msg_id,
        "role": role,
        "content": content,
        "parentId": parent_id,
        "childrenIds": children_ids or [],
        "timestamp": timestamp,
    }
    if role == "assistant":
        # modelName is the human-readable name; model is the API ID.
        # Parser prefers modelName, falls back to model.
        msg["modelName"] = model_name or "Qwen3.5-Plus"
        msg["model"] = model or "qwen3.5-plus"
        msg["content_list"] = content_list or []
    if role == "user":
        msg["files"] = files or []
    return msg


def _make_export(messages_dict, title="Test Chat"):
    """Wrap messages dict into a full Qwen export structure.

    The real export has many more fields (user_id, share_id, meta, etc.)
    but only these are used by the parser.
    """
    return [
        {
            "id": "chat-001",
            "title": title,
            "chat": {
                "history": {
                    "messages": messages_dict,
                    "currentId": None,
                },
                # chat.messages is the summary view — assistant content is always
                # empty here. The parser must use chat.history.messages instead.
                "messages": [],
                "models": [],
            },
            "created_at": 1774807300,
            "updated_at": 1774807400,
        }
    ]


def _simple_two_turn():
    """Two-turn conversation: user → assistant → user → assistant.

    Thread chain: msg-u1 → msg-a1 → msg-u2 → msg-a2
    msg-a1 has both thinking_summary (empty) and answer phases.
    msg-a2 has answer phase only.
    """
    msgs = {
        "msg-u1": _make_message(
            "msg-u1",
            "user",
            content="What is ACH?",
            children_ids=["msg-a1"],
            timestamp=1774807312,
        ),
        "msg-a1": _make_message(
            "msg-a1",
            "assistant",
            parent_id="msg-u1",
            children_ids=["msg-u2"],
            content_list=[
                # thinking_summary phase — should be skipped by parser
                {"content": "", "phase": "thinking_summary", "status": "finished"},
                # answer phase — this is the actual response
                {
                    "content": "ACH is Analysis of Competing Hypotheses.",
                    "phase": "answer",
                    "status": "finished",
                },
            ],
            timestamp=1774807320,
        ),
        "msg-u2": _make_message(
            "msg-u2",
            "user",
            content="How does it work?",
            parent_id="msg-a1",
            children_ids=["msg-a2"],
            timestamp=1774807330,
        ),
        "msg-a2": _make_message(
            "msg-a2",
            "assistant",
            parent_id="msg-u2",
            content_list=[
                {
                    "content": "You list hypotheses and test evidence against each.",
                    "phase": "answer",
                    "status": "finished",
                },
            ],
            timestamp=1774807340,
        ),
    }
    return _make_export(msgs, title="ACH Discussion")


# ---------------------------------------------------------------------------
# TestQwenJsonParsing
# ---------------------------------------------------------------------------


class TestQwenJsonParsing:
    """Contract: parse_export() accepts Qwen JSON array, returns ParsedChat.

    ParsedChat must have: title, messages, model, date.
    Raises ParseError on invalid/missing structure.
    """

    def test_parses_valid_export(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result is not None, (
            "parse_export() returned None for valid two-turn export"
        )

    def test_extracts_chat_title(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result.title == "ACH Discussion", (
            f"Expected title 'ACH Discussion', got '{result.title}'. "
            "Title comes from [0].title in the export JSON."
        )

    def test_rejects_empty_list(self):
        with pytest.raises(_module.ParseError, match="[Ee]mpty"):
            _module.parse_export([])

    def test_rejects_missing_chat_key(self):
        """Export item without 'chat' key → ParseError."""
        export = [{"id": "x", "title": "t"}]
        with pytest.raises(_module.ParseError, match="chat"):
            _module.parse_export(export)

    def test_rejects_missing_history(self):
        """chat dict without 'history' key → ParseError.

        This catches the trap of using chat.messages (summary view with
        empty assistant content) instead of chat.history.messages.
        """
        export = [{"id": "x", "title": "t", "chat": {"messages": []}}]
        with pytest.raises(_module.ParseError, match="history"):
            _module.parse_export(export)

    def test_handles_multiple_chats_uses_first(self):
        """Multiple items in root array — use first chat only.

        Real exports from Open WebUI batch multiple chats into one file.
        """
        export = _simple_two_turn()
        export.append(
            {
                "id": "chat-002",
                "title": "Second Chat",
                "chat": {
                    "history": {"messages": {}, "currentId": None},
                    "messages": [],
                    "models": [],
                },
            }
        )
        result = _module.parse_export(export)
        assert result.title == "ACH Discussion", (
            f"Expected first chat title, got '{result.title}'. "
            "Parser should use export[0], not later items."
        )


# ---------------------------------------------------------------------------
# TestThreadReconstruction
# ---------------------------------------------------------------------------


class TestThreadReconstruction:
    """Contract: messages ordered by parentId/childrenIds chain, not dict order.

    Qwen stores messages in a dict keyed by UUID. Dict iteration order is
    insertion order (Python 3.7+), but this does NOT match conversation order.
    The parser must find root (parentId=None) and walk childrenIds[0].
    """

    def test_reconstructs_linear_thread(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        roles = [m.role for m in result.messages]
        assert roles == ["user", "assistant", "user", "assistant"], (
            f"Thread order wrong: got roles {roles}. "
            "Expected user→assistant→user→assistant. "
            "Check parentId/childrenIds chain walking logic."
        )

    def test_content_order_matches_thread(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result.messages[0].content == "What is ACH?", (
            f"First message content wrong: '{result.messages[0].content}'. "
            "Root message (parentId=None) should be first."
        )
        assert result.messages[2].content == "How does it work?", (
            f"Third message content wrong: '{result.messages[2].content}'. "
            "Thread chain: msg-u1 → msg-a1 → msg-u2 → msg-a2."
        )

    def test_single_message_thread(self):
        msgs = {
            "msg-u1": _make_message("msg-u1", "user", content="Hello"),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert len(result.messages) == 1, (
            f"Expected 1 message, got {len(result.messages)}. "
            "Single root message with no children should work."
        )
        assert result.messages[0].role == "user"

    def test_finds_root_by_null_parent(self):
        """Root message has parentId=None — dict order is irrelevant.

        Here msg-a1 appears first in dict but msg-u1 is the root.
        """
        msgs = {
            # Deliberately put assistant first in dict to test ordering
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                content_list=[
                    {"content": "Response", "phase": "answer", "status": "finished"}
                ],
            ),
            "msg-u1": _make_message(
                "msg-u1", "user", content="Question", children_ids=["msg-a1"]
            ),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert result.messages[0].role == "user", (
            f"First message role is '{result.messages[0].role}', expected 'user'. "
            "Root detection must use parentId=None, not dict insertion order."
        )
        assert result.messages[1].role == "assistant"


# ---------------------------------------------------------------------------
# TestContentExtraction
# ---------------------------------------------------------------------------


class TestContentExtraction:
    """Contract: user content from 'content' field, assistant from content_list.

    Key Qwen format quirk: assistant messages have content="" (empty string)
    at the top level. Actual response text is in content_list[N].content
    where content_list[N].phase == "answer". The "thinking_summary" phase
    contains internal reasoning and must be filtered out.
    """

    def test_user_content_from_content_field(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result.messages[0].content == "What is ACH?", (
            f"User content: '{result.messages[0].content}'. "
            "User messages use the top-level 'content' field directly."
        )

    def test_assistant_content_from_answer_phase(self):
        """Assistant content comes from content_list where phase='answer'."""
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result.messages[1].content == "ACH is Analysis of Competing Hypotheses.", (
            f"Assistant content: '{result.messages[1].content}'. "
            "Must extract from content_list items with phase='answer', "
            "NOT from the top-level content field (always empty for assistants)."
        )

    def test_skips_thinking_summary_phase(self):
        """thinking_summary phase = internal reasoning, must not appear in output."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1", "user", content="Q", children_ids=["msg-a1"]
            ),
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                content_list=[
                    {
                        "content": "Internal reasoning here",
                        "phase": "thinking_summary",
                        "status": "finished",
                    },
                    {
                        "content": "Visible answer",
                        "phase": "answer",
                        "status": "finished",
                    },
                ],
            ),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert result.messages[1].content == "Visible answer", (
            f"Got: '{result.messages[1].content}'. "
            "Only phase='answer' items should be extracted."
        )
        assert "Internal reasoning" not in result.messages[1].content, (
            "thinking_summary content leaked into extracted text. "
            "Filter content_list by phase != 'thinking_summary'."
        )

    def test_assistant_empty_content_list(self):
        """Assistant with no content_list items → empty content string."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1", "user", content="Q", children_ids=["msg-a1"]
            ),
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                content_list=[],
            ),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert result.messages[1].content == "", (
            f"Expected empty content for empty content_list, got: "
            f"'{result.messages[1].content}'"
        )

    def test_concatenates_multiple_answer_phases(self):
        """Multiple answer-phase items → concatenated with separator."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1", "user", content="Q", children_ids=["msg-a1"]
            ),
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                content_list=[
                    {"content": "Part one.", "phase": "answer", "status": "finished"},
                    {"content": "Part two.", "phase": "answer", "status": "finished"},
                ],
            ),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert "Part one." in result.messages[1].content, (
            f"Missing 'Part one.' in: '{result.messages[1].content}'. "
            "Multiple answer phases should be concatenated."
        )
        assert "Part two." in result.messages[1].content, (
            f"Missing 'Part two.' in: '{result.messages[1].content}'. "
            "All answer-phase items must be included."
        )

    def test_detects_file_attachments(self):
        """User messages with files[] → parsed into Attachment dataclasses."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1",
                "user",
                content="Check this file",
                files=[
                    {
                        "name": "report.html",
                        "file_type": "text/html",
                        "type": "file",
                    }
                ],
            ),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert len(result.messages[0].attachments) == 1, (
            f"Expected 1 attachment, got {len(result.messages[0].attachments)}. "
            "Attachments come from user message files[] array."
        )
        assert result.messages[0].attachments[0].name == "report.html", (
            f"Attachment name: '{result.messages[0].attachments[0].name}'. "
            "Should match files[0].name from the Qwen export."
        )
        assert result.messages[0].attachments[0].file_type == "text/html"

    def test_no_attachments_when_no_files(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result.messages[0].attachments == [], (
            f"Expected empty attachments, got {result.messages[0].attachments}. "
            "Messages without files[] should have empty attachment list."
        )


# ---------------------------------------------------------------------------
# TestModelDetection
# ---------------------------------------------------------------------------


class TestModelDetection:
    """Contract: model name from first assistant message's modelName field.

    Falls back to 'model' field if modelName absent. Returns 'unknown'
    if no assistant messages exist (user-only conversation).
    """

    def test_detects_model_from_assistant(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        assert result.model == "Qwen3.5-Plus", (
            f"Model: '{result.model}'. Expected 'Qwen3.5-Plus' from "
            "first assistant message's modelName field."
        )

    def test_fallback_to_model_field(self):
        """If modelName missing, fall back to model (API ID) field."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1", "user", content="Q", children_ids=["msg-a1"]
            ),
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                model="qwen3.5-plus",
                model_name=None,
                content_list=[
                    {"content": "A", "phase": "answer", "status": "finished"}
                ],
            ),
        }
        # Remove modelName to test fallback path
        msgs["msg-a1"].pop("modelName", None)
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert result.model == "qwen3.5-plus", (
            f"Model: '{result.model}'. When modelName is absent, "
            "parser should fall back to the 'model' field."
        )

    def test_no_assistant_messages_model_unknown(self):
        """User-only conversation → model is 'unknown'."""
        msgs = {
            "msg-u1": _make_message("msg-u1", "user", content="Hello"),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        assert result.model == "unknown", (
            f"Model: '{result.model}'. No assistant messages in thread, "
            "so model should be 'unknown'."
        )


# ---------------------------------------------------------------------------
# TestDateExtraction
# ---------------------------------------------------------------------------


class TestDateExtraction:
    """Contract: date derived from earliest message timestamp (Unix epoch)."""

    def test_date_from_earliest_timestamp(self):
        export = _simple_two_turn()
        result = _module.parse_export(export)
        # 1774807312 = the timestamp of msg-u1 (earliest in fixture)
        expected = datetime.fromtimestamp(1774807312, tz=timezone.utc).date()
        assert result.date == expected, (
            f"Date: {result.date}, expected {expected}. "
            f"Should be derived from earliest timestamp (1774807312)."
        )

    def test_date_uses_minimum_across_all_messages(self):
        """Date must be the minimum timestamp, even if later message has earlier time."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1",
                "user",
                content="First",
                children_ids=["msg-a1"],
                timestamp=1774807400,  # later
            ),
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                content_list=[
                    {"content": "A", "phase": "answer", "status": "finished"}
                ],
                timestamp=1774807300,  # earlier
            ),
        }
        export = _make_export(msgs)
        result = _module.parse_export(export)
        expected = datetime.fromtimestamp(1774807300, tz=timezone.utc).date()
        assert result.date == expected, (
            f"Date: {result.date}, expected {expected}. "
            "Must use min(timestamp) across ALL messages, not just the root."
        )


# ---------------------------------------------------------------------------
# TestFrontmatterGeneration
# ---------------------------------------------------------------------------


class TestFrontmatterGeneration:
    """Contract: generate_frontmatter() → YAML block with --- delimiters.

    Required fields per evidence.conf.json: id, title, date, model.
    """

    def test_contains_required_fields(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        fm = _module.generate_frontmatter(parsed, artifact_id="S-26019")
        for field in ("id: S-26019", "title:", "date:", "model:"):
            assert field in fm, (
                f"Missing '{field}' in frontmatter. "
                f"Required by evidence.conf.json. Got:\n{fm}"
            )

    def test_uses_provided_title_override(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        fm = _module.generate_frontmatter(
            parsed, artifact_id="S-26019", title_override="Custom Title"
        )
        assert "Custom Title" in fm, (
            f"Title override not applied. Got:\n{fm}"
        )

    def test_uses_chat_title_when_no_override(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        fm = _module.generate_frontmatter(parsed, artifact_id="S-26019")
        assert "ACH Discussion" in fm, (
            f"Chat title not used as default. Got:\n{fm}"
        )

    def test_frontmatter_delimiters(self):
        """YAML frontmatter must be wrapped in --- delimiters."""
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        fm = _module.generate_frontmatter(parsed, artifact_id="S-26019")
        assert fm.startswith("---\n"), (
            f"Frontmatter must start with '---\\n'. Got: {fm[:20]!r}"
        )
        assert fm.rstrip().endswith("---"), (
            f"Frontmatter must end with '---'. Got: ...{fm[-20:]!r}"
        )


# ---------------------------------------------------------------------------
# TestMarkdownOutput
# ---------------------------------------------------------------------------


class TestMarkdownOutput:
    """Contract: generate_markdown() → dialogue with ### User / ### Assistant headers."""

    def test_contains_user_sections(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        md = _module.generate_markdown(parsed)
        assert "### User" in md, (
            f"Missing '### User' section header in markdown output. "
            f"First 200 chars: {md[:200]!r}"
        )

    def test_contains_assistant_sections(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        md = _module.generate_markdown(parsed)
        assert "### Assistant" in md, (
            f"Missing '### Assistant' section header in markdown output. "
            f"First 200 chars: {md[:200]!r}"
        )

    def test_preserves_message_content(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        md = _module.generate_markdown(parsed)
        assert "What is ACH?" in md, (
            "User message content not preserved in markdown output."
        )
        assert "ACH is Analysis of Competing Hypotheses." in md, (
            "Assistant message content not preserved in markdown output."
        )

    def test_includes_attachment_note(self):
        """File attachments rendered as blockquote notes in markdown."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1",
                "user",
                content="See attached",
                files=[
                    {
                        "name": "data.html",
                        "file_type": "text/html",
                        "type": "file",
                    }
                ],
            ),
        }
        export = _make_export(msgs)
        parsed = _module.parse_export(export)
        md = _module.generate_markdown(parsed)
        assert "data.html" in md, (
            f"Attachment filename not in markdown. Got:\n{md}"
        )
        assert "text/html" in md, (
            f"Attachment file_type not in markdown. Got:\n{md}"
        )

    def test_empty_assistant_content_still_has_section(self):
        """Empty assistant response → section header still present."""
        msgs = {
            "msg-u1": _make_message(
                "msg-u1", "user", content="Q", children_ids=["msg-a1"]
            ),
            "msg-a1": _make_message(
                "msg-a1",
                "assistant",
                parent_id="msg-u1",
                content_list=[],
            ),
        }
        export = _make_export(msgs)
        parsed = _module.parse_export(export)
        md = _module.generate_markdown(parsed)
        assert "### Assistant" in md, (
            "Empty assistant response should still produce a section header. "
            "This preserves the dialogue structure in the source artifact."
        )


# ---------------------------------------------------------------------------
# TestFullOutput
# ---------------------------------------------------------------------------


class TestFullOutput:
    """Contract: generate_source_file() = frontmatter + blank line + markdown body."""

    def test_full_output_starts_with_frontmatter(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        output = _module.generate_source_file(parsed, artifact_id="S-26019")
        assert output.startswith("---\n"), (
            f"Full output must start with frontmatter. Got: {output[:30]!r}"
        )

    def test_full_output_contains_dialogue(self):
        export = _simple_two_turn()
        parsed = _module.parse_export(export)
        output = _module.generate_source_file(parsed, artifact_id="S-26019")
        assert "### User" in output, "Dialogue section headers missing from full output"
        assert "What is ACH?" in output, "Message content missing from full output"


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------


class TestCLI:
    """Contract: main(argv) returns exit codes and writes output files.

    Exit 0: success, file written.
    Exit 1: any error (missing file, bad JSON, invalid structure).
    """

    def test_exit_0_on_valid_input(self, tmp_path):
        export = _simple_two_turn()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(export))

        exit_code = _module.main(
            [str(input_file), "--id", "S-26099", "--output-dir", str(tmp_path)]
        )
        assert exit_code == 0, (
            f"Exit code {exit_code} on valid input. "
            f"Check stderr for error details."
        )

    def test_creates_output_file(self, tmp_path):
        export = _simple_two_turn()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(export))

        _module.main(
            [str(input_file), "--id", "S-26099", "--output-dir", str(tmp_path)]
        )
        output_files = list(tmp_path.glob("S-26099_*.md"))
        assert len(output_files) == 1, (
            f"Expected exactly 1 output file matching S-26099_*.md, "
            f"found {len(output_files)}: {[f.name for f in output_files]}. "
            f"All files in tmp_path: {[f.name for f in tmp_path.iterdir()]}"
        )

    def test_output_filename_contains_slug(self, tmp_path):
        """Output filename: S-YYNNN_<slug_from_title>.md"""
        export = _simple_two_turn()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(export))

        _module.main(
            [str(input_file), "--id", "S-26099", "--output-dir", str(tmp_path)]
        )
        output_files = list(tmp_path.glob("S-26099_*.md"))
        assert len(output_files) == 1
        filename = output_files[0].name.lower()
        assert "ach_discussion" in filename, (
            f"Filename '{output_files[0].name}' should contain slug from "
            f"chat title 'ACH Discussion' → 'ach_discussion'."
        )

    def test_title_override_in_output_content(self, tmp_path):
        export = _simple_two_turn()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(export))

        _module.main(
            [
                str(input_file),
                "--id",
                "S-26099",
                "--title",
                "Custom Title Here",
                "--output-dir",
                str(tmp_path),
            ]
        )
        output_file = list(tmp_path.glob("S-26099_*.md"))[0]
        content = output_file.read_text()
        assert "Custom Title Here" in content, (
            f"--title override not found in output file frontmatter. "
            f"First 200 chars: {content[:200]!r}"
        )

    def test_dry_run_prints_to_stdout(self, tmp_path, capsys):
        """--dry-run prints output to stdout, does NOT write a file."""
        export = _simple_two_turn()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(export))

        exit_code = _module.main(
            [str(input_file), "--id", "S-26099", "--dry-run"]
        )
        assert exit_code == 0, (
            f"Exit code {exit_code} on dry-run, expected 0."
        )
        captured = capsys.readouterr()
        assert "---" in captured.out, (
            "Dry-run output should contain frontmatter delimiters on stdout. "
            f"Got stdout: {captured.out[:200]!r}"
        )
        assert "### User" in captured.out, (
            "Dry-run output should contain dialogue on stdout."
        )
        # No file should be written
        output_files = list(tmp_path.glob("S-26099_*.md"))
        assert len(output_files) == 0, (
            f"--dry-run should NOT write files, but found: "
            f"{[f.name for f in output_files]}"
        )

    def test_exit_1_on_missing_file(self, tmp_path):
        exit_code = _module.main(
            [str(tmp_path / "nonexistent.json"), "--id", "S-26099"]
        )
        assert exit_code == 1, (
            f"Exit code {exit_code} for missing file, expected 1."
        )

    def test_exit_1_on_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json at all")
        exit_code = _module.main(
            [str(bad_file), "--id", "S-26099", "--output-dir", str(tmp_path)]
        )
        assert exit_code == 1, (
            f"Exit code {exit_code} for invalid JSON, expected 1."
        )

    def test_exit_1_on_invalid_structure(self, tmp_path):
        """Valid JSON but wrong structure (dict instead of list) → exit 1."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text(json.dumps({"not": "a list"}))
        exit_code = _module.main(
            [str(bad_file), "--id", "S-26099", "--output-dir", str(tmp_path)]
        )
        assert exit_code == 1, (
            f"Exit code {exit_code} for invalid structure (dict, not list), "
            f"expected 1. Root of Qwen export must be a JSON array."
        )
