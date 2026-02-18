"""Tests for validate_commit_msg.py — commit message validation hook.

## Architecture for future agents

This script is a pre-commit hook (stage: commit-msg) that validates commit messages
against the project's Conventional Commits + structured body convention (ADR-26024).

It reads a commit message file (path passed as CLI argument by git's commit-msg hook),
validates the subject line format and body bullet presence, then exits 0 (pass) or 1 (fail).

The validation has three layers:
1. Subject: must match CC format — type[(scope)][!]: description
2. Body: must contain at least one changelog bullet (line starting with '- ')
3. ArchTag: required for refactor/perf types and breaking changes (Tier 3)

## Test contracts

- validate_subject: subject line → list[str] errors (empty = valid)
- validate_body: body lines → list[str] errors (empty = valid)
- validate_archtag: type + body + breaking flag → list[str] errors
- CLI: reads file, validates, exits 0 or raises SystemExit(1)

## Non-brittleness strategy

Tests assert on error list LENGTH (empty vs non-empty), not error message content.
This means the implementation can freely change error wording without breaking tests.
Parametrized inputs derive from VALID_TYPES/ARCHTAG_REQUIRED_TYPES (loaded from pyproject.toml).
"""

import pytest

from tools.scripts.validate_commit_msg import (
    validate_subject,
    validate_body,
    validate_archtag,
    ValidateCommitMsgCLI,
    VALID_TYPES,
    ARCHTAG_REQUIRED_TYPES,
)


# ---------------------------------------------------------------------------
# validate_subject
#
# Contract: subject line → list of error strings.
# Empty list = valid. Non-empty list = validation failures.
#
# Valid format: type[(scope)][!]: description
# Where type ∈ VALID_TYPES, scope is optional, ! indicates breaking change,
# and description is non-empty text after ': '.
# ---------------------------------------------------------------------------


class TestValidateSubject:
    """Contract: subject line → list of error strings (empty = valid)."""

    @pytest.mark.parametrize("commit_type", sorted(VALID_TYPES))
    def test_valid_cc_subjects_produce_no_errors(self, commit_type):
        """All types from pyproject.toml [tool.commit-convention] with valid format → no errors."""
        subject = f"{commit_type}: test description"
        errors = validate_subject(subject)
        assert errors == []

    def test_scope_in_parentheses_is_valid(self):
        """feat(auth): ... is valid CC syntax."""
        errors = validate_subject("feat(auth): add login")
        assert errors == []

    def test_missing_type_prefix_is_invalid(self):
        """Subject without 'type: ' prefix fails validation."""
        errors = validate_subject("add login page")
        assert len(errors) > 0

    def test_unknown_type_is_invalid(self):
        """Type not in VALID_TYPES → error."""
        errors = validate_subject("unknown: do something")
        assert len(errors) > 0

    def test_missing_colon_separator_is_invalid(self):
        """'feat add login' (no colon) → error."""
        errors = validate_subject("feat add login page")
        assert len(errors) > 0

    def test_empty_subject_is_invalid(self):
        errors = validate_subject("")
        assert len(errors) > 0

    def test_empty_description_after_colon_is_invalid(self):
        """'feat: ' (trailing space, no description) → error."""
        errors = validate_subject("feat: ")
        assert len(errors) > 0

    def test_no_space_after_colon_is_invalid(self):
        """'feat:no space' — CC spec requires space after colon."""
        errors = validate_subject("feat:no space")
        assert len(errors) > 0

    def test_breaking_bang_syntax_is_valid(self):
        """'type!: description' is valid CC syntax for breaking changes."""
        errors = validate_subject("feat!: breaking change")
        assert errors == []

    def test_scope_with_breaking_bang_is_valid(self):
        """'type(scope)!: description' is valid CC syntax."""
        errors = validate_subject("feat(auth)!: breaking login")
        assert errors == []


# ---------------------------------------------------------------------------
# validate_body
#
# Contract: body lines → list of error strings.
# Body MUST contain at least one changelog bullet (line matching ^\s*- ).
#
# Lines that are NOT bullets:
#   - Prose context lines (human-readable, ignored by parser)
#   - ArchTag lines (ArchTag:TAG-NAME — Tier 3 metadata)
#   - Git trailers (Key: Value after blank line)
#   - Blank lines
# ---------------------------------------------------------------------------


