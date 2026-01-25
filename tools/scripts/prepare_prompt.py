#!/usr/bin/env python3
"""
Script to prepare prompt files for LLM consumption.

Usage:
    prepare_prompt.py <file>                    # Process JSON file (YAML-like output)
    prepare_prompt.py <file> --format plain     # Extract text values only
    prepare_prompt.py --stdin                   # Read from stdin
    prepare_prompt.py --stdin --format plain    # Stdin with plain text output

Exit codes:
    0 = Success
    1 = Error (file not found, invalid JSON, etc.)

This script converts prompt JSON files to LLM-friendly formats by removing
metadata, stripping special characters, and converting to YAML-like output.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO


def main():
    """Entry point."""
    cli = PreparePromptCLI()
    cli.run()


class JsonHandler:
    """Handle JSON-specific processing: metadata removal, YAML conversion."""

    # Characters to strip from YAML-like output (matches bash: sed "s/[*'\"\\`#]//g")
    STRIP_CHARS = "*'\"\\`#"

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def parse(self, content: str) -> dict | list | None:
        """Parse JSON content. Returns None if invalid."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON - {e.msg} at line {e.lineno}", file=sys.stderr)
            return None

    def remove_metadata(self, data: dict) -> dict:
        """Remove metadata field from JSON object."""
        if isinstance(data, dict) and "metadata" in data:
            result = {k: v for k, v in data.items() if k != "metadata"}
            if self.verbose:
                print("  Removed 'metadata' field", file=sys.stderr)
            return result
        return data

    def to_yaml_like(self, data: dict | list, indent: int = 0) -> str:
        """Convert JSON to YAML-like format with character stripping."""
        lines = []
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self.to_yaml_like(value, indent + 1))
                else:
                    clean_value = self._strip_chars(self._format_value(value))
                    lines.append(f"{prefix}{key}: {clean_value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    lines.append(self.to_yaml_like(item, indent + 1))
                else:
                    clean_item = self._strip_chars(self._format_value(item))
                    lines.append(f"{prefix}- {clean_item}")
        else:
            lines.append(f"{prefix}{self._strip_chars(str(data))}")

        return "\n".join(lines)

    def to_plain_text(self, data: dict | list) -> str:
        """Extract text values only, newline-separated."""
        values = []
        self._extract_values(data, values)
        return "\n".join(values)

    def _extract_values(self, data: dict | list, values: list) -> None:
        """Recursively extract string values."""
        if isinstance(data, dict):
            for value in data.values():
                self._extract_values(value, values)
        elif isinstance(data, list):
            for item in data:
                self._extract_values(item, values)
        elif isinstance(data, str):
            clean = self._strip_chars(data)
            if clean.strip():
                values.append(clean)
        elif data is not None:
            values.append(self._format_value(data))

    def _strip_chars(self, text: str) -> str:
        """Remove special characters from text."""
        result = text
        for char in self.STRIP_CHARS:
            result = result.replace(char, "")
        return result

    def _format_value(self, value) -> str:
        """Format a value for output, converting booleans to lowercase."""
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)


class Reporter:
    """Handle output formatting and exit behavior."""

    @staticmethod
    def output(content: str) -> None:
        """Print content to stdout."""
        print(content)

    @staticmethod
    def success() -> None:
        """Exit with success code."""
        sys.exit(0)

    @staticmethod
    def error(message: str) -> None:
        """Print error message and exit with error code."""
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)


class PreparePromptCLI:
    """Main application orchestrator."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Prepare prompt files for LLM consumption",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Examples:
  %(prog)s prompt.json                    # YAML-like output (default)
  %(prog)s prompt.json --format plain     # Extract text values only
  cat prompt.json | %(prog)s --stdin      # Read from stdin
  %(prog)s prompt.json --verbose          # Show processing details
""",
        )
        parser.add_argument(
            "file",
            nargs="?",
            help="Path to prompt file (JSON)",
        )
        parser.add_argument(
            "--stdin",
            action="store_true",
            default=False,
            help="Read input from stdin instead of file",
        )
        parser.add_argument(
            "--format",
            choices=["yaml", "plain"],
            default="yaml",
            help="Output format: yaml (default) or plain text",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output",
        )
        return parser

    def run(self, argv: list[str] | None = None) -> None:
        """Execute the prompt preparation."""
        args = self.parser.parse_args(argv)

        # Validate arguments
        if not args.stdin and not args.file:
            Reporter.error("Either provide a file path or use --stdin")

        if args.stdin and args.file:
            Reporter.error("Cannot use both file path and --stdin")

        # Read content
        content = self._read_content(args.file, args.stdin, args.verbose)

        # Process content
        handler = JsonHandler(verbose=args.verbose)
        data = handler.parse(content)

        if data is None:
            sys.exit(1)

        # Remove metadata if present
        if isinstance(data, dict):
            data = handler.remove_metadata(data)

        # Generate output
        if args.format == "yaml":
            output = handler.to_yaml_like(data)
        else:
            output = handler.to_plain_text(data)

        Reporter.output(output)
        Reporter.success()

    def _read_content(
        self, file_path: str | None, use_stdin: bool, verbose: bool
    ) -> str:
        """Read content from file or stdin."""
        if use_stdin:
            if verbose:
                print("Reading from stdin...", file=sys.stderr)
            return self._read_stdin(sys.stdin)

        path = Path(file_path)
        if not path.exists():
            Reporter.error(f"File not found: {file_path}")

        if not path.is_file():
            Reporter.error(f"Not a file: {file_path}")

        if verbose:
            print(f"Reading from file: {file_path}", file=sys.stderr)

        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            Reporter.error(f"UTF-8 encoding error: {e}")
        except OSError as e:
            Reporter.error(f"Cannot read file: {e}")

    def _read_stdin(self, stdin: TextIO) -> str:
        """Read all content from stdin."""
        return stdin.read()


if __name__ == "__main__":
    main()
