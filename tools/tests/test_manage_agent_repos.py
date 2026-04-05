"""
Tests for manage_agent_repos.py script.

Tests the contract of the agent repository management tool:
- Repository discovery in agents_source_code/
- Git operations (clone, pull, status)
- CLI exit codes and argument parsing

Design: Tests behavior boundaries and contracts, not implementation details.
Uses mocked git operations for deterministic, fast testing.

Non-brittleness principles applied:
- Test exit codes, not output messages
- Test presence/absence of patterns, not exact wording
- Use semantic assertions (len > 0, in set) not exact counts where not contractual
- Mock external dependencies (git functions) — never call real git
- Import module once at top — single point of update on rename
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import tools.scripts.manage_agent_repos as _module


class TestAgentRepoDataClass:
    """Verify AgentRepo data class structure and properties."""

    def test_agent_repo_creation(self):
        """AgentRepo can be instantiated with required fields."""
        repo = _module.AgentRepo(
            name="langgraph",
            path=Path("/tmp/test/langgraph"),
            url="https://github.com/langchain-ai/langgraph",
        )
        assert repo.name == "langgraph"
        assert repo.path == Path("/tmp/test/langgraph")
        assert repo.url == "https://github.com/langchain-ai/langgraph"
        assert repo.branch is None  # Optional field


class TestDiscoverRepos:
    """Verify repository discovery in agents_source_code/ directory.
    
    Contract: Returns list of AgentRepo objects for each git repo found.
    """

    def test_discover_repos_finds_git_repos(self, tmp_path):
        """Discover returns AgentRepo for directories with .git."""
        # Create mock directories with .git subdirs
        langgraph = tmp_path / "langgraph"
        autogen = tmp_path / "autogen"
        langgraph.mkdir()
        autogen.mkdir()
        (langgraph / ".git").mkdir()
        (autogen / ".git").mkdir()
        
        # Create a non-git directory
        readme = tmp_path / "README.md"
        readme.write_text("# Readme")

        repos = _module.discover_repos(tmp_path)
        
        assert len(repos) == 2
        assert all(isinstance(r, _module.AgentRepo) for r in repos)
        assert {r.name for r in repos} == {"langgraph", "autogen"}

    def test_discover_repos_empty_directory(self, tmp_path):
        """Returns empty list when no repos exist."""
        repos = _module.discover_repos(tmp_path)
        
        assert repos == []


class TestCLIArgumentParsing:
    """Verify CLI argument parsing and dispatch.
    
    Contract: CLI exits with appropriate codes for valid/invalid arguments.
    """

    def test_setup_command_requires_url(self, capsys):
        """setup command fails when URL is missing."""
        with patch("sys.argv", ["manage_agent_repos.py", "setup"]):
            with pytest.raises(SystemExit):
                _module.main()

    @patch.object(_module, "detect_repo_root")
    def test_list_command_valid(self, mock_detect, tmp_path):
        """list command parses successfully."""
        mock_detect.return_value = tmp_path
        (tmp_path / _module.AGENTS_SOURCE_CODE_DIR).mkdir(parents=True)

        with patch("sys.argv", ["manage_agent_repos.py", "list"]):
            exit_code = _module.main()

        # Contract: exits without error when agents directory exists
        assert exit_code == 0

    @patch.object(_module, "detect_repo_root")
    def test_list_missing_agents_directory(self, mock_detect, tmp_path):
        """List exits with error when agents directory doesn't exist."""
        mock_detect.return_value = tmp_path
        # Don't create agents directory

        exit_code = _module.list_command()

        # Contract: exits 1 when agents directory missing
        assert exit_code != 0

    @patch.object(_module, "detect_repo_root")
    def test_update_command_valid(self, mock_detect, tmp_path):
        """update command parses successfully."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        with patch("sys.argv", ["manage_agent_repos.py", "update"]):
            exit_code = _module.main()

        # Contract: exits 0 when no repos found (not an error condition)
        assert exit_code == 0

    def test_invalid_command(self, capsys):
        """Invalid command exits with error."""
        with patch("sys.argv", ["manage_agent_repos.py", "invalid_cmd"]):
            with pytest.raises(SystemExit):
                _module.main()


class TestSetupCommand:
    """Verify setup command orchestrates clone + config updates.
    
    Contract: Setup clones repo and updates configuration files.
    """

    @patch.object(_module, "add_to_myst_exclude", create=True)
    @patch.object(_module, "clone_repo")
    @patch.object(_module, "detect_repo_root")
    def test_setup_clones_and_configures(
        self, mock_detect, mock_clone, mock_add_exclude, tmp_path
    ):
        """Setup clones repo when agents directory exists."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)
        mock_clone.return_value = True

        exit_code = _module.setup_command(
            "https://github.com/test/repo",
        )

        assert exit_code == 0
        mock_clone.assert_called_once()

    @patch.object(_module, "clone_repo")
    @patch.object(_module, "detect_repo_root")
    def test_setup_fails_on_clone_error(self, mock_detect, mock_clone, tmp_path):
        """Setup exits with error when clone fails."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)
        mock_clone.return_value = False

        exit_code = _module.setup_command(
            "https://github.com/test/invalid",
        )

        assert exit_code != 0

    @patch.object(_module, "clone_repo")
    @patch.object(_module, "detect_repo_root")
    def test_setup_repo_already_exists(self, mock_detect, mock_clone, tmp_path):
        """Setup exits with error when repo already exists."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        # Create existing repo directory
        existing_repo = agents_dir / "existing-repo"
        existing_repo.mkdir()

        exit_code = _module.setup_command(
            "https://github.com/test/existing-repo",
        )

        # Contract: exits 1 when repo already exists
        assert exit_code != 0

    @patch.object(_module, "clone_repo")
    @patch.object(_module, "detect_repo_root")
    def test_setup_missing_agents_directory(self, mock_detect, mock_clone, tmp_path):
        """Setup exits with error when agents directory doesn't exist."""
        mock_detect.return_value = tmp_path
        # Don't create agents directory

        exit_code = _module.setup_command(
            "https://github.com/test/repo",
        )

        # Contract: exits 1 when agents directory missing
        assert exit_code != 0
        # Contract: never attempts to clone when directory doesn't exist
        assert mock_clone.call_count == 0


