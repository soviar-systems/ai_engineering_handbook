"""
Test suite for check_adr.py - ADR Index synchronization validator.

Tests are organized following the behavior-based testing principle:
- Test what the code does, not how it does it
- Use semantic assertions rather than exact string matching
- Parameterize inputs for varied scenarios
"""

import runpy
import subprocess
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest


# ======================
# Test Fixtures & Helpers
# ======================


@dataclass
class AdrTestEnv:
    """Test environment with isolated ADR directory structure."""

    adr_dir: Path
    index_path: Path
    root: Path


def create_adr_file(directory: Path, number: int, title: str, slug: str | None = None) -> Path:
    """Create an ADR file with given number and title.

    Creates a full ADR file with YAML frontmatter and all required sections
    from the module's REQUIRED_SECTIONS (loaded from config).

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26001)
        title: ADR title for the header
        slug: Optional slug for filename (derived from title if not provided)

    Returns:
        Path to created file
    """
    if slug is None:
        # Generate slug from title: lowercase, replace spaces with underscores, truncate
        slug = title.lower().replace(" ", "_").replace("-", "_")[:40]

    # Use create_adr_file_full with default sections from config
    return create_adr_file_full(
        directory=directory,
        number=number,
        title=title,
        slug=slug,
        status="accepted",
        include_subsections=True,
    )


def create_adr_file_with_frontmatter(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    status: str = "proposed",
    tags: list[str] | None = None,
    frontmatter_title: str | None = None,
) -> Path:
    """Create an ADR file with YAML frontmatter (new format).

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26016)
        title: ADR title for the header
        slug: Slug for filename
        status: ADR status (proposed, accepted, rejected, superseded, deprecated)
        tags: Optional list of tags
        frontmatter_title: Optional title in frontmatter (defaults to title param)

    Returns:
        Path to created file
    """
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    # Build frontmatter
    fm_title = frontmatter_title if frontmatter_title is not None else title
    frontmatter_lines = [
        "---",
        f"title: {fm_title}",
        f"status: {status}",
    ]
    if tags:
        frontmatter_lines.append(f"tags: [{', '.join(tags)}]")
    frontmatter_lines.append("---")

    content = "\n".join(frontmatter_lines) + f"\n\n# ADR-{number}: {title}\n\n## Context\n\nSome context.\n"
    filepath.write_text(content, encoding="utf-8")
    return filepath


def create_index(path: Path, entries: list[tuple[int, str, str]]) -> None:
    """Create index file with given entries.

    Args:
        path: Path to index file
        entries: List of (number, title, link) tuples
    """
    lines = ["# ADR Index\n", "\n", ":::{glossary}\n"]
    for number, title, link in entries:
        lines.append(f"ADR-{number}\n")
        lines.append(f": [{title}]({link})\n")
        lines.append("\n")
    lines.append(":::\n")
    path.write_text("".join(lines), encoding="utf-8")


def create_empty_index(path: Path) -> None:
    """Create an empty index file with glossary block but no entries."""
    content = "# ADR Index\n\n:::{glossary}\n:::\n"
    path.write_text(content, encoding="utf-8")


def create_adr_config(path: Path) -> None:
    """Copy real ADR config to test directory.

    Sources from the production adr_config.yaml (Single Source of Truth)
    to avoid maintaining a duplicate hardcoded config in tests.

    Args:
        path: Path to write config file
    """
    import shutil

    real_config = Path(__file__).resolve().parent.parent.parent / "architecture" / "adr" / "adr_config.yaml"
    shutil.copy2(real_config, path)


def create_legacy_adr_file(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    status: str = "Accepted",
    sections: list[str] | None = None,
) -> Path:
    """Create a legacy ADR file without YAML frontmatter (old format).

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26001)
        title: ADR title for the header
        slug: Slug for filename
        status: ADR status in old markdown format
        sections: Optional list of section names to include

    Returns:
        Path to created file
    """
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    content_lines = [
        f"# ADR-{number}: {title}",
        "",
        "## Status",
        "",
        status,
        "",
    ]

    if sections is None:
        sections = ["Context", "Decision", "Consequences", "Alternatives", "References", "Participants"]

    for section in sections:
        content_lines.append(f"## {section}")
        content_lines.append("")
        content_lines.append(f"Content for {section.lower()} section.")
        content_lines.append("")

    filepath.write_text("\n".join(content_lines), encoding="utf-8")
    return filepath


def create_adr_file_full(
    directory: Path,
    number: int,
    title: str,
    slug: str,
    status: str = "proposed",
    tags: list[str] | None = None,
    frontmatter_title: str | None = None,
    date: str = "2024-01-15",
    adr_id: str | None = None,
    sections: list[str] | None = None,
    include_subsections: bool = False,
    superseded_by: str | None = None,
) -> Path:
    """Create an ADR file with full YAML frontmatter and optional sections.

    Args:
        directory: Directory to create file in
        number: ADR number (e.g., 26016)
        title: ADR title for the header
        slug: Slug for filename
        status: ADR status
        tags: Optional list of tags
        frontmatter_title: Optional title in frontmatter (defaults to title param)
        date: Date in YYYY-MM-DD format
        adr_id: Optional ADR ID (defaults to number)
        sections: Optional list of section names to include. If None, uses
                  REQUIRED_SECTIONS from the module (loaded from config).
        include_subsections: Whether to include recommended subsections
        superseded_by: Optional ADR reference (e.g., "ADR-26023") for superseded ADRs

    Returns:
        Path to created file
    """
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename

    # Build frontmatter
    fm_title = frontmatter_title if frontmatter_title is not None else title
    fm_id = adr_id if adr_id is not None else str(number)
    fm_tags = tags if tags is not None else ["architecture"]

    frontmatter_lines = [
        "---",
        f"id: {fm_id}",
        f"title: {fm_title}",
        f"date: {date}",
        f"status: {status}",
        f"tags: [{', '.join(fm_tags)}]",
        f"superseded_by: {superseded_by}" if superseded_by else "superseded_by: null",
        "---",
    ]

    content_lines = frontmatter_lines + [
        "",
        f"# ADR-{number}: {title}",
        "",
    ]

    if sections is None:
        # Import here to get the monkeypatched value from the test fixture
        import tools.scripts.check_adr as module
        sections = module.REQUIRED_SECTIONS

    for section in sections:
        content_lines.append(f"## {section}")
        content_lines.append("")
        if section == "Consequences" and include_subsections:
            content_lines.append("### Positive")
            content_lines.append("")
            content_lines.append("Some positive consequence.")
            content_lines.append("")
            content_lines.append("### Negative / Risks")
            content_lines.append("")
            content_lines.append("Some negative consequence.")
            content_lines.append("")
        elif section == "Alternatives" and status == "accepted":
            # Accepted ADRs must pass the promotion gate (ADR-26025):
            # ≥2 alternative entries in "- **Name**: Reason." format.
            content_lines.append("- **Option A**: Rejected. First alternative.")
            content_lines.append("- **Option B**: Rejected. Second alternative.")
            content_lines.append("")
        elif section == "Participants" and status == "accepted":
            # Accepted ADRs must have non-empty Participants (ADR-26025).
            content_lines.append("1. Test Author")
            content_lines.append("")
        else:
            content_lines.append(f"Content for {section.lower()} section.")
            content_lines.append("")

    filepath.write_text("\n".join(content_lines), encoding="utf-8")
    return filepath


@pytest.fixture
def adr_env(tmp_path, monkeypatch):
    """Create isolated ADR environment with configurable state."""
    adr_dir = tmp_path / "architecture" / "adr"
    adr_dir.mkdir(parents=True)
    index_path = tmp_path / "architecture" / "adr_index.md"
    config_path = adr_dir / "adr_config.yaml"

    # Create the template file (should be excluded)
    template = adr_dir / "adr_template.md"
    template.write_text("# ADR Template\n\nUse this as a template.\n", encoding="utf-8")

    # Create config file
    create_adr_config(config_path)

    # Monkeypatch to use test directories
    monkeypatch.setattr("tools.scripts.check_adr.ADR_DIR", adr_dir)
    monkeypatch.setattr("tools.scripts.check_adr.INDEX_PATH", index_path)
    monkeypatch.setattr("tools.scripts.check_adr.ADR_CONFIG_PATH", config_path)

    # Reload config with test paths
    import tools.scripts.check_adr as module
    config = module.load_adr_config()
    monkeypatch.setattr(module, "VALID_STATUSES", set(config.get("statuses", [])))
    monkeypatch.setattr(module, "STATUS_SECTIONS", module._build_status_sections(config))
    monkeypatch.setattr(module, "DEFAULT_STATUS", config.get("default_status", "proposed"))
    monkeypatch.setattr(module, "SECTION_ORDER", list(config.get("sections", {}).keys()))
    monkeypatch.setattr(module, "STATUS_CORRECTIONS", module._build_status_corrections(config))
    monkeypatch.setattr(module, "REQUIRED_SECTIONS", config.get("required_sections", []))
    monkeypatch.setattr(module, "ALLOWED_SECTIONS", set(config.get("allowed_sections", [])))
    monkeypatch.setattr(module, "CONDITIONAL_SECTIONS", config.get("conditional_sections", {}))

    return AdrTestEnv(adr_dir=adr_dir, index_path=index_path, root=tmp_path)


@pytest.fixture
def synced_env(adr_env):
    """Create environment with ADRs that are in sync with index."""
    # Create some ADR files
    create_adr_file(adr_env.adr_dir, 26001, "First Feature", "first_feature")
    create_adr_file(adr_env.adr_dir, 26002, "Second Feature", "second_feature")
    create_adr_file(adr_env.adr_dir, 26003, "Third Feature", "third_feature")

    # Create matching index
    create_index(
        adr_env.index_path,
        [
            (26001, "First Feature", "/architecture/adr/adr_26001_first_feature.md"),
            (26002, "Second Feature", "/architecture/adr/adr_26002_second_feature.md"),
            (26003, "Third Feature", "/architecture/adr/adr_26003_third_feature.md"),
        ],
    )
    return adr_env


# ======================
# Unit Tests: ADR File Discovery
# ======================


