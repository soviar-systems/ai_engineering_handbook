# Tools: Commit & Changelog Tooling for Release Pipelines

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.0  
Birth: 2025-12-02  
Last Modified: 2025-12-15

-----

## 1. Purpose

This handbook **eliminates confusion** around the sprawling ecosystem of Git commit and changelog tooling by prescribing a **minimal, deterministic, and maintainable stack** that aligns with the **Small Language Model (SLM)-based release documentation pipeline**.

We **do not adopt** the JavaScript/Node.js tooling ecosystem (e.g., `commitizen`, `semantic-release`) due to its complexity, fragility, and mismatch with the Linux-first, containerized, resource-constrained MLOps environment.

Instead, we enforce a **two-tool standard** that is:

  - **Language-agnostic**
  - **CLI-native**
  - **Zero runtime dependencies** (or pure Python/Go)
  - **Fully compatible with `pre-commit` and CI**
  - **Deterministic and reproducible**

## 2. The Tooling Standard

| Stage | Tool | Type | Why It’s Chosen |
|-------|------|------|-----------------|
| **Stage 1: Commit Message Enforcement** | [`gitlint`](https://www.google.com/search?q=%5Bhttps://jorisroovers.com/gitlint/%5D\(https://jorisroovers.com/gitlint/\)) | Python CLI | Validates Conventional Commits **at commit time** via `pre-commit`. No interactivity. No Node.js. |
| **Stage 2: Changelog Generation** | [`git-chglog`](https://www.google.com/search?q=%5Bhttps://github.com/git-chglog/git-chglog%5D\(https://github.com/git-chglog/git-chglog\)) | Go binary | Parses structured commits into `CHANGELOG.md` **without parsing code, diffs, or configs**. Fast, idempotent, templatable. |

> **This is the only approved stack for the current baseline workflow.** Deviations require Architecture Review Board (ARB) approval.

## 3. Why We Reject the JavaScript Ecosystem

| Tool | Problem | Impact |
|:------|:--------|:--------|
| `commitizen` | Interactive CLI, requires `cz-cli`, `inquirer`, `adapter` config | Breaks automation; forces developers into wizard flows; adds npm bloat |
| `conventional-changelog` | Requires `package.json`, `conventional-changelog-cli`, parsers | Couples changelog logic to JS project structure—even in Python/C repos |
| `semantic-release` | Auto-publishes to npm/GitHub; assumes CI owns versioning | Over-automates; violates the **human-in-the-loop audit gates**; not idempotent |

> **These tools assume a frontend/JS monorepo workflow.** They are **incompatible** with the bare-metal, multi-language, SLM-constrained pipeline.

-----

## 4. Stage 1: Commit Message Enforcement with `gitlint` (Restored)

### 4.1 What It Does

- Validates that every commit message conforms to **Conventional Commits (Tier 2 or 3)**:
  `  <type>[optional scope]: <short summary>   <BLANK LINE>   <optional body>  `
- Blocks non-compliant commits **before they enter Git history**.

### 4.2 Integration

**Install via `pre-commit`:**

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/jorisroovers/gitlint
  rev: v0.19.1
  hooks:
    - id: gitlint
      stages: [commit-msg]
```

**Run manually (for testing):**

```bash
gitlint --msg-filename .git/COMMIT_EDITMSG
```

### 4.3 Configuration

Use the default Conventional Commits rules. **Do not customize** unless adding team-specific scopes (e.g., `docs`, `sllm`, `infra`). Store config in `.gitlint`:

```ini
[general]
contrib = CC

[CC1]
# Enforce type case: feat, fix, perf, etc.
```

> **Never disable `gitlint` in CI or local hooks.** Broken commits break the entire pipeline.

### 4.4 Alignment with Stacked Diffs

The **Stacked Diff** methodology (Section 6.D of the Git Workflow Handbook) is fully supported by `gitlint`. When using stacked diffs, the enforcement gate applies **to every single commit in the stack**.

  * **Enhancement:** Every atomic unit of the feature is semantically validated, leading to a higher-quality, more granular mainline history compared to enforcing only the final squashed commit.

-----

## 5. Stage 2: Changelog Generation with `git-chglog` (Restored)

### 5.1 What It Does

  - Reads **only Git commit history** (no file content, no diffs).
  - Filters and groups commits by Conventional Commit `type`.
  - Renders a clean, standard `CHANGELOG.md` using a Go template.

### 5.2 Installation

Download the single binary:

```bash
# Linux x86_64
wget https://github.com/git-chglog/git-chglog/releases/latest/download/git-chglog_linux_amd64.tar.gz
tar -xzf git-chglog_linux_amd64.tar.gz
sudo mv git-chglog /usr/local/bin/
```

> No Go runtime needed. No `go.mod`. No dependencies.

### 5.3 Configuration

**`.chglog/config.yml`** (minimal):

```yaml
style: github
template: .chglog/CHANGELOG.tpl.md
output: CHANGELOG.md
commits:
  filters:
    Type:
      - feat
      - fix
      - perf
      - refactor
```

**`.chglog/CHANGELOG.tpl.md`** (standard template):

```markdown
# Changelog

{{ range .Versions }}
## {{ if .Tag }}{{ .Tag }}{{ else }}Unreleased{{ end }}

{{ range .CommitGroups -}}
### {{ .Title }}

{{ range .Commits -}}
- {{ .Subject }} ({{ .Hash.Short }})
{{ end }}
{{ end }}
{{ end }}
```

### 5.4 Usage

```bash
# Generate full changelog
git-chglog

# Generate from vX.Y.Z onward
git-chglog --next-tag v1.2.0 vX.Y.Z
```

> **Output is 100% reproducible** given the same Git history and config.

### 5.5 Alignment with Stacked Diffs

`git-chglog` is inherently compatible with the linear, multi-commit history produced by Stacked Diffs.

  * **Handling Feature Spanning Multiple Commits:** If a single feature is integrated as a stack of multiple atomic commits (all carrying the same relevant type, e.g., `feat:`), `git-chglog` will correctly aggregate all their subjects into the single "Features" section of the `CHANGELOG.md` for that release, preserving the complete narrative.

-----

## 6. Architectural Alignment

| Principle | How This Stack Complies | Enhancement with Stacked Diffs |
|:---------|:--------------------------|:------------------------------|
| **Decoupling** | Commit linting (dev) ≠ changelog gen (tool) ≠ release notes (SLM) | *(No Change)* |
| **Determinism** | `gitlint` and `git-chglog` produce identical output across runs | *(No Change)* |
| **Low Overhead** | No interpreters, no lockfiles, no network calls | *(No Change)* |
| **Auditability** | Every commit is validated; every changelog entry maps to a real commit | **Enhanced:** Every *atomic step* in a feature is semantically validated before landing in the main branch. |
| **SLM Efficiency** | Stage 2 output is clean, structured Markdown → minimal SLM context | **Enhanced:** Cleaner mainline history reduces noise for the parser and SLM. |
| **Atomic Enforcement** | Fully supports the transition from single-squash-commit history to **linear, multi-atomic-commit history**. | Transition enables higher velocity and better diagnostics. |

-----

## 7. Advanced Workflow Adoption Strategy

### 7.1 The Scaling Dilemma: Complexity vs. Velocity

The default enforcement of **Squash and Merge** provides simplicity and consistency but can create a velocity bottleneck on large, complex features where a developer is forced to rebase a deep, multi-day work branch locally. The **Stacked Diff** method (Section 6.D of the Git Workflow Handbook) is the engineering solution to this scaling dilemma.

### 7.2 Trigger for Specialized Tool Adoption

The adoption of specialized Stacked Diff tools is **not mandatory** for the baseline workflow. They will be mandated only when the limitations of the default `Squash and Merge` workflow impede team velocity.

Mandatory adoption of tools like Graphite or Sapling is triggered by any two of the following conditions sustained for two sprints:

1.  **Review Latency:** The median time-to-review for PRs exceeds 48 hours, often due to large, monolithic change sets.
2.  **Rebase Complexity:** Developers are consistently reporting significant time lost (e.g., \>2 hours per week per engineer) resolving conflicts during interactive rebases (`git rebase -i`).
3.  **WIP History:** Feature branches frequently exceed 20 commits prior to the final squash, indicating a violation of the "Commit by Logic" principle (Section 4).

### 7.3 Tooling Compatibility

The current core tooling (`gitlint` and `git-chglog`) is **agnostic** to the adoption of specialized Stacked Diff tools. They rely only on the clean, atomic, semantic nature of the commits landing in the mainline branch, which is enforced by both the default `Squash and Merge` and the advanced `Stacked Diff` exception.

-----

## 8. Anti-Patterns to Avoid

| Anti-Pattern | Consequence |
|:-------------|:-------------|
| Using `commitizen` in CI | Interactive prompts hang CI; non-idempotent |
| Generating changelogs from `git log --oneline` + regex | Fragile parsing; misses scope/type structure |
| Feeding raw `git diff` to SLM for changelog | VRAM explosion; OOM; non-reproducible output |
| Custom Python changelog scripts | Reinventing the wheel; introduces drift and bugs |

-----

## 9. Summary: The Golden Path

1.  **Developer writes code** → stages changes.
2.  **`git commit`** → `pre-commit` runs `gitlint` → enforces Conventional Commits.
3.  **On release prep**, CI runs `git-chglog` → produces `CHANGELOG.md`.
4.  **SLM (7B–14B)** consumes **only the relevant `CHANGELOG.md` section** → generates audience-tailored release notes.
5.  **Engineer reviews** both changelog and SLM output before publish.

> **This is the only supported workflow.** Keep it simple. Keep it deterministic. Keep SLMs where they add unique value—**not for parsing Git history**.
