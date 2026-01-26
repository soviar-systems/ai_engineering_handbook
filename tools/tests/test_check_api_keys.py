import sys
import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.scripts.check_api_keys import (
    ApiKeyCheckerCLI,
    ApiKeyDetector,
    ApiKeyMatch,
    ApiKeyValidator,
    FileFinder,
    Reporter,
)
from tools.scripts.paths import API_KEYS_PLACEHOLDER_INDICATORS


@pytest.fixture(autouse=True)
def mock_paths_module():
    """Patch the import of API_KEYS_PLACEHOLDER_INDICATORS."""
    with patch.dict(
        sys.modules,
        {
            "tools.scripts.paths": MagicMock(
                API_KEYS_PLACEHOLDER_INDICATORS=API_KEYS_PLACEHOLDER_INDICATORS,
            )
        },
    ):
        yield


# ======================
# Unit Tests: ApiKeyDetector
# ======================


class TestApiKeyDetector:
    @pytest.fixture
    def detector(self):
        return ApiKeyDetector(verbose=False)

    @pytest.mark.parametrize(
        "content,provider,expected_count",
        [
            # OpenAI key (sk- + 48 chars)
            ("sk-" + "a" * 48, "OpenAI", 0),  # Low entropy, should not detect
            ("sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234", "OpenAI", 1),
            # OpenAI Project key (sk-proj- + 48 chars)
            ("sk-proj-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234", "OpenAI Project", 1),
            # GROQ key (gsk_ + 48 chars)
            ("gsk_TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234", "GROQ", 1),
            # Google key (AIza + 35 chars) - must be exactly 35 chars after AIza
            ("AIzaTESTDATATESTDATATESTDATATESTDATASyBx7", "Google", 1),
            # GitHub token (gh[pousr]_ + 36 chars)
            ("ghp_TESTDATATESTDATATESTDATATESTDATA1234", "GitHub", 1),
            # Slack token (xox[bpras]- + chars) - avoid sequential pattern
            ("xoxb-TEST-TOKEN-FOR-UNIT-TESTING-PURPOSES-ONLY", "Slack", 1),
            # AWS key (AKIA + 16 chars)
            ("AKIATESTDATATESTDATA", "AWS", 1),
            # No keys
            ("This is normal text without any keys", None, 0),
            ("API_KEY=placeholder", None, 0),
        ],
    )
    def test_detect_known_patterns(self, detector, tmp_path, content, provider, expected_count):
        file = tmp_path / "test.txt"
        file.write_text(content, encoding="utf-8")
        matches = detector.detect_in_file(file)
        assert len(matches) == expected_count
        if expected_count > 0:
            assert matches[0].provider == provider

    @pytest.mark.parametrize(
        "content,should_detect",
        [
            # Placeholders should NOT be detected
            ("[API_KEY]", False),
            ("<your_api_key>", False),
            ("${OPENAI_KEY}", False),
            ("{{ api_key }}", False),
            ("sk-example1234567890abcdefghij1234567890abcdefghij12", False),
            ("sk-placeholder567890abcdefghij1234567890abcdefghij12", False),
            ("sk-your_key_here890abcdefghij1234567890abcdefghij12", False),
            ("sk-test_key_12345890abcdefghij1234567890abcdefghij12", False),
            ("sk-fake_api_key_here1290abcdefghij1234567890abcdefghij12", False),
            # Low entropy should NOT be detected
            ("sk-" + "x" * 48, False),  # All same character
            # Real-looking keys SHOULD be detected
            ("sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234", True),
        ],
    )
    def test_placeholder_detection(self, detector, tmp_path, content, should_detect):
        file = tmp_path / "test.txt"
        file.write_text(content, encoding="utf-8")
        matches = detector.detect_in_file(file)
        assert (len(matches) > 0) == should_detect

    def test_detect_handles_binary_file(self, detector, tmp_path, capsys):
        detector = ApiKeyDetector(verbose=True)
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\xff\xfe\x00\x01")
        matches = detector.detect_in_file(binary_file)
        assert matches == []
        captured = capsys.readouterr()
        assert "SKIP (binary file)" in captured.err

    def test_detect_handles_missing_file(self, detector, tmp_path, capsys):
        missing = tmp_path / "missing.txt"
        matches = detector.detect_in_file(missing)
        assert matches == []
        captured = capsys.readouterr()
        assert "Cannot read file" in captured.err

    def test_detect_multiline_file(self, detector, tmp_path):
        content = """# Config file
API_KEY=[YOUR_KEY_HERE]
SECRET=sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234
# End of config
"""
        file = tmp_path / "config.txt"
        file.write_text(content, encoding="utf-8")
        matches = detector.detect_in_file(file)
        assert len(matches) == 1
        assert matches[0].line_no == 3
        assert matches[0].provider == "OpenAI"

    def test_is_low_entropy_empty_string(self, detector):
        # Directly test the static method for coverage
        assert detector.validator._is_low_entropy("") is True

    def test_verbose_skips(self, tmp_path, capsys):
        detector = ApiKeyDetector(verbose=True)
        file = tmp_path / "test.txt"
        # First key: low entropy (51 chars total, all x after prefix)
        # Second key: contains 16-digit sequential pattern (must be 51+ chars to match)
        low_entropy_key = "sk-" + "x" * 48
        sequential_key = "sk-1234567890123456" + "a" * 32  # 51 chars with 16-digit sequence
        file.write_text(f"{low_entropy_key}\n{sequential_key}", encoding="utf-8")
        detector.detect_in_file(file)
        captured = capsys.readouterr()
        assert "SKIP (low entropy)" in captured.out
        assert "SKIP (sequential pattern)" in captured.out


