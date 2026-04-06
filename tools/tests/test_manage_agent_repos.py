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

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import tools.scripts.manage_agent_repos as _module

_AGENTS_DIR = next(iter(_module.EXTERNAL_REPO_DIRS))


class TestAgentsSourceCodeDirResolution:
    """Verify EXTERNAL_REPO_DIRS resolves from the registry.

    Contract: The module reads get_external_repo_paths at import time.
    When registry has entries, all are used.
    When registry is empty/missing, the fallback default is used.

    Because detect_repo_root and get_external_repo_paths are called at
    module import time, we must patch them before the module loads.
    """

    def _reload_module_with_registry(self, registry_entries, detect_root_return):
        """Reload manage_agent_repos module with mocked registry and detect_repo_root."""
        mod_name = "tools.scripts.manage_agent_repos"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        # Patch at the source modules BEFORE import triggers resolve-time calls
        with patch("tools.scripts.paths.get_external_repo_paths", return_value=registry_entries):
            with patch("tools.scripts.git.detect_repo_root", return_value=detect_root_return):
                reloaded = importlib.import_module(mod_name)
                return reloaded

    def test_resolves_from_registry(self, tmp_path):
        """EXTERNAL_REPO_DIRS uses paths from registry when populated."""
        registry_entries = {"ai_agents/agents_source_code"}
        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        assert reloaded.EXTERNAL_REPO_DIRS == {Path("ai_agents/agents_source_code")}

    def test_fallback_when_registry_empty(self, tmp_path):
        """EXTERNAL_REPO_DIRS uses fallback when registry has no entries."""
        registry_entries = set()
        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        # Fallback path contains "agents_source_code"
        assert any("agents_source_code" in str(p) for p in reloaded.EXTERNAL_REPO_DIRS)

    def test_fallback_when_registry_missing(self, tmp_path):
        """EXTERNAL_REPO_DIRS uses fallback when registry returns empty set."""
        registry_entries = set()
        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        assert any("agents_source_code" in str(p) for p in reloaded.EXTERNAL_REPO_DIRS)


class TestAgentRepoDataClass:
    """Verify AgentRepo data class structure and properties."""

    def test_agent_repo_creation(self):
        """AgentRepo can be instantiated with required fields."""
        # Use the module's EXTERNAL_REPO_DIRS as SSoT — no hardcoded paths
        parent = next(iter(_module.EXTERNAL_REPO_DIRS))
        repo = _module.AgentRepo(
            name="langgraph",
            path=Path("/tmp/test/langgraph"),
            url="https://github.com/langchain-ai/langgraph",
            parent_dir=parent,
        )
        assert repo.name == "langgraph"
        assert repo.path == Path("/tmp/test/langgraph")
        assert repo.url == "https://github.com/langchain-ai/langgraph"
        assert repo.parent_dir == parent
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

        repos = _module.discover_repos(tmp_path, parent_dir=tmp_path)
        
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
        (tmp_path / _AGENTS_DIR).mkdir(parents=True)

        with patch("sys.argv", ["manage_agent_repos.py", "list"]):
            exit_code = _module.main()

        # Contract: exits without error when agents directory exists
        assert exit_code == 0

    @patch.object(_module, "detect_repo_root")
    def test_list_no_dirs_on_disk(self, mock_detect, tmp_path):
        """List exits 0 when no directories exist on disk."""
        mock_detect.return_value = tmp_path

        exit_code = _module.list_command()

        # Contract: exits 0 (informational, never fails)
        assert exit_code == 0

    @patch.object(_module, "detect_repo_root")
    def test_update_command_valid(self, mock_detect, tmp_path):
        """update command parses successfully."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
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
    def test_setup_creates_directory_if_missing(self, mock_detect, mock_clone, tmp_path):
        """Setup creates directory when it doesn't exist on disk."""
        mock_detect.return_value = tmp_path
        mock_clone.return_value = True

        exit_code = _module.setup_command(
            "https://github.com/test/repo",
        )

        # Contract: creates directory and exits 0 when single dir registered
        assert exit_code == 0
        # Contract: clones successfully
        mock_clone.assert_called_once()


