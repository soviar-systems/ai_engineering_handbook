#!/usr/bin/env python3
"""Generate hierarchical CHANGELOG from structured git commit bodies.

Extracts structured body bullets from git log and formats them into the
project's CHANGELOG format:

    release X.Y.Z
    * Section Name:
        - Capitalized subject line
            - Body bullet from commit

Usage:
    # Generate changelog between two refs
    uv run tools/scripts/generate_changelog.py v2.4.0..HEAD

    # Generate with version label
    uv run tools/scripts/generate_changelog.py v2.4.0..HEAD --version 2.5.0

    # Prepend to existing CHANGELOG file
    uv run tools/scripts/generate_changelog.py v2.4.0..HEAD --version 2.5.0 --prepend CHANGELOG

Exit codes:
    0 — success
    1 — error (e.g., git command failure)
"""

import argparse
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration loaded from pyproject.toml [tool.commit-convention]
#
# The type list, CHANGELOG section names, and section ordering are defined in:
#   tools/docs/git/01_production_git_workflow_standards.md
# and configured in:
#   pyproject.toml [tool.commit-convention]
#
# See: architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md
# ---------------------------------------------------------------------------

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _load_commit_convention() -> dict:
    with open(_PYPROJECT, "rb") as f:
        return tomllib.load(f)["tool"]["commit-convention"]


_CONFIG = _load_commit_convention()

# Type → human-readable CHANGELOG section name
TYPE_TO_SECTION: dict[str, str] = dict(_CONFIG["changelog-sections"])

# Ordered list of type keys — defines section ordering in CHANGELOG output
SECTION_ORDER: list[str] = list(_CONFIG["changelog-sections"].keys())

# Substring patterns for filtering housekeeping commits and bullets
EXCLUDE_PATTERNS: list[str] = list(_CONFIG.get("changelog-exclude-patterns", []))

# ---------------------------------------------------------------------------
# Commit dataclass
# ---------------------------------------------------------------------------


@dataclass
class Commit:
    """A parsed git commit with structured body bullets."""

    hash: str
    type: str
    scope: str | None
    subject: str
    bullets: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# CC subject: type[(scope)][!]: description
_SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)"          # type (lowercase alpha)
    r"(?:\((?P<scope>[^)]+)\))?"  # optional (scope)
    r"!?"                         # optional ! for breaking (ignored for parsing)
    r":\s+"                       # colon + at least one space
    r"(?P<desc>.+)$"              # description
)

# Bullet line: optional whitespace + '- ' + content
_BULLET_RE = re.compile(r"^\s*- .+")

# ArchTag line: ArchTag:TAG-NAME
_ARCHTAG_RE = re.compile(r"^ArchTag:\S+")

# Git trailer: Key: Value (after blank line)
_TRAILER_RE = re.compile(r"^[\w-]+: .+")

# Delimiter used in git log --format to separate commits
_COMMIT_MARKER = "END_COMMIT_MARKER"


# ---------------------------------------------------------------------------
# Main entry point (top-down design)
# ---------------------------------------------------------------------------


def main():
    cli = GenerateChangelogCLI()
    cli.run()


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def generate_changelog(
    ref_range: str,
    version: str | None = None,
    *,
    verbose: bool = False,
) -> str:
    """Generate formatted CHANGELOG string from git history."""
    commits = parse_commits(ref_range, verbose=verbose)
    commits = _filter_excluded_commits(commits, verbose=verbose)
    groups = group_by_type(commits)
    return format_changelog(groups, version)