# ======================
# Unit Tests: ApiKeyValidator
# ======================


class TestApiKeyValidator:
    @pytest.fixture
    def validator(self):
        return ApiKeyValidator(verbose=False)

    def test_excludes_bracket_placeholders(self, validator):
        assert validator.is_real_key("[API_KEY]") is False
        assert validator.is_real_key("<your_api_key>") is False

    def test_excludes_env_vars(self, validator):
        assert validator.is_real_key("${OPENAI_KEY}") is False
        assert validator.is_real_key("${{secrets.API_KEY}}") is False

    def test_excludes_jinja_templates(self, validator):
        assert validator.is_real_key("{{ api_key }}") is False

    def test_excludes_example_placeholders(self, validator):
        assert validator.is_real_key("sk-example123456") is False
        assert validator.is_real_key("sk-placeholder123") is False
        assert validator.is_real_key("your_api_key_here") is False
        assert validator.is_real_key("test_key_12345678") is False
        assert validator.is_real_key("fake_api_key_here") is False

    def test_excludes_low_entropy(self, validator):
        # More than 80% same character
        assert validator.is_real_key("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") is False

    def test_excludes_sequential_patterns(self, validator):
        # Only very long sequential patterns are rejected
        assert validator.is_real_key("sk-1234567890123456abcd") is False
        assert validator.is_real_key("sk-abcdefghijklmnop") is False
        assert validator.is_real_key("sk-ABCDEFGHIJKLMNOP") is False
        # Short sequences are allowed (can appear in real keys)
        assert validator.is_real_key("sk-123456abcdefXYZ789") is True

    def test_accepts_real_looking_key(self, validator):
        # A key that looks real (high entropy, no placeholder indicators)
        real_key = "sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234"
        assert validator.is_real_key(real_key) is True

    def test_verbose_output(self, capsys):
        validator = ApiKeyValidator(verbose=True)
        validator.is_real_key("[placeholder]")
        captured = capsys.readouterr()
        assert "SKIP (placeholder indicator" in captured.out


# ======================
# Unit Tests: FileFinder
# ======================


class TestFileFinder:
    def test_finds_all_files(self, tmp_path):
        # Create various files
        (tmp_path / "file1.md").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "file3.json").touch()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        assert len(files) == 3
        filenames = {f.name for f in files}
        assert filenames == {"file1.md", "file2.py", "file3.json"}

    def test_excludes_directories(self, tmp_path):
        (tmp_path / "file.txt").touch()
        (tmp_path / "subdir").mkdir()

        finder = FileFinder(verbose=False)
        files = finder.find(tmp_path)

        # Should only find the file, not the directory
        assert len(files) == 1
        assert files[0].name == "file.txt"


# ======================
# Unit Tests: Reporter
# ======================


