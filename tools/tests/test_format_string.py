import sys
from unittest.mock import patch

import pytest

from tools.scripts.format_string import format_string, main


# ======================
# Unit Tests: format_string
# ======================


class TestFormatString:
    """Contract: format_string(input, trunc=False, trunc_len=50) → URL-safe,
    filesystem-friendly slug. Guarantees:
    - Known file extensions (.pdf, .epub, .tar.gz, etc.) are stripped before formatting
    - Output contains only lowercase alphanumeric chars and underscores
    - No leading/trailing underscores, no consecutive underscores
    - Truncation is opt-in (off by default); when enabled, len(output) <= trunc_len
    - Empty input is undefined (raises IndexError)
    """

    def test_converts_to_lowercase(self):
        assert format_string("Hello World") == "hello_world"

    def test_strips_file_extension(self):
        assert format_string("My Book Title.pdf") == "my_book_title"
        assert format_string("Deep Learning.epub") == "deep_learning"
        assert format_string("notes.txt") == "notes"

    def test_strips_compound_extension(self):
        """Contract: compound extensions like .tar.gz are stripped as a unit."""
        result = format_string("archive.tar.gz")
        assert "tar" not in result
        assert "gz" not in result

    def test_preserves_dots_in_middle(self):
        """Contract: dots not at file-extension position are replaced with _."""
        assert format_string("v2.0 release notes") == "v2_0_release_notes"

    def test_replaces_ampersand_with_and(self):
        assert format_string("Rock & Roll") == "rock_and_roll"

    def test_removes_the_prefix(self):
        assert format_string("The Quick Brown Fox") == "quick_brown_fox"

    def test_removes_parentheses(self):
        assert format_string("Hello (World)") == "hello_world"

    def test_removes_hash_symbols(self):
        assert format_string("# Header") == "header"
        assert format_string("#hashtag") == "hashtag"

    def test_removes_backticks(self):
        assert format_string("`code`") == "code"

    def test_removes_tilde(self):
        assert format_string("~approximately") == "approximately"

    def test_removes_dollar_sign(self):
        assert format_string("$100") == "100"

    def test_removes_percent_sign(self):
        assert format_string("100%") == "100"

    def test_removes_at_sign(self):
        assert format_string("user@email") == "useremail"

    def test_removes_various_quotes(self):
        assert format_string('"quoted"') == "quoted"
        assert format_string("'single'") == "single"
        assert format_string("\u201cspecial\u201d") == "special"  # smart quotes

    @pytest.mark.parametrize("symbol", [".", ",", ";", ":", "!", "?"])
    def test_replaces_punctuation_with_underscore(self, symbol):
        assert format_string(f"hello{symbol}world") == "hello_world"

    def test_replaces_dash_with_underscore(self):
        assert format_string("hello-world") == "hello_world"

    def test_replaces_en_dash_with_underscore(self):
        assert format_string("hello\u2013world") == "hello_world"

    def test_replaces_slashes_with_underscore(self):
        assert format_string("hello/world") == "hello_world"
        assert format_string("hello\\world") == "hello_world"

    def test_replaces_pipe_with_underscore(self):
        assert format_string("hello|world") == "hello_world"

    def test_replaces_angle_brackets_with_underscore(self):
        assert format_string("hello<world>") == "hello_world"

    def test_replaces_asterisk_with_underscore(self):
        assert format_string("hello*world") == "hello_world"

    def test_replaces_spaces_with_underscores(self):
        assert format_string("hello world") == "hello_world"

    def test_collapses_multiple_underscores(self):
        assert format_string("hello___world") == "hello_world"
        assert format_string("hello - world") == "hello_world"

    def test_strips_trailing_underscores(self):
        # Note: leading underscores from input are preserved after space->underscore conversion
        # The strip("_") in the code only strips underscores created during processing
        assert format_string("_hello_") == "hello"

    def test_no_truncation_by_default(self):
        """Contract: truncation is off by default — output preserves full length."""
        long_input = "a" * 100
        result = format_string(long_input)
        assert len(result) > 50

    def test_truncates_when_enabled(self):
        """Contract: trunc=True limits output to at most trunc_len."""
        long_input = "a" * 100
        result = format_string(long_input, trunc=True)
        assert len(result) <= 50

    def test_truncates_to_custom_length(self):
        """Contract: trunc_len overrides the default limit."""
        long_input = "a" * 100
        result = format_string(long_input, trunc=True, trunc_len=30)
        assert len(result) <= 30

    def test_no_truncation_when_shorter_than_limit(self):
        """Contract: strings shorter than trunc_len pass through unchanged."""
        result = format_string("hello", trunc=True, trunc_len=50)
        assert result == "hello"

    def test_removes_trailing_underscore_after_truncation(self):
        """Contract: output never ends with underscore, even after truncation."""
        result = format_string("a" * 49 + " b", trunc=True)
        assert not result.endswith("_")

    def test_empty_string(self):
        # Edge case - may raise IndexError on line 84
        # This documents current behavior
        with pytest.raises(IndexError):
            format_string("")

    def test_complex_string(self):
        result = format_string("The Quick & Brown Fox: A Story!")
        assert result == "quick_and_brown_fox_a_story"

    def test_url_friendly_output(self):
        result = format_string("Hello, World! How are you?")
        # Should only contain lowercase letters and underscores
        assert all(c.isalnum() or c == "_" for c in result)


# ======================
# Unit Tests: main
# ======================


class TestMain:
    """Contract: CLI accepts a positional string and optional --trunc/--trunc-len flags."""

    def test_exits_nonzero_with_no_args(self):
        """Contract: missing required argument exits with non-zero status."""
        with patch.object(sys, "argv", ["format_string.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_prints_formatted_string_with_arg(self, capsys):
        with patch.object(sys, "argv", ["format_string.py", "Hello World"]):
            main()
        captured = capsys.readouterr()
        assert captured.out.strip() == "hello_world"

    def test_handles_special_characters(self, capsys):
        with patch.object(sys, "argv", ["format_string.py", "Rock & Roll!"]):
            main()
        captured = capsys.readouterr()
        assert captured.out.strip() == "rock_and_roll"

    def test_trunc_flag_limits_output(self, capsys):
        """Contract: --trunc flag enables truncation."""
        long_input = "a" * 100
        with patch.object(sys, "argv", ["format_string.py", "--trunc", long_input]):
            main()
        captured = capsys.readouterr()
        assert len(captured.out.strip()) <= 50

    def test_trunc_len_flag(self, capsys):
        """Contract: --trunc-len sets custom limit."""
        long_input = "a" * 100
        with patch.object(
            sys, "argv", ["format_string.py", "--trunc", "--trunc-len", "20", long_input]
        ):
            main()
        captured = capsys.readouterr()
        assert len(captured.out.strip()) <= 20
