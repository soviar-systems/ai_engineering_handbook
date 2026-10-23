# Plan: Archive the AI Engineering Book (Complete Freeze)

**Date:** 2026-10-24
**Status:** Ready for execution
**Decision (owner, 2026-10-24):** **complete freeze** — archive the repository read-only, copy nothing into a successor, maintain nothing afterwards. The archive itself is the reference to be consulted later for insight.
**One directory leaves:** `soviar_toolkit/` is a candidate successor that was being built *inside* this repository. Closing the predecessor requires separating them, so Phase 1 moves it out and takes a local snapshot of it. That is a **move of the candidate's own files, not a harvest of archive content** — the direction of travel is outbound, and nothing from the archive goes with it.
**Two withdrawn options:** (a) *salvage-then-freeze* — copying skills, ADRs, and scripts into a successor; (b) *leave the candidate in place and gitignore it*. Both were withdrawn by the owner. If you find stray references to a "harvest", a "handoff root", `soviar-archive-handoff`, or a `.gitignore` rule for `soviar_toolkit/`, they are stale — this document is authoritative.
**Deliberately not decided here:** the successor's architecture, its relationship to `../soviar-toolkit`, and its branches, remotes, tags, or CI. The owner is closing old projects, not designing new ones. Phase 1 relocates a directory; it does not start a project.
**Executing agent:** you have no prior session context. Everything needed is below. Do not re-brainstorm, do not add steps, do not decide to salvage anything, and do not merge the two toolkits.

---

## 0. Why This Plan Exists

The AI Engineering Book has been de facto dormant since June 2026 (18 commits in June, 0 in July–September, 3 in October). Its governance layer (369 tracked files) is larger than the knowledge it governs (140 files). Its three validators report 130 frontmatter errors, 6 ADR errors, and 18 broken links while **all exiting 0**. Its candidate successor was living untracked inside it, and because one project's files sat under the other project's schema, 58 of those 130 errors and 13 of those 18 broken links were never about this repository at all.

The owner has decided to close it completely: no successor migration, no copied content, no ongoing maintenance. The repository's value from here on is as a **readable legacy record** — someone returns to the tag, reads the decisions, and takes ideas. That requires the archive to be complete and honest, not repaired and not modernised.

It also requires the archive to be *only the archive*. A closed project that still contains a live one is not closed, and post-mortem measure M4 — no successor inside a predecessor — is the one lesson this freeze can still apply to itself. Phase 1 is therefore a separation, not a migration.

The full reasoning is `architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md` (R-26004), which is part of this change.

**Repairing the remaining debt is explicitly out of scope.** The post-mortem argues that the attempt to repair is what caused the archive. Do not fix the 72 legacy errors. Do not upgrade dependencies. Do not migrate the schema.

---

## 1. Full Context

### 1.1 Repository identity

| Property | Value |
|---|---|
| Absolute path | `/home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book` |
| Branch at planning time | `release/3.2.0` |
| HEAD at planning time | `8b8c90b` |
| Remotes | `origin` → `git@github.com:soviar-systems/ai_engineering_handbook.git`; `hub` → `git@hub.soviar.ru:commi/ai_engineering_book.git` |
| Tracked files | 532 |
| Git object size | 19 MB |
| Commits / authors | 686 / 1 (Vadim Rudakov) |
| Latest tag | `v3.1.0` (15 tags) |
| `main` vs `release/3.2.0` | `main` is 21 commits behind, **0 divergent** → fast-forward is lossless |

### 1.2 Measured state at planning time

| Measurement | Command | Result |
|---|---|---|
| Knowledge files | `git ls-files ai_system_layers ai_agents 0_intro security \| wc -l` | 140 |
| Governance/support files | `git ls-files tools architecture .vadocs .qwen misc \| wc -l` | 369 |
| Scripts / tests | `ls tools/scripts/*.py` / `uv run pytest tools/tests -q` | 23 scripts / **1379 passed, 1 skipped** in 2.6 s |
| ADRs | `ls architecture/adr/*.md \| wc -l` | 56 (55 numbered + template) |
| Skills on disk | `ls .qwen/skills \| wc -l` | 32 |
| Frontmatter errors | `uv run python -m tools.scripts.check_frontmatter` | 130, **exit 0** |
| ADR errors | `uv run tools/scripts/check_adr.py` | 6, **exit 0** |
| Broken links | `uv run tools/scripts/check_broken_links.py --pattern "*.md"` | 18, **exit 0** |
| External corpus | `du -sh ai_agents/research` | **4.2 GB**, 15 registered clones |
| Successor candidate (untracked) | `du -sh soviar_toolkit` / `find … \| wc -l` | 25 MB (688 KB source + 25 MB regenerable `.venv`), **61 source files** (+25 `.pyc` in `__pycache__`) |

Attributable to the archive itself: **72 frontmatter errors** and **5 broken links** at separation, all genuine core debt, none of it repaired during the freeze. The remaining 58 frontmatter errors and 13 broken links belonged to the untracked candidate, which Phase 1 removes from this working tree.

**Measured outcome (Phase 1 + Phase 0 executed 2026-10-24):** `check_frontmatter` reports **62**, not 72, because ten of the 72 belonged to R-26001/R-26002/R-26003, which Phase 0 repaired in order to commit them at all. `check_adr` reports **6** and `check_broken_links` reports **5**, both matching the prediction exactly. None of the 62 remaining errors is in a file this plan added or modified — verified by filtering the validator output for `R-2600`, `post_mortem_sunset`, and `ARCHIVED`. `check_frontmatter` walks the filesystem rather than Git, so the 130/18 figures in the table above are the **pre-separation** measurement and must not be quoted as the archive's own count.

### 1.3 Working tree at planning time (`git status --porcelain`)