class TestUpdateCommand:
    """Verify update command pulls all repos.
    
    Contract: Update pulls all repos and exits 0 if all succeed, 1 if any fail.
    """

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_all_success(self, mock_detect, mock_pull, tmp_path):
        """Update exits 0 when all repos pull successfully."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
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
    def test_update_no_dirs_registered(self, mock_detect, tmp_path):
        """Update exits 0 when no directories exist on disk."""
        mock_detect.return_value = tmp_path

        exit_code = _module.update_command(repo_names=[])

        # Contract: exits 0 when no dirs/repos found (not an error)
        assert exit_code == 0

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_no_repos_found(self, mock_detect, mock_pull, tmp_path):
        """Update exits 0 when agents directory exists but is empty."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _AGENTS_DIR
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
        agents_dir = tmp_path / _AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        exit_code = _module.update_command(repo_names=["nonexistent-repo"])

        # Contract: exits 1 when specified repos not found
        assert exit_code != 0


class TestMultiDirectorySupport:
    """Verify support for multiple external repo directories from registry.

    Contract: The script can operate on any directory registered in
    .vadocs/validation/external-repos.conf.json, not just agents_source_code.
    A new `register` command adds directories to the registry.
    """

    def _reload_module_with_registry(self, registry_entries, detect_root_return):
        """Reload manage_agent_repos module with mocked registry and detect_repo_root."""
        mod_name = "tools.scripts.manage_agent_repos"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        with patch("tools.scripts.paths.get_external_repo_paths", return_value=registry_entries):
            with patch("tools.scripts.git.detect_repo_root", return_value=detect_root_return):
                reloaded = importlib.import_module(mod_name)
                return reloaded

    def test_resolves_all_registry_directories(self, tmp_path):
        """Module discovers all directories from registry, not just one."""
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/llm_source_code",
        }
        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        # Contract: EXTERNAL_REPO_DIRS contains all registry entries
        assert len(reloaded.EXTERNAL_REPO_DIRS) == 2
        assert Path("ai_agents/agents_source_code") in reloaded.EXTERNAL_REPO_DIRS
        assert Path("research/llm_source_code") in reloaded.EXTERNAL_REPO_DIRS

    def test_fallback_when_registry_empty(self, tmp_path):
        """Fallback is used when registry has no entries."""
        registry_entries = set()
        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        # Contract: fallback path is used
        assert len(reloaded.EXTERNAL_REPO_DIRS) >= 1

    def test_list_command_discovers_all_directories(self, tmp_path):
        """list command shows repos from all registered directories."""
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/other_agents",
        }

        # Create both directories with repos
        agents1 = tmp_path / "ai_agents" / "agents_source_code"
        agents2 = tmp_path / "research" / "other_agents"
        agents1.mkdir(parents=True)
        agents2.mkdir(parents=True)
        (agents1 / "repo1" / ".git").mkdir(parents=True)
        (agents2 / "repo2" / ".git").mkdir(parents=True)

        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        # Reload list_command to use new module
        import io
        import sys
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        exit_code = reloaded.list_command()

        sys.stdout = old_stdout
        output = captured.getvalue()

        # Contract: exits 0 and shows repos from all directories
        assert exit_code == 0
        assert "repo1" in output
        assert "repo2" in output

    def test_setup_requires_dir_option(self, tmp_path):
        """setup command requires --dir when multiple directories registered."""
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/other_agents",
        }

        agents1 = tmp_path / "ai_agents" / "agents_source_code"
        agents2 = tmp_path / "research" / "other_agents"
        agents1.mkdir(parents=True)
        agents2.mkdir(parents=True)

        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        with patch.object(reloaded, "clone_repo", return_value=True):
            # Contract: exits 1 when multiple dirs exist and --dir not specified
            exit_code = reloaded.setup_command(
                "https://github.com/test/repo",
            )
            assert exit_code != 0

    def test_setup_with_specific_dir(self, tmp_path):
        """setup command works when --dir specifies target directory."""
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/other_agents",
        }

        agents1 = tmp_path / "ai_agents" / "agents_source_code"
        agents2 = tmp_path / "research" / "other_agents"
        agents1.mkdir(parents=True)
        agents2.mkdir(parents=True)

        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        with patch.object(reloaded, "clone_repo", return_value=True):
            exit_code = reloaded.setup_command(
                "https://github.com/test/repo",
                target_dir_name="ai_agents/agents_source_code",
            )
            assert exit_code == 0

    def test_update_all_directories(self, tmp_path):
        """update command pulls from all registered directories."""
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/other_agents",
        }

        agents1 = tmp_path / "ai_agents" / "agents_source_code"
        agents2 = tmp_path / "research" / "other_agents"
        agents1.mkdir(parents=True)
        agents2.mkdir(parents=True)
        (agents1 / "repo1" / ".git").mkdir(parents=True)
        (agents2 / "repo2" / ".git").mkdir(parents=True)

        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        with patch.object(reloaded, "pull_repo", return_value=(True, "Updated")):
            exit_code = reloaded.update_command(repo_names=[])
            # Contract: exits 0 when all repos update across all directories
            assert exit_code == 0


