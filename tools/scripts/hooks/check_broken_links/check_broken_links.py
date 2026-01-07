#!/usr/bin/env python3
"""
Script to check broken links in files (default: Jupyter files .ipynb).

Usage: check_broken_links.py [paths] [--pattern PATTERN] [options]

This script is fully SVA (Smallest Viable Architecture) compliant, using only
Python's standard library (pathlib, re, sys, argparse, tempfile) for robust, local-only
link validation with full exclusion capabilities.

By default, it looks for Markdown-style links ([text](link)) in files matching the
given pattern (default: *.ipynb), but any file type can be scanned.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


def main():
    """Entry point."""
    app = LinkCheckerCLI()
    app.run()


class LinkCheckerCLI:
    """Main application orchestrator."""

    DEFAULT_EXCLUDE_DIRS = ["in_progress", ".venv"]
    DEFAULT_EXCLUDE_FILES = [".aider.chat.history.md"]

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Check for broken Markdown-style links in files (Local Filesystem Only)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Example: %(prog)s . "*.ipynb" --exclude-dirs drafts
Example: %(prog)s docs "*.rst"
Default directory: current directory
Default pattern: *.ipynb""",
        )
        parser.add_argument(
            "paths",
            nargs="*",  # This allows 0 or more files/dirs
            default=["."],
            help="Directory to search or a single file path (default: current directory)",
        )
        parser.add_argument(
            "--pattern",
            default="*.ipynb",
            help="File glob pattern to match (default: *.ipynb) - ignored if a single file is specified",
        )
        parser.add_argument(
            "--exclude-dirs",
            nargs="*",
            default=self.DEFAULT_EXCLUDE_DIRS,
            help="Directory names to exclude from the check",
        )
        parser.add_argument(
            "--exclude-files",
            nargs="*",
            default=self.DEFAULT_EXCLUDE_FILES,
            help="Specific file names to exclude from the check",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose mode for more output information.",
        )
        return parser

    def get_git_root_dir(self) -> Optional[Path]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return Path(result.stdout.strip()).resolve()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def run(self) -> None:
        args = self.parser.parse_args()
        verbose = args.verbose
        pattern = args.pattern

        # 🔍 Determine project root: Git root first, then CWD
        root_dir = self.get_git_root_dir()
        if root_dir is None:
            root_dir = Path(".").resolve()
            if verbose:
                print(
                    "Warning: Not in a Git repository. Using current directory as root."
                )
        else:
            if verbose:
                print(f"Using Git root as project root: {root_dir}")

        files = []
        file_finder = FileFinder(args.exclude_dirs, args.exclude_files, verbose)

        input_paths = args.paths if args.paths else ["."]

        for p in input_paths:
            # Resolve input path relative to current working directory (not root_dir!)
            path_obj = Path(p)
            if path_obj.is_absolute():
                resolved = path_obj.resolve()
            else:
                resolved = (Path.cwd() / path_obj).resolve()

            if resolved.is_file():
                files.append(resolved)
            elif resolved.is_dir():
                files.extend(file_finder.find(resolved, pattern))
            else:
                print(f"Warning: Path does not exist: {resolved}", file=sys.stderr)

        if not files:
            print(f"No files matching '{pattern}' found!")
            sys.exit(0)

        effective_pattern = (
            "file" if len(files) == 1 and files[0].is_file() else pattern
        )
        search_display = input_paths[0] if input_paths != ["."] else "."

        print(f"Found {len(files)} {effective_pattern} file(s) in {search_display}")

        link_extractor = LinkExtractor(verbose=verbose)
        link_validator = LinkValidator(root_dir=root_dir, verbose=verbose)
        broken_links_found = False

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", encoding="utf-8"
        ) as tf:
            temp_path = Path(tf.name)
            for file in files:
                if verbose:
                    print(f"\nChecking file: {file}")
                links = link_extractor.extract(file)
                for link in links:
                    error = link_validator.validate_link(link, file)
                    if error:
                        with open(temp_path, "a", encoding="utf-8") as f:
                            f.write(error)
                        broken_links_found = True

            Reporter.report(temp_path, broken_links_found)


