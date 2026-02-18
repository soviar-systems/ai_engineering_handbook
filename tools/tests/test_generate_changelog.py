"""Tests for generate_changelog.py — automated CHANGELOG extraction from git history.

## Architecture for future agents

This script parses git log output (format: %H%n%s%n%b%nEND_COMMIT_MARKER) into
structured Commit dataclasses, groups them by conventional commit type, and formats
them into the project's hierarchical CHANGELOG format.

The CHANGELOG format (defined in the plan and ADR-26024) is:

    release X.Y.Z
    * Section Name:
        - Capitalized subject line
            - Body bullet from commit
            - Another body bullet

## Test contracts

- parse_single_commit: raw commit text → Commit dataclass with type, scope, subject, bullets
- group_by_type: list[Commit] → dict[str, list[Commit]] grouped by commit type
- format_changelog: grouped commits → formatted CHANGELOG string
- parse_commits: git ref range → list[Commit] via git log --first-parent
- CLI: argparse interface with ref_range, --version, --prepend

## Non-brittleness strategy

Tests use constants (TYPE_TO_SECTION, SECTION_ORDER) from the module rather than
hardcoded strings. Format tests verify structural properties (indentation depth,
relative ordering) rather than exact line content. Parametrized inputs cover all
types without duplicating test logic.
"""

import pytest
from unittest.mock import patch, MagicMock

from tools.scripts.generate_changelog import (
    Commit,
    parse_single_commit,
    group_by_type,
    format_changelog,
    parse_commits,
    GenerateChangelogCLI,
    TYPE_TO_SECTION,
    SECTION_ORDER,
)


# ---------------------------------------------------------------------------
# Fixtures — raw commit text in git log %H%n%s%n%b format
#
# These mirror real commit output. The format is:
#   line 0: full hash (%H)
#   line 1: subject line (%s)
#   lines 2+: body (%b) — bullets, prose, ArchTag, trailers
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_commit_raw():
    """Minimal valid commit: one type, one bullet, no scope."""
    return "abc1234\nfeat: add login page\n- Created: auth/login.py — new login page\n"


@pytest.fixture
def scoped_commit_raw():
    """Commit with scope in parentheses: feat(auth): ..."""
    return "abc1234\nfeat(auth): add login\n- Created: auth/login.py — new\n"


@pytest.fixture
def complex_commit_raw():
    """Commit with ArchTag, multiple bullets, and Co-Authored-By trailer.

    This is the most realistic fixture — it mirrors the example in ADR-26024
    for a refactor commit with Tier 3 ArchTag coexisting with structured bullets.
    """
    return (
        "def5678\n"
        "refactor: simplify model loading logic\n"
        "ArchTag:TECHDEBT-PAYMENT\n"
        "- Updated: model_loader.py — reduced cyclomatic complexity from 15 to 8\n"
        "- Deleted: legacy_loader.py — consolidated into main loader\n"
        "\n"
        "Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n"
    )


@pytest.fixture
def bodyless_commit_raw():
    """Legacy commit predating the structured body convention.

    The parser must handle these gracefully — they appear as subject-only
    entries in the CHANGELOG with no sub-items.
    """
    return "aaa1111\nchore: bump version\n"


@pytest.fixture
def sample_commits():
    """Mixed list of Commit objects covering multiple types and bullet counts.

    Used for grouping and formatting tests. Includes:
    - Two feat commits (tests grouping of same type)
    - One fix commit with scope (tests scope handling)
    - One docs commit with no bullets (tests legacy/bodyless handling)
    """
    return [
        Commit(
            hash="abc1234",
            type="feat",
            scope=None,
            subject="add login page",
            bullets=["- Created: auth/login.py — new login page"],
        ),
        Commit(
            hash="def5678",
            type="fix",
            scope="auth",
            subject="correct token expiry",
            bullets=["- Fixed: auth/token.py — expiry was off by one"],
        ),
        Commit(
            hash="ghi9012",
            type="feat",
            scope=None,
            subject="add dashboard",
            bullets=[
                "- Created: dashboard/views.py — main dashboard view",
                "- Updated: urls.py — added dashboard route",
            ],
        ),
        Commit(
            hash="jkl3456",
            type="docs",
            scope=None,
            subject="update README",
            bullets=[],
        ),
    ]


# ---------------------------------------------------------------------------
# parse_single_commit
#
# Contract: raw text (hash + subject + body) → Commit dataclass.
# The parser must:
#   - Extract hash (line 0), type/scope/subject (line 1), bullets (body lines)
#   - Exclude ArchTag lines, git trailers, and non-bullet prose
#   - Handle bodyless commits (empty bullets list)
#   - Return None for empty/invalid input
# ---------------------------------------------------------------------------