```
 M .qwen/skills/jit-instruction-tooling-for-agents/SKILL.md
 M .qwen/skills/pre-commit-commit-scoped-validation/SKILL.md
 M .qwen/skills/production-link-safety-validation/SKILL.md
 M misc/in_progress/apendices/markdown/local_markdown_rendering.md
 M misc/todo.md
?? architecture/evidence/retrospective/
?? architecture/evidence/sources/S-26025_skillopt_adoption_analysis.md
?? architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md
?? repro_order.md
?? soviar_toolkit/
?? tools/docs/git/git_notes_for_ai_provenance.md
```

`architecture/evidence/retrospective/` contains exactly three files: `R-26001_validation_deadlock.md`, `R-26002_link_validation_false_positives.md`, `R-26003_instruction_drift.md`.

**Two corrections to `misc/plan/freeze.md`** (do not "fix" that file, just know it):

- It lists ADR-26057 and A-26026 as uncommitted. They are **already tracked**. Only `S-26025` is untracked.
- It promises ADR-26058, which **does not exist** (55 numbered ADRs, highest is 26057). **Do not create it.**

### 1.4 The successor candidate — what is decided and what is not

`soviar_toolkit/` is **not** a stray prototype. It is the **candidate replacement** for the sibling repository `../soviar-toolkit`, which is exactly why it was never tracked here: it belongs to the next project, not to this one. It is 61 source files and 688 KB — a Python package (`src/soviar_toolkit/`, 11 modules), 4 test files, `config/manifest.json`, 9 ADRs (`26001`–`26009`), 13 RDD skills, and three requirement bundles — sitting inside a documentation repository whose validators then scanned it under the wrong schema. That is the entanglement post-mortem measure **M4 — no successor inside a predecessor** describes.

**Decided (owner, 2026-10-24):** the candidate leaves this working tree before the write lock. Not because the archive needs it — the archive needs nothing from it — but because two things follow from leaving it:

1. `git status --porcelain` can never be empty while an untracked 25 MB foreign project sits in the root, so the freeze could never be verified.
2. A closed project that still contains a live one has not closed. The owner's stated goal is to finalise old projects and clear the debt out of them; a nested live project *is* the debt.

Phase 1 relocates it to `../soviar-toolkit-candidate` and takes a local git snapshot so that 61 source files cannot be lost to a single `rm` or a disk failure.

**Not decided, and deliberately left open:** how the candidate relates to `../soviar-toolkit` (which holds `master` at `045aae6`, a `feature/pre-commit-skill` branch at `8b660fc`, and **16 staged-but-uncommitted files**), whether either becomes the successor, and what that successor's architecture, branch model, or remotes will be. The owner is finalising old projects, not designing new ones. **Do not merge the two repositories. Do not delete, rename, or commit inside `../soviar-toolkit`.** Phase 1b is optional, gated, and explicitly outside this repository.

**Consequence, which is accepted:** the candidate is not part of this archive, will not appear on GitHub, and cannot be recovered from the tag. `ARCHIVED.md` records that it was separated so a future reader is not puzzled by references to a successor that is absent. The relocation is one `mv` away from being undone.

### 1.5 Constraints inherited from the repository (non-negotiable)

- Never use `sed -i`, `git reset`, `git clean -f`, `git add -A`, `--no-verify`, or force-push.
- Stage files explicitly by path.
- Use `git restore` (not `git checkout --`) and `git switch` (not `git checkout <branch>`).
- Commit format: `type: subject` (≤50 chars), body as `- Verb: path — what_and_why`. Valid types are in `pyproject.toml [tool.commit-convention]`.
- Never edit `CHANGELOG` (generated from commits).
- Commit bullets naming `misc/`, `CLAUDE.md`, `AGENTS.md`, `QWEN.md`, `.aider`, or `jupytext` are filtered from the changelog — describe intent, do not list those literal paths.
- `.qwen/` is listed in `.gitignore`; only 9 of the 32 skill directories are tracked (they were force-added historically). Do not "fix" this.

### 1.6 Out of scope

- Fixing legacy validation errors, dependencies, or the frontmatter schema.
- Publishing v3.2.0 as a release.
- Rewriting history, removing blobs, or `git filter-repo` (the 4.2 GB corpus is untracked, so no rewrite is needed or authorised).
- Deleting, privatising, or re-publishing the GitHub repository.
- Repairing, restructuring, or extending `soviar_toolkit/` before or after the move. It is relocated **as-is**, at the state it was left in.
- Deciding the successor's architecture, merging it with `../soviar-toolkit`, or giving it branches, remotes, tags, or CI.
- Modifying `../soviar-toolkit` at all: no commit, no merge, no rename, no delete. Phase 1b is gated and optional.
- Copying anything out of the archive into any successor, handoff package, or skills directory.

---

## 2. Target End State (Definition of Done)

1. All outstanding artifacts are committed; `git status --porcelain` is **empty**.
2. `soviar_toolkit/` no longer exists under the archive path. It lives at `../soviar-toolkit-candidate` with a local git snapshot whose single commit contains all 61 source files.
3. `main` contains the final state (fast-forwarded from `release/3.2.0`) and is checked out.
4. Annotated tag `archive-2026-10-24` exists locally and on `origin`.
5. `ARCHIVED.md` exists at root; `README.md` carries an archive banner; `RELEASE_NOTES.md` closes with a sunset entry.
6. `myst.yml` excludes `ai_system_layers/**/*.md` and names the `soviar-systems` owner.
7. `uv run pytest tools/tests -q` still reports 1379 passed, 1 skipped.
8. `check_frontmatter` on every file added or modified by this plan exits **0**.
9. GitHub repository archived (read-only); Pages left serving its last deployment.
10. **No file has been copied out of the archive.** One directory (`soviar_toolkit/`) was moved out whole in Phase 1, and `repro_order.md` was moved to `/tmp`. Nothing else crosses the boundary, and no tracked file changed as a result of Phase 1.

