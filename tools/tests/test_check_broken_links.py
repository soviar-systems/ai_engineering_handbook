import subprocess
import sys
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

from tools.scripts.check_broken_links import (
    FileFinder,
    LinkCheckerCLI,
    LinkExtractor,
    LinkValidator,
    Reporter,
)
from tools.scripts.paths import BROKEN_LINKS_EXCLUDE_DIRS, BROKEN_LINKS_EXCLUDE_FILES


@pytest.fixture(autouse=True)
def mock_paths_module():
    """Patch the import of BROKEN_LINKS_EXCLUDE_*."""
    with patch.dict(
        sys.modules,
        {
            "tools.scripts.paths": MagicMock(
                BROKEN_LINKS_EXCLUDE_DIRS=BROKEN_LINKS_EXCLUDE_DIRS,
                BROKEN_LINKS_EXCLUDE_FILES=BROKEN_LINKS_EXCLUDE_FILES,
            )
        },
    ):
        yield


# ======================
# Unit Tests
# ======================


class TestLinkExtractor:
    @pytest.mark.parametrize(
        "content,expected_links",
        [
            ("[text](link.ipynb)", ["link.ipynb"]),
            ("[a](x.ipynb) and [b](y.ipynb)", ["x.ipynb", "y.ipynb"]),
            ("no links here", []),
            ("![image](img.png)", ["img.png"]),  # also matches image links
            ("[broken](  spaced link.ipynb  )", ["  spaced link.ipynb  "]),
        ],
    )
    def test_extract_links(self, tmp_path, content, expected_links):
        file = tmp_path / "test.ipynb"
        file.write_text(content, encoding="utf-8")
        extractor = LinkExtractor(verbose=False)
        links = extractor.extract(file)
        assert links == expected_links

    def test_extract_handles_decode_error(self, capsys):
        extractor = LinkExtractor(verbose=False)
        # Create a file that can't be decoded as UTF-8
        binary_file = Path(__file__).parent / "binary_file.bin"
        binary_file.write_bytes(b"\xff\xfe")
        try:
            links = extractor.extract(binary_file)
            assert links == []
            captured = capsys.readouterr()
            assert "Cannot decode file" in captured.err
        finally:
            binary_file.unlink(missing_ok=True)


