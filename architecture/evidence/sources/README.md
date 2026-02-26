# Evidence Sources

This directory holds **ephemeral source material** — dialogue transcripts, meeting notes, and raw research inputs — that feed into analyses (`evidence/analyses/`) and ultimately produce ADRs (`decisions/`).

## Lifecycle

Sources follow a three-commit minimum workflow:

1. **Commit 1 — Capture:** Add the transcript to `evidence/sources/S-YYNNN_slug.md`
2. **Commit 2 — Extract:** Write the analysis to `evidence/analyses/A-YYNNN_slug.md` with `sources: [S-YYNNN]`. Update the source's `extracted_into` field to point at the analysis.
3. **Commit 3 — Delete:** Remove the source file. Git history preserves it at a predictable path.

**Rule:** A source is only deleted AFTER its `extracted_into` field points to a committed analysis.

## Naming Convention

`S-YYNNN_descriptive_slug.md` where:
- `S` = Source namespace prefix
- `YY` = Two-digit year (e.g., `26` for 2026)
- `NNN` = Sequential number within the year (e.g., `001`)
- `_descriptive_slug` = Kebab-style description

## Frontmatter Schema

```yaml
---
id: S-26001
title: "Claude — AKB Taxonomy Discussion"
date: 2026-02-26
model: claude-opus-4     # AI model used, or "human" for meeting notes
extracted_into: A-26001  # null until analysis exists
---
```

## Git Archaeology

Sources are designed to be committed and then deleted. The git history preserves them permanently at predictable paths.

**Search for deleted transcripts:**

```bash
git log --all --full-history -- architecture/evidence/sources/
```

**Recover a specific deleted transcript:**

```bash
git show <commit-hash>:architecture/evidence/sources/S-YYNNN_slug.md
```

**Find which commit deleted a file:**

```bash
git log --diff-filter=D -- architecture/evidence/sources/S-26001_slug.md
```
