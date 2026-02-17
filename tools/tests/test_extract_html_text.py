"""
Test suite for extract_html_text.py - HTML text extraction script.

Tests are organized following the behavior-based testing principle:
- Test what the code does, not how it does it
- Use semantic assertions rather than exact string matching

Contracts tested:
- Input: path to HTML file → Output: extracted text to stdout or file
- Strips <script>, <style>, <noscript> tags and their content
- Preserves meaningful text from semantic tags (p, li, h1-h6, td, etc.)
- Handles UTF-8 encoding
- Exit 0 on success, exit 1 on file not found / read error
- --output flag writes to file instead of stdout
- Empty HTML → empty output (no crash)
- MHTML (multipart MIME): auto-detects, extracts HTML part, decodes quoted-printable
- SVG path data and base64 images are stripped from output
"""

import runpy
from pathlib import Path

import pytest

from tools.scripts.extract_html_text import (
    extract_html_from_mhtml,
    extract_text,
    is_mhtml,
    main,
)


# ======================
# Helpers
# ======================


def create_html_file(tmp_path: Path, content: str, name: str = "test.html") -> Path:
    """Create an HTML file with given content."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


# ======================
# Unit Tests: extract_text
# ======================


class TestExtractText:
    """Contract: extract_text(html_string) → plain text with tags stripped."""

    def test_extracts_paragraph_text(self):
        html = "<html><body><p>Hello world</p></body></html>"
        result = extract_text(html)
        assert "Hello world" in result

    def test_extracts_heading_text(self):
        html = "<h1>Title</h1><h2>Subtitle</h2>"
        result = extract_text(html)
        assert "Title" in result
        assert "Subtitle" in result

    def test_extracts_list_items(self):
        html = "<ul><li>Item one</li><li>Item two</li></ul>"
        result = extract_text(html)
        assert "Item one" in result
        assert "Item two" in result

    def test_extracts_table_cells(self):
        html = "<table><tr><td>Cell A</td><td>Cell B</td></tr></table>"
        result = extract_text(html)
        assert "Cell A" in result
        assert "Cell B" in result

    def test_strips_script_tags(self):
        html = "<p>Keep this</p><script>var x = 1; alert('gone');</script><p>And this</p>"
        result = extract_text(html)
        assert "Keep this" in result
        assert "And this" in result
        assert "alert" not in result
        assert "var x" not in result

    def test_strips_style_tags(self):
        html = "<p>Visible</p><style>body { color: red; }</style>"
        result = extract_text(html)
        assert "Visible" in result
        assert "color" not in result

    def test_strips_noscript_tags(self):
        html = "<p>Main</p><noscript>Enable JS</noscript>"
        result = extract_text(html)
        assert "Main" in result
        assert "Enable JS" not in result

    def test_empty_html_returns_empty(self):
        result = extract_text("")
        assert result.strip() == ""

    def test_html_with_only_tags_returns_empty(self):
        html = "<html><head><title></title></head><body></body></html>"
        result = extract_text(html)
        assert result.strip() == ""

    def test_preserves_unicode(self):
        html = "<p>Привет мир</p><p>日本語テスト</p>"
        result = extract_text(html)
        assert "Привет мир" in result
        assert "日本語テスト" in result

    def test_handles_nested_tags(self):
        html = "<div><p>Outer <strong>bold <em>italic</em></strong> text</p></div>"
        result = extract_text(html)
        assert "bold" in result
        assert "italic" in result
        assert "Outer" in result
        assert "text" in result

    def test_strips_html_entities(self):
        html = "<p>A &amp; B &lt; C</p>"
        result = extract_text(html)
        assert "A & B < C" in result

    def test_handles_numeric_char_references(self):
        html = "<p>Em dash: &#8212; and &#x2014;</p>"
        result = extract_text(html)
        assert "—" in result

    def test_multiple_script_and_style_blocks(self):
        html = (
            "<script>one</script>"
            "<p>Keep</p>"
            "<style>.a{}</style>"
            "<script>two</script>"
            "<p>Also keep</p>"
        )
        result = extract_text(html)
        assert "Keep" in result
        assert "Also keep" in result
        assert "one" not in result
        assert "two" not in result


# ======================
# Integration Tests: main() in-process
# ======================
#
# These call main() directly (not via subprocess) so coverage
# can track all code paths through argparse, file I/O, and output.


class TestMainSuccessPath:
    """Contract: valid input → exit 0."""

    def test_extracts_to_stdout(self, tmp_path, capsys):
        path = create_html_file(tmp_path, "<p>Hello main</p>")
        exit_code = main([str(path)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Hello main" in captured.out

    def test_extracts_to_output_file(self, tmp_path):
        html_path = create_html_file(tmp_path, "<p>File output</p>")
        output_path = tmp_path / "output.txt"
        exit_code = main([str(html_path), "--output", str(output_path)])
        assert exit_code == 0
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "File output" in content

    def test_empty_html_file_succeeds(self, tmp_path):
        path = create_html_file(tmp_path, "")
        assert main([str(path)]) == 0

    def test_unicode_file(self, tmp_path, capsys):
        path = create_html_file(tmp_path, "<p>Ёжик в тумане</p>")
        exit_code = main([str(path)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Ёжик" in captured.out


class TestMainErrorPath:
    """Contract: invalid input → exit 1."""

    def test_file_not_found(self, tmp_path):
        assert main([str(tmp_path / "nonexistent.html")]) == 1

    def test_directory_instead_of_file(self, tmp_path):
        assert main([str(tmp_path)]) == 1

    def test_no_arguments_raises_system_exit(self):
        # argparse calls sys.exit(2) on missing required arguments
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code != 0

    def test_main_entry_point(self, tmp_path, monkeypatch):
        """Cover the if __name__ == '__main__' block."""
        path = create_html_file(tmp_path, "<p>entry point</p>")
        monkeypatch.setattr("sys.argv", ["extract_html_text.py", str(path)])
        # runpy executes sys.exit(main()), so we catch SystemExit
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path(
                "tools/scripts/extract_html_text.py", run_name="__main__"
            )
        assert exc_info.value.code == 0


# ======================
# Helpers: MHTML test fixtures
# ======================

SAMPLE_MHTML = (
    "From: \n"
    "Subject: Test Page\n"
    "MIME-Version: 1.0\n"
    "Content-Type: multipart/related;\n"
    '\ttype="text/html";\n'
    '\tboundary="----TestBoundary----"\n'
    "\n"
    "------TestBoundary----\n"
    "Content-Type: text/html\n"
    "Content-Transfer-Encoding: quoted-printable\n"
    "Content-Location: https://example.com/page\n"
    "\n"
    "<html><body><p>Hello =D0=9C=D0=B8=D1=80</p></body></html>\n"
    "\n"
    "------TestBoundary----\n"
    "Content-Type: text/css\n"
    "Content-Transfer-Encoding: quoted-printable\n"
    "\n"
    "body { color: red; }\n"
    "\n"
    "------TestBoundary------\n"
)

SAMPLE_MHTML_WITH_SVG = (
    "From: \n"
    "MIME-Version: 1.0\n"
    "Content-Type: multipart/related;\n"
    '\tboundary="----TestBoundary----"\n'
    "\n"
    "------TestBoundary----\n"
    "Content-Type: text/html\n"
    "Content-Transfer-Encoding: quoted-printable\n"
    "\n"
    '<html><body><p>Content here</p><svg><path d=3D"M10 20 L30 40 Z"/></sv=\n'
    "g><p>More content</p></body></html>\n"
    "\n"
    "------TestBoundary------\n"
)

SAMPLE_MHTML_WITH_BASE64_IMG = (
    "From: \n"
    "MIME-Version: 1.0\n"
    "Content-Type: multipart/related;\n"
    '\tboundary="----TestBoundary----"\n'
    "\n"
    "------TestBoundary----\n"
    "Content-Type: text/html\n"
    "Content-Transfer-Encoding: quoted-printable\n"
    "\n"
    '<html><body><p>Text</p><img src=3D"data:image/png;base64,iVBORw0KGgo=3D=\n'
    '"/><p>After image</p></body></html>\n'
    "\n"
    "------TestBoundary------\n"
)


# ======================
# Unit Tests: is_mhtml
# ======================


class TestIsMhtml:
    """Contract: is_mhtml(content) → True if content is MHTML multipart format."""

    def test_detects_mhtml_with_from_header(self):
        assert is_mhtml(SAMPLE_MHTML) is True

    def test_rejects_plain_html(self):
        assert is_mhtml("<html><body><p>Hello</p></body></html>") is False

    def test_rejects_empty_string(self):
        assert is_mhtml("") is False

    def test_detects_mhtml_with_mime_version_first(self):
        content = "MIME-Version: 1.0\nContent-Type: multipart/related;\n"
        assert is_mhtml(content) is True

    def test_rejects_html_with_from_in_body(self):
        """HTML that happens to contain 'From:' in the body is not MHTML."""
        html = "<html><body>From: someone@example.com</body></html>"
        assert is_mhtml(html) is False


# ======================
# Unit Tests: extract_html_from_mhtml
# ======================


class TestExtractHtmlFromMhtml:
    """Contract: extract_html_from_mhtml(mhtml) → decoded HTML string from first text/html part."""

    def test_extracts_html_part(self):
        html = extract_html_from_mhtml(SAMPLE_MHTML)
        assert "<html>" in html or "<body>" in html

    def test_decodes_quoted_printable_utf8(self):
        html = extract_html_from_mhtml(SAMPLE_MHTML)
        # =D0=9C=D0=B8=D1=80 is "Мир" in quoted-printable UTF-8
        assert "Мир" in html

    def test_ignores_non_html_parts(self):
        html = extract_html_from_mhtml(SAMPLE_MHTML)
        assert "color: red" not in html

    def test_returns_empty_for_no_html_part(self):
        mhtml = (
            "From: \n"
            "MIME-Version: 1.0\n"
            "Content-Type: multipart/related;\n"
            '\tboundary="----TestBoundary----"\n'
            "\n"
            "------TestBoundary----\n"
            "Content-Type: text/css\n"
            "\n"
            "body { color: red; }\n"
            "\n"
            "------TestBoundary------\n"
        )
        result = extract_html_from_mhtml(mhtml)
        assert result == ""


# ======================
# Unit Tests: SVG and base64 stripping
# ======================


class TestSvgAndBase64Stripping:
    """Contract: extract_text strips SVG path data and base64 image sources."""

    def test_strips_svg_path_data(self):
        html = '<html><body><p>Content</p><svg><path d="M10 20 L30 40 Z"/></svg><p>More</p></body></html>'
        result = extract_text(html)
        assert "Content" in result
        assert "More" in result
        assert "M10 20" not in result

    def test_strips_base64_image_data(self):
        html = '<html><body><p>Text</p><img src="data:image/png;base64,iVBORw0KGgo="/><p>After</p></body></html>'
        result = extract_text(html)
        assert "Text" in result
        assert "After" in result
        assert "iVBORw0KGgo" not in result


# ======================
# Integration Tests: main() with MHTML files
# ======================


class TestMainMhtml:
    """Contract: main() auto-detects MHTML and extracts text correctly."""

    def test_extracts_text_from_mhtml_file(self, tmp_path, capsys):
        path = tmp_path / "test.mhtml"
        path.write_text(SAMPLE_MHTML, encoding="utf-8")
        exit_code = main([str(path)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Hello" in captured.out
        assert "Мир" in captured.out

    def test_mhtml_with_html_extension(self, tmp_path, capsys):
        """MHTML saved with .html extension should still be detected."""
        path = tmp_path / "page.html"
        path.write_text(SAMPLE_MHTML, encoding="utf-8")
        exit_code = main([str(path)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Hello" in captured.out

    def test_mhtml_to_output_file(self, tmp_path):
        input_path = tmp_path / "test.mhtml"
        input_path.write_text(SAMPLE_MHTML, encoding="utf-8")
        output_path = tmp_path / "output.txt"
        exit_code = main([str(input_path), "--output", str(output_path)])
        assert exit_code == 0
        content = output_path.read_text(encoding="utf-8")
        assert "Hello" in content
