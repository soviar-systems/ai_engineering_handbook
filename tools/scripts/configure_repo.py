#!/usr/bin/env python3
"""
Script to configure the repository for development.

Usage:
    configure_repo.py                    # Full setup
    configure_repo.py --skip-uv-sync     # Skip uv sync and pre-commit install
    configure_repo.py --skip-symlinks    # Skip ~/bin symlink creation
    configure_repo.py --dry-run          # Show what would be done
    configure_repo.py --verbose          # Verbose output

Exit codes:
    0 = Setup completed successfully
    1 = Setup failed

This script performs the following setup tasks:
1. Runs `uv sync` to install dependencies
2. Runs `uv run pre-commit install` to set up git hooks
3. Copies aider config file to repository root
4. Makes all .sh and .py files executable
5. Creates symlinks in ~/bin for scripts
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    """Entry point."""
    app = ConfigureRepoCLI()
    app.run()


class UvSyncRunner:
    """Run uv sync and pre-commit install commands."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run

    def run(self) -> bool:
        """Run both uv sync and pre-commit install."""
        if not self.run_uv_sync():
            return False
        if not self.run_precommit_install():
            return False
        return True

    def run_uv_sync(self) -> bool:
        """Run uv sync command."""
        cmd = ["uv", "sync"]
        return self._execute(cmd, "Running uv sync")

    def run_precommit_install(self) -> bool:
        """Run uv run pre-commit install command."""
        cmd = ["uv", "run", "pre-commit", "install"]
        return self._execute(cmd, "Installing pre-commit hooks")

    def _execute(self, cmd: list[str], description: str) -> bool:
        """Execute a command and return success status."""
        if self.verbose:
            print(f"  {description}...")

        if self.dry_run:
            if self.verbose:
                print(f"    [DRY RUN] Would execute: {' '.join(cmd)}")
            return True

        result = subprocess.run(cmd, capture_output=not self.verbose)
        if result.returncode != 0:
            print(f"Error: {description} failed", file=sys.stderr)
            if not self.verbose and result.stderr:
                print(result.stderr.decode(), file=sys.stderr)
            return False

        return True


