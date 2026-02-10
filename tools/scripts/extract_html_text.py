#!/usr/bin/env python3
"""Extract readable text from HTML files, stripping scripts, styles, and markup.

Usage:
    extract_html_text.py INPUT_FILE [--output OUTPUT_FILE]

Exit codes:
    0 - Success
    1 - File not found or read error
"""

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse arguments, extract text, write output."""
    parser = argparse.ArgumentParser(
        description="Extract readable text from an HTML file."
    )
    parser.add_argument("input", help="Path to the HTML file")
    parser.add_argument("--output", help="Write output to file instead of stdout")
    args = parser.parse_args(argv)

    input_path = Path(args.input)

    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a file or does not exist.", file=sys.stderr)
        return 1

    try:
        html_content = input_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error reading '{input_path}': {exc}", file=sys.stderr)
        return 1

    text = extract_text(html_content)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    return 0


def extract_text(html: str) -> str:
    """Extract plain text from an HTML string.

    Strips <script>, <style>, and <noscript> tags along with their content.
    Preserves text from all other elements. Decodes HTML entities.

    Args:
        html: Raw HTML string.

    Returns:
        Extracted plain text with whitespace normalized between blocks.
    """
    extractor = _TextExtractor()
    extractor.feed(html)
    return extractor.get_text()


# Tags whose content should be completely discarded
_SKIP_TAGS = frozenset({"script", "style", "noscript"})


class _TextExtractor(HTMLParser):
    """SAX-style HTML parser that collects text, skipping script/style/noscript."""

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._pieces.append(data)

    def handle_entityref(self, name: str) -> None:
        from html import unescape

        if self._skip_depth == 0:
            self._pieces.append(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        from html import unescape

        if self._skip_depth == 0:
            self._pieces.append(unescape(f"&#{name};"))

    def get_text(self) -> str:
        """Join collected text pieces, normalizing excessive blank lines."""
        raw = "".join(self._pieces)
        # Collapse runs of 3+ newlines into 2
        lines = raw.split("\n")
        result: list[str] = []
        blank_count = 0
        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        return "\n".join(result)


if __name__ == "__main__":
    sys.exit(main())
