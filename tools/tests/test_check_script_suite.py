import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tools.scripts.check_script_suite import (
    get_staged_files,
    get_renamed_files,
    is_mode_only_change,
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


# =======================
# Unit Tests: script_name_to_paths
# =======================


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
# Unit Tests: is_mode_only_change
# ======================


class TestIsModeOnlyChange:
    def test_returns_true_for_mode_only_change(self):
        """Mode-only change shows old mode/new mode lines without hunks."""
        mock_result = MagicMock()
        mock_result.stdout = """diff --git a/script.py b/script.py
old mode 100644
new mode 100755"""
        with patch("subprocess.run", return_value=mock_result):
            result = is_mode_only_change("script.py")
        assert result is True

    def test_returns_false_for_content_change(self):
        """Content change shows hunk headers (@@)."""
        mock_result = MagicMock()
        mock_result.stdout = """diff --git a/script.py b/script.py
index abc123..def456 100644
--- a/script.py
+++ b/script.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2"""
        with patch("subprocess.run", return_value=mock_result):
            result = is_mode_only_change("script.py")
        assert result is False

    def test_returns_false_for_mode_and_content_change(self):
        """Both mode and content changes should return False."""
        mock_result = MagicMock()
        mock_result.stdout = """diff --git a/script.py b/script.py
old mode 100644
new mode 100755
index abc123..def456
--- a/script.py
+++ b/script.py
@@ -1,3 +1,4 @@
 line1
+new line"""
        with patch("subprocess.run", return_value=mock_result):
            result = is_mode_only_change("script.py")
        assert result is False

    def test_returns_true_for_empty_diff(self):
        """Empty diff means no content changes (edge case)."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = is_mode_only_change("script.py")
        assert result is True

    def test_calls_git_diff_with_correct_arguments(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            is_mode_only_change("tools/scripts/my_script.py")
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--", "tools/scripts/my_script.py"],
            capture_output=True,
            text=True,
        )


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
            errors = check_naming_convention(verbose=True)

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
    MOCK_DIFF_CONTENT_CHANGE = """diff --git a/script.py b/script.py
index abc123..def456 100644
--- a/script.py
+++ b/script.py
@@ -1,1 +1,2 @@
+new line
"""
    MOCK_DIFF_MODE_ONLY = """diff --git a/script.py b/script.py
old mode 100644
new mode 100755
"""

    def _setup_test_env(self, tmp_path):
        scripts_dir = tmp_path / "tools" / "scripts"
        tests_dir = tmp_path / "tools" / "tests"
        docs_dir = tmp_path / "tools" / "docs" / "scripts_instructions"
        for d in [scripts_dir, tests_dir, docs_dir]:
            d.mkdir(parents=True)

        script_path = scripts_dir / "my_script.py"
        test_path = tests_dir / "test_my_script.py"
        doc_path = docs_dir / "my_script_py_script.md"
        script_path.touch()
        test_path.touch()
        doc_path.touch()

        return scripts_dir, tests_dir, docs_dir, script_path, test_path, doc_path

    def test_no_error_when_doc_staged_with_script(self, tmp_path):
        scripts_dir, tests_dir, docs_dir, script_path, _, doc_path = self._setup_test_env(tmp_path)
        staged = {str(script_path), str(doc_path)}

        mock_result = MagicMock()
        mock_result.stdout = self.MOCK_DIFF_CONTENT_CHANGE

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            errors = check_doc_staged(staged)

        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--", str(script_path)],
            capture_output=True,
            text=True
        )
        assert errors == []

    def test_error_when_script_changed_doc_not_staged(self, tmp_path):
        scripts_dir, tests_dir, docs_dir, script_path, _, _ = self._setup_test_env(tmp_path)
        staged = {str(script_path)}

        mock_result = MagicMock()
        mock_result.stdout = self.MOCK_DIFF_CONTENT_CHANGE

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_result):
            errors = check_doc_staged(staged)

        assert len(errors) == 1
        assert "Doc not staged" in errors[0]

    def test_error_when_test_changed_doc_not_staged(self, tmp_path):
        scripts_dir, tests_dir, docs_dir, _, test_path, _ = self._setup_test_env(tmp_path)
        staged = {str(test_path)}

        mock_result = MagicMock()
        mock_result.stdout = self.MOCK_DIFF_CONTENT_CHANGE

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_result):
            errors = check_doc_staged(staged)

        assert len(errors) == 1
        assert "Doc not staged" in errors[0]

    def test_no_error_when_unrelated_file_staged(self, tmp_path):
        scripts_dir, tests_dir, docs_dir, _, _, _ = self._setup_test_env(tmp_path)
        staged = {"some_other_file.py"}

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run") as mock_run:
            errors = check_doc_staged(staged)

        mock_run.assert_not_called()
        assert errors == []

    def test_no_error_when_script_has_mode_only_change(self, tmp_path):
        scripts_dir, tests_dir, docs_dir, script_path, _, _ = self._setup_test_env(tmp_path)
        staged = {str(script_path)}

        mock_result = MagicMock()
        mock_result.stdout = self.MOCK_DIFF_MODE_ONLY

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_result):
            errors = check_doc_staged(staged)

        assert errors == []

    def test_no_error_when_test_has_mode_only_change(self, tmp_path):
        scripts_dir, tests_dir, docs_dir, _, test_path, _ = self._setup_test_env(tmp_path)
        staged = {str(test_path)}

        mock_result = MagicMock()
        mock_result.stdout = self.MOCK_DIFF_MODE_ONLY

        with patch("tools.scripts.check_script_suite.SCRIPTS_DIR", scripts_dir), \
             patch("tools.scripts.check_script_suite.TESTS_DIR", tests_dir), \
             patch("tools.scripts.check_script_suite.DOCS_DIR", docs_dir), \
             patch("subprocess.run", return_value=mock_result):
            errors = check_doc_staged(staged)

        assert errors == []


# ======================
# Unit Tests: check_doc_rename
# ======================


class TestCheckDocRename:
    def test_error_when_doc_renamed_config_not_staged(self):
        old_doc = DOCS_DIR / "old_name_py_script.md"
        new_doc = DOCS_DIR / "new_name_py_script.md"
        staged = {str(new_doc)}
        renamed = {str(old_doc): str(new_doc)}

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value=renamed):
            errors = check_doc_rename(staged)

        assert len(errors) == len(CONFIG_FILES)
        for config_file in CONFIG_FILES:
            assert any(config_file in e for e in errors)

    def test_no_error_when_doc_renamed_and_configs_staged(self):
        old_doc = DOCS_DIR / "old_name_py_script.md"
        new_doc = DOCS_DIR / "new_name_py_script.md"
        staged = {str(new_doc), *CONFIG_FILES}
        renamed = {str(old_doc): str(new_doc)}

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value=renamed):
            errors = check_doc_rename(staged, verbose=True)

        assert errors == []

    def test_no_error_if_rename_endswith_but_not_in_doc_dir(self):
        staged = {"some_file.py"}
        renamed = {"other_dir/old_name_py_script.md": "other_dir/new_name_py_script.md"}

        with patch("tools.scripts.check_script_suite.get_renamed_files", return_value=renamed):
            errors = check_doc_rename(staged)

        assert errors == []

    def test_no_error_if_rename_in_doc_dir_but_not_doc_file(self):
        staged = {"some_file.py"}
        old_path = str(DOCS_DIR / "not_a_doc.md")
        new_path = str(DOCS_DIR / "also_not_a_doc.md")
        renamed = {old_path: new_path}

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

    def test_verbose_output_on_success(self, tmp_path, capsys):
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
             patch("sys.argv", ["check_script_suite.py", "-v"]):
            result = main()

        captured = capsys.readouterr()
        assert result == 0
        assert "All checks passed" in captured.out

    def test_exits_one_when_errors(self, tmp_path, capsys):
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

        captured = capsys.readouterr()
        assert result == 1
        assert "Errors found" in captured.out
        assert "Missing test" in captured.out
        assert "Missing doc" in captured.out

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
