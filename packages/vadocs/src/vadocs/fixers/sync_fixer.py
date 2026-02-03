"""
Bi-directional sync fixer for YAML frontmatter and markdown content.

Synchronizes fields that can exist in both YAML frontmatter and markdown
sections. Detects mismatches and can sync in either direction.

Sync-able fields (for ADRs):
- title: YAML `title:` <-> `# ADR-XXXXX: Title` header
- date: YAML `date:` <-> `## Date` section
- status: YAML `status:` <-> `## Status` section

Sync modes:
- auto: Determine direction automatically (one source has value, other doesn't)
- yaml_to_md: Use YAML as source of truth
- md_to_yaml: Use markdown as source of truth

If both sources have different values and mode is 'auto', sync reports an
error and requires explicit direction choice.

Usage:
    from vadocs.fixers.sync_fixer import SyncFixer

    fixer = SyncFixer()
    config = {"sync_direction": "auto"}
    result = fixer.fix(document, config, dry_run=True)
"""

import re
from enum import Enum

from vadocs.core.models import Document, SyncField, SyncResult
from vadocs.core.parsing import (
    FRONTMATTER_PATTERN,
    SECTION_HEADER_PATTERN,
    extract_section_content,
    parse_frontmatter,
)
from vadocs.fixers.base import Fixer


class SyncDirection(str, Enum):
    """Direction for bi-directional sync."""

    AUTO = "auto"
    YAML_TO_MD = "yaml_to_md"
    MD_TO_YAML = "md_to_yaml"


