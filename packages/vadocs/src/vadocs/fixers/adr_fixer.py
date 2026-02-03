"""
ADR document fixer.

Automatically fixes common ADR issues:
- Invalid status values (using configured corrections)
- Title mismatch between header and frontmatter
- Missing YAML frontmatter (migration from legacy format)

This fixer works with AdrValidator - it can fix many of the issues
that the validator detects.

Configuration (from adr_config.yaml):
- status_corrections: Dict mapping typos/synonyms to correct status
- default_status: Status to use when none can be determined
- statuses: List of valid status values

Usage:
    from vadocs.fixers.adr_fixer import AdrFixer

    fixer = AdrFixer()
    config = load_config("adr_config.yaml")
    result = fixer.fix(document, config, dry_run=False)
"""

import re
from pathlib import Path

from vadocs.core.models import Document, SyncResult
from vadocs.core.parsing import FRONTMATTER_PATTERN, parse_frontmatter
from vadocs.fixers.base import Fixer


class AdrFixer(Fixer):
    """Fixer for Architecture Decision Records (ADRs).

    Fixes common ADR issues like invalid statuses and title mismatches.
    """

    name = "adr"

    def supports(self, document: Document) -> bool:
        """Check if document is an ADR.

        Supports documents with doc_type="adr" or files matching adr_*.md pattern.
        """
        if document.doc_type == "adr":
            return True
        return document.path.name.startswith("adr_") and document.path.suffix == ".md"

    def fix(self, document: Document, config: dict, dry_run: bool = False) -> SyncResult:
        """Fix ADR document issues.

        Args:
            document: The ADR document to fix.
            config: Configuration with status_corrections, default_status, etc.
            dry_run: If True, report changes without modifying files.

        Returns:
            SyncResult with changes made and any errors.
        """
        changes: list[str] = []
        errors: list[str] = []
        modified = False

        content = document.content
        frontmatter = document.frontmatter or parse_frontmatter(content)

        # Fix invalid status
        new_content, status_changes = self._fix_invalid_status(
            content, frontmatter, config, dry_run
        )
        if status_changes:
            changes.extend(status_changes)
            content = new_content
            modified = True

        # Fix title mismatch
        new_content, title_changes = self._fix_title_mismatch(content, frontmatter, dry_run)
        if title_changes:
            changes.extend(title_changes)
            content = new_content
            modified = True

        # Write changes if not dry run
        if modified and not dry_run:
            document.path.write_text(content, encoding="utf-8")

        return SyncResult(
            modified=modified and not dry_run,
            changes=changes,
            errors=errors,
        )

    def _fix_invalid_status(
        self, content: str, frontmatter: dict | None, config: dict, dry_run: bool
    ) -> tuple[str, list[str]]:
        """Fix invalid status using configured corrections.

        Returns:
            Tuple of (new_content, list of change descriptions).
        """
        changes = []
        valid_statuses = set(config.get("statuses", []))
        corrections = self._build_corrections(config)
        default_status = config.get("default_status", "proposed")

        if frontmatter is None:
            return content, changes

        status = frontmatter.get("status")
        if status is None:
            return content, changes

        status_lower = str(status).lower()
        if status_lower in valid_statuses:
            return content, changes

        # Try to find correction
        new_status = corrections.get(status_lower, default_status)

        if new_status not in valid_statuses:
            return content, changes

        # Update frontmatter
        def replace_status(match: re.Match) -> str:
            frontmatter_content = match.group(1)
            updated = re.sub(
                r"^status:\s*.+$",
                f"status: {new_status}",
                frontmatter_content,
                flags=re.MULTILINE,
            )
            return f"---\n{updated}\n---\n"

        new_content = FRONTMATTER_PATTERN.sub(replace_status, content)
        changes.append(f"Fixed status: '{status}' -> '{new_status}'")

        return new_content, changes

    def _fix_title_mismatch(
        self, content: str, frontmatter: dict | None, dry_run: bool
    ) -> tuple[str, list[str]]:
        """Fix title mismatch by updating frontmatter to match header.

        Returns:
            Tuple of (new_content, list of change descriptions).
        """
        changes = []

        if frontmatter is None:
            return content, changes

        frontmatter_title = frontmatter.get("title")
        if frontmatter_title is None:
            return content, changes

        # Extract title from header
        header_match = re.search(r"^#\s+ADR-\d+:\s+(.+)$", content, re.MULTILINE)
        if not header_match:
            return content, changes

        header_title = header_match.group(1).strip()

        if frontmatter_title == header_title:
            return content, changes

        # Update frontmatter title to match header
        def replace_title(match: re.Match) -> str:
            frontmatter_content = match.group(1)
            updated = re.sub(
                r"^title:\s*.+$",
                f"title: {header_title}",
                frontmatter_content,
                flags=re.MULTILINE,
            )
            return f"---\n{updated}\n---\n"

        new_content = FRONTMATTER_PATTERN.sub(replace_title, content)
        changes.append(f"Fixed title mismatch: '{frontmatter_title}' -> '{header_title}'")

        return new_content, changes

    def _build_corrections(self, config: dict) -> dict[str, str]:
        """Build typo-to-correct-status mapping from config."""
        mapping = {}
        for correct_status, typos in config.get("status_corrections", {}).items():
            for typo in typos:
                mapping[typo.lower()] = correct_status
        return mapping