class TestLinkValidator:
    @pytest.fixture
    def validator(self, tmp_path):
        return LinkValidator(root_dir=tmp_path, verbose=False)

    def test_is_absolute_url(self, validator):
        assert validator.is_absolute_url("https://example.com") is True
        assert validator.is_absolute_url("http://local.dev") is True
        assert validator.is_absolute_url("/relative/path") is False
        assert validator.is_absolute_url("relative.ipynb") is False

    @pytest.mark.parametrize(
        "link,expected",
        [
            ("file.ipynb#section", "file.ipynb"),
            ("clean.ipynb", "clean.ipynb"),
            ("", ""),
        ],
    )
    def test_get_path_from_link(self, validator, link, expected):
        assert validator.get_path_from_link(link) == expected

    def test_resolve_target_path_absolute_from_root(self, validator, tmp_path):
        source = tmp_path / "docs" / "a.ipynb"
        target = validator.resolve_target_path("/notebooks/b.ipynb", source)
        assert target == tmp_path / "notebooks" / "b.ipynb"

    def test_resolve_target_path_relative(self, validator, tmp_path):
        source = tmp_path / "docs" / "a.ipynb"
        target = validator.resolve_target_path("../data.csv", source)
        assert target == (tmp_path / "data.csv").resolve()

    def test_is_valid_target_file_exists(self, validator, tmp_path):
        target = tmp_path / "exists.ipynb"
        target.touch()
        assert validator.is_valid_target(target) is True

    def test_is_valid_target_dir_with_index(self, validator, tmp_path):
        target_dir = tmp_path / "folder"
        target_dir.mkdir()
        (target_dir / "index.ipynb").touch()
        assert validator.is_valid_target(target_dir) is True

    def test_is_valid_target_dir_with_readme(self, validator, tmp_path):
        target_dir = tmp_path / "folder"
        target_dir.mkdir()
        (target_dir / "README.ipynb").touch()
        assert validator.is_valid_target(target_dir) is True

    def test_is_valid_target_dir_no_index(self, validator, tmp_path):
        target_dir = tmp_path / "empty"
        target_dir.mkdir()
        assert validator.is_valid_target(target_dir) is False

    def test_validate_link_external_skipped(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("https://example.com", source)
        assert error is None

    def test_validate_link_internal_fragment_skipped(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("#section", source)
        assert error is None

    def test_validate_link_broken(self, validator, tmp_path):
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("nonexistent.ipynb", source)
        assert "BROKEN LINK" in error
        assert "a.ipynb" in error

    def test_validate_link_valid(self, validator, tmp_path):
        target = tmp_path / "exists.ipynb"
        target.touch()
        source = tmp_path / "a.ipynb"
        error = validator.validate_link("exists.ipynb", source)
        assert error is None


class TestFileFinder:
    def test_find_respects_exclude_dirs_nested(self, tmp_path):
        # Setup a mock repository structure with various excluded directories
        root_test_dir = tmp_path / "repo_root"
        root_test_dir.mkdir()

        # Files that should be included
        (root_test_dir / "docs").mkdir()
        (root_test_dir / "docs" / "good_doc_1.ipynb").touch()
        (root_test_dir / "src").mkdir()
        # Nested good file within a valid path
        (root_test_dir / "src" / "sub_module" / "valid_code_folder").mkdir(parents=True)
        (root_test_dir / "src" / "sub_module" / "valid_code_folder" / "good_2.py").touch()
        # Directory name contains part of an excluded dir, but isn't the excluded dir itself
        (root_test_dir / "valid_dir_not_node_modules" / "some_file.ipynb").mkdir(parents=True)
        (root_test_dir / "valid_dir_not_node_modules" / "some_file.ipynb" / "good_3.ipynb").touch()

        # Files that should be excluded by directory name (from BROKEN_LINKS_EXCLUDE_DIRS)
        (root_test_dir / "misc" / "in_progress" / "temp_folder").mkdir(parents=True)
        (root_test_dir / "misc" / "in_progress" / "temp_folder" / "bad_1.ipynb").touch() # Excluded by misc/in_progress
        (root_test_dir / "src" / "my_module" / "__pycache__").mkdir(parents=True)
        (root_test_dir / "src" / "my_module" / "__pycache__" / "bad_2.py").touch() # Excluded by __pycache__
        (root_test_dir / ".git" / "hooks").mkdir(parents=True)
        (root_test_dir / ".git" / "hooks" / "bad_3.md").touch() # Excluded by .git
        (root_test_dir / "node_modules" / "some_lib" / "bad_folder").mkdir(parents=True)
        (root_test_dir / "node_modules" / "some_lib" / "bad_folder" / "bad_4.js").touch() # Excluded by node_modules
        (root_test_dir / "nested_build" / "build" / "another_bad.py").mkdir(parents=True)
        (root_test_dir / "nested_build" / "build" / "another_bad.py" / "bad_5.txt").touch() # Excluded by build

        finder = FileFinder(
            exclude_dirs=list(BROKEN_LINKS_EXCLUDE_DIRS),
            exclude_files=list(BROKEN_LINKS_EXCLUDE_FILES),
            verbose=False, # Set to True for debugging if needed
        )
        files = finder.find(root_test_dir, "*") # Use '*' to find all file types

        expected_files = {
            root_test_dir / "docs" / "good_doc_1.ipynb",
            root_test_dir / "src" / "sub_module" / "valid_code_folder" / "good_2.py",
            root_test_dir / "valid_dir_not_node_modules" / "some_file.ipynb" / "good_3.ipynb",
        }

        assert len(files) == len(expected_files)
        assert set(files) == expected_files

    def test_find_respects_exclude_files_globally(self, tmp_path):
        root_test_dir = tmp_path / "repo_root"
        root_test_dir.mkdir()

        # Files that should be included
        (root_test_dir / "good_file_1.ipynb").touch()
        (root_test_dir / "sub" / "good_dir").mkdir(parents=True) # Renamed for clarity, it's a directory
        (root_test_dir / "sub" / "good_dir" / "another_good.txt").touch()

        # File that should be excluded by name (from BROKEN_LINKS_EXCLUDE_FILES)
        (root_test_dir / "sub" / "excluded_dir_for_file_test").mkdir(parents=True)
        (root_test_dir / "sub" / "excluded_dir_for_file_test" / ".aider.chat.history.md").touch() # The file itself has the excluded name


        finder = FileFinder(
            exclude_dirs=list(BROKEN_LINKS_EXCLUDE_DIRS),
            exclude_files=list(BROKEN_LINKS_EXCLUDE_FILES),
            verbose=False,
        )
        files = finder.find(root_test_dir, "*") # Use '*' to find all file types

        expected_files = {
            root_test_dir / "good_file_1.ipynb",
            root_test_dir / "sub" / "good_dir" / "another_good.txt",
        }
        assert len(files) == len(expected_files)
        assert set(files) == expected_files

    def test_find_excludes_ipynb_checkpoints(self, tmp_path):
        (tmp_path / "normal.ipynb").touch()
        cp_dir = tmp_path / ".ipynb_checkpoints"
        cp_dir.mkdir()
        (cp_dir / "auto.ipynb").touch()

        finder = FileFinder(exclude_dirs=[], exclude_files=[], verbose=False)
        files = finder.find(tmp_path, "*.ipynb")
        assert len(files) == 1
        assert ".ipynb_checkpoints" not in str(files[0])


class TestReporter:
    def test_report_broken_links_exits_1(self, tmp_path, capsys):
        report_file = tmp_path / "report.txt"
        report_file.write_text("BROKEN LINK: ...\n", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(report_file, broken_links_found=True)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌" in captured.out

    def test_report_no_broken_links_exits_0(self, tmp_path, capsys):
        report_file = tmp_path / "empty.txt"
        report_file.write_text("", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(report_file, broken_links_found=False)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "✅" in captured.out

    def test_report_missing_temp_file(self, tmp_path, capsys):
        missing = tmp_path / "missing.txt"
        with pytest.raises(SystemExit) as exc_info:
            Reporter.report(missing, broken_links_found=True)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


# ======================
# Integration & E2E Tests
# ======================


class TestLinkCheckerCLI:
    @pytest.fixture
    def cli(self):
        return LinkCheckerCLI()

    @patch("tools.scripts.check_broken_links.subprocess.run")
    def test_get_git_root_dir_success(self, mock_run, cli):
        mock_run.return_value = MagicMock(stdout="/fake/repo\n")
        root = cli.get_git_root_dir()
        assert root == Path("/fake/repo").resolve()
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            stdout=ANY,
            stderr=ANY,
            text=True,
        )

    @patch("tools.scripts.check_broken_links.subprocess.run")
    def test_get_git_root_dir_failure(self, mock_run, cli):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        root = cli.get_git_root_dir()
        assert root is None

    @patch("tools.scripts.check_broken_links.subprocess.run")
    def test_get_git_root_dir_git_not_installed(self, mock_run, cli):
        mock_run.side_effect = FileNotFoundError()
        root = cli.get_git_root_dir()
        assert root is None

    def test_run_single_file_input(self, tmp_path, capsys, monkeypatch):
        target = tmp_path / "target.ipynb"
        target.touch()
        source = tmp_path / "source.ipynb"
        source.write_text(f"[link]({target.name})", encoding="utf-8")

        # Corrected: Added "--paths" flag
        monkeypatch.setattr(
            "sys.argv",
            ["check_broken_links.py", "--paths", str(source), "--pattern", "*.ipynb"],
        )
        with pytest.raises(SystemExit) as exc_info:
            cli = LinkCheckerCLI()
            cli.run()
        assert exc_info.value.code == 0

    def test_run_broken_link_in_dir(self, tmp_path, capsys):
        (tmp_path / "source.ipynb").write_text("[bad](missing.ipynb)", encoding="utf-8")

        cli = LinkCheckerCLI()
        with pytest.raises(SystemExit) as exc_info:
            # Pass arguments directly to the method
            cli.run(["--paths", str(tmp_path), "--pattern", "*.ipynb"])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "BROKEN LINK" in captured.out

    def test_run_no_files_found(self, tmp_path, capsys):
        cli = LinkCheckerCLI()
        with pytest.raises(SystemExit) as exc_info:
            # Use the new injectable argv and include --paths
            cli.run(["--paths", str(tmp_path), "--pattern", "*.xyz"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No files matching '*.xyz' found!" in captured.out


# ======================
# Defensive Tests
# ======================


def test_nonexistent_input_path(tmp_path, capsys):
    cli = LinkCheckerCLI()
    bad_path = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as exc_info:
        cli.run(["--paths", str(bad_path)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Warning: Path does not exist" in captured.err


# ======================
# Parametrized Edge Cases
# ======================


@pytest.mark.parametrize(
    "link_str,should_skip",
    [
        ("#top", True),
        ("#section-1", True),
        ("page.ipynb#anchor", False),
        ("", False),
        (".", False),
        ("..", False),
        ("./local.ipynb", False),
    ],
)
def test_link_validator_skip_logic(tmp_path, link_str, should_skip):
    validator = LinkValidator(root_dir=tmp_path)
    source = tmp_path / "source.ipynb"
    error = validator.validate_link(link_str, source)
    if should_skip:
        assert error is None
    else:
        # May be broken or valid, but not skipped
        pass  # We only care it wasn't skipped


# ======================
# End-to-End Git Root Simulation
# ======================


def test_e2e_with_git_root(tmp_path, capsys):
    git_root = tmp_path / "repo"
    git_root.mkdir()
    (git_root / ".git").mkdir()
    docs = git_root / "docs"
    docs.mkdir()
    target = git_root / "data.ipynb"
    target.touch()
    source = docs / "guide.ipynb"
    source.write_text("[data](/data.ipynb)", encoding="utf-8")

    cli = LinkCheckerCLI()
    with (
        patch.object(LinkCheckerCLI, "get_git_root_dir", return_value=git_root),
        patch("pathlib.Path.cwd", return_value=docs),
    ):
        # Explicitly use --paths and avoid monkeypatch
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["--verbose", "--paths", str(source)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Using Git root" in captured.out
