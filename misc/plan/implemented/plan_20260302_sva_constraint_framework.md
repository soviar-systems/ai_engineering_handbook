# Plan: ADR-26037 — Formalization of Smallest Viable Architecture (SVA) Constraint Framework

## Context

SVA is referenced in 14+ ADRs as the governing architectural principle, but was never formally defined in its own ADR. Three consultant prompts define SVA constraints with **incompatible numbering**:

| Constraint concept | Local (C1-C4) | DevOps (C1-C4) | Hybrid (C1-C5) |
|---|---|---|---|
| Non-CLI/non-GitOps | C1 | C1 | C2 |
| Not runnable locally | C2 | C2 | — |
| Vendor lock-in | — | — | C1 |
| Unversionable artifacts | C3 | C3 | C3 |
| Unjustified orchestration | C4 | C4 | C4 |
| Scalability limits | — | — | C5 |

ADR-26026 invented "C2 (separation of concerns)" matching no consultant definition. The changelog self-filtering plan exposed a gap: the old C1-C4 would have **approved** a plan that duplicated existing logic — proving the framework was incomplete.

## Decision: Canonical C1-C6 Constraints (redesigned from first principles)

### C1: Automation-First Operation
- **Definition:** Every workflow step must be executable non-interactively via CLI or API, enabling CI/CD integration without manual gates.
- **Litmus test:** Can a CI runner execute this without human interaction?
- **Sources:** GitOps, Twelve-Factor App (Factor V), ISO 29148 (verifiability)
- **Penalty:** -0.10 on P-score

### C2: Vendor Portability
- **Definition:** No component may create single-vendor dependency that prevents migration to an equivalent alternative within one sprint.
- **Litmus test:** If the vendor disappears tomorrow, can you replace the component within two weeks?
- **Sources:** Twelve-Factor App (Factor IV), IEEE 1016 (replaceability), UNIX Philosophy (loose coupling)
- **Penalty:** -0.10 on P-score

### C3: Git-Native Traceability
- **Definition:** All artifacts that influence system behavior must be stored in version-controlled, text-diffable formats within the repository.
- **Litmus test:** Can `git diff` show a meaningful, human-reviewable change for any modification?
- **Sources:** GitOps (Git as SSoT), ISO 29148 (traceability), SRE (postmortem culture)
- **Penalty:** -0.10 on P-score

### C4: Proportional Complexity
- **Definition:** Every component must justify its existence; the cost of adding/maintaining it must not exceed the cost of the problem it addresses.
- **Litmus test:** Remove the component — does the system still meet requirements, perhaps through existing capability?
- **Sources:** YAGNI (XP), UNIX Philosophy, KISS, SRE (operational simplicity)
- **Penalty:** -0.10 on P-score

### C5: Reuse Before Invention
- **Definition:** New code must not duplicate logic already present in an existing, tested component within the system boundary.
- **Litmus test:** Does a tool or function already exist that provides the capability (perhaps with a flag or minor extension)?
- **Sources:** DRY, UNIX Philosophy (compose), Single Source of Truth, XP (Simple Design)
- **Penalty:** -0.10 on P-score

### C6: Bounded Scalability
- **Definition:** The solution must degrade gracefully (not catastrophically) as input size grows 10x, and must document known scaling boundaries.
- **Litmus test:** What happens at 10x input? Documented limits with mitigation paths do NOT violate C6 — only undocumented/unfixable limits do.
- **Sources:** SRE (capacity planning), Twelve-Factor App (Factor VIII), ISO 29148 (scalability NFR)
- **Penalty:** -0.10 on P-score

### Design note: "Runnable locally" (old local C2)
Intentionally dropped as a universal constraint. It's a deployment context that affects P_raw scoring in the local consultant, not a universal architectural principle. The hybrid consultant correctly omitted it.

## Case Study Validation

The changelog self-filtering plan (4 functions, 1 dataclass, 13 tests) vs. single post-commit hook entry:

| Constraint | Original Plan | Post-commit Hook |
|---|---|---|
| C1: Automation-First | Pass | Pass |
| C2: Vendor Portability | Pass | Pass |
| C3: Git-Native Traceability | Pass | Pass |
| **C4: Proportional Complexity** | **FAIL** — disproportionate to goal | Pass — zero new code |
| **C5: Reuse Before Invention** | **FAIL** — duplicates `generate_changelog.py` filtering | Pass — reuses existing tool |
| C6: Bounded Scalability | Pass | Pass |

Old C1-C4: 0 violations (would approve the wrong plan). New C1-C6: 2 violations (correctly flags it).

## Implementation Steps

### Step 0: Save design analysis as evidence artifact
- File: `architecture/evidence/analyses/A-26003_sva_constraint_framework_design.md`
- Frontmatter: `id: A-26003`, `status: active`, `tags: [architecture, governance]`, `sources: []`, `produces: [ADR-26037]`
- Content: The full constraint derivation — current state analysis (3-consultant comparison table), principled redesign from first principles (UNIX, YAGNI, Twelve-Factor, SRE, GitOps, ISO 29148), migration mapping table, case study validation (changelog pivot)
- Required sections: `## Problem Statement`, `## References`

### Step 1: Create ADR-26037
- File: `architecture/adr/adr_26037_smallest_viable_architecture_constraint_framework.md`
- Status: `accepted`
- Tags: `[architecture, governance]`
- Include: Context (inconsistency problem), Decision (C1-C6 with litmus tests), case study, migration mapping table
- References: `A-26003` (design analysis), related ADRs that reference SVA
- Participants: Vadim Rudakov, Claude Opus 4.6

### Step 2: Update consultant prompts (C1-C6 alignment)
- `ai_system/3_prompts/consultants/local_ai_systems_consultant.json` — replace `sva_violations` C1-C4 with canonical C1-C6, update `p_score_audit` to reference C1-C6
- `ai_system/3_prompts/consultants/devops_consultant.json` — same replacement
- `ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json` — replace C1-C5 with canonical C1-C6, update `p_score_audit`

### Step 3: Update ADR index
- Run `uv run tools/scripts/check_adr.py --fix` to auto-update the index

### Step 4: Add insight to `misc/insights.md`
- Document the constraint framework design rationale — why C5 was the critical missing piece

## Verification

```bash
# Validate evidence artifact
uv run tools/scripts/check_evidence.py

# Validate ADR format
uv run tools/scripts/check_adr.py --fix

# Validate JSON consultants
python -c "import json; json.load(open('ai_system/3_prompts/consultants/local_ai_systems_consultant.json'))"
python -c "import json; json.load(open('ai_system/3_prompts/consultants/devops_consultant.json'))"
python -c "import json; json.load(open('ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json'))"

# Verify changelog entry
uv run tools/scripts/generate_changelog.py --verbose HEAD~1..HEAD 1>/dev/null
```

### Step 5: Save plan to misc/plan/
- File: `misc/plan/plan_20260302_sva_constraint_framework.md`
- Per CLAUDE.md convention: save plan before implementation, move to `misc/plan/implemented/` after fully implemented

## Out of Scope (follow-up)

- Retroactively annotating existing ADRs with canonical constraint IDs — do when each ADR is next modified (phased rollout)
- Updating the requirements engineering glossary to reference ADR-26037
