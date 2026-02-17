#!/usr/bin/env python3
"""Extract readable text from HTML and MHTML files.

Handles plain HTML and MHTML (multipart MIME with quoted-printable encoding).
Auto-detects format based on content headers.

Usage:
    extract_html_text.py INPUT_FILE [--output OUTPUT_FILE]

Exit codes:
    0 - Success
    1 - File not found or read error
"""

import argparse
import email
import email.policy
import quopri
import re
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
        raw_content = input_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error reading '{input_path}': {exc}", file=sys.stderr)
        return 1

    if is_mhtml(raw_content):
        html_content = extract_html_from_mhtml(raw_content)
    else:
        html_content = raw_content

    text = extract_text(html_content)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    return 0


def is_mhtml(content: str) -> bool:
    """Detect whether content is MHTML (multipart MIME) rather than plain HTML.

    MHTML files start with email-style headers (From:, MIME-Version:),
    not HTML markup. Plain HTML starts with '<' or whitespace then '<'.
    """
    stripped = content.lstrip()
    if not stripped:
        return False
    # HTML always starts with a tag; MHTML starts with RFC 822 headers
    if stripped.startswith("<"):
        return False
    first_line = stripped.split("\n", 1)[0]
    return first_line.startswith(("From:", "MIME-Version:"))


def extract_html_from_mhtml(mhtml_content: str) -> str:
    """Extract and decode the first text/html part from an MHTML string.

    Parses the MIME multipart structure, finds the text/html part,
    and decodes quoted-printable encoding to produce clean HTML.

    Returns empty string if no text/html part is found.
    """
    msg = email.message_from_string(mhtml_content, policy=email.policy.default)

    # Walk all MIME parts looking for text/html
    for part in msg.walk():
        if part.get_content_type() != "text/html":
            continue

        payload = part.get_payload(decode=False)
        if not payload:
            continue

        # Handle quoted-printable encoding manually for precise control
        cte = part.get("Content-Transfer-Encoding", "").lower()
        if isinstance(payload, str) and cte == "quoted-printable":
            decoded_bytes = quopri.decodestring(payload.encode("ascii", errors="replace"))
            return decoded_bytes.decode("utf-8", errors="replace")

        if isinstance(payload, bytes):
            return payload.decode("utf-8", errors="replace")

        return str(payload)

    return ""


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
_SKIP_TAGS = frozenset({"script", "style", "noscript", "svg"})


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
