# ADR 0003: Adoption of `gitlint` for Tiered Workflow Enforcement

## Title

Standardizing Git Commit Validation using `gitlint` to Enforce Three-Tier Architectural Integrity.

## Status

Proposed

## Date

2026-01-10

## Context

The [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb) mandate a complex, conditional validation logic that standard regex-based tools cannot easily support. Specifically:

* **Tier 2 (Intent):** Requires strict Conventional Commits formatting.
* **Tier 3 (Justification):** Mandates an **Architectural Tag (ArchTag)** (e.g., `TECHDEBT-PAYMENT`) as the first line of the body **only if** the commit type is `refactor:`, `perf:`, or a `BREAKING CHANGE`.
* **ADR 0001 & 0002** established a preference for Python-based, OOP-structured hooks managed by the `pre-commit` framework to avoid Node.js dependencies.

## Decision

We will adopt `gitlint` ([https://jorisroovers.com/gitlint/](https://jorisroovers.com/gitlint/)) as the primary engine for commit message enforcement.

1. **Integration:** `gitlint` will be orchestrated via `.pre-commit-config.yaml` using the `pre-commit-msg` stage.
2. **Custom Logic (Tier 3):** We will utilize `gitlint`'s **User Defined Rules** feature. Following the OOP standards of ADR 0001, we will implement a Python class (e.g., `ArchTagRule`) that inspects the commit object and enforces the presence of tags based on the commit type.
3. **Branch Validation:** Since `gitlint` focuses on commits, Tier 1 (Branch Naming) will be handled by a separate `repo: local` hook or the native `pre-commit` `check-branch-name` hook to ensure full compliance with the `<prefix>/<ID>-<desc>` format.

## Consequences

### Positive

* **Context-Aware Validation:** Unlike simple regex tools, `gitlint` allows Python-based logic to verify the relationship between a commit's "Intent" (Header) and its "Justification" (Body ArchTag).
* **Python Native:** Zero Node.js or Ruby runtime requirements, maintaining a lean Linux/MLOps environment.
* **Detailed Feedback:** Provides developers with clear, line-specific error messages, reducing friction during the "Check vs. Fix" cycle.
* **Full Automation:** Supports the "Hard Gate" requirement for CI/CD blocking defined in the standards.

### Negative

* **Orchestration Complexity:** Requires maintaining a small Python script for custom rules. **Mitigation:** This aligns with ADR 0001's requirement for tested, maintainable hook logic.
* **Dual-Tooling for Branches:** `gitlint` does not validate branch names. **Mitigation:** Use the existing `pre-commit` framework to add a 10-line branch validator, keeping the SVA (Smallest Viable Architecture) intact.

## Alternatives

* `commit-check`: Rejected because it lacks the native Python extensibility required to easily enforce the **conditional** Tier 3 ArchTag rules across multi-line commit bodies.
* `commitlint` (Node.js): Rejected due to the requirement for a Node.js toolchain, which violates our MLOps environment constraints.

## References

- [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb)
- [ADR 0001: Use of Python and OOP for Git Hook Scripts](/architecture/adr/adr_0001_use_of_python_and_oop_for_git_hook_scripts.md)
- [ADR 0002: Adoption of the Pre-commit Framework](/architecture/adr/adr_0002_adoption_of_pre_commit_framework.md)
- [Gitlint User-defined Rules](https://www.google.com/search?q=https://jorisroovers.com/gitlint/user_defined_rules/)

## Participants

1. Vadim Rudakov
2. Senior DevOps Systems Architect (Gemini)
