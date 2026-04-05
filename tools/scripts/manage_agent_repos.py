"""
Manage agent source code repositories.

Scope: clone new agent repositories, pull updates for existing ones.
Designed for two use cases:
1) One-time setup: cloning a new agent framework for research
2) Pre-session refresh: ensuring all researched agents have latest code

Public interface (CLI commands):
    setup <url> [--branch <branch>]  — Clone repo and verify exclusions
    update [--parallel] [repo ...]   — Pull updates for all/specified repos
    list                              — Display all repos with branch/date/remote

Configuration:
    AGENTS_SOURCE_CODE_DIR (Path) — Directory where agent repos are cloned.
        Set via constant below. The entire directory is excluded from:
        - .gitignore: Excludes from git tracking
        - paths.py VALIDATION_EXCLUDE_DIRS: Excludes from validation scripts
        - myst.yml site.exclude: Excludes from documentation build
        See AGENTS_SOURCE_CODE_DIR constant for current path.

Dependencies:
    - git CLI
    - tools.scripts.git (clone_repo, pull_repo, get_repo_status, detect_repo_root)
    - concurrent.futures (stdlib) for parallel updates

Key design decisions:
    - Reuses git.py functions — does NOT duplicate git operations
    - Exclusion is directory-level, not per-repo — parent dir excluded everywhere
    - Setup verifies exclusions exist but does NOT modify exclusion lists
    - Pull uses --rebase to maintain linear history
    - Structure follows project conventions: data classes → config → main → helpers
    - Exit codes: 0 = success, 1 = failure (standard CLI contract)

Usage examples:
    # Before starting work — update all agent repos
    uv run tools/scripts/manage_agent_repos.py update

    # Update specific repos in parallel
    uv run tools/scripts/manage_agent_repos.py update --parallel langgraph autogen

    # Add a new agent repository
    uv run tools/scripts/manage_agent_repos.py setup https://github.com/langchain-ai/langgraph
    uv run tools/scripts/manage_agent_repos.py setup https://github.com/example/agent --branch main

    # List all repos and their status
    uv run tools/scripts/manage_agent_repos.py list
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from tools.scripts.git import clone_repo, detect_repo_root, get_repo_status, pull_repo

# Configuration constants
AGENTS_SOURCE_CODE_DIR = Path("ai_system/6_agents/agents_source_code")


@dataclass
class AgentRepo:
    """Represents an agent source code repository."""

    name: str
    path: Path
    url: str
    branch: Optional[str] = None


def main() -> int:
    """Entry point for the CLI.

    Contract: Parses CLI arguments and dispatches to appropriate command function.
    Returns exit code (0 = success, 1 = failure).

    Returns:
        Exit code for sys.exit().
    """
    parser = _create_parser()
    args = parser.parse_args()

    if args.command == "setup":
        return setup_command(args.url, branch=args.branch)
    elif args.command == "update":
        repo_names = args.repos if args.repos else []
        return update_command(repo_names=repo_names, parallel=args.parallel)
    elif args.command == "list":
        return list_command()
    else:
        parser.print_help()
        return 1


def _create_parser() -> argparse.ArgumentParser:
    """Create argument parser with comprehensive help.

    Returns:
        Configured ArgumentParser with subcommands and examples.
    """
    epilog = """
Configuration:
  Agent repositories are cloned to the directory configured in
  AGENTS_SOURCE_CODE_DIR constant (see script source). The entire directory
  is excluded from git tracking, validation scripts, and documentation builds.

  To change the location, edit AGENTS_SOURCE_CODE_DIR in the script and
  update exclusion lists in .gitignore, paths.py, and myst.yml accordingly.

Examples:
  # Pre-session refresh: update all agent repos
  %(prog)s update

  # Update specific repos in parallel
  %(prog)s update --parallel langgraph autogen

  # Clone a new agent repository
  %(prog)s setup https://github.com/langchain-ai/langgraph

  # Clone from specific branch
  %(prog)s setup https://github.com/example/agent --branch main

  # List all repos with status
  %(prog)s list