class TestGetAdrFiles:
    """Tests for ADR file discovery functionality."""

    def test_discovers_adr_files(self, adr_env):
        """Should find all ADR files in the directory."""
        from tools.scripts.check_adr import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        create_adr_file(adr_env.adr_dir, 26002, "Another ADR", "another_adr")

        files = get_adr_files()

        assert len(files) == 2
        numbers = {f.number for f in files}
        assert numbers == {26001, 26002}

    def test_excludes_template_file(self, adr_env):
        """Template file should not be included in results."""
        from tools.scripts.check_adr import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        # Template already created by fixture

        files = get_adr_files()

        filenames = {f.path.name for f in files}
        assert "adr_template.md" not in filenames

    def test_returns_sorted_by_number(self, adr_env):
        """ADR files should be sorted by number ascending."""
        from tools.scripts.check_adr import get_adr_files

        # Create in reverse order
        create_adr_file(adr_env.adr_dir, 26003, "Third", "third")
        create_adr_file(adr_env.adr_dir, 26001, "First", "first")
        create_adr_file(adr_env.adr_dir, 26002, "Second", "second")

        files = get_adr_files()

        numbers = [f.number for f in files]
        assert numbers == [26001, 26002, 26003]

    def test_empty_directory_returns_empty_list(self, adr_env):
        """Empty ADR directory should return empty list."""
        from tools.scripts.check_adr import get_adr_files

        # Only template exists (created by fixture)
        files = get_adr_files()

        assert files == []

    def test_parses_title_from_header(self, adr_env):
        """Should extract title from ADR header line."""
        from tools.scripts.check_adr import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Use of Python for Scripts", "python_scripts")

        files = get_adr_files()

        assert len(files) == 1
        assert files[0].title == "Use of Python for Scripts"

    def test_handles_file_without_valid_header(self, adr_env):
        """File without valid ADR header should be skipped with warning."""
        from tools.scripts.check_adr import get_adr_files

        # Create a file with wrong header format
        bad_file = adr_env.adr_dir / "adr_26001_bad.md"
        bad_file.write_text("# Not a valid ADR header\n\nContent here.\n", encoding="utf-8")

        # Also create a valid file
        create_adr_file(adr_env.adr_dir, 26002, "Valid ADR", "valid")

        files = get_adr_files()

        # Only the valid file should be returned
        assert len(files) == 1
        assert files[0].number == 26002

    def test_nonexistent_adr_directory(self, tmp_path, monkeypatch):
        """Should return empty list if ADR directory doesn't exist."""
        from tools.scripts.check_adr import get_adr_files

        nonexistent = tmp_path / "nonexistent" / "adr"
        monkeypatch.setattr("tools.scripts.check_adr.ADR_DIR", nonexistent)

        files = get_adr_files()

        assert files == []


# ======================
# Unit Tests: Index Parsing
# ======================


class TestParseIndex:
    """Tests for index file parsing functionality."""

    def test_parses_glossary_entries(self, adr_env):
        """Should parse entries from glossary block."""
        from tools.scripts.check_adr import parse_index

        create_index(
            adr_env.index_path,
            [
                (26001, "First ADR", "/architecture/adr/adr_26001_first.md"),
                (26002, "Second ADR", "/architecture/adr/adr_26002_second.md"),
            ],
        )

        entries = parse_index()

        assert len(entries) == 2
        numbers = {e.number for e in entries}
        assert numbers == {26001, 26002}

    def test_extracts_title_and_link(self, adr_env):
        """Should extract title and link from each entry."""
        from tools.scripts.check_adr import parse_index

        create_index(
            adr_env.index_path,
            [(26001, "Use of Python and OOP", "/architecture/adr/adr_26001_python_oop.md")],
        )

        entries = parse_index()

        assert len(entries) == 1
        assert entries[0].title == "Use of Python and OOP"
        assert entries[0].link == "/architecture/adr/adr_26001_python_oop.md"

    def test_empty_glossary_returns_empty_list(self, adr_env):
        """Empty glossary block should return empty list."""
        from tools.scripts.check_adr import parse_index

        create_empty_index(adr_env.index_path)

        entries = parse_index()

        assert entries == []

    def test_missing_index_file_raises_error(self, adr_env):
        """Missing index file should raise appropriate error."""
        from tools.scripts.check_adr import parse_index

        # Don't create the index file

        with pytest.raises(FileNotFoundError):
            parse_index()

    def test_index_without_glossary_block(self, adr_env):
        """Index file without glossary block should return empty list."""
        from tools.scripts.check_adr import parse_index

        # Create index without glossary block
        adr_env.index_path.write_text("# ADR Index\n\nNo glossary here.\n", encoding="utf-8")

        entries = parse_index()

        assert entries == []

    def test_preserves_entry_order(self, adr_env):
        """Entries should be returned in the order they appear in the file."""
        from tools.scripts.check_adr import parse_index

        create_index(
            adr_env.index_path,
            [
                (26003, "Third", "/architecture/adr/adr_26003_third.md"),
                (26001, "First", "/architecture/adr/adr_26001_first.md"),
                (26002, "Second", "/architecture/adr/adr_26002_second.md"),
            ],
        )

        entries = parse_index()

        numbers = [e.number for e in entries]
        assert numbers == [26003, 26001, 26002]  # Order preserved from file


# ======================
# Unit Tests: Sync Validation
# ======================


