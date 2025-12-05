# Appendices for Git Production Workflow Handbook

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-15  
Last Modified: 2025-12-15

-----

## Appendix A: Detailed ArchTag Commit Examples

These examples illustrate the correct structure for commits that require Tier 3 architectural justification, using the `ArchTag:TAG-NAME` format.

### 1. ArchTag: `DEPRECATION-PLANNED`

*Goal: Remove a function slated for sunsetting.*

```
feat: remove legacy user analytics module

ArchTag:DEPRECATION-PLANNED
This module has been replaced by the new Kafka-based logging system (see JIRA-255).
All calls to `legacy_analytics_log()` have been removed from the frontend service.

BREAKING CHANGE: The `legacy_analytics_log()` function and its HTTP endpoint /api/v1/log are no longer available.
```

### 2. ArchTag: `TECHDEBT-PAYMENT`

*Goal: Restructure code to improve maintainability and adherence to modern Python standards.*

```
refactor: standardize all model config loading via Pydantic

ArchTag:TECHDEBT-PAYMENT
Replaced outdated dict-based config parsing with Pydantic schemas across 12 files.
This significantly reduces validation error handling boilerplate and improves type safety.
```

### 3. ArchTag: `REFACTOR-MIGRATION`

*Goal: Implement a fundamental shift in how the system handles a core component.*

```
refactor: migrate database connection pool to SQLAlchemy 2.0 async

ArchTag:REFACTOR-MIGRATION
Upgraded the core data layer to use the new asyncio ORM style.
This is a breaking change and requires updating all repository methods to use `await`.
```

### 4. ArchTag: `PERF-OPTIMIZATION`

*Goal: Optimize a slow loop, requiring proof of performance gain.*

```
perf: optimize feature extraction by replacing list with numpy array

ArchTag:PERF-OPTIMIZATION
Profiling showed the bottleneck was array conversion in the main loop.
Benchmark results show a 22% reduction in latency for large inputs (1000+ features).
```

## Appendix B: The Big Tech Philosophy: Atomic Submission

The large-scale tech companies (Meta, Google, etc.) have workflows built around a concept called the **Small Change List (CL)**, which mandates that the **unit of submission** is one, single, atomic change. This philosophy heavily favors one of the merge strategies, but not in the standard way.

The guiding principle is **one logical change $\rightarrow$ one commit to the mainline branch**. This ensures maximum:

1.  **Revertability:** If the change breaks production, the entire feature can be removed instantly with one `git revert`.
2.  **Reviewability:** Reviewers only assess a single, focused change that does one thing.
3.  **Traceability:** `git blame` and changelogs point directly to the full feature/fix, not an intermediate development step.

### How Each Company Achieves This

Your understanding that they heavily use rebase is correct, but the context is key.

#### 1. Google (Squash and Merge)

* **Workflow:** Google uses an internal version control system (Piper, conceptually similar to Perforce, but with front-ends that make it feel like Git). Their primary mechanism for submission is the **CL (Changelist)**, which is conceptually identical to a **single, atomic commit**.
* **Git Equivalent:** The closest public Git equivalent to their merge strategy is **Squash and Merge**. All intermediate commits created during development on a feature branch are flattened into one single, clean, atomic commit for the mainline repository.
* **The Role of Rebase:** Developers **do** use `git rebase` *locally* to clean up their history (squash "WIP" or "fix typo" commits) *before* submitting the single CL for review.

#### 2. Meta (Rebase, but with Stacked Diffs)

* **Workflow:** Meta primarily uses a version control system called **Mercurial** (though they have highly customized their tooling around it, notably **Sapling**). They are the pioneers of **Stacked Diffs** or **Stacked Changes**.
* **Stacked Diffs:** A large feature is split into a stack of many small, dependent, atomic changes (e.g., Change A depends on B, B depends on C). Each change is reviewed and submitted **independently**.
* **Git Equivalent:** When these individual atomic changes are submitted, they are often integrated in a way that is equivalent to a **Rebase and Merge** or a **Fast-Forward Merge**, where no merge commit is created, and the history remains perfectly linear. This preserves the full, clean, *atomic* commit history of the stack.
* **Key Difference:** The history Meta preserves is a series of clean, atomic, reviewed commits. They **do not** preserve messy development history.