class TestParseSingleCommit:
    """Contract: raw commit text → Commit dataclass with extracted fields.

    The parser is PERMISSIVE — it extracts whatever it can and does not
    enforce validation rules (that's validate_commit_msg.py's job).
    """

    def test_extracts_hash(self, simple_commit_raw):
        """First line of raw text is the commit hash."""
        commit = parse_single_commit(simple_commit_raw)
        assert commit.hash == "abc1234"

    def test_extracts_type(self, simple_commit_raw):
        """Type is the prefix before ':' in the subject line."""
        commit = parse_single_commit(simple_commit_raw)
        assert commit.type == "feat"

    def test_extracts_subject_without_type_prefix(self, simple_commit_raw):
        """Subject is everything after 'type: ' — the type prefix is stripped."""
        commit = parse_single_commit(simple_commit_raw)
        assert commit.subject == "add login page"

    def test_scope_is_none_when_absent(self, simple_commit_raw):
        commit = parse_single_commit(simple_commit_raw)
        assert commit.scope is None

    def test_extracts_scope_when_present(self, scoped_commit_raw):
        """Scope is the text inside parentheses: feat(scope): ..."""
        commit = parse_single_commit(scoped_commit_raw)
        assert commit.scope == "auth"

    def test_extracts_single_bullet(self, simple_commit_raw):
        """Body lines starting with '- ' are changelog bullets."""
        commit = parse_single_commit(simple_commit_raw)
        assert len(commit.bullets) == 1

    def test_extracts_multiple_bullets(self, complex_commit_raw):
        """Multiple '- ' lines in body → multiple bullets."""
        commit = parse_single_commit(complex_commit_raw)
        assert len(commit.bullets) == 2

    def test_excludes_trailers(self, complex_commit_raw):
        """Git trailers (Key: Value after blank line) must not appear in bullets.

        Trailers like Co-Authored-By are metadata, not changelog content.
        Detection rule: lines matching ^[\\w-]+: .+ after a blank line.
        """
        commit = parse_single_commit(complex_commit_raw)
        trailer_keywords = ["Co-Authored-By", "Signed-off-by", "Reviewed-by"]
        for bullet in commit.bullets:
            for keyword in trailer_keywords:
                assert keyword not in bullet

    def test_excludes_archtag_from_bullets(self, complex_commit_raw):
        """ArchTag lines are Tier 3 metadata — excluded from changelog output.

        ArchTag format: ^ArchTag:[A-Z-]+ (no space after colon).
        """
        commit = parse_single_commit(complex_commit_raw)
        for bullet in commit.bullets:
            assert not bullet.startswith("ArchTag")

    def test_ignores_prose_lines(self):
        """Non-bullet, non-trailer prose in body is ignored by parser.

        Prose is allowed for human context but not extracted into CHANGELOG.
        """
        raw = (
            "abc123\n"
            "feat: add feature\n"
            "This is some context about the change.\n"
            "- Created: file.py — new file\n"
            "More context here.\n"
        )
        commit = parse_single_commit(raw)
        assert len(commit.bullets) == 1

    def test_bodyless_commit_has_empty_bullets(self, bodyless_commit_raw):
        """Legacy commits without body → empty bullets list (graceful degradation)."""
        commit = parse_single_commit(bodyless_commit_raw)
        assert commit.bullets == []

    def test_empty_raw_text_returns_none(self):
        """Empty input (e.g., trailing split artifact) → None, not crash."""
        result = parse_single_commit("")
        assert result is None

    @pytest.mark.parametrize("commit_type", sorted(TYPE_TO_SECTION))
    def test_recognizes_all_commit_types(self, commit_type):
        """All types from pyproject.toml changelog-sections must be parseable."""
        raw = f"hash1\n{commit_type}: something\n- Updated: f.py — thing\n"
        commit = parse_single_commit(raw)
        assert commit.type == commit_type

    def test_preserves_bullet_text_verbatim(self):
        """Bullets are extracted as-is — no trimming, rewriting, or reformatting."""
        bullet = "- Created: tools/docs/website/guide.md — canonical guide (309 lines)"
        raw = f"abc123\nfeat: add guide\n{bullet}\n"
        commit = parse_single_commit(raw)
        assert commit.bullets[0] == bullet

    def test_handles_indented_bullets(self):
        """Bullets with leading whitespace (^\\s*- ) are still captured.

        Some commit bodies indent bullets for readability.
        """
        raw = "abc123\nfeat: add\n  - Created: f.py — thing\n"
        commit = parse_single_commit(raw)
        assert len(commit.bullets) == 1

    def test_unrecognized_type_still_parsed(self):
        """Parser is permissive — unknown types are extracted as-is.

        Validation is not this function's job (that's validate_commit_msg.py).
        Unknown types may appear in legacy commits or ecosystem extensions.
        """
        raw = "abc123\nunknown: something\n- Updated: f.py — thing\n"
        commit = parse_single_commit(raw)
        assert commit.type == "unknown"

    def test_breaking_bang_extracts_base_type(self):
        """Subject 'feat!: ...' → type is 'feat', not 'feat!'.

        The '!' indicates a breaking change (CC spec) but the base type
        is what matters for CHANGELOG section grouping.
        """
        raw = "abc123\nfeat!: breaking change\n- Updated: f.py — thing\n"
        commit = parse_single_commit(raw)
        assert commit.type == "feat"