---

## 3. Disposition Table

Legend: ✅ stays in archive · ✗ removed from the working tree only (untracked/ignored/moved out) · 📋 committed by this plan · ⊘ ignored, left in place

| Path | Size | Disposition | Note |
|---|---|---|---|
| `ai_system_layers/`, `0_intro/`, `ai_agents/architecture/`, `ai_agents/guides/`, `security/`, `mlops/` | 7.2 MB | ✅ | The knowledge; the reason the archive exists |
| `architecture/` (ADRs, evidence, post-mortems) | 2.2 MB | ✅ 📋 | Decision corpus; post-mortem + three retrospectives + S-26025 are new |
| `tools/` (23 scripts, 1379 tests, docs) | 14 MB | ✅ 📋 | Provenance and reference implementations |
| `.vadocs/` | 56 KB | ✅ | Governance SSoT: what the rules were |
| `.qwen/skills/` | 344 KB | ✅ | 9 tracked, 23 untracked-and-ignored (see §1.5) |
| `misc/` (52 plans, todo, drafts) | 42 MB | ✅ 📋 | Decision history |
| `AGENTS.md` + `QWEN.md`/`CLAUDE.md`/`CONVENTIONS.md` symlinks | 22 KB | ✅ | Preserved as evidence of the instruction bloat |
| `README.md`, `RELEASE_NOTES.md`, `myst.yml` | — | ✅ 📋 | Edited in Phase 2 |
| `ARCHIVED.md` | new | 📋 | Archive notice, full content in §7 |
| `ai_agents/research/` | **4.2 GB** | ✗ (optional, Phase 4) | 15 registered clones, all re-clonable |
| `.venv/` | 356 MB | ✗ (optional) | `uv sync --frozen` |
| `.mypy_cache/`, `.pytest_cache/`, `.coverage`, `**/.ipynb_checkpoints/`, `__pycache__/` | ~9 MB | ✗ (optional) | Caches |
| `.aider.chat.history.md`, `.aider.input.history`, `.aider.tags.cache.v4` | ~6.6 MB | ⊘ | Already ignored; leave |
| `soviar_toolkit/` | 688 KB + 25 MB `.venv` | ✗ moved out (Phase 1) | Candidate successor, not archive material. Relocated whole to `../soviar-toolkit-candidate` with its own local snapshot. Its `.venv` is deleted after the move (regenerable, and broken by relocation anyway). |
| `repro_order.md` | 10 lines | ✗ | Stray frontmatter scaffold in repo root; back up to `/tmp`, then remove |
| `tools/docs/jupyter_and_markdown/Untitled.md` | corrupt | ✅ | Leave. Removing it would be a repair, which is out of scope. |
| `release/3.2.0` branch | — | ✅ | Kept as evidence of the abandoned release |

---

## 4. Cross-Reference Map

| Changed thing | Referenced by | Current | After |
|---|---|---|---|
| Notebook `.md` exclusion | `myst.yml:21` | `- "ai_system/**/*.md"` (directory no longer exists) | `- "ai_system_layers/**/*.md"` |
| Repository owner | `myst.yml:9` | `github: https://github.com/lefthand67/ai_engineering_handbook` | `.../soviar-systems/ai_engineering_handbook` |
| Archive status | `README.md:19` (after `# AI Engineering Handbook`) | none | warning admonition |
| Release history | `RELEASE_NOTES.md:3` | `## release v3.1.0 …` | sunset entry inserted above it |
| Archive notice | `ARCHIVED.md` (new) | — | links to R-26004, `misc/plan/freeze.md`, `misc/plan/techdebt.md` |
| Successor candidate | this working tree (no tracked file references it) | at `soviar_toolkit/`, inside the archive | moves to `../soviar-toolkit-candidate`; **no tracked file changes** |
| Candidate → archive links | `soviar_toolkit/AGENTS.md:31`, `Roadmap.md:66` | relative `../ai_engineering_book`, which resolves to a non-existent *nested* directory | **not touched.** After the move they resolve to this archive, because the candidate becomes a sibling of it. The link starts working by accident and creates exactly the dependency M6 forbids — note it in Phase 1's report, do not fix it here. |
| Research corpus | `myst.yml:17–18`, `.gitignore`, `tools/scripts/paths.py` | excluded / ignored | unchanged (corpus is removed locally, not from history) |
| `~/.qwen/skills/*` | 6 symlinks into `ai_agents/research/…`, 1 into a sibling repo | working | **break if Phase 4 runs** — see Phase 4 gate |
| `misc/plan/freeze.md`, `misc/plan/techdebt.md` | `ARCHIVED.md` | — | linked, not edited |

**Nothing else in the repository references the strings this plan edits.** Verified with `grep` over `*.md`, `*.yml`, `*.py`, `*.json`, `*.toml`.

### Final-state link diagram

```
GitHub (archived, read-only)
└── soviar-systems/ai_engineering_handbook @ archive-2026-10-24
    ├── README.md ──banner──▶ ARCHIVED.md ──▶ R-26004 post-mortem
    ├── RELEASE_NOTES.md ──▶ tag tree URL
    ├── myst.yml (corrected; Pages frozen on its last deployment)
    └── architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md
              └──▶ misc/plan/plan_20261024_archive_ai_engineering_book.md (this plan, implemented)
```

No outward edges. That is the point: the archive depends on nothing and nothing depends on it.

One exception to state plainly: after Phase 1 the candidate becomes a **sibling** of the archive directory, so its relative link `../ai_engineering_book` starts resolving where it previously dangled. That is an accidental inbound edge from outside the archive. It is not repaired here (the candidate is out of scope) and it must not be relied on — M6 exists because an archive that acquires a live dependent can no longer stay frozen.

