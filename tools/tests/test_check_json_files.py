import sys
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.scripts.check_json_files import (
    FileFinder,
    JsonError,
    JsonValidator,
    JsonValidatorCLI,
    Reporter,
)


# ======================
# Unit Tests: JsonValidator
# ======================


class TestJsonValidator:
    @pytest.fixture
    def validator(self):
        return JsonValidator(verbose=False)

    def test_valid_json_object(self, validator, tmp_path):
        file = tmp_path / "valid.json"
        file.write_text('{"key": "value"}', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is None

    def test_valid_json_array(self, validator, tmp_path):
        file = tmp_path / "valid.json"
        file.write_text('[1, 2, 3]', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is None

    def test_valid_json_nested(self, validator, tmp_path):
        file = tmp_path / "valid.json"
        content = '{"nested": {"array": [1, 2, 3], "object": {"a": "b"}}}'
        file.write_text(content, encoding="utf-8")
        error = validator.validate_file(file)
        assert error is None

    def test_valid_json_with_unicode(self, validator, tmp_path):
        file = tmp_path / "valid.json"
        file.write_text('{"emoji": "🎉", "text": "Привет"}', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is None

    def test_empty_file_passes(self, validator, tmp_path):
        file = tmp_path / "empty.json"
        file.write_text("", encoding="utf-8")
        error = validator.validate_file(file)
        assert error is None

    def test_whitespace_only_file_passes(self, validator, tmp_path):
        file = tmp_path / "whitespace.json"
        file.write_text("   \n\t  ", encoding="utf-8")
        error = validator.validate_file(file)
        assert error is None

    def test_missing_closing_brace(self, validator, tmp_path):
        file = tmp_path / "invalid.json"
        file.write_text('{"key": "value"', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is not None
        assert error.file_path == file
        assert "Expecting" in error.message or "End of data" in error.message

    def test_missing_closing_bracket(self, validator, tmp_path):
        file = tmp_path / "invalid.json"
        file.write_text('[1, 2, 3', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is not None
        assert error.file_path == file

    def test_trailing_comma(self, validator, tmp_path):
        file = tmp_path / "invalid.json"
        file.write_text('{"key": "value",}', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is not None
        assert error.file_path == file

    def test_single_quotes_invalid(self, validator, tmp_path):
        file = tmp_path / "invalid.json"
        file.write_text("{'key': 'value'}", encoding="utf-8")
        error = validator.validate_file(file)
        assert error is not None
        assert error.file_path == file

    def test_unquoted_key_invalid(self, validator, tmp_path):
        file = tmp_path / "invalid.json"
        file.write_text('{key: "value"}', encoding="utf-8")
        error = validator.validate_file(file)
        assert error is not None
        assert error.file_path == file

    def test_reports_line_number(self, validator, tmp_path):
        file = tmp_path / "invalid.json"
        content = '{\n  "valid": true,\n  "invalid": ,\n}'
        file.write_text(content, encoding="utf-8")
        error = validator.validate_file(file)
        assert error is not None
        assert error.line == 3

    def test_handles_binary_file(self, validator, tmp_path):
        binary_file = tmp_path / "binary.json"
        binary_file.write_bytes(b"\xff\xfe\x00\x01")
        error = validator.validate_file(binary_file)
        assert error is not None
        assert "encoding error" in error.message.lower() or "decode" in error.message.lower()

    def test_handles_missing_file(self, validator, tmp_path):
        missing = tmp_path / "missing.json"
        error = validator.validate_file(missing)
        assert error is not None
        assert "Cannot read file" in error.message

    def test_verbose_output_valid(self, tmp_path, capsys):
        validator = JsonValidator(verbose=True)
        file = tmp_path / "valid.json"
        file.write_text('{"test": true}', encoding="utf-8")
        validator.validate_file(file)
        captured = capsys.readouterr()
        assert "OK" in captured.out

    def test_verbose_output_empty(self, tmp_path, capsys):
        validator = JsonValidator(verbose=True)
        file = tmp_path / "empty.json"
        file.write_text("", encoding="utf-8")
        validator.validate_file(file)
        captured = capsys.readouterr()
        assert "SKIP (empty file)" in captured.out


# ======================
# Unit Tests: FileFinder
# ======================


class TestFileFinder:
    def test_finds_json_files(self, tmp_path):
        (tmp_path / "file1.json").touch()
        (tmp_path / "file2.json").touch()
        (tmp_path / "file3.txt").touch()  # Not JSON

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 2
        filenames = {f.name for f in files}
        assert filenames == {"file1.json", "file2.json"}

    def test_finds_nested_json_files(self, tmp_path):
        (tmp_path / "file1.json").touch()
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "file2.json").touch()
        (tmp_path / "sub" / "deep").mkdir()
        (tmp_path / "sub" / "deep" / "file3.json").touch()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 3
        filenames = {f.name for f in files}
        assert filenames == {"file1.json", "file2.json", "file3.json"}

    def test_find_skips_directories(self, tmp_path):
        # Create a directory named 'test.json'
        (tmp_path / "test.json").mkdir()
        (tmp_path / "real.json").touch()
        
        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)
        assert len(files) == 1
        assert files[0].name == "real.json"

    def test_excludes_git_directory(self, tmp_path):
        (tmp_path / "file.json").touch()
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config.json").touch()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 1
        assert files[0].name == "file.json"

    def test_excludes_node_modules(self, tmp_path):
        (tmp_path / "file.json").touch()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.json").touch()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 1
        assert files[0].name == "file.json"

    def test_excludes_venv(self, tmp_path):
        (tmp_path / "file.json").touch()
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "pyvenv.json").touch()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 1
        assert files[0].name == "file.json"

    def test_excludes_pycache(self, tmp_path):
        (tmp_path / "file.json").touch()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.json").touch()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 1
        assert files[0].name == "file.json"

    def test_verbose_excludes(self, tmp_path, capsys):
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.json").touch()

        finder = FileFinder(verbose=True)
        finder.find(tmp_path)

        captured = capsys.readouterr()
        assert "EXCLUDING" in captured.out

    def test_empty_directory(self, tmp_path):
        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)
        assert files == []


# ======================
# Unit Tests: Reporter
# ======================


class TestReporter:
    def test_report_with_errors_exits_1(self, tmp_path, capsys):
        errors = [
            JsonError(
                file_path=tmp_path / "test.json",
                line=10,
                message="Unexpected token",
            )
        ]
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(errors)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "validation error(s) found" in captured.out
        assert "test.json:10" in captured.out

    def test_report_multiple_errors(self, tmp_path, capsys):
        errors = [
            JsonError(file_path=tmp_path / "a.json", line=1, message="Error 1"),
            JsonError(file_path=tmp_path / "b.json", line=5, message="Error 2"),
        ]
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(errors)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "2 JSON validation error(s) found" in captured.out

    def test_report_no_errors_exits_0(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report([], verbose=True)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "All JSON files are valid" in captured.out

    def test_report_no_errors_quiet(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report([], verbose=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out == ""


# ======================
# Integration Tests: JsonValidatorCLI
# ======================


class TestJsonValidatorCLI:
    @pytest.fixture
    def cli(self):
        return JsonValidatorCLI()

    def test_valid_file_exits_0(self, cli, tmp_path):
        file = tmp_path / "valid.json"
        file.write_text('{"key": "value"}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0

    def test_invalid_file_exits_1(self, cli, tmp_path, capsys):
        file = tmp_path / "invalid.json"
        file.write_text('{"key": }', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "validation error(s) found" in captured.out

    def test_run_with_directory_in_files(self, cli, tmp_path):
        # Passing a directory in the files list should be skipped by is_file check
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(subdir)])
        assert exc_info.value.code == 0

    def test_multiple_files_all_valid(self, cli, tmp_path):
        file1 = tmp_path / "file1.json"
        file1.write_text('{"a": 1}', encoding="utf-8")
        file2 = tmp_path / "file2.json"
        file2.write_text('[1, 2, 3]', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file1), str(file2)])
        assert exc_info.value.code == 0

    def test_multiple_files_one_invalid(self, cli, tmp_path, capsys):
        file1 = tmp_path / "valid.json"
        file1.write_text('{"a": 1}', encoding="utf-8")
        file2 = tmp_path / "invalid.json"
        file2.write_text('{bad}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file1), str(file2)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "invalid.json" in captured.out

    def test_verbose_output(self, cli, tmp_path, capsys):
        file = tmp_path / "valid.json"
        file.write_text('{"test": true}', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose", str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Checking 1 file(s)" in captured.out
        assert "All JSON files are valid" in captured.out

    def test_missing_file_warning(self, cli, tmp_path, capsys):
        missing = tmp_path / "missing.json"

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(missing)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "File does not exist" in captured.err

    def test_directory_scan_mode(self, cli, tmp_path, monkeypatch, capsys):
        (tmp_path / "test.json").write_text('{"a": 1}', encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Scanning" in captured.out

    def test_directory_scan_finds_nested(self, cli, tmp_path, monkeypatch, capsys):
        (tmp_path / "root.json").write_text('{"a": 1}', encoding="utf-8")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.json").write_text('{"b": 2}', encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "2 JSON file(s)" in captured.out


# ======================
# Parametrized Edge Cases
# ======================


@pytest.mark.parametrize(
    "content,is_valid",
    [
        # Valid JSON
        ('{"key": "value"}', True),
        ('[1, 2, 3]', True),
        ('"string"', True),
        ('123', True),
        ('true', True),
        ('false', True),
        ('null', True),
        ('{"nested": {"a": [1, 2, 3]}}', True),
        # Invalid JSON
        ('{"key": }', False),
        ('{key: "value"}', False),
        ("{'key': 'value'}", False),
        ('{"key": "value",}', False),
        ('[1, 2, 3,]', False),
        ('{', False),
        ('[', False),
        ('undefined', False),
        ("{'single': 'quotes'}", False),
    ],
)
def test_json_validation_edge_cases(tmp_path, content, is_valid):
    file = tmp_path / "test.json"
    file.write_text(content, encoding="utf-8")
    validator = JsonValidator(verbose=False)
    error = validator.validate_file(file)
    assert (error is None) == is_valid


# ======================
# Main Entry Point Test
# ======================


def test_main_entry_point():
    # Cover the __main__ block
    with patch("sys.argv", ["check_json_files.py", "--help"]), pytest.raises(SystemExit):
        runpy.run_path("tools/scripts/check_json_files.py", run_name="__main__")

    with patch("tools.scripts.check_json_files.JsonValidatorCLI.run") as mock_run:
        from tools.scripts.check_json_files import main
        main()
        mock_run.assert_called_once_with()
