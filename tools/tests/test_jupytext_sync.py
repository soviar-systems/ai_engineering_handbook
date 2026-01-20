"""Tests for jupytext_sync.py script."""
import sys
import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add tools/scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from tools.scripts.jupytext_sync import main, find_all_paired_notebooks


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

class TestFindAllPairedNotebooks:
    """Test the find_all_paired_notebooks function."""

    def test_finds_paired_notebooks(self, tmp_path):
        """Should find .md files that have paired .ipynb files."""
        # Create paired notebooks
        (tmp_path / "notebook1.md").touch()
        (tmp_path / "notebook1.ipynb").touch()
        (tmp_path / "notebook2.md").touch()
        (tmp_path / "notebook2.ipynb").touch()

        result = find_all_paired_notebooks(tmp_path)

        assert len(result) == 2
        assert any("notebook1.md" in f for f in result)
        assert any("notebook2.md" in f for f in result)

    def test_ignores_unpaired_md_files(self, tmp_path):
        """Should ignore .md files without paired .ipynb files."""
        (tmp_path / "paired.md").touch()
        (tmp_path / "paired.ipynb").touch()
        (tmp_path / "unpaired.md").touch()  # No matching .ipynb

        result = find_all_paired_notebooks(tmp_path)

        assert len(result) == 1
        assert any("paired.md" in f for f in result)

    def test_excludes_venv_directory(self, tmp_path):
        """Should skip files in .venv directory."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "notebook.md").touch()
        (venv_dir / "notebook.ipynb").touch()

        result = find_all_paired_notebooks(tmp_path)

        assert len(result) == 0

    def test_excludes_multiple_directories(self, tmp_path):
        """Should skip files in all excluded directories."""
        for dir_name in [".git", "node_modules", "__pycache__", "_build"]:
            exc_dir = tmp_path / dir_name
            exc_dir.mkdir()
            (exc_dir / "notebook.md").touch()
            (exc_dir / "notebook.ipynb").touch()

        result = find_all_paired_notebooks(tmp_path)

        assert len(result) == 0

    def test_finds_nested_notebooks(self, tmp_path):
        """Should find notebooks in subdirectories."""
        subdir = tmp_path / "docs" / "tutorials"
        subdir.mkdir(parents=True)
        (subdir / "intro.md").touch()
        (subdir / "intro.ipynb").touch()

        result = find_all_paired_notebooks(tmp_path)

        assert len(result) == 1
        assert any("intro.md" in f for f in result)

    def test_returns_sorted_list(self, tmp_path):
        """Should return sorted list of paths."""
        (tmp_path / "z_last.md").touch()
        (tmp_path / "z_last.ipynb").touch()
        (tmp_path / "a_first.md").touch()
        (tmp_path / "a_first.ipynb").touch()

        result = find_all_paired_notebooks(tmp_path)

        assert len(result) == 2
        assert result[0] < result[1]  # Sorted order

    def test_empty_directory(self, tmp_path):
        """Should return empty list for directory with no paired notebooks."""
        result = find_all_paired_notebooks(tmp_path)

        assert result == []


class TestJupytextSyncAllFlag:
    """Test the --all flag behavior."""

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    @patch("tools.scripts.jupytext_sync.find_all_paired_notebooks")
    def test_all_flag_finds_and_processes_notebooks(
        self, mock_find, mock_run, monkeypatch, tmp_path
    ):
        """--all flag should find all paired notebooks and process them."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        mock_find.return_value = [str(md_file)]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", "--all"])
        result = main()

        assert result == 0
        mock_find.assert_called_once()
        mock_run.assert_called_once()

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    @patch("tools.scripts.jupytext_sync.find_all_paired_notebooks")
    def test_all_flag_with_test_mode(self, mock_find, mock_run, monkeypatch, tmp_path):
        """--all --test should run test mode on all notebooks."""
        md_file = tmp_path / "test.md"
        md_file.touch()
        mock_find.return_value = [str(md_file)]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", "--all", "--test"])
        result = main()

        assert result == 0
        call_args = mock_run.call_args[0][0]
        assert "--to" in call_args
        assert "ipynb" in call_args
        assert "--test" in call_args

    @patch("tools.scripts.jupytext_sync.find_all_paired_notebooks")
    def test_all_flag_no_notebooks_found(self, mock_find, monkeypatch, capsys):
        """--all flag with no notebooks should print message and return 0."""
        mock_find.return_value = []

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", "--all"])
        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "No paired notebooks found" in captured.out

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    @patch("tools.scripts.jupytext_sync.find_all_paired_notebooks")
    def test_all_flag_processes_multiple_notebooks(
        self, mock_find, mock_run, monkeypatch, tmp_path
    ):
        """--all flag should process all found notebooks."""
        file1 = tmp_path / "file1.md"
        file1.touch()
        file2 = tmp_path / "file2.md"
        file2.touch()
        mock_find.return_value = [str(file1), str(file2)]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", "--all"])
        result = main()

        assert result == 0
        assert mock_run.call_count == 2

    @patch("tools.scripts.jupytext_sync.subprocess.run")
    @patch("tools.scripts.jupytext_sync.find_all_paired_notebooks")
    def test_all_flag_one_failure_returns_one(
        self, mock_find, mock_run, monkeypatch, tmp_path
    ):
        """--all flag should return 1 if any notebook fails."""
        file1 = tmp_path / "file1.md"
        file1.touch()
        file2 = tmp_path / "file2.md"
        file2.touch()
        mock_find.return_value = [str(file1), str(file2)]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="Error"),
        ]

        monkeypatch.setattr("sys.argv", ["jupytext_sync.py", "--all"])
        result = main()

        assert result == 1


def test_main_entry_point():
    # Cover the __main__ block
    with patch("sys.argv", ["jupytext_sync.py", "--help"]), pytest.raises(SystemExit):
        runpy.run_path("tools/scripts/jupytext_sync.py", run_name="__main__")
