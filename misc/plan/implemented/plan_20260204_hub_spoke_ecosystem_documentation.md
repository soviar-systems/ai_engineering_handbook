# Plan: Hub-and-Spoke Ecosystem Documentation Architecture

## Overview

Establish a documentation architecture where `ai_engineering_book` serves as the **hub** (meta-documentation for the entire AI engineering ecosystem) and packages like `vadocs` serve as **spokes** (implementations with their own ADRs).

---

## Tasks

### 1. Write ADR-26020: Hub-and-Spoke Ecosystem Documentation Architecture

**File**: `architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md`

**Content outline**:
- **Context**: ai_engineering_book evolved into a meta-documentation hub; packages are being extracted to standalone repos
- **Decision**: Two-tier ADR system
  - Hub ADRs: Ecosystem-wide decisions, interfaces, conventions
  - Spoke ADRs: Implementation-specific decisions (how, not why)
- **Structure**:
  - Hub: `architecture/packages/` for package specifications
  - Spokes: `ARCHITECTURE.md` linking to hub + local `docs/adr/` for implementation ADRs
- **Linking strategy**: Spokes reference hub ADRs in ARCHITECTURE.md
- **Consequences**: Single source of truth for ecosystem, independence for implementations

### 2. Create Hub Directory Structure

```
architecture/
├── adr/                      # Ecosystem ADRs (existing)
│   ├── adr_26020_hub_spoke_ecosystem_documentation.md  # NEW
│   └── ... (existing ADRs)
└── packages/                 # Package specifications (NEW)
    ├── README.md             # Overview of ecosystem packages
    └── vadocs.md             # vadocs package spec (what it should do)
```

### 3. Identify ADRs for vadocs

**ADRs to COPY to vadocs repo** (founding documents):
- ADR-26012: Extraction of Documentation Validation Engine
  - This is THE founding document for vadocs
  - Copy to `vadocs/docs/adr/adr_0001_founding_document.md`

**ADRs to KEEP in hub only** (ecosystem standards):
- ADR-26001: Python for git hooks (standard, not vadocs-specific)
- ADR-26002: Pre-commit framework (standard)
- ADR-26011: Script suite workflow (standard for hub repo)
- ADR-26016-26019: Frontmatter/metadata standards (vadocs implements these)

**Hub ADR-26012 update**:
- Add "Implementation" section pointing to vadocs repo
- Status remains "proposed" until vadocs v1.0

### 4. Create Package Spec Document

**File**: `architecture/packages/vadocs.md`

**Content**:
- Package purpose and scope
- Required capabilities (validators, fixers, config loading)
- Interface contracts (Validator ABC, error format)
- Links to relevant ecosystem ADRs
- Version roadmap

### 5. Create vadocs ARCHITECTURE.md Template

**File** (for vadocs repo): `ARCHITECTURE.md`

**Content**:
- Links to governing ADRs in hub
- List of implementation ADRs in this repo
- Architecture overview

---

## Files to Create

| File | Purpose |
|------|---------|
| `architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md` | New ADR defining the ecosystem structure |
| `architecture/packages/README.md` | Overview of ecosystem packages |
| `architecture/packages/vadocs.md` | vadocs package specification |

## Files to Modify

| File | Change |
|------|--------|
| `architecture/adr/adr_26012_*.md` | Add "Implementation" section with vadocs repo link |

## Files for vadocs Repo (reference only)

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | Links to hub ADRs |
| `docs/adr/adr_0001_founding_document.md` | Copy of ADR-26012 |

---

## Verification

1. ADR-26020 follows existing ADR format (frontmatter, sections)
2. `architecture/packages/` directory exists with README.md
3. vadocs.md contains clear specification
4. No broken term references in new files

---

## Open Questions

None - ready for implementation.
