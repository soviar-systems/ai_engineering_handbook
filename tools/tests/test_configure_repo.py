"""
Test suite for configure_repo.py script.

Tests the repository configuration functionality including:
- UV sync and pre-commit installation
- Aider config file copying
- Script permission settings
- Symlink creation to ~/bin
"""

import os
import runpy
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from tools.scripts.configure_repo import (
    AiderConfigCopier,
    ConfigureRepoCLI,
    Reporter,
    ScriptPermissions,
    SymlinkCreator,
    UvSyncRunner,
)


# ======================
# Unit Tests: UvSyncRunner
# ======================


class TestUvSyncRunner:
    @pytest.fixture
    def runner(self):
        return UvSyncRunner(verbose=False, dry_run=False)

    def test_run_uv_sync_success(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.run_uv_sync()
            assert result is True
            mock_run.assert_called_once()
            assert "uv" in mock_run.call_args[0][0]
            assert "sync" in mock_run.call_args[0][0]

    def test_run_uv_sync_failure(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = runner.run_uv_sync()
            assert result is False

    def test_run_precommit_install_success(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.run_precommit_install()
            assert result is True
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "pre-commit" in args
            assert "install" in args

    def test_run_precommit_install_failure(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = runner.run_precommit_install()
            assert result is False

    def test_run_precommit_install_commit_msg_success(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.run_precommit_install_commit_msg()
            assert result is True
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "pre-commit" in args
            assert "install" in args
            assert "--hook-type" in args
            assert "commit-msg" in args

    def test_run_precommit_install_commit_msg_failure(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = runner.run_precommit_install_commit_msg()
            assert result is False

    def test_run_all_success(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.run()
            assert result is True
            assert mock_run.call_count == 3

    def test_run_all_uv_sync_fails(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = runner.run()
            assert result is False
            assert mock_run.call_count == 1

    def test_run_all_precommit_install_fails(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),  # uv sync succeeds
                MagicMock(returncode=1),  # pre-commit install fails
            ]
            result = runner.run()
            assert result is False
            assert mock_run.call_count == 2

    def test_run_all_commit_msg_hook_fails(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),  # uv sync succeeds
                MagicMock(returncode=0),  # pre-commit install succeeds
                MagicMock(returncode=1),  # commit-msg hook install fails
            ]
            result = runner.run()
            assert result is False
            assert mock_run.call_count == 3

    def test_dry_run_skips_execution(self):
        runner = UvSyncRunner(verbose=False, dry_run=True)
        with patch("subprocess.run") as mock_run:
            result = runner.run()
            assert result is True
            mock_run.assert_not_called()

    def test_verbose_output(self, capsys):
        runner = UvSyncRunner(verbose=True, dry_run=True)
        runner.run()
        captured = capsys.readouterr()
        assert "uv sync" in captured.out.lower() or "dry run" in captured.out.lower()


# ======================
# Unit Tests: AiderConfigCopier
# ======================


class TestAiderConfigCopier:
    @pytest.fixture
    def copier(self, tmp_path):
        return AiderConfigCopier(
            repo_root=tmp_path,
            verbose=False,
            dry_run=False,
        )

    def test_copy_when_source_exists_target_missing(self, tmp_path):
        # Setup: create source file
        configs_dir = tmp_path / "tools" / "configs"
        configs_dir.mkdir(parents=True)
        source = configs_dir / "aider.conf.yml"
        source.write_text("test: value", encoding="utf-8")

        copier = AiderConfigCopier(repo_root=tmp_path, verbose=False, dry_run=False)
        result = copier.copy()

        assert result is True
        target = tmp_path / ".aider.conf.yml"
        assert target.exists()
        assert target.read_text() == "test: value"

    def test_skip_when_target_exists(self, tmp_path, capsys):
        # Setup: create both source and target
        configs_dir = tmp_path / "tools" / "configs"
        configs_dir.mkdir(parents=True)
        source = configs_dir / "aider.conf.yml"
        source.write_text("new: content", encoding="utf-8")
        target = tmp_path / ".aider.conf.yml"
        target.write_text("existing: content", encoding="utf-8")

        copier = AiderConfigCopier(repo_root=tmp_path, verbose=True, dry_run=False)
        result = copier.copy()

        assert result is True
        # Target should NOT be overwritten
        assert target.read_text() == "existing: content"
        captured = capsys.readouterr()
        assert "exists" in captured.out.lower() or "skip" in captured.out.lower()

    def test_warning_when_source_missing(self, tmp_path, capsys):
        copier = AiderConfigCopier(repo_root=tmp_path, verbose=True, dry_run=False)
        result = copier.copy()

        assert result is True  # Should continue gracefully
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "skip" in captured.out.lower()

    def test_dry_run_does_not_copy(self, tmp_path):
        # Setup: create source file
        configs_dir = tmp_path / "tools" / "configs"
        configs_dir.mkdir(parents=True)
        source = configs_dir / "aider.conf.yml"
        source.write_text("test: value", encoding="utf-8")

        copier = AiderConfigCopier(repo_root=tmp_path, verbose=False, dry_run=True)
        result = copier.copy()

        assert result is True
        target = tmp_path / ".aider.conf.yml"
        assert not target.exists()

    def test_verbose_output_on_copy(self, tmp_path, capsys):
        configs_dir = tmp_path / "tools" / "configs"
        configs_dir.mkdir(parents=True)
        source = configs_dir / "aider.conf.yml"
        source.write_text("test: value", encoding="utf-8")

        copier = AiderConfigCopier(repo_root=tmp_path, verbose=True, dry_run=False)
        copier.copy()

        captured = capsys.readouterr()
        assert "aider" in captured.out.lower()


# ======================
# Unit Tests: ScriptPermissions
# ======================


class TestScriptPermissions:
    @pytest.fixture
    def permissions(self, tmp_path):
        return ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)

    def test_makes_sh_files_executable(self, tmp_path):
        # Create .sh file
        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash\necho hello", encoding="utf-8")
        # Remove execute permission
        script.chmod(0o644)

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)
        result = permissions.set_permissions()

        assert result is True
        assert os.access(script, os.X_OK)

    def test_makes_py_files_executable(self, tmp_path):
        # Create .py file
        script = tmp_path / "test.py"
        script.write_text("#!/usr/bin/env python3\nprint('hello')", encoding="utf-8")
        script.chmod(0o644)

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)
        result = permissions.set_permissions()

        assert result is True
        assert os.access(script, os.X_OK)

    def test_handles_nested_directories(self, tmp_path):
        # Create nested structure
        nested = tmp_path / "sub" / "deep"
        nested.mkdir(parents=True)
        script = nested / "script.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")
        script.chmod(0o644)

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)
        result = permissions.set_permissions()

        assert result is True
        assert os.access(script, os.X_OK)

    def test_skips_directories_named_like_scripts(self, tmp_path):
        # Create a directory named 'script.py'
        dir_path = tmp_path / "script.py"
        dir_path.mkdir()

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)
        result = permissions.set_permissions()

        assert result is True
        # Should not crash and directory should remain a directory
        assert dir_path.is_dir()

    def test_dry_run_does_not_change_permissions(self, tmp_path):
        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash", encoding="utf-8")
        script.chmod(0o644)
        original_mode = script.stat().st_mode

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=True)
        result = permissions.set_permissions()

        assert result is True
        assert script.stat().st_mode == original_mode

    def test_verbose_output(self, tmp_path, capsys):
        script = tmp_path / "test.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")
        script.chmod(0o644)

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=True, dry_run=False)
        permissions.set_permissions()

        captured = capsys.readouterr()
        assert "executable" in captured.out.lower() or "test.py" in captured.out

    def test_counts_modified_files(self, tmp_path):
        # Create multiple scripts
        (tmp_path / "a.py").write_text("#!/usr/bin/env python3", encoding="utf-8")
        (tmp_path / "b.sh").write_text("#!/bin/bash", encoding="utf-8")
        (tmp_path / "c.py").write_text("#!/usr/bin/env python3", encoding="utf-8")
        for f in tmp_path.glob("*"):
            f.chmod(0o644)

        permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)
        permissions.set_permissions()

        assert permissions.modified_count == 3


