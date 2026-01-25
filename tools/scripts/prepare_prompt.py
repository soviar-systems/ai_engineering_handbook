#!/usr/bin/env python3
"""
Script to prepare prompt files for LLM consumption.

Usage:
    prepare_prompt.py <file>                       # Auto-detect format, YAML-like output
    prepare_prompt.py <file> --output-format plain # Extract text values only
    prepare_prompt.py --stdin                      # Read from stdin (JSON default)
    prepare_prompt.py --stdin --input-format yaml  # Stdin with explicit format

Supported input formats: JSON, YAML, TOML, Markdown (with frontmatter), Plain Text
Format is auto-detected from file extension, or can be specified with --input-format.

Exit codes:
    0 = Success
    1 = Error (file not found, invalid format, etc.)

This script converts prompt files to LLM-friendly formats by removing
metadata, stripping special characters, and converting to YAML-like output.
"""

import argparse
import json
import sys
import tomllib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO

import yaml


def main():
    """Entry point."""
    cli = PreparePromptCLI()
    cli.run()


class FormatDetector:
    """Detect input format from file extension or explicit flag."""

    EXTENSION_MAP = {
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".txt": "text",
    }

    @classmethod
    def detect(cls, file_path: str | None, explicit_format: str | None) -> str:
        """Detect format from extension or use explicit override."""
        if explicit_format:
            return explicit_format
        if file_path:
            suffix = Path(file_path).suffix.lower()
            return cls.EXTENSION_MAP.get(suffix, "json")
        return "json"


class InputHandler(ABC):
    """Abstract base class for input format handlers."""

    STRIP_CHARS = "*'\"\\`#"

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @abstractmethod
    def parse(self, content: str) -> dict | list | None:
        """Parse content into a data structure."""
        pass

    def remove_metadata(self, data: dict) -> dict:
        """Remove metadata field from data structure."""
        if isinstance(data, dict) and "metadata" in data:
            result = {k: v for k, v in data.items() if k != "metadata"}
            if self.verbose:
                print("  Removed 'metadata' field", file=sys.stderr)
            return result
        return data

    def to_yaml_like(self, data: dict | list, indent: int = 0) -> str:
        """Convert data to YAML-like format with character stripping."""
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


class JsonHandler(InputHandler):
    """Handle JSON-specific processing."""

    def parse(self, content: str) -> dict | list | None:
        """Parse JSON content. Returns None if invalid."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON - {e.msg} at line {e.lineno}", file=sys.stderr)
            return None


class YamlHandler(InputHandler):
    """Handle YAML-specific processing."""

    def parse(self, content: str) -> dict | list | None:
        """Parse YAML content. Returns None if invalid."""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML - {e}", file=sys.stderr)
            return None


class TomlHandler(InputHandler):
    """Handle TOML-specific processing."""

    def parse(self, content: str) -> dict | None:
        """Parse TOML content. Returns None if invalid."""
        try:
            return tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            print(f"Error: Invalid TOML - {e}", file=sys.stderr)
            return None


class MarkdownHandler(InputHandler):
    """Handle Markdown with YAML frontmatter."""

    def parse(self, content: str) -> dict | None:
        """Parse Markdown content, extracting YAML frontmatter and body."""
        lines = content.split("\n")
        frontmatter = {}
        body_start = 0

        if lines and lines[0].strip() == "---":
            end_index = None
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    end_index = i
                    break

            if end_index is not None:
                frontmatter_content = "\n".join(lines[1:end_index])
                if frontmatter_content.strip():
                    try:
                        frontmatter = yaml.safe_load(frontmatter_content) or {}
                    except yaml.YAMLError as e:
                        print(
                            f"Error: Invalid YAML in frontmatter - {e}", file=sys.stderr
                        )
                        return None
                body_start = end_index + 1

        body = "\n".join(lines[body_start:])
        return {"frontmatter": frontmatter, "body": body}

    def remove_metadata(self, data: dict) -> dict:
        """Remove metadata from frontmatter section."""
        if isinstance(data, dict) and "frontmatter" in data:
            frontmatter = data["frontmatter"]
            if isinstance(frontmatter, dict) and "metadata" in frontmatter:
                new_frontmatter = {
                    k: v for k, v in frontmatter.items() if k != "metadata"
                }
                if self.verbose:
                    print("  Removed 'metadata' from frontmatter", file=sys.stderr)
                return {"frontmatter": new_frontmatter, "body": data.get("body", "")}
        return data


class PlainTextHandler(InputHandler):
    """Handle plain text pass-through."""

    def parse(self, content: str) -> dict:
        """Wrap plain text content in a dict structure."""
        return {"content": content}

    def remove_metadata(self, data: dict) -> dict:
        """Plain text has no metadata to remove."""
        return data


class HandlerFactory:
    """Factory to create appropriate handler based on format."""

    HANDLERS = {
        "json": JsonHandler,
        "yaml": YamlHandler,
        "toml": TomlHandler,
        "markdown": MarkdownHandler,
        "text": PlainTextHandler,
    }

    @classmethod
    def create(cls, format_type: str, verbose: bool = False) -> InputHandler:
        """Create a handler for the specified format."""
        handler_class = cls.HANDLERS.get(format_type)
        if handler_class is None:
            raise ValueError(f"Unsupported format: {format_type}")
        return handler_class(verbose=verbose)


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
  %(prog)s prompt.json                        # Auto-detect JSON, YAML-like output
  %(prog)s prompt.yaml                        # Auto-detect YAML input
  %(prog)s config.toml                        # Auto-detect TOML input
  %(prog)s doc.md                             # Auto-detect Markdown with frontmatter
  %(prog)s prompt.json --output-format plain  # Extract text values only
  %(prog)s --stdin --input-format yaml        # Read YAML from stdin
  %(prog)s prompt.json --verbose              # Show processing details
""",
        )
        parser.add_argument(
            "file",
            nargs="?",
            help="Path to prompt file (JSON, YAML, TOML, Markdown, or text)",
        )
        parser.add_argument(
            "--stdin",
            action="store_true",
            default=False,
            help="Read input from stdin instead of file",
        )
        parser.add_argument(
            "--input-format",
            choices=["json", "yaml", "toml", "markdown", "text"],
            default=None,
            help="Input format (auto-detected from extension if not specified)",
        )
        parser.add_argument(
            "--output-format",
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

        # Detect input format
        input_format = FormatDetector.detect(args.file, args.input_format)
        if args.verbose:
            print(f"  Detected input format: {input_format}", file=sys.stderr)

        # Process content with appropriate handler
        handler = HandlerFactory.create(input_format, verbose=args.verbose)
        data = handler.parse(content)

        if data is None:
            sys.exit(1)

        # Remove metadata if present
        if isinstance(data, dict):
            data = handler.remove_metadata(data)

        # Generate output
        if args.output_format == "yaml":
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
