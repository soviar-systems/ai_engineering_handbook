"""
Tests for manage_external_repos.py script.

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

import tools.scripts.manage_external_repos as _module

# Fixed test directory path — not derived from live registry to avoid brittleness.
_TEST_AGENTS_DIR = Path("research/test_repos")

# Shared class-level patch for tests that create mock repo directories.
# Applied as @_PATCHED_DIRS on test classes to decorate all methods.
# So tests don't depend on the live registry having 1 vs N entries.
_PATCHED_DIRS = patch.object(_module, "EXTERNAL_REPO_DIRS", {_TEST_AGENTS_DIR})


class TestAgentsSourceCodeDirResolution:
    """Verify EXTERNAL_REPO_DIRS resolves from the registry.

    Contract: The module reads get_external_repo_paths at import time.
    When registry has entries, all are used.
    When registry is empty/missing, the fallback default is used.

    Because detect_repo_root and get_external_repo_paths are called at
    module import time, we must patch them before the module loads.
    """

    def _reload_module_with_registry(self, registry_entries, detect_root_return):
        """Reload manage_external_repos module with mocked registry and detect_repo_root."""
        mod_name = "tools.scripts.manage_external_repos"
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

        # Fallback uses the default path
        assert any("research" in str(p) for p in reloaded.EXTERNAL_REPO_DIRS)

    def test_fallback_when_registry_missing(self, tmp_path):
        """EXTERNAL_REPO_DIRS uses fallback when registry returns empty set."""
        registry_entries = set()
        reloaded = self._reload_module_with_registry(registry_entries, tmp_path)

        assert any("research" in str(p) for p in reloaded.EXTERNAL_REPO_DIRS)


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


@_PATCHED_DIRS
class TestCLIArgumentParsing:
    """Verify CLI argument parsing and dispatch.

    Contract: CLI exits with appropriate codes for valid/invalid arguments.
    """

    def test_setup_command_requires_url(self, capsys):
        """setup command fails when URL is missing."""
        with patch("sys.argv", ["manage_external_repos.py", "setup"]):
            with pytest.raises(SystemExit):
                _module.main()

    @patch.object(_module, "detect_repo_root")
    def test_list_command_valid(self, mock_detect, tmp_path):
        """list command parses successfully."""
        mock_detect.return_value = tmp_path
        (tmp_path / _TEST_AGENTS_DIR).mkdir(parents=True)

        with patch("sys.argv", ["manage_external_repos.py", "list"]):
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        with patch("sys.argv", ["manage_external_repos.py", "update"]):
            exit_code = _module.main()

        # Contract: exits 0 when no repos found (not an error condition)
        assert exit_code == 0

    def test_invalid_command(self, capsys):
        """Invalid command exits with error."""
        with patch("sys.argv", ["manage_external_repos.py", "invalid_cmd"]):
            with pytest.raises(SystemExit):
                _module.main()


@_PATCHED_DIRS
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
        agents_dir = tmp_path / "research/test_repos"
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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


@_PATCHED_DIRS
class TestUpdateCommand:
    """Verify update command pulls all repos.

    Contract: Update pulls all repos and exits 0 if all succeed, 1 if any fail.
    """

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_all_success(self, mock_detect, mock_pull, tmp_path):
        """Update exits 0 when all repos pull successfully."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        agents_dir = tmp_path / _TEST_AGENTS_DIR
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
        """Reload manage_external_repos module with mocked registry and detect_repo_root."""
        mod_name = "tools.scripts.manage_external_repos"
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

    def test_register_adds_full_entry(self, tmp_path):
        """register adds entry with managed_by and consumers (ADR-26046).

        Contract: consumers and managed_by come from config top-level fields,
        not from any hardcoded value in the script.
        """
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({
            "default_consumers": [".gitignore"],
            "managed_by": "tools/scripts/manage_external_repos.py",
            "entries": []
        }))

        from tools.scripts.manage_external_repos import register_command

        exit_code = register_command(
            "research/new_agents",
            "New agent research directory",
            config_path=registry_file,
        )

        assert exit_code == 0

        with open(registry_file) as f:
            data = json.load(f)
        entry = data["entries"][0]
        assert entry["path"] == "research/new_agents"
        assert entry["description"] == "New agent research directory"
        # Required fields for registry contract (ADR-26046)
        assert "managed_by" in entry
        assert isinstance(entry["managed_by"], str)
        assert "consumers" in entry
        assert isinstance(entry["consumers"], list)
        # Fields come from config top-level, not hardcoded
        assert entry["consumers"] == [".gitignore"]
        assert entry["managed_by"] == "tools/scripts/manage_external_repos.py"

    def test_register_uses_config_consumers(self, tmp_path):
        """register copies consumers and managed_by from config.

        Contract: entry fields match config top-level fields, not script constants.
        Uses arbitrary values to prove the data flows from config → entry.
        """
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({
            "default_consumers": [".arbitrary-consumer-1", ".arbitrary-consumer-2"],
            "managed_by": "tools/scripts/arbitrary-script.py",
            "entries": []
        }))

        from tools.scripts.manage_external_repos import register_command

        exit_code = register_command(
            "research/new_agents",
            "New agent research directory",
            config_path=registry_file,
        )

        assert exit_code == 0

        with open(registry_file) as f:
            data = json.load(f)
        entry = data["entries"][0]
        # Contract: values match config, proving they were read — not hardcoded
        assert entry["consumers"] == [".arbitrary-consumer-1", ".arbitrary-consumer-2"]
        assert entry["managed_by"] == "tools/scripts/arbitrary-script.py"

    def test_register_handles_missing_defaults(self, tmp_path):
        """register works when config has no default_consumers or managed_by.

        Contract: falls back to empty values — no crash, no hardcoded defaults.
        """
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({"entries": []}))

        from tools.scripts.manage_external_repos import register_command

        exit_code = register_command(
            "research/new_agents",
            "New agent research directory",
            config_path=registry_file,
        )

        assert exit_code == 0

        with open(registry_file) as f:
            data = json.load(f)
        entry = data["entries"][0]
        # Contract: empty values when config lacks top-level fields
        assert entry["consumers"] == []
        assert entry["managed_by"] == ""

    def _make_registry_file(self, tmp_path):
        """Build a minimal registry file for register tests.

        Returns (registry_file, gitignore) where gitignore is created
        from the config's default_consumers.
        """
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        config = {
            "default_consumers": [".gitignore"],
            "managed_by": "tools/scripts/test.py",
            "entries": [],
        }
        registry_file.write_text(json.dumps(config))

        # Create consumer files from config
        for consumer_name in config["default_consumers"]:
            (tmp_path / consumer_name).write_text("# existing\n")

        return registry_file, tmp_path / ".gitignore"

    def test_register_updates_consumer_files(self, tmp_path):
        """register adds exclusion path to .gitignore."""
        registry_file, gitignore = self._make_registry_file(tmp_path)

        with patch("tools.scripts.manage_external_repos.detect_repo_root", return_value=tmp_path):
            from tools.scripts.manage_external_repos import register_command

            exit_code = register_command(
                "research/new_agents",
                "New agent research directory",
                config_path=registry_file,
            )

        assert exit_code == 0
        # Contract: exclusion added to the consumer from config
        assert "research/new_agents/" in gitignore.read_text()

    def test_register_skips_existing_exclusion(self, tmp_path):
        """register does not duplicate exclusion paths already in consumer files."""
        registry_file, gitignore = self._make_registry_file(tmp_path)
        gitignore.write_text("# existing\nresearch/new_agents/\n")

        with patch("tools.scripts.manage_external_repos.detect_repo_root", return_value=tmp_path):
            from tools.scripts.manage_external_repos import register_command

            exit_code = register_command(
                "research/new_agents",
                "Already excluded",
                config_path=registry_file,
            )

        assert exit_code == 0
        # Contract: no duplicate exclusion line
        assert gitignore.read_text().count("research/new_agents") == 1

    def test_register_rejects_duplicate(self, tmp_path):
        """register command fails if directory already in registry."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(
            '{"entries": [{"path": "ai_agents/agents_source_code", "description": "test"}]}'
        )

        from tools.scripts.manage_external_repos import register_command

        exit_code = register_command(
            "ai_agents/agents_source_code",
            "Duplicate entry",
            config_path=registry_file,
        )

        # Contract: exits 1 for duplicate
        assert exit_code != 0


class TestUnregisterCommand:
    """Verify unregister command removes directories from the registry.

    Contract: unregister removes an entry from external-repos.conf.json.
    Returns 1 if path not found.
    """

    def test_unregister_removes_entry(self, tmp_path):
        """unregister removes a path from the registry."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({
            "entries": [
                {"path": "research/alpha", "description": "Alpha",
                 "product_type": "external_product",
                 "managed_by": "tools/scripts/manage_external_repos.py",
                 "consumers": [".gitignore", "myst.yml"]},
                {"path": "research/beta", "description": "Beta",
                 "product_type": "external_product",
                 "managed_by": "tools/scripts/manage_external_repos.py",
                 "consumers": [".gitignore", "myst.yml"]},
            ]
        }))

        from tools.scripts.manage_external_repos import unregister_command

        exit_code = unregister_command("research/alpha", config_path=registry_file)

        assert exit_code == 0
        with open(registry_file) as f:
            data = json.load(f)
        assert len(data["entries"]) == 1
        assert data["entries"][0]["path"] == "research/beta"

    def test_unregister_not_found(self, tmp_path):
        """unregister returns 1 if path is not in registry."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({
            "entries": [
                {"path": "research/alpha", "description": "Alpha",
                 "product_type": "external_product",
                 "managed_by": "tools/scripts/manage_external_repos.py",
                 "consumers": [".gitignore", "myst.yml"]},
            ]
        }))

        from tools.scripts.manage_external_repos import unregister_command

        exit_code = unregister_command("research/nonexistent", config_path=registry_file)

        assert exit_code != 0

    def test_unregister_removes_from_consumer_files(self, tmp_path):
        """unregister removes exclusion path from all consumer files in the entry."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({
            "entries": [
                {"path": "research/alpha", "description": "Alpha",
                 "product_type": "external_product",
                 "managed_by": "tools/scripts/manage_external_repos.py",
                 "consumers": [".gitignore", "myst.yml"]},
            ]
        }))

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# exclusions\nresearch/alpha/\nsome_other/\n")

        myst_yml = tmp_path / "myst.yml"
        myst_yml.write_text('project:\n  exclude:\n    - "research/alpha/*"\n    - "other/*"\n')

        with patch("tools.scripts.manage_external_repos.detect_repo_root", return_value=tmp_path):
            from tools.scripts.manage_external_repos import unregister_command

            exit_code = unregister_command("research/alpha", config_path=registry_file)

        assert exit_code == 0
        # Contract: path removed from consumer files
        assert "research/alpha" not in gitignore.read_text()
        assert "research/alpha" not in myst_yml.read_text()
        # Contract: other lines preserved
        assert "some_other" in gitignore.read_text()
        assert "other/*" in myst_yml.read_text()