# ======================
# Unit Tests: SymlinkCreator
# ======================


class TestSymlinkCreator:
    @pytest.fixture
    def setup_dirs(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        return scripts_dir, bin_dir

    def test_creates_symlinks_for_files(self, tmp_path, setup_dirs):
        scripts_dir, bin_dir = setup_dirs
        script = scripts_dir / "test.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=False,
        )
        result = creator.create()

        assert result is True
        link = bin_dir / "test.py"
        assert link.is_symlink()
        assert link.resolve() == script.resolve()

    def test_skips_directories(self, tmp_path, setup_dirs):
        scripts_dir, bin_dir = setup_dirs
        subdir = scripts_dir / "subdir"
        subdir.mkdir()

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=False,
        )
        result = creator.create()

        assert result is True
        # Should not create symlink for directory
        assert not (bin_dir / "subdir").exists()

    def test_updates_existing_symlinks(self, tmp_path, setup_dirs):
        scripts_dir, bin_dir = setup_dirs
        script = scripts_dir / "test.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")

        # Create old symlink pointing elsewhere
        old_target = tmp_path / "old_script.py"
        old_target.write_text("old", encoding="utf-8")
        link = bin_dir / "test.py"
        link.symlink_to(old_target)

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=False,
        )
        result = creator.create()

        assert result is True
        assert link.resolve() == script.resolve()

    def test_creates_bin_dir_if_missing(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        script = scripts_dir / "test.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")

        bin_dir = tmp_path / "bin"
        # bin_dir does NOT exist

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=False,
        )
        result = creator.create()

        assert result is True
        assert bin_dir.exists()
        assert (bin_dir / "test.py").is_symlink()

    def test_dry_run_does_not_create_symlinks(self, tmp_path, setup_dirs):
        scripts_dir, bin_dir = setup_dirs
        script = scripts_dir / "test.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=True,
        )
        result = creator.create()

        assert result is True
        assert not (bin_dir / "test.py").exists()

    def test_verbose_output(self, tmp_path, setup_dirs, capsys):
        scripts_dir, bin_dir = setup_dirs
        script = scripts_dir / "test.py"
        script.write_text("#!/usr/bin/env python3", encoding="utf-8")

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=True,
            dry_run=False,
        )
        creator.create()

        captured = capsys.readouterr()
        assert "symlink" in captured.out.lower() or "test.py" in captured.out

    def test_counts_created_symlinks(self, tmp_path, setup_dirs):
        scripts_dir, bin_dir = setup_dirs
        (scripts_dir / "a.py").write_text("#!/usr/bin/env python3", encoding="utf-8")
        (scripts_dir / "b.sh").write_text("#!/bin/bash", encoding="utf-8")

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=False,
        )
        creator.create()

        assert creator.created_count == 2

    def test_handles_missing_scripts_dir(self, tmp_path):
        scripts_dir = tmp_path / "nonexistent"
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        creator = SymlinkCreator(
            scripts_dir=scripts_dir,
            bin_dir=bin_dir,
            verbose=False,
            dry_run=False,
        )
        result = creator.create()

        assert result is True  # Should gracefully handle missing dir


