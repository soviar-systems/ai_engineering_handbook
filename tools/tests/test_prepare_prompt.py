import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.scripts.prepare_prompt import (
    JsonHandler,
    PreparePromptCLI,
    Reporter,
)


# ======================
# Unit Tests: JsonHandler
# ======================


class TestJsonHandler:
    @pytest.fixture
    def handler(self):
        return JsonHandler(verbose=False)

    def test_parse_valid_json_object(self, handler):
        result = handler.parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_valid_json_array(self, handler):
        result = handler.parse('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_valid_nested_json(self, handler):
        content = '{"nested": {"array": [1, 2, 3], "object": {"a": "b"}}}'
        result = handler.parse(content)
        assert result == {"nested": {"array": [1, 2, 3], "object": {"a": "b"}}}

    def test_parse_invalid_json_returns_none(self, handler, capsys):
        result = handler.parse('{"key": }')
        assert result is None
        captured = capsys.readouterr()
        assert "Error: Invalid JSON" in captured.err

    def test_parse_empty_string_returns_none(self, handler, capsys):
        result = handler.parse("")
        assert result is None
        captured = capsys.readouterr()
        assert "Error: Invalid JSON" in captured.err

    def test_remove_metadata_from_dict(self, handler):
        data = {"metadata": {"version": "1.0"}, "prompt": "Hello"}
        result = handler.remove_metadata(data)
        assert result == {"prompt": "Hello"}
        assert "metadata" not in result

    def test_remove_metadata_preserves_other_fields(self, handler):
        data = {"metadata": {}, "a": 1, "b": 2, "c": 3}
        result = handler.remove_metadata(data)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_remove_metadata_no_metadata_field(self, handler):
        data = {"prompt": "Hello", "other": "value"}
        result = handler.remove_metadata(data)
        assert result == {"prompt": "Hello", "other": "value"}

    def test_remove_metadata_non_dict_returns_original(self, handler):
        data = [1, 2, 3]
        result = handler.remove_metadata(data)
        assert result == [1, 2, 3]

    def test_to_yaml_like_simple_dict(self, handler):
        data = {"key": "value"}
        result = handler.to_yaml_like(data)
        assert result == "key: value"

    def test_to_yaml_like_nested_dict(self, handler):
        data = {"outer": {"inner": "value"}}
        result = handler.to_yaml_like(data)
        assert "outer:" in result
        assert "  inner: value" in result

    def test_to_yaml_like_array(self, handler):
        data = {"items": ["one", "two", "three"]}
        result = handler.to_yaml_like(data)
        assert "items:" in result
        assert "  - one" in result
        assert "  - two" in result
        assert "  - three" in result

    def test_to_yaml_like_strips_special_chars(self, handler):
        data = {"key": "value with *'\"# special chars"}
        result = handler.to_yaml_like(data)
        assert "*" not in result
        assert "'" not in result
        assert '"' not in result
        assert "#" not in result

    def test_to_yaml_like_strips_backticks(self, handler):
        data = {"code": "`example`"}
        result = handler.to_yaml_like(data)
        assert "`" not in result
        assert "example" in result

    def test_to_plain_text_simple(self, handler):
        data = {"key": "value"}
        result = handler.to_plain_text(data)
        assert result == "value"

    def test_to_plain_text_nested(self, handler):
        data = {"a": "first", "b": {"c": "second"}}
        result = handler.to_plain_text(data)
        lines = result.split("\n")
        assert "first" in lines
        assert "second" in lines

    def test_to_plain_text_array(self, handler):
        data = {"items": ["one", "two", "three"]}
        result = handler.to_plain_text(data)
        lines = result.split("\n")
        assert "one" in lines
        assert "two" in lines
        assert "three" in lines

    def test_to_plain_text_strips_special_chars(self, handler):
        data = {"key": "value with *'\"# chars"}
        result = handler.to_plain_text(data)
        assert "*" not in result
        assert "'" not in result

    def test_to_plain_text_skips_empty_values(self, handler):
        data = {"key": ""}
        result = handler.to_plain_text(data)
        assert result == ""

    def test_to_plain_text_includes_numbers(self, handler):
        data = {"count": 42, "ratio": 3.14}
        result = handler.to_plain_text(data)
        assert "42" in result
        assert "3.14" in result

    def test_to_plain_text_includes_booleans(self, handler):
        data = {"flag": True, "other": False}
        result = handler.to_plain_text(data)
        assert "true" in result
        assert "false" in result


class TestJsonHandlerVerbose:
    def test_remove_metadata_verbose_output(self, capsys):
        handler = JsonHandler(verbose=True)
        data = {"metadata": {"version": "1.0"}, "prompt": "Hello"}
        handler.remove_metadata(data)
        captured = capsys.readouterr()
        assert "Removed 'metadata' field" in captured.err


# ======================
# Unit Tests: Reporter
# ======================


class TestReporter:
    def test_output_prints_to_stdout(self, capsys):
        Reporter.output("test content")
        captured = capsys.readouterr()
        assert captured.out == "test content\n"

    def test_success_exits_0(self):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.success()
        assert exc_info.value.code == 0

    def test_error_exits_1_with_message(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.error("something went wrong")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: something went wrong" in captured.err


# ======================
# Integration Tests: PreparePromptCLI
# ======================


class TestPreparePromptCLI:
    @pytest.fixture
    def cli(self):
        return PreparePromptCLI()

    def test_valid_json_file_yaml_output(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        file.write_text('{"key": "value"}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_valid_json_file_plain_output(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        file.write_text('{"key": "value"}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file), "--format", "plain"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "value" in captured.out

    def test_metadata_removed(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        content = '{"metadata": {"version": "1.0"}, "prompt": "Hello"}'
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "metadata" not in captured.out
        assert "version" not in captured.out
        assert "prompt: Hello" in captured.out

    def test_special_chars_stripped(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        content = '{"key": "value with *# chars"}'
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "*" not in captured.out
        assert "#" not in captured.out

    def test_invalid_json_exits_1(self, cli, tmp_path, capsys):
        file = tmp_path / "invalid.json"
        file.write_text('{"key": }', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    def test_file_not_found_exits_1(self, cli, tmp_path, capsys):
        missing = tmp_path / "missing.json"

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(missing)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err

    def test_empty_file_exits_1(self, cli, tmp_path, capsys):
        file = tmp_path / "empty.json"
        file.write_text("", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    def test_stdin_mode(self, cli, capsys):
        mock_stdin = io.StringIO('{"key": "value"}')

        with patch.object(sys, "stdin", mock_stdin):
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--stdin"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_stdin_with_plain_format(self, cli, capsys):
        mock_stdin = io.StringIO('{"key": "value"}')

        with patch.object(sys, "stdin", mock_stdin):
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--stdin", "--format", "plain"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "value" in captured.out

    def test_no_file_and_no_stdin_exits_1(self, cli, capsys):
        with pytest.raises(SystemExit) as exc_info:
            cli.run([])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Either provide a file path or use --stdin" in captured.err

    def test_both_file_and_stdin_exits_1(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        file.write_text('{"key": "value"}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file), "--stdin"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Cannot use both file path and --stdin" in captured.err

    def test_verbose_output(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        content = '{"metadata": {"v": "1"}, "prompt": "Hello"}'
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file), "--verbose"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Reading from file" in captured.err
        assert "Removed 'metadata' field" in captured.err

    def test_directory_not_file_exits_1(self, cli, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(tmp_path)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Not a file" in captured.err


class TestPreparePromptCLIComplexJson:
    """Test with realistic prompt file structures."""

    @pytest.fixture
    def cli(self):
        return PreparePromptCLI()

    def test_nested_structure_yaml_output(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        content = """{
            "metadata": {"id": "test", "version": "1.0"},
            "persona": {
                "role": "Assistant",
                "principles": ["Be helpful", "Be honest"]
            }
        }"""
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Metadata should be removed
        assert "metadata" not in captured.out.lower()
        assert "version" not in captured.out

        # Other content should be present
        assert "persona:" in captured.out
        assert "role: Assistant" in captured.out
        assert "- Be helpful" in captured.out
        assert "- Be honest" in captured.out

    def test_nested_structure_plain_output(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.json"
        content = """{
            "metadata": {"id": "test"},
            "persona": {"role": "Assistant"},
            "items": ["one", "two"]
        }"""
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file), "--format", "plain"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        lines = captured.out.strip().split("\n")
        assert "Assistant" in lines
        assert "one" in lines
        assert "two" in lines
        # Metadata values should NOT be present
        assert "test" not in lines


# ======================
# Main Entry Point Test
# ======================


def test_main_entry_point():
    with patch("tools.scripts.prepare_prompt.PreparePromptCLI.run") as mock_run:
        from tools.scripts.prepare_prompt import main

        main()
        mock_run.assert_called_once_with()