class TestReporter:
    def test_report_with_matches_exits_1(self, tmp_path, capsys):
        matches = [
            ApiKeyMatch(
                key="sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234",
                provider="OpenAI",
                file_path=tmp_path / "test.py",
                line_no=10,
            )
        ]
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(matches)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "potential API key(s) detected" in captured.out
        assert "OpenAI" in captured.out

    def test_report_no_matches_exits_0(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report([], verbose=True)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No API keys detected" in captured.out

    def test_report_no_matches_quiet(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report([], verbose=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out == ""


# ======================
# Integration Tests: ApiKeyCheckerCLI
# ======================


class TestApiKeyCheckerCLI:
    @pytest.fixture
    def cli(self):
        return ApiKeyCheckerCLI()

    def test_file_with_key_exits_1(self, cli, tmp_path, capsys):
        # Create file with a real-looking key
        file = tmp_path / "config.py"
        file.write_text(
            'API_KEY = "sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234"',
            encoding="utf-8",
        )

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "potential API key(s) detected" in captured.out

    def test_run_with_directory_in_files(self, cli, tmp_path):
        # Passing a directory in the files list should be skipped by is_file check
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(subdir)])
        assert exc_info.value.code == 0

    def test_file_without_key_exits_0(self, cli, tmp_path, capsys):
        file = tmp_path / "clean.py"
        file.write_text('API_KEY = "[YOUR_KEY_HERE]"', encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(file)])
        assert exc_info.value.code == 0

    def test_verbose_output(self, cli, tmp_path, capsys):
        file = tmp_path / "clean.py"
        file.write_text("# No keys here", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose", str(file)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Checking 1 file(s)" in captured.out
        assert "No API keys detected" in captured.out

    def test_multiple_files(self, cli, tmp_path, capsys):
        # Create two clean files
        file1 = tmp_path / "file1.py"
        file1.write_text("# Clean file 1", encoding="utf-8")
        file2 = tmp_path / "file2.py"
        file2.write_text("# Clean file 2", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose", str(file1), str(file2)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Checking 2 file(s)" in captured.out

    def test_missing_file_warning(self, cli, tmp_path, capsys):
        missing = tmp_path / "missing.py"

        with pytest.raises(SystemExit) as exc_info:
            cli.run([str(missing)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "File does not exist" in captured.err

    def test_directory_scan_mode(self, cli, tmp_path, monkeypatch, capsys):
        # Create a file in tmp_path
        (tmp_path / "test.py").write_text("# No keys", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Scanning" in captured.out


# ======================
# Parametrized Edge Cases
# ======================


@pytest.mark.parametrize(
    "key,should_detect",
    [
        # Real keys (should detect) - must meet minimum length requirements
        ("sk-TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234", True),  # 51 chars total
        ("gsk_TESTDATATESTDATATESTDATATESTDATATESTDATATESTDATA1234", True),  # 52 chars total
        ("AKIA" + "ABCXYZ1234567890", True),  # 20 chars total
        ("ghp_TESTDATATESTDATATESTDATATESTDATA1234", True),  # 40 chars total
        # Placeholders (should NOT detect)
        ("[API_KEY]", False),
        ("<your_api_key>", False),
        ("${OPENAI_KEY}", False),
        ("sk-" + "x" * 48, False),  # Low entropy
        ("sk-example" + "a" * 40, False),  # Contains 'example'
        ("sk-placeholder" + "a" * 36, False),  # Contains 'placeholder'
        ("sk-your_key_here" + "a" * 32, False),  # Contains 'your_key_here'
        ("sk-test_key_here" + "a" * 32, False),  # Contains 'test_key_here'
        ("sk-fake_api_key_here" + "a" * 24, False),  # Contains 'fake_api_key_here'
        # Short keys don't match any pattern (OpenAI requires 51+ chars)
        ("sk-123456abcdefXYZ789", False),
        # Edge cases
        ("", False),
        ("short", False),
        ("sk-", False),  # Too short
    ],
)
def test_edge_cases(tmp_path, key, should_detect):
    file = tmp_path / "test.txt"
    file.write_text(key, encoding="utf-8")
    detector = ApiKeyDetector(verbose=False)
    matches = detector.detect_in_file(file)
    assert (len(matches) > 0) == should_detect


# ======================
# Main Entry Point Test
# ======================


def test_main_entry_point():
    # Cover the __main__ block
    with patch("sys.argv", ["check_api_keys.py", "--help"]), pytest.raises(SystemExit):
        runpy.run_path("tools/scripts/check_api_keys.py", run_name="__main__")

    with patch("tools.scripts.check_api_keys.ApiKeyCheckerCLI.run") as mock_run:
        from tools.scripts.check_api_keys import main

        main()
        mock_run.assert_called_once_with()
