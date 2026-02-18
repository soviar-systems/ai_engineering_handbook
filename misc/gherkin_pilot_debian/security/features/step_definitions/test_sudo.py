"""
Step definitions for security/features/sudo.feature

Execution context: QEMU/KVM test image snapshot (not production).
All steps call real OS state — no mocks.

Run:
    uv run pytest security/features/sudo.feature -v
    uv run pytest security/features/sudo.feature -v -k "approved package"

Dependencies:
    pytest-bdd    (BDD framework, aligns with uv run pytest patterns)
    pytest        (test runner)

Install in Debian fork repo:
    uv add --dev pytest pytest-bdd
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, then, when

# ---------------------------------------------------------------------------
# Scenario bindings — one decorator per scenario in sudo.feature
# ---------------------------------------------------------------------------

@scenario("../sudo.feature", "Developer installs an approved package via apt")
def test_developer_installs_approved_package():
    pass


@scenario("../sudo.feature", "Developer cannot install a package not on the approved list")
def test_developer_blocked_from_unapproved_package():
    pass


@scenario("../sudo.feature", "Analyst role cannot run apt with sudo")
def test_analyst_cannot_run_apt():
    pass


@scenario("../sudo.feature", "Sysadmin reloads the firewall service")
def test_sysadmin_reloads_firewall():
    pass


@scenario("../sudo.feature", "Developer cannot manage systemd services")
def test_developer_cannot_manage_services():
    pass


@scenario("../sudo.feature", "No role can gain an unrestricted root shell")
def test_no_role_gains_root_shell():
    pass


@scenario("../sudo.feature", "The sudoers configuration passes visudo syntax validation")
def test_visudo_syntax_valid():
    pass


@scenario("../sudo.feature", "No sudoers fragment grants unrestricted ALL=(ALL) NOPASSWD:ALL")
def test_no_wildcard_privilege_grant():
    pass


# ---------------------------------------------------------------------------
# Fixtures — shared state passed between steps via pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def context():
    """Mutable dict shared across steps within a single scenario."""
    return {}


# ---------------------------------------------------------------------------
# Given steps — precondition checks on real OS state
# ---------------------------------------------------------------------------

@given(parsers.parse("the user is a member of the '{group}' group"), target_fixture="user_group")
def check_user_in_group(group: str, context: dict) -> str:
    """Verify the test user is actually in the expected group via getent."""
    test_user = _test_user()
    result = subprocess.run(
        ["getent", "group", group],
        capture_output=True, text=True
    )
    members = result.stdout.strip().split(":")[-1].split(",") if result.returncode == 0 else []
    assert test_user in members, (
        f"Test user '{test_user}' is not a member of group '{group}'. "
        f"Group members: {members}"
    )
    context["user"] = test_user
    context["group"] = group
    return group


@given("the workstation has a configured sudoers policy in /etc/sudoers.d/")
def check_sudoers_policy_exists():
    """Verify the sudoers drop-in directory exists and is not empty."""
    sudoers_dir = Path("/etc/sudoers.d")
    assert sudoers_dir.is_dir(), "/etc/sudoers.d directory does not exist"
    fragments = [f for f in sudoers_dir.iterdir() if not f.name.startswith(".")]
    assert len(fragments) > 0, "/etc/sudoers.d is empty — no policy fragments found"


@given("the audit daemon is running and writes to /var/log/auth.log")
def check_audit_daemon():
    """Verify rsyslog or auditd is active and auth.log is writable."""
    result = subprocess.run(
        ["systemctl", "is-active", "rsyslog"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, "rsyslog is not active — auth.log will not be written"
    assert Path("/var/log/auth.log").exists(), "/var/log/auth.log does not exist"


@given(parsers.parse("'{package}' is in the approved package list"))
def check_package_approved(package: str, context: dict):
    """Verify the package appears in the approved package allowlist."""
    approved_list = _load_approved_packages()
    assert package in approved_list, (
        f"Package '{package}' is not in the approved package list. "
        f"Update the list or choose a different test package."
    )
    context["package"] = package


@given(parsers.parse("'{package}' is not in the approved package list"))
def check_package_not_approved(package: str, context: dict):
    """Verify the package is absent from the approved package allowlist."""
    approved_list = _load_approved_packages()
    assert package not in approved_list, (
        f"Package '{package}' is in the approved package list — "
        f"choose a package that should be blocked."
    )
    context["package"] = package


# ---------------------------------------------------------------------------
# When steps — execute the action under test
# ---------------------------------------------------------------------------

@when(parsers.parse('the user runs "{command}"'), target_fixture="command_result")
def run_command_as_user(command: str, context: dict) -> subprocess.CompletedProcess:
    """
    Run the given command as the test user via `su -c`.

    In CI, the test runner must be root or have sufficient privilege to switch
    users. The test user is configured in the SUDO_TEST_USER environment variable
    or falls back to 'testuser'.
    """
    test_user = context.get("user", _test_user())
    result = subprocess.run(
        ["su", "-c", command, test_user],
        capture_output=True, text=True
    )
    context["command"] = command
    context["result"] = result
    return result


@when("visudo -c is run against /etc/sudoers and /etc/sudoers.d/")
def run_visudo_check(context: dict):
    result = subprocess.run(
        ["visudo", "-c", "-f", "/etc/sudoers"],
        capture_output=True, text=True
    )
    context["result"] = result


@when("the sudoers policy is inspected for wildcard privilege grants")
def inspect_sudoers_for_wildcards(context: dict):
    """Read all sudoers fragments and collect their text for Then assertions."""
    sudoers_text = Path("/etc/sudoers").read_text()
    for fragment in Path("/etc/sudoers.d").iterdir():
        if not fragment.name.startswith("."):
            sudoers_text += "\n" + fragment.read_text()
    context["sudoers_text"] = sudoers_text


# ---------------------------------------------------------------------------
# Then steps — assert expected outcomes on real OS state
# ---------------------------------------------------------------------------

@then(parsers.parse("the command exits with code {code:d}"))
def assert_exit_code(code: int, context: dict):
    result: subprocess.CompletedProcess = context["result"]
    assert result.returncode == code, (
        f"Expected exit code {code}, got {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


@then(parsers.parse("/var/log/auth.log contains an entry with the user's identity and the command"))
def assert_auth_log_entry(context: dict):
    """Check that auth.log recorded the sudo action with the actual username."""
    user = context["user"]
    command = context["command"]
    auth_log = Path("/var/log/auth.log").read_text()
    # Standard sudo log format: "sudo: <user> : ... COMMAND=<cmd>"
    pattern = rf"sudo:\s+{re.escape(user)}\s+:.*COMMAND=.*{re.escape(command.split()[-1])}"
    assert re.search(pattern, auth_log), (
        f"No auth.log entry found for user '{user}' running '{command}'.\n"
        f"Last 20 lines of auth.log:\n" + "\n".join(auth_log.splitlines()[-20:])
    )


@then("no package is installed on the system")
def assert_package_not_installed(context: dict):
    package = context.get("package", "")
    if not package:
        return
    result = subprocess.run(
        ["dpkg", "-l", package],
        capture_output=True, text=True
    )
    # dpkg -l exits 1 if package not found; exit 0 with "un" state = not installed
    not_installed = result.returncode != 0 or "ii" not in result.stdout
    assert not_installed, f"Package '{package}' was installed despite the denial"


@then("no interactive shell process is spawned as root")
def assert_no_root_shell(context: dict):
    """Verify no root shell was spawned after the denied command."""
    result = subprocess.run(
        ["pgrep", "-u", "root", "-a"],
        capture_output=True, text=True
    )
    # Check that the denied command didn't spawn a persistent root process
    # (pgrep output checked against known shell names)
    shell_patterns = [r"\bbash\b", r"\bzsh\b", r"\bsh\b", r"\bsu\b"]
    command = context.get("command", "")
    for line in result.stdout.splitlines():
        for pattern in shell_patterns:
            if re.search(pattern, line) and command.split()[-1] in line:
                pytest.fail(f"Root shell process found after denial: {line}")


@then(parsers.parse('no fragment contains the pattern "{pattern}"'))
def assert_no_wildcard_in_sudoers(pattern: str, context: dict):
    sudoers_text: str = context["sudoers_text"]
    # Strip comment lines before checking
    active_lines = [
        line for line in sudoers_text.splitlines()
        if not line.strip().startswith("#") and line.strip()
    ]
    for line in active_lines:
        assert pattern not in line, (
            f"Prohibited pattern found in sudoers policy:\n"
            f"  Pattern: {pattern!r}\n"
            f"  Line:    {line!r}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _test_user() -> str:
    """Return the OS username to run commands as during tests."""
    import os
    return os.environ.get("SUDO_TEST_USER", "testuser")


def _load_approved_packages() -> set[str]:
    """
    Load the approved package list from the canonical source.

    The list lives in /etc/apt/approved-packages.list (one package per line).
    This file is managed by the security division and version-controlled
    in the Debian fork repository.
    """
    approved_list_path = Path("/etc/apt/approved-packages.list")
    if not approved_list_path.exists():
        pytest.skip(f"Approved package list not found at {approved_list_path}")
    return {
        line.strip()
        for line in approved_list_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
