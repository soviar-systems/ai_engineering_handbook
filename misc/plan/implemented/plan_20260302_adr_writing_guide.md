# Plan: Architecture Decision Workflow Guide

## Context

The repository has a mature evidence → ADR pipeline (ADR-26035) and an established ADR system (ADR-26016, ADR-26017, ADR-26025), but no guide on HOW to write well. The existing `what_is_an_adr.md` explains what ADRs are and the RFC workflow; it does not cover quality standards, the evidence pipeline, or common mistakes.

During ADR-26037 creation, 6 quality problems were identified (undefined terms, unexpanded abbreviations, ephemeral implementation details, artifact-tied consequences, weak mitigations, wrong-abstraction alternatives). These — plus anti-patterns from ADR-26005 (tool-as-architecture) and ADR-26026 (invented identifiers) — provide the empirical basis for the guide.

## Deliverables

### 1. Create `architecture/adr_writing_guide.md`

**Title:** "Architecture Decision Workflow"

**Frontmatter:**
```yaml
---
title: "Architecture Decision Workflow"
author: rudakow.wadim@gmail.com
date: 2026-03-02
options:
  version: 1.0.0
  birth: 2026-03-02
---
```

**Structure (target: ~250 lines, readable in 8-10 minutes):**

#### Opening (5 lines)
- Purpose: how to produce high-quality architectural decisions
- Complements `what_is_an_adr.md` (what/why/workflow) and `adr_template.md` (structure)
- Guiding principle: **"Write for the reader 3 years from now who has no context about today's implementation."**

#### Phase 1: Evidence Gathering
- **When to gather evidence:** Before writing an ADR, determine if the decision needs upstream research (trade study, comparison, dialogue extraction)
- **Sources (S-YYNNN):** Ephemeral transcripts and raw inputs → `evidence/sources/`. Three-commit lifecycle (capture → extract → delete). Reference: `evidence.config.yaml`, `evidence/sources/README.md`
- **Analyses (A-YYNNN):** Extracted findings, trade studies, comparisons → `evidence/analyses/`. Required sections: Problem Statement, References. Link to producing ADR via `produces:` field
- **Retrospectives (R-YYNNN):** Post-mortems and failure analyses → `evidence/retrospective/`. Include severity level
- **When to skip evidence:** If the decision is straightforward with clear alternatives, go directly to the ADR. Not every ADR needs an upstream analysis
- **Validation:** `uv run tools/scripts/check_evidence.py`

#### Phase 2: Writing the ADR — Core Discipline
Three rules that apply to every section:

1. **Decisions, not descriptions.** An ADR records a choice and its rationale, not a specification or tutorial
2. **Every assertion must be falsifiable or traceable.** "Improves developer experience" is not falsifiable; "reduces CI runtime from 12 minutes to 4 minutes" is
3. **No undefined vocabulary.** Expand every abbreviation on first use. Do not use terminology not defined in this repository or a referenced standard

Do/Don't examples:
- Do: "YAGNI (You Ain't Gonna Need It) prohibits speculative features"
- Don't: "This violates YAGNI" (without prior expansion)
- Do: "Migration requires updating all three configuration files"
- Don't: "This can be completed within one sprint" (undefined term)

#### Phase 2a: Section-by-Section Guidance

**Context:**
1. Start with the problem, not the solution
2. Include evidence (tables, metrics, references to specific failures)
3. Do not front-load the solution

**Decision:**
1. Affirmative, active language: "Adopt X," "Require Z"
2. Make it falsifiable
3. Avoid ephemeral implementation details — migration mappings belong in evidence artifacts (A-YYNNN)
4. Never invent identifiers — every constraint ID, principle number, or framework label must be defined in an authoritative source

**Consequences:**
1. Positive: focus on capabilities and principles, not current artifacts
2. Negative/Risks: honest mitigations that address the actual risk mechanism
3. Format: "When X occurs, do Y" — not "This is unlikely because Z"
4. Best-effort or deferred mitigations must say so explicitly

**Alternatives:**
1. Same level of abstraction as the decision
2. Minimum two (promotion gate enforces this)
3. Rejection reasons grounded in principles or evidence, not dismissals
4. "Do nothing" only when status quo is genuinely viable

**References:**
1. Internal: markdown links `[Title](/path)` for `check_broken_links.py`
2. ADR cross-references: `{term}`ADR-NNNNN`` with hyphen
3. Glob to verify exact ADR filenames before linking
4. Include evidence analysis when one exists
5. External: stable links only

**Participants:**
1. All contributors who materially influenced the decision
2. AI participants include model name

#### Phase 3: Anti-Patterns Checklist
One-line scannable items (10 items):

1. Undefined domain vocabulary
2. Unexpanded abbreviations
3. Ephemeral implementation details in the ADR body
4. Consequences tied to current artifacts instead of principles
5. Reassurance mitigations that don't address the risk mechanism
6. Alternatives at the wrong abstraction level
7. Invented identifiers
8. Tool choice masquerading as architecture
9. Future promises as mitigations
10. Dismissive alternatives without trade-off analysis

#### Phase 4: Validation
- `uv run tools/scripts/check_adr.py --fix`
- `uv run tools/scripts/check_evidence.py`
- `uv run tools/scripts/check_broken_links.py`
- Anti-patterns checklist review

#### Closing (3 lines)
- Cross-reference to SSoT documents
- Core message: invest in quality now

### 2. Update `architecture/what_is_an_adr.md`

Add step 4 to "Creating an ADR" list (after current step 3, ~line 37):
```markdown
4. Consult the [Architecture Decision Workflow](/architecture/adr_writing_guide.md) for the full evidence-to-ADR pipeline and quality guidelines.
```

Bump `options.version` from `1.1.0` to `1.2.0`, update `date` to `2026-03-02`.

### 3. Update `architecture/adr/adr_template.md`

Add HTML comment after frontmatter (after line 8, before `# ADR-{{ id }}`):
```markdown
<!-- Quality guidelines: /architecture/adr_writing_guide.md -->
```

### 4. Do NOT update onboarding

Discoverable through: onboarding → read ADRs → `what_is_an_adr.md` → writing guide.

## Files to Create/Modify

| File | Action |
|------|--------|
| `architecture/adr_writing_guide.md` | **Create** — the full guide (~250 lines) |
| `architecture/what_is_an_adr.md` | **Edit** — add cross-reference, bump version |
| `architecture/adr/adr_template.md` | **Edit** — add HTML comment |

## Verification

```bash
# Validate broken links (the new file has internal markdown links)
uv run tools/scripts/check_broken_links.py --pattern "architecture/adr_writing_guide.md"

# Validate ADR template still parses
uv run tools/scripts/check_adr.py --fix

# Validate evidence config
uv run tools/scripts/check_evidence.py
```