class TestValidateBody:
    """Contract: body lines → list of error strings (empty = valid).

    The key contract: at least one line must start with (optional whitespace +) '- '.
    ArchTag lines and trailers do NOT count as bullets.
    """

    def test_single_bullet_passes(self):
        lines = ["- Created: file.py — new file"]
        errors = validate_body(lines)
        assert errors == []

    def test_multiple_bullets_pass(self):
        lines = [
            "- Created: file.py — new file",
            "- Updated: other.py — modified",
        ]
        errors = validate_body(lines)
        assert errors == []

    def test_empty_body_fails(self):
        """No body at all → error (at least one bullet required)."""
        errors = validate_body([])
        assert len(errors) > 0

    def test_prose_only_body_fails(self):
        """Body with prose but no bullets → error."""
        lines = ["This is just prose context.", "No bullets here."]
        errors = validate_body(lines)
        assert len(errors) > 0

    def test_prose_mixed_with_bullets_passes(self):
        """Prose lines are allowed alongside bullets — only bullets matter."""
        lines = [
            "Some context about this change.",
            "- Created: file.py — new file",
        ]
        errors = validate_body(lines)
        assert errors == []

    def test_indented_bullet_passes(self):
        """Bullets with leading whitespace ('  - ...') are still valid bullets."""
        lines = ["  - Updated: file.py — thing"]
        errors = validate_body(lines)
        assert errors == []

    def test_trailer_only_body_fails(self):
        """Trailers alone (Co-Authored-By etc.) don't satisfy bullet requirement.

        Trailers are metadata, not changelog content. A commit with only
        trailers in the body is effectively bodyless from a changelog perspective.
        """
        lines = [
            "",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
        ]
        errors = validate_body(lines)
        assert len(errors) > 0

    def test_archtag_only_body_fails(self):
        """ArchTag line alone doesn't satisfy bullet requirement.

        ArchTag is Tier 3 metadata, not a changelog entry.
        """
        lines = ["ArchTag:TECHDEBT-PAYMENT"]
        errors = validate_body(lines)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# validate_archtag
#
# Contract: commit type + body lines + breaking flag → list of error strings.
# ArchTag is REQUIRED when:
#   - type ∈ ARCHTAG_REQUIRED_TYPES (refactor, perf)
#   - OR breaking=True (from ! in subject or BREAKING CHANGE footer)
# ArchTag format: ^ArchTag:[A-Z-]+ (first line of body, before bullets)
# ---------------------------------------------------------------------------


class TestValidateArchTag:
    """Contract: types in ARCHTAG_REQUIRED_TYPES + breaking changes need ArchTag."""

    def test_refactor_with_archtag_passes(self):
        lines = ["ArchTag:TECHDEBT-PAYMENT", "- Updated: f.py — simplified"]
        errors = validate_archtag("refactor", lines, breaking=False)
        assert errors == []

    def test_perf_with_archtag_passes(self):
        lines = ["ArchTag:PERF-OPTIMIZATION", "- Updated: f.py — faster"]
        errors = validate_archtag("perf", lines, breaking=False)
        assert errors == []

    def test_refactor_without_archtag_fails(self):
        lines = ["- Updated: f.py — simplified"]
        errors = validate_archtag("refactor", lines, breaking=False)
        assert len(errors) > 0

    def test_perf_without_archtag_fails(self):
        lines = ["- Updated: f.py — faster"]
        errors = validate_archtag("perf", lines, breaking=False)
        assert len(errors) > 0

    def test_feat_without_archtag_passes(self):
        """Non-refactor/perf types don't need ArchTag."""
        lines = ["- Created: f.py — new"]
        errors = validate_archtag("feat", lines, breaking=False)
        assert errors == []

    def test_fix_without_archtag_passes(self):
        lines = ["- Fixed: f.py — bug"]
        errors = validate_archtag("fix", lines, breaking=False)
        assert errors == []

    def test_breaking_change_without_archtag_fails(self):
        """Breaking changes (! in subject) also require ArchTag."""
        lines = ["- Updated: f.py — breaking"]
        errors = validate_archtag("feat", lines, breaking=True)
        assert len(errors) > 0

    def test_breaking_change_with_archtag_passes(self):
        lines = ["ArchTag:BREAKING-CHANGE", "- Updated: f.py — breaking"]
        errors = validate_archtag("feat", lines, breaking=True)
        assert errors == []


# ---------------------------------------------------------------------------
# Constants validation
#
# These tests anchor the constants to the type list defined in:
#   tools/docs/git/01_production_git_workflow_standards.md
#     § Conventional Commits Policy — valid type prefixes
#     § Tier 3: Justification (ArchTag) — ArchTag-required types
#
# If a new type or ArchTag rule is added there, these tests will remind
# you to update the constants in validate_commit_msg.py.
# ---------------------------------------------------------------------------