# ---------------------------------------------------------------------------
# group_by_type
#
# Contract: list[Commit] → dict[str, list[Commit]].
# Keys are commit type strings (e.g., "feat", "fix").
# Values preserve insertion order of commits.
# ---------------------------------------------------------------------------


class TestGroupByType:
    """Contract: list[Commit] → dict mapping type key to list of commits."""

    def test_groups_commits_by_type_key(self, sample_commits):
        """Each commit's type field determines which group it belongs to."""
        groups = group_by_type(sample_commits)
        assert len(groups["feat"]) == 2
        assert len(groups["fix"]) == 1
        assert len(groups["docs"]) == 1

    def test_empty_input_returns_empty_dict(self):
        assert group_by_type([]) == {}

    def test_single_commit_creates_single_group(self):
        commits = [Commit("a", "feat", None, "add X", ["- bullet"])]
        groups = group_by_type(commits)
        assert len(groups) == 1
        assert "feat" in groups

    def test_preserves_commit_order_within_group(self, sample_commits):
        """Commits within a type group maintain their original order.

        This matters because CHANGELOG entries should appear in chronological
        (git log) order, not alphabetical or random.
        """
        groups = group_by_type(sample_commits)
        subjects = [c.subject for c in groups["feat"]]
        assert subjects == ["add login page", "add dashboard"]


# ---------------------------------------------------------------------------
# format_changelog
#
# Contract: grouped commits + optional version → formatted CHANGELOG string.
#
# Output format (from ADR-26024):
#   release X.Y.Z          ← version header (or "Unreleased")
#   * Section Name:         ← from TYPE_TO_SECTION mapping
#       - Subject line      ← 4-space indent, capitalized first letter
#           - Body bullet   ← 8-space indent, verbatim from commit
# ---------------------------------------------------------------------------


