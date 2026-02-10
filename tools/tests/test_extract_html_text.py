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
"""

import runpy
from pathlib import Path

import pytest

from tools.scripts.extract_html_text import extract_text, main


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
