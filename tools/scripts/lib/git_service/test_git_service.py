import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Standardized import assuming execution from project root via 'uv run pytest'
from tools.scripts.lib.git_service.git_service import GitService

class TestGitService:
    # --- 1. Root Discovery Success ---
    @patch("subprocess.run", autospec=True)
    def test_find_git_root_success(self, mock_run):
        """Verify root discovery sets Path object correctly and resolves it."""
        mock_run.return_value = MagicMock(stdout="/mock/repo\n", returncode=0)
        gs = GitService()
        assert gs.root_dir == Path("/mock/repo").resolve()

    # --- 2. Root Discovery Failure ---
    @patch("subprocess.run", autospec=True)
    def test_find_git_root_failure(self, mock_run):
        """Ensure failure to find root (e.g. not in a repo) raises RuntimeError."""
        mock_run.side_effect = subprocess.CalledProcessError(128, "git rev-parse")
        with pytest.raises(RuntimeError, match="Not a git repository"):
            GitService()

    # --- 3. Manual Path Override ---
    @patch("subprocess.run", autospec=True)
    def test_init_with_provided_path(self, mock_run):
        """Verify that passing a path avoids subprocess discovery and resolves the path."""
        custom_path = Path("/custom/path")
        gs = GitService(root_dir=custom_path)
        assert gs.root_dir == custom_path.resolve()
        mock_run.assert_not_called()

    # --- 4. Index Check Logic ---
    @patch("subprocess.run", autospec=True)
    def test_is_in_index(self, mock_run):
        """Verify tracked file detection logic."""
        with patch.object(GitService, "__init__", return_value=None):
            gs = GitService()
            gs.root_dir = Path("/mock/repo")
            
            # Case: File is tracked
            mock_run.return_value = MagicMock(returncode=0)
            assert gs.is_in_index(Path("test.ipynb")) is True
            
            # Case: File is untracked
            mock_run.return_value = MagicMock(returncode=1)
            assert gs.is_in_index(Path("untracked.txt")) is False

    # --- 5. Staging Logic & Error Mapping (Hardened) ---
    @patch("subprocess.run", autospec=True)
    def test_has_unstaged_changes_logic(self, mock_run):
        """Verify explicit mapping of exit codes: 0=clean, 1=dirty, 128=error."""
        with patch.object(GitService, "__init__", return_value=None):
            gs = GitService()
            gs.root_dir = Path("/mock/repo")

            # Case: Clean (0)
            mock_run.return_value = MagicMock(returncode=0)
            assert gs.has_unstaged_changes(Path("f.py")) is False

            # Case: Dirty (1)
            mock_run.return_value = MagicMock(returncode=1)
            assert gs.has_unstaged_changes(Path("f.py")) is True

            # Case: Critical Git Error (128) - Grounded DevOps fix
            mock_run.return_value = MagicMock(returncode=128, stderr="fatal error")
            with pytest.raises(RuntimeError, match="Git diff failed"):
                gs.has_unstaged_changes(Path("f.py"))

    # --- 6. Command Execution & Capture (Resilience) ---
    @patch("subprocess.run", autospec=True)
    def test_run_cmd_capture_and_whitespace(self, mock_run):
        """Verify stdout/stderr capture and handling of paths with spaces."""
        mock_run.return_value = MagicMock(
            stdout="output", stderr="error_msg", returncode=0
        )
        with patch.object(GitService, "__init__", return_value=None):
            gs = GitService()
            gs.root_dir = Path("/mock/repo")
            path_with_spaces = Path("my docs/note book.ipynb")
            
            result = gs.run_cmd(["git", "status", str(path_with_spaces)])
            
            assert result.stdout == "output"
            assert result.stderr == "error_msg"
            # Verify the path with spaces was passed correctly to the shell
            assert str(path_with_spaces) in mock_run.call_args[0][0]

    # --- 7. Environmental Resilience (Missing Binary) ---
    @patch("subprocess.run")
    def test_run_cmd_env_missing(self, mock_run):
        """Verify resilience when 'git' or other binaries are missing from the system PATH."""
        mock_run.side_effect = FileNotFoundError
        with patch.object(GitService, "__init__", return_value=None):
            gs = GitService()
            gs.root_dir = Path("/mock/repo")
            
            result = gs.run_cmd(["git", "status"])
            # Should return a simulated CompletedProcess with 127 (command not found)
            assert result.returncode == 127
            assert "Executable not found" in result.stderr
