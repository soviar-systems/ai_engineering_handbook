# helpers/scripts/hooks/test_sync_and_verify.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sync_and_verify import GitInterface, NotebookPairProcessor, SyncOrchestrator


class TestGitInterface:
    def setup_method(self):
        self.git = GitInterface()

    @patch("sync_and_verify.subprocess.run")
    def test_run_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="out", returncode=0)
        assert self.git.run(["ls"]).stdout == "out"

    @patch("sync_and_verify.subprocess.run")
    def test_jupytext_sync(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.git.jupytext_sync(Path("t.ipynb"))
        assert "jupytext" in mock_run.call_args[0][0]

    @patch("sync_and_verify.subprocess.run")
    def test_is_in_index(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert self.git.is_in_index(Path("f.md")) is True

    @patch("sync_and_verify.subprocess.run")
    def test_is_file_fully_staged(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert self.git.is_file_fully_staged(Path("f.md")) is True


class TestNotebookPairProcessor:
    def test_should_skip(self):
        assert (
            NotebookPairProcessor(
                Path("pr/tg_channel/a.ipynb"), GitInterface()
            ).should_skip()
            is True
        )
        assert (
            NotebookPairProcessor(
                Path("notebooks/a.ipynb"), GitInterface()
            ).should_skip()
            is False
        )

    @patch.object(GitInterface, "jupytext_sync", return_value=MagicMock(returncode=0))
    @patch.object(GitInterface, "is_in_index", return_value=True)
    @patch.object(GitInterface, "is_file_fully_staged", return_value=True)
    def test_process_success(self, m1, m2, m3):
        assert NotebookPairProcessor(Path("a.ipynb"), GitInterface()).process() is True

    @pytest.mark.parametrize(
        "path,skip",
        [
            ("pr/tg_channel/a.ipynb", True),
            ("pr/tg_channel/b.md", True),
            ("notebooks/a.ipynb", False),
            ("other/pr/tg_channel/c.ipynb", True),
            ("pr/tg_channel.ipynb", True),
            ("notebooks/pr/tg_channel/d.ipynb", True),
        ],
    )  # 6 tests
    def test_should_skip_parametrized(self, path, skip):
        assert NotebookPairProcessor(Path(path), GitInterface()).should_skip() == skip


class TestSyncOrchestrator:
    @patch("sync_and_verify.Path.exists", return_value=True)
    @patch.object(NotebookPairProcessor, "process", return_value=True)
    def test_all_success_message(self, m1, m2, capsys):
        assert SyncOrchestrator().run(["a.ipynb"]) == 0
        assert "synced" in capsys.readouterr().out

    @patch("sync_and_verify.Path.exists", return_value=True)
    @patch.object(NotebookPairProcessor, "process", return_value=False)
    def test_failure_exit_code(self, m1, m2):
        assert SyncOrchestrator().run(["a.ipynb"]) == 1

    def test_nonexistent_file_ignored(self, tmp_path):
        nb = tmp_path / "exists.ipynb"
        nb.write_text("{}")
        # Fix: ignore the 'self' argument passed by mock to Path.exists
        with patch(
            "sync_and_verify.Path.exists",
            side_effect=lambda *args: str(args[0]) == str(nb) if args else False,
        ):
            with patch.object(NotebookPairProcessor, "process", return_value=True):
                assert SyncOrchestrator().run([str(nb), "missing.ipynb"]) == 0

    @patch("sync_and_verify.Path.exists", return_value=True)
    def test_orchestrator_skips(self, m, capsys):
        assert SyncOrchestrator().run(["pr/tg_channel/a.ipynb"]) == 0


class TestDefensive:
    @patch.object(GitInterface, "run")
    def test_jupytext_failure(self, mock_run, capsys):
        mock_run.return_value = MagicMock(returncode=1, stderr="err")
        assert NotebookPairProcessor(Path("a.ipynb"), GitInterface()).process() is False
        assert "failed" in capsys.readouterr().err

    @patch("sync_and_verify.subprocess.run", side_effect=FileNotFoundError("no uv"))
    def test_missing_uv(self, m, capsys):
        # Script catch block converts FileNotFoundError to a returncode=1 process
        assert NotebookPairProcessor(Path("a.ipynb"), GitInterface()).process() is False

    @patch("sync_and_verify.subprocess.run", side_effect=PermissionError("denied"))
    def test_permission_denied(self, m):
        assert NotebookPairProcessor(Path("a.ipynb"), GitInterface()).process() is False


@pytest.mark.parametrize(
    "i_idx, m_idx, i_stg, m_stg, expected",
    [
        (True, True, True, True, True),
        (True, True, True, False, False),
        (True, True, False, True, False),
        (True, False, True, True, False),
        (False, True, True, True, False),
        (False, False, True, True, False),
        (True, True, False, False, False),
        (False, False, False, False, False),
    ],
)  # 8 tests
def test_staging_integrity_parametrized(i_idx, m_idx, i_stg, m_stg, expected):
    git = GitInterface()
    with patch.object(git, "jupytext_sync", return_value=MagicMock(returncode=0)):
        with patch.object(
            git,
            "is_in_index",
            side_effect=lambda p: i_idx if p.suffix == ".ipynb" else m_idx,
        ):
            with patch.object(
                git,
                "is_file_fully_staged",
                side_effect=lambda p: i_stg if p.suffix == ".ipynb" else m_stg,
            ):
                assert NotebookPairProcessor(Path("t.ipynb"), git).process() == expected