class TestListRegisteredDirsCommand:
    """Verify list --dirs shows registered directories from the registry.

    Contract: list --dirs outputs paths from external-repos.conf.json entries.
    Returns 0 (informational command).
    """

    def test_list_dirs_outputs_registered_paths(self, tmp_path, capsys):
        """list --dirs shows all registered directories from config."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(json.dumps({
            "entries": [
                {"path": "research/alpha", "description": "Alpha repos",
                 "product_type": "ai_coding_agents",
                 "managed_by": "tools/scripts/manage_external_repos.py",
                 "consumers": [".gitignore", "myst.yml"]},
                {"path": "research/beta", "description": "Beta repos",
                 "product_type": "ai_infrastructure",
                 "managed_by": "tools/scripts/manage_external_repos.py",
                 "consumers": [".gitignore", "myst.yml"]},
            ]
        }))

        with patch.object(_module, 'EXTERNAL_REPO_DIRS',
                          {Path("research/alpha"), Path("research/beta")}):
            with patch.object(_module, '_EXTERNAL_REPOS_CONFIG', str(registry_file)):
                exit_code = _module.list_command(dirs_only=True)

        assert exit_code == 0
        captured = capsys.readouterr()
        # Contract: paths from the registry appear in output
        assert "research/alpha" in captured.out
        assert "research/beta" in captured.out


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

        from tools.scripts.manage_external_repos import relocate_command

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

        from tools.scripts.manage_external_repos import relocate_command

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

        from tools.scripts.manage_external_repos import relocate_command

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

        from tools.scripts.manage_external_repos import relocate_command

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


@_PATCHED_DIRS
class TestUpdateCommandVerboseOutput:
    """Verify verbose output in update command (ADR verbose enhancement).

    Contract: Update command shows progress, directory discovery, and summary.
    """

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_directory_discovery(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows which directories are being scanned."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Already up to date.")

        _module.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows directory discovery phase
        assert "Discovering" in captured.out or str(_TEST_AGENTS_DIR) in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_sequential_mode(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows sequential mode indicator."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Updated")

        _module.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows mode indicator
        assert "Sequential" in captured.out or "Updating" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_parallel_mode(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows parallel mode indicator."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Updated")

        _module.update_command(repo_names=[], parallel=True)

        captured = capsys.readouterr()
        # Contract: shows parallel mode and thread pool info
        assert "Parallel" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_progress_counter(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows progress counter in sequential mode."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo2 = agents_dir / "repo2"
        repo1.mkdir()
        repo2.mkdir()
        (repo1 / ".git").mkdir()
        (repo2 / ".git").mkdir()

        mock_pull.return_value = (True, "Already up to date.")

        _module.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows progress like [1/2], [2/2]
        assert "1/2" in captured.out and "2/2" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_summary_on_success(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows success summary."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Already up to date.")

        _module.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows success summary
        assert "All repositories updated successfully" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_summary_on_failure(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows failure summary."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo2 = agents_dir / "repo2"
        repo1.mkdir()
        repo2.mkdir()
        (repo1 / ".git").mkdir()
        (repo2 / ".git").mkdir()

        mock_pull.side_effect = [(True, "Updated"), (False, "error: conflict")]

        _module.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows failure summary
        assert "Some repositories failed" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_parallel_shows_thread_pool(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update parallel mode shows thread pool info."""
        mock_detect.return_value = tmp_path
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Updated")

        _module.update_command(repo_names=[], parallel=True)

        captured = capsys.readouterr()
        # Contract: shows thread pool info
        assert "thread pool" in captured.out or "workers" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "get_repo_status")
    @patch.object(_module, "detect_repo_root")
    def test_update_parallel_exception_handling(self, mock_detect, mock_status, mock_pull, tmp_path, capsys):
        """Update parallel mode handles exceptions gracefully."""
        mock_detect.return_value = tmp_path
        mock_status.return_value = ("main", None, None)
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        # Simulate exception
        mock_pull.side_effect = Exception("Network error")

        exit_code = _module.update_command(repo_names=[], parallel=True)

        captured = capsys.readouterr()
        # Contract: exits 1 and shows exception
        assert exit_code != 0
        assert "Unexpected exception" in captured.out or "Error" in captured.out


