"""
Test suite for check_evidence.py - Evidence artifact validator.

Tests are organized following the behavior-based testing principle:
- Test what the code does, not how it does it
- Use semantic assertions rather than exact string matching
- Parametrize from config, not hardcoded lists (SSoT-driven)

Test classes and their contracts:
- TestConfigLoading: Config loads from pyproject.toml pointer, resolves parent_config tags
- TestValidateNaming: Filenames match regex patterns from config per artifact type
- TestValidateFrontmatter: Required fields present, valid statuses/severity/tags per type
- TestValidateSections: Required sections present, no unexpected sections
- TestDetectOrphanedSources: Sources with null extracted_into flagged past threshold
- TestDiscoverArtifacts: Scans correct directories, returns sorted artifacts
- TestCli: Exit codes 0 (valid) / 1 (errors), --verbose and --check-staged flags
"""

import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

import tools.scripts.check_evidence as _module


# ======================
# Config-driven constants (SSoT)
# ======================
# All paths resolve from pyproject.toml → evidence.config.yaml → parent_config.
# No hardcoded directory paths or field lists.

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Entry point: pyproject.toml [tool.check-evidence] config pointer
with open(_REPO_ROOT / "pyproject.toml", "rb") as _f:
    _PYPROJECT = tomllib.load(_f)
_EVIDENCE_CONFIG_REL = _PYPROJECT["tool"]["check-evidence"]["config"]
_EVIDENCE_CONFIG_PATH = _REPO_ROOT / _EVIDENCE_CONFIG_REL

# Evidence config → parent_config relative path → parent config
_EVIDENCE_CONFIG = yaml.safe_load(_EVIDENCE_CONFIG_PATH.read_text(encoding="utf-8"))
_PARENT_CONFIG_REL = _EVIDENCE_CONFIG["parent_config"]
_PARENT_CONFIG_PATH = _REPO_ROOT / _PARENT_CONFIG_REL
_PARENT_CONFIG = yaml.safe_load(_PARENT_CONFIG_PATH.read_text(encoding="utf-8"))

# Derived constants — all from config, nothing hardcoded
_ARTIFACT_TYPES = _EVIDENCE_CONFIG["artifact_types"]
_NAMING_PATTERNS = _EVIDENCE_CONFIG["naming_patterns"]
_LIFECYCLE = _EVIDENCE_CONFIG["lifecycle"]
_COMMON_REQUIRED_FIELDS = _EVIDENCE_CONFIG["common_required_fields"]
_DATE_FORMAT = _EVIDENCE_CONFIG["date_format"]
_VALID_TAGS = _PARENT_CONFIG["tags"]

# Default values for common fields, keyed by field name.
# "id" and "date" need type-aware formatting; handled in _build_valid_frontmatter.
_COMMON_FIELD_DEFAULTS = {
    field: f"Test {field.capitalize()}" for field in _COMMON_REQUIRED_FIELDS
}


# ======================
# Test Fixtures & Helpers
# ======================


@dataclass
class EvidenceTestEnv:
    """Test environment with isolated evidence directory structure."""

    evidence_dir: Path
    root: Path

    def dir_for(self, artifact_type: str) -> Path:
        """Return the directory for a given artifact type, from config."""
        dirname = _ARTIFACT_TYPES[artifact_type]["directory_name"]
        return self.evidence_dir / dirname


def _resolve_field_default(field: str, type_config: dict) -> object:
    """Resolve a valid default value for a required field by searching config structure.

    Resolution order (no field names are hardcoded):
    1. Direct key match in type_config (e.g., "severity" → type_config["severity"][0])
    2. Pluralized key match (e.g., "status" → type_config["statuses"][0])
    3. Key match in parent config (e.g., "tags" → [parent_config["tags"][0]])
    4. Free-text fallback for fields with no validation list
    """
    # 1. Direct key match (e.g., severity → type_config["severity"])
    if field in type_config and isinstance(type_config[field], list) and type_config[field]:
        return type_config[field][0]

    # 2. Pluralized key match (e.g., status → type_config["statuses"])
    for suffix in ("s", "es"):
        plural = field + suffix
        if plural in type_config and isinstance(type_config[plural], list) and type_config[plural]:
            return type_config[plural][0]

    # 3. Parent config match (e.g., tags → parent_config["tags"])
    if field in _PARENT_CONFIG and isinstance(_PARENT_CONFIG[field], list) and _PARENT_CONFIG[field]:
        return [_PARENT_CONFIG[field][0]]

    # 4. Free-text fallback
    return f"test-{field}-value"