class AiderConfigCopier:
    """Copy aider configuration file to repository root."""

    def __init__(
        self,
        repo_root: Path,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.repo_root = repo_root
        self.verbose = verbose
        self.dry_run = dry_run
        self.source = repo_root / "tools" / "configs" / "aider.conf.yml"
        self.target = repo_root / ".aider.conf.yml"

    def copy(self) -> bool:
        """Copy aider config if source exists and target doesn't."""
        if self.verbose:
            print("  Checking aider config...")

        if not self.source.exists():
            if self.verbose:
                print(f"    Source not found: {self.source}")
                print("    Skipping aider config copy.")
            return True

        if self.target.exists():
            if self.verbose:
                print(f"    Target already exists: {self.target}")
                print("    Skipping aider config copy.")
            return True

        if self.dry_run:
            if self.verbose:
                print(f"    [DRY RUN] Would copy {self.source} to {self.target}")
            return True

        shutil.copy2(self.source, self.target)
        if self.verbose:
            print(f"    Copied aider config to {self.target}")

        return True


class ScriptPermissions:
    """Make script files executable."""

    def __init__(
        self,
        repo_root: Path,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.repo_root = repo_root
        self.verbose = verbose
        self.dry_run = dry_run
        self.modified_count = 0

    def set_permissions(self) -> bool:
        """Make all .sh and .py files executable."""
        if self.verbose:
            print("  Setting script permissions...")

        self.modified_count = 0

        for pattern in ["**/*.sh", "**/*.py"]:
            for script in self.repo_root.glob(pattern):
                if not script.is_file():
                    continue

                if self.dry_run:
                    if self.verbose:
                        print(f"    [DRY RUN] Would make executable: {script}")
                    self.modified_count += 1
                    continue

                # Add execute permission for owner, group, and others
                current_mode = script.stat().st_mode
                new_mode = current_mode | 0o111
                if current_mode != new_mode:
                    script.chmod(new_mode)
                    self.modified_count += 1
                    if self.verbose:
                        print(f"    Made executable: {script}")

        if self.verbose:
            print(f"    {self.modified_count} file(s) made executable")

        return True


class SymlinkCreator:
    """Create symlinks in ~/bin for scripts."""

    def __init__(
        self,
        scripts_dir: Path,
        bin_dir: Path,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.scripts_dir = scripts_dir
        self.bin_dir = bin_dir
        self.verbose = verbose
        self.dry_run = dry_run
        self.created_count = 0

    def create(self) -> bool:
        """Create symlinks for all files in scripts directory."""
        if self.verbose:
            print(f"  Creating symlinks in {self.bin_dir}...")

        if not self.scripts_dir.exists():
            if self.verbose:
                print(f"    Scripts directory not found: {self.scripts_dir}")
            return True

        # Ensure bin directory exists
        if not self.dry_run and not self.bin_dir.exists():
            self.bin_dir.mkdir(parents=True)
            if self.verbose:
                print(f"    Created bin directory: {self.bin_dir}")

        self.created_count = 0

        for script in self.scripts_dir.iterdir():
            if not script.is_file():
                continue

            link = self.bin_dir / script.name

            if self.dry_run:
                if self.verbose:
                    print(f"    [DRY RUN] Would create symlink: {link} -> {script}")
                self.created_count += 1
                continue

            # Remove existing symlink if it points elsewhere
            if link.is_symlink():
                link.unlink()
            elif link.exists():
                if self.verbose:
                    print(f"    Skipping {link.name}: file exists and is not a symlink")
                continue

            link.symlink_to(script.resolve())
            self.created_count += 1
            if self.verbose:
                print(f"    Created symlink: {link.name}")

        if self.verbose:
            print(f"    {self.created_count} symlink(s) created")

        return True


class Reporter:
    """Report results and handle exit behavior."""

    @staticmethod
    def report_success(message: str, verbose: bool = False) -> None:
        """Report successful completion and exit with code 0."""
        if verbose:
            print(message)
        sys.exit(0)

    @staticmethod
    def report_failure(message: str) -> None:
        """Report failure and exit with code 1."""
        print(message)
        sys.exit(1)


class ConfigureRepoCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Configure repository for development",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Examples:
  %(prog)s                    # Full setup
  %(prog)s --skip-uv-sync     # Skip uv sync and pre-commit install
  %(prog)s --skip-symlinks    # Skip symlink creation
  %(prog)s --dry-run          # Preview what would be done
  %(prog)s --verbose          # Show detailed progress
""",
        )
        parser.add_argument(
            "--skip-uv-sync",
            action="store_true",
            default=False,
            help="Skip uv sync and pre-commit install",
        )
        parser.add_argument(
            "--skip-symlinks",
            action="store_true",
            default=False,
            help="Skip creating symlinks in ~/bin",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--bin-dir",
            type=Path,
            default=Path.home() / "bin",
            help="Target directory for symlinks (default: ~/bin)",
        )
        return parser

    def run(self, argv: list[str] | None = None) -> None:
        """Execute the repository configuration."""
        args = self.parser.parse_args(argv)
        verbose = args.verbose
        dry_run = args.dry_run

        if verbose:
            print("Setting up the repository...")
            if dry_run:
                print("  [DRY RUN MODE - no changes will be made]")

        repo_root = Path.cwd()

        # Step 1: uv sync and pre-commit install
        if not args.skip_uv_sync:
            runner = UvSyncRunner(verbose=verbose, dry_run=dry_run)
            if not runner.run():
                Reporter.report_failure("Error: Failed to run uv sync or pre-commit install")
        elif verbose:
            print("  Skipping uv sync and pre-commit install")

        # Step 2: Copy aider config
        copier = AiderConfigCopier(repo_root=repo_root, verbose=verbose, dry_run=dry_run)
        copier.copy()

        # Step 3: Make scripts executable
        permissions = ScriptPermissions(repo_root=repo_root, verbose=verbose, dry_run=dry_run)
        permissions.set_permissions()

        # Step 4: Create symlinks
        if not args.skip_symlinks:
            scripts_dir = repo_root / "tools" / "scripts"
            creator = SymlinkCreator(
                scripts_dir=scripts_dir,
                bin_dir=args.bin_dir,
                verbose=verbose,
                dry_run=dry_run,
            )
            creator.create()
        elif verbose:
            print("  Skipping symlink creation")

        Reporter.report_success("Done!", verbose=verbose)


if __name__ == "__main__":
    main()