class TestUpdateCommand:
    """Verify update command pulls all repos.
    
    Contract: Update pulls all repos and exits 0 if all succeed, 1 if any fail.
    """

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_all_success(self, mock_detect, mock_pull, tmp_path):
        """Update exits 0 when all repos pull successfully."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        # Create mock repos
        repo1 = agents_dir / "repo1"
        repo2 = agents_dir / "repo2"
        repo1.mkdir()
        repo2.mkdir()
        (repo1 / ".git").mkdir()
        (repo2 / ".git").mkdir()

        mock_pull.return_value = (True, "Already up to date.")

        exit_code = _module.update_command(repo_names=[])

        # Contract: exits 0 when all succeed
        assert exit_code == 0
        # Contract: calls pull_repo for each discovered repo
        assert mock_pull.call_count > 0

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_partial_failure(self, mock_detect, mock_pull, tmp_path):
        """Update exits 1 when any repo fails."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo2 = agents_dir / "repo2"
        repo1.mkdir()
        repo2.mkdir()
        (repo1 / ".git").mkdir()
        (repo2 / ".git").mkdir()

        # First succeeds, second fails
        mock_pull.side_effect = [(True, "Updated"), (False, "error: conflict")]

        exit_code = _module.update_command(repo_names=[])

        # Contract: exits 1 when any repo fails
        assert exit_code != 0

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_specific_repos(self, mock_detect, mock_pull, tmp_path):
        """Update only specified repos when names provided."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo2 = agents_dir / "repo2"
        repo3 = agents_dir / "repo3"
        repo1.mkdir()
        repo2.mkdir()
        repo3.mkdir()
        (repo1 / ".git").mkdir()
        (repo2 / ".git").mkdir()
        (repo3 / ".git").mkdir()

        mock_pull.return_value = (True, "Already up to date.")

        exit_code = _module.update_command(repo_names=["repo1", "repo3"])

        # Contract: exits 0 when specified repos succeed
        assert exit_code == 0
        # Contract: only calls pull_repo for specified repos (not all 3)
        assert mock_pull.call_count == 2

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_parallel_execution(self, mock_detect, mock_pull, tmp_path):
        """Update with --parallel flag uses concurrent execution."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Updated")

        exit_code = _module.update_command(repo_names=[], parallel=True)

        # Contract: exits 0 on success with parallel flag
        assert exit_code == 0
        assert mock_pull.call_count == 1

    @patch.object(_module, "detect_repo_root")
    def test_update_missing_agents_directory(self, mock_detect, tmp_path):
        """Update exits with error when agents directory doesn't exist."""
        mock_detect.return_value = tmp_path
        # Don't create agents directory

        exit_code = _module.update_command(repo_names=[])

        # Contract: exits 1 when agents directory missing
        assert exit_code != 0

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_no_repos_found(self, mock_detect, mock_pull, tmp_path):
        """Update exits 0 when agents directory exists but is empty."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)
        # Don't create any repos

        exit_code = _module.update_command(repo_names=[])

        # Contract: exits 0 when no repos found (not an error)
        assert exit_code == 0
        # Contract: never calls pull_repo when no repos exist
        assert mock_pull.call_count == 0

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_specified_repos_not_found(self, mock_detect, mock_pull, tmp_path):
        """Update exits with error when specified repos don't exist."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _module.AGENTS_SOURCE_CODE_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        exit_code = _module.update_command(repo_names=["nonexistent-repo"])

        # Contract: exits 1 when specified repos not found
        assert exit_code != 0
