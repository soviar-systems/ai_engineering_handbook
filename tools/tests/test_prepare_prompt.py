import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.scripts.prepare_prompt import (
    FormatDetector,
    HandlerFactory,
    InputHandler,
    JsonHandler,
    MarkdownHandler,
    PlainTextHandler,
    PreparePromptCLI,
    Reporter,
    TomlHandler,
    YamlHandler,
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
            cli.run([str(file), "--output-format", "plain"])
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
                cli.run(["--stdin", "--output-format", "plain"])
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
            cli.run([str(file), "--output-format", "plain"])
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


# ======================
# Unit Tests: FormatDetector
# ======================


class TestFormatDetector:
    def test_detect_json_extension(self):
        assert FormatDetector.detect("prompt.json", None) == "json"

    def test_detect_yaml_extension(self):
        assert FormatDetector.detect("prompt.yaml", None) == "yaml"

    def test_detect_yml_extension(self):
        assert FormatDetector.detect("prompt.yml", None) == "yaml"

    def test_detect_toml_extension(self):
        assert FormatDetector.detect("config.toml", None) == "toml"

    def test_detect_markdown_extension(self):
        assert FormatDetector.detect("doc.md", None) == "markdown"

    def test_detect_txt_extension(self):
        assert FormatDetector.detect("readme.txt", None) == "text"

    def test_explicit_format_overrides_extension(self):
        assert FormatDetector.detect("prompt.json", "yaml") == "yaml"

    def test_unknown_extension_defaults_to_json(self):
        assert FormatDetector.detect("file.unknown", None) == "json"

    def test_no_extension_defaults_to_json(self):
        assert FormatDetector.detect("Makefile", None) == "json"

    def test_path_with_directories(self):
        assert FormatDetector.detect("/path/to/file.yaml", None) == "yaml"


# ======================
# Unit Tests: InputHandler (ABC)
# ======================


class TestInputHandler:
    def test_is_abstract_class(self):
        with pytest.raises(TypeError):
            InputHandler()

    def test_shared_strip_chars_constant(self):
        assert InputHandler.STRIP_CHARS == "*'\"\\`#"


# ======================
# Unit Tests: YamlHandler
# ======================


class TestYamlHandler:
    @pytest.fixture
    def handler(self):
        return YamlHandler(verbose=False)

    def test_parse_valid_yaml_simple(self, handler):
        result = handler.parse("key: value")
        assert result == {"key": "value"}

    def test_parse_valid_yaml_with_list(self, handler):
        content = "key: value\nlist:\n  - item1\n  - item2"
        result = handler.parse(content)
        assert result == {"key": "value", "list": ["item1", "item2"]}

    def test_parse_valid_yaml_nested(self, handler):
        content = "outer:\n  inner: value"
        result = handler.parse(content)
        assert result == {"outer": {"inner": "value"}}

    def test_parse_invalid_yaml_returns_none(self, handler, capsys):
        result = handler.parse("key: [invalid")
        assert result is None
        captured = capsys.readouterr()
        assert "Error: Invalid YAML" in captured.err

    def test_remove_metadata_from_yaml(self, handler):
        data = {"metadata": {"version": "1.0"}, "content": "Hello"}
        result = handler.remove_metadata(data)
        assert result == {"content": "Hello"}
        assert "metadata" not in result

    def test_to_yaml_like_output(self, handler):
        data = {"key": "value"}
        result = handler.to_yaml_like(data)
        assert result == "key: value"

    def test_to_plain_text_output(self, handler):
        data = {"key": "value", "list": ["a", "b"]}
        result = handler.to_plain_text(data)
        assert "value" in result
        assert "a" in result
        assert "b" in result


# ======================
# Unit Tests: TomlHandler
# ======================


class TestTomlHandler:
    @pytest.fixture
    def handler(self):
        return TomlHandler(verbose=False)

    def test_parse_valid_toml_simple(self, handler):
        result = handler.parse('key = "value"')
        assert result == {"key": "value"}

    def test_parse_valid_toml_with_section(self, handler):
        content = '[section]\nkey = "value"'
        result = handler.parse(content)
        assert result == {"section": {"key": "value"}}

    def test_parse_valid_toml_nested(self, handler):
        content = '[section]\nkey = "value"\n\n[section.sub]\ninner = 42'
        result = handler.parse(content)
        assert result == {"section": {"key": "value", "sub": {"inner": 42}}}

    def test_parse_invalid_toml_returns_none(self, handler, capsys):
        result = handler.parse("key = [invalid")
        assert result is None
        captured = capsys.readouterr()
        assert "Error: Invalid TOML" in captured.err

    def test_remove_metadata_table(self, handler):
        data = {"metadata": {"version": "1.0"}, "content": {"key": "value"}}
        result = handler.remove_metadata(data)
        assert result == {"content": {"key": "value"}}
        assert "metadata" not in result

    def test_to_yaml_like_output(self, handler):
        data = {"key": "value"}
        result = handler.to_yaml_like(data)
        assert result == "key: value"


# ======================
# Unit Tests: MarkdownHandler
# ======================


class TestMarkdownHandler:
    @pytest.fixture
    def handler(self):
        return MarkdownHandler(verbose=False)

    def test_parse_markdown_with_frontmatter(self, handler):
        content = "---\ntitle: Test\nauthor: Me\n---\n# Body Content"
        result = handler.parse(content)
        assert "frontmatter" in result
        assert "body" in result
        assert result["frontmatter"]["title"] == "Test"
        assert result["frontmatter"]["author"] == "Me"
        assert "# Body Content" in result["body"]

    def test_parse_markdown_without_frontmatter(self, handler):
        content = "# Just a heading\n\nSome text here."
        result = handler.parse(content)
        assert result["frontmatter"] == {}
        assert "# Just a heading" in result["body"]
        assert "Some text here" in result["body"]

    def test_parse_markdown_empty_frontmatter(self, handler):
        content = "---\n---\n# Body"
        result = handler.parse(content)
        assert result["frontmatter"] == {}
        assert "# Body" in result["body"]

    def test_parse_invalid_frontmatter_yaml(self, handler, capsys):
        content = "---\ninvalid: [broken\n---\n# Body"
        result = handler.parse(content)
        assert result is None
        captured = capsys.readouterr()
        assert "Error: Invalid YAML in frontmatter" in captured.err

    def test_remove_metadata_from_frontmatter(self, handler):
        data = {
            "frontmatter": {"title": "Test", "metadata": {"version": "1.0"}},
            "body": "# Content",
        }
        result = handler.remove_metadata(data)
        assert "metadata" not in result["frontmatter"]
        assert result["frontmatter"]["title"] == "Test"
        assert result["body"] == "# Content"

    def test_to_yaml_like_output(self, handler):
        data = {"frontmatter": {"title": "Test"}, "body": "# Content"}
        result = handler.to_yaml_like(data)
        assert "frontmatter:" in result
        assert "title: Test" in result
        assert "body:" in result

    def test_to_plain_text_output(self, handler):
        data = {"frontmatter": {"title": "Test"}, "body": "Content here"}
        result = handler.to_plain_text(data)
        assert "Test" in result
        assert "Content here" in result


# ======================
# Unit Tests: PlainTextHandler
# ======================


class TestPlainTextHandler:
    @pytest.fixture
    def handler(self):
        return PlainTextHandler(verbose=False)

    def test_parse_returns_dict_with_content(self, handler):
        result = handler.parse("Just some text content")
        assert result == {"content": "Just some text content"}

    def test_parse_preserves_multiline(self, handler):
        content = "Line 1\nLine 2\nLine 3"
        result = handler.parse(content)
        assert result == {"content": content}

    def test_remove_metadata_does_nothing(self, handler):
        data = {"content": "text"}
        result = handler.remove_metadata(data)
        assert result == {"content": "text"}

    def test_to_yaml_like_output(self, handler):
        data = {"content": "some text"}
        result = handler.to_yaml_like(data)
        assert "content: some text" in result

    def test_to_plain_text_output(self, handler):
        data = {"content": "some text here"}
        result = handler.to_plain_text(data)
        assert "some text here" in result


# ======================
# Unit Tests: HandlerFactory
# ======================


class TestHandlerFactory:
    def test_create_json_handler(self):
        handler = HandlerFactory.create("json")
        assert isinstance(handler, JsonHandler)

    def test_create_yaml_handler(self):
        handler = HandlerFactory.create("yaml")
        assert isinstance(handler, YamlHandler)

    def test_create_toml_handler(self):
        handler = HandlerFactory.create("toml")
        assert isinstance(handler, TomlHandler)

    def test_create_markdown_handler(self):
        handler = HandlerFactory.create("markdown")
        assert isinstance(handler, MarkdownHandler)

    def test_create_text_handler(self):
        handler = HandlerFactory.create("text")
        assert isinstance(handler, PlainTextHandler)

    def test_create_with_verbose(self):
        handler = HandlerFactory.create("json", verbose=True)
        assert handler.verbose is True

    def test_create_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            HandlerFactory.create("unknown")


# ======================
# Integration Tests: CLI with New Input Formats
# ======================


class TestPreparePromptCLIInputFormats:
    @pytest.fixture
    def cli(self):
        return PreparePromptCLI()

    def test_yaml_file_auto_detected(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.yaml"
        file.write_text("key: value\nlist:\n  - item1", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_toml_file_auto_detected(self, cli, tmp_path, capsys):
        file = tmp_path / "config.toml"
        file.write_text('[section]\nkey = "value"', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "section:" in captured.out
        assert "key: value" in captured.out

    def test_markdown_file_auto_detected(self, cli, tmp_path, capsys):
        file = tmp_path / "doc.md"
        file.write_text("---\ntitle: Test\n---\n# Content", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "title: Test" in captured.out

    def test_txt_file_auto_detected(self, cli, tmp_path, capsys):
        file = tmp_path / "readme.txt"
        file.write_text("Plain text content", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "content: Plain text content" in captured.out

    def test_explicit_input_format_overrides_extension(self, cli, tmp_path, capsys):
        # File has .json extension but contains YAML
        file = tmp_path / "prompt.json"
        file.write_text("key: value", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file), "--input-format", "yaml"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_stdin_with_input_format_yaml(self, cli, capsys):
        mock_stdin = io.StringIO("key: value")

        with patch.object(sys, "stdin", mock_stdin):
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--stdin", "--input-format", "yaml"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_stdin_defaults_to_json(self, cli, capsys):
        mock_stdin = io.StringIO('{"key": "value"}')

        with patch.object(sys, "stdin", mock_stdin):
            with pytest.raises(SystemExit) as exc_info:
                cli.run(["--stdin"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_output_format_plain(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.yaml"
        file.write_text("key: value", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file), "--output-format", "plain"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "value"

    def test_yaml_metadata_removed(self, cli, tmp_path, capsys):
        file = tmp_path / "prompt.yaml"
        content = "metadata:\n  version: 1.0\nprompt: Hello"
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "metadata" not in captured.out
        assert "prompt: Hello" in captured.out

    def test_toml_metadata_removed(self, cli, tmp_path, capsys):
        file = tmp_path / "config.toml"
        content = '[metadata]\nversion = "1.0"\n\n[content]\nkey = "value"'
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "metadata" not in captured.out
        assert "content:" in captured.out

    def test_markdown_metadata_removed(self, cli, tmp_path, capsys):
        file = tmp_path / "doc.md"
        content = "---\ntitle: Test\nmetadata:\n  version: 1.0\n---\n# Body"
        file.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "title: Test" in captured.out
        assert "metadata" not in captured.out