def _build_valid_frontmatter(artifact_type: str, **overrides) -> dict:
    """Build a valid frontmatter dict for any artifact type, fully config-driven.

    Common fields come from evidence.config.yaml common_required_fields.
    Type-specific fields resolved via _resolve_field_default heuristic.
    Individual fields can be overridden via kwargs for negative testing.
    """
    type_config = _ARTIFACT_TYPES[artifact_type]
    prefix = type_config["id_prefix"]

    # Common required fields
    fm = dict(_COMMON_FIELD_DEFAULTS)
    # id and date need structured values, not plain strings
    fm["id"] = f"{prefix}-26001"
    fm["date"] = "2026-02-26"

    # Type-specific required fields — resolved dynamically from config
    for field in type_config["required_fields"]:
        fm[field] = _resolve_field_default(field, type_config)

    fm.update(overrides)
    return fm


def _build_valid_filename(artifact_type: str, artifact_id: str | None = None, slug: str = "test_slug") -> str:
    """Build a valid filename for a given artifact type from config prefix."""
    prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
    if artifact_id is None:
        artifact_id = f"{prefix}-26001"
    return f"{artifact_id}_{slug}.md"


def create_artifact_file(
    directory: Path,
    artifact_type: str,
    artifact_id: str | None = None,
    slug: str = "test_artifact",
    frontmatter_overrides: dict | None = None,
    sections: list[str] | None = None,
    extra_content: str = "",
) -> Path:
    """Create an evidence artifact file with valid frontmatter and sections.

    Builds valid-by-default content from config. Override specific fields
    or sections as needed for negative testing.

    Args:
        directory: Directory to create file in
        artifact_type: Type key from config (e.g., "analysis")
        artifact_id: Explicit ID (default: derived from config prefix)
        slug: Filename slug
        frontmatter_overrides: Dict of fields to override in frontmatter
        sections: List of section headers (default: required_sections from config)
        extra_content: Extra markdown to append after sections

    Returns:
        Path to created file
    """
    type_config = _ARTIFACT_TYPES[artifact_type]
    prefix = type_config["id_prefix"]
    if artifact_id is None:
        artifact_id = f"{prefix}-26001"

    fm = _build_valid_frontmatter(artifact_type, id=artifact_id)
    if frontmatter_overrides:
        fm.update(frontmatter_overrides)

    if sections is None:
        sections = list(type_config.get("required_sections", []))

    filename = f"{artifact_id}_{slug}.md"
    filepath = directory / filename

    # Build YAML frontmatter
    fm_lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            fm_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        elif value is None:
            fm_lines.append(f"{key}: null")
        else:
            fm_lines.append(f"{key}: {value}")
    fm_lines.append("---")

    # Build body
    body_lines = [
        "",
        f"# {artifact_id}: {fm.get('title', 'Test')}",
        "",
    ]
    for section in sections:
        body_lines.append(f"## {section}")
        body_lines.append("")
        body_lines.append(f"Content for {section.lower()} section.")
        body_lines.append("")

    if extra_content:
        body_lines.append(extra_content)

    content = "\n".join(fm_lines + body_lines)
    filepath.write_text(content, encoding="utf-8")
    return filepath


def create_evidence_config(path: Path) -> None:
    """Copy real evidence config to test directory (SSoT)."""
    shutil.copy2(_EVIDENCE_CONFIG_PATH, path)


def create_parent_config(path: Path) -> None:
    """Copy real architecture config to test directory (SSoT)."""
    shutil.copy2(_PARENT_CONFIG_PATH, path)


