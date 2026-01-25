import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tools.scripts.check_script_suite import (
    get_staged_files,
    get_renamed_files,
    script_name_to_paths,
    get_all_scripts,
    check_naming_convention,
    check_doc_staged,
    check_doc_rename,
    main,
    SCRIPTS_DIR,
    TESTS_DIR,
    DOCS_DIR,
    EXCLUDED_SCRIPTS,
    CONFIG_FILES,
)


# ======================
# Unit Tests: script_name_to_paths
# ======================


class TestScriptNameToPaths:
    def test_converts_name_to_all_paths(self):
        script, test, doc = script_name_to_paths("check_broken_links")
        assert script == SCRIPTS_DIR / "check_broken_links.py"
        assert test == TESTS_DIR / "test_check_broken_links.py"
        assert doc == DOCS_DIR / "check_broken_links_py_script.md"

    def test_handles_simple_name(self):
        script, test, doc = script_name_to_paths("foo")
        assert script == SCRIPTS_DIR / "foo.py"
        assert test == TESTS_DIR / "test_foo.py"
        assert doc == DOCS_DIR / "foo_py_script.md"


# ======================
# Unit Tests: get_staged_files
# ======================


class TestGetStagedFiles:
    def test_returns_set_of_staged_files(self):
        mock_result = MagicMock()
        mock_result.stdout = "file1.py\nfile2.py\nfile3.md\n"
        with patch("subprocess.run", return_value=mock_result):
            result = get_staged_files()
        assert result == {"file1.py", "file2.py", "file3.md"}

    def test_returns_empty_set_when_no_staged_files(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = get_staged_files()
        assert result == set()

    def test_handles_single_file(self):
        mock_result = MagicMock()
        mock_result.stdout = "single.py\n"
        with patch("subprocess.run", return_value=mock_result):
            result = get_staged_files()
        assert result == {"single.py"}


# ======================
# Unit Tests: get_renamed_files
# ======================


class TestGetRenamedFiles:
    def test_detects_renamed_file(self):
        mock_result = MagicMock()
        mock_result.stdout = "R100\told_name.md\tnew_name.md\n"
        with patch("subprocess.run", return_value=mock_result):
            result = get_renamed_files()
        assert result == {"old_name.md": "new_name.md"}

    def test_detects_multiple_renames(self):
        mock_result = MagicMock()
        mock_result.stdout = "R100\ta.md\tb.md\nR095\tc.py\td.py\n"
        with patch("subprocess.run", return_value=mock_result):
            result = get_renamed_files()
        assert result == {"a.md": "b.md", "c.py": "d.py"}

    def test_ignores_non_rename_statuses(self):
        mock_result = MagicMock()
        mock_result.stdout = "M\tmodified.py\nA\tadded.py\nD\tdeleted.py\n"
        with patch("subprocess.run", return_value=mock_result):
            result = get_renamed_files()
        assert result == {}

    def test_returns_empty_when_no_changes(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = get_renamed_files()
        assert result == {}


# ======================
# Unit Tests: get_all_scripts
# ======================


class TestGetAllScripts:
    def test_finds_scripts_in_directory(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "script_a.py").touch()
        (scripts_dir / "script_b.py").touch()
        (scripts_dir / "paths.py").touch()  # excluded

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = get_all_scripts()

        assert set(result) == {"script_a", "script_b"}

    def test_excludes_paths_py(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "paths.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = get_all_scripts()

        assert "paths" not in result

    def test_excludes_init_py(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "__init__.py").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir):
            result = get_all_scripts()

        assert "__init__" not in result

    def test_returns_empty_when_dir_not_exists(self, tmp_path):
        nonexistent = tmp_path / "nonexistent"
        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", nonexistent):
            result = get_all_scripts()
        assert result == []


# ======================
# Unit Tests: check_naming_convention
# ======================


class TestCheckNamingConvention:
    def test_no_errors_when_suite_complete(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_naming_convention()

        assert errors == []

    def test_error_when_test_missing(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()
        # test file missing

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_naming_convention()

        assert len(errors) == 1
        assert "Missing test" in errors[0]

    def test_error_when_doc_missing(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        # doc file missing

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_naming_convention()

        assert len(errors) == 1
        assert "Missing doc" in errors[0]

    def test_multiple_errors_for_multiple_missing(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        # both test and doc missing

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_naming_convention()

        assert len(errors) == 2


# ======================
# Unit Tests: check_doc_staged
# ======================


class TestCheckDocStaged:
    def test_no_error_when_doc_staged_with_script(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        staged = {
            str(scripts_dir / "my_script.py"),
            str(docs_dir / "my_script_py_script.md"),
        }

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_doc_staged(staged)

        assert errors == []

    def test_error_when_script_changed_doc_not_staged(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        staged = {str(scripts_dir / "my_script.py")}  # doc not staged

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_doc_staged(staged)

        assert len(errors) == 1
        assert "Doc not staged" in errors[0]

    def test_error_when_test_changed_doc_not_staged(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        staged = {str(tests_dir / "test_my_script.py")}  # doc not staged

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_doc_staged(staged)

        assert len(errors) == 1
        assert "Doc not staged" in errors[0]

    def test_no_error_when_unrelated_file_staged(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        staged = {"some_other_file.py"}  # unrelated file

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir):
            errors = check_doc_staged(staged)

        assert errors == []


# ======================
# Unit Tests: check_doc_rename
# ======================


class TestCheckDocRename:
    def test_error_when_doc_renamed_config_not_staged(self):
        staged = {"tools/docs/scripts_instructions/new_name_py_script.md"}
        renamed = {
            "tools/docs/scripts_instructions/old_name_py_script.md":
            "tools/docs/scripts_instructions/new_name_py_script.md"
        }

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value=renamed):
            errors = check_doc_rename(staged)

        assert len(errors) == 2  # both config files missing
        assert any(".pre-commit-config.yaml" in e for e in errors)
        assert any("quality.yml" in e for e in errors)

    def test_no_error_when_doc_renamed_and_configs_staged(self):
        staged = {
            "tools/docs/scripts_instructions/new_name_py_script.md",
            ".pre-commit-config.yaml",
            ".github/workflows/quality.yml",
        }
        renamed = {
            "tools/docs/scripts_instructions/old_name_py_script.md":
            "tools/docs/scripts_instructions/new_name_py_script.md"
        }

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value=renamed):
            errors = check_doc_rename(staged)

        assert errors == []

    def test_no_error_when_non_doc_file_renamed(self):
        staged = {"some_file.py"}
        renamed = {"old.py": "new.py"}

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value=renamed):
            errors = check_doc_rename(staged)

        assert errors == []

    def test_no_error_when_no_renames(self):
        staged = {"some_file.py"}

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value={}):
            errors = check_doc_rename(staged)

        assert errors == []


# ======================
# Integration Tests: main
# ======================


class TestMain:
    def test_exits_zero_when_no_errors(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py"]):
            result = main()

        assert result == 0

    def test_exits_one_when_errors(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        # missing test and doc

        mock_staged = MagicMock()
        mock_staged.stdout = ""

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_staged), \
             patch("sys.argv", ["check_script_suite.py"]):
            result = main()

        assert result == 1

    def test_check_convention_only_skips_staging_checks(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        scripts_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)

        (scripts_dir / "my_script.py").touch()
        (tests_dir / "test_my_script.py").touch()
        (docs_dir / "my_script_py_script.md").touch()

        # Should not call get_staged_files when --check-convention-only
        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("tools.scripts.check_script_suite.get_staged_files") as mock_staged, \
             patch("sys.argv", ["check_script_suite.py", "--check-convention-only"]):
            result = main()

        mock_staged.assert_not_called()
        assert result == 0
