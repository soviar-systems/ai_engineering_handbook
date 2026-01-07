import sys
from unittest.mock import ANY, patch

import pytest

from tools.scripts.core.cli import main


@pytest.fixture
def mock_hooks():
    """Patch hooks at their import points in tools.scripts.core.cli."""
    with (
        patch("tools.scripts.core.cli.jupytext_sync.run") as sync,
        patch("tools.scripts.core.cli.jupytext_verify_pair.run") as verify,
        patch("tools.scripts.core.cli.check_broken_links.run", create=True) as links,
    ):
        yield {"sync": sync, "verify": verify, "links": links}


def test_cli_routes_sync_correctly(mock_hooks):
    """Ensure 'jupytext-sync' without flags calls the sync hook."""
    with patch.object(sys, "argv", ["cli.py", "jupytext-sync"]):  #
        mock_hooks["sync"].return_value = True
        main()
        mock_hooks["sync"].assert_called_once()


def test_cli_routes_check_flag_to_verify(mock_hooks):
    """Ensure 'jupytext-sync --test' triggers sync hook with test_only=True."""
    with patch.object(sys, "argv", ["cli.py", "jupytext-sync", "--test"]):
        mock_hooks["sync"].return_value = True
        main()
        # Use ANY to ignore the 'paths' positional argument while verifying 'test_only'
        mock_hooks["sync"].assert_called_once_with(
            ANY, test_only=True
        )  # Fixed citation


def test_cli_routes_links_command(mock_hooks):
    """Ensure 'check-broken-links' command triggers the correct hook."""
    with patch.object(sys, "argv", ["cli.py", "check-broken-links"]):  #
        mock_hooks["links"].return_value = True
        main()
        mock_hooks["links"].assert_called_once()


def test_cli_exits_fail_on_hook_failure(mock_hooks):
    """CLI must exit with code 1 if a hook returns False."""
    with patch.object(sys, "argv", ["cli.py", "jupytext-sync"]):
        mock_hooks["sync"].return_value = False
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