@_PATCHED_DIRS
class TestUpdateCommandEdgeCases:
    """Test edge cases in update command for full coverage."""

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "get_repo_status")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_branch_info(self, mock_detect, mock_status, mock_pull, tmp_path, capsys):
        """Update shows branch information."""
        mock_detect.return_value = tmp_path
        mock_status.return_value = ("main", "origin", "2024-01-01")
        agents_dir = tmp_path / _TEST_AGENTS_DIR
        agents_dir.mkdir(parents=True)

        repo1 = agents_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        mock_pull.return_value = (True, "Already up to date.")

        _module.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows branch info
        assert "(main)" in captured.out

    @patch.object(_module, "pull_repo")
    @patch.object(_module, "detect_repo_root")
    def test_update_shows_repo_count_per_directory(self, mock_detect, mock_pull, tmp_path, capsys):
        """Update shows how many repos found per directory."""
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

        # Reload module with multi-directory registry
        mod_name = "tools.scripts.manage_external_repos"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        with patch("tools.scripts.paths.get_external_repo_paths", return_value=registry_entries):
            with patch("tools.scripts.git.detect_repo_root", return_value=tmp_path):
                reloaded = importlib.import_module(mod_name)

        with patch.object(reloaded, "pull_repo", return_value=(True, "Updated")):
            reloaded.update_command(repo_names=[])

        captured = capsys.readouterr()
        # Contract: shows repo count per directory
        assert "Found" in captured.out and "repo" in captured.out.lower()