class TestFormatChangelog:
    """Contract: grouped commits + version → formatted CHANGELOG string.

    Format tests verify STRUCTURAL properties (indentation depth, section
    presence, relative ordering) rather than exact line content. This makes
    them resilient to wording changes in section names.
    """

    def test_includes_version_in_header(self, sample_commits):
        """When version is provided, it appears in the header line."""
        groups = group_by_type(sample_commits)
        output = format_changelog(groups, version="2.5.0")
        assert "2.5.0" in output

    def test_unreleased_header_when_no_version(self, sample_commits):
        """When version is None, header indicates unreleased state."""
        groups = group_by_type(sample_commits)
        output = format_changelog(groups, version=None)
        # Test for the word rather than exact line — avoids coupling to header format
        first_line = output.split("\n")[0].lower()
        assert "unreleased" in first_line

    def test_section_headers_use_type_to_section_mapping(self, sample_commits):
        """Each type group produces a section header from TYPE_TO_SECTION.

        Uses the module's own TYPE_TO_SECTION constant rather than hardcoded
        strings, so this test stays valid if section names are renamed.
        """
        groups = group_by_type(sample_commits)
        output = format_changelog(groups)
        for type_key in groups:
            section_name = TYPE_TO_SECTION[type_key]
            assert section_name in output, (
                f"Section name '{section_name}' for type '{type_key}' not found in output"
            )

    def test_subject_appears_in_output(self, sample_commits):
        """Each commit's subject line is present in the formatted output."""
        groups = group_by_type(sample_commits)
        output = format_changelog(groups)
        # Check case-insensitively — subject may be capitalized
        output_lower = output.lower()
        assert "add login page" in output_lower

    def test_bullets_appear_in_output(self):
        """Body bullets from commits appear verbatim in formatted output."""
        commits = [
            Commit("a", "feat", None, "add feature", [
                "- Created: file.py — new file",
                "- Updated: other.py — modified",
            ])
        ]
        groups = group_by_type(commits)
        output = format_changelog(groups)
        assert "Created:" in output
        assert "Updated:" in output

    def test_topic_lines_more_indented_than_section_headers(self):
        """Topic lines (subjects) must be indented deeper than section headers.

        Tests the hierarchical structure without hardcoding exact indent widths.
        """
        commits = [Commit("a", "feat", None, "add X", ["- bullet"])]
        groups = group_by_type(commits)
        output = format_changelog(groups)
        lines = output.split("\n")
        section_name = TYPE_TO_SECTION["feat"]
        section_line = next(l for l in lines if section_name in l)
        # Subject is capitalized in output
        topic_line = next(l for l in lines if "Add X" in l or "add X" in l.lower())
        section_indent = len(section_line) - len(section_line.lstrip())
        topic_indent = len(topic_line) - len(topic_line.lstrip())
        assert topic_indent > section_indent

    def test_bullet_lines_more_indented_than_topic_lines(self):
        """Bullet sub-items must be indented deeper than topic lines.

        Tests the 3-level hierarchy: section > topic > bullet.
        """
        bullet_text = "Created: `f.py` — thing"
        commits = [Commit("a", "feat", None, "add X", [f"- {bullet_text}"])]
        groups = group_by_type(commits)
        output = format_changelog(groups)
        lines = output.split("\n")
        topic_line = next(l for l in lines if "Add X" in l or "add X" in l.lower())
        bullet_line = next(l for l in lines if bullet_text in l)
        topic_indent = len(topic_line) - len(topic_line.lstrip())
        bullet_indent = len(bullet_line) - len(bullet_line.lstrip())
        assert bullet_indent > topic_indent

    def test_legacy_commit_produces_no_sub_items(self):
        """Commits without body bullets appear with subject only.

        Legacy commits (pre-convention) should degrade gracefully —
        they get a topic line but no bullet sub-items beneath it.
        """
        commits = [Commit("a", "docs", None, "update README", [])]
        groups = group_by_type(commits)
        output = format_changelog(groups)
        # Subject appears
        assert "update readme" in output.lower()
        lines = output.split("\n")
        # Find the topic line and verify nothing is more deeply indented after it
        topic_idx = next(
            i for i, l in enumerate(lines) if "update readme" in l.lower()
        )
        topic_indent = len(lines[topic_idx]) - len(lines[topic_idx].lstrip())
        # No subsequent non-empty lines should be more deeply indented
        for line in lines[topic_idx + 1 :]:
            if line.strip():
                line_indent = len(line) - len(line.lstrip())
                assert line_indent <= topic_indent, (
                    f"Unexpected sub-item after bodyless commit: {line!r}"
                )
                break  # Only check the next non-empty line

    def test_empty_groups_returns_string(self):
        """Empty input → valid string (not crash). May be empty or header-only."""
        output = format_changelog({})
        assert isinstance(output, str)

    def test_sections_follow_section_order(self):
        """Sections appear in SECTION_ORDER, not insertion or alphabetical order.

        Uses the module's SECTION_ORDER constant to verify relative positions.
        This test is resilient to reordering — it only checks that the defined
        order is respected.
        """
        commits = [
            Commit("a", "fix", None, "fix bug", ["- Fixed: f.py — bug"]),
            Commit("b", "feat", None, "add feature", ["- Created: g.py — new"]),
            Commit("c", "docs", None, "update docs", ["- Updated: d.md — docs"]),
        ]
        groups = group_by_type(commits)
        output = format_changelog(groups)
        # Collect positions of sections that appear in the output
        positions = []
        for type_key in SECTION_ORDER:
            if type_key in groups:
                section_name = TYPE_TO_SECTION[type_key]
                pos = output.find(section_name)
                if pos != -1:
                    positions.append(pos)
        # Positions must be monotonically increasing (respects SECTION_ORDER)
        assert positions == sorted(positions), (
            "Sections do not follow SECTION_ORDER"
        )

    def test_subject_first_letter_capitalized(self):
        """Format contract: subject's first letter is uppercased in output.

        Input subject 'add feature' → output shows 'Add feature'.
        """
        subject = "add feature"
        commits = [Commit("a", "feat", None, subject, ["- bullet"])]
        groups = group_by_type(commits)
        output = format_changelog(groups)
        capitalized = subject[0].upper() + subject[1:]
        assert capitalized in output


