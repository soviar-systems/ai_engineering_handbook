from pathlib import Path
from unittest.mock import patch

import pytest

from tools.scripts.hooks.jupytext_verify_pair.jupytext_verify_pair import run

# --- Fixtures ---


@pytest.fixture
def mock_git():
    """Mocks GitService to isolate logic from the local git environment."""
    with patch(
        "tools.scripts.hooks.jupytext_verify_pair.jupytext_verify_pair.GitService",
        autospec=True,
    ) as mock:
        yield mock.return_value


@pytest.fixture
def fs_setup(tmp_path):
    """Creates physical dummy files to satisfy path.is_file() checks."""
    ipynb = tmp_path / "test.ipynb"
    md = tmp_path / "test.md"
    ipynb.write_text("{}")
    md.write_text("# Test")
    return ipynb


# --- Tests ---


class TestJupytextVerifyPair:
    # 1-7. The Core Logic Matrix (Comprehensive Truth Table)
    @pytest.mark.parametrize(
        "i_tracked, md_tracked, i_dirty, md_dirty, expected, state_desc",
        [
            (True, True, False, False, True, "State 1: Both staged and clean"),
            (True, True, True, False, False, "State 2: ipynb has unstaged changes"),
            (True, True, False, True, False, "State 3: md has unstaged changes"),
            (False, True, False, False, False, "State 4: ipynb not in index"),
            (True, False, False, False, False, "State 5: md not in index"),
            # State 0/6: Refined to pass if neither is tracked (WIP isolation)
            (False, False, False, False, True, "State 0: Neither in index (Ignore)"),
            (True, True, True, True, False, "State 7: Both have unstaged changes"),
        ],
    )
    def test_logic_matrix(
        self,
        mock_git,
        fs_setup,
        i_tracked,
        md_tracked,
        i_dirty,
        md_dirty,
        expected,
        state_desc,
    ):
        """Verifies the integrity logic for all possible Git staging/dirty states."""
        mock_git.is_in_index.side_effect = (
            lambda p: i_tracked if Path(p).suffix == ".ipynb" else md_tracked
        )
        mock_git.has_unstaged_changes.side_effect = (
            lambda p: i_dirty if Path(p).suffix == ".ipynb" else md_dirty
        )

        assert run([str(fs_setup)]) is expected, f"Failed logic for {state_desc}"

    # 8. State 8 Resilience (Git Failure)
    def test_git_service_exception_handling(self, mock_git, fs_setup, capsys):
        """TC-08: Ensures State 8 (System/Git Failure) returns False without crashing."""
        mock_git.is_in_index.side_effect = Exception("fatal: ambiguous argument")

        assert run([str(fs_setup)]) is False
        captured = capsys.readouterr()
        assert "State 8 Failure" in captured.err

    # 9-11. Exclusion Logic (Aligning Test with Production)
    @pytest.mark.parametrize("ignored_dir", ["architecture", "in_progress", ".venv"])
    def test_robust_exclusion_absolute_paths(self, mock_git, tmp_path, ignored_dir):
        """Verifies that absolute paths in excluded dirs are skipped (Fixes prod bug)."""
        ignored_folder = tmp_path / ignored_dir
        ignored_folder.mkdir(parents=True, exist_ok=True)
        nb_path = ignored_folder / "research.ipynb"
        nb_path.write_text("{}")

        # Run with absolute path - should skip and return True
        assert run([str(nb_path)]) is True
        mock_git.is_in_index.assert_not_called()

    def test_extension_filtering(self, mock_git, tmp_path):
        """Ensures non-paired extensions (.txt, .py) are ignored immediately."""
        txt_file = tmp_path / "info.txt"
        txt_file.write_text("ignore")
        assert run([str(txt_file)]) is True
        mock_git.is_in_index.assert_not_called()

    # 12-14. Error Messaging
    def test_partial_tracking_message_content(self, mock_git, fs_setup, capsys):
        """Checks if instructions to 'git add' the specific missing file are printed."""
        # ipynb tracked, md NOT tracked (State 5)
        mock_git.is_in_index.side_effect = lambda p: Path(p).suffix == ".ipynb"

        run([str(fs_setup)])
        captured = capsys.readouterr()
        assert "Partial Tracking" in captured.err
        assert "test.ipynb is staged but test.md is not" in captured.err
        assert "Run 'git add test.md'" in captured.err

    def test_dirty_file_message_content(self, mock_git, fs_setup, capsys):
        """Checks if instructions to 'git add' the dirty file are printed."""
        mock_git.is_in_index.return_value = True
        # ipynb is dirty
        mock_git.has_unstaged_changes.side_effect = lambda p: Path(p).suffix == ".ipynb"

        run([str(fs_setup)])
        captured = capsys.readouterr()
        assert "Unstaged changes in test.ipynb" in captured.err

    # 15-17. Batch Handling and Physical Files
    def test_batch_failure_persistence(self, mock_git, tmp_path):
        """Ensures a single failure in a set of paths fails the entire hook run."""
        f1 = tmp_path / "valid.ipynb"
        f2 = tmp_path / "invalid.ipynb"
        for f in [f1, f2]:
            f.write_text("{}")
            f.with_suffix(".md").write_text("#")

        # First pair staged/clean, second pair missing .md tracking
        mock_git.is_in_index.side_effect = [True, True, True, False]
        mock_git.has_unstaged_changes.return_value = False

        assert run([str(f1), str(f2)]) is False

    def test_missing_physical_file_is_skipped(self, tmp_path):
        """Deleted files on disk should be skipped to let Git handle the removal."""
        ghost = tmp_path / "deleted.ipynb"
        assert run([str(ghost)]) is True

    # 18-20. Defensive Programming (Edge Cases)
    @pytest.mark.parametrize("invalid_input", [None, "", 123, []])
    def test_malformed_input_resilience(self, invalid_input):
        """Tests handling of non-string or empty inputs."""
        assert run([invalid_input]) is False

    def test_path_resolution_consistency(self, mock_git, fs_setup):
        """Ensures paths are resolved correctly before being passed to GitService."""
        # Use a relative-looking path
        rel_path = f"./{fs_setup.name}"
        with patch(
            "tools.scripts.hooks.jupytext_verify_pair.jupytext_verify_pair.Path.resolve"
        ) as mock_resolve:
            mock_resolve.return_value = fs_setup
            run([rel_path])
            # The git service should receive the resolved path, not the string
            mock_git.is_in_index.assert_called()

    def test_non_string_path_triggers_failure(self, mock_git):
        """Explicitly targets line 44: non-string input sets overall_success=False."""
        assert run([123]) is False

    def test_run_with_md_file(self, mock_git, tmp_path):
        """processing .md files as input."""
        md_path = tmp_path / "example.md"
        ipynb_path = tmp_path / "example.ipynb"
        md_path.write_text("# Test")
        ipynb_path.write_text("{}")

        # Simulate both files being staged and clean
        mock_git.is_in_index.return_value = True
        mock_git.has_unstaged_changes.return_value = False

        result = run([str(md_path)])
        assert result is True