class LinkExtractor:
    """Extracts Markdown-style links from a given file."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def extract(self, file: Path) -> List[str]:
        """Extract all Markdown links from the file."""
        try:
            content = file.read_text(encoding="utf-8")
            matches = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)

            if self.verbose:
                if matches:
                    print(f"  Links found in {file}: {matches}")
                else:
                    print(f"  No links found for {file}")

            return matches
        except UnicodeDecodeError:
            print(f"Warning: Cannot decode file {file}. Skipping.", file=sys.stderr)
            return []


class LinkValidator:
    """Validates whether a link points to a valid local target."""

    def __init__(self, root_dir: Path, verbose: bool = False):
        self.root_dir = root_dir.resolve()
        self.verbose = verbose

    def is_absolute_url(self, link: str) -> bool:
        """Check if link is an absolute HTTP/HTTPS URL."""
        return bool(re.match(r"^https?://", link))

    def get_path_from_link(self, link: str) -> str:
        """Remove fragment and escape characters from link."""
        path_only = link.split("#")[0]
        return path_only.replace("\\", "")

    def resolve_target_path(self, link_path_str: str, source_file: Path) -> Path:
        """Resolve relative or absolute (project-root-relative) paths."""
        link_path = Path(link_path_str)

        if link_path.is_absolute():
            # Treat as absolute from project root (strip leading /)
            path_str_cleaned = str(link_path).lstrip("/")
            return self.root_dir / path_str_cleaned
        else:
            return source_file.parent / link_path

    def is_valid_target(self, target_file: Path) -> bool:
        """Check if target exists or is a dir with index/README."""
        if target_file.exists():
            if target_file.is_dir():
                index_files = [
                    target_file / "index.ipynb",
                    target_file / "README.ipynb",
                ]
                return any(p.exists() for p in index_files)
            return True
        return False

    def validate_link(self, link: str, source_file: Path) -> Optional[str]:
        """
        Validate a single link.
        Returns error message if broken, None if valid/skipped.
        """
        if self.is_absolute_url(link):
            if self.verbose:
                print(f"  SKIP External URL: {link}")
            return None

        link_path = self.get_path_from_link(link)
        if not link_path:
            return None

        # Skip internal fragments without path separators or dots
        if "/" not in link_path and "\\" not in link_path and "." not in link_path:
            if self.verbose:
                print(f"  SKIP Internal Fragment/Variable: {link}")
            return None

        target_file = self.resolve_target_path(link_path, source_file)

        if not self.is_valid_target(target_file):
            try:
                rel_source = source_file.relative_to(self.root_dir)
            except ValueError:
                rel_source = source_file
            return f"BROKEN LINK: File '{rel_source}' contains broken link: {link}\n"
        elif self.verbose:
            try:
                rel_target = target_file.relative_to(self.root_dir)
            except ValueError:
                rel_target = target_file
            print(f"  OK: {link} -> {rel_target}")

        return None


class FileFinder:
    """Finds files matching a pattern while respecting exclusion rules."""

    def __init__(
        self,
        exclude_dirs: List[str],
        exclude_files: List[str],
        verbose: bool = False,
    ):
        self.exclude_dirs = exclude_dirs
        self.exclude_files = exclude_files
        self.verbose = verbose

    def find(self, search_dir: Path, pattern: str) -> List[Path]:
        """Return list of matching files, excluding specified dirs/files."""
        all_files = list(search_dir.rglob(pattern))
        filtered_files = []

        for file in all_files:
            resolved_file = file.resolve()

            # Exclude by directory
            excluded = False
            for excl_dir in self.exclude_dirs:
                exclude_path = search_dir / excl_dir
                if (
                    exclude_path in resolved_file.parents
                    or exclude_path == resolved_file
                ):
                    excluded = True
                    break

            if not excluded and file.name in self.exclude_files:
                excluded = True

            if not excluded and ".ipynb_checkpoints" in str(resolved_file):
                excluded = True

            if not excluded:
                filtered_files.append(file)

        return filtered_files


class Reporter:
    """Handles result reporting and exit behavior."""

    @staticmethod
    def report(temp_file: Path, broken_links_found: bool) -> None:
        if broken_links_found:
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    report_content = f.read()
            except FileNotFoundError:
                print("Error: Temporary report file not found.", file=sys.stderr)
                sys.exit(1)

            count = sum(
                1 for line in report_content.splitlines() if "BROKEN LINK" in line
            )
            print(f"\n❌ {count} Broken links found:")
            print(report_content, end="")
            sys.exit(1)
        else:
            print("\n✅ All links are valid!")
            sys.exit(0)


if __name__ == "__main__":
    main()