class TestValidTypes:
    """Contract: all types from pyproject.toml [tool.commit-convention] are in VALID_TYPES."""

    @pytest.mark.parametrize("commit_type", sorted(VALID_TYPES))
    def test_all_config_types_recognized(self, commit_type):
        """Every type in pyproject.toml valid-types is in VALID_TYPES constant."""
        assert commit_type in VALID_TYPES


class TestArchTagRequiredTypes:
    """Contract: refactor and perf require ArchTag; other types do not."""

    @pytest.mark.parametrize("commit_type", ["refactor", "perf"])
    def test_requires_archtag(self, commit_type):
        assert commit_type in ARCHTAG_REQUIRED_TYPES

    @pytest.mark.parametrize(
        "commit_type", sorted(VALID_TYPES - ARCHTAG_REQUIRED_TYPES)
    )
    def test_does_not_require_archtag(self, commit_type):
        """Types outside ARCHTAG_REQUIRED_TYPES don't need ArchTag."""
        assert commit_type not in ARCHTAG_REQUIRED_TYPES


# ---------------------------------------------------------------------------
# CLI integration
#
# Contract: CLI reads a commit message file (positional arg), runs all
# validations, and either returns normally (exit 0) or raises SystemExit(1).
#
# The tmp_path fixture provides isolated temporary files for each test.
# Each test creates a COMMIT_EDITMSG file mimicking what git passes
# to the commit-msg hook.
# ---------------------------------------------------------------------------


class TestValidateCommitMsgCLI:
    """Contract: reads file, validates, returns normally (valid) or exits 1 (invalid)."""

    def test_valid_message_passes(self, tmp_path):
        """Full valid commit message: CC subject + body bullet + trailer."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text(
            "feat: add login page\n\n"
            "- Created: auth/login.py — new login page\n\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>\n"
        )
        cli = ValidateCommitMsgCLI()
        cli.run(argv=[str(msg_file)])  # Should not raise SystemExit

    def test_invalid_subject_exits_1(self, tmp_path):
        """Subject without CC type prefix → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("bad commit message\n\n- Some bullet\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_missing_body_bullets_exits_1(self, tmp_path):
        """Valid subject but no bullets in body → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("feat: add login page\n\nSome prose but no bullets.\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_no_body_at_all_exits_1(self, tmp_path):
        """Subject-only message (no blank line, no body) → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("feat: quick fix\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_missing_file_arg_exits_nonzero(self):
        """No positional argument → argparse error (exit code 2)."""
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[])
        assert exc_info.value.code != 0

    def test_refactor_without_archtag_exits_1(self, tmp_path):
        """Refactor commit missing ArchTag → exit 1 (Tier 3 violation)."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text(
            "refactor: simplify loader\n\n"
            "- Updated: loader.py — simplified\n"
        )
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_refactor_with_archtag_passes(self, tmp_path):
        """Refactor commit with ArchTag → valid, no error."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text(
            "refactor: simplify loader\n\n"
            "ArchTag:TECHDEBT-PAYMENT\n"
            "- Updated: loader.py — simplified\n"
        )
        cli = ValidateCommitMsgCLI()
        cli.run(argv=[str(msg_file)])  # Should not raise SystemExit


# ---------------------------------------------------------------------------
# Formerly skipped commits now fail
#
# Contract: WIP, Merge, fixup, squash commits → exit 1 (no longer skipped).
# is_skip_commit() was removed — all commits go through validation.
# The only escape hatch is --no-verify.
# ---------------------------------------------------------------------------


class TestFormerlySkippedCommitsFail:
    """Contract: WIP, Merge, fixup, squash commits → exit 1 (no longer skipped)."""

    def test_wip_commit_fails_validation(self, tmp_path):
        """WIP: prefix is not a valid CC type → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("WIP: work in progress\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_merge_commit_fails_validation(self, tmp_path):
        """Merge commits are not valid CC format → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("Merge branch 'feature' into main\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_fixup_commit_fails_validation(self, tmp_path):
        """fixup! prefix is not a valid CC type → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("fixup! feat: add login\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1

    def test_squash_commit_fails_validation(self, tmp_path):
        """squash! prefix is not a valid CC type → exit 1."""
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("squash! feat: add login\n")
        cli = ValidateCommitMsgCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[str(msg_file)])
        assert exc_info.value.code == 1
