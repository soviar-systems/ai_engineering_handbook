"""Tests for jupytext_sync.py script."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add tools/scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from tools.scripts.jupytext_sync import main


class TestJupytextSyncNoFiles:
    """Test behavior when no files are provided."""

    def test_no_files_returns_zero(self, monkeypatch):
        """No files provided should return 0."""
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py"])
        assert main() == 0

    def test_empty_files_list_returns_zero(self, monkeypatch):
        """Empty files list should return 0."""
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py"])
        assert main() == 0


class TestJupytextSyncFileFiltering:
    """Test file filtering logic."""

    def test_non_md_ipynb_files_filtered_out(self, monkeypatch, tmp_path):
        """Non-.md/.ipynb files should be silently filtered out."""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()
        py_file = tmp_path / "test.py"
        py_file.touch()

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(txt_file), str(py_file)])
        # Should return 0 because all files are filtered out
        assert main() == 0

    def test_excluded_dirs_skipped(self, monkeypatch, tmp_path):
        """Files in excluded directories should be skipped."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        venv_file = venv_dir / "test.md"
        venv_file.touch()

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(venv_file)])
        # Should return 0 because file is in excluded dir
        assert main() == 0

    def test_multiple_excluded_dirs(self, monkeypatch, tmp_path):
        """Multiple excluded directories should all be skipped."""
        excluded_dirs = [".git", "__pycache__", "node_modules", "build"]
        for dir_name in excluded_dirs:
            exc_dir = tmp_path / dir_name
            exc_dir.mkdir()
            (exc_dir / "test.md").touch()

        files = [str(tmp_path / d / "test.md") for d in excluded_dirs]
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py"] + files)
        assert main() == 0


class TestJupytextSyncNonExistentFile:
    """Test handling of non-existent files."""

    def test_nonexistent_file_warning(self, monkeypatch, capsys, tmp_path):
        """Non-existent file should print warning and continue."""
        nonexistent = tmp_path / "nonexistent.md"

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(nonexistent)])
        result = main()

        captured = capsys.readouterr()
        assert "Warning:" in captured.out
        assert "does not exist" in captured.out
        assert result == 0


class TestJupytextSyncMode:
    """Test sync mode execution."""

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    def test_sync_mode_calls_jupytext_sync(self, mock_run, monkeypatch, tmp_path):
        """Sync mode should run jupytext --sync."""
        md_file = tmp_path / "test.md"
        md_file.touch()

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(md_file)])

        result = main()

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "jupytext" in call_args
        assert "--sync" in call_args
        assert str(md_file) in call_args

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    def test_sync_mode_with_ipynb(self, mock_run, monkeypatch, tmp_path):
        """Sync mode should work with .ipynb files."""
        ipynb_file = tmp_path / "test.ipynb"
        ipynb_file.touch()

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(ipynb_file)])

        result = main()

        assert result == 0
        call_args = mock_run.call_args[0][0]
        assert "--sync" in call_args


class TestJupytextSyncTestMode:
    """Test --test mode execution."""

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    def test_test_mode_calls_jupytext_to_ipynb_test(self, mock_run, monkeypatch, tmp_path):
        """Test mode should run jupytext --to ipynb --test."""
        md_file = tmp_path / "test.md"
        md_file.touch()

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", "--test", str(md_file)])

        result = main()

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "jupytext" in call_args
        assert "--to" in call_args
        assert "ipynb" in call_args
        assert "--test" in call_args


class TestJupytextSyncSubprocessFailure:
    """Test subprocess failure handling."""

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    def test_subprocess_failure_returns_one(self, mock_run, monkeypatch, tmp_path, capsys):
        """Subprocess failure should return 1 and print error."""
        md_file = tmp_path / "test.md"
        md_file.touch()

        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Jupytext error: file not synced"
        )
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(md_file)])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAIL:" in captured.out
        assert "Jupytext error" in captured.out

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    def test_multiple_files_one_failure(self, mock_run, monkeypatch, tmp_path, capsys):
        """If one file fails, should return 1 but continue processing."""
        file1 = tmp_path / "file1.md"
        file1.touch()
        file2 = tmp_path / "file2.md"
        file2.touch()

        # First call fails, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="Error on file1"),
            MagicMock(returncode=0, stdout="file2 synced", stderr=""),
        ]
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(file1), str(file2)])

        result = main()

        assert result == 1
        assert mock_run.call_count == 2

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    def test_success_prints_stdout(self, mock_run, monkeypatch, tmp_path, capsys):
        """Successful sync should print stdout."""
        md_file = tmp_path / "test.md"
        md_file.touch()

        mock_run.return_value = MagicMock(
            returncode=0, stdout="[jupytext] Syncing test.md", stderr=""
        )
        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", str(md_file)])

        main()

        captured = capsys.readouterr()
        assert "[jupytext] Syncing test.md" in captured.out


class TestIsExcluded:
    """Test the is_excluded function from paths.py."""

    def test_excluded_dir_in_path(self):
        """Path containing excluded dir should return True."""
        from tools.scripts.paths import is_excluded

        assert is_excluded(".venv/test.md") is True
        assert is_excluded("project/.git/config") is True
        assert is_excluded("node_modules/package/file.md") is True
        assert is_excluded("some/path/__pycache__/module.py") is True
        assert is_excluded("misc/in_progress/draft.md") is True

    def test_clean_path_not_excluded(self):
        """Clean path should return False."""
        from tools.scripts.paths import is_excluded

        assert is_excluded("src/test.md") is False
        assert is_excluded("docs/guide.ipynb") is False
        assert is_excluded("notebooks/analysis.md") is False
