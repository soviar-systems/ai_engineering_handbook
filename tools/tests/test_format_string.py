import sys
from unittest.mock import patch

import pytest

from tools.scripts.format_string import format_string, main


# ======================
# Unit Tests: format_string
# ======================


class TestFormatString:
    def test_converts_to_lowercase(self):
        assert format_string("Hello World") == "hello_world"

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

    def test_replaces_punctuation_with_underscore(self):
        assert format_string("hello.world") == "hello_world"
        assert format_string("hello,world") == "hello_world"
        assert format_string("hello;world") == "hello_world"
        assert format_string("hello:world") == "hello_world"
        assert format_string("hello!world") == "hello_world"
        assert format_string("hello?world") == "hello_world"

    def test_replaces_dash_with_underscore(self):
        assert format_string("hello-world") == "hello_world"

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

    def test_truncates_long_strings(self):
        long_input = "a" * 100
        result = format_string(long_input)
        assert len(result) <= 50

    def test_removes_trailing_underscore_after_truncation(self):
        # Input that would have underscore at position 50
        result = format_string("a" * 49 + " b")
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
    def test_prints_usage_with_no_args(self, capsys):
        with patch.object(sys, "argv", ["format_string.py"]):
            main()
        captured = capsys.readouterr()
        assert "Usage:" in captured.out

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
