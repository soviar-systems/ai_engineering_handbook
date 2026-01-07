from unittest.mock import MagicMock, patch

import pytest

from tools.scripts.hooks.jupytext_sync.jupytext_sync import run


@pytest.fixture
def mock_subprocess():
    """Patch subprocess.run to isolate tests from actual CLI execution."""
    with patch("tools.scripts.hooks.jupytext_sync.jupytext_sync.subprocess.run") as m:
        m.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield m


@pytest.fixture
def fs_setup(tmp_path):
    """Creates physical dummy files for path resolution testing."""
    nb = tmp_path / "analysis.ipynb"
    nb.write_text("{}", encoding="utf-8")
    return tmp_path


class TestJupytextSyncProduction:
    def test_sync_no_changes_success(self, mock_subprocess, fs_setup):
        """TC-01: Returns True if sync runs and command succeeds."""
        assert run([str(fs_setup / "analysis.ipynb")]) is True

    def test_sync_modifies_files_returns_true(self, mock_subprocess, fs_setup):
        """TC-02: Verify test_only=True routes to --test flag."""
        assert run([str(fs_setup / "analysis.ipynb")], test_only=True) is True
        assert "--test" in mock_subprocess.call_args[0][0]

    def test_absolute_vs_relative_paths(self, mock_subprocess, fs_setup):
        """TC-03: Ensure hook handles path resolution."""
        abs_p = (fs_setup / "analysis.ipynb").resolve()
        assert run([str(abs_p)]) is True

    def test_exclusion_logic(self, mock_subprocess, tmp_path):
        """TC-04: Ensure non-notebook/markdown extensions are ignored."""
        txt = tmp_path / "data.txt"
        txt.write_text("ignore")
        assert run([str(txt)]) is True
        mock_subprocess.assert_not_called()

    def test_jupytext_command_failure(self, mock_subprocess, fs_setup):
        """TC-05: Returns False if jupytext exit code is non-zero."""
        mock_subprocess.return_value.returncode = 1
        assert run([str(fs_setup / "analysis.ipynb")]) is False

    def test_missing_file_returns_false(self, mock_subprocess, tmp_path):
        """TC-06: Returns False if target path does not exist."""
        assert run([str(tmp_path / "ghost.ipynb")]) is False

    def test_batch_partial_failure(self, mock_subprocess, fs_setup):
        """TC-07: Ensures one failure in a batch fails the whole hook."""
        f1, f2 = fs_setup / "1.ipynb", fs_setup / "2.ipynb"
        f1.write_text("{}")
        f2.write_text("{}")
        mock_subprocess.side_effect = [MagicMock(returncode=0), MagicMock(returncode=1)]
        assert run([str(f1), str(f2)]) is False

    @pytest.mark.parametrize("path_input", ["", None, 123])
    def test_invalid_input_types(self, path_input):
        """TC-08, 09, 10: Robustness check against malformed inputs."""
        assert run([path_input]) is False

    def test_empty_input_list(self, mock_subprocess):
        """TC-11: Returns True (no-op) for empty list."""
        assert run([]) is True

    def test_unexpected_exception_handling(self, mock_subprocess, fs_setup):
        """EXTRA: Forces an Exception to cover the 'except' block (Lines 51-53)."""
        mock_subprocess.side_effect = OSError("System error")
        assert run([str(fs_setup / "analysis.ipynb")]) is False
