# Roadmap: Gherkin Adoption in Corporate Debian Fork Development

## Context

**Problem:** Development of a corporate Debian fork with strict security requirements lacks a formalized lifecycle. Requirements flow as meetings → emails → Confluence docs → Jira tickets, but these artifacts are passive — the security division and clients can ignore them. There is no traceable link from requirement → implementation → verified behavior. The security division has their own assessment scripts (correctness checks) but these are disconnected from the requirements pipeline.

**Goal:** Establish Gherkin/BDD as the **executable requirements layer** — a single artifact that the security division authors, users can read, and CI enforces. Traceability becomes structural rather than documentary.

**Key insight from analysis summary (A7, E4):** Gherkin does not generate configurations — it specifies and verifies behavior. The lifecycle is: security requirement → Gherkin scenario → step definition wraps existing OS checks → CI gate on image builds. Living documentation that cannot go stale because the tests ARE the documentation.

**AI agent context:** AI tools are in a pre-mature integration stage. The roadmap treats AI as a scenario-writing assistant (meetings/emails → Gherkin drafts) in early phases, expanding to full specification assistant later.

---

## Recommended Approach: Domain-Scoped Incremental (C)

Pick one bounded security domain, run the full BDD lifecycle end-to-end, prove the approach, then expand. Domains follow natural OS layer boundaries.

**Selected pilot domain:** Sudo privilege division — the exact tension point where user stories (developer needs elevated access to do X) conflict with security requirements (least-privilege, audited actions only). The same `.feature` file serves all three stakeholders simultaneously:
- Security division: "what we permit and prohibit"
- Users: "what I can do and why"
- Developer: "the sudoers configuration contract"

---

## Roadmap Phases

### Phase 0: Foundation (Weeks 1–2)
**Goal:** Establish language, roles, tooling — without writing a single line of code yet.

- **Ubiquitous language session:** Define shared terms with security division. "Privilege," "role," "user class," "audit event" must mean the same thing in policy documents and Gherkin scenarios.
- **Three Amigos role mapping:**
  - Security division → Product Owner (authors acceptance criteria, signs off on scenarios)
  - System architect/you → Business Analyst (translates policy intent into concrete scenarios)
  - OS developer → Developer (implements configurations, writes step definitions)
- **Tooling decision:** Use `pytest-bdd` (not behave) — aligns with existing `uv run pytest` patterns in the project. Step definitions call OS-level checks directly (e.g., `sudo -l -U username`, `getent group`, `auditctl -l`).
- **Repository structure:** Create `security/features/` directory with one `.feature` file per domain.

### Phase 1: Pilot — Sudo Privilege Division (Weeks 3–8)
**Goal:** Full BDD lifecycle on the sudo domain. One working reference implementation.

**The flow: User Story → Security Requirements Engineering → Gherkin**

The trigger is always a **user story**, not a security policy. A developer/user brings a concrete need to the Three Amigos session. The security division engineers the requirements under which that story is permitted. Gherkin captures both the user's intent and the security constraints in a single executable artifact.

**Step 1 — Collect user stories (Week 3):**
- Gather all stories from users/developers that involve elevated privilege
- Format: "As a `<role>`, I need to `<action>` so that `<outcome>`"
- Examples: "As a developer, I need to install Python packages from PyPI"; "As a sysadmin, I need to reload the firewall rules"
- These are inputs to the Three Amigos session — not yet requirements

**Step 2 — Three Amigos session: story → requirements engineering (Week 3):**
- Developer brings the user story
- Security division engineers the requirements: "you can do X, but only under conditions A, B, C, with logging D"
- You (architect/developer) translate the agreed constraints into a Gherkin scenario in the session
- Each story produces: one or more scenarios (permitted path + denied paths + audit expectations)
- Output: draft `.feature` file that all three stakeholders co-authored

**Step 3 — Step definitions (Weeks 4–5):**
- Step definitions call real OS state: `subprocess.run(["sudo", "-l", "-U", user])`, `getent group`, read `/etc/sudoers.d/`
- Wrap security division's existing assessment script checks as steps where applicable
- Run against a QEMU/KVM test image (not production) — use existing image build pipeline

**Step 4 — CI gate (Week 6):**
- Add `uv run pytest security/features/ --tb=short` to CI pipeline
- Gate image delivery on green scenarios
- Failing scenario = requirement not met = image blocked

