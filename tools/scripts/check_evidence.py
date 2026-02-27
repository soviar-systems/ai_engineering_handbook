#!/usr/bin/env python3
"""
Evidence Artifact Validator.

Validates evidence artifacts (analyses, retrospectives, sources) in
architecture/evidence/ against the schema defined in evidence.config.yaml.

Exit codes:
    0: All artifacts are valid
    1: Validation errors found
"""

import argparse
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import yaml


# ======================
# Data Classes
# ======================


@dataclass
class EvidenceArtifact:
    """Represents an evidence artifact on disk."""

    path: Path
    artifact_id: str
    artifact_type: str
    frontmatter: dict | None = None
    content: str | None = None


@dataclass
class ValidationError:
    """Represents a validation error."""

    artifact_id: str
    error_type: str
    message: str


# ======================
# Configuration
# ======================

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SECTION_HEADER_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def _detect_repo_root() -> Path:
    """Detect repository root via git, with __file__ fallback."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path(__file__).resolve().parent.parent.parent


def resolve_config_path(repo_root: Path) -> Path:
    """Resolve evidence config path from pyproject.toml [tool.check-evidence].

    Args:
        repo_root: Repository root directory.

    Returns:
        Absolute path to evidence.config.yaml.

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist.
        KeyError: If [tool.check-evidence] section is missing.
    """
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found: {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    rel_path = pyproject["tool"]["check-evidence"]["config"]
    return repo_root / rel_path


def load_evidence_config(config_path: Path) -> dict:
    """Load evidence configuration from YAML file.

    Args:
        config_path: Path to evidence.config.yaml.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Evidence config not found: {config_path}")

    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def load_parent_config(evidence_config: dict, repo_root: Path) -> dict:
    """Load parent config (shared tags) resolved via parent_config pointer.

    Args:
        evidence_config: Loaded evidence configuration.
        repo_root: Repository root directory.

    Returns:
        Parent configuration dictionary (architecture.config.yaml).

    Raises:
        FileNotFoundError: If parent config file doesn't exist.
    """
    parent_rel = evidence_config.get("parent_config", "")
    parent_path = repo_root / parent_rel

    if not parent_path.exists():
        raise FileNotFoundError(f"Parent config not found: {parent_path}")

    return yaml.safe_load(parent_path.read_text(encoding="utf-8"))


# Module-level constants — loaded once at import time, monkeypatched in tests
REPO_ROOT: Path = _detect_repo_root()
EVIDENCE_CONFIG_PATH: Path = resolve_config_path(REPO_ROOT)
EVIDENCE_CONFIG: dict = load_evidence_config(EVIDENCE_CONFIG_PATH)
_parent_config: dict = load_parent_config(EVIDENCE_CONFIG, REPO_ROOT)

VALID_TAGS: set[str] = set(_parent_config.get("tags", []))
ARTIFACT_TYPES: dict = EVIDENCE_CONFIG.get("artifact_types", {})
NAMING_PATTERNS: dict = EVIDENCE_CONFIG.get("naming_patterns", {})
LIFECYCLE: dict = EVIDENCE_CONFIG.get("lifecycle", {})
COMMON_REQUIRED_FIELDS: list[str] = EVIDENCE_CONFIG.get("common_required_fields", [])
DATE_FORMAT_PATTERN: str = EVIDENCE_CONFIG.get("date_format", r"^\d{4}-\d{2}-\d{2}$")


# ======================
# Main
# ======================