---

## 5. Tasks

### Phase 0 — Commit the outstanding artifacts

**Rationale:** the write lock must be applied to a complete record. Two commits, because `misc/` is changelog-excluded and mixing it into a changelog-visible commit produces a self-filtered body that promises more than it delivers.

```bash
cd /home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book
git switch release/3.2.0
git branch --show-current          # EXPECT: release/3.2.0

# 0.1 Evidence, provenance, skills, post-mortem, and this plan
git add architecture/evidence/sources/S-26025_skillopt_adoption_analysis.md \
        architecture/evidence/retrospective/R-26001_validation_deadlock.md \
        architecture/evidence/retrospective/R-26002_link_validation_false_positives.md \
        architecture/evidence/retrospective/R-26003_instruction_drift.md \
        architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md \
        tools/docs/git/git_notes_for_ai_provenance.md \
        .qwen/skills/jit-instruction-tooling-for-agents/SKILL.md \
        .qwen/skills/pre-commit-commit-scoped-validation/SKILL.md \
        .qwen/skills/production-link-safety-validation/SKILL.md \
        misc/plan/plan_20261024_archive_ai_engineering_book.md
git commit                          # message: Commit A, §6

# 0.2 Scratch notes
git add misc/todo.md \
        misc/in_progress/apendices/markdown/local_markdown_rendering.md
git commit                          # message: Commit B, §6

# 0.3 Relocate the stray scaffold out of the repository root
cat repro_order.md                  # EXPECT: ~10 lines, generic frontmatter template
mv repro_order.md /tmp/ai_engineering_book_repro_order.md.bak
```

**Expected:** both commits succeed. `git status --porcelain` afterwards shows exactly one entry — `?? soviar_toolkit/` — which Phase 1 removes.

**What the first attempt at this commit discovered** (recorded so the next agent does not repeat it): the three retrospectives had never been validated, because they were untracked. Once staged, three `[BLOCKING]` frontmatter failures appeared — R-26001 and R-26002 had no `options.type`, and R-26003 had no frontmatter at all. Repairing them exposed a second defect: their filenames used `R_26001_...` while the evidence naming pattern is `^R-(\d{2})(\d{3})_[a-z]...`, i.e. `R-26001_...`. `check_evidence.py` had been **silently skipping** all three, which is why the hook reported success. They were restructured to the canonical retrospective sections, renamed with a hyphen, and `token_size` recomputed. `misc/plan/implemented/plan_20260627_fix_validation_blind_spots.md` is staged alongside them because it referenced the old filenames.

**Why the plan file ships in Commit A, not Commit B:** the post-mortem links to this plan. The link checker treats a link to an *untracked* file as `[BLOCKING]`, so if the plan were still untracked when the post-mortem was staged, Commit A's hook would fail. Everything the post-mortem links to — the three retrospectives, `S-26025`, and this plan — is staged in Commit A for that reason. No changelog bullet names the `misc/` path, because such bullets are self-filtered.

**If a commit is rejected** for `token_size`, run `uv run tools/scripts/update_token_counts.py <file named in the error>`, stage **only that file**, and retry. `[LEGACY]` messages from hooks are expected and non-blocking; a `[BLOCKING]` failure is not expected after the staging order above — investigate rather than bypass.

**Do not** stage `soviar_toolkit/`. **Do not** create ADR-26058. **Do not** commit `repro_order.md`.

---

### Phase 1 — Separate the successor candidate

**Rationale:** the candidate must not be inside the predecessor when the predecessor closes (M4), and `git status` can never be empty while a 25 MB foreign project sits in the root. This phase changes **no tracked file** in the archive. It moves one untracked directory out and gives it a local snapshot so it survives.

The destination is `/home/commi/Yandex.Disk/it_working/projects/soviar-systems/soviar-toolkit-candidate`. It is a **parking position, not a project setup**: no remote, no branches beyond the default, no tags, no CI, no rename of anything inside it. The owner has not decided the successor's architecture, and this phase must not decide it by accident.

```bash
cd /home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book

# 1.1 Preconditions — capture them, they are the baseline for V7
test -d soviar_toolkit && echo "CANDIDATE PRESENT"
du -sh soviar_toolkit                                  # EXPECT: 25M (25M of which is .venv)
find soviar_toolkit -path soviar_toolkit/.venv -prune -o \
                    -path soviar_toolkit/.pytest_cache -prune -o \
                    -name __pycache__ -prune -o \
                    -type f -print | wc -l              # EXPECT: 61
test -f soviar_toolkit/.gitignore && echo "HAS .gitignore" || echo "NO .gitignore"   # EXPECT: NO

# 1.2 The destination must be free — do not overwrite anything
test -e ../soviar-toolkit-candidate && echo "STOP: destination exists" || echo "FREE"
# EXPECT: FREE. If it says STOP, do not proceed; report and ask.

# 1.3 Move it out, whole, in one operation
mv soviar_toolkit ../soviar-toolkit-candidate
test -d soviar_toolkit || echo "SEPARATED"
git status --porcelain                                 # EXPECT: no output
```

`mv` on the same filesystem is a rename, not a copy — 25 MB moves instantly and nothing is lost if the command is interrupted mid-way (it either happened or it did not).

