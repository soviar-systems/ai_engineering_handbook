#!/usr/bin/env python3
"""
Script to check link format in Markdown files - ensures ipynb priority.

Usage: check_link_format.py [--paths PATH ...] [--pattern PATTERN] [options]

When a .md file has a paired .ipynb file (Jupytext pair), links should point to
the .ipynb version because myst.yml only renders .ipynb files. Links to .md files
cause downloads instead of opening as web pages.

This script is fully SVA (Smallest Viable Architecture) compliant, using only
Python's standard library (pathlib, re, sys, argparse, tempfile).
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from tools.scripts.paths import (
    BROKEN_LINKS_EXCLUDE_DIRS,
    BROKEN_LINKS_EXCLUDE_FILES,
    BROKEN_LINKS_EXCLUDE_LINK_STRINGS,
)


def main():
    """Entry point."""
    app = LinkFormatCLI()
    app.run()


class LinkFormatCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Check link format in Markdown files - ensures ipynb priority when paired file exists",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Example: %(prog)s --pattern "*.md" --exclude-dirs drafts
Example: %(prog)s --paths docs --verbose
Default directory: current directory
Default pattern: *.md""",
        )
        parser.add_argument(
            "--paths",
            nargs="*",
            help="Paths to Markdown files or directories to check (default: current directory).",
        )
        parser.add_argument(
            "--pattern",
            default="*.md",
            help="File glob pattern to match (default: *.md) - ignored if a single file is specified",
        )
        parser.add_argument(
            "--exclude-dirs",
            nargs="*",
            default=BROKEN_LINKS_EXCLUDE_DIRS,
            help="Directory names to exclude from the check",
        )
        parser.add_argument(
            "--exclude-files",
            nargs="*",
            default=BROKEN_LINKS_EXCLUDE_FILES,
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

    def run(self, argv: Optional[List[str]] = None) -> None:
        """
        Execute logic.
        :param argv: Optional list of strings. If None, uses sys.argv[1:].
        """
        args = self.parser.parse_args(argv)
        verbose = args.verbose
        pattern = args.pattern

        root_dir = self.get_git_root_dir()
        if root_dir is None:
            root_dir = Path(".").resolve()
            if verbose:
                print(
                    "Warning: Not in a Git repository. Using current directory as root."
                )
        else:
            print(f"Using Git root as project root: {root_dir.name}")

        files = []
        file_finder = FileFinder(args.exclude_dirs, args.exclude_files, verbose)

        is_current_dir = False
        if args.paths:
            input_paths = args.paths
        else:
            is_current_dir = True
            input_paths = [str(Path.cwd())]

        for p in input_paths:
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
            "file" if len(files) == 1 and files[0].is_file() else "files"
        )

        print(f"Found {len(files)} {effective_pattern} in:", end="")
        if is_current_dir:
            print(f" {input_paths[0].split('/')[-1]}/")
        elif len(input_paths) == 1:
            print(f" {input_paths[0]}")
        else:
            for p in input_paths:
                print(f"\n- {p}", end="")
            print()

        link_extractor = LinkExtractor(verbose=verbose)
        link_format_validator = LinkFormatValidator(
            root_dir=root_dir,
            verbose=verbose,
            exclude_link_strings=list(BROKEN_LINKS_EXCLUDE_LINK_STRINGS),
        )
        format_errors_found = False

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", encoding="utf-8"
        ) as tf:
            temp_path = Path(tf.name)
            for file in files:
                if verbose:
                    print(f"\nChecking file: {file}")
                links = link_extractor.extract(file)
                for link, line_no in links:
                    error = link_format_validator.validate_link_format(
                        link, file, line_no
                    )
                    if error:
                        with open(temp_path, "a", encoding="utf-8") as f:
                            f.write(error)
                        format_errors_found = True

            Reporter.report(temp_path, format_errors_found)


