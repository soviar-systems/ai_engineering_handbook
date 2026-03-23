"""
Test suite for git.py — shared git utilities.

Scope: tests for detect_repo_root() and get_staged_files().
Does NOT test git itself — mocks subprocess calls.

Test classes and their contracts:
- TestDetectRepoRoot: returns resolved Path from git rev-parse, falls back to __file__
- TestGetStagedFiles: returns set of repo-relative paths from git diff --cached

Naming convention: one class per public function.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import tools.scripts.git as _module


class TestDetectRepoRoot:
    """Contract: detect_repo_root() returns repo root via git, or __file__ fallback."""

    @patch.object(_module.subprocess, "run")
    def test_returns_path_from_git(self, mock_run):
        """git rev-parse succeeds → return its output as resolved Path."""
        mock_run.return_value = MagicMock(stdout="/fake/repo\n")
        result = _module.detect_repo_root()
        assert result == Path("/fake/repo").resolve()
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_fallback_on_git_failure(self, mock_run):
        """git rev-parse fails → fallback to __file__-based path."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _module.detect_repo_root()
        expected = Path(_module.__file__).resolve().parent.parent.parent
        assert result == expected

    @patch.object(_module.subprocess, "run")
    def test_fallback_on_git_not_installed(self, mock_run):
        """git not found → fallback to __file__-based path."""
        mock_run.side_effect = FileNotFoundError()
        result = _module.detect_repo_root()
        expected = Path(_module.__file__).resolve().parent.parent.parent
        assert result == expected

    @patch.object(_module.subprocess, "run")
    def test_strips_whitespace(self, mock_run):
        """Output whitespace (newlines, spaces) is stripped."""
        mock_run.return_value = MagicMock(stdout="  /fake/repo  \n")
        result = _module.detect_repo_root()
        assert result == Path("/fake/repo").resolve()


class TestGetStagedFiles:
    """Contract: get_staged_files() returns set[str] of staged file paths."""

    @patch.object(_module.subprocess, "run")
    def test_returns_staged_files(self, mock_run):
        """Normal output → set of file paths."""
        mock_run.return_value = MagicMock(stdout="file1.py\nfile2.md\ndir/file3.txt\n")
        result = _module.get_staged_files()
        assert result == {"file1.py", "file2.md", "dir/file3.txt"}
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.object(_module.subprocess, "run")
    def test_empty_staging_area(self, mock_run):
        """No staged files → empty set."""
        mock_run.return_value = MagicMock(stdout="")
        result = _module.get_staged_files()
        assert result == set()

    @patch.object(_module.subprocess, "run")
    def test_ignores_blank_lines(self, mock_run):
        """Blank lines in output are filtered out."""
        mock_run.return_value = MagicMock(stdout="file1.py\n\n\nfile2.py\n")
        result = _module.get_staged_files()
        assert result == {"file1.py", "file2.py"}

    @patch.object(_module.subprocess, "run")
    def test_returns_empty_on_git_failure(self, mock_run):
        """git fails → empty set (graceful degradation)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _module.get_staged_files()
        assert result == set()
