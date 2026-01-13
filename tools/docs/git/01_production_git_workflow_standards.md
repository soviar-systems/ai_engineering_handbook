---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Production Git Workflow Standards

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.1  
Birth: 2025-11-29  
Last Modified: 2026-01-14

---

+++

This handbook establishes mandatory, professional-grade conventions for Git branching and committing. Adherence to these standards is essential for achieving traceability, enabling automated MLOps gates, ensuring accurate changelogs, and streamlining architectural reviews.

The workflow is enforced through a Three-Tier Naming Structure and a strict Conventional Commits policy, culminating in an Atomic Commit merge strategy.

+++

## **Intro: Three-Tier Naming Structure**

+++

All changes must follow this strictly enforced hierarchy for complete lifecycle context.

| Tier                 | Component                                                | Purpose                                                                            | Requirement                                                                     |
|:-----------------|:-----------------|:-----------------|:-----------------|
| **1. SCOPE**         | Branch Prefix + Ticket ID<br>`fix/29-fix-broken-feature` | Defines the **scope** of work (e.g., `feature/`) and its associated **work item**. | **MANDATORY** for all branches.                                                 |
| **2. INTENT**        | Commit Title Prefix<br>`fix: Fix login in app`           | Defines **what changed** (Conventional Commits type, e.g., `feat:`, `fix:`).       | **MANDATORY** for all commits.                                                  |
| **3. JUSTIFICATION** | Architectural Tag (ArchTag)                              | Defines **why** a structural change was made. Placed in the commit body.           | **CONDITIONAL** (Mandatory for `refactor:`, `perf:`, `BREAKING CHANGE` Footer). |

+++

## **Tier 1: Branch Prefixing Policy - Scope & Traceability**

+++

Branch names **MUST** use the format:

`<prefix>/<TICKET-ID>-<short-kebab-description>`

*Names must be lowercase with hyphens. This format enables automatic linking to issues and Pull Requests. Not implemented yet.*

| Prefix | Work Scope | Example  |
|:-----------------------|:-----------------------|:-----------------------|
| `main/`| The main development branch (e.g., `main`, `master`, or `develop`) | N/A  |
| `feat/`| New features or significant enhancements/additions.| `feat/456-add-metrics-endpoint`  |
| `fix/` | Correcting a user-impacting defect/bug.| `bugfix/123-login-404-error` |
| `hotfix/`  | Urgent fixes applied directly to the production branch.| `hotfix/123-payment-gateway-bug` |
| `release/` | Preparation for a formal release (e.g., final testing, version bumps). | `release/v1.2.0-final-prep`  |
| `chore/`   | For non-code tasks like dependency, docs updates.  | `chore/TICKET-789-update-deps`   |