```bash
cd ../soviar-toolkit-candidate

# 1.4 The snapshot needs an ignore file first, or .venv enters the commit
#     Create .gitignore with exactly these five lines:
#       .venv/
#       __pycache__/
#       .pytest_cache/
#       *.pyc
#       *.egg-info/
cat .gitignore

# 1.5 Drop the environment — it is regenerable and its shebangs already
#     point at the old absolute path, so it is half-broken after the move
rm -rf .venv .pytest_cache
find . -name __pycache__ -type d -prune -exec rm -rf {} +
du -sh .                                               # EXPECT: under 1M

# 1.6 Local snapshot — one commit, nothing else
git init -b main
git add .
git commit -m "snapshot: park the RDD toolkit candidate as it stood at successor separation"
git rev-list --count HEAD                              # EXPECT: 1
git ls-files | wc -l                                   # EXPECT: 62 (61 files + .gitignore)
git status --porcelain                                 # EXPECT: no output
git remote -v                                          # EXPECT: no output — no remote is created
```

**Expected:** the archive's `git status --porcelain` is empty; `/home/commi/Yandex.Disk/it_working/projects/soviar-systems/soviar-toolkit-candidate/` contains 62 tracked files in one commit and no remote; `soviar_toolkit/` no longer exists under the archive path.

**Commit C of the earlier draft is deleted.** There is no `.gitignore` edit and no commit in this phase, because moving the directory out is what makes the tree clean — an ignore rule would only have hidden the entanglement instead of ending it. Do not add `soviar_toolkit/` to `.gitignore`; the directory is gone.

**If the move is impossible** (destination exists, permissions, cross-device `EXDEV` in a way `mv` cannot handle): stop and report. Do **not** fall back to deleting the candidate, and do **not** fall back to gitignoring it.

---

### Phase 1b — (OPTIONAL, GATED, OTHER REPOSITORY) Preserve the incumbent's staged work

**Rationale:** `../soviar-toolkit` holds **16 staged-but-uncommitted files** — an openspec change and the `pre-commit-review` skill with 5 prompt revisions and 2 report templates. They exist only on this disk and in no commit. The owner's goal is to clear old debts, and an uncommitted working tree is a debt with a single point of failure.

This phase is **outside the archive repository** and is **not required** for the freeze. Skip it unless the owner explicitly approves: it writes to a repository this plan does not otherwise touch.

```bash
cd /home/commi/Yandex.Disk/it_working/projects/soviar-systems/soviar-toolkit
git status --porcelain --branch                         # EXPECT: ## feature/pre-commit-skill, 16 x "A "
git diff --cached --name-only | wc -l                   # EXPECT: 16

git commit -m "feat(skills): add pre-commit-review skill and openspec change"
git status --porcelain                                  # EXPECT: no output
git log --oneline -1
```

**Deliberately not done here:** switching branches, merging into `master`, adding a remote, or touching the candidate. Those are architecture decisions the owner has deferred. This phase only converts 16 staged files into 1 commit.

**Expected if skipped:** nothing is lost *today*; the files remain staged on disk. Record in the handover note that the incumbent still carries 16 uncommitted files.

---

### Phase 2 — Freeze the surfaces

**Rationale:** a legacy record that is read later must not contain a site configuration that silently duplicates every notebook page, and must state plainly what it is and what is broken inside it.

#### 2.1 `myst.yml` — correct the repository owner

`old_string`:
```
  # keywords: []
  # authors: []
  github: https://github.com/lefthand67/ai_engineering_handbook
  exclude:
```
`new_string`:
```
  # keywords: []
  # authors: []
  github: https://github.com/soviar-systems/ai_engineering_handbook
  exclude:
```

#### 2.2 `myst.yml` — point the notebook exclusion at the renamed tree

`old_string`:
```
    # jupytext pairs md to ipynb
    - "0_intro/**/*.md"
    - "ai_system/**/*.md"
    - "mlops/**/*.md"
```
`new_string`:
```
    # jupytext pairs md to ipynb
    - "0_intro/**/*.md"
    - "ai_system_layers/**/*.md"
    - "mlops/**/*.md"
```

#### 2.3 `README.md` — banner above the fold

`old_string`:
```
  version: 3.1.0
  birth: 2025-10-19
  token_size: 3595
---
# AI Engineering Handbook
```
`new_string`:
```
  version: 3.1.0
  birth: 2025-10-19
  token_size: 3595
---
# AI Engineering Handbook

:::{warning} Archived — 2026-10-24
This repository is **archived and read-only**. It ran from 2025-10-19 to 2026-10-24 as the AI Engineering Book and is preserved as a closed legacy record. Active work continues elsewhere. Known validation debt was deliberately left unrepaired — see [ARCHIVED.md](/ARCHIVED.md) for the full disposition and the post-mortem.
:::
```

#### 2.4 `RELEASE_NOTES.md` — close the release history

`old_string`:
```
# Release Notes

## release v3.1.0 "The Industrialization of Intelligence"
```
`new_string`:
```
# Release Notes

## archive v3.1.x "Sunset"

**2026-10-24** — This repository is archived and read-only. No further releases will be published from it.

The final state is tagged [`archive-2026-10-24`](https://github.com/soviar-systems/ai_engineering_handbook/tree/archive-2026-10-24). The post-mortem records what the project achieved, why its governance layer outgrew the knowledge it governed, and what a future reader should and should not take from it: [R-26004](/architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md).

**v3.2.0 was never published.** The `release/3.2.0` branch carried frontmatter normalization, ADR governance consolidation, and validation fixes. It was fast-forwarded into `main` as the archive baseline without a version bump, because the repository ended before the release criteria were met.

## release v3.1.0 "The Industrialization of Intelligence"
```

#### 2.5 `ARCHIVED.md` — new file at repository root

Create it with the **exact content in §7**, then:

```bash
uv run tools/scripts/update_token_counts.py ARCHIVED.md
uv run python -m tools.scripts.check_frontmatter ARCHIVED.md README.md
echo "EXIT=$?"
```

**Expected:** `EXIT=0`. `token_size` is set by the first command, so it will differ from the `0` placeholder in §7 — that is correct, leave the computed value.

#### 2.6 Commit