class TestValidateSync:
    """Tests for synchronization validation logic."""

    def test_synced_environment_has_no_errors(self, synced_env):
        """When ADRs and index are in sync, no errors should be reported."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        assert errors == []

    def test_detects_missing_adr_in_index(self, synced_env):
        """New ADR file without index entry should be detected."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Add new ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should have at least one error for the missing ADR
        missing_errors = [e for e in errors if e.number == 26004 and e.error_type == "missing_in_index"]
        assert len(missing_errors) == 1

    def test_detects_orphan_index_entry(self, synced_env):
        """Index entry pointing to non-existent file should be detected."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Add entry to index without corresponding file
        create_index(
            synced_env.index_path,
            [
                (26001, "First Feature", "/architecture/adr/adr_26001_first_feature.md"),
                (26002, "Second Feature", "/architecture/adr/adr_26002_second_feature.md"),
                (26003, "Third Feature", "/architecture/adr/adr_26003_third_feature.md"),
                (26004, "Ghost Feature", "/architecture/adr/adr_26004_ghost.md"),  # No file
            ],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should have at least one orphan error for ADR 26004
        orphan_errors = [e for e in errors if e.number == 26004 and e.error_type == "orphan_in_index"]
        assert len(orphan_errors) == 1

    def test_detects_wrong_link_path(self, synced_env):
        """Index entry with incorrect link path should be detected."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create index with wrong link for 26002
        create_index(
            synced_env.index_path,
            [
                (26001, "First Feature", "/architecture/adr/adr_26001_first_feature.md"),
                (26002, "Second Feature", "/architecture/adr/adr_26002_wrong_path.md"),  # Wrong!
                (26003, "Third Feature", "/architecture/adr/adr_26003_third_feature.md"),
            ],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should detect wrong link for ADR 26002
        link_errors = [e for e in errors if e.number == 26002 and e.error_type == "wrong_link"]
        assert len(link_errors) == 1

    def test_detects_out_of_order_entries(self, synced_env):
        """Entries not in numerical order should be detected."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create index with wrong order
        create_index(
            synced_env.index_path,
            [
                (26001, "First Feature", "/architecture/adr/adr_26001_first_feature.md"),
                (26003, "Third Feature", "/architecture/adr/adr_26003_third_feature.md"),  # Wrong order
                (26002, "Second Feature", "/architecture/adr/adr_26002_second_feature.md"),
            ],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should detect ordering issue
        order_errors = [e for e in errors if e.error_type == "wrong_order"]
        assert len(order_errors) >= 1

    def test_detects_duplicate_adr_numbers(self, adr_env):
        """Duplicate ADR numbers in files should be detected."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create two files with same number but different slugs
        create_adr_file(adr_env.adr_dir, 26001, "First Version", "first_version")
        # Manually create another file with same number
        dup_file = adr_env.adr_dir / "adr_26001_duplicate.md"
        dup_file.write_text("# ADR-26001: Duplicate\n\n## Status\n\nAccepted\n", encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26001, "First Version", "/architecture/adr/adr_26001_first_version.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should detect duplicate
        assert any(e.error_type == "duplicate_number" for e in errors)

    def test_multiple_errors_reported(self, adr_env):
        """All errors should be reported, not just the first one."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADRs
        create_adr_file(adr_env.adr_dir, 26001, "First", "first")
        create_adr_file(adr_env.adr_dir, 26002, "Second", "second")
        create_adr_file(adr_env.adr_dir, 26004, "Fourth", "fourth")  # Not in index

        # Create index with missing 26004 and orphan 26003
        create_index(
            adr_env.index_path,
            [
                (26001, "First", "/architecture/adr/adr_26001_first.md"),
                (26002, "Second", "/architecture/adr/adr_26002_second.md"),
                (26003, "Third", "/architecture/adr/adr_26003_third.md"),  # Orphan
            ],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        error_types = {e.error_type for e in errors}
        assert "missing_in_index" in error_types  # 26004
        assert "orphan_in_index" in error_types  # 26003


# ======================
# Unit Tests: Auto-Fix
# ======================


class TestAutoFixIndex:
    """Tests for auto-fix functionality."""

    def test_adds_missing_entries(self, synced_env):
        """Fix should add missing ADR entries to index."""
        from tools.scripts.check_adr import fix_index, get_adr_files, parse_index

        # Add new ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        fix_index()

        # Re-parse to verify
        entries = parse_index()
        numbers = {e.number for e in entries}
        assert 26004 in numbers

    def test_maintains_numerical_order(self, adr_env):
        """Fix should ensure entries are in numerical order."""
        from tools.scripts.check_adr import fix_index, parse_index

        # Create ADRs
        create_adr_file(adr_env.adr_dir, 26003, "Third", "third")
        create_adr_file(adr_env.adr_dir, 26001, "First", "first")
        create_adr_file(adr_env.adr_dir, 26002, "Second", "second")

        # Create index with wrong order
        create_index(
            adr_env.index_path,
            [
                (26003, "Third", "/architecture/adr/adr_26003_third.md"),
                (26001, "First", "/architecture/adr/adr_26001_first.md"),
            ],
        )

        fix_index()

        entries = parse_index()
        numbers = [e.number for e in entries]
        assert numbers == sorted(numbers)

    def test_preserves_existing_valid_entries(self, synced_env):
        """Fix should not remove or alter valid existing entries."""
        from tools.scripts.check_adr import fix_index, parse_index

        original_entries = parse_index()

        # Add new ADR
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        fix_index()

        new_entries = parse_index()

        # All original entries should still be present
        original_numbers = {e.number for e in original_entries}
        new_numbers = {e.number for e in new_entries}
        assert original_numbers.issubset(new_numbers)

    def test_removes_orphan_entries(self, synced_env):
        """Fix should remove entries for non-existent ADR files."""
        from tools.scripts.check_adr import fix_index, parse_index

        # Add orphan entry to index
        create_index(
            synced_env.index_path,
            [
                (26001, "First Feature", "/architecture/adr/adr_26001_first_feature.md"),
                (26002, "Second Feature", "/architecture/adr/adr_26002_second_feature.md"),
                (26003, "Third Feature", "/architecture/adr/adr_26003_third_feature.md"),
                (26999, "Orphan", "/architecture/adr/adr_26999_orphan.md"),  # No file
            ],
        )

        fix_index()

        entries = parse_index()
        numbers = {e.number for e in entries}
        assert 26999 not in numbers

    def test_fixes_wrong_links(self, synced_env):
        """Fix should correct links that point to wrong paths."""
        from tools.scripts.check_adr import fix_index, parse_index

        # Create index with wrong link
        create_index(
            synced_env.index_path,
            [
                (26001, "First Feature", "/architecture/adr/adr_26001_first_feature.md"),
                (26002, "Second Feature", "/architecture/adr/adr_26002_WRONG.md"),  # Wrong path
                (26003, "Third Feature", "/architecture/adr/adr_26003_third_feature.md"),
            ],
        )

        fix_index()

        entries = parse_index()
        entry_26002 = next(e for e in entries if e.number == 26002)
        assert "second_feature" in entry_26002.link

    def test_creates_index_if_missing(self, adr_env):
        """Fix should create index file if it doesn't exist."""
        from tools.scripts.check_adr import fix_index, parse_index

        create_adr_file(adr_env.adr_dir, 26001, "First", "first")

        # Don't create index - let fix create it
        fix_index()

        assert adr_env.index_path.exists()
        entries = parse_index()
        assert len(entries) == 1

    def test_superseded_entry_has_annotation(self, adr_env):
        """Superseded ADRs should include 'superseded by' annotation in index."""
        from tools.scripts.check_adr import fix_index, parse_index

        create_adr_file_full(
            adr_env.adr_dir, 26001, "Old Decision", "old_decision",
            status="superseded", superseded_by="ADR-26002",
        )
        create_adr_file_full(
            adr_env.adr_dir, 26002, "New Decision", "new_decision",
            status="accepted",
        )

        fix_index()

        content = adr_env.index_path.read_text(encoding="utf-8")
        # Superseded entry should have annotation
        assert "superseded by" in content.lower()
        assert "ADR-26002" in content

    def test_non_superseded_entry_has_no_annotation(self, adr_env):
        """Non-superseded ADRs should NOT have 'superseded by' annotation."""
        from tools.scripts.check_adr import fix_index

        create_adr_file_full(
            adr_env.adr_dir, 26001, "Active Decision", "active_decision",
            status="accepted",
        )

        fix_index()

        content = adr_env.index_path.read_text(encoding="utf-8")
        assert "superseded by" not in content.lower()


# ======================
# Integration Tests: CLI
# ======================


class TestCli:
    """Integration tests for command-line interface."""

    def test_exit_code_0_when_synced(self, synced_env):
        """Should exit with 0 when ADRs are in sync."""
        from tools.scripts.check_adr import main

        exit_code = main([])

        assert exit_code == 0

    def test_exit_code_1_when_out_of_sync(self, synced_env):
        """Should exit with 1 when ADRs are out of sync."""
        from tools.scripts.check_adr import main

        # Add ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        exit_code = main([])

        assert exit_code == 1

    def test_verbose_flag_shows_output(self, synced_env, capsys):
        """Verbose flag should produce output even when in sync."""
        from tools.scripts.check_adr import main

        main(["--verbose"])

        captured = capsys.readouterr()
        assert captured.out  # Verbose mode should produce output

    def test_fix_flag_modifies_index(self, synced_env):
        """Fix flag should modify the index file."""
        from tools.scripts.check_adr import main, parse_index

        # Add ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        exit_code = main(["--fix"])

        # Should succeed after fix
        assert exit_code == 0

        # Entry should now be in index
        entries = parse_index()
        numbers = {e.number for e in entries}
        assert 26004 in numbers

    def test_fix_reports_changes(self, synced_env, capsys):
        """Fix should produce output when changes are made."""
        from tools.scripts.check_adr import main

        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        main(["--fix"])

        captured = capsys.readouterr()
        assert captured.out  # Should inform user about changes

    def test_check_staged_with_no_staged_files(self, synced_env, capsys):
        """Check-staged with no staged ADR files should pass."""
        from tools.scripts.check_adr import main

        with patch("tools.scripts.check_adr.get_staged_adr_files", return_value=[]):
            exit_code = main(["--check-staged"])

        assert exit_code == 0

    def test_main_entry_point(self, synced_env, monkeypatch):
        """Cover the __main__ block."""
        monkeypatch.setattr("sys.argv", ["check_adr.py", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path("tools/scripts/check_adr.py", run_name="__main__")

        assert exc_info.value.code == 0

    def test_fix_verbose_mode(self, synced_env, capsys):
        """Fix with verbose flag should produce output."""
        from tools.scripts.check_adr import main

        exit_code = main(["--fix", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose fix should produce output

    def test_fix_no_changes_verbose(self, synced_env, capsys):
        """Fix with no changes needed should produce output in verbose mode."""
        from tools.scripts.check_adr import main

        exit_code = main(["--fix", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Should inform user even when no changes needed

    def test_fix_with_errors_remaining(self, adr_env, capsys):
        """Fix should fail if unfixable errors remain (e.g., duplicates)."""
        from tools.scripts.check_adr import main

        # Create duplicate ADR numbers (can't be auto-fixed)
        create_adr_file(adr_env.adr_dir, 26001, "First Version", "first_version")
        dup_file = adr_env.adr_dir / "adr_26001_duplicate.md"
        dup_file.write_text("# ADR-26001: Duplicate\n\n## Status\n\nAccepted\n", encoding="utf-8")

        exit_code = main(["--fix"])

        # Should fail because duplicates can't be auto-fixed
        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out  # Should explain why fix failed

    def test_check_staged_verbose_with_staged_files(self, synced_env, capsys):
        """Check-staged with verbose should produce output when files are staged."""
        from tools.scripts.check_adr import main

        with patch("tools.scripts.check_adr.get_staged_adr_files") as mock_staged:
            mock_staged.return_value = [Path("architecture/adr/adr_26001_first_feature.md")]
            exit_code = main(["--check-staged", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose should produce output

    def test_check_staged_verbose_no_staged_files(self, synced_env, capsys):
        """Check-staged with verbose and no staged files should produce output."""
        from tools.scripts.check_adr import main

        with patch("tools.scripts.check_adr.get_staged_adr_files") as mock_staged:
            mock_staged.return_value = []
            exit_code = main(["--check-staged", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose should produce output

    def test_missing_index_with_adr_files(self, adr_env, capsys):
        """Missing index with existing ADR files should fail."""
        from tools.scripts.check_adr import main

        create_adr_file(adr_env.adr_dir, 26001, "Test", "test")
        # Don't create index

        exit_code = main([])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out  # Should explain the error

    def test_missing_index_no_adr_files_verbose(self, adr_env, capsys):
        """Missing index with no ADR files should pass in verbose mode."""
        from tools.scripts.check_adr import main

        # No ADR files, no index
        exit_code = main(["--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose should produce output



# ======================
# Edge Cases
# ======================


class TestGetStagedAdrFiles:
    """Tests for git staged file detection."""

    def test_returns_staged_adr_files(self, adr_env):
        """Should return list of staged ADR files."""
        from tools.scripts.check_adr import get_staged_adr_files

        staged_output = "architecture/adr/adr_26001_test.md\narchitecture/adr/adr_26002_other.md\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = staged_output
            files = get_staged_adr_files()

        assert len(files) == 2
        assert files[0] == Path("architecture/adr/adr_26001_test.md")

    def test_filters_non_adr_files(self, adr_env):
        """Should only return ADR files, not other staged files."""
        from tools.scripts.check_adr import get_staged_adr_files

        staged_output = "README.md\narchitecture/adr/adr_26001_test.md\narchitecture/adr_index.md\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = staged_output
            files = get_staged_adr_files()

        assert len(files) == 1
        assert "adr_26001" in str(files[0])

    def test_handles_git_error(self, adr_env):
        """Should return empty list on git error."""
        from tools.scripts.check_adr import get_staged_adr_files

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            files = get_staged_adr_files()

        assert files == []

    def test_handles_git_not_found(self, adr_env):
        """Should return empty list if git is not installed."""
        from tools.scripts.check_adr import get_staged_adr_files

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            files = get_staged_adr_files()

        assert files == []


# ======================
# Unit Tests: YAML Frontmatter Parsing
# ======================


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parses_valid_yaml_frontmatter(self, adr_env):
        """Should extract frontmatter from content with valid YAML."""
        from tools.scripts.check_adr import parse_frontmatter

        content = """---
title: Test ADR
status: accepted
tags: [python, architecture]
---

# ADR-26001: Test ADR

Content here.
"""
        result = parse_frontmatter(content)

        assert result is not None
        assert result["title"] == "Test ADR"
        assert result["status"] == "accepted"
        assert result["tags"] == ["python", "architecture"]

    def test_returns_none_when_no_frontmatter(self, adr_env):
        """Should return None when content has no frontmatter."""
        from tools.scripts.check_adr import parse_frontmatter

        content = """# ADR-26001: Test ADR

## Status

Accepted
"""
        result = parse_frontmatter(content)

        assert result is None

    def test_returns_none_for_invalid_yaml(self, adr_env):
        """Should return None when frontmatter contains invalid YAML."""
        from tools.scripts.check_adr import parse_frontmatter

        content = """---
title: Test ADR
status: [invalid: yaml: here
---

# ADR-26001: Test ADR
"""
        result = parse_frontmatter(content)

        assert result is None


# ======================
# Unit Tests: Status Extraction
# ======================


class TestExtractStatus:
    """Tests for status extraction from ADR files."""

    def test_extracts_status_from_yaml_frontmatter(self, adr_env):
        """Should extract status from YAML frontmatter."""
        from tools.scripts.check_adr import extract_status

        content = """---
title: Test ADR
status: accepted
---

# ADR-26001: Test ADR
"""
        result = extract_status(content)

        assert result == "accepted"

    def test_extracts_status_from_markdown_section(self, adr_env):
        """Should extract status from ## Status section (old format)."""
        from tools.scripts.check_adr import extract_status

        content = """# ADR-26001: Test ADR

## Status

Accepted

## Context

Some context.
"""
        result = extract_status(content)

        assert result == "accepted"

    def test_yaml_frontmatter_takes_priority(self, adr_env):
        """When both formats exist, YAML frontmatter should take priority."""
        from tools.scripts.check_adr import extract_status

        content = """---
title: Test ADR
status: proposed
---

# ADR-26001: Test ADR

## Status

Accepted
"""
        result = extract_status(content)

        assert result == "proposed"

    def test_returns_none_when_no_status(self, adr_env):
        """Should return None when no status is found in either format."""
        from tools.scripts.check_adr import extract_status

        content = """# ADR-26001: Test ADR

## Context

No status section here.
"""
        result = extract_status(content)

        assert result is None

    def test_normalizes_status_to_lowercase(self, adr_env):
        """Status should be normalized to lowercase."""
        from tools.scripts.check_adr import extract_status

        content = """# ADR-26001: Test ADR

## Status

ACCEPTED

## Context
"""
        result = extract_status(content)

        assert result == "accepted"


# ======================
# Unit Tests: Status Validation
# ======================


class TestStatusValidation:
    """Tests for status validation in validate_sync."""

    def test_valid_status_passes_validation(self, adr_env):
        """ADR with valid status should not produce errors."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="accepted")
        create_index(
            adr_env.index_path,
            [(26001, "Test ADR", "/architecture/adr/adr_26001_test_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert not any(e.error_type == "invalid_status" for e in errors)

    def test_invalid_status_produces_error(self, adr_env):
        """ADR with invalid status should produce validation error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="invalid_status")
        create_index(
            adr_env.index_path,
            [(26001, "Test ADR", "/architecture/adr/adr_26001_test_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "invalid_status" for e in errors)

    def test_all_valid_statuses_pass(self, adr_env):
        """All valid status values defined in module should pass validation."""
        from tools.scripts.check_adr import VALID_STATUSES, get_adr_files, parse_index, validate_sync

        # Test each valid status from the module's own definition
        for i, status in enumerate(sorted(VALID_STATUSES)):
            adr_num = 26001 + i
            create_adr_file_with_frontmatter(adr_env.adr_dir, adr_num, f"Test ADR {i}", f"test_adr_{i}", status=status)

        # Create matching index entries
        entries = [
            (26001 + i, f"Test ADR {i}", f"/architecture/adr/adr_{26001 + i}_test_adr_{i}.md")
            for i in range(len(VALID_STATUSES))
        ]
        create_index(adr_env.index_path, entries)

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # None of the valid statuses should produce status-related errors
        status_errors = [e for e in errors if "status" in e.error_type.lower()]
        assert status_errors == []


# ======================
# Unit Tests: Mixed Format Coexistence
# ======================


class TestMixedFormatCoexistence:
    """Tests for handling both old (markdown) and new (YAML) ADR formats."""

    def test_discovers_both_formats(self, adr_env):
        """Should discover ADR files in both old and new formats."""
        from tools.scripts.check_adr import get_adr_files

        # Old format (markdown Status section)
        create_adr_file(adr_env.adr_dir, 26001, "Old Format ADR", "old_format")
        # New format (YAML frontmatter)
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "New Format ADR", "new_format", status="accepted")

        files = get_adr_files()

        assert len(files) == 2
        numbers = {f.number for f in files}
        assert numbers == {26001, 26002}

    def test_validates_both_formats(self, adr_env):
        """Validation should work for both old and new formats."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Old format (legacy, will have missing field/section errors)
        create_legacy_adr_file(adr_env.adr_dir, 26001, "Old Format", "old_format")
        # New format (complete)
        create_adr_file_full(adr_env.adr_dir, 26002, "New Format", "new_format", status="accepted")

        create_index(
            adr_env.index_path,
            [
                (26001, "Old Format", "/architecture/adr/adr_26001_old_format.md"),
                (26002, "New Format", "/architecture/adr/adr_26002_new_format.md"),
            ],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should have no index sync errors (missing_in_index, orphan_in_index, etc.)
        # Format errors (missing_field, missing_section) are expected for legacy files
        sync_error_types = {"missing_in_index", "orphan_in_index", "wrong_link", "wrong_order", "duplicate_number"}
        sync_errors = [e for e in errors if e.error_type in sync_error_types]
        assert sync_errors == []


# ======================
# Unit Tests: Title Mismatch Handling
# ======================


# ======================
# Unit Tests: Status Fix
# ======================


class TestFixInvalidStatus:
    """Tests for fixing invalid statuses in ADR files."""

    def test_fix_with_suggested_correction_accepted(self, adr_env, monkeypatch):
        """Should fix status when user accepts suggested correction."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files, parse_frontmatter

        # Create ADR with typo in status (prposed -> proposed)
        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user accepting suggested fix (empty input = yes)
        monkeypatch.setattr("builtins.input", lambda _: "")

        result = fix_invalid_status(adr_file)

        assert result is True
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter["status"] == "proposed"

    def test_fix_with_custom_status(self, adr_env, monkeypatch):
        """Should fix status when user provides custom valid status."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files, parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user typing custom status
        monkeypatch.setattr("builtins.input", lambda _: "accepted")

        result = fix_invalid_status(adr_file)

        assert result is True
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter["status"] == "accepted"

    def test_fix_rejected_by_user(self, adr_env, monkeypatch):
        """Should return False when user rejects the fix."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user rejecting
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = fix_invalid_status(adr_file)

        assert result is False

    def test_fix_unknown_typo_with_manual_input(self, adr_env, monkeypatch):
        """Should prompt for manual input when typo is not in corrections list."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files, parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="unknownstatus"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user typing valid status
        monkeypatch.setattr("builtins.input", lambda _: "rejected")

        result = fix_invalid_status(adr_file)

        assert result is True
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter["status"] == "rejected"

    def test_fix_skipped_when_empty_input(self, adr_env, monkeypatch):
        """Should skip fix when user provides empty input for unknown typo."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="unknownstatus"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user skipping (empty input for unknown typo)
        monkeypatch.setattr("builtins.input", lambda _: "")

        result = fix_invalid_status(adr_file)

        assert result is False

    def test_fix_invalid_custom_status_rejected(self, adr_env, monkeypatch):
        """Should reject when user provides invalid custom status."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="prposed"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user typing invalid status
        monkeypatch.setattr("builtins.input", lambda _: "notavalidstatus")

        result = fix_invalid_status(adr_file)

        assert result is False

    def test_fix_valid_status_returns_true(self, adr_env):
        """Should return True immediately for valid status (no-op)."""
        from tools.scripts.check_adr import fix_invalid_status, get_adr_files

        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Test ADR", "test_adr", status="accepted"
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        result = fix_invalid_status(adr_file)

        assert result is True

    def test_fix_old_format_markdown_status(self, adr_env, monkeypatch):
        """Should fix status in old markdown format (no YAML frontmatter)."""
        from tools.scripts.check_adr import extract_status, fix_invalid_status, get_adr_files

        # Create old-format ADR with typo in status section
        filepath = adr_env.adr_dir / "adr_26001_old_format.md"
        content = """# ADR-26001: Old Format ADR

## Status

Prposed

## Context

Some context.
"""
        filepath.write_text(content, encoding="utf-8")

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user accepting suggested fix
        monkeypatch.setattr("builtins.input", lambda _: "")

        result = fix_invalid_status(adr_file)

        assert result is True
        # Verify the markdown status section was updated
        new_content = filepath.read_text(encoding="utf-8")
        new_status = extract_status(new_content)
        assert new_status == "proposed"


class TestTitleMismatchHandling:
    """Tests for detecting and fixing title mismatches between header and frontmatter."""

    def test_detects_title_mismatch(self, adr_env):
        """Should detect when frontmatter title differs from header title."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADR with mismatched titles
        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "test_adr",
            status="accepted",
            frontmatter_title="Different Frontmatter Title",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Header Title", "/architecture/adr/adr_26001_test_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "title_mismatch" for e in errors)

    def test_fix_title_mismatch_updates_frontmatter(self, adr_env, monkeypatch):
        """Fix should update frontmatter title to match header when user confirms."""
        from tools.scripts.check_adr import fix_title_mismatch, get_adr_files, parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "test_adr",
            status="accepted",
            frontmatter_title="Wrong Title",
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user confirming the fix
        monkeypatch.setattr("builtins.input", lambda _: "y")

        result = fix_title_mismatch(adr_file)

        assert result is True
        # Verify the file was updated by parsing the frontmatter
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("title") == "Header Title"

    def test_fix_title_mismatch_rejected_returns_false(self, adr_env, monkeypatch):
        """Fix should return False when user rejects the fix."""
        from tools.scripts.check_adr import fix_title_mismatch, get_adr_files, parse_frontmatter

        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "test_adr",
            status="accepted",
            frontmatter_title="Wrong Title",
        )

        adr_files = get_adr_files()
        adr_file = adr_files[0]

        # Simulate user rejecting the fix
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = fix_title_mismatch(adr_file)

        assert result is False
        # Verify the file was NOT updated by parsing the frontmatter
        content = adr_file.path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("title") == "Wrong Title"


# ======================
# Unit Tests: Partitioned Index
# ======================


class TestPartitionedIndex:
    """Tests for state-partitioned index generation."""

    def test_groups_adrs_by_status(self, adr_env):
        """Fix should group ADRs by status into different sections."""
        from tools.scripts.check_adr import STATUS_SECTIONS, fix_index, parse_index

        # Create ADRs with different statuses
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "Accepted ADR", "accepted_adr", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "Proposed ADR", "proposed_adr", status="proposed")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26003, "Rejected ADR", "rejected_adr", status="rejected")

        fix_index()

        entries = parse_index()

        # Check that entries are grouped according to STATUS_SECTIONS mapping
        accepted_entry = next(e for e in entries if e.number == 26001)
        proposed_entry = next(e for e in entries if e.number == 26002)
        rejected_entry = next(e for e in entries if e.number == 26003)

        # Use the module's own mapping to verify section assignment
        assert accepted_entry.section == STATUS_SECTIONS["accepted"]
        assert proposed_entry.section == STATUS_SECTIONS["proposed"]
        assert rejected_entry.section == STATUS_SECTIONS["rejected"]

    def test_adrs_with_same_status_grouped_together(self, adr_env):
        """ADRs with the same status should appear in the same section."""
        from tools.scripts.check_adr import fix_index, parse_index

        # Create multiple ADRs with same status
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "First Accepted", "first", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "Second Accepted", "second", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26003, "Third Accepted", "third", status="accepted")

        fix_index()

        entries = parse_index()

        # All entries should be in the same section
        sections = {e.section for e in entries}
        assert len(sections) == 1

    def test_numerical_order_within_sections(self, adr_env):
        """ADRs should be in numerical order within each section."""
        from tools.scripts.check_adr import fix_index, parse_index

        # Create ADRs in non-sequential order
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26003, "Third Accepted", "third", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "First Accepted", "first", status="accepted")
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26002, "Second Accepted", "second", status="accepted")

        fix_index()

        entries = parse_index()
        # Get entries from any section (they're all in same section)
        section = entries[0].section
        numbers = [e.number for e in entries if e.section == section]

        assert numbers == sorted(numbers)

    def test_default_section_for_no_status(self, adr_env):
        """ADRs without explicit status should be treated as proposed."""
        from tools.scripts.check_adr import STATUS_SECTIONS, fix_index, parse_index

        # Create old-format ADR without explicit status
        filepath = adr_env.adr_dir / "adr_26001_no_status.md"
        content = """# ADR-26001: No Status ADR

## Context

Some context without a status section.
"""
        filepath.write_text(content, encoding="utf-8")

        fix_index()

        entries = parse_index()
        entry = next(e for e in entries if e.number == 26001)

        # Should be in the same section as "proposed" ADRs
        assert entry.section == STATUS_SECTIONS["proposed"]

    def test_validates_section_placement(self, adr_env):
        """Should detect ADRs placed in a section that doesn't match their status."""
        from tools.scripts.check_adr import STATUS_SECTIONS, get_adr_files, parse_index, validate_sync

        # Create accepted ADR
        create_adr_file_with_frontmatter(adr_env.adr_dir, 26001, "Accepted ADR", "accepted_adr", status="accepted")

        # Get the section name for "proposed" (different from "accepted")
        wrong_section = STATUS_SECTIONS["proposed"]

        # Create index with ADR in wrong section
        content = f"""# ADR Index

## {wrong_section}

:::{{glossary}}
ADR-26001
: [Accepted ADR](/architecture/adr/adr_26001_accepted_adr.md)
:::
"""
        adr_env.index_path.write_text(content, encoding="utf-8")

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should have an error (type doesn't matter, just that it's detected)
        assert len(errors) > 0
        # At least one error should mention the ADR number
        assert any(e.number == 26001 for e in errors)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_adr_number_in_header_differs_from_filename(self, adr_env):
        """Header number should be authoritative over filename number."""
        from tools.scripts.check_adr import get_adr_files

        # Create file with mismatched numbers
        filepath = adr_env.adr_dir / "adr_26001_test.md"
        filepath.write_text("# ADR-26002: Different Number\n\n## Status\n\nAccepted\n", encoding="utf-8")

        files = get_adr_files()

        # Should use header number (26002), not filename number (26001)
        assert len(files) == 1
        assert files[0].number == 26002

    def test_title_with_special_characters(self, adr_env):
        """Titles with special characters should be handled correctly."""
        from tools.scripts.check_adr import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Use: Python & OOP (v2.0)", "python_oop")

        files = get_adr_files()

        assert len(files) == 1
        assert "Python & OOP" in files[0].title

    def test_index_with_extra_whitespace(self, adr_env):
        """Index with extra whitespace should be parsed correctly."""
        from tools.scripts.check_adr import parse_index

        # Write index with extra blank lines
        content = """# ADR Index

:::{glossary}
ADR-26001
: [First ADR](/architecture/adr/adr_26001_first.md)


ADR-26002
: [Second ADR](/architecture/adr/adr_26002_second.md)
:::
"""
        adr_env.index_path.write_text(content, encoding="utf-8")

        entries = parse_index()

        assert len(entries) == 2

    def test_link_with_relative_path(self, adr_env):
        """Index entry with relative path should be detected as wrong."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file(adr_env.adr_dir, 26001, "Test", "test")

        # Create index with relative path
        create_index(
            adr_env.index_path,
            [(26001, "Test", "adr/adr_26001_test.md")],  # Relative, not absolute
        )

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        # Should detect wrong link format
        assert any(e.error_type == "wrong_link" for e in errors)

    def test_empty_adr_directory_and_empty_index(self, adr_env):
        """Both empty directory and empty index should result in no errors."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_empty_index(adr_env.index_path)

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        assert errors == []


# ======================
# Unit Tests: Frontmatter Field Validation
# ======================


class TestValidateFrontmatterFields:
    """Tests for required frontmatter field validation."""

    def test_all_required_fields_present_passes(self, adr_env):
        """ADR with all required frontmatter fields should pass validation."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Complete ADR",
            "complete_adr",
            status="accepted",
            tags=["architecture"],
            date="2024-01-15",
            adr_id="26001",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Complete ADR", "/architecture/adr/adr_26001_complete_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert not any(e.error_type == "missing_field" for e in errors)

    def test_missing_required_field_produces_error(self, adr_env):
        """ADR missing required frontmatter field should produce error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADR with missing 'id' field (using old helper that doesn't include id)
        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Incomplete ADR",
            "incomplete_adr",
            status="accepted",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Incomplete ADR", "/architecture/adr/adr_26001_incomplete_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "missing_field" for e in errors)

    def test_optional_superseded_by_field_ok(self, adr_env):
        """Optional superseded_by field should not cause errors when missing."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "ADR Without Superseded By",
            "no_superseded",
            status="accepted",
        )
        create_index(
            adr_env.index_path,
            [(26001, "ADR Without Superseded By", "/architecture/adr/adr_26001_no_superseded.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # No error for missing optional field
        assert not any("superseded_by" in e.message for e in errors)

    def test_no_frontmatter_produces_error(self, adr_env):
        """ADR without YAML frontmatter should produce missing field errors."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")
        create_index(
            adr_env.index_path,
            [(26001, "Legacy ADR", "/architecture/adr/adr_26001_legacy_adr.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should have missing field errors for legacy files
        assert any(e.error_type == "missing_field" for e in errors)


# ======================
# Unit Tests: Date Format Validation
# ======================


class TestValidateDateFormat:
    """Tests for date format validation."""

    def test_valid_date_format_passes(self, adr_env):
        """Date in YYYY-MM-DD format should pass validation."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Valid Date ADR",
            "valid_date",
            date="2024-01-15",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Valid Date ADR", "/architecture/adr/adr_26001_valid_date.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert not any(e.error_type == "invalid_date" for e in errors)

    def test_invalid_date_format_produces_error(self, adr_env):
        """Date not in YYYY-MM-DD format should produce error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Invalid Date ADR",
            "invalid_date",
            date="01/15/2024",  # Wrong format
        )
        create_index(
            adr_env.index_path,
            [(26001, "Invalid Date ADR", "/architecture/adr/adr_26001_invalid_date.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "invalid_date" for e in errors)

    def test_missing_date_produces_missing_field_error(self, adr_env):
        """Missing date field should produce missing field error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADR without date field (using old helper)
        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "No Date ADR",
            "no_date",
            status="accepted",
        )
        create_index(
            adr_env.index_path,
            [(26001, "No Date ADR", "/architecture/adr/adr_26001_no_date.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should have missing field error for date
        assert any(e.error_type == "missing_field" and "date" in e.message for e in errors)

    def test_date_edge_cases(self, adr_env):
        """Date validation should handle edge cases correctly."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADR with text date instead of ISO format
        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Text Date ADR",
            "text_date",
            date="January 15, 2024",  # Wrong format
        )
        create_index(
            adr_env.index_path,
            [(26001, "Text Date ADR", "/architecture/adr/adr_26001_text_date.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "invalid_date" for e in errors)


# ======================
# Unit Tests: Tag Validation
# ======================


class TestValidateTags:
    """Tests for tag validation."""

    def test_all_valid_tags_pass(self, adr_env):
        """ADR with all valid tags should pass validation."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Valid Tags ADR",
            "valid_tags",
            tags=["architecture", "documentation"],
        )
        create_index(
            adr_env.index_path,
            [(26001, "Valid Tags ADR", "/architecture/adr/adr_26001_valid_tags.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert not any(e.error_type == "invalid_tag" for e in errors)

    def test_invalid_tag_produces_error(self, adr_env):
        """ADR with invalid tag should produce error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Invalid Tag ADR",
            "invalid_tag",
            tags=["architecture", "nonexistent_tag"],
        )
        create_index(
            adr_env.index_path,
            [(26001, "Invalid Tag ADR", "/architecture/adr/adr_26001_invalid_tag.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert any(e.error_type == "invalid_tag" for e in errors)

    def test_empty_tags_list_produces_error(self, adr_env):
        """ADR with empty tags list should produce error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Empty Tags ADR",
            "empty_tags",
            tags=[],
        )
        create_index(
            adr_env.index_path,
            [(26001, "Empty Tags ADR", "/architecture/adr/adr_26001_empty_tags.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Empty tags should produce an error (tags is required and must have at least one)
        assert any(e.error_type == "empty_tags" or (e.error_type == "invalid_tag" and "empty" in e.message.lower()) for e in errors)

    def test_mixed_valid_invalid_tags(self, adr_env):
        """ADR with mix of valid and invalid tags should produce error for invalid ones."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Mixed Tags ADR",
            "mixed_tags",
            tags=["architecture", "bad_tag", "documentation"],
        )
        create_index(
            adr_env.index_path,
            [(26001, "Mixed Tags ADR", "/architecture/adr/adr_26001_mixed_tags.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        invalid_tag_errors = [e for e in errors if e.error_type == "invalid_tag"]
        assert len(invalid_tag_errors) >= 1
        assert any("bad_tag" in e.message for e in invalid_tag_errors)


# ======================
# Unit Tests: Section Validation
# ======================


class TestValidateSections:
    """Tests for required section validation."""

    def test_all_required_sections_present_passes(self, adr_env):
        """ADR with all required sections should pass validation."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Don't pass sections= to use defaults from REQUIRED_SECTIONS (config-driven)
        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Complete Sections ADR",
            "complete_sections",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Complete Sections ADR", "/architecture/adr/adr_26001_complete_sections.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        assert not any(e.error_type == "missing_section" for e in errors)

    def test_missing_required_section_produces_error(self, adr_env):
        """ADR missing required section should produce error."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Incomplete Sections ADR",
            "incomplete_sections",
            sections=["Context", "Decision", "Consequences"],  # Missing Alternatives, References, Participants
        )
        create_index(
            adr_env.index_path,
            [(26001, "Incomplete Sections ADR", "/architecture/adr/adr_26001_incomplete_sections.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        assert len(missing_section_errors) >= 1

    def test_partial_sections_reports_all_missing(self, adr_env):
        """Should report all missing sections, not just the first one."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Partial Sections ADR",
            "partial_sections",
            sections=["Context", "Decision"],  # Missing many sections
        )
        create_index(
            adr_env.index_path,
            [(26001, "Partial Sections ADR", "/architecture/adr/adr_26001_partial_sections.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        # Should have errors for Consequences, Alternatives, References, Participants
        assert len(missing_section_errors) >= 4

    def test_subsections_warning_not_error(self, adr_env):
        """Missing recommended subsections should not produce errors (only warnings)."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "No Subsections ADR",
            "no_subsections",
            sections=["Context", "Decision", "Consequences", "Alternatives", "References", "Participants"],
            include_subsections=False,  # Don't include Positive/Negative subsections
        )
        create_index(
            adr_env.index_path,
            [(26001, "No Subsections ADR", "/architecture/adr/adr_26001_no_subsections.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should not fail on missing subsections (they're recommended, not required)
        assert not any(e.error_type == "missing_subsection" for e in errors)

    def test_section_case_sensitivity(self, adr_env):
        """Section validation should be case-sensitive."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADR with lowercase section names
        filepath = adr_env.adr_dir / "adr_26001_lowercase.md"
        content = """---
id: 26001
title: Lowercase Sections ADR
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26001: Lowercase Sections ADR

## context

Content.

## decision

Content.

## consequences

Content.

## alternatives

Content.

## references

Content.

## participants

Content.
"""
        filepath.write_text(content, encoding="utf-8")
        create_index(
            adr_env.index_path,
            [(26001, "Lowercase Sections ADR", "/architecture/adr/adr_26001_lowercase.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Lowercase sections should not match required sections (case-sensitive)
        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        assert len(missing_section_errors) >= 1


# ======================
# Unit Tests: Legacy ADR Migration
# ======================


class TestMigrateLegacyAdr:
    """Tests for legacy ADR migration functionality."""

    def test_migrate_adds_frontmatter(self, adr_env):
        """Migration should add YAML frontmatter to legacy file."""
        from tools.scripts.check_adr import migrate_legacy_adr, parse_frontmatter

        filepath = create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert "title" in frontmatter
        assert "status" in frontmatter

    def test_migrate_preserves_content(self, adr_env):
        """Migration should preserve the document body unchanged."""
        from tools.scripts.check_adr import migrate_legacy_adr

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            sections=["Context", "Decision"],
        )
        original_body = "## Context\n"  # Part of the original content

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        assert original_body in content

    def test_migrate_extracts_status(self, adr_env):
        """Migration should extract status from ## Status section."""
        from tools.scripts.check_adr import migrate_legacy_adr, parse_frontmatter

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            status="Accepted",  # Status in markdown section
        )

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("status") == "accepted"

    def test_migrate_skips_files_with_frontmatter(self, adr_env):
        """Migration should skip files that already have YAML frontmatter."""
        from tools.scripts.check_adr import migrate_legacy_adr, parse_frontmatter

        # Create file with existing frontmatter
        filepath = create_adr_file_full(
            adr_env.adr_dir,
            26001,
            "Already Migrated",
            "already_migrated",
            status="proposed",
        )
        original_content = filepath.read_text(encoding="utf-8")

        result = migrate_legacy_adr(filepath)

        # Should return False (no changes made) or True (idempotent)
        # Either way, content should be unchanged
        new_content = filepath.read_text(encoding="utf-8")
        assert new_content == original_content

    def test_migrate_with_invalid_status_typo(self, adr_env):
        """Migration should correct status typos using corrections map."""
        from tools.scripts.check_adr import migrate_legacy_adr, parse_frontmatter

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            status="Prposed",  # Typo that should be corrected
        )

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("status") == "proposed"  # Corrected

    def test_migrate_with_unknown_status_uses_default(self, adr_env):
        """Migration should use default status for unknown status values."""
        from tools.scripts.check_adr import DEFAULT_STATUS, migrate_legacy_adr, parse_frontmatter

        filepath = create_legacy_adr_file(
            adr_env.adr_dir,
            26001,
            "Legacy ADR",
            "legacy_adr",
            status="UnknownStatus",  # Not in corrections map
        )

        result = migrate_legacy_adr(filepath)

        assert result is True
        content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("status") == DEFAULT_STATUS

    def test_migrate_without_status_section(self, adr_env):
        """Migration should use default status when no Status section exists."""
        from tools.scripts.check_adr import DEFAULT_STATUS, migrate_legacy_adr, parse_frontmatter

        # Create file without Status section
        filepath = adr_env.adr_dir / "adr_26001_no_status.md"
        content = """# ADR-26001: No Status ADR

## Context

Some context.
"""
        filepath.write_text(content, encoding="utf-8")

        result = migrate_legacy_adr(filepath)

        assert result is True
        new_content = filepath.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(new_content)
        assert frontmatter is not None
        assert frontmatter.get("status") == DEFAULT_STATUS

    def test_migrate_skips_file_without_valid_header(self, adr_env):
        """Migration should skip files without valid ADR header."""
        from tools.scripts.check_adr import migrate_legacy_adr

        # Create file without valid header
        filepath = adr_env.adr_dir / "adr_26001_invalid.md"
        content = """# Not an ADR header

Some content.
"""
        filepath.write_text(content, encoding="utf-8")

        result = migrate_legacy_adr(filepath)

        assert result is False  # Can't migrate without valid header


# ======================
# Unit Tests: CLI Migration Mode
# ======================


class TestCliMigrateMode:
    """Tests for --migrate CLI mode."""

    def test_migrate_mode_migrates_legacy_files(self, adr_env, capsys):
        """--migrate should add frontmatter to legacy ADR files."""
        from tools.scripts.check_adr import main

        create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")

        exit_code = main(["--migrate"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Migrated" in captured.out

    def test_migrate_mode_no_legacy_files(self, adr_env, capsys):
        """--migrate with no legacy files should report nothing to migrate."""
        from tools.scripts.check_adr import main

        # Create only files with frontmatter
        create_adr_file_full(adr_env.adr_dir, 26001, "Modern ADR", "modern_adr")

        exit_code = main(["--migrate"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No legacy ADRs found" in captured.out

    def test_migrate_mode_verbose(self, adr_env, capsys):
        """--migrate --verbose should show detailed output."""
        from tools.scripts.check_adr import main

        create_legacy_adr_file(adr_env.adr_dir, 26001, "Legacy ADR", "legacy_adr")

        exit_code = main(["--migrate", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Running in migrate mode" in captured.out


# ======================
# Unit Tests: Tag Edge Cases
# ======================


class TestTagEdgeCases:
    """Tests for tag validation edge cases."""

    def test_single_tag_as_string(self, adr_env):
        """Single tag provided as string (not list) should be handled."""
        from tools.scripts.check_adr import get_adr_files, parse_index, validate_sync

        # Create ADR with single tag as string in YAML
        filepath = adr_env.adr_dir / "adr_26001_single_tag.md"
        content = """---
id: 26001
title: Single Tag ADR
date: 2024-01-15
status: proposed
tags: architecture
---

# ADR-26001: Single Tag ADR

## Context

Content.

## Decision

Content.

## Consequences

Content.

## Alternatives

Content.

## References

Content.

## Participants

Content.
"""
        filepath.write_text(content, encoding="utf-8")
        create_index(
            adr_env.index_path,
            [(26001, "Single Tag ADR", "/architecture/adr/adr_26001_single_tag.md")],
        )

        adr_files = get_adr_files()
        index_entries = parse_index()
        errors = validate_sync(adr_files, index_entries)

        # Should not produce invalid_tag error for valid single tag
        assert not any(e.error_type == "invalid_tag" for e in errors)


# ======================
# Unit Tests: Fix Mode Edge Cases
# ======================


class TestFixModeEdgeCases:
    """Tests for --fix mode edge cases."""

    def test_fix_with_invalid_status(self, adr_env, monkeypatch, capsys):
        """--fix should prompt to fix invalid status."""
        from tools.scripts.check_adr import main

        # Create ADR with invalid status
        create_adr_file_with_frontmatter(
            adr_env.adr_dir, 26001, "Invalid Status ADR", "invalid_status", status="prposed"
        )

        # Simulate user accepting the fix
        monkeypatch.setattr("builtins.input", lambda _: "")

        exit_code = main(["--fix"])

        captured = capsys.readouterr()
        assert "prposed" in captured.out  # Should show the typo

    def test_fix_with_title_mismatch(self, adr_env, monkeypatch, capsys):
        """--fix should prompt to fix title mismatch."""
        from tools.scripts.check_adr import main

        # Create ADR with mismatched titles
        create_adr_file_with_frontmatter(
            adr_env.adr_dir,
            26001,
            "Header Title",
            "mismatch",
            status="accepted",
            frontmatter_title="Different Title",
        )
        create_index(
            adr_env.index_path,
            [(26001, "Header Title", "/architecture/adr/adr_26001_mismatch.md")],
        )

        # Simulate user accepting the fix
        monkeypatch.setattr("builtins.input", lambda _: "y")

        exit_code = main(["--fix"])

        captured = capsys.readouterr()
        assert "title mismatch" in captured.out.lower() or exit_code == 0


class TestSectionValidationEdgeCases:
    """Tests for section validation edge cases."""

    def test_adr_file_with_no_content(self, adr_env):
        """Should handle AdrFile with content=None."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        adr_file = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26001,
            title="Test",
            content=None,  # No content
        )

        errors = validate_sections(adr_file)

        assert errors == []  # Should return empty list, not crash


# ======================
# Term Reference Validation Tests
# ======================


def create_md_file_with_term_refs(directory: Path, name: str, content: str) -> Path:
    """Create a markdown file with term references.

    Args:
        directory: Directory to create file in
        name: Filename (without extension)
        content: File content

    Returns:
        Path to created file
    """
    filepath = directory / f"{name}.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


class TestTermReferenceDetection:
    """Tests for detecting MyST term reference patterns.

    Core contract: find_broken_term_references should identify {term}`ADR <space>`
    patterns that need to be changed to {term}`ADR-<hyphen>` format.
    """

    def test_detects_broken_space_format(self, adr_env):
        """Space separator in term ref should be detected as broken."""
        from tools.scripts.check_adr import find_broken_term_references

        content = "This references {term}`ADR 26001` which is wrong."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        broken = find_broken_term_references([filepath])

        assert len(broken) == 1
        assert broken[0].adr_number == 26001

    def test_valid_hyphen_format_not_flagged(self, adr_env):
        """Hyphen separator in term ref should NOT be flagged."""
        from tools.scripts.check_adr import find_broken_term_references

        content = "This references {term}`ADR-26001` which is correct."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        broken = find_broken_term_references([filepath])

        assert len(broken) == 0

    def test_detects_multiple_broken_refs_same_file(self, adr_env):
        """Multiple broken refs in one file should all be detected."""
        from tools.scripts.check_adr import find_broken_term_references

        content = """
See {term}`ADR 26001` and {term}`ADR 26002` for details.
Also {term}`ADR 26005` is relevant.
"""
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        broken = find_broken_term_references([filepath])

        numbers = {b.adr_number for b in broken}
        assert numbers == {26001, 26002, 26005}

    def test_detects_broken_refs_across_files(self, adr_env):
        """Broken refs should be detected across multiple files."""
        from tools.scripts.check_adr import find_broken_term_references

        content1 = "Reference {term}`ADR 26001` here."
        content2 = "Reference {term}`ADR 26002` there."

        file1 = create_md_file_with_term_refs(adr_env.adr_dir.parent, "doc1", content1)
        file2 = create_md_file_with_term_refs(adr_env.adr_dir.parent, "doc2", content2)

        broken = find_broken_term_references([file1, file2])

        numbers = {b.adr_number for b in broken}
        assert 26001 in numbers
        assert 26002 in numbers

    def test_mixed_valid_and_broken_refs(self, adr_env):
        """Only broken refs should be flagged, valid ones ignored."""
        from tools.scripts.check_adr import find_broken_term_references

        content = """
Valid: {term}`ADR-26001`
Broken: {term}`ADR 26002`
Valid: {term}`ADR-26003`
"""
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        broken = find_broken_term_references([filepath])

        assert len(broken) == 1
        assert broken[0].adr_number == 26002


class TestTermReferenceValidation:
    """Tests for validate_term_references function.

    Core contract: should return ValidationError list for broken refs.
    """

    def test_returns_validation_errors_for_broken_refs(self, adr_env):
        """Broken refs should produce ValidationError objects."""
        from tools.scripts.check_adr import validate_term_references

        content = "See {term}`ADR 26001` for details."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        errors = validate_term_references([filepath])

        assert len(errors) == 1
        assert errors[0].error_type == "broken_term_reference"

    def test_no_errors_for_valid_refs(self, adr_env):
        """Valid refs should produce no errors."""
        from tools.scripts.check_adr import validate_term_references

        content = "See {term}`ADR-26001` and {term}`ADR-26002` for details."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        errors = validate_term_references([filepath])

        assert len(errors) == 0

    def test_no_errors_for_no_term_refs(self, adr_env):
        """Files without term refs should produce no errors."""
        from tools.scripts.check_adr import validate_term_references

        content = "Just some regular markdown content without ADR references."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        errors = validate_term_references([filepath])

        assert len(errors) == 0


class TestTermReferenceFix:
    """Tests for fix_term_references function.

    Core contract: should replace space with hyphen in term refs
    and return list of modified files.
    """

    def test_fixes_space_to_hyphen(self, adr_env):
        """Space separator should be replaced with hyphen."""
        from tools.scripts.check_adr import fix_term_references

        content = "Reference {term}`ADR 26001` in text."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        modified = fix_term_references([filepath])

        assert filepath in modified
        new_content = filepath.read_text(encoding="utf-8")
        assert "{term}`ADR-26001`" in new_content
        assert "{term}`ADR 26001`" not in new_content

    def test_fixes_multiple_refs_in_file(self, adr_env):
        """All broken refs in a file should be fixed."""
        from tools.scripts.check_adr import fix_term_references

        content = "{term}`ADR 26001` and {term}`ADR 26002` referenced."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        fix_term_references([filepath])

        new_content = filepath.read_text(encoding="utf-8")
        # No space-separated refs should remain
        assert "{term}`ADR " not in new_content
        # Both should be fixed
        assert "{term}`ADR-26001`" in new_content
        assert "{term}`ADR-26002`" in new_content

    def test_preserves_valid_refs(self, adr_env):
        """Valid refs should remain unchanged after fix."""
        from tools.scripts.check_adr import fix_term_references

        content = "Valid {term}`ADR-26001` and broken {term}`ADR 26002` refs."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        fix_term_references([filepath])

        new_content = filepath.read_text(encoding="utf-8")
        # Valid ref count should be unchanged
        assert new_content.count("{term}`ADR-26001`") == 1
        # Broken one should be fixed
        assert "{term}`ADR-26002`" in new_content

    def test_returns_empty_for_no_broken_refs(self, adr_env):
        """No modifications when all refs are valid."""
        from tools.scripts.check_adr import fix_term_references

        content = "All valid: {term}`ADR-26001` and {term}`ADR-26002`."
        filepath = create_md_file_with_term_refs(
            adr_env.adr_dir.parent, "test_doc", content
        )

        modified = fix_term_references([filepath])

        assert len(modified) == 0

    def test_fixes_refs_across_multiple_files(self, adr_env):
        """Refs should be fixed in all provided files."""
        from tools.scripts.check_adr import fix_term_references

        content1 = "File 1: {term}`ADR 26001`"
        content2 = "File 2: {term}`ADR 26002`"

        file1 = create_md_file_with_term_refs(adr_env.adr_dir.parent, "doc1", content1)
        file2 = create_md_file_with_term_refs(adr_env.adr_dir.parent, "doc2", content2)

        modified = fix_term_references([file1, file2])

        assert len(modified) == 2
        assert "{term}`ADR-26001`" in file1.read_text(encoding="utf-8")
        assert "{term}`ADR-26002`" in file2.read_text(encoding="utf-8")


class TestTermReferenceCliFlags:
    """Tests for --check-terms and --fix-terms CLI flags.

    Core contract:
    - --check-terms: exit 1 if broken refs found, exit 0 otherwise
    - --fix-terms: fix broken refs and exit 0
    """

    def test_check_terms_fails_on_broken_refs(self, adr_env):
        """--check-terms should exit 1 when broken refs exist."""
        from tools.scripts.check_adr import main

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        create_index(
            adr_env.index_path,
            [(26001, "Test ADR", "/architecture/adr/adr_26001_test_adr.md")],
        )

        docs_dir = adr_env.root / "docs"
        docs_dir.mkdir(exist_ok=True)
        create_md_file_with_term_refs(docs_dir, "guide", "See {term}`ADR 26001`.")

        exit_code = main(["--check-terms"])

        assert exit_code == 1

    def test_check_terms_passes_with_valid_refs(self, adr_env):
        """--check-terms should exit 0 when all refs are valid."""
        from tools.scripts.check_adr import main

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        create_index(
            adr_env.index_path,
            [(26001, "Test ADR", "/architecture/adr/adr_26001_test_adr.md")],
        )

        docs_dir = adr_env.root / "docs"
        docs_dir.mkdir(exist_ok=True)
        create_md_file_with_term_refs(docs_dir, "guide", "See {term}`ADR-26001`.")

        exit_code = main(["--check-terms"])

        assert exit_code == 0

    def test_fix_terms_fixes_and_succeeds(self, adr_env):
        """--fix-terms should fix refs and exit 0."""
        from tools.scripts.check_adr import main

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        create_index(
            adr_env.index_path,
            [(26001, "Test ADR", "/architecture/adr/adr_26001_test_adr.md")],
        )

        docs_dir = adr_env.root / "docs"
        docs_dir.mkdir(exist_ok=True)
        doc_file = create_md_file_with_term_refs(
            docs_dir, "guide", "See {term}`ADR 26001`."
        )

        exit_code = main(["--fix-terms"])

        assert exit_code == 0
        # Verify the actual fix happened
        new_content = doc_file.read_text(encoding="utf-8")
        assert "{term}`ADR-26001`" in new_content

    def test_check_terms_scans_md_files_recursively(self, adr_env, monkeypatch):
        """get_all_md_files should find .md files in subdirectories."""
        from tools.scripts.check_adr import get_all_md_files

        (adr_env.root / "README.md").write_text("# README", encoding="utf-8")
        (adr_env.root / "docs").mkdir(exist_ok=True)
        (adr_env.root / "docs" / "guide.md").write_text("# Guide", encoding="utf-8")

        monkeypatch.chdir(adr_env.root)

        files = get_all_md_files(adr_env.root)

        filenames = {f.name for f in files}
        assert "README.md" in filenames
        assert "guide.md" in filenames


class TestBrokenTermReferenceDataClass:
    """Tests for BrokenTermReference dataclass."""

    def test_stores_required_fields(self):
        """Should store file path, line number, and ADR number."""
        from tools.scripts.check_adr import BrokenTermReference

        ref = BrokenTermReference(
            file_path=Path("/test/file.md"),
            line_number=42,
            adr_number=26001,
            original="{term}`ADR 26001`",
        )

        assert ref.file_path == Path("/test/file.md")
        assert ref.line_number == 42
        assert ref.adr_number == 26001

    def test_provides_suggested_fix(self):
        """Should provide the corrected hyphen format."""
        from tools.scripts.check_adr import BrokenTermReference

        ref = BrokenTermReference(
            file_path=Path("/test/file.md"),
            line_number=42,
            adr_number=26001,
            original="{term}`ADR 26001`",
        )

        # The fix should use hyphen instead of space
        assert "-" in ref.suggested_fix
        assert "26001" in ref.suggested_fix


# ======================
# Unit Tests: Promotion Gate Validation (ADR-26025)
# ======================
#
# ADR-26025 formalizes that `status: proposed` ADRs serve as RFCs.
# The "promotion gate" prevents an ADR from being accepted without
# sufficient analysis. validate_promotion_gate() returns (errors, warnings):
#
#   - accepted ADRs: errors if ## Alternatives < 2 entries or ## Participants empty
#   - proposed ADRs: warnings (not errors) if ## Alternatives is empty
#
# Tests assert on error_type strings (structured contract) and exit codes,
# never on human-readable messages — messages may change without breaking contracts.
#
# Entry detection patterns (all found in real ADRs in this repo):
#   "- **Name**: ..."   → dash bullet + bold  (ADR-26016)
#   "* **Name**: ..."   → asterisk bullet + bold  (ADR-26001, 26002, 26023)
#   "### Name"          → subheading per alternative  (ADR-26013, 26014)
#   "1. **Name**: ..."  → numbered list


def _make_adr_content(
    number: int,
    status: str,
    alternatives_body: str = "",
    participants_body: str = "",
    references_body: str = "",
) -> str:
    """Build minimal ADR content string for promotion gate tests.

    Args:
        number: ADR number.
        status: ADR status (proposed, accepted, etc.).
        alternatives_body: Raw text under ## Alternatives.
        participants_body: Raw text under ## Participants.
        references_body: Raw text under ## References.

    Returns:
        Full ADR content string with all required sections.
    """
    return (
        f"---\nid: ADR-{number}\ntitle: Test\ndate: 2026-01-01\n"
        f"status: {status}\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
        f"# ADR-{number}: Test\n\n"
        f"## Title\n\nTest\n\n"
        f"## Date\n\n2026-01-01\n\n"
        f"## Status\n\n{status}\n\n"
        f"## Context\n\nSome context.\n\n"
        f"## Decision\n\nSome decision.\n\n"
        f"## Consequences\n\nSome consequences.\n\n"
        f"## Alternatives\n\n{alternatives_body}\n\n"
        f"## References\n\n{references_body}\n\n"
        f"## Participants\n\n{participants_body}\n"
    )


class TestPromotionGateAlternatives:
    """Contract: accepted ADRs MUST have ≥2 entries in ## Alternatives.

    An 'entry' is a line starting with '- **' or a numbered item (e.g. '1.').
    Proposed ADRs get a warning (not error) if empty.

    Boundary: 0 → error, 1 → error, 2 → pass. Status determines severity.
    """

    # --- accepted: hard errors ---

    def test_accepted_with_zero_alternatives_fails(self, adr_env):
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        content = _make_adr_content(26099, "accepted", alternatives_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert len(errors) > 0
        assert any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_one_alternative_fails(self, adr_env):
        # 1 < 2, still below the gate threshold
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = "- **Option A**: Rejected. Some reason."
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert len(errors) > 0
        assert any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_two_alternatives_passes(self, adr_env):
        # Exactly at the boundary — should pass
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = (
            "- **Option A**: Rejected. Some reason.\n"
            "- **Option B**: Rejected. Another reason."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_numbered_alternatives_passes(self, adr_env):
        # Numbered list format ("1. **...") is a valid alternative entry
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = (
            "1. **Option A**: Rejected.\n"
            "2. **Option B**: Rejected."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_asterisk_bullet_alternatives_passes(self, adr_env):
        # Asterisk bullet format ("* **...") used by ADR-26001, 26002, 26023
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = (
            "* **Shell/Bash:** Rejected due to poor testability.\n"
            "* **Functional Python:** Rejected because shared state."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    def test_accepted_with_subheading_alternatives_passes(self, adr_env):
        # Subheading format ("### Name (Rejected)") used by ADR-26013, 26014
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = (
            "### Persistent Artifact Storage (Rejected)\n\n"
            "Some analysis paragraph.\n\n"
            "### YAML as Source of Truth (Rejected)\n\n"
            "Another analysis paragraph."
        )
        content = _make_adr_content(26099, "accepted", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "insufficient_alternatives" for e in errors)

    # --- proposed: soft warnings ---

    def test_proposed_with_empty_alternatives_warns(self, adr_env):
        # Proposed ADRs are still in RFC phase — no hard failure, just a nudge
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        content = _make_adr_content(26099, "proposed", alternatives_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="proposed", content=content)
        errors, warnings = validate_promotion_gate(adr)
        assert len(errors) == 0
        assert len(warnings) > 0

    def test_proposed_with_alternatives_no_warning(self, adr_env):
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = "- **Option A**: Rejected.\n- **Option B**: Rejected."
        content = _make_adr_content(26099, "proposed", alternatives_body=alt)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="proposed", content=content)
        errors, warnings = validate_promotion_gate(adr)
        assert len(errors) == 0
        assert len(warnings) == 0


class TestPromotionGateParticipants:
    """Contract: accepted ADRs MUST have non-empty ## Participants.

    'Non-empty' means the section body has any non-whitespace text.
    Proposed ADRs are exempt — the Participants section may be empty
    while the ADR is still in RFC phase.
    """

    def test_accepted_with_empty_participants_fails(self, adr_env):
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        # Alternatives pass the gate so the only error is empty participants
        alt = "- **A**: Rejected.\n- **B**: Rejected."
        content = _make_adr_content(26099, "accepted", alternatives_body=alt, participants_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert any(e.error_type == "empty_participants" for e in errors)

    def test_accepted_with_participants_passes(self, adr_env):
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        alt = "- **A**: Rejected.\n- **B**: Rejected."
        participants = "1. Test Author\n2. Test Reviewer"
        content = _make_adr_content(26099, "accepted", alternatives_body=alt,
                                     participants_body=participants)
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="accepted", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "empty_participants" for e in errors)

    def test_proposed_with_empty_participants_no_error(self, adr_env):
        # Proposed ADRs are exempt from the participants requirement
        from tools.scripts.check_adr import AdrFile, validate_promotion_gate

        content = _make_adr_content(26099, "proposed", participants_body="")
        adr = AdrFile(path=adr_env.adr_dir / "test.md", number=26099, title="Test",
                      status="proposed", content=content)
        errors, _warnings = validate_promotion_gate(adr)
        assert not any(e.error_type == "empty_participants" for e in errors)


class TestPromotionGateCLIIntegration:
    """Contract: promotion gate feeds into main() exit code.

    - Gate errors (accepted ADR failing criteria) → exit 1
    - Gate warnings (proposed ADR missing alternatives) → exit 0
    - Gate pass (all criteria met) → exit 0

    These tests use create_adr_file_full + create_index to set up
    a synced environment, so only the promotion gate determines the exit code.
    Tests assert solely on exit codes — never on output text.
    """

    def test_accepted_adr_failing_gate_causes_exit_1(self, adr_env):
        """Synced but under-analyzed accepted ADR → exit 1."""
        from tools.scripts.check_adr import main

        # Write ADR content directly — no dependency on helper placeholder strings.
        # This accepted ADR has no "- **" entries and empty participants.
        content = _make_adr_content(
            26090, "accepted",
            alternatives_body="No real alternatives analyzed.",
            participants_body="",
        )
        filepath = adr_env.adr_dir / "adr_26090_gate_fail_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26090, "Gate Fail Test", "/architecture/adr/adr_26090_gate_fail_test.md")],
        )

        assert main([]) == 1

    def test_proposed_adr_with_empty_alternatives_still_exits_0(self, adr_env):
        """Synced proposed ADR with no alternatives → warnings only, exit 0."""
        from tools.scripts.check_adr import main

        # Write directly — proposed with empty alternatives should only warn.
        content = _make_adr_content(
            26091, "proposed",
            alternatives_body="",
            participants_body="",
        )
        filepath = adr_env.adr_dir / "adr_26091_proposed_warning_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26091, "Proposed Warning Test", "/architecture/adr/adr_26091_proposed_warning_test.md")],
        )

        assert main([]) == 0


# ======================
# Duplicate Section Detection Tests
# ======================


class TestDuplicateSections:
    """Contract: validate_sections() must detect duplicate ## headers.

    A section name appearing more than once produces a 'duplicate_section' error.
    The set-based approach silently collapsed duplicates — this catches them.
    """

    def test_duplicate_section_produces_error(self, adr_env):
        """ADR with two ## Participants headers should produce duplicate_section error."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: proposed\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\nSome alternatives.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        adr = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26099,
            title="Test",
            content=content,
        )
        errors = validate_sections(adr)
        assert any(e.error_type == "duplicate_section" for e in errors)

    def test_no_duplicates_passes(self, adr_env):
        """ADR with unique sections should not produce duplicate_section error."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = _make_adr_content(26099, "proposed", participants_body="1. Author")
        adr = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26099,
            title="Test",
            content=content,
        )
        errors = validate_sections(adr)
        assert not any(e.error_type == "duplicate_section" for e in errors)

    def test_three_duplicates_produce_single_error(self, adr_env):
        """Three ## Participants headers should produce exactly one duplicate_section error."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: proposed\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\nSome alternatives.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Author\n"
            "## Participants\n\n2. Another Author\n"
        )
        adr = AdrFile(
            path=adr_env.adr_dir / "test.md",
            number=26099,
            title="Test",
            content=content,
        )
        errors = validate_sections(adr)
        dup_errors = [e for e in errors if e.error_type == "duplicate_section"]
        # One error per duplicated section name, not per occurrence
        assert len(dup_errors) == 1


class TestFixDuplicateSections:
    """Contract: fix_duplicate_sections() merges duplicate ## headers.

    Keeps the first header, concatenates all bodies (preserving order).
    Returns True if any file was modified.
    """

    def test_merges_two_duplicate_sections(self, adr_env):
        """Two ## Participants should merge into one with combined body."""
        from tools.scripts.check_adr import AdrFile, fix_duplicate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: accepted\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\n"
            "- **Option A**: Rejected.\n"
            "- **Option B**: Rejected.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="accepted",
            content=content,
        )

        with patch("builtins.input", return_value="y"):
            modified = fix_duplicate_sections([adr])
        assert modified is True

        result = filepath.read_text(encoding="utf-8")
        # Should have exactly one ## Participants
        assert result.count("## Participants") == 1
        # The merged body should contain the actual content
        assert "1. Test Author" in result

    def test_no_duplicates_returns_false(self, adr_env):
        """When no duplicates exist, should return False (no changes)."""
        from tools.scripts.check_adr import AdrFile, fix_duplicate_sections

        content = _make_adr_content(26099, "proposed", participants_body="1. Author")
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="proposed",
            content=content,
        )

        modified = fix_duplicate_sections([adr])
        assert modified is False

    def test_merges_preserves_body_content(self, adr_env):
        """Merged section should contain content from all duplicate bodies."""
        from tools.scripts.check_adr import AdrFile, fix_duplicate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: accepted\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\n"
            "- **Option A**: Rejected.\n"
            "- **Option B**: Rejected.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\nFirst body content.\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="accepted",
            content=content,
        )

        with patch("builtins.input", return_value="y"):
            fix_duplicate_sections([adr])

        result = filepath.read_text(encoding="utf-8")
        assert result.count("## Participants") == 1
        assert "First body content." in result
        assert "1. Test Author" in result

    def test_rejected_merge_returns_false(self, adr_env):
        """User rejecting merge should return False and not modify file."""
        from tools.scripts.check_adr import AdrFile, fix_duplicate_sections

        content = (
            "---\nid: 26099\ntitle: Test\ndate: 2026-01-01\n"
            "status: accepted\ntags: [architecture]\nsuperseded_by: null\n---\n\n"
            "# ADR-26099: Test\n\n"
            "## Context\n\nSome context.\n\n"
            "## Decision\n\nSome decision.\n\n"
            "## Consequences\n\nSome consequences.\n\n"
            "## Alternatives\n\n"
            "- **Option A**: Rejected.\n"
            "- **Option B**: Rejected.\n\n"
            "## References\n\nSome references.\n\n"
            "## Participants\n\n"
            "## Participants\n\n1. Test Author\n"
        )
        filepath = adr_env.adr_dir / "adr_26099_test.md"
        filepath.write_text(content, encoding="utf-8")

        adr = AdrFile(
            path=filepath,
            number=26099,
            title="Test",
            status="accepted",
            content=content,
        )

        with patch("builtins.input", return_value="n"):
            modified = fix_duplicate_sections([adr])
        assert modified is False

        # File should be unchanged
        result = filepath.read_text(encoding="utf-8")
        assert result.count("## Participants") == 2


class TestPromotionGateInFixMode:
    """Contract: --fix mode must run promotion gate validation.

    Previously, --fix exited at line 1313 before reaching the promotion
    gate block (line 1357). This caused pre-commit (--fix) to pass while
    CI (--verbose) failed on the same ADR.
    """

    def test_fix_mode_returns_exit_1_for_empty_participants(self, adr_env):
        """--fix mode should fail when accepted ADR has empty ## Participants."""
        from tools.scripts.check_adr import main

        content = _make_adr_content(
            26090, "accepted",
            alternatives_body=(
                "- **Option A**: Rejected.\n"
                "- **Option B**: Rejected."
            ),
            participants_body="",
        )
        filepath = adr_env.adr_dir / "adr_26090_gate_fix_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26090, "Gate Fix Test", "/architecture/adr/adr_26090_gate_fix_test.md")],
        )

        assert main(["--fix"]) == 1

    def test_fix_mode_returns_exit_0_when_gate_passes(self, adr_env):
        """--fix mode should succeed when accepted ADR passes promotion gate."""
        from tools.scripts.check_adr import main

        content = _make_adr_content(
            26090, "accepted",
            alternatives_body=(
                "- **Option A**: Rejected.\n"
                "- **Option B**: Rejected."
            ),
            participants_body="1. Test Author",
        )
        filepath = adr_env.adr_dir / "adr_26090_gate_pass_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26090, "Gate Pass Test", "/architecture/adr/adr_26090_gate_pass_test.md")],
        )

        assert main(["--fix"]) == 0

    def test_accepted_adr_passing_gate_exits_0(self, adr_env):
        """Synced accepted ADR with ≥2 alternatives + participants → exit 0."""
        from tools.scripts.check_adr import main

        # Write directly — this accepted ADR satisfies all gate criteria.
        content = _make_adr_content(
            26092, "accepted",
            alternatives_body=(
                "- **Option A**: Rejected. Reason.\n"
                "- **Option B**: Rejected. Reason."
            ),
            participants_body="1. Author A\n2. Author B",
        )
        filepath = adr_env.adr_dir / "adr_26092_gate_pass_test.md"
        filepath.write_text(content, encoding="utf-8")

        create_index(
            adr_env.index_path,
            [(26092, "Gate Pass Test", "/architecture/adr/adr_26092_gate_pass_test.md")],
        )

        assert main([]) == 0


# ======================
# Section Whitelist Validation
# ======================


class TestSectionWhitelist:
    """Contract: validate_sections() must reject sections not in allowed_sections.

    Allowed sections are defined in adr_config.yaml as the Single Source of Truth.
    Any ## header not in that list should produce an 'unexpected_section' error.
    """

    def test_unexpected_section_produces_error(self, adr_env):
        """ADR with a ## section not in allowed_sections should fail."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = """---
id: 26050
title: Test Unexpected Section
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26050: Test Unexpected Section

## Date
2024-01-15

## Status
proposed

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## CustomBogusSection
This should be flagged.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26050_test.md",
            number=26050,
            title="Test Unexpected Section",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        unexpected_errors = [e for e in errors if e.error_type == "unexpected_section"]
        assert len(unexpected_errors) == 1
        assert 26050 == unexpected_errors[0].number

    def test_all_allowed_sections_pass(self, adr_env):
        """ADR with only allowed sections should produce no unexpected_section errors."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = """---
id: 26051
title: All Allowed Sections
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26051: All Allowed Sections

## Title
All Allowed Sections

## Date
2024-01-15

## Status
proposed

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26051_test.md",
            number=26051,
            title="All Allowed Sections",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        unexpected_errors = [e for e in errors if e.error_type == "unexpected_section"]
        assert len(unexpected_errors) == 0


class TestConditionalSections:
    """Contract: conditional sections are only allowed for specific statuses.

    ## Rejection Rationale is only valid in ADRs with status: rejected.
    """

    def test_rejection_rationale_in_proposed_adr_produces_error(self, adr_env):
        """## Rejection Rationale in a proposed ADR should fail."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = """---
id: 26052
title: Wrong Rationale
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26052: Wrong Rationale

## Date
2024-01-15

## Status
proposed

## Rejection Rationale
Should not be here in a proposed ADR.

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26052_test.md",
            number=26052,
            title="Wrong Rationale",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        conditional_errors = [e for e in errors if e.error_type == "conditional_section_violation"]
        assert len(conditional_errors) == 1
        assert 26052 == conditional_errors[0].number

    def test_rejection_rationale_in_rejected_adr_passes(self, adr_env):
        """## Rejection Rationale in a rejected ADR should pass."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = """---
id: 26053
title: Proper Rejection
date: 2024-01-15
status: rejected
tags: [architecture]
---

# ADR-26053: Proper Rejection

## Date
2024-01-15

## Status
rejected

## Rejection Rationale
Valid rationale for rejection.

## Context
Some context.

## Decision
Some decision.

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
"""
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26053_test.md",
            number=26053,
            title="Proper Rejection",
            status="rejected",
            content=content,
        )

        errors = validate_sections(adr)
        conditional_errors = [e for e in errors if e.error_type == "conditional_section_violation"]
        assert len(conditional_errors) == 0


class TestCodeFencedSectionsIgnored:
    """Contract: ## headers inside fenced code blocks must not be treated as sections.

    The regex ^## with re.MULTILINE matches inside code fences. The parser
    must strip code blocks before extracting section headers.
    """

    def test_section_inside_code_block_is_ignored(self, adr_env):
        """## headers inside ```markdown fences should not be counted as sections."""
        from tools.scripts.check_adr import AdrFile, validate_sections

        content = '''---
id: 26054
title: Code Block Sections
date: 2024-01-15
status: proposed
tags: [architecture]
---

# ADR-26054: Code Block Sections

## Date
2024-01-15

## Status
proposed

## Context
Some context.

## Decision

Example of what an ARCHITECTURE.md looks like:

```markdown
## Governing ADRs (in hub)
- ADR-001: Example

## Implementation ADRs (in this repo)
- ADR-002: Example
```

## Consequences
Some consequences.

## Alternatives
Some alternatives.

## References
Some references.

## Participants
1. Author
'''
        adr = AdrFile(
            path=adr_env.adr_dir / "adr_26054_test.md",
            number=26054,
            title="Code Block Sections",
            status="proposed",
            content=content,
        )

        errors = validate_sections(adr)
        unexpected_errors = [e for e in errors if e.error_type == "unexpected_section"]
        assert len(unexpected_errors) == 0