class SyncFixer(Fixer):
    """Bi-directional sync fixer for frontmatter and markdown.

    Synchronizes fields between YAML frontmatter and corresponding
    markdown sections.
    """

    name = "sync"

    def supports(self, document: Document) -> bool:
        """Check if document supports sync.

        Supports any document with YAML frontmatter.
        """
        if document.frontmatter is not None:
            return True
        return parse_frontmatter(document.content) is not None

    def fix(self, document: Document, config: dict, dry_run: bool = False) -> SyncResult:
        """Synchronize frontmatter and markdown content.

        Args:
            document: The document to sync.
            config: Configuration with sync_direction and field mappings.
            dry_run: If True, report changes without modifying files.

        Returns:
            SyncResult with changes made and any errors.
        """
        changes: list[str] = []
        errors: list[str] = []

        direction = SyncDirection(config.get("sync_direction", "auto"))
        sync_fields = config.get("sync_fields", ["title", "status", "date"])

        content = document.content
        frontmatter = document.frontmatter or parse_frontmatter(content)

        if frontmatter is None:
            errors.append("No YAML frontmatter found - cannot sync")
            return SyncResult(modified=False, changes=[], errors=errors)

        # Extract current values from both sources
        fields = self._extract_sync_fields(content, frontmatter, sync_fields)

        # Determine what needs syncing
        for field in fields:
            if field.is_synced:
                continue

            # Both have values but differ - need direction
            if field.yaml_value is not None and field.markdown_value is not None:
                if direction == SyncDirection.AUTO:
                    errors.append(
                        f"Field '{field.name}' has conflicting values: "
                        f"YAML='{field.yaml_value}', markdown='{field.markdown_value}'. "
                        "Specify --sync-direction to resolve."
                    )
                    continue
                elif direction == SyncDirection.YAML_TO_MD:
                    content, change = self._sync_field_to_markdown(
                        content, field.name, field.yaml_value
                    )
                    if change:
                        changes.append(change)
                else:  # MD_TO_YAML
                    content, change = self._sync_field_to_yaml(
                        content, field.name, field.markdown_value
                    )
                    if change:
                        changes.append(change)

            # Only YAML has value - sync to markdown
            elif field.yaml_value is not None:
                if direction in (SyncDirection.AUTO, SyncDirection.YAML_TO_MD):
                    content, change = self._sync_field_to_markdown(
                        content, field.name, field.yaml_value
                    )
                    if change:
                        changes.append(change)

            # Only markdown has value - sync to YAML
            elif field.markdown_value is not None:
                if direction in (SyncDirection.AUTO, SyncDirection.MD_TO_YAML):
                    content, change = self._sync_field_to_yaml(
                        content, field.name, field.markdown_value
                    )
                    if change:
                        changes.append(change)

        # Write changes if not dry run
        modified = len(changes) > 0
        if modified and not dry_run:
            document.path.write_text(content, encoding="utf-8")

        return SyncResult(
            modified=modified and not dry_run,
            changes=changes,
            errors=errors,
        )

    def _extract_sync_fields(
        self, content: str, frontmatter: dict, field_names: list[str]
    ) -> list[SyncField]:
        """Extract values for sync fields from both sources."""
        fields = []

        for name in field_names:
            yaml_value = frontmatter.get(name)
            if yaml_value is not None:
                yaml_value = str(yaml_value)

            # Extract from markdown based on field name
            md_value = self._extract_markdown_value(content, name)

            fields.append(
                SyncField(
                    name=name,
                    yaml_value=yaml_value,
                    markdown_value=md_value,
                )
            )

        return fields

    def _extract_markdown_value(self, content: str, field_name: str) -> str | None:
        """Extract field value from markdown content."""
        if field_name == "title":
            # Extract from header: # ADR-XXXXX: Title
            match = re.search(r"^#\s+ADR-\d+:\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        elif field_name == "status":
            # Extract from ## Status section
            section = extract_section_content(content, "Status")
            if section:
                # First word after Status header
                match = re.match(r"\s*(\w+)", section)
                if match:
                    return match.group(1).lower()

        elif field_name == "date":
            # Extract from ## Date section
            section = extract_section_content(content, "Date")
            if section:
                # Look for YYYY-MM-DD pattern
                match = re.search(r"(\d{4}-\d{2}-\d{2})", section)
                if match:
                    return match.group(1)

        return None

    def _sync_field_to_markdown(
        self, content: str, field_name: str, value: str
    ) -> tuple[str, str | None]:
        """Sync field value from YAML to markdown.

        Returns:
            Tuple of (new_content, change_description or None).
        """
        if field_name == "title":
            # Update header title
            new_content = re.sub(
                r"^(#\s+ADR-\d+:\s+).+$",
                rf"\g<1>{value}",
                content,
                count=1,
                flags=re.MULTILINE,
            )
            if new_content != content:
                return new_content, f"Updated markdown title to '{value}'"

        elif field_name == "status":
            # Update ## Status section content
            section = extract_section_content(content, "Status")
            if section:
                # Replace first word in section
                old_section = section
                new_section = re.sub(r"^\s*\w+", f"\n{value.capitalize()}", section, count=1)
                new_content = content.replace(old_section, new_section)
                if new_content != content:
                    return new_content, f"Updated markdown status to '{value}'"

        elif field_name == "date":
            # Update ## Date section
            section = extract_section_content(content, "Date")
            if section:
                old_section = section
                new_section = re.sub(r"\d{4}-\d{2}-\d{2}", value, section, count=1)
                new_content = content.replace(old_section, new_section)
                if new_content != content:
                    return new_content, f"Updated markdown date to '{value}'"

        return content, None

    def _sync_field_to_yaml(
        self, content: str, field_name: str, value: str
    ) -> tuple[str, str | None]:
        """Sync field value from markdown to YAML.

        Returns:
            Tuple of (new_content, change_description or None).
        """

        def replace_field(match: re.Match) -> str:
            frontmatter_content = match.group(1)
            # Check if field exists
            if re.search(rf"^{field_name}:", frontmatter_content, re.MULTILINE):
                # Update existing field
                updated = re.sub(
                    rf"^{field_name}:\s*.+$",
                    f"{field_name}: {value}",
                    frontmatter_content,
                    flags=re.MULTILINE,
                )
            else:
                # Add new field
                updated = frontmatter_content.rstrip() + f"\n{field_name}: {value}\n"
            return f"---\n{updated}\n---\n"

        new_content = FRONTMATTER_PATTERN.sub(replace_field, content)
        if new_content != content:
            return new_content, f"Updated YAML {field_name} to '{value}'"

        return content, None