@pytest.fixture
def evidence_env(tmp_path, monkeypatch):
    """Create isolated evidence environment with configurable state."""
    # Mirror real directory structure — all paths derived from config
    config_path = tmp_path / _EVIDENCE_CONFIG_REL
    config_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_dir = config_path.parent

    for type_config in _ARTIFACT_TYPES.values():
        (evidence_dir / type_config["directory_name"]).mkdir(exist_ok=True)

    # Copy real configs to test directory
    create_evidence_config(config_path)

    parent_config_path = tmp_path / _PARENT_CONFIG_REL
    parent_config_path.parent.mkdir(parents=True, exist_ok=True)
    create_parent_config(parent_config_path)

    # pyproject.toml with the same relative path as production
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        f'[tool.check-evidence]\nconfig = "{_EVIDENCE_CONFIG_REL}"\n',
        encoding="utf-8",
    )

    # Monkeypatch module-level constants — all through _module reference
    monkeypatch.setattr(_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_module, "EVIDENCE_CONFIG_PATH", config_path)

    # Reload config with test paths
    config = _module.load_evidence_config(config_path)
    parent_config = _module.load_parent_config(config, tmp_path)

    monkeypatch.setattr(_module, "EVIDENCE_CONFIG", config)
    monkeypatch.setattr(_module, "VALID_TAGS", set(parent_config.get("tags", [])))
    monkeypatch.setattr(_module, "ARTIFACT_TYPES", config.get("artifact_types", {}))
    monkeypatch.setattr(_module, "NAMING_PATTERNS", config.get("naming_patterns", {}))
    monkeypatch.setattr(_module, "LIFECYCLE", config.get("lifecycle", {}))

    return EvidenceTestEnv(
        evidence_dir=evidence_dir,
        root=tmp_path,
    )


# ======================
# Config Loading
# ======================


class TestConfigLoading:
    """Contract: Config loads from YAML, resolves parent_config for shared tags."""

    def test_loads_evidence_config(self, evidence_env):
        """Should load evidence config with artifact_types, naming_patterns, lifecycle."""
        config = _module.load_evidence_config(evidence_env.evidence_dir / "evidence.config.yaml")

        assert "artifact_types" in config
        assert "naming_patterns" in config
        assert "lifecycle" in config

    def test_loads_parent_config_tags(self, evidence_env):
        """Should resolve parent_config and load shared tags."""
        config = _module.load_evidence_config(evidence_env.evidence_dir / "evidence.config.yaml")
        parent = _module.load_parent_config(config, evidence_env.root)

        assert "tags" in parent
        assert len(parent["tags"]) > 0

    def test_parent_config_tags_match_production(self, evidence_env):
        """Tags from parent config should match the real architecture.config.yaml."""
        config = _module.load_evidence_config(evidence_env.evidence_dir / "evidence.config.yaml")
        parent = _module.load_parent_config(config, evidence_env.root)

        assert set(parent["tags"]) == set(_VALID_TAGS)

    def test_missing_config_raises_error(self, tmp_path):
        """Should raise FileNotFoundError when config file doesn't exist."""

        with pytest.raises(FileNotFoundError):
            _module.load_evidence_config(tmp_path / "nonexistent.yaml")

    def test_missing_parent_config_raises_error(self, evidence_env):
        """Should raise FileNotFoundError when parent config doesn't exist."""
        config = _module.load_evidence_config(evidence_env.evidence_dir / "evidence.config.yaml")
        config["parent_config"] = "nonexistent/config.yaml"

        with pytest.raises(FileNotFoundError):
            _module.load_parent_config(config, evidence_env.root)

    def test_all_artifact_types_present(self, evidence_env):
        """Should load all artifact types defined in config."""
        config = _module.load_evidence_config(evidence_env.evidence_dir / "evidence.config.yaml")
        loaded_types = set(config["artifact_types"].keys())

        assert loaded_types == set(_ARTIFACT_TYPES.keys())

    def test_config_from_pyproject_pointer(self, evidence_env):
        """Should resolve config path from pyproject.toml [tool.check-evidence]."""
        config_path = _module.resolve_config_path(evidence_env.root)
        assert config_path.exists()


# ======================
# Naming Convention Validation
# ======================