def parse_commits(ref_range: str, *, verbose: bool = False) -> list[Commit]:
    """Extract commits from git log using --first-parent.

    --first-parent is critical: it filters out feature branch noise,
    scanning only the squashed trunk commits produced by Squash-and-Merge.
    """
    result = subprocess.run(
        [
            "git", "log", "--first-parent",
            f"--format=%H%n%s%n%b%n{_COMMIT_MARKER}",
            ref_range,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(f"git log failed: {result.stderr}", file=sys.stderr)
        return []

    if not result.stdout.strip():
        return []

    chunks = result.stdout.split(_COMMIT_MARKER)
    commits = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        commit = parse_single_commit(chunk, verbose=verbose)
        if commit is not None:
            commits.append(commit)

    return commits


def parse_single_commit(raw: str, *, verbose: bool = False) -> Commit | None:
    """Parse raw commit text into a Commit dataclass.

    Expected format (from git log %H%n%s%n%b):
        line 0: full hash
        line 1: subject line
        lines 2+: body (bullets, prose, ArchTag, trailers)

    The parser is PERMISSIVE — it extracts what it can without enforcing
    validation rules (that's validate_commit_msg.py's job).
    """
    raw = raw.strip()
    if not raw:
        return None

    lines = raw.splitlines()
    if len(lines) < 2:
        return None

    commit_hash = lines[0].strip()
    subject_line = lines[1].strip()

    # Parse subject: type[(scope)][!]: description
    match = _SUBJECT_RE.match(subject_line)
    if match:
        commit_type = match.group("type")
        scope = match.group("scope")
        subject = match.group("desc")
    else:
        # Permissive fallback for non-CC commits
        commit_type = "other"
        scope = None
        subject = subject_line

    # Extract bullets from body (lines 2+)
    body_lines = lines[2:]
    bullets = _extract_bullets(body_lines, verbose=verbose)

    return Commit(
        hash=commit_hash,
        type=commit_type,
        scope=scope,
        subject=subject,
        bullets=bullets,
    )


def _extract_bullets(body_lines: list[str], *, verbose: bool = False) -> list[str]:
    """Extract changelog bullets from body, excluding ArchTag and trailers.

    Trailers are detected as Key: Value lines that appear after a blank line.
    ArchTag lines (ArchTag:TAG-NAME) are Tier 3 metadata, not changelog content.
    Prose lines (non-bullet, non-trailer) are ignored.
    """
    bullets = []
    in_trailer_section = False

    for i, line in enumerate(body_lines):
        stripped = line.strip()

        # Blank line may start trailer section
        if not stripped:
            # Check if remaining non-empty lines are all trailers
            remaining = [l.strip() for l in body_lines[i + 1:] if l.strip()]
            if remaining and all(_TRAILER_RE.match(l) for l in remaining):
                in_trailer_section = True
            continue

        if in_trailer_section:
            continue

        # Skip ArchTag lines
        if _ARCHTAG_RE.match(stripped):
            continue

        # Capture bullet lines
        if _BULLET_RE.match(line):
            bullets.append(line.strip())

    filtered = []
    for b in bullets:
        if _matches_exclude_pattern(b):
            if verbose:
                print(f"  [excluded bullet] {b}", file=sys.stderr)
        else:
            filtered.append(b)
    return filtered


def _matches_exclude_pattern(text: str) -> bool:
    """Return True if text contains any configured exclusion pattern (case-insensitive)."""
    text_lower = text.lower()
    return any(p.lower() in text_lower for p in EXCLUDE_PATTERNS)


def _filter_excluded_commits(
    commits: list[Commit], *, verbose: bool = False,
) -> list[Commit]:
    """Drop commits whose subject matches an exclusion pattern."""
    filtered = []
    for c in commits:
        if _matches_exclude_pattern(c.subject):
            if verbose:
                print(f"[excluded commit] {c.subject}", file=sys.stderr)
        else:
            filtered.append(c)
    return filtered


def group_by_type(commits: list[Commit]) -> dict[str, list[Commit]]:
    """Group commits by their type key, preserving insertion order."""
    groups: dict[str, list[Commit]] = {}
    for commit in commits:
        groups.setdefault(commit.type, []).append(commit)
    return groups


def format_changelog(
    groups: dict[str, list[Commit]],
    version: str | None = None,
) -> str:
    """Format grouped commits into hierarchical CHANGELOG string.

    Output format:
        release X.Y.Z          (or "Unreleased")
        * Section Name:
            - Capitalized subject
                - Body bullet
    """
    if not groups:
        return ""

    lines: list[str] = []

    # Version header
    if version:
        lines.append(f"release {version}")
    else:
        lines.append("Unreleased")

    # Sections in defined order, then any remaining types not in SECTION_ORDER
    ordered_types = [t for t in SECTION_ORDER if t in groups]
    extra_types = [t for t in groups if t not in SECTION_ORDER]

    for type_key in ordered_types + extra_types:
        section_name = TYPE_TO_SECTION.get(type_key, type_key.capitalize())
        lines.append(f"* **{section_name}:**")

        for commit in groups[type_key]:
            # Subject line — capitalize first letter
            capitalized_subject = commit.subject[0].upper() + commit.subject[1:]
            lines.append(f"    - {capitalized_subject}")

            # Body bullets as sub-items
            for bullet in commit.bullets:
                lines.append(f"        {bullet}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI class
# ---------------------------------------------------------------------------


class GenerateChangelogCLI:
    """CLI for CHANGELOG generation from git history."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Generate CHANGELOG from structured git commit bodies",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""\
Examples:
    # Generate from last tag to HEAD
    generate_changelog.py v2.4.0..HEAD

    # With version label
    generate_changelog.py v2.4.0..HEAD --version 2.5.0

    # Prepend to existing CHANGELOG
    generate_changelog.py v2.4.0..HEAD --version 2.5.0 --prepend CHANGELOG
""",
        )
        parser.add_argument(
            "ref_range",
            help="Git ref range (e.g., v2.4.0..HEAD)",
        )
        parser.add_argument(
            "--version",
            default=None,
            help="Version label for the CHANGELOG header (default: Unreleased)",
        )
        parser.add_argument(
            "--prepend",
            default=None,
            metavar="FILE",
            help="Prepend output to an existing file instead of printing to stdout",
        )
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            default=False,
            help="Print excluded commits and bullets to stderr",
        )
        return parser

    def run(self, argv: list[str] | None = None) -> None:
        args = self.parser.parse_args(argv)
        output = generate_changelog(args.ref_range, args.version, verbose=args.verbose)

        if args.prepend:
            target = Path(args.prepend)
            existing = target.read_text(encoding="utf-8") if target.exists() else ""
            target.write_text(output + "\n" + existing, encoding="utf-8")
        else:
            print(output, end="")


if __name__ == "__main__":
    main()