```bash
git add myst.yml README.md RELEASE_NOTES.md ARCHIVED.md
git commit                          # message: Commit C, §6
git status --porcelain              # EXPECT: no output
```

---

### Phase 3 — Fast-forward `main` and tag

**Rationale:** archiving a default branch that is 21 commits stale would make the GitHub landing page misrepresent the final state. There are 0 divergent commits, so the fast-forward is lossless.

```bash
git switch main
git merge --ff-only release/3.2.0
git tag -a archive-2026-10-24 -m "Final state of the AI Engineering Book; archived 2026-10-24. Read-only legacy record. See ARCHIVED.md."

git branch --show-current           # EXPECT: main
git log --oneline -1                # EXPECT: the Phase 2 commit (Commit C)
git tag -l 'archive-*'              # EXPECT: archive-2026-10-24
git status --porcelain              # EXPECT: no output
git merge-base --is-ancestor release/3.2.0 main && echo "RELEASE INCLUDED"
```

**Expected:** `Fast-forward`, then `RELEASE INCLUDED`.

**Do not** tag `v3.2.0`. **Do not** delete or rename `release/3.2.0`.

---

### Phase 4 — Reclaim local disk (OPTIONAL, GATED, destructive)

**Rationale:** 4.6 GB of regenerable material makes the archive unpleasant to keep locally. This phase changes **no** tracked file; everything it deletes is untracked or ignored.

**Gate 4a — prove re-clonability:**

```bash
uv run tools/scripts/manage_external_repos.py list
```

**Expected:** `📚 External Product Repositories (15 total):` and 15 rows each with a `Remote` URL. **If any row has an empty or missing Remote, stop** — that repository is not re-clonable and must be kept.

**Gate 4b — accept the symlink breakage:**

```bash
ls -l ~/.qwen/skills | grep -- '->'
```

Expected: 7 symlinks. Six point into `ai_engineering_book/ai_agents/research/…` (`brainstorming`, `pdf`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `writing-skills`, `xlsx`) and will **break** if the corpus is deleted. One points into a sibling `soviar-toolkit/` repo and is unaffected.

The broken links are user-level conveniences, not archive content. Either accept the breakage (re-clone later to restore them) or skip Phase 4 entirely. **Do not** delete the symlinks as part of this plan — that is outside the repository and outside the decision.

**Gate 4c — explicit owner approval.** Report the exact sizes, then run:

```bash
du -sh ai_agents/research .venv .mypy_cache .pytest_cache .aider.chat.history.md
# EXPECT: ~4.2G  356M  7.9M  280K  5.0M

rm -rf ai_agents/research .venv .mypy_cache .pytest_cache __pycache__ 0_intro/.ipynb_checkpoints
rm -f .aider.chat.history.md .aider.input.history
rm -rf .aider.tags.cache.v4

git status --porcelain              # EXPECT: no output (all of the above is ignored)
```

**Expected:** `git status --porcelain` still empty, and `du -sh .` drops by roughly 4.6 GB. Skipping this phase entirely is a valid outcome.

---

### Phase 5 — Publish and archive (GATED: shared state)

**Rationale:** pushing and archiving are visible to anyone with the URL and cannot be undone silently. `gh` returned HTTP 401 during planning, so authentication is a prerequisite, not a formality.

**Gate 5 — explicit owner approval required before this block.**

```bash
# 5.1 Push the final state and the tag
git push origin main
git push origin archive-2026-10-24

# 5.2 Mirror to the self-hosted remote, then stop pushing there permanently
git push hub main
git push hub archive-2026-10-24

# 5.3 Authenticate
gh auth login

# 5.4 Record the pre-archive state
gh repo view soviar-systems/ai_engineering_handbook \
  --json name,visibility,isArchived,pushedAt,defaultBranchRef

# 5.5 Archive (read-only). Pages keeps serving its last deployment.
gh repo archive soviar-systems/ai_engineering_handbook --yes

# 5.6 Verify
gh repo view soviar-systems/ai_engineering_handbook --json isArchived
```

**Expected:** `main -> main` and the tag ref created on both remotes; 5.4 returns `"isArchived": false` (record `visibility` and `pushedAt` in the handover note); 5.5 prints `✓ Archived repository …`; 5.6 returns `{"isArchived":true}`.

**If 5.5 fails on permissions:** stop and report. Do **not** make the repository private, and do **not** delete it, as a workaround.

**After archiving:** do not run the deploy workflow, do not push, do not open PRs. The `hub` remote becomes a cold mirror and receives nothing further.

---

## 6. Commit Messages (paste verbatim)

There are **three** commits on the archive branch. Phase 1 produces none — it moves an untracked directory and writes nothing into the archive. An earlier draft had a fourth commit that added `soviar_toolkit/` to `.gitignore`; it is gone, and any instruction you find telling you to add that rule is stale.

**Commit A**
```
docs: commit pending artifacts before freeze

- Add: architecture/evidence/sources/S-26025_skillopt_adoption_analysis.md — preserve the analysis behind ADR-26057
- Add: architecture/evidence/retrospective — record validation-deadlock, false-positive, and instruction-drift lessons
- Add: architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md — final post-mortem for the project
- Add: tools/docs/git/git_notes_for_ai_provenance.md — capture provenance conventions the history depends on
- Refine: .qwen/skills — capture validated revisions to three SOPs before the write lock
```

**Commit B**
```
chore: record pre-archive status notes

- Refine: local markdown rendering notes — preserve scratch research on offline rendering
- Refine: open work snapshot — capture outstanding tooling items at the moment of archival
```

Commit B carries **no** bullet for the execution plan: that file ships in Commit A, so a bullet here would describe work this commit does not contain.