class TestRegisterCommand:
    """Verify register command adds directories to the registry.

    Contract: register command updates the external-repos.conf.json
    and updates exclusion configs atomically.
    """

    def test_register_adds_to_registry(self, tmp_path):
        """register command adds new directory to the registry."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text('{"entries": []}')

        # Import the register function
        from tools.scripts.manage_agent_repos import register_command

        exit_code = register_command(
            "research/new_agents",
            "New agent research directory",
            config_path=registry_file,
        )

        assert exit_code == 0

        # Verify the entry was added
        import json
        with open(registry_file) as f:
            data = json.load(f)
        assert len(data["entries"]) == 1
        assert data["entries"][0]["path"] == "research/new_agents"

    def test_register_rejects_duplicate(self, tmp_path):
        """register command fails if directory already in registry."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(
            '{"entries": [{"path": "ai_agents/agents_source_code", "description": "test"}]}'
        )

        from tools.scripts.manage_agent_repos import register_command

        exit_code = register_command(
            "ai_agents/agents_source_code",
            "Duplicate entry",
            config_path=registry_file,
        )

        # Contract: exits 1 for duplicate
        assert exit_code != 0


class TestRelocateCommand:
    """Verify relocate command atomically moves directory and updates registry.

    Contract: relocate moves the directory on disk AND updates all consumers
    listed in the registry. This is the safe relocation mechanism from ADR-26046.
    Consumer list is read from the live config — no duplication.
    """

    # Template paths for test scenarios — derived from common relocation pattern.
    _OLD_PATH = "old_dir/agents_source_code"
    _NEW_PATH = "new_dir/agents_source_code"

    # Read consumers from the live SSoT config, not from a test constant.
    _LIVE_CONFIG = Path(__file__).resolve().parents[2] / ".vadocs" / "validation" / "external-repos.conf.json"
    with open(_LIVE_CONFIG) as _f:
        _config_data = json.load(_f)
    _CONSUMERS = _config_data["entries"][0].get("consumers", [])
    _product_type = _config_data["entries"][0].get("product_type", "")
    del _config_data

    def _build_registry(self, tmp_path, entries):
        """Build a temporary registry file.

        Args:
            tmp_path: pytest tmp_path fixture.
            entries: list of dicts with at least "path" and "description" keys.

        Returns:
            Path to the registry file.
        """
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        with open(registry_file, "w") as f:
            json.dump({"entries": entries}, f)
        return registry_file

    def _setup_consumer_files(self, tmp_path, old_path):
        """Create mock consumer files with exclusion entries for old_path.

        Consumer list comes from the live .vadocs/config (SSoT).

        Args:
            tmp_path: pytest tmp_path fixture.
            old_path: path string to put in exclusion entries.

        Returns:
            Dict mapping relative consumer path → created file Path.
        """
        created = {}
        for rel_path in self._CONSUMERS:
            f = tmp_path / rel_path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"# placeholder\n{old_path}\n{old_path}/\n")
            created[rel_path] = f
        return created

    def test_relocate_moves_directory_and_updates_registry(self, tmp_path):
        """relocate moves dir on disk and updates all consumers (registry, .gitignore, myst.yml)."""
        old_path = self._OLD_PATH
        new_path = self._NEW_PATH

        # Setup: old path exists with a repo + consumer files from SSoT
        old_dir = tmp_path / old_path
        old_dir.mkdir(parents=True)
        (old_dir / "aider" / ".git").mkdir(parents=True)

        registry_file = self._build_registry(tmp_path, [
            {"path": old_path, "description": "Old dir",
             "product_type": self._product_type,
             "consumers": self._CONSUMERS},
        ])
        consumer_files = self._setup_consumer_files(tmp_path, old_path)

        from tools.scripts.manage_agent_repos import relocate_command

        exit_code = relocate_command(
            old_path, new_path,
            config_path=registry_file,
            repo_root=tmp_path,
        )

        assert exit_code == 0

        # Verify directory moved
        assert not old_dir.exists()
        new_dir = tmp_path / new_path
        assert new_dir.exists()
        assert (new_dir / "aider" / ".git").exists()

        # Verify registry updated
        with open(registry_file) as f:
            data = json.load(f)
        paths = {e["path"] for e in data["entries"]}
        assert old_path not in paths
        assert new_path in paths

        # Verify all consumer files updated
        for rel_path, f_path in consumer_files.items():
            content = f_path.read_text()
            assert old_path not in content, f"{rel_path} still contains old path"
            assert new_path in content, f"{rel_path} missing new path"

    def test_relocate_rejects_missing_old_path(self, tmp_path):
        """relocate exits with error when old path doesn't exist in registry."""
        registry_file = self._build_registry(tmp_path, [])

        from tools.scripts.manage_agent_repos import relocate_command

        exit_code = relocate_command(
            "nonexistent/old/path", self._NEW_PATH,
            config_path=registry_file,
            repo_root=tmp_path,
        )

        assert exit_code != 0

    def test_relocate_rejects_existing_new_path(self, tmp_path):
        """relocate exits with error when new path is already registered."""
        old_path = self._OLD_PATH
        existing_path = self._NEW_PATH

        registry_file = self._build_registry(tmp_path, [
            {"path": old_path, "description": "Old"},
            {"path": existing_path, "description": "Already exists"},
        ])

        from tools.scripts.manage_agent_repos import relocate_command

        exit_code = relocate_command(
            old_path, existing_path,
            config_path=registry_file,
            repo_root=tmp_path,
        )

        assert exit_code != 0

    def test_relocate_updates_registry_when_dir_already_moved_manually(self, tmp_path):
        """relocate fixes registry when directory was already moved by git mv.

        This covers the scenario: user did `git mv` manually, registry is stale.
        """
        old_path = self._OLD_PATH
        new_path = self._NEW_PATH

        registry_file = self._build_registry(tmp_path, [
            {"path": old_path, "description": "Old dir", "product_type": "ai_coding_agents"},
        ])

        # Don't create the old directory on disk (already moved manually)

        from tools.scripts.manage_agent_repos import relocate_command

        exit_code = relocate_command(
            old_path, new_path,
            config_path=registry_file,
            repo_root=tmp_path,
        )

        # Contract: exits 0 — registry updated, directory already moved
        assert exit_code == 0

        # Verify registry updated
        import json
        with open(registry_file) as f:
            data = json.load(f)
        paths = {e["path"] for e in data["entries"]}
        assert old_path not in paths
        assert new_path in paths
