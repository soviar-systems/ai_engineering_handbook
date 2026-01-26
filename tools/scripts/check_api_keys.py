#!/usr/bin/env python3
"""
Script to detect real API keys in files.

Usage:
    check_api_keys.py [files...]           # Pre-commit mode (specific files)
    check_api_keys.py --verbose            # Directory scan mode

Exit codes:
    0 = No API keys found
    1 = API keys detected

This script detects potential API keys using regex patterns while filtering out
placeholders and low-entropy strings to minimize false positives.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

from tools.scripts.paths import API_KEYS_PLACEHOLDER_INDICATORS


def main():
    """Entry point."""
    app = ApiKeyCheckerCLI()
    app.run()


class ApiKeyMatch(NamedTuple):
    """Represents a detected API key match."""

    key: str
    provider: str
    file_path: Path
    line_no: int


class ApiKeyDetector:
    """Detect API keys using regex patterns."""

    # API key patterns: (provider_name, regex_pattern, min_length)
    PATTERNS = [
        ("OpenAI", r"sk-[a-zA-Z0-9]{48,}", 51),
        ("OpenAI Project", r"sk-proj-[a-zA-Z0-9_-]{48,}", 56),
        ("GROQ", r"gsk_[a-zA-Z0-9]{48,}", 52),
        ("Google", r"AIza[a-zA-Z0-9_-]{35}", 39),
        ("GitHub", r"gh[pousr]_[a-zA-Z0-9]{36,}", 40),
        ("Slack", r"xox[bpras]-[a-zA-Z0-9-]+", 32),
        ("AWS", r"AKIA[A-Z0-9]{16}", 20),
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.validator = ApiKeyValidator(verbose=verbose)

    def detect_in_file(self, file_path: Path) -> list[ApiKeyMatch]:
        """Detect API keys in a single file."""
        matches = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            if self.verbose:
                print(f"  SKIP (binary file): {file_path}", file=sys.stderr)
            return []
        except OSError as e:
            print(f"Warning: Cannot read file {file_path}: {e}", file=sys.stderr)
            return []

        lines = content.splitlines()

        for line_no, line in enumerate(lines, 1):
            # Check known provider patterns
            for provider, pattern, min_length in self.PATTERNS:
                for match in re.finditer(pattern, line):
                    key = match.group()
                    if len(key) >= min_length and self.validator.is_real_key(key):
                        matches.append(
                            ApiKeyMatch(
                                key=key,
                                provider=provider,
                                file_path=file_path,
                                line_no=line_no,
                            )
                        )

        return matches


class ApiKeyValidator:
    """Validate if a detected string is a real key vs placeholder."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.placeholder_indicators = API_KEYS_PLACEHOLDER_INDICATORS

    def is_real_key(self, key: str) -> bool:
        """Check if the key appears to be a real key (not a placeholder)."""
        key_lower = key.lower()

        # Check for placeholder indicators
        for indicator in self.placeholder_indicators:
            if indicator in key_lower:
                if self.verbose:
                    print(f"  SKIP (placeholder indicator '{indicator}'): {key[:20]}...")
                return False

        # Check for low entropy (repetitive characters)
        if self._is_low_entropy(key):
            if self.verbose:
                print(f"  SKIP (low entropy): {key[:20]}...")
            return False

        # Check for sequential patterns
        if self._is_sequential(key):
            if self.verbose:
                print(f"  SKIP (sequential pattern): {key[:20]}...")
            return False

        return True

    @staticmethod
    def _is_low_entropy(key: str) -> bool:
        """Check if key has suspiciously low entropy (e.g., all same char)."""
        # If more than 80% of characters are the same, it's likely fake
        if not key:
            return True

        char_counts = {}
        for char in key:
            char_counts[char] = char_counts.get(char, 0) + 1

        max_count = max(char_counts.values())
        return max_count / len(key) > 0.8

    @staticmethod
    def _is_sequential(key: str) -> bool:
        """Check if key contains obvious sequential patterns (very long runs only)."""
        # Only match very long sequential runs that are clearly fake
        # Short sequences like "123456" or "abcdef" can appear in real keys
        sequential_patterns = [
            "1234567890123456",  # 16+ digit sequence
            "abcdefghijklmnop",  # 16+ letter sequence
            "ABCDEFGHIJKLMNOP",  # 16+ letter sequence
        ]
        return any(pattern in key for pattern in sequential_patterns)


class FileFinder:
    """Find files to scan."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def find(self, search_dir: Path) -> list[Path]:
        """Return list of all files in directory."""
        files = []

        for file_path in search_dir.rglob("*"):
            if file_path.is_file():
                files.append(file_path)

        return files


class Reporter:
    """Report results and handle exit behavior."""

    @staticmethod
    def report(matches: list[ApiKeyMatch], verbose: bool = False) -> None:
        """Report detected API keys and exit with appropriate code."""
        if matches:
            print(f"\n{len(matches)} potential API key(s) detected:")
            for match in matches:
                print(
                    f"  [{match.provider}] {match.file_path}:{match.line_no}: "
                    f"{match.key[:10]}...{match.key[-4:]}"
                )
            sys.exit(1)
        else:
            if verbose:
                print("\nNo API keys detected.")
            sys.exit(0)


class ApiKeyCheckerCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Detect real API keys in files",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Examples:
  %(prog)s file1.md file2.py    # Check specific files
  %(prog)s --verbose            # Scan current directory with verbose output
""",
        )
        parser.add_argument(
            "files",
            nargs="*",
            help="Files to check (if none provided, scans current directory)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output",
        )
        return parser

    def run(self, argv: list[str] | None = None) -> None:
        """Execute the API key check."""
        args = self.parser.parse_args(argv)
        verbose = args.verbose

        detector = ApiKeyDetector(verbose=verbose)
        all_matches: list[ApiKeyMatch] = []

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
                print(f"Scanning {len(files)} file(s) in current directory...")

        for file_path in files:
            if not file_path.exists():
                print(f"Warning: File does not exist: {file_path}", file=sys.stderr)
                continue

            if not file_path.is_file():
                continue

            matches = detector.detect_in_file(file_path)
            all_matches.extend(matches)

        Reporter.report(all_matches, verbose=verbose)


if __name__ == "__main__":
    main()