**Commit C**
```
docs: publish archive notice and fix site config

- Add: ARCHIVED.md — state the archive status, known issues, and what was not included
- Add: README.md — surface the archive banner above the fold
- Add: RELEASE_NOTES.md — close the release history with the sunset entry
- Fix: myst.yml — target ai_system_layers in the notebook exclusion and correct the repository owner
```

---

## 7. `ARCHIVED.md` — full content

```markdown
---
title: Archive Notice — AI Engineering Book
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Status, known issues, and disposition of an archived knowledge base on building production-grade AI systems.
tags:
- governance
- documentation
date: 2026-10-24
options:
  type: guide
  birth: 2026-10-24
  version: 1.0.0
  token_size: 0
---
# Archive Notice

**Status:** archived and read-only since 2026-10-24.
**Lifetime:** 2025-10-19 → 2026-10-24 · 686 commits · 15 releases (final published: v3.1.0).
**Final tag:** `archive-2026-10-24`.
**Post-mortem:** [R-26004](/architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md).

## Why it was archived

The repository succeeded as a knowledge artifact and became unsustainable as a system. Its governance and support layer (369 tracked files) grew larger than the knowledge it governed (140 files); its validators reported errors while exiting 0; and a candidate successor was being built untracked inside it. Activity stopped in June 2026 and never resumed.

Archiving keeps everything readable while ending the maintenance obligation. No archive content was copied into a successor: the archive is the reference. The one directory that left — the candidate successor — left because a closed project cannot contain a live one, not because the archive had anything to hand on. The post-mortem contains the full diagnosis and eight preventive measures written for whatever comes next.

## How to use this archive

Read it for insight, then build independently. It is a closed record, not a dependency.

- **Methodology** — 56 ADRs on documentation engineering, prompt compilation, context budgeting, and AI-native development.
- **Reference implementations** — the prompt compiler (`tools/scripts/prepare_prompt.py`), the frontmatter validator, the broken-link checker, and 1379 tests that document their intended behaviour.
- **Debugging patterns** — the tracked skills under `.qwen/skills/` and the retrospectives under `architecture/evidence/retrospective/`.
- **A negative result worth reading** — how a well-intentioned governance system consumes the artifact it governs.

Do not import this repository's schema, ADR identifiers, or scripts into new work. Its ADR namespace was already colliding with a nested project's before the freeze, and the governance model it documents is the one the post-mortem argues against.

## Known issues, deliberately unrepaired

Do not read a green pipeline as compliance. At the moment of archiving:

- `check_frontmatter` reports 72 errors and **exits 0** (`[LEGACY]` mode).
- `check_adr` reports 6 errors and **exits 0**.
- `check_broken_links` reports 5 errors and **exits 0**.
- `tools/docs/jupyter_and_markdown/Untitled.md` contains malformed YAML frontmatter.
- ADR-26055 (Modular Knowledge Pull Architecture) was accepted and never implemented; `AGENTS.md` remains a 22 KB entry point symlinked four times.
- `misc/plan/freeze.md` contains stale entries: ADR-26057 and A-26026 are listed as uncommitted but were committed, and the promised ADR-26058 was never written.
- `release/3.2.0` was never released as v3.2.0; it was fast-forwarded into `main` as the archive baseline.

These are recorded rather than fixed. Fixing them would repeat the disproportion that caused the archive.

## What is not here

- `ai_agents/research/` — 4.2 GB of 15 external repositories, excluded from version control and removed locally. Re-clonable from the upstream URLs registered in `.vadocs/inventory/manage_external_repos.json`.
- The candidate successor that was being built inside this directory (`soviar_toolkit/`, 61 source files). It was separated from the repository immediately before the freeze and continues outside it, in its own directory with its own history. It is not part of this archive and was not derived from it; this repository is not a dependency of it.
- Skill directories under `.qwen/skills/` that were never tracked (`.qwen/` is gitignored; 9 of 32 directories are present in history).
- Virtual environments, caches, and agent session logs.

## Licensing

Code is covered by `LICENSE-CODE`; documentation is covered by `LICENSE-DOCS`. Archived content remains available under those terms.
```

---

## 8. Content Removal List

**Kept (✅):** all knowledge directories; all of `architecture/`; all of `tools/`; `.vadocs/`; `.qwen/skills/` as tracked — 9 of 32 directories, the other 23 are gitignored and stay untracked (§1.5, do not force-add them); all of `misc/`; `AGENTS.md` and its three symlinks; `release/3.2.0`; `CHANGELOG`; `tools/docs/jupyter_and_markdown/Untitled.md`.

**Removed from the working tree only, untracked or ignored (✗):** `ai_agents/research/` (4.2 GB, Phase 4 only); `.venv/`; caches; `repro_order.md` (after backing up to `/tmp`).

**Moved out of the repository, whole (✗ — Phase 1):** `soviar_toolkit/` → `../soviar-toolkit-candidate`, with a local commit. Nothing in it was copied, edited, or dropped except `.venv/`, `.pytest_cache/`, and `__pycache__/`, which are regenerable.

**Ignored and left in place (⊘):** `.aider*` logs.

**Explicitly not removed:** the GitHub repository (archive, never delete); the `hub` remote (cold mirror); any tracked file.

---

## 9. Verification

Run in order. V1–V8 must pass before Phase 5; V9 after.

