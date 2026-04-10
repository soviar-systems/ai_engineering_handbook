"""
Manage external product source code repositories.

Scope: clone new external repos, pull updates for existing ones.
Designed for two use cases:
1) One-time setup: cloning a new external product for research
2) Pre-session refresh: ensuring all researched products have latest code

Supports multiple directories from the external repo registry (ADR-26046).

Public interface (CLI commands):
    setup <url> [--dir <dir_name>]         — Clone repo to specified directory
    update [--parallel] [repo ...]         — Pull updates for all/specified repos
    list                                    — Display all repos with branch/date/remote
    register <path> <description>           — Add new directory to registry

Configuration:
    EXTERNAL_REPO_DIRS (set[Path]) — All directories from the registry.
        Loaded from .vadocs/validation/external-repos.conf.json at import time.
        Falls back to a default path when the registry has no entries.

Dependencies:
    - git CLI
    - tools.scripts.git (clone_repo, pull_repo, get_repo_status, detect_repo_root)
    - tools.scripts.paths (get_external_repo_paths)
    - concurrent.futures (stdlib) for parallel updates

Key design decisions:
    - Reuses git.py functions — does NOT duplicate git operations
    - All directories excluded from git, validation, and docs via registry
    - Setup requires --dir when multiple directories are registered
    - Pull uses --rebase to maintain linear history
    - Structure follows project conventions: data classes → config → main → helpers
    - Exit codes: 0 = success, 1 = failure (standard CLI contract)

Usage examples:
    # Before starting work — update all repos across all directories
    uv run tools/scripts/manage_external_repos.py update

    # Update specific repos in parallel
    uv run tools/scripts/manage_external_repos.py update --parallel langgraph autogen

    # Add a new repository to the default directory
    uv run tools/scripts/manage_external_repos.py setup https://github.com/langchain-ai/langgraph

    # Add a new repository to a specific directory
    uv run tools/scripts/manage_external_repos.py setup https://github.com/example/agent --dir research/my_repos

    # Register a new directory
    uv run tools/scripts/manage_external_repos.py register research/new_agents "New agent research"

    # List all repos and their status
    uv run tools/scripts/manage_external_repos.py list
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from tools.scripts.git import clone_repo, detect_repo_root, get_repo_status, pull_repo
from tools.scripts.paths import get_external_repo_paths

# Configuration constants
# EXTERNAL_REPO_DIRS is resolved from the external repos registry at import time.
# Falls back to a default path when the registry has no entries.
_repo_root = detect_repo_root()
_external_paths = get_external_repo_paths(_repo_root)
_FALLBACK_DIRS: Set[Path] = {Path("research/ai_coding_agents")}

if _external_paths:
    EXTERNAL_REPO_DIRS: Set[Path] = {Path(p) for p in _external_paths}
else:
    EXTERNAL_REPO_DIRS: Set[Path] = _FALLBACK_DIRS

# Registry config path
_EXTERNAL_REPOS_CONFIG = ".vadocs/validation/external-repos.conf.json"


@dataclass
class AgentRepo:
    """Represents an external product source code repository."""

    name: str
    path: Path
    url: str
    parent_dir: Path  # Which registered directory contains this repo
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
        return setup_command(args.url, target_dir_name=args.dir)
    elif args.command == "update":
        repo_names = args.repos if args.repos else []
        return update_command(repo_names=repo_names, parallel=args.parallel)
    elif args.command == "list":
        return list_command(dirs_only=getattr(args, 'dirs', False))
    elif args.command == "register":
        return register_command(args.path, args.description)
    elif args.command == "unregister":
        return unregister_command(args.path)
    elif args.command == "relocate":
        return relocate_command(args.old_path, args.new_path)
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
  External product repos are cloned to directories registered in
  .vadocs/validation/external-repos.conf.json (ADR-26046).
  All registered directories are excluded from git tracking, validation
  scripts, and documentation builds.

  Consumer files (.gitignore, myst.yml) are defined per-entry in the registry.
  The relocate command updates all consumers atomically.

  To see registered directories: %(prog)s list --dirs

Examples:
  # Pre-session refresh: update all repos
  %(prog)s update

  # Update specific repos in parallel
  %(prog)s update --parallel langgraph autogen

  # Clone a new external repository
  %(prog)s setup https://github.com/langchain-ai/langgraph

  # Clone to specific registered directory (required when multiple dirs exist)
  %(prog)s setup https://github.com/example/agent --dir research/my_repos

  # Register a new directory
  %(prog)s register research/new_agents "New agent research"

  # Remove a directory from the registry
  %(prog)s unregister research/old_agents

  # Rename a directory — updates registry AND all consumer files atomically
  %(prog)s relocate old/path/external_repos new/path/external_repos

  # List all repos with status
  %(prog)s list

  # Show registered directories
  %(prog)s list --dirs
"""

    parser = argparse.ArgumentParser(
        description="Manage external product source code repositories",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Clone a new external repository",
        description="Clone a git repository into a registered directory. "
        "When multiple directories are registered, --dir is required.",
    )
    setup_parser.add_argument(
        "url",
        help="Repository URL to clone (e.g., https://github.com/org/repo)",
    )
    setup_parser.add_argument(
        "--dir",
        help="Target registered directory (required when multiple directories exist)",
        default=None,
    )

    # update command
    update_parser = subparsers.add_parser(
        "update",
        help="Pull updates for external repositories",
        description="Run 'git pull --rebase' on all (or specified) repositories. "
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
    list_parser = subparsers.add_parser(
        "list",
        help="List all external repositories with branch, date, and remote URL",
        description="Display a table of all cloned repositories with their "
        "current branch, last commit date, and remote URL.",
    )
    list_parser.add_argument(
        "--dirs",
        action="store_true",
        help="Show registered directories instead of repositories",
    )

    # register command
    register_parser = subparsers.add_parser(
        "register",
        help="Add a new directory to the external repos registry",
        description="Register a new directory for external product repos. "
        "Updates .vadocs/validation/external-repos.conf.json.",
    )
    register_parser.add_argument(
        "path",
        help="Relative path for the new directory (e.g., research/new_agents)",
    )
    register_parser.add_argument(
        "description",
        help="Description of what this directory contains",
    )

    # unregister command
    unregister_parser = subparsers.add_parser(
        "unregister",
        help="Remove a directory from the external repos registry",
        description="Remove a registered directory from the registry. "
        "Does NOT delete the directory on disk — only updates the config.",
    )
    unregister_parser.add_argument(
        "path",
        help="Relative path of the directory to remove from registry",
    )

    # relocate command
    relocate_parser = subparsers.add_parser(
        "relocate",
        help="Update registered path across all consumer files",
        description="Rename a registered directory path in the registry AND all consumer "
        "files (.gitignore, myst.yml). Moves the directory on disk if it still exists, "
        "or updates consumers only if it was already moved manually (e.g., git mv).",
    )
    relocate_parser.add_argument(
        "old_path",
        help="Current registered path (e.g., old_dir/external_repos)",
    )
    relocate_parser.add_argument(
        "new_path",
        help="New path to relocate to (e.g., new_dir/external_repos)",
    )

    return parser


def setup_command(url: str, target_dir_name: str | None = None) -> int:
    """Clone a repository to a registered directory.

    Contract: Clones repo to specified directory.
    When multiple directories registered, --dir is required.
    Returns 1 if repo already exists or clone fails.

    Args:
        url: Repository URL to clone.
        target_dir_name: Optional registered directory path (required if multiple dirs).

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    target_dir = _resolve_target_dir(repo_root, target_dir_name)
    if target_dir is None:
        return 1

    # Create directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract repo name from URL
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = target_dir / repo_name

    if repo_path.exists():
        print(f"❌ Error: Repository already exists at {repo_path}")
        print(f"   To update, run: uv run tools/scripts/manage_external_repos.py update {repo_name}")
        return 1

    # Clone the repository
    print(f"📦 Cloning {url}")
    print(f"   → {repo_path}")
    success = clone_repo(url, repo_path)
    if not success:
        print(f"❌ Error: Failed to clone repository: {url}")
        print(f"   Check the URL and your network connection")
        return 1

    print(f"✅ Repository '{repo_name}' cloned successfully")
    print(f"   Directory: {target_dir.relative_to(repo_root)}")
    print(f"   Excluded from: .gitignore, validation scripts, myst build")
    return 0


def update_command(repo_names: List[str] = None, parallel: bool = False) -> int:
    """Pull updates for repositories across all registered directories.

    Contract: Runs git pull --rebase on all (or specified) repos.
    Returns 0 only if ALL repos update successfully, 1 if ANY fail.

    Args:
        repo_names: List of repository names to update (empty list = all repos).
        parallel: Whether to update repositories concurrently.

    Returns:
        0 if all updates succeed, 1 if any fail.
    """
    repo_root = detect_repo_root()

    print(f"🔍 Discovering repositories in registered directories...")
    for dir_path in sorted(EXTERNAL_REPO_DIRS, key=str):
        full_path = repo_root / dir_path
        status = "✓" if full_path.exists() else "✗"
        print(f"   {status} {dir_path}")

    # Discover repositories across all directories
    all_repos = []
    for dir_path in EXTERNAL_REPO_DIRS:
        full_path = repo_root / dir_path
        if full_path.exists():
            repos = discover_repos(full_path, parent_dir=dir_path)
            all_repos.extend(repos)
            if repos:
                print(f"   Found {len(repos)} repo(s) in {dir_path}")

    if not all_repos:
        print("ℹ No git repositories found in registered directories")
        dirs_str = ", ".join(str(d) for d in EXTERNAL_REPO_DIRS)
        print(f"   Registered directories: {dirs_str}")
        return 0

    # Filter to specified repos if provided
    if repo_names:
        print(f"\n🎯 Filtering to specified repositories: {', '.join(repo_names)}")
        all_repos = [r for r in all_repos if r.name in repo_names]
        if not all_repos:
            available = ", ".join(r.name for r in _discover_all(repo_root))
            print(f"❌ Error: Specified repositories not found: {', '.join(repo_names)}")
            print(f"   Available: {available}")
            return 1

    print(f"\n🔄 Updating {len(all_repos)} repository/ies...")
    print(f"   Mode: {'Parallel' if parallel else 'Sequential'}")
    all_success = True

    if parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        print(f"   Using thread pool with max 5 workers\n")
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_repo = {
                executor.submit(pull_repo, repo.path): repo for repo in all_repos
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
        print()
        for idx, repo in enumerate(all_repos, 1):
            branch, _, _ = get_repo_status(repo.path)
            branch_tag = f" ({branch})" if branch else ""
            print(f"[{idx}/{len(all_repos)}] {repo.name}{branch_tag}...")
            success, message = pull_repo(repo.path)
            if success:
                if "Already up to date" in message:
                    print(f"    ✓ Already up to date")
                else:
                    print(f"    ✅ Updated")
            else:
                print(f"    ❌ FAILED: {message.strip()}")
                all_success = False

    print(f"\n{'='*60}")
    if all_success:
        print(f"✅ All repositories updated successfully")
    else:
        print(f"❌ Some repositories failed to update (see errors above)")
    print(f"{'='*60}")

    return 0 if all_success else 1


def list_command(dirs_only: bool = False) -> int:
    """List all repositories with status across all registered directories.

    Contract: Displays table of all repos with branch, date, remote.
    With dirs_only=True, shows registered directories from the registry config.
    Always returns 0 (informational command, never fails).

    Args:
        dirs_only: If True, show registered directories with descriptions
                   instead of individual git repositories.

    Returns:
        0 always.
    """
    repo_root = detect_repo_root()

    if dirs_only:
        return _list_dirs(repo_root)

    repos = _discover_all(repo_root)

    if not repos:
        print("ℹ No git repositories found in registered directories")
        dirs_str = ", ".join(str(d) for d in EXTERNAL_REPO_DIRS)
        print(f"   Registered directories: {dirs_str}")
        return 0

    print(f"📚 External Product Repositories ({len(repos)} total):\n")
    print(f"{'Name':<30} {'Directory':<30} {'Branch':<15} {'Last Commit':<12} {'Remote'}")
    print("-" * 120)

    for repo in repos:
        branch, remote, date = get_repo_status(repo.path)
        branch_str = branch if branch else "N/A"
        date_str = date if date else "N/A"
        remote_str = remote if remote else "N/A"
        dir_str = str(repo.parent_dir)
        print(f"{repo.name:<30} {dir_str:<30} {branch_str:<15} {date_str:<12} {remote_str}")

    return 0


def _list_dirs(repo_root: Path) -> int:
    """Show registered directories from the registry config.

    Args:
        repo_root: Repository root.

    Returns:
        0 always.
    """
    config_path = repo_root / _EXTERNAL_REPOS_CONFIG
    if not config_path.exists():
        print("ℹ No registry config found")
        return 0

    with open(config_path) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        print("ℹ No directories registered")
        return 0

    print(f"📂 Registered Directories ({len(entries)} total):\n")
    print(f"{'Path':<35} {'Type':<25} {'Description'}")
    print("-" * 100)

    for entry in entries:
        path_str = entry.get("path", "N/A")
        type_str = entry.get("product_type", "N/A")
        desc_str = entry.get("description", "")
        print(f"{path_str:<35} {type_str:<25} {desc_str}")

    return 0


def register_command(path: str, description: str, config_path: Path | None = None) -> int:
    """Add a new directory to the external repos registry.

    Contract: Updates external-repos.conf.json with new entry.
    Returns 1 if path already registered.

    Args:
        path: Relative path for the new directory.
        description: Human-readable description.
        config_path: Optional explicit config path (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _EXTERNAL_REPOS_CONFIG

    # Load existing registry
    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
    else:
        data = {"entries": []}

    # Check for duplicate
    existing_paths = {entry["path"] for entry in data.get("entries", [])}
    if path in existing_paths:
        print(f"❌ Error: Directory already registered: {path}")
        return 1

    # Add new entry — consumers and managed_by copied from config top-level
    # fields (ADR-26046). Not hardcoded — the config is the SSoT.
    default_consumers = data.get("default_consumers", [])
    default_managed_by = data.get("managed_by", "")
    entry = {
        "path": path,
        "description": description,
        "product_type": "external_product",
        "managed_by": default_managed_by,
        "consumers": list(default_consumers),
    }
    data["entries"].append(entry)

    # Write back
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    # Update consumer files — add exclusion for the new path
    _add_path_to_consumers(repo_root, path, entry["consumers"])

    print(f"✅ Registered directory: {path}")
    print(f"   Description: {description}")
    try:
        config_rel = config_path.relative_to(repo_root)
        print(f"   Config: {config_rel}")
    except ValueError:
        # Test or non-standard path
        print(f"   Config: {config_path}")
    return 0


def _add_path_to_consumers(repo_root: Path, path: str, consumers: List[str]) -> None:
    """Append a new exclusion path to all consumer files if not already present.

    When a directory is registered, it needs to be excluded from:
    - .gitignore: prevent git from tracking the cloned repos
    - myst.yml project.exclude: prevent docs build from processing nested repos

    Args:
        repo_root: Repository root.
        path: Relative path to add (e.g., "research/new_agents").
        consumers: List of relative consumer file paths from registry entry.
    """
    for consumer_rel in consumers:
        consumer_path = repo_root / consumer_rel
        if not consumer_path.exists():
            continue
        content = consumer_path.read_text()
        # Use trailing slash for gitignore (directory match), bare path for YAML
        exclusion = f"{path}/"
        if exclusion in content:
            # Already excluded — skip to avoid duplicates
            continue
        if consumer_rel.endswith(".gitignore"):
            # .gitignore: append as a bare directory path with trailing slash
            content = content.rstrip() + f"\n{exclusion}\n"
        else:
            # myst.yml: append as a quoted glob item under project.exclude
            yaml_entry = f'    - "{path}/*"'
            content = content.rstrip() + f"\n{yaml_entry}\n"
        consumer_path.write_text(content)


def _remove_path_from_consumers(repo_root: Path, path: str, consumers: List[str]) -> None:
    """Remove all occurrences of a path from consumer files.

    When a directory is unregistered, its exclusion entries should be cleaned up
    so future moves/renames don't leave stale entries in .gitignore or myst.yml.

    Args:
        repo_root: Repository root.
        path: Relative path to remove (e.g., "ai_agents/agents_source_code").
        consumers: List of relative consumer file paths from registry entry.
    """
    for consumer_rel in consumers:
        consumer_path = repo_root / consumer_rel
        if not consumer_path.exists():
            continue
        content = consumer_path.read_text()
        # Filter out any line containing the old path (handles both trailing-slash
        # gitignore entries and quoted YAML glob items)
        lines = content.split("\n")
        filtered = [l for l in lines if path not in l]
        updated = "\n".join(filtered)
        if updated != content:
            consumer_path.write_text(updated)


def unregister_command(path: str, config_path: Path | None = None) -> int:
    """Remove a directory from the external repos registry.

    Contract: Removes an entry from external-repos.conf.json.
    Returns 1 if path not found. Does NOT delete the directory on disk.

    Args:
        path: Relative path of the directory to remove from registry.
        config_path: Optional explicit config path (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _EXTERNAL_REPOS_CONFIG

    # Load existing registry
    if not config_path.exists():
        print(f"❌ Error: Registry not found: {config_path}")
        return 1
    with open(config_path) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    before_count = len(entries)
    # Capture consumers before removing the entry
    consumers = None
    for e in entries:
        if e["path"] == path:
            consumers = e.get("consumers", [])
            break
    entries = [e for e in entries if e["path"] != path]
    after_count = len(entries)

    if after_count == before_count:
        print(f"❌ Error: Directory not in registry: {path}")
        dirs = ", ".join(e["path"] for e in data.get("entries", []))
        print(f"   Registered: {dirs}")
        return 1

    data["entries"] = entries

    # Write back
    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    # Update consumer files — remove exclusion for the old path
    if consumers:
        _remove_path_from_consumers(repo_root, path, consumers)

    print(f"✅ Unregistered directory: {path}")
    try:
        config_rel = config_path.relative_to(repo_root)
        print(f"   Config: {config_rel}")
    except ValueError:
        print(f"   Config: {config_path}")
    return 0


def sync_consumers_command(dry_run: bool = False, config_path: Path | None = None) -> int:
    """Rebuild consumer file exclusions to match the current registry.

    Contract: Reads all registered paths, then rebuilds .gitignore and
    myst.yml exclude sections. Removes stale entries, adds missing ones.
    Returns 0 on success, 1 on failure.

    Args:
        dry_run: If True, show changes without applying them.
        config_path: Optional explicit config path (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _EXTERNAL_REPOS_CONFIG

    if not config_path.exists():
        print("❌ Error: Registry not found")
        return 1

    with open(config_path) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        print("ℹ No directories in registry")
        return 0

    # Collect all registered paths grouped by consumer
    # consumer_rel -> set of registered paths
    consumer_paths: dict[str, set[str]] = {}
    for entry in entries:
        for consumer_rel in entry.get("consumers", []):
            consumer_paths.setdefault(consumer_rel, set()).add(entry["path"])

    action = "Would update" if dry_run else "Updating"
    for consumer_rel, registered_paths in sorted(consumer_paths.items()):
        consumer_path = repo_root / consumer_rel
        if not consumer_path.exists():
            print(f"⚠ Consumer file not found: {consumer_rel}")
            continue

        content = consumer_path.read_text()
        lines = content.split("\n")

        # Determine which lines to keep:
        # - Lines not containing any registered or unregistered path pattern
        # - Then re-add all registered paths
        registered_in_file = {p for p in registered_paths if p in content}
        # Find paths in file that are NOT in registry (stale)
        all_in_file = set()
        for line in lines:
            for p in registered_paths:
                if p in line:
                    all_in_file.add(p)
        stale = all_in_file - registered_paths

        if not stale and len(registered_in_file) == len(registered_paths):
            print(f"✓ {consumer_rel}: already in sync")
            continue

        print(f"{action} {consumer_rel}:")
        for p in sorted(stale):
            print(f"  - {p}")
        for p in sorted(registered_paths - registered_in_file):
            print(f"  + {p}")

        if dry_run:
            continue

        # Remove ALL lines containing any registered or stale path
        filtered = [l for l in lines if not any(p in l for p in registered_paths | stale)]
        # Re-add registered paths
        for p in sorted(registered_paths):
            if consumer_rel.endswith(".gitignore"):
                filtered.append(f"{p}/")
            else:
                filtered.append(f'    - "{p}/*"')

        consumer_path.write_text("\n".join(filtered))

    return 0


def _resolve_target_dir(repo_root: Path, target_dir_name: str | None) -> Path | None:
    """Resolve the target directory for setup command.

    Contract: Returns the target Path if resolvable, None otherwise.
    When multiple directories registered, target_dir_name is required.

    Args:
        repo_root: Repository root.
        target_dir_name: Optional registered directory name.

    Returns:
        Resolved Path or None (with error message printed).
    """
    if len(EXTERNAL_REPO_DIRS) == 1:
        # Single directory - use it
        return repo_root / next(iter(EXTERNAL_REPO_DIRS))

    # Multiple directories - require explicit target
    if target_dir_name is None:
        dirs_str = "\n".join(f"  - {d}" for d in sorted(EXTERNAL_REPO_DIRS))
        print(f"❌ Error: Multiple directories registered. Specify --dir:")
        print(dirs_str)
        return None

    target = Path(target_dir_name)
    if target not in EXTERNAL_REPO_DIRS:
        dirs_str = ", ".join(str(d) for d in sorted(EXTERNAL_REPO_DIRS))
        print(f"❌ Error: Directory not in registry: {target_dir_name}")
        print(f"   Registered: {dirs_str}")
        return None

    full_path = repo_root / target
    if not full_path.exists():
        print(f"❌ Error: Directory does not exist: {full_path}")
        print(f"   Create it with: mkdir -p {full_path}")
        return None

    return full_path


def relocate_command(old_path: str, new_path: str,
                     config_path: Path | None = None,
                     repo_root: Path | None = None) -> int:
    """Move an external repo directory and update the registry atomically.

    Contract: Moves directory on disk (if it exists) AND updates
    the registry entry. Safe relocation — validates before moving.

    Args:
        old_path: Current registered path (relative to repo root).
        new_path: New path to relocate to (relative to repo root).
        config_path: Optional explicit config path (for testing).
        repo_root: Optional repo root (for testing).

    Returns:
        0 on success, 1 on failure.
    """
    if repo_root is None:
        repo_root = detect_repo_root()
    if config_path is None:
        config_path = repo_root / _EXTERNAL_REPOS_CONFIG

    # Load registry
    if not config_path.exists():
        print(f"❌ Error: Registry not found: {config_path}")
        return 1
    with open(config_path) as f:
        data = json.load(f)

    entries = data.get("entries", [])

    # Validate old_path exists in registry
    old_entry = None
    for e in entries:
        if e["path"] == old_path:
            old_entry = e
            break
    if old_entry is None:
        print(f"❌ Error: Path not in registry: {old_path}")
        return 1

    # Validate new_path not already registered
    existing_paths = {e["path"] for e in entries}
    if new_path in existing_paths:
        print(f"❌ Error: New path already registered: {new_path}")
        return 1

    # Move directory on disk (if it exists)
    old_dir = repo_root / old_path
    new_dir = repo_root / new_path
    if old_dir.exists():
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        old_dir.rename(new_dir)
        print(f"📁 Moved: {old_path} → {new_path}")
    else:
        print(f"ℹ Directory not on disk (already moved manually): {old_path}")

    # Update registry entry
    old_entry["path"] = new_path

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"✅ Registry updated: {old_path} → {new_path}")

    # Update all consumer files listed in the registry entry
    consumers = old_entry.get("consumers", [])
    for consumer_rel in consumers:
        consumer_path = repo_root / consumer_rel
        if consumer_path.exists():
            _update_path_in_file(consumer_path, old_path, new_path)
        else:
            print(f"   Skipped (not found): {consumer_rel}")

    print(f"✅ All consumers updated: {old_path} → {new_path}")
    return 0


def _update_path_in_file(file_path: Path, old_path: str, new_path: str) -> None:
    """Replace all occurrences of old_path with new_path in a text file.

    Args:
        file_path: Path to the file to update.
        old_path: Old path string to replace.
        new_path: New path string to replace with.
    """
    content = file_path.read_text()
    updated = content.replace(old_path, new_path)
    if updated != content:
        file_path.write_text(updated)
        print(f"   Updated: {file_path.name}")


def _discover_all(repo_root: Path) -> List[AgentRepo]:
    """Discover repositories across all registered directories.

    Args:
        repo_root: Repository root.

    Returns:
        List of AgentRepo from all directories.
    """
    all_repos = []
    for dir_path in EXTERNAL_REPO_DIRS:
        full_path = repo_root / dir_path
        if full_path.exists():
            all_repos.extend(discover_repos(full_path, parent_dir=dir_path))
    return all_repos


def discover_repos(scan_dir: Path, parent_dir: Path = None) -> List[AgentRepo]:
    """Discover all git repositories in a directory.

    Contract: Returns AgentRepo for each directory containing .git subdirectory.
    Sorted alphabetically by name for deterministic output.

    Args:
        scan_dir: Path to the directory to scan.
        parent_dir: Which registered directory contains this (for list display).

    Returns:
        List of AgentRepo objects (empty list if directory doesn't exist).
    """
    if not scan_dir.exists():
        return []

    repos = []
    for item in sorted(scan_dir.iterdir()):
        if item.is_dir() and (item / ".git").exists():
            repos.append(
                AgentRepo(
                    name=item.name,
                    path=item,
                    url="",  # Will be populated by get_repo_status if needed
                    parent_dir=parent_dir or scan_dir,
                )
            )
    return repos


if __name__ == "__main__":
    sys.exit(main())