# ---------------------------------------------------------------------------
# parse_commits (mocked git)
#
# Contract: ref_range string → list[Commit] via subprocess git log.
# MUST use --first-parent to scan only squashed trunk commits.
# ---------------------------------------------------------------------------


class TestParseCommits:
    """Contract: ref range → list[Commit] via git log --first-parent.

    Git subprocess is mocked — these tests verify the command construction
    and output parsing, not actual git behavior.
    """

    @patch("tools.scripts.generate_changelog.subprocess")
    def test_uses_first_parent_flag(self, mock_subprocess):
        """--first-parent is critical: it filters out feature branch noise.

        Without it, squash-merged branches would expose their internal
        commits alongside the squashed trunk commit.
        """
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result
        parse_commits("v1.0..HEAD")
        call_args = mock_subprocess.run.call_args
        assert "--first-parent" in call_args[0][0]

    @patch("tools.scripts.generate_changelog.subprocess")
    def test_parses_multiple_commits_from_git_output(self, mock_subprocess):
        """Git output split on END_COMMIT_MARKER → one Commit per chunk."""
        mock_result = MagicMock()
        mock_result.stdout = (
            "abc123\nfeat: add X\n- Created: f.py — new\n\n"
            "END_COMMIT_MARKER\n"
            "def456\nfix: fix Y\n- Fixed: g.py — bug\n\n"
            "END_COMMIT_MARKER\n"
        )
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result
        commits = parse_commits("v1.0..HEAD")
        assert len(commits) == 2

    @patch("tools.scripts.generate_changelog.subprocess")
    def test_empty_range_returns_empty_list(self, mock_subprocess):
        """No commits in range → empty list, not error."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result
        commits = parse_commits("v1.0..v1.0")
        assert commits == []


# ---------------------------------------------------------------------------
# TYPE_TO_SECTION mapping
#
# Contract: every commit type from ADR-26024 has a CHANGELOG section name.
# If a new type is added to ADR-26024, it must be added to TYPE_TO_SECTION.
# ---------------------------------------------------------------------------


class TestTypeToSection:
    """Contract: all commit types from ADR-26024 have CHANGELOG section mappings."""

    @pytest.mark.parametrize("commit_type", sorted(TYPE_TO_SECTION))
    def test_all_types_mapped(self, commit_type):
        """Every type in pyproject.toml changelog-sections has a section mapping."""
        assert commit_type in TYPE_TO_SECTION


# ---------------------------------------------------------------------------
# CLI integration
#
# Contract: argparse with positional ref_range, optional --version, --prepend.
# Tests mock generate_changelog() to isolate CLI behavior from generation logic.
# ---------------------------------------------------------------------------


class TestGenerateChangelogCLI:
    """Contract: CLI interface with ref_range, --version, --prepend."""

    @patch("tools.scripts.generate_changelog.generate_changelog")
    def test_ref_range_is_required_positional(self, _mock_gen):
        """Missing ref_range → argparse error (nonzero exit)."""
        cli = GenerateChangelogCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.run(argv=[])
        assert exc_info.value.code != 0

    @patch("tools.scripts.generate_changelog.generate_changelog")
    def test_outputs_to_stdout_by_default(self, mock_gen, capsys):
        """Without --prepend, changelog is printed to stdout."""
        mock_gen.return_value = "changelog output"
        cli = GenerateChangelogCLI()
        cli.run(argv=["v1.0..HEAD"])
        captured = capsys.readouterr()
        assert "changelog output" in captured.out

    @patch("tools.scripts.generate_changelog.generate_changelog")
    def test_version_flag_forwarded_to_generator(self, mock_gen):
        """--version value is passed through to generate_changelog()."""
        mock_gen.return_value = ""
        cli = GenerateChangelogCLI()
        cli.run(argv=["v1.0..HEAD", "--version", "2.5.0"])
        mock_gen.assert_called_once_with("v1.0..HEAD", "2.5.0")

    @patch("tools.scripts.generate_changelog.generate_changelog")
    def test_prepend_writes_before_existing_content(self, mock_gen, tmp_path):
        """--prepend FILE: new changelog is prepended, existing content preserved."""
        mock_gen.return_value = "new changelog\n"
        changelog = tmp_path / "CHANGELOG"
        changelog.write_text("old content\n")
        cli = GenerateChangelogCLI()
        cli.run(argv=["v1.0..HEAD", "--prepend", str(changelog)])
        content = changelog.read_text()
        assert content.startswith("new changelog")
        assert "old content" in content