```bash
cd /home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book

# V1 — tree is clean
git status --porcelain
# EXPECT: no output

# V2 — archive baseline
git branch --show-current                                   # EXPECT: main
git tag -l 'archive-*'                                       # EXPECT: archive-2026-10-24
git merge-base --is-ancestor release/3.2.0 main && echo "RELEASE INCLUDED"

# V3 — site config corrected
grep -n "ai_system_layers\*\*/\*.md\|soviar-systems/ai_engineering_handbook" myst.yml
# EXPECT: both lines present
grep -c 'ai_system/\*\*' myst.yml                            # EXPECT: 0

# V4 — new/modified docs validate
uv run python -m tools.scripts.check_frontmatter ARCHIVED.md README.md; echo "EXIT=$?"
# EXPECT: EXIT=0

# V5 — tooling still healthy (unchanged by this plan)
uv run pytest tools/tests -q
# EXPECT: 1379 passed, 1 skipped

# V6 — legacy debt, measured after separation
uv run python -m tools.scripts.check_frontmatter 2>&1 | grep -c ERROR
# EXPECT: 72. Phase 1 removed the 58 errors that belonged to the candidate.
# The 130/18 figures in §1.2 were the PRE-separation measurement — do not expect them here.
# A number ABOVE 72 means a file added by this plan has invalid frontmatter —
# fix that file, never the validator.

# V7 — successor separated and snapshotted
test -d soviar_toolkit && echo "STILL NESTED — FAIL" || echo "SEPARATED"
test -d ../soviar-toolkit-candidate/src/soviar_toolkit && echo "CANDIDATE PRESENT"
git -C ../soviar-toolkit-candidate rev-list --count HEAD   # EXPECT: 1
git -C ../soviar-toolkit-candidate ls-files | wc -l        # EXPECT: 62
git -C ../soviar-toolkit-candidate status --porcelain      # EXPECT: no output
git -C ../soviar-toolkit-candidate remote -v               # EXPECT: no output

# V8 — nothing copied out of the archive
git -C ../soviar-toolkit-candidate ls-files | grep -c 'ai_engineering_book'   # EXPECT: 0
ls /home/commi/Yandex.Disk/it_working/projects/soviar-systems/ | grep -c 'archive-handoff\|harvest'
# EXPECT: 0

# V9 — after Phase 5
gh repo view soviar-systems/ai_engineering_handbook --json isArchived
# EXPECT: {"isArchived":true}
```

**Acceptance:** V1–V8 pass before pushing. V9 passes after archiving. A V6 count **above** 72 means a file added by this plan has invalid frontmatter — fix that file; never touch the validator.

---

## 10. Rollback

| After | Undo | Loss |
|---|---|---|
| Phase 0 | `git restore --staged <path>`; `git restore <path>` for the edits | None (commits can be left in place; the archive tag can move) |
| Phase 1 | `mv ../soviar-toolkit-candidate soviar_toolkit` and, if a byte-identical tree is wanted, `rm -rf soviar_toolkit/.git` | None. `.venv` is gone; regenerate with `uv sync --frozen` inside it. |
| Phase 1b | Nothing needed. The commit is additive and lives in a repository outside this plan's scope; do not rewrite it. | None — 16 files move from the index into history |
| Phase 2 | `git restore myst.yml README.md RELEASE_NOTES.md`; `rm ARCHIVED.md` | None |
| Phase 3 | `git switch release/3.2.0`; `git tag -d archive-2026-10-24` | None, until pushed |
| Phase 4 | `uv sync --frozen`; `manage_external_repos.py update` | Re-clone time only |
| Phase 5 push | Correct with a new commit. **Force-push is not authorised.** | None |
| Phase 5 archive | Unarchive in GitHub Settings or via API; repository and Pages remain intact | None |
| Deleting the GitHub repository | **no rollback** — never part of this plan | Total |

---

## 11. Self-Review (completed by the plan author)

- [x] **Decision fidelity:** every trace of the withdrawn salvage option was removed. No harvest, no handoff root, no cross-repo copy of archive content. V8 asserts mechanically that nothing from the archive landed in the candidate.
- [x] **Spec coverage:** Phase 0 ← "commit as historical record"; Phase 1 ← "the candidate is the successor and must not live inside the archive" (M4) — it **moves**, it does not get gitignored and it does not get merged; Phase 1b ← the incumbent's 16 uncommitted files, gated because it is another repository; Phase 2 ← complete-freeze shape (honest record); Phase 3–5 ← freeze the surfaces; Phase 4 ← optional disk reclaim with gates.
- [x] **Direction of travel:** the plan moves exactly one directory **out** of the archive and copies nothing **into** any successor. The relocation and the rejected salvage differ in direction, and V8 distinguishes them.
- [x] **Placeholder scan:** no "appropriate content", no TBD, no "handle as needed". `ARCHIVED.md` has full content (§7); every edit has exact `old_string`/`new_string` with surrounding context.
- [x] **Cross-reference consistency:** `ai_system/**` occurs only at `myst.yml:21`; the owner string only at `myst.yml:9`; the banner anchors on `README.md:13–19`; the release entry on `RELEASE_NOTES.md:1–4`. There is **no** `.gitignore` edit: the only thing that made that file relevant was the candidate, and the candidate leaves.
- [x] **Numeric consistency:** 130 → 72 frontmatter errors reconciled by the 58 originating in the candidate, which Phase 1 removes; 18 → 5 broken links reconciled by 13; 21-commit fast-forward reconciled with `git rev-list --left-right --count` returning `0 21`. V6 was corrected to expect 72 because the validator walks the filesystem, not Git.
- [x] **Scope check:** nothing repairs the 72 legacy errors; nothing upgrades dependencies; nothing rewrites history; the candidate is relocated unmodified and its architecture left undecided; no archive content is copied outside the repository.
- [x] **Safety:** the only destructive steps are gated (Gate 4c for deletion, Gate 5 for publication), and Gate 4a/4b prove re-clonability and state the symlink consequences before anything is removed. No forbidden Git operation appears.
- [x] **Known unknowns:** GitHub visibility and Pages health were unverifiable at planning time (`gh` returned HTTP 401); Phase 5.4 records them instead of asserting them.
- [x] **Post-freeze discipline:** the plan forbids maintenance after the lock, including the tempting "one last cleanup". That prohibition is the substance of the decision, not an afterthought.