# ======================
# Unit Tests: Reporter
# ======================


class TestReporter:
    def test_report_success(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report_success("Setup complete", verbose=True)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Setup complete" in captured.out

    def test_report_success_quiet(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report_success("Setup complete", verbose=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_report_failure(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report_failure("Something went wrong")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out


# ======================
# Integration Tests: ConfigureRepoCLI
# ======================


class TestConfigureRepoCLI:
    @pytest.fixture
    def cli(self):
        return ConfigureRepoCLI()

    @pytest.fixture
    def mock_env(self, tmp_path, monkeypatch):
        """Setup a mock environment with all required directories."""
        # Create tools/scripts and tools/configs
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        configs_dir = tmp_path / "tools" / "configs"
        configs_dir.mkdir(parents=True)

        # Create aider config
        (configs_dir / "aider.conf.yml").write_text("test: true", encoding="utf-8")

        # Create some scripts
        (scripts_dir / "test.py").write_text("#!/usr/bin/env python3", encoding="utf-8")
        (scripts_dir / "test.sh").write_text("#!/bin/bash", encoding="utf-8")

        # Create bin dir
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        return tmp_path, bin_dir

    def test_dry_run_mode(self, cli, mock_env, capsys):
        tmp_path, bin_dir = mock_env

        with patch("subprocess.run") as mock_run:
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--dry-run", "--verbose", f"--bin-dir={bin_dir}"])
            assert exc_info.value.code == 0

        # subprocess should not be called in dry-run mode
        mock_run.assert_not_called()
        captured = capsys.readouterr()
        assert "dry" in captured.out.lower()

    def test_skip_uv_sync_flag(self, cli, mock_env):
        tmp_path, bin_dir = mock_env

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--skip-uv-sync", f"--bin-dir={bin_dir}"])
            assert exc_info.value.code == 0

        # uv sync should not be called
        mock_run.assert_not_called()

    def test_skip_symlinks_flag(self, cli, mock_env):
        tmp_path, bin_dir = mock_env

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--skip-symlinks", f"--bin-dir={bin_dir}"])
            assert exc_info.value.code == 0

        # No symlinks should be created
        assert not (bin_dir / "test.py").exists()

    def test_verbose_flag(self, cli, mock_env, capsys):
        tmp_path, bin_dir = mock_env

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--verbose", f"--bin-dir={bin_dir}"])
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_full_run_success(self, cli, mock_env):
        tmp_path, bin_dir = mock_env

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as exc_info:
                cli.run([f"--bin-dir={bin_dir}"])
            assert exc_info.value.code == 0

        # Verify symlinks created
        assert (bin_dir / "test.py").is_symlink()
        assert (bin_dir / "test.sh").is_symlink()

        # Verify aider config copied
        assert (tmp_path / ".aider.conf.yml").exists()

    def test_help_flag(self, cli):
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--help"])
        assert exc_info.value.code == 0


# ======================
# Parametrized Edge Cases
# ======================


@pytest.mark.parametrize(
    "filename,should_be_executable",
    [
        ("script.py", True),
        ("script.sh", True),
        ("script.txt", False),
        ("script.md", False),
        ("Makefile", False),
        (".hidden.py", True),
        ("test.PY", False),  # Case sensitive
        ("test.SH", False),  # Case sensitive
    ],
)
def test_script_permissions_file_types(tmp_path, filename, should_be_executable):
    script = tmp_path / filename
    script.write_text("content", encoding="utf-8")
    script.chmod(0o644)

    permissions = ScriptPermissions(repo_root=tmp_path, verbose=False, dry_run=False)
    permissions.set_permissions()

    assert os.access(script, os.X_OK) == should_be_executable


# ======================
# Main Entry Point Test
# ======================


def test_main_entry_point():
    with patch("sys.argv", ["configure_repo.py", "--help"]), pytest.raises(SystemExit):
        runpy.run_path("tools/scripts/configure_repo.py", run_name="__main__")

    with patch("tools.scripts.configure_repo.ConfigureRepoCLI.run") as mock_run:
        mock_run.side_effect = SystemExit(0)
        from tools.scripts.configure_repo import main

        with pytest.raises(SystemExit):
            main()
        mock_run.assert_called_once()
