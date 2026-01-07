import sys
import pytest
from unittest.mock import patch, MagicMock
from tools.scripts.core.cli import main

# We mock the hook functions to avoid running actual Jupytext/Link-check logic
HOOKS_PATH = "tools.scripts.hooks"

@pytest.fixture
def mock_hooks():
    """Context manager for patching all hook entry points."""
    with patch(f"{HOOKS_PATH}.jupytext_sync.run") as sync, \
         patch(f"{HOOKS_PATH}.jupytext_verify_pair.run") as verify, \
         patch(f"{HOOKS_PATH}.check_broken_links.run") as links:
        yield {
            "sync": sync,
            "verify": verify,
            "links": links
        }

## --- Command Routing Tests ---

def test_cli_routes_sync_correctly(mock_hooks):
    """Ensure 'sync' without flags calls the sync hook."""
    with patch.object(sys, 'argv', ["cli.py", "sync"]):
        mock_hooks["sync"].return_value = True
        main()
        mock_hooks["sync"].assert_called_once()
        mock_hooks["verify"].assert_not_called()

def test_cli_routes_check_flag_to_verify(mock_hooks):
    """Ensure 'sync --check' switches routing to the verification hook."""
    with patch.object(sys, 'argv', ["cli.py", "sync", "--check"]):
        mock_hooks["verify"].return_value = True
        main()
        mock_hooks["verify"].assert_called_once()
        mock_hooks["sync"].assert_not_called()

def test_cli_routes_links_command(mock_hooks):
    """Ensure 'links' command triggers the broken links hook."""
    with patch.object(sys, 'argv', ["cli.py", "links"]):
        mock_hooks["links"].return_value = True
        main()
        mock_hooks["links"].assert_called_once()

## --- Defensive & Exit Code Tests ---

def test_cli_exits_fail_on_hook_failure(mock_hooks):
    """Programmatic resilience: CLI must exit 1 if a hook returns False."""
    with patch.object(sys, 'argv', ["cli.py", "sync"]):
        mock_hooks["sync"].return_value = False # Simulate failure
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

@pytest.mark.parametrize("invalid_args", [
    (["cli.py", "invalid_cmd"]),
    (["cli.py", "sync", "--unknown-flag"]),
])
def test_cli_invalid_arguments(invalid_args):
    """Verify argparse handles undefined inputs gracefully."""
    with patch.object(sys, 'argv', invalid_args):
        with pytest.raises(SystemExit):
            main()

## --- Path Handling ---

def test_cli_defaults_to_root_if_no_paths(mock_hooks):
    """Verify the 'brain' defaults to current directory if no paths provided."""
    with patch.object(sys, 'argv', ["cli.py", "sync"]):
        mock_hooks["sync"].return_value = True
        main()
        # Check if the first argument passed to the hook was default '.' or repo root
        args, _ = mock_hooks["sync"].call_args
        assert "." in args or len(args) == 0