class TestValidateNaming:
    """Contract: Filenames must match regex patterns from config per artifact type."""

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_valid_name_per_type(self, evidence_env, artifact_type):
        """Valid filename (built from config) should pass for each type."""
        
        filename = _build_valid_filename(artifact_type)
        errors = _module.validate_naming(filename, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_uppercase_slug_rejected(self, evidence_env, artifact_type):
        """Uppercase characters in slug should fail naming validation."""
        
        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        filename = f"{prefix}-26001_UpperCase.md"
        errors = _module.validate_naming(filename, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_missing_dash_rejected(self, evidence_env, artifact_type):
        """Missing dash between prefix and number should fail."""
        
        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        filename = f"{prefix}26001_some_slug.md"
        errors = _module.validate_naming(filename, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize("artifact_type", list(_NAMING_PATTERNS.keys()))
    def test_short_number_rejected(self, evidence_env, artifact_type):
        """Number with fewer than 5 digits should fail."""
        
        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        filename = f"{prefix}-2601_short.md"
        errors = _module.validate_naming(filename, artifact_type)
        assert len(errors) > 0

    def test_wrong_prefix_rejected(self, evidence_env):
        """Wrong prefix letter for artifact type should fail."""
        
        # Use retrospective prefix for analysis type
        errors = _module.validate_naming("R-26001_wrong_prefix.md", "analysis")
        assert len(errors) > 0


# ======================
# Frontmatter Validation
# ======================


class TestValidateFrontmatter:
    """Contract: Required fields present and valid per artifact type."""

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_valid_frontmatter_passes(self, evidence_env, artifact_type):
        """Valid frontmatter (built from config) should pass for each type."""

        fm = _build_valid_frontmatter(artifact_type)
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize("field", _COMMON_REQUIRED_FIELDS)
    def test_missing_common_field_detected(self, evidence_env, field):
        """Missing common field (id, title, date) should produce error."""

        # Use first type that has the simplest config
        first_type = list(_ARTIFACT_TYPES.keys())[0]
        fm = _build_valid_frontmatter(first_type)
        del fm[field]

        errors = _module.validate_frontmatter(fm, first_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type,field",
        [
            (atype, field)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            for field in tcfg["required_fields"]
        ],
    )
    def test_missing_type_specific_field_detected(self, evidence_env, artifact_type, field):
        """Missing type-specific required field should produce error."""

        fm = _build_valid_frontmatter(artifact_type)
        del fm[field]

        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type,status",
        [
            (atype, status)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            if tcfg["statuses"]
            for status in tcfg["statuses"]
        ],
    )
    def test_all_valid_statuses_accepted(self, evidence_env, artifact_type, status):
        """All statuses from config should be accepted."""

        fm = _build_valid_frontmatter(artifact_type, status=status)
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type",
        [atype for atype, tcfg in _ARTIFACT_TYPES.items() if tcfg["statuses"]],
    )
    def test_invalid_status_detected(self, evidence_env, artifact_type):
        """Invalid status should produce error for types with status validation."""

        fm = _build_valid_frontmatter(artifact_type, status="bogus_nonexistent_status")
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type",
        [atype for atype, tcfg in _ARTIFACT_TYPES.items() if not tcfg["statuses"]],
    )
    def test_no_status_validation_for_statusless_types(self, evidence_env, artifact_type):
        """Types with empty statuses list should not require or validate status."""

        fm = _build_valid_frontmatter(artifact_type)
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type,severity",
        [
            (atype, sev)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            if "severity" in tcfg
            for sev in tcfg["severity"]
        ],
    )
    def test_all_valid_severities_accepted(self, evidence_env, artifact_type, severity):
        """All severity levels from config should be accepted."""

        fm = _build_valid_frontmatter(artifact_type, severity=severity)
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type",
        [atype for atype, tcfg in _ARTIFACT_TYPES.items() if "severity" in tcfg],
    )
    def test_invalid_severity_detected(self, evidence_env, artifact_type):
        """Invalid severity should produce error for types with severity validation."""

        fm = _build_valid_frontmatter(artifact_type, severity="catastrophic_nonexistent")
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) > 0

    def test_invalid_tag_detected(self, evidence_env):
        """Tag not in parent config should produce error."""

        # Use any type that requires tags
        types_with_tags = [
            atype for atype, tcfg in _ARTIFACT_TYPES.items()
            if "tags" in tcfg["required_fields"]
        ]
        if not types_with_tags:
            pytest.skip("No artifact types require tags")

        artifact_type = types_with_tags[0]
        fm = _build_valid_frontmatter(artifact_type, tags=["nonexistent_invalid_tag_xyz"])
        errors = _module.validate_frontmatter(fm, artifact_type)
        assert len(errors) > 0

    def test_invalid_date_format_detected(self, evidence_env):
        """Date not matching YYYY-MM-DD should produce error."""

        first_type = list(_ARTIFACT_TYPES.keys())[0]
        fm = _build_valid_frontmatter(first_type, date="26-02-2026")
        errors = _module.validate_frontmatter(fm, first_type)
        assert len(errors) > 0