class LinkExtractor:
    """Extracts Markdown-style links from a given file."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def extract(self, file: Path) -> List[Tuple[str, int]]:
        """Extract all Markdown links from the file with their line numbers."""
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
            matches = []
            for i, line in enumerate(lines, 1):
                # Standard Markdown links: [text](link)
                md_links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", line)
                for link in md_links:
                    matches.append((link, i))

                # MyST include directives: {include} path
                myst_includes = [
                    m[1:] if m.startswith(" ") and not m.startswith("  ") else m
                    for m in re.findall(r"```\{include\}([^`\n]+)", line)
                    if m.strip()
                ]
                for link in myst_includes:
                    matches.append((link, i))

            if self.verbose:
                if matches:
                    print(f"  Links found in {file}: {matches}")
                else:
                    print(f"  No links found for {file}")

            return matches
        except UnicodeDecodeError:
            print(f"Warning: Cannot decode file {file}. Skipping.", file=sys.stderr)
            return []


class LinkFormatValidator:
    """Validates link format - checks if .md links should be .ipynb instead."""

    def __init__(
        self,
        root_dir: Path,
        verbose: bool = False,
        exclude_link_strings: Optional[List[str]] = None,
    ):
        self.root_dir = root_dir.resolve()
        self.verbose = verbose
        self.exclude_link_strings = (
            set(exclude_link_strings) if exclude_link_strings else set()
        )

    def is_absolute_url(self, link: str) -> bool:
        """Check if link is an absolute HTTP/HTTPS URL."""
        return bool(re.match(r"^https?://", link))

    def get_path_from_link(self, link: str) -> str:
        """Remove fragment from link."""
        return link.split("#")[0]

    def resolve_target_path(self, link_path_str: str, source_file: Path) -> Path:
        """Resolve relative or absolute (project-root-relative) paths."""
        link_path = Path(link_path_str)

        if link_path.is_absolute():
            path_str_cleaned = str(link_path).lstrip("/")
            return (self.root_dir / path_str_cleaned).resolve()
        else:
            return (source_file.parent / link_path).resolve()

    def validate_link_format(
        self, link: str, source_file: Path, line_no: int
    ) -> Optional[str]:
        """
        Validate link format - check if .md link should be .ipynb.
        Returns error message if format issue found, None if valid/skipped.
        """
        if self.is_absolute_url(link):
            if self.verbose:
                print(f"  SKIP External URL: {link}")
            return None

        link_path = self.get_path_from_link(link)
        if not link_path:
            return None

        # Skip internal fragments without path separators or dots
        if "/" not in link_path and "." not in link_path:
            if self.verbose:
                print(f"  SKIP Internal Fragment/Variable: {link}")
            return None

        # Check for excluded link strings
        if any(exclude_str in link_path for exclude_str in self.exclude_link_strings):
            if self.verbose:
                print(f"  SKIP Excluded Link String: {link}")
            return None

        # Only check .md links
        if not link_path.endswith(".md"):
            if self.verbose:
                print(f"  OK (not .md): {link}")
            return None

        target_path = self.resolve_target_path(link_path, source_file)

        # Check if paired .ipynb exists
        ipynb_path = target_path.with_suffix(".ipynb")
        if ipynb_path.exists():
            try:
                rel_source = source_file.relative_to(self.root_dir)
            except ValueError:
                rel_source = source_file

            suggested_link = link.replace(".md", ".ipynb")
            return (
                f"LINK FORMAT ERROR: File '{rel_source}:{line_no}' links to '{link}' "
                f"but paired .ipynb exists.\n"
                f"  Suggested fix: Change to '{suggested_link}'\n"
            )
        elif self.verbose:
            print(f"  OK (no .ipynb pair): {link}")

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
        filtered_files = []

        for file in search_dir.rglob(pattern):
            if not file.is_file():
                if self.verbose:
                    print(f"  SKIPPING (not a file): {file}")
                continue

            if file.name in self.exclude_files:
                if self.verbose:
                    print(f"  EXCLUDING (by file name): {file}")
                continue

            try:
                relative_path = file.relative_to(search_dir)
            except ValueError:
                filtered_files.append(file)
                continue

            is_excluded_by_dir = False

            if ".ipynb_checkpoints" in relative_path.parts:
                is_excluded_by_dir = True

            if not is_excluded_by_dir:
                for part in relative_path.parts:
                    if part in self.exclude_dirs:
                        is_excluded_by_dir = True
                        break

            if not is_excluded_by_dir:
                current_check_path = relative_path
                while current_check_path != Path("."):
                    if str(current_check_path) in self.exclude_dirs:
                        is_excluded_by_dir = True
                        break
                    current_check_path = current_check_path.parent

            if is_excluded_by_dir:
                if self.verbose:
                    print(f"  EXCLUDING (by directory rule): {file}")
                continue

            filtered_files.append(file)

        return filtered_files


class Reporter:
    """Handles result reporting and exit behavior."""

    @staticmethod
    def report(temp_file: Path, errors_found: bool) -> None:
        if errors_found:
            try:
                with open(temp_file, "r", encoding="utf-8") as f:
                    report_content = f.read()
            except FileNotFoundError:
                print("Error: Temporary report file not found.", file=sys.stderr)
                sys.exit(1)

            count = sum(
                1 for line in report_content.splitlines() if "LINK FORMAT ERROR" in line
            )
            print(f"\n❌ {count} Link format errors found:")
            print(report_content, end="")
            sys.exit(1)
        else:
            print("\n✅ All link formats are correct!")
            sys.exit(0)


if __name__ == "__main__":
    main()