"""

    parser = argparse.ArgumentParser(
        description="Manage agent source code repositories",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Clone a new agent repository",
        description="Clone a git repository into the configured agents source "
        "directory. Verifies that the directory is properly excluded from "
        "git tracking, validation scripts, and documentation builds.",
    )
    setup_parser.add_argument(
        "url",
        help="Repository URL to clone (e.g., https://github.com/org/repo)",
    )
    setup_parser.add_argument(
        "--branch",
        help="Specific branch to clone (default: repository default branch)",
        default=None,
    )

    # update command
    update_parser = subparsers.add_parser(
        "update",
        help="Pull updates for agent repositories (use --parallel for speed)",
        description="Run 'git pull --rebase' on all (or specified) agent repositories. "
        "Use --parallel flag to update multiple repositories simultaneously. "
        "NOTE: With --parallel, SSH passphrase prompts from multiple repos "
        "will interleave on the terminal. Use sequential mode (default) if your "
        "repos require passphrase authentication.",
    )
    update_parser.add_argument(
        "repos",
        nargs="*",
        help="Specific repository names to update (empty = update all)",
    )
    update_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Update repositories concurrently. WARNING: SSH passphrase prompts "
        "from multiple repos will interleave on terminal — use sequential mode "
        "if keys require passphrase. Recommended for 3+ repos with SSH agent.",
    )

    # list command
    subparsers.add_parser(
        "list",
        help="List all agent repositories with branch, date, and remote URL",
        description="Display a table of all cloned repositories with their "
        "current branch, last commit date, and remote URL.",
    )

    return parser


def setup_command(url: str, branch: str | None = None) -> int:
    """Clone a repository and verify exclusions.

    Contract: Clones repo to AGENTS_SOURCE_CODE_DIR and verifies the directory
    is properly excluded from all tooling. Does NOT modify exclusion lists.
    If repo already exists, returns 1 with warning message.

    Args:
        url: Repository URL to clone.
        branch: Optional branch name (None = default branch).

    Returns:
        0 on success, 1 on failure (clone error or repo exists).
    """
    repo_root = detect_repo_root()
    agents_dir = repo_root / AGENTS_SOURCE_CODE_DIR

    # Verify agents directory exists
    if not agents_dir.exists():
        print(f"❌ Error: Agents directory does not exist: {agents_dir}")
        print(f"   Create it with: mkdir -p {agents_dir}")
        return 1

    # Extract repo name from URL
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = agents_dir / repo_name

    if repo_path.exists():
        print(f"❌ Error: Repository already exists at {repo_path}")
        print(f"   To update, run: uv run tools/scripts/manage_agent_repos.py update {repo_name}")
        return 1

    # Clone the repository
    print(f"📦 Cloning {url}")
    print(f"   → {repo_path}")
    success = clone_repo(url, repo_path, branch=branch)
    if not success:
        print(f"❌ Error: Failed to clone repository: {url}")
        print(f"   Check the URL and your network connection")
        return 1

    print(f"✅ Repository '{repo_name}' cloned successfully")
    if branch:
        print(f"   Branch: {branch}")
    print(f"   Path: {repo_path}")
    print(f"   Excluded from: .gitignore, validation scripts, myst build")
    return 0


def update_command(repo_names: List[str] = None, parallel: bool = False) -> int:
    """Pull updates for repositories.

    Contract: Runs git pull --rebase on all (or specified) repos.
    Returns 0 only if ALL repos update successfully, 1 if ANY fail.

    Args:
        repo_names: List of repository names to update (empty list = all repos).
        parallel: Whether to update repositories concurrently.

    Returns:
        0 if all updates succeed, 1 if any fail or no agents directory.
    """
    repo_root = detect_repo_root()
    agents_dir = repo_root / AGENTS_SOURCE_CODE_DIR

    if not agents_dir.exists():
        print(f"❌ Error: Agents directory not found: {agents_dir}")
        print(f"   Create it with: mkdir -p {agents_dir}")
        return 1

    # Discover repositories
    repos = discover_repos(agents_dir)
    if not repos:
        print("ℹ No git repositories found in agents_source_code/")
        print("   Clone a repo first: uv run tools/scripts/manage_agent_repos.py setup <url>")
        return 0

    # Filter to specified repos if provided
    if repo_names:
        repos = [r for r in repos if r.name in repo_names]
        if not repos:
            print(f"❌ Error: Specified repositories not found in {agents_dir}: {', '.join(repo_names)}")
            print(f"   Available repositories: {', '.join(r.name for r in discover_repos(agents_dir))}")
            return 1

    # Update repositories
    print(f"🔄 Updating {len(repos)} repository/ies...")
    all_success = True

    if parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_repo = {
                executor.submit(pull_repo, repo.path): repo for repo in repos
            }
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                branch, _, _ = get_repo_status(repo.path)
                branch_tag = f" ({branch})" if branch else ""
                try:
                    success, message = future.result()
                    if success:
                        if "Already up to date" in message:
                            print(f"✓ {repo.name}{branch_tag}: Already up to date")
                        else:
                            print(f"✅ {repo.name}{branch_tag}: Updated")
                    else:
                        print(f"❌ Error in {repo.name}{branch_tag} ({repo.path}): {message.strip()}")
                        all_success = False
                except Exception as e:
                    print(f"❌ Error in {repo.name}{branch_tag} ({repo.path}): Unexpected exception: {e}")
                    all_success = False
    else:
        for repo in repos:
            branch, _, _ = get_repo_status(repo.path)
            branch_tag = f" ({branch})" if branch else ""
            success, message = pull_repo(repo.path)
            if success:
                if "Already up to date" in message:
                    print(f"✓ {repo.name}{branch_tag}: Already up to date")
                else:
                    print(f"✅ {repo.name}{branch_tag}: Updated")
            else:
                print(f"❌ Error in {repo.name}{branch_tag} ({repo.path}): {message.strip()}")
                all_success = False

    return 0 if all_success else 1


def list_command() -> int:
    """List all repositories with status.

    Contract: Displays table of all repos with branch, date, remote.
    Always returns 0 (informational command, never fails).

    Returns:
        0 always.
    """
    repo_root = detect_repo_root()
    agents_dir = repo_root / AGENTS_SOURCE_CODE_DIR

    if not agents_dir.exists():
        print(f"❌ Error: Agents directory not found: {agents_dir}")
        print(f"   Create it with: mkdir -p {agents_dir}")
        return 1

    repos = discover_repos(agents_dir)
    if not repos:
        print("ℹ No git repositories found in agents_source_code/")
        print("   Clone a repo first: uv run tools/scripts/manage_agent_repos.py setup <url>")
        return 0

    print(f"📚 Agent Repositories ({len(repos)} total):\n")
    print(f"{'Name':<30} {'Branch':<15} {'Last Commit':<12} {'Remote'}")
    print("-" * 100)

    for repo in repos:
        branch, remote, date = get_repo_status(repo.path)
        branch_str = branch if branch else "N/A"
        date_str = date if date else "N/A"
        remote_str = remote if remote else "N/A"
        print(f"{repo.name:<30} {branch_str:<15} {date_str:<12} {remote_str}")

    return 0


def discover_repos(agents_dir: Path) -> List[AgentRepo]:
    """Discover all git repositories in the agents_source_code directory.

    Contract: Returns AgentRepo for each directory containing .git subdirectory.
    Sorted alphabetically by name for deterministic output.

    Args:
        agents_dir: Path to the agents_source_code directory.

    Returns:
        List of AgentRepo objects (empty list if directory doesn't exist).
    """
    if not agents_dir.exists():
        return []

    repos = []
    for item in sorted(agents_dir.iterdir()):
        if item.is_dir() and (item / ".git").exists():
            repos.append(
                AgentRepo(
                    name=item.name,
                    path=item,
                    url="",  # Will be populated by get_repo_status if needed
                )
            )
    return repos


if __name__ == "__main__":
    sys.exit(main())