def main() -> None:
    """Validate all evidence artifacts. Exit 0 if valid, 1 if errors found."""
    parser = argparse.ArgumentParser(description="Validate evidence artifacts.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--check-staged", action="store_true", help="Only validate staged files")
    args = parser.parse_args()

    all_errors: list[ValidationError] = []
    all_warnings: list[ValidationError] = []
    artifact_count = 0

    staged_files = _get_staged_files() if args.check_staged else None

    for artifact_type in ARTIFACT_TYPES:
        artifacts = discover_artifacts(artifact_type)

        for artifact in artifacts:
            if staged_files is not None:
                try:
                    rel_path = str(artifact.path.relative_to(REPO_ROOT))
                except ValueError:
                    rel_path = str(artifact.path)
                if rel_path not in staged_files:
                    continue

            artifact_count += 1

            if args.verbose:
                print(f"  Validating {artifact.artifact_id} ({artifact_type})")

            all_errors.extend(validate_naming(artifact.path.name, artifact_type))

            if artifact.frontmatter:
                all_errors.extend(validate_frontmatter(artifact.frontmatter, artifact_type))

            if artifact.content:
                sections = _extract_sections(artifact.content)
                section_errors = validate_sections(sections, artifact_type)
                for err in section_errors:
                    err.artifact_id = artifact.artifact_id
                all_errors.extend(section_errors)

    # Orphaned source detection
    source_type = next((k for k, v in ARTIFACT_TYPES.items() if not v.get("statuses")), None)
    if source_type:
        sources_dir = EVIDENCE_CONFIG_PATH.parent / ARTIFACT_TYPES[source_type]["directory_name"]
        all_warnings.extend(detect_orphaned_sources(sources_dir))

    # Report
    if args.verbose or all_errors or all_warnings:
        print(f"\nEvidence validation: {artifact_count} artifacts checked")

    if all_warnings:
        print(f"\n  Warnings ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"    {w.artifact_id}: {w.message}")

    if all_errors:
        print(f"\n  Errors ({len(all_errors)}):")
        for e in all_errors:
            print(f"    {e.artifact_id}: [{e.error_type}] {e.message}")
        sys.exit(1)

    if args.verbose:
        print("  All artifacts valid.")

    sys.exit(0)


# ======================
# Validation
# ======================


def validate_naming(filename: str, artifact_type: str) -> list[ValidationError]:
    """Validate filename against naming pattern from config.

    Args:
        filename: Filename (with .md extension).
        artifact_type: Artifact type key from config.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    pattern_str = NAMING_PATTERNS.get(artifact_type)

    if pattern_str is None:
        errors.append(ValidationError(
            artifact_id=filename,
            error_type="naming",
            message=f"No naming pattern defined for type '{artifact_type}'",
        ))
        return errors

    stem = filename.removesuffix(".md") if filename.endswith(".md") else filename

    if not re.compile(pattern_str).match(stem):
        errors.append(ValidationError(
            artifact_id=filename,
            error_type="naming",
            message=f"Filename '{filename}' does not match pattern: {pattern_str}",
        ))

    return errors


def validate_frontmatter(frontmatter: dict, artifact_type: str) -> list[ValidationError]:
    """Validate frontmatter fields against config requirements.

    Checks common required fields, type-specific required fields,
    valid statuses/severity/tags, and date format.

    Args:
        frontmatter: Parsed YAML frontmatter dict.
        artifact_type: Artifact type key from config.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    type_config = ARTIFACT_TYPES.get(artifact_type, {})
    artifact_id = frontmatter.get("id", "unknown")

    # Common required fields
    for field_name in COMMON_REQUIRED_FIELDS:
        if field_name not in frontmatter:
            errors.append(ValidationError(
                artifact_id=artifact_id,
                error_type="frontmatter",
                message=f"Missing required field: {field_name}",
            ))

    # Type-specific required fields
    for field_name in type_config.get("required_fields", []):
        if field_name not in frontmatter:
            errors.append(ValidationError(
                artifact_id=artifact_id,
                error_type="frontmatter",
                message=f"Missing required field: {field_name}",
            ))

    # Date format
    date_value = frontmatter.get("date")
    if date_value is not None:
        date_str = str(date_value)
        if not re.match(DATE_FORMAT_PATTERN, date_str):
            errors.append(ValidationError(
                artifact_id=artifact_id,
                error_type="frontmatter",
                message=f"Invalid date format: '{date_str}' (expected YYYY-MM-DD)",
            ))

    # Status (only for types with non-empty statuses list)
    valid_statuses = type_config.get("statuses", [])
    if valid_statuses and "status" in frontmatter:
        if frontmatter["status"] not in valid_statuses:
            errors.append(ValidationError(
                artifact_id=artifact_id,
                error_type="frontmatter",
                message=f"Invalid status: '{frontmatter['status']}' (valid: {valid_statuses})",
            ))

    # Severity (only for types with severity list)
    valid_severities = type_config.get("severity", [])
    if valid_severities and "severity" in frontmatter:
        if frontmatter["severity"] not in valid_severities:
            errors.append(ValidationError(
                artifact_id=artifact_id,
                error_type="frontmatter",
                message=f"Invalid severity: '{frontmatter['severity']}' (valid: {valid_severities})",
            ))

    # Tags (against parent config tags)
    if "tags" in frontmatter and isinstance(frontmatter["tags"], list):
        invalid_tags = [t for t in frontmatter["tags"] if t not in VALID_TAGS]
        if invalid_tags:
            errors.append(ValidationError(
                artifact_id=artifact_id,
                error_type="frontmatter",
                message=f"Invalid tags: {invalid_tags} (valid: {sorted(VALID_TAGS)})",
            ))

    return errors


def validate_sections(sections: list[str], artifact_type: str) -> list[ValidationError]:
    """Validate document sections against config requirements.

    Types with no required/optional sections accept anything (free-form).

    Args:
        sections: List of ## section headers found in document.
        artifact_type: Artifact type key from config.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    type_config = ARTIFACT_TYPES.get(artifact_type, {})

    required_sections = type_config.get("required_sections", [])
    optional_sections = type_config.get("optional_sections", [])

    if not required_sections and not optional_sections:
        return errors

    allowed_sections = set(required_sections) | set(optional_sections)

    for section in required_sections:
        if section not in sections:
            errors.append(ValidationError(
                artifact_id="",
                error_type="sections",
                message=f"Missing required section: '{section}'",
            ))

    for section in sections:
        if section not in allowed_sections:
            errors.append(ValidationError(
                artifact_id="",
                error_type="sections",
                message=f"Unexpected section: '{section}' (allowed: {sorted(allowed_sections)})",
            ))

    return errors


def detect_orphaned_sources(sources_dir: Path) -> list[ValidationError]:
    """Detect source files with null extracted_into older than threshold.

    Args:
        sources_dir: Path to evidence/sources/ directory.

    Returns:
        List of warning-level validation errors.
    """
    warnings = []
    orphan_days = LIFECYCLE.get("orphan_warning_days", 30)
    threshold = date.today() - timedelta(days=orphan_days)

    if not sources_dir.exists():
        return warnings

    for md_file in sorted(sources_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        fm_match = FRONTMATTER_PATTERN.match(content)
        if not fm_match:
            continue

        fm = yaml.safe_load(fm_match.group(1))
        if fm is None:
            continue

        if fm.get("extracted_into") is not None:
            continue

        date_str = str(fm.get("date", ""))
        try:
            source_date = date.fromisoformat(date_str)
        except (ValueError, TypeError):
            continue

        if source_date < threshold:
            warnings.append(ValidationError(
                artifact_id=fm.get("id", md_file.stem),
                error_type="orphan",
                message=f"Source has null extracted_into and is {(date.today() - source_date).days} days old",
            ))

    return warnings


# ======================
# Discovery
# ======================


def discover_artifacts(artifact_type: str) -> list[EvidenceArtifact]:
    """Discover and parse evidence artifacts of a given type.

    Scans the type's directory (from config), filters by naming pattern,
    parses frontmatter, and returns sorted by ID.

    Args:
        artifact_type: Artifact type key from config.

    Returns:
        List of EvidenceArtifact sorted by artifact_id.
    """
    type_config = ARTIFACT_TYPES.get(artifact_type, {})
    directory_name = type_config.get("directory_name", "")

    evidence_dir = EVIDENCE_CONFIG_PATH.parent
    target_dir = evidence_dir / directory_name

    if not target_dir.exists():
        return []

    pattern_str = NAMING_PATTERNS.get(artifact_type)
    if pattern_str is None:
        return []

    pattern = re.compile(pattern_str)
    artifacts = []

    for md_file in target_dir.glob("*.md"):
        stem = md_file.stem
        if not pattern.match(stem):
            continue

        content = md_file.read_text(encoding="utf-8")
        fm_match = FRONTMATTER_PATTERN.match(content)
        fm = yaml.safe_load(fm_match.group(1)) if fm_match else {}
        artifact_id = fm.get("id", stem.split("_")[0] if "_" in stem else stem)

        artifacts.append(EvidenceArtifact(
            path=md_file,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            frontmatter=fm,
            content=content,
        ))

    return sorted(artifacts, key=lambda a: a.artifact_id)


# ======================
# Helpers
# ======================


def _extract_sections(content: str) -> list[str]:
    """Extract ## section headers from markdown content, ignoring code fences."""
    stripped = CODE_FENCE_PATTERN.sub("", content)
    return SECTION_HEADER_PATTERN.findall(stripped)


def _get_staged_files() -> set[str]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except subprocess.CalledProcessError:
        return set()


if __name__ == "__main__":
    main()