class TestRegisterCommandEdgeCases:
    """Test edge cases in register command for full coverage."""

    def test_register_creates_parent_directory(self, tmp_path):
        """register command creates parent directory if it doesn't exist."""
        registry_file = tmp_path / "nested" / ".vadocs" / "validation" / "external-repos.conf.json"

        from tools.scripts.manage_external_repos import register_command

        exit_code = register_command(
            "research/new_agents",
            "New agent research directory",
            config_path=registry_file,
        )

        assert exit_code == 0
        assert registry_file.exists()

    def test_register_creates_config_from_scratch(self, tmp_path):
        """register command creates config file when it doesn't exist."""
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"

        from tools.scripts.manage_external_repos import register_command

        exit_code = register_command(
            "research/new_agents",
            "New agent research directory",
            config_path=registry_file,
        )

        assert exit_code == 0
        assert registry_file.exists()

        with open(registry_file) as f:
            data = json.load(f)
        assert len(data["entries"]) == 1
        entry = data["entries"][0]
        assert entry["path"] == "research/new_agents"
        assert entry["description"] == "New agent research directory"
        assert entry["product_type"] == "external_product"
        # Contract: no consumers or managed_by when config has no defaults
        assert entry["consumers"] == []
        assert entry["managed_by"] == ""


class TestResolveTargetDirEdgeCases:
    """Test _resolve_target_dir edge cases for full coverage."""

    def test_resolve_target_dir_not_in_registry(self, tmp_path, capsys):
        """_resolve_target_dir returns None when dir not in registry."""
        # Need multiple directories to trigger the "dir not in registry" check
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/other_agents",
        }

        agents1 = tmp_path / "ai_agents" / "agents_source_code"
        agents2 = tmp_path / "research" / "other_agents"
        agents1.mkdir(parents=True)
        agents2.mkdir(parents=True)

        mod_name = "tools.scripts.manage_external_repos"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        with patch("tools.scripts.paths.get_external_repo_paths", return_value=registry_entries):
            with patch("tools.scripts.git.detect_repo_root", return_value=tmp_path):
                with patch("tools.scripts.git.clone_repo", return_value=True):
                    reloaded = importlib.import_module(mod_name)

        exit_code = reloaded.setup_command(
            "https://github.com/test/repo",
            target_dir_name="nonexistent/dir",
        )

        assert exit_code != 0
        captured = capsys.readouterr()
        assert "not in registry" in captured.out

    def test_resolve_target_dir_does_not_exist(self, tmp_path, capsys):
        """_resolve_target_dir returns None when directory doesn't exist on disk."""
        registry_entries = {
            "ai_agents/agents_source_code",
            "research/other_agents",
        }

        agents1 = tmp_path / "ai_agents" / "agents_source_code"
        agents2 = tmp_path / "research" / "other_agents"
        agents1.mkdir(parents=True)
        # Don't create agents2

        mod_name = "tools.scripts.manage_external_repos"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        with patch("tools.scripts.paths.get_external_repo_paths", return_value=registry_entries):
            with patch("tools.scripts.git.detect_repo_root", return_value=tmp_path):
                with patch("tools.scripts.git.clone_repo", return_value=True):
                    reloaded = importlib.import_module(mod_name)

        exit_code = reloaded.setup_command(
            "https://github.com/test/repo",
            target_dir_name="research/other_agents",
        )

        # Contract: exits 1 when directory doesn't exist
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "does not exist" in captured.out


