# test_check_broken_links.py
import subprocess
import sys
from pathlib import Path

import pytest
from check_broken_links import FileFinder, LinkExtractor, LinkValidator


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample .ipynb file for testing."""
    f = tmp_path / "sample.ipynb"
    f.write_text(
        "# Test\n[Valid](target.ipynb)\n[External](https://example.com)\n[Fragment](#section)"
    )
    return f


def test_link_extractor_finds_links(sample_file):
    extractor = LinkExtractor(verbose=False)
    links = extractor.extract(sample_file)
    assert links == ["target.ipynb", "https://example.com", "#section"]


def test_link_extractor_handles_no_links(tmp_path):
    f = tmp_path / "empty.ipynb"
    f.write_text("No links here.")
    extractor = LinkExtractor(verbose=False)
    assert extractor.extract(f) == []


def test_link_extractor_handles_unicode_error(tmp_path, capsys):
    f = tmp_path / "bad.ipynb"
    f.write_bytes(b"\xff\xfe")  # Invalid UTF-8
    extractor = LinkExtractor(verbose=False)
    assert extractor.extract(f) == []
    captured = capsys.readouterr()
    assert "Cannot decode file" in captured.err


# ── LinkValidator Tests ───────────────────────────────────────────────


@pytest.fixture
def project_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "existing.ipynb").write_text("OK")
    docs = root / "docs"
    docs.mkdir()
    (docs / "index.ipynb").write_text("Index")
    (docs / "README.ipynb").write_text("Readme")
    return root


def test_valid_relative_link(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("existing.ipynb", source)
    assert error is None


def test_broken_relative_link(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("missing.ipynb", source)
    assert error is not None
    assert "BROKEN LINK" in error


def test_valid_directory_with_index(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("docs/", source)
    assert error is None


def test_valid_directory_with_readme(project_root):
    # Remove index, keep README
    (project_root / "docs" / "index.ipynb").unlink()
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("docs/", source)
    assert error is None


def test_external_url_skipped(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("https://example.com", source)
    assert error is None


def test_internal_fragment_skipped(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("#section", source)
    assert error is None


def test_absolute_project_path_link(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "sub" / "deep.ipynb"
    source.parent.mkdir()
    error = validator.validate_link("/existing.ipynb", source)
    assert error is None


def test_broken_absolute_project_path_link(project_root):
    validator = LinkValidator(root_dir=project_root)
    source = project_root / "source.ipynb"
    error = validator.validate_link("/missing.ipynb", source)
    assert error is not None


# ── FileFinder Tests ──────────────────────────────────────────────────


def test_file_finder_respects_exclusions(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "good.ipynb").write_text("ok")
    (root / "in_progress").mkdir()
    (root / "in_progress" / "bad.ipynb").write_text("skip")
    (root / ".aider.chat.history.ipynb").write_text("skip")
    (root / "pr").mkdir()
    (root / "pr" / "draft.ipynb").write_text("skip")
    (root / "normal_dir").mkdir()
    (root / "normal_dir" / "keep.ipynb").write_text("keep")

    finder = FileFinder(
        exclude_dirs=["in_progress", "pr", ".venv"],
        exclude_files=[".aider.chat.history.ipynb"],
        verbose=False,
    )
    files = finder.find(root, "*.ipynb")
    names = {f.name for f in files}
    assert names == {"good.ipynb", "keep.ipynb"}


def test_file_finder_ignores_ipynb_checkpoints(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    checkpoints = root / ".ipynb_checkpoints"
    checkpoints.mkdir()
    (checkpoints / "temp.ipynb").write_text("auto-save")
    (root / "main.ipynb").write_text("real")

    finder = FileFinder([], [], verbose=False)
    files = finder.find(root, "*.ipynb")
    names = {f.name for f in files}
    assert names == {"main.ipynb"}  # checkpoint excluded


# ── Full CLI Integration Tests ───────────────────────────────────────


def test_cli_all_links_valid(tmp_path):
    (tmp_path / "a.ipynb").write_text("[link](b.ipynb)")
    (tmp_path / "b.ipynb").write_text("target")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(tmp_path)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "All links are valid" in result.stdout


def test_cli_broken_link_detected(tmp_path):
    (tmp_path / "a.ipynb").write_text("[broken](missing.ipynb)")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(tmp_path)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Broken links found" in result.stdout
    assert "missing.ipynb" in result.stdout


def test_cli_single_file_mode(tmp_path):
    good = tmp_path / "good.ipynb"
    good.write_text("[ok](target.ipynb)")
    (tmp_path / "target.ipynb").write_text("exists")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(good)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "1 file file(s)" in result.stdout  # should say "file", not pattern


def test_cli_no_files_found(tmp_path):
    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(tmp_path), "--pattern", "*.xyz"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No files matching" in result.stdout


# --- NEW TESTS: Closing Critical Gaps ---


def test_encoded_spaces_in_links(tmp_path):
    """Test that %20 in links is NOT decoded (current behavior), and file must match encoded name."""
    # Current implementation does NOT URL-decode, so link must match filesystem literally
    target = tmp_path / "file%20with%20spaces.ipynb"
    target.write_text("exists")
    source = tmp_path / "source.ipynb"
    source.write_text("[link](file%20with%20spaces.ipynb)")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    # Should PASS because filename on disk matches encoded link exactly
    assert result.returncode == 0

    # Now test the more common case: user writes [link](file with spaces.ipynb)
    # But filesystem has no such file → should fail
    source2 = tmp_path / "source2.ipynb"
    source2.write_text("[link](file with spaces.ipynb)")
    result2 = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source2)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 1  # broken, because no "file with spaces.ipynb" exists
    # Note: This exposes a limitation—script doesn't handle URL decoding.
    # But at least we now DOCUMENT and TEST the behavior.


def test_image_links_are_validated(tmp_path):
    """Confirm ![](image.png) is extracted and validated like regular links."""
    img_path = tmp_path / "diagram.png"
    img_path.write_bytes(b"fake png")
    source = tmp_path / "notebook.ipynb"
    source.write_text("![label](diagram.png)")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0  # valid image link

    # Now break it
    img_path.unlink()
    result2 = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 1
    assert "diagram.png" in result2.stdout


def test_case_sensitivity_on_linux(tmp_path):
    """On Linux, case matters. Test that mismatched case fails."""
    (tmp_path / "Target.ipynb").write_text("real file")
    source = tmp_path / "source.ipynb"
    # Link uses lowercase, file is uppercase
    source.write_text("[link](target.ipynb)")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    # On Linux, this should FAIL
    assert result.returncode == 1
    assert "target.ipynb" in result.stdout


def test_link_to_non_ipynb_file(tmp_path):
    """Script should validate ANY local file, not just .ipynb."""
    (tmp_path / "helper.py").write_text("print('ok')")
    source = tmp_path / "notebook.ipynb"
    source.write_text("[code](helper.py)")

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0  # valid non-ipynb link


def test_nested_directory_without_index_fails(tmp_path):
    """Link to dir/ should fail if no index.ipynb or README.ipynb exists in that dir."""
    docs = tmp_path / "docs"
    docs.mkdir()
    # Create a nested subdirectory with its own index (should NOT help docs/)
    (docs / "sub").mkdir()
    (docs / "sub" / "index.ipynb").write_text("deep")  # This is fine — it's a file

    source = tmp_path / "source.ipynb"
    source.write_text("[docs](docs/)")  # points to docs/, which has no index/README

    result = subprocess.run(
        [sys.executable, "check_broken_links.py", str(source)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1  # should fail
    assert "docs/" in result.stdout