**Step 5 — Security division review (Week 7–8):**
- Present `.feature` file as the new "security policy document" for the sudo domain
- Show failing/passing CI run as the acceptance report
- Get formal sign-off: Gherkin scenario is the Definition of Done

### Phase 2: PAM & Identity (Weeks 9–16)
- Same Three Amigos → Gherkin → step definitions → CI gate process
- Domains: PAM password policy, SSSD integration, SSH access control
- Reuse step definition patterns from Phase 1
- Security division now has prior experience reading Gherkin — faster session

### Phase 3: Package Policy (Weeks 17–22)
- Integrate Gherkin gate into the image build pipeline (not just post-build verification)
- Scenarios test: prohibited packages absent, version pins enforced, repository restrictions active
- Security division's assessment scripts fully wrapped as step definitions at this stage

### Phase 4: Application Allow-listing — fapolicyd (Weeks 23–30)
- Higher complexity: fapolicyd rules require VM-based execution environments
- QEMU/KVM test images with fapolicyd in enforcing mode
- Scenarios test: specific binaries/scripts allowed/denied, trust database state

### Phase 5: GUI Layer & Cross-Cutting (Weeks 31–38)
- GUI application policies, screensaver lock, USB restriction enforcement
- Workstation profiles (physical vs virtual) as `Background:` context in each feature file
- Cross-domain scenarios: "Given the workstation is a virtual workstation with developer role, When..."

### Phase 6: AI Agent Integration (Weeks 20–ongoing, parallel)
- Start in Phase 3 after Gherkin patterns are stable
- **Scenario drafting:** AI agent receives meeting notes/email thread → produces draft `.feature` file → human review in Three Amigos session
- **Step suggestion:** AI agent reads `.feature` file → suggests step definition implementation
- **Conflict detection:** AI agent compares new user story against existing scenarios → flags contradictions before Three Amigos session
- **Gherkin as AI contract (B1 from analysis):** AI-generated configurations (sudoers fragments, PAM snippets) must pass all existing Gherkin scenarios before integration — "never trust, always verify" applied to AI output

---

## Critical Success Factors

1. **Security division must author, not just consume.** If they only receive Gherkin reports, it's just another Confluence page. They must write or co-write scenarios to develop ownership. Start with pre-written drafts for them to edit.
2. **Step definitions must test real state, not mocks.** Steps call `sudo -l`, read `/etc/sudoers.d/`, run actual commands. This is integration testing of the OS, not unit testing of configs.
3. **CI gate is the enforcement mechanism.** Without blocking image delivery on failing scenarios, Gherkin is documentation. With it, Gherkin is policy.
4. **One domain at a time.** Do not write Gherkin for all domains simultaneously. Complete Phase 1 before Phase 2.

---

## Tooling Stack

| Layer | Tool | Rationale |
|-------|------|-----------|
| BDD framework | `pytest-bdd` | Aligns with existing `uv run pytest` patterns |
| OS state testing | `testinfra` (optional) or raw `subprocess` | Direct OS state verification |
| Test environment | QEMU/KVM image snapshot | Real OS, not Docker — needed for PAM/sudo/fapolicyd |
| CI runner | Existing GitHub Actions / GitLab CI | Wire to existing pipeline |
| AI scenario drafting | Claude / local LLM (pre-mature stage) | Meeting notes → draft `.feature` files |

---

## Artifacts Created

All artifacts live in `misc/gherkin_pilot_debian/` (reference implementation for the Debian fork project):

- `misc/gherkin_pilot_debian/ROADMAP.md` — full learning guide with step-by-step adoption instructions
- `misc/gherkin_pilot_debian/security/features/sudo.feature` — Phase 1 pilot feature file (executable specification)
- `misc/gherkin_pilot_debian/security/features/step_definitions/test_sudo.py` — pytest-bdd step definitions
- `misc/gherkin_pilot_debian/security/features/step_definitions/conftest.py` — shared pytest fixtures

---

## Verification (end-to-end test of the roadmap artifact)

1. After Phase 1: `uv run pytest security/features/sudo.feature -v` runs against a test image and all scenarios pass
2. Manually violate a sudoers rule in the test image → corresponding scenario fails in CI
3. Security division reads `security/features/sudo.feature` and confirms it matches their policy intent
4. A new user story (from email) is translated into a scenario → Three Amigos session confirms → implemented → CI green