class TestRelocateCommandEdgeCases:
    """Test relocate command edge cases for full coverage."""

    def test_relocate_rejects_missing_config(self, tmp_path):
        """relocate exits with error when config file doesn't exist."""
        from tools.scripts.manage_external_repos import relocate_command

        exit_code = relocate_command(
            "old/path", "new/path",
            config_path=tmp_path / "nonexistent" / "config.json",
            repo_root=tmp_path,
        )

        assert exit_code != 0

    def test_relocate_skips_missing_consumer(self, tmp_path, capsys):
        """relocate skips consumer files that don't exist."""
        old_path = "old_dir/agents_source_code"
        new_path = "new_dir/agents_source_code"

        # Build registry with consumer that doesn't exist
        registry_file = tmp_path / ".vadocs" / "validation" / "external-repos.conf.json"
        registry_file.parent.mkdir(parents=True)
        with open(registry_file, "w") as f:
            json.dump({
                "entries": [{
                    "path": old_path,
                    "description": "Old dir",
                    "product_type": "ai_coding_agents",
                    "consumers": ["nonexistent_file.txt"],
                }]
            }, f)

        # Create old directory
        old_dir = tmp_path / old_path
        old_dir.mkdir(parents=True)

        from tools.scripts.manage_external_repos import relocate_command

        exit_code = relocate_command(
            old_path, new_path,
            config_path=registry_file,
            repo_root=tmp_path,
        )

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Skipped" in captured.out