> Branches are different from commits—they are temporary and mainly used until merged. Introducing too many types for branches would be unnecessary and would make them harder to manage and remember.
> 
> -- [Conventional Branch docs](https://conventional-branch.github.io/)

:::{seealso}
> 1. [Conventional Branch](https://conventional-branch.github.io/) - external link
> 2. [ADR 26003: Adoption of `gitlint` for Tiered Workflow Enforcement](/architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md)
:::

+++

## **Tiers 2 & 3: Conventional Commit Policy - Intent & Justification**

+++

### Tier 2: Commit Title Prefix - **What** Changed

+++

The commit title **MUST** start with `<type>: <description>`. The description must be **50 characters maximum** and written in the **imperative mood**.

| Group  | Type| Intent | ArchTag Required? | SemVer Impact |
|:--------------|:--------------|:--------------|:--------------|:--------------|
| **Core**   | `feat:` | A new feature or enhancement.  | NO | **Minor** |
|| `fix:`  | A bug fix. | NO| **Patch** |
| **Breaking**   | *(any type)* + `BREAKING CHANGE` footer | Introduces an incompatible API/behavior change.| **YES**   | **Major** |
| **Architectural**  | `refactor:` | Code restructuring that neither fixes a bug nor adds a feature; can change public API. | **YES**   | Patch/Minor/Major |
|| `perf:` | Code change that measurably improves performance; can change public API.   | **YES**   | Patch/Minor/Major |
| **Routine**| `docs:` | Changes to documentation only. | NO| None  |
|| `test:` | Adding or correcting tests.| NO| None  |
|| `chore:`| Routine maintenance, dependency updates, minor clean-up.   | NO| None  |
| **Internal/Temporary** | `WIP:`  | **Incomplete work. Must be squashed/rebased before merging.**  | NO| None  |

:::{important}
Commit types inform SemVer, but do not dictate it. Final SemVer must be validated against API/behavior contracts.

See: [SemVer: Artifact Versioning Policy (AVP)](/tools/docs/git/semver_artifact_versioning_policy_avp.ipynb)
:::

+++

#### **BREAKING CHANGE** Footer

+++

The official way to signal changes that **break compatibility** is:

```
<type>(<optional scope>): <description>

BREAKING CHANGE: <description of breaking impact>
```

| Intent  | Correct Conventional Commit Form   |
|-----------------------------|-------------------------------------------|
| **Removing a feature** (user-facing)| `feat: remove legacy auth API`<br>`BREAKING CHANGE: The /v1/login endpoint is deleted. Use /v2/auth.`  |
| **Removing internal code** (no external impact) | `refactor: delete unused cache module`<br>*(No `BREAKING CHANGE` needed)*  |
| **Removing a config option or API** (breaking)  | `fix: drop support for deprecated TLS 1.0`<br>`BREAKING CHANGE: TLS 1.0 connections are now rejected.` |

:::{important} Key principle
A **breaking change** is defined by **observable behavior change for consumers** — not by the act of change itself.
:::

:::{seealso}
> [Conventional Commits – Breaking Changes: Commit Message with Description and Breaking Change Footer](https://www.conventionalcommits.org/en/v1.0.0/#commit-message-with-description-and-breaking-change-footer)
:::

+++

### Tier 3: Architectural Tagging - **Why** Changed

+++

For commits of type 
- `refactor:`, 
- `perf:`, or 
- `BREAKING CHANGE` Footer,

the architectural intent **MUST** be provided as an ArchTag (Architectural Tag).

- **Format:** The tag **MUST** be the **first line** of the commit body: `ArchTag:TAG-NAME` (one tag only).
- **Syntax Rules:** The tag **MUST NOT** include the `#` symbol or any spaces.
- **Validation:** CI/CD automation tools will validate the tag’s presence and correctness.

| Tag Name  | Intent   | Heuristic / Automation Gate |
|:-----------------------|:-----------------------|:-----------------------|
| `DEPRECATION-PLANNED` | Sunset code, APIs, or features scheduled for removal.| PR requires Architect Approval (Hard Gate). |
| `TECHDEBT-PAYMENT`| Reducing complexity, upgrading dependencies, or simplifying code.| Signals maintenance work.   |
| `REFACTOR-MIGRATION`  | Major architecture shift or pattern change (e.g., monolith to microservice). | PR requires Architect Approval (Hard Gate). |
| `PERF-OPTIMIZATION`   | Code change explicitly addressing a performance bottleneck.  | Benchmarks must be provided in the commit body. |

+++

:::{tip} Example of a full commit with `ArchTag`
```
refactor: Simplify model loading logic

ArchTag:TECHDEBT-PAYMENT
Reduced cyclomatic complexity from 15 to 8, improving maintainability.
```
:::

+++

``` mermaid
---
config:
  layout: dagre
  theme: redux
---
flowchart TB
    A["Commit w/ Tag"] --> B["ArchTag:"]
    B -- PERF-OPTIMIZATION --> C["Perf Tests"]
    B -- REFACTOR-MIGRATION --> D["Architect Review"]
    B -- DEPRECATION-PLANNED --> E["API Docs Update"]
    B -- TECHDEBT-PAYMENT --> F["Debt Score Δ"]
    C --> G["Changelog Section"]
    D --> G
    E --> G
    F --> G
```

+++

## **"WIP" Commits: Interactive Rebase**

+++

Before opening a Pull Request (PR), all intermediate commits like `WIP` **MUST** be consolidated (squashed) into one or more **atomic commits** using a valid semantic type (`feat:`, `fix:`, etc.).

1.  **Start Interactive Rebase:** Execute `git rebase -i <target-branch>` (e.g., `git rebase -i develop`).
2.  **Edit Commit List:** Change the action for every `WIP:` commit from `pick` to **`squash` (`s`)** or **`fixup` (`f`)**.
3.  **Finalize Message:** Ensure the final, consolidated commit message is a single, valid, semantic commit title and body.

A `WIP:` type is useful only if its temporary nature is strictly enforced. Allowing `WIP:` commits to pollute the final, merged history defeats the purpose of Conventional Commits and introduces unnecessary noise and technical debt.

:::{important}
The `WIP:` commit type is strictly for **personal backup and context switching** on feature branches. It **MUST NOT** be present in the final commit history of any main branch (e.g., `main`, `develop`).
:::

+++

### PR System Guardrails (Hard Gates)

+++

- **CI/CD Block:** The CI/CD pipeline is to be configured to automatically **fail a Pull Request** if any commit in the branch’s history contains the prefix `WIP:`. This is a **hard technical gate**.
- **Mandatory Merge Strategy:** The repository is configured to **enforce “Squash and Merge”** for all feature branches into mainline branches. This guarantees that the final history is composed of single, clean, semantic commits.

The most effective enforcement mechanism is at the code review and merge gate.

| Policy   | Implementation | Rationale  |
|:-----|:--------|:------|
| **PR Status Check**  | Configure your CI/CD system (e.g., GitHub Actions, GitLab CI, Azure DevOps Pipelines) to run a script that **fails the build** if any commit in the PR history (prior to merge) contains the regex pattern `^WIP:` in its title. | This is a **hard gate**. It prevents developer oversight from reaching the main codebase, forcing the immediate correction of the branch history. |
| **Reviewer Responsibility** | Peer reviewers are explicitly tasked with a **quick history audit**. The reviewer must verbally confirm that the history is clean and semantic before approving the PR. | Provides a human layer of quality control, ensuring the final commit message correctly reflects the change’s semantic intent and is well-written. |
| **Enforce `merge --ff-only`**    | Set the default merge strategy on your repository to fast-forward only.  | The history should be linear and any change should be atomic so reverts can be made instantly if the bug found. The developer must rebase their work on main before initiating PR |

The dev's workflow on topic branch:

```bash
$ git switch topic-branch
$ git rebase -i main

# squash intermediate commits, fix any conflicts
# then
$ git push origin topic-branch

# and initiate a PR
```

+++

### Guidance: When to Use "WIP:" vs. Standard Commit Types

+++

New engineers must understand the difference to avoid misusing `WIP:`.

| Scenario  | Recommended Type  | Rationale   |
|:-------|:-----|:--------|
| **Saving work** at the end of the day or switching machines. | `WIP: short summary of current state`  | Work is incomplete, not ready for review, and exists purely for personal continuity. Must be squashed later. |
| **Completing a logical unit** of work (e.g., finishing the utility function signature, adding a new test). | `test: add unit test for X service` or `refactor: extract Z function from module A` | The change is coherent, stable, and useful, even if the overall feature is unfinished. It improves branch history readability *before* the final squash. |
| **Fixing a minor bug** discovered while working on a feature. | `fix: prevent divide by zero in function Y` | This is a small, atomic fix that is technically correct and may be valuable on its own. It can be squashed later or kept as a separate atomic commit. |

:::{important} **Key Takeaway**
If the commit is stable, complete, and describes an atomic, logical change that could stand on its own in the history, use a standard type. If the code is broken, half-finished, or purely a checkpoint, use `WIP:`.
:::

+++

## **Atomic Commits: The Guiding Principle**

+++

The goal of every feature branch’s final history is **logical atomicity**. An **Atomic Commit** is a self-contained, complete, and logically isolated unit of work.

+++

### Rules of Atomicity

+++

- **Rule 1: One Goal Per Commit.** A commit must achieve one objective only (e.g., *refactor logic*, *add unit tests*, *fix a bug*).
- **Rule 2: Commits Must Be Stable.** Every commit in the final, merged history **MUST** be buildable and pass all tests. This is mandatory for advanced diagnostic tools like `git bisect`. **Broken commits are technical debt.**
- **Rule 3: Cohesive Narrative.** The sequence of commits in a Pull Request (PR) must tell a clear story of how the feature was developed, making it easy for reviewers to follow the logic.

+++

### The “Commit by Logic” Workflow

+++

To create atomic commits, **DO NOT** use `git add .` indiscriminately.

| Step  | Action   | Tool | Goal|
|:-----------------|:-----------------|:-----------------|:-----------------|
| **Stage Selectively** | Use the patch utility to stage only changes relevant to a single logical task.  | `git add -p`  | **Group changes by function and purpose,** not by file or timing.|
| **Review and Commit** | Review the staged changes (`git diff --staged`). If they represent one complete, stable, logical step, commit them with a semantic type. | `git commit -m "feat: implement X interface"` | Ensure the commit is **atomic**. |
| **Iterate and Clean** | Perform the rebase and squashing procedure (Section 4).  | `git rebase -i` | Produce a clean, coherent history ready for review and final merge. |

This disciplined approach ensures that your contributions are professionally structured, easily maintainable, and maximally effective for the long-term health of our engineering systems.

:::{seealso} Read more
> - [“Pro Git”, Chapter 7: Git Tools - Rewriting History’](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History) by Scott Chacon and Ben Straub
:::

+++

### Merge Strategy: Atomic Change Submission

+++

All changes merged into mainline branches (`main`, `develop`, etc.) **MUST** be integrated as a **single, atomic, logical unit**. This is a **fundamental engineering discipline** used in scaled production environments (Google, Meta, Microsoft) to ensure **reviewability, revertability, and traceability**.

+++

#### One Change, One Commit: The BigTech Standard

+++

In professional code review systems:
* A Pull Request (PR) or Change List (CL) represents **one logical modification** to the system.
* Intermediate development steps (e.g., test scaffolding, incremental refactors) are **development artifacts**, not production history.
* Preserving them in `main` adds **noise without operational value** and **dilutes accountability**.

:::{important} **Key Principle**
*“If it can’t be reviewed, reverted, or reasoned about as a single unit, it’s not production-ready.”*
:::

+++

### Debugging Without "git bisect" Granularity

+++

Fine-grained bisect on noisy history is **not the primary debugging tool** in production systems. Instead, rely on:
- **Structured logging** (with trace IDs),
- **Metrics and alerting** (e.g., latency, error rates),
- **Atomic revert** (if a change breaks, revert the **entire unit**—not part of it).

If a change is **too large to debug or revert safely**, it **violates atomicity** and should have been split **before submission**.

+++

### (To Consider) Advanced Strategy: The Stacked Diff Exception

+++

The **Stacked Diff** workflow is permitted as an **advanced implementation** of Atomic Change Submission, enabling high velocity and rapid peer review. This methodology involves breaking a large feature into a **series of small, dependent, atomic CLs** (Change Lists or Diffs) .

1.  **Scope:** The entire feature remains **one logical change** to the system.
2.  **Integration Method:** The default **Squash and Merge** is overridden. The stack is integrated using a specialized tool (e.g., Sapling, Graphite) that executes an atomic **Rebase and Merge** or **Fast-Forward Merge** for each sequential diff.
3.  **Strict Condition:** This exception is **only** permitted if:
    -   The work is managed through an approved Stacked Diff platform.
    -   **Every single commit in the stack** must be independently reviewed, CI-verified, and comply with all Tier 1, 2, and 3 policies.
4.  **Benefit:** The resulting mainline history is linear, atomic, and preserves the clean narrative of the feature’s development, thus **restoring the utility of `git bisect`** for diagnostics.

+++

### Enforcement

+++

| Guardrail | Implementation |
|:-----------------------------------|:-----------------------------------|
| **Reviewer Gate**  | Reviewers **reject PRs** that are not logically atomic (e.g., mix refactor + feature).         |
| **Merge Policy**| Repository settings **enforce “Merge --ff-only”** as the only allowed method. |

:::{caution} No Rebase on `main`
Rebase operations create new commits with their own hashes, so such operation can break the monitoring systems if they configured on commit hash change detection.
:::
