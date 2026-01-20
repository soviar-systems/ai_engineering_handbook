#!/usr/bin/env python3
"""
Script to validate JSON files for syntax errors.

Usage:
    check_json_files.py [files...]           # Pre-commit mode (specific files)
    check_json_files.py --verbose            # Directory scan mode

Exit codes:
    0 = All JSON files valid
    1 = Validation errors found

This script validates JSON syntax using Python's standard library json module,
following the SVA (Smallest Viable Architecture) principle with zero external
dependencies.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple


def main():
    """Entry point."""
    app = JsonValidatorCLI()
    app.run()


class JsonError(NamedTuple):
    """Represents a JSON validation error."""

    file_path: Path
    line: int
    message: str


class JsonValidator:
    """Validate JSON file syntax."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def validate_file(self, file_path: Path) -> JsonError | None:
        """Validate a single JSON file.

        Returns JsonError if invalid, None if valid.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            return JsonError(
                file_path=file_path,
                line=1,
                message=f"UTF-8 encoding error: {e}",
            )
        except OSError as e:
            return JsonError(
                file_path=file_path,
                line=1,
                message=f"Cannot read file: {e}",
            )

        # Handle empty files
        if not content.strip():
            if self.verbose:
                print(f"  SKIP (empty file): {file_path}")
            return None

        try:
            json.loads(content)
            if self.verbose:
                print(f"  OK: {file_path}")
            return None
        except json.JSONDecodeError as e:
            return JsonError(
                file_path=file_path,
                line=e.lineno,
                message=e.msg,
            )


class FileFinder:
    """Find JSON files to scan."""

    # Directories to exclude from scanning
    EXCLUDE_DIRS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".ipynb_checkpoints",
        "build",
        "dist",
    }

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def find(self, search_dir: Path) -> list[Path]:
        """Return list of all JSON files in directory."""
        files = []

        for file_path in search_dir.rglob("*.json"):
            if not file_path.is_file():
                continue

            # Check for excluded directories
            if any(part in self.EXCLUDE_DIRS for part in file_path.parts):
                if self.verbose:
                    print(f"  EXCLUDING (directory rule): {file_path}")
                continue

            files.append(file_path)

        return files


class Reporter:
    """Report results and handle exit behavior."""

    @staticmethod
    def report(errors: list[JsonError], verbose: bool = False) -> None:
        """Report validation errors and exit with appropriate code."""
        if errors:
            print(f"\n{len(errors)} JSON validation error(s) found:")
            for error in errors:
                print(f"  {error.file_path}:{error.line}: {error.message}")
            sys.exit(1)
        else:
            if verbose:
                print("\nAll JSON files are valid.")
            sys.exit(0)


class JsonValidatorCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Validate JSON file syntax",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Examples:
  %(prog)s file1.json file2.json    # Check specific files
  %(prog)s --verbose                # Scan current directory with verbose output
""",
        )
        parser.add_argument(
            "files",
            nargs="*",
            help="Files to check (if none provided, scans current directory for *.json)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output",
        )
        return parser

    def run(self, argv: list[str] | None = None) -> None:
        """Execute the JSON validation."""
        args = self.parser.parse_args(argv)
        verbose = args.verbose

        validator = JsonValidator(verbose=verbose)
        all_errors: list[JsonError] = []

        if args.files:
            # Pre-commit mode: check specific files
            files = [Path(f) for f in args.files]
            if verbose:
                print(f"Checking {len(files)} file(s)...")
        else:
            # Directory scan mode
            finder = FileFinder(verbose=verbose)
            files = finder.find(Path.cwd())
            if verbose:
                print(f"Scanning {len(files)} JSON file(s) in current directory...")

        for file_path in files:
            if not file_path.exists():
                print(f"Warning: File does not exist: {file_path}", file=sys.stderr)
                continue

            if not file_path.is_file():
                continue

            error = validator.validate_file(file_path)
            if error:
                all_errors.append(error)

        Reporter.report(all_errors, verbose=verbose)


if __name__ == "__main__":
    main()