# ======================
# Section Validation
# ======================


class TestValidateSections:
    """Contract: Required sections present, no unexpected sections."""

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_required_sections_pass(self, evidence_env, artifact_type):
        """Artifact with exactly the required sections should pass."""

        required = list(_ARTIFACT_TYPES[artifact_type].get("required_sections", []))
        errors = _module.validate_sections(required, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_required_plus_optional_pass(self, evidence_env, artifact_type):
        """Artifact with required + optional sections should pass."""

        type_config = _ARTIFACT_TYPES[artifact_type]
        all_sections = (
            list(type_config.get("required_sections", []))
            + list(type_config.get("optional_sections", []))
        )
        errors = _module.validate_sections(all_sections, artifact_type)
        assert len(errors) == 0

    @pytest.mark.parametrize(
        "artifact_type,missing_section",
        [
            (atype, section)
            for atype, tcfg in _ARTIFACT_TYPES.items()
            for section in tcfg.get("required_sections", [])
        ],
    )
    def test_missing_required_section_detected(self, evidence_env, artifact_type, missing_section):
        """Each missing required section should produce error."""

        required = list(_ARTIFACT_TYPES[artifact_type]["required_sections"])
        sections = [s for s in required if s != missing_section]
        errors = _module.validate_sections(sections, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type",
        [
            atype for atype, tcfg in _ARTIFACT_TYPES.items()
            if tcfg.get("required_sections") or tcfg.get("optional_sections")
        ],
    )
    def test_unexpected_section_detected(self, evidence_env, artifact_type):
        """Section not in required or optional should produce error."""

        required = list(_ARTIFACT_TYPES[artifact_type].get("required_sections", []))
        sections = required + ["Completely Unknown Section XYZ"]
        errors = _module.validate_sections(sections, artifact_type)
        assert len(errors) > 0

    @pytest.mark.parametrize(
        "artifact_type",
        [
            atype for atype, tcfg in _ARTIFACT_TYPES.items()
            if not tcfg.get("required_sections") and not tcfg.get("optional_sections")
        ],
    )
    def test_freeform_types_accept_any_sections(self, evidence_env, artifact_type):
        """Types with no required/optional sections should accept anything."""

        sections = ["Anything Goes", "Another Header"]
        errors = _module.validate_sections(sections, artifact_type)
        assert len(errors) == 0


# ======================
# Orphaned Source Detection
# ======================


class TestDetectOrphanedSources:
    """Contract: Sources with extracted_into=null older than threshold produce warnings."""

    def test_no_orphans_when_extracted(self, evidence_env):
        """Source with extracted_into set should not be flagged."""

        sources_dir = evidence_env.dir_for("source")
        create_artifact_file(
            sources_dir,
            artifact_type="source",
            frontmatter_overrides={"extracted_into": "A-26001", "date": "2025-01-01"},
        )
        warnings = _module.detect_orphaned_sources(sources_dir)
        assert len(warnings) == 0

    def test_recent_unextracted_not_flagged(self, evidence_env):
        """Source with null extracted_into but recent date should not be flagged."""

        sources_dir = evidence_env.dir_for("source")
        create_artifact_file(
            sources_dir,
            artifact_type="source",
            frontmatter_overrides={"extracted_into": None, "date": "2026-02-27"},
        )
        warnings = _module.detect_orphaned_sources(sources_dir)
        assert len(warnings) == 0

    def test_old_unextracted_flagged(self, evidence_env):
        """Source with null extracted_into older than threshold should be flagged."""

        sources_dir = evidence_env.dir_for("source")
        create_artifact_file(
            sources_dir,
            artifact_type="source",
            frontmatter_overrides={"extracted_into": None, "date": "2025-01-01"},
        )
        warnings = _module.detect_orphaned_sources(sources_dir)
        assert len(warnings) > 0


# ======================
# Artifact Discovery
# ======================


class TestDiscoverArtifacts:
    """Contract: Scans correct directories per config, returns sorted artifacts."""

    @pytest.mark.parametrize("artifact_type", list(_ARTIFACT_TYPES.keys()))
    def test_discovers_artifacts_per_type(self, evidence_env, artifact_type):
        """Should find artifact files in the type's directory."""

        target_dir = evidence_env.dir_for(artifact_type)
        create_artifact_file(target_dir, artifact_type=artifact_type)

        artifacts = _module.discover_artifacts(artifact_type)
        assert len(artifacts) == 1

    def test_returns_sorted_by_id(self, evidence_env):
        """Artifacts should be returned sorted by ID."""

        # Pick any type for this test
        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        target_dir = evidence_env.dir_for(artifact_type)

        # Create in reverse order
        for num in [26003, 26001, 26002]:
            create_artifact_file(
                target_dir,
                artifact_type=artifact_type,
                artifact_id=f"{prefix}-{num}",
                slug=f"item_{num}",
            )

        artifacts = _module.discover_artifacts(artifact_type)
        ids = [a.artifact_id for a in artifacts]
        assert ids == [f"{prefix}-26001", f"{prefix}-26002", f"{prefix}-26003"]

    def test_empty_directory_returns_empty_list(self, evidence_env):
        """Empty directory should return empty list."""

        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        artifacts = _module.discover_artifacts(artifact_type)
        assert artifacts == []

    def test_ignores_non_matching_files(self, evidence_env):
        """Files not matching naming pattern (e.g., README.md) should be skipped."""

        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        target_dir = evidence_env.dir_for(artifact_type)

        readme = target_dir / "README.md"
        readme.write_text("# README\n", encoding="utf-8")

        artifacts = _module.discover_artifacts(artifact_type)
        assert len(artifacts) == 0


# ======================
# CLI Integration
# ======================


class TestCli:
    """Contract: Exit 0 on valid artifacts, exit 1 on validation errors."""

    def test_exit_0_on_valid_artifacts(self, evidence_env):
        """Should exit 0 when all artifacts are valid."""

        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        create_artifact_file(evidence_env.dir_for(artifact_type), artifact_type=artifact_type)

        with patch("sys.argv", ["check_evidence"]):
            with pytest.raises(SystemExit) as exc_info:
                _module.main()

        assert exc_info.value.code == 0

    def test_exit_1_on_validation_errors(self, evidence_env):
        """Should exit 1 when validation errors exist."""

        # Create a file with missing required fields
        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        prefix = _ARTIFACT_TYPES[artifact_type]["id_prefix"]
        target_dir = evidence_env.dir_for(artifact_type)

        bad_file = target_dir / f"{prefix}-26001_bad_artifact.md"
        bad_file.write_text(
            f"---\nid: {prefix}-26001\ntitle: Bad\n---\n\n# {prefix}-26001: Bad\n",
            encoding="utf-8",
        )

        with patch("sys.argv", ["check_evidence"]):
            with pytest.raises(SystemExit) as exc_info:
                _module.main()

        assert exc_info.value.code == 1

    def test_exit_0_on_empty_evidence(self, evidence_env):
        """Should exit 0 when no evidence artifacts exist (nothing to validate)."""

        with patch("sys.argv", ["check_evidence"]):
            with pytest.raises(SystemExit) as exc_info:
                _module.main()

        assert exc_info.value.code == 0

    def test_verbose_flag_accepted(self, evidence_env):
        """Should accept --verbose flag without error."""

        artifact_type = list(_ARTIFACT_TYPES.keys())[0]
        create_artifact_file(evidence_env.dir_for(artifact_type), artifact_type=artifact_type)

        with patch("sys.argv", ["check_evidence", "--verbose"]):
            with pytest.raises(SystemExit) as exc_info:
                _module.main()

        assert exc_info.value.code == 0

    def test_check_staged_flag_accepted(self, evidence_env):
        """Should accept --check-staged flag without error."""

        with patch("sys.argv", ["check_evidence", "--check-staged"]):
            with pytest.raises(SystemExit) as exc_info:
                _module.main()

        assert exc_info.value.code == 0
