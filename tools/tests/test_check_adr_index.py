"""
Test suite for check_adr_index.py - ADR Index synchronization validator.

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
    filename = f"adr_{number}_{slug}.md"
    filepath = directory / filename
    content = f"# ADR {number}: {title}\n\n## Status\n\nAccepted\n"
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
        lines.append(f"ADR {number}\n")
        lines.append(f": [{title}]({link})\n")
        lines.append("\n")
    lines.append(":::\n")
    path.write_text("".join(lines), encoding="utf-8")


def create_empty_index(path: Path) -> None:
    """Create an empty index file with glossary block but no entries."""
    content = "# ADR Index\n\n:::{glossary}\n:::\n"
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def adr_env(tmp_path, monkeypatch):
    """Create isolated ADR environment with configurable state."""
    adr_dir = tmp_path / "architecture" / "adr"
    adr_dir.mkdir(parents=True)
    index_path = tmp_path / "architecture" / "adr_index.md"

    # Create the template file (should be excluded)
    template = adr_dir / "adr_template.md"
    template.write_text("# ADR Template\n\nUse this as a template.\n", encoding="utf-8")

    # Monkeypatch to use test directories
    monkeypatch.setattr("tools.scripts.check_adr_index.ADR_DIR", adr_dir)
    monkeypatch.setattr("tools.scripts.check_adr_index.INDEX_PATH", index_path)

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
        from tools.scripts.check_adr_index import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        create_adr_file(adr_env.adr_dir, 26002, "Another ADR", "another_adr")

        files = get_adr_files()

        assert len(files) == 2
        numbers = {f.number for f in files}
        assert numbers == {26001, 26002}

    def test_excludes_template_file(self, adr_env):
        """Template file should not be included in results."""
        from tools.scripts.check_adr_index import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Test ADR", "test_adr")
        # Template already created by fixture

        files = get_adr_files()

        filenames = {f.path.name for f in files}
        assert "adr_template.md" not in filenames

    def test_returns_sorted_by_number(self, adr_env):
        """ADR files should be sorted by number ascending."""
        from tools.scripts.check_adr_index import get_adr_files

        # Create in reverse order
        create_adr_file(adr_env.adr_dir, 26003, "Third", "third")
        create_adr_file(adr_env.adr_dir, 26001, "First", "first")
        create_adr_file(adr_env.adr_dir, 26002, "Second", "second")

        files = get_adr_files()

        numbers = [f.number for f in files]
        assert numbers == [26001, 26002, 26003]

    def test_empty_directory_returns_empty_list(self, adr_env):
        """Empty ADR directory should return empty list."""
        from tools.scripts.check_adr_index import get_adr_files

        # Only template exists (created by fixture)
        files = get_adr_files()

        assert files == []

    def test_parses_title_from_header(self, adr_env):
        """Should extract title from ADR header line."""
        from tools.scripts.check_adr_index import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Use of Python for Scripts", "python_scripts")

        files = get_adr_files()

        assert len(files) == 1
        assert files[0].title == "Use of Python for Scripts"

    def test_handles_file_without_valid_header(self, adr_env):
        """File without valid ADR header should be skipped with warning."""
        from tools.scripts.check_adr_index import get_adr_files

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
        from tools.scripts.check_adr_index import get_adr_files

        nonexistent = tmp_path / "nonexistent" / "adr"
        monkeypatch.setattr("tools.scripts.check_adr_index.ADR_DIR", nonexistent)

        files = get_adr_files()

        assert files == []


# ======================
# Unit Tests: Index Parsing
# ======================


class TestParseIndex:
    """Tests for index file parsing functionality."""

    def test_parses_glossary_entries(self, adr_env):
        """Should parse entries from glossary block."""
        from tools.scripts.check_adr_index import parse_index

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
        from tools.scripts.check_adr_index import parse_index

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
        from tools.scripts.check_adr_index import parse_index

        create_empty_index(adr_env.index_path)

        entries = parse_index()

        assert entries == []

    def test_missing_index_file_raises_error(self, adr_env):
        """Missing index file should raise appropriate error."""
        from tools.scripts.check_adr_index import parse_index

        # Don't create the index file

        with pytest.raises(FileNotFoundError):
            parse_index()

    def test_index_without_glossary_block(self, adr_env):
        """Index file without glossary block should return empty list."""
        from tools.scripts.check_adr_index import parse_index

        # Create index without glossary block
        adr_env.index_path.write_text("# ADR Index\n\nNo glossary here.\n", encoding="utf-8")

        entries = parse_index()

        assert entries == []

    def test_preserves_entry_order(self, adr_env):
        """Entries should be returned in the order they appear in the file."""
        from tools.scripts.check_adr_index import parse_index

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
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        assert errors == []

    def test_detects_missing_adr_in_index(self, synced_env):
        """New ADR file without index entry should be detected."""
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

        # Add new ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        assert len(errors) == 1
        assert errors[0].number == 26004
        assert errors[0].error_type == "missing_in_index"

    def test_detects_orphan_index_entry(self, synced_env):
        """Index entry pointing to non-existent file should be detected."""
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

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

        assert len(errors) == 1
        assert errors[0].number == 26004
        assert errors[0].error_type == "orphan_in_index"

    def test_detects_wrong_link_path(self, synced_env):
        """Index entry with incorrect link path should be detected."""
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

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

        assert len(errors) == 1
        assert errors[0].number == 26002
        assert errors[0].error_type == "wrong_link"

    def test_detects_out_of_order_entries(self, synced_env):
        """Entries not in numerical order should be detected."""
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

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

        assert len(errors) == 1
        assert errors[0].error_type == "wrong_order"

    def test_detects_duplicate_adr_numbers(self, adr_env):
        """Duplicate ADR numbers in files should be detected."""
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

        # Create two files with same number but different slugs
        create_adr_file(adr_env.adr_dir, 26001, "First Version", "first_version")
        # Manually create another file with same number
        dup_file = adr_env.adr_dir / "adr_26001_duplicate.md"
        dup_file.write_text("# ADR 26001: Duplicate\n\n## Status\n\nAccepted\n", encoding="utf-8")

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
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

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
        from tools.scripts.check_adr_index import fix_index, get_adr_files, parse_index

        # Add new ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        fix_index()

        # Re-parse to verify
        entries = parse_index()
        numbers = {e.number for e in entries}
        assert 26004 in numbers

    def test_maintains_numerical_order(self, adr_env):
        """Fix should ensure entries are in numerical order."""
        from tools.scripts.check_adr_index import fix_index, parse_index

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
        from tools.scripts.check_adr_index import fix_index, parse_index

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
        from tools.scripts.check_adr_index import fix_index, parse_index

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
        from tools.scripts.check_adr_index import fix_index, parse_index

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
        from tools.scripts.check_adr_index import fix_index, parse_index

        create_adr_file(adr_env.adr_dir, 26001, "First", "first")

        # Don't create index - let fix create it
        fix_index()

        assert adr_env.index_path.exists()
        entries = parse_index()
        assert len(entries) == 1


# ======================
# Integration Tests: CLI
# ======================


class TestCli:
    """Integration tests for command-line interface."""

    def test_exit_code_0_when_synced(self, synced_env):
        """Should exit with 0 when ADRs are in sync."""
        from tools.scripts.check_adr_index import main

        exit_code = main([])

        assert exit_code == 0

    def test_exit_code_1_when_out_of_sync(self, synced_env):
        """Should exit with 1 when ADRs are out of sync."""
        from tools.scripts.check_adr_index import main

        # Add ADR not in index
        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        exit_code = main([])

        assert exit_code == 1

    def test_verbose_flag_shows_output(self, synced_env, capsys):
        """Verbose flag should produce output even when in sync."""
        from tools.scripts.check_adr_index import main

        main(["--verbose"])

        captured = capsys.readouterr()
        assert captured.out  # Verbose mode should produce output

    def test_fix_flag_modifies_index(self, synced_env):
        """Fix flag should modify the index file."""
        from tools.scripts.check_adr_index import main, parse_index

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
        from tools.scripts.check_adr_index import main

        create_adr_file(synced_env.adr_dir, 26004, "New Feature", "new_feature")

        main(["--fix"])

        captured = capsys.readouterr()
        assert captured.out  # Should inform user about changes

    def test_check_staged_with_no_staged_files(self, synced_env, capsys):
        """Check-staged with no staged ADR files should pass."""
        from tools.scripts.check_adr_index import main

        with patch("tools.scripts.check_adr_index.get_staged_adr_files", return_value=[]):
            exit_code = main(["--check-staged"])

        assert exit_code == 0

    def test_main_entry_point(self, synced_env, monkeypatch):
        """Cover the __main__ block."""
        monkeypatch.setattr("sys.argv", ["check_adr_index.py", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path("tools/scripts/check_adr_index.py", run_name="__main__")

        assert exc_info.value.code == 0

    def test_fix_verbose_mode(self, synced_env, capsys):
        """Fix with verbose flag should produce output."""
        from tools.scripts.check_adr_index import main

        exit_code = main(["--fix", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose fix should produce output

    def test_fix_no_changes_verbose(self, synced_env, capsys):
        """Fix with no changes needed should produce output in verbose mode."""
        from tools.scripts.check_adr_index import main

        exit_code = main(["--fix", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Should inform user even when no changes needed

    def test_fix_with_errors_remaining(self, adr_env, capsys):
        """Fix should fail if unfixable errors remain (e.g., duplicates)."""
        from tools.scripts.check_adr_index import main

        # Create duplicate ADR numbers (can't be auto-fixed)
        create_adr_file(adr_env.adr_dir, 26001, "First Version", "first_version")
        dup_file = adr_env.adr_dir / "adr_26001_duplicate.md"
        dup_file.write_text("# ADR 26001: Duplicate\n\n## Status\n\nAccepted\n", encoding="utf-8")

        exit_code = main(["--fix"])

        # Should fail because duplicates can't be auto-fixed
        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out  # Should explain why fix failed

    def test_check_staged_verbose_with_staged_files(self, synced_env, capsys):
        """Check-staged with verbose should produce output when files are staged."""
        from tools.scripts.check_adr_index import main

        with patch("tools.scripts.check_adr_index.get_staged_adr_files") as mock_staged:
            mock_staged.return_value = [Path("architecture/adr/adr_26001_first_feature.md")]
            exit_code = main(["--check-staged", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose should produce output

    def test_check_staged_verbose_no_staged_files(self, synced_env, capsys):
        """Check-staged with verbose and no staged files should produce output."""
        from tools.scripts.check_adr_index import main

        with patch("tools.scripts.check_adr_index.get_staged_adr_files") as mock_staged:
            mock_staged.return_value = []
            exit_code = main(["--check-staged", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out  # Verbose should produce output

    def test_missing_index_with_adr_files(self, adr_env, capsys):
        """Missing index with existing ADR files should fail."""
        from tools.scripts.check_adr_index import main

        create_adr_file(adr_env.adr_dir, 26001, "Test", "test")
        # Don't create index

        exit_code = main([])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out  # Should explain the error

    def test_missing_index_no_adr_files_verbose(self, adr_env, capsys):
        """Missing index with no ADR files should pass in verbose mode."""
        from tools.scripts.check_adr_index import main

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
        from tools.scripts.check_adr_index import get_staged_adr_files

        staged_output = "architecture/adr/adr_26001_test.md\narchitecture/adr/adr_26002_other.md\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = staged_output
            files = get_staged_adr_files()

        assert len(files) == 2
        assert files[0] == Path("architecture/adr/adr_26001_test.md")

    def test_filters_non_adr_files(self, adr_env):
        """Should only return ADR files, not other staged files."""
        from tools.scripts.check_adr_index import get_staged_adr_files

        staged_output = "README.md\narchitecture/adr/adr_26001_test.md\narchitecture/adr_index.md\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = staged_output
            files = get_staged_adr_files()

        assert len(files) == 1
        assert "adr_26001" in str(files[0])

    def test_handles_git_error(self, adr_env):
        """Should return empty list on git error."""
        from tools.scripts.check_adr_index import get_staged_adr_files

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            files = get_staged_adr_files()

        assert files == []

    def test_handles_git_not_found(self, adr_env):
        """Should return empty list if git is not installed."""
        from tools.scripts.check_adr_index import get_staged_adr_files

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            files = get_staged_adr_files()

        assert files == []


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_adr_number_in_header_differs_from_filename(self, adr_env):
        """Header number should be authoritative over filename number."""
        from tools.scripts.check_adr_index import get_adr_files

        # Create file with mismatched numbers
        filepath = adr_env.adr_dir / "adr_26001_test.md"
        filepath.write_text("# ADR 26002: Different Number\n\n## Status\n\nAccepted\n", encoding="utf-8")

        files = get_adr_files()

        # Should use header number (26002), not filename number (26001)
        assert len(files) == 1
        assert files[0].number == 26002

    def test_title_with_special_characters(self, adr_env):
        """Titles with special characters should be handled correctly."""
        from tools.scripts.check_adr_index import get_adr_files

        create_adr_file(adr_env.adr_dir, 26001, "Use: Python & OOP (v2.0)", "python_oop")

        files = get_adr_files()

        assert len(files) == 1
        assert "Python & OOP" in files[0].title

    def test_index_with_extra_whitespace(self, adr_env):
        """Index with extra whitespace should be parsed correctly."""
        from tools.scripts.check_adr_index import parse_index

        # Write index with extra blank lines
        content = """# ADR Index

:::{glossary}
ADR 26001
: [First ADR](/architecture/adr/adr_26001_first.md)


ADR 26002
: [Second ADR](/architecture/adr/adr_26002_second.md)
:::
"""
        adr_env.index_path.write_text(content, encoding="utf-8")

        entries = parse_index()

        assert len(entries) == 2

    def test_link_with_relative_path(self, adr_env):
        """Index entry with relative path should be detected as wrong."""
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

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
        from tools.scripts.check_adr_index import get_adr_files, parse_index, validate_sync

        create_empty_index(adr_env.index_path)

        adr_files = get_adr_files()
        index_entries = parse_index()

        errors = validate_sync(adr_files, index_entries)

        assert errors == []
