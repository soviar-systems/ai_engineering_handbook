# Gherkin/BDD Adoption in Corporate Debian Fork Development
## A Step-by-Step Learning Guide

**Audience:** System architects, security engineers, and OS developers adopting BDD
for infrastructure security testing for the first time.

**What you will learn:**
- Why the current requirements lifecycle fails and how BDD fixes it structurally
- How to think about Gherkin for OS-level (not application-level) testing
- How to facilitate each phase: from the first workshop to the CI gate
- How to write feature files and step definitions that test real OS state
- How to grow the practice across domains without losing momentum

---

## Part 0: The Problem You Are Actually Solving

Before writing a single `.feature` file, you need to understand what is broken
and why BDD fixes it — not just in theory, but in your specific context.

### The current lifecycle (and where it breaks)

```
meeting → email thread → Confluence doc → Jira ticket → implementation → ???
```

Each arrow is a translation step. Each translation step is an information loss
opportunity. The security division writes a policy requirement in Confluence. A
developer reads it weeks later and interprets it differently. The difference never
surfaces until an audit — or a breach.

The deeper problem: **these artifacts are passive**. A Jira ticket can be closed
as "done" even if the implementation does not match the requirement. Confluence
pages go stale. There is no mechanism that enforces correspondence between the
requirement and the running system.

### What BDD adds

BDD does not fix the meeting → email → doc chain. It adds one artifact at the
end that is **active**: the `.feature` file. Active means:

- It is executed by a machine against the real system.
- If it passes, the requirement is met. If it fails, it is not — and the image
  build is blocked.
- It cannot go stale: a stale test fails, which surfaces the gap.

The `.feature` file becomes the **Definition of Done** for a security requirement.
Not a checkbox. An executable assertion.

### Why Gherkin specifically (not pytest alone)

You could write the same assertions directly in pytest. The reason for Gherkin
is **stakeholder readability**. The security division does not read Python. They
do read:

```gherkin
Scenario: Developer cannot install unapproved packages
  Given the user is in the 'developers' group
  When the user runs "sudo apt install netcat-traditional"
  Then the command is denied with exit code 1
```

This is a security policy statement in plain language. The security division can
read it, argue with it, sign off on it. That sign-off has meaning because they
understand exactly what they are signing.

**Key mental model:** Gherkin is the contract. pytest-bdd is the enforcement
mechanism that executes the contract. Never confuse the two.

---

## Part 1: Phase 0 — Foundation (Weeks 1–2)

The goal of Phase 0 is **not** to write code. It is to create the shared
language and role clarity that makes the rest of the work coherent. Skipping
this phase is the most common cause of BDD adoption failure.

### 1.1 The Ubiquitous Language Session

**What it is:** A 2-hour workshop with security division + system architect.
No developers yet — the language must be settled before implementation begins.

**Goal:** Every term used in feature files must have one agreed definition.
Ambiguity in language = bugs in tests = useless tests.

**Terms to define (minimum for sudo domain):**

| Term | Questions to resolve |
|------|----------------------|
| `user role` | Is this a Unix group? An LDAP attribute? Both? |
| `privilege` | Specifically `sudo` rights, or broader (file ACLs, capabilities)? |
| `approved package` | Who owns the list? Where does it live? How is it updated? |
| `audit event` | What constitutes a logged action? Which log file? What fields are required? |
| `denied` | Exit code 1? Exit code 126? Both? Does stderr matter? |
| `workstation type` | Is `physical` vs `virtual` a runtime check or a configuration flag? |

**Output:** A one-page glossary. This glossary becomes the vocabulary of every
feature file. If a term is not in the glossary, it does not go in a feature file.

**Common mistake:** Skipping the glossary because "everyone knows what we mean."
They do not. The value surfaces in Week 4 when the developer writes a step
definition and discovers that "denied" means exit code 1 to the architect and
"no output to stdout" to the security division. Write the glossary.

### 1.2 Three Amigos Role Mapping

BDD defines three roles for a feature. Map your team to these roles explicitly:

```
Security Division    →  Product Owner
                        Authors acceptance criteria
                        Signs off on scenarios
                        Has veto power on the Definition of Done

System Architect     →  Business Analyst
                        Translates policy intent into concrete scenarios
                        Facilitates the Three Amigos session
                        Writes the first draft of feature files

OS Developer         →  Developer
                        Implements sudoers configuration
                        Writes step definitions that call real OS checks
                        Raises infeasibility concerns early
```

**Why these mappings matter:** The Product Owner (security division) must feel
ownership of the `.feature` file. If they feel it is "the developer's test," they
will not read it, will not sign it, and will continue to treat it as someone
else's artifact. The session facilitation in Phase 1 is designed to create this
ownership.

### 1.3 Tooling Setup

**Framework choice: `pytest-bdd` over `behave`**

The reason is operational: your project already uses `uv run pytest`. Adding
`pytest-bdd` means BDD tests use the same runner, same fixture system, same
CI command, same output format. There is no new mental model for the developer.

```bash
# In the Debian fork repository
uv add --dev pytest pytest-bdd
```

**Verify the install:**
```bash
uv run pytest --co -q security/features/
# Should list collected scenarios, not error
```

**Test environment requirement:** All step definitions run against a QEMU/KVM
image snapshot, never against production or a Docker container. The reason:
`sudo`, `PAM`, `fapolicyd`, and `auditd` have kernel-level dependencies that
Docker does not provide. Plan for a KVM snapshot in your CI pipeline before
Phase 1 begins.

### 1.4 Repository Structure

Create this in the Debian fork repository (not in this knowledge base):

```
security/
└── features/
    ├── sudo.feature              # Phase 1
    ├── pam.feature               # Phase 2
    ├── package_policy.feature    # Phase 3
    ├── fapolicyd.feature         # Phase 4
    └── step_definitions/
        ├── conftest.py           # shared fixtures
        ├── test_sudo.py
        ├── test_pam.py
        └── test_package_policy.py
```

One `.feature` file per security domain. One step definitions file per feature.
Do not mix domains — it becomes impossible to run a single domain in isolation.

---

## Part 2: Phase 1 — Pilot: Sudo Privilege Division (Weeks 3–8)

This is the phase where BDD theory becomes practice. Work through every sub-step.
The patterns you establish here are the template for all later phases.

### 2.1 Why Sudo as the Pilot Domain

Three properties make sudo ideal:

1. **Visible tension.** Developer needs (elevated access) conflict directly with
   security requirements (least privilege). This tension makes the Three Amigos
   session productive — there is something real to negotiate.

2. **Immediate verifiability.** You can run `sudo -l -U username` right now and
   see exactly what permissions a user has. No infrastructure required.

3. **Single-file policy.** The entire sudo policy lives in `/etc/sudoers` and
   `/etc/sudoers.d/`. One domain, one policy file, one feature file.

### 2.2 Step 1: Collecting User Stories (Week 3)

**Do this before the Three Amigos session**, not during. The session is for
negotiating requirements — not for discovering what users need.

**How to collect:**
- Send a one-paragraph email to developers and sysadmins: "We are formalizing
  sudo policy. Tell us: what do you need elevated access for? Format: 'As a
  [your role], I need to [action] so that [outcome].'"
- Give them 3 business days. Follow up once.
- Do not filter or edit the stories — collect all of them.

**Example stories you will receive:**
```
"As a developer, I need to install Python packages from apt
 so that I can set up my project environment."

"As a developer, I need to restart my test service
 so that I can validate configuration changes."

"As a sysadmin, I need to reload the firewall rules
 so that network policy changes take effect without rebooting."

"As a sysadmin, I need a root shell for emergency situations
 so that I can fix broken systems."

"As a developer, I need to run docker commands
 so that I can build container images locally."
```

**What you learn from the raw list:**
- Which roles need which categories of elevated access
- Where the highest-risk requests are (root shell, docker group)
- Where you will need multiple scenarios per story (the root shell story will
  produce a "denied" scenario with an alternative procedure)

### 2.3 Step 2: The Three Amigos Session (Week 3)

**Duration:** 90 minutes for the sudo domain.

**Participants:** Security division rep (1–2), system architect (you), OS developer.

**Format:** Walk through each user story one at a time. For each story:

1. **Developer presents the story** (30 seconds). Just reads it aloud.
2. **Security division engineers the requirement** (5–10 minutes). The question
   is: "Under what conditions can we permit this, and what controls are required?"
   This is the real work. Examples:
   - "Developers can install from apt only if the package is on our approved list."
   - "The action must be logged with full user identity and timestamp."
   - "No developer can install a package that provides a network listener."
3. **Architect writes the scenario(s) in real time.** Share screen. The security
   division watches the Gherkin appear and corrects it immediately. This is the
   fastest feedback loop possible.
4. **Developer flags infeasibility** (if any). "We can't check the approved list
   at sudo time — here's why." This triggers a constraint conversation.
5. **Repeat for the denied path.** Every permitted story has at least one denied
   scenario. Ask: "What should happen if the user tries this without being in the
   right group?" Write that scenario too.

**What to do with the root shell story:**

The security division will deny this. The response is not just "denied" — it is
a conversation about the alternative procedure (break-glass, out-of-band access).
Write two artifacts:
- A `Scenario: No role can gain an unrestricted root shell` (the denied path)
- A note in the `.feature` file comment block linking to the break-glass procedure

**Output:** A `.feature` file that all three stakeholders have seen built
sentence by sentence. They do not need to understand pytest-bdd. They need to
understand Gherkin — and they watched it being written.

### 2.4 Step 3: Reading the Feature File You Now Have

After the session, you have `security/features/sudo.feature`. Read it as the
security division would read it:

```gherkin
Feature: Sudo Privilege Division
  As a security division, we need to enforce the principle of least privilege
  for all workstation user roles. Elevated access must be scoped, audited,
  and individually granted.

  Background:
    Given the workstation has a configured sudoers policy in /etc/sudoers.d/
    And the audit daemon is running and writes to /var/log/auth.log
```

The `Background:` block runs before every scenario. It is the precondition that
must be true for any scenario to be meaningful. If the audit daemon is not
running, a "logged in auth.log" assertion is vacuously false. The Background
makes this explicit.

```gherkin
  Scenario: Developer installs an approved package via apt
    Given the user is a member of the 'developers' group
    And 'python3-dev' is in the approved package list
    When the user runs "sudo apt install python3-dev"
    Then the command exits with code 0
    And /var/log/auth.log contains an entry with the user's identity and the command
```

Note the structure:
- `Given` — preconditions (state of the world before the action)
- `When` — the action (one action per scenario)
- `Then` — the expected outcomes (can be multiple)

This is not a style rule — it maps directly to how step definitions are
organized. Each keyword binds to a different phase of test execution.

### 2.5 Step 4: Writing Step Definitions (Weeks 4–5)

Step definitions are Python functions that implement each `Given/When/Then` step.
The binding is by string pattern, not by import.

**The cardinal rule: call real OS state.**

```python
# WRONG — mocks sudo behavior, proves nothing about the real system
@when('the user runs "sudo apt install python3-dev"')
def run_apt(context):
    context["result"] = Mock(returncode=0)

# RIGHT — calls the real command on the real (test image) OS
@when(parsers.parse('the user runs "{command}"'))
def run_command_as_user(command: str, context: dict) -> subprocess.CompletedProcess:
    test_user = context.get("user", _test_user())
    result = subprocess.run(
        ["su", "-c", command, test_user],
        capture_output=True, text=True
    )
    context["result"] = result
    return result
```

The test user runs the command. The test runner (CI, with appropriate privilege)
executes `su -c` to switch to the test user context. This is not a simulation —
the command hits the real sudo policy on the real test image.

**Step reuse across scenarios:**

The step `the user runs "{command}"` is parametrized — it handles any command
string. This is a `Scenario Outline` pattern at the step level. Write steps
to be reusable from the beginning:

```python
# This one step handles ALL "When the user runs X" steps in any scenario
@when(parsers.parse('the user runs "{command}"'), target_fixture="command_result")
def run_command_as_user(command: str, context: dict):
    ...
```

**Wrapping the security division's existing checks:**

The security division already has assessment scripts that check correctness.
Treat these as the oracle:

```python
# If they have a script that checks visudo syntax:
@when("visudo -c is run against /etc/sudoers and /etc/sudoers.d/")
def run_visudo_check(context: dict):
    result = subprocess.run(
        ["visudo", "-c", "-f", "/etc/sudoers"],
        capture_output=True, text=True
    )
    context["result"] = result
```

The step definition wraps their existing check. The scenario gives it a
human-readable description. The CI gate gives it enforcement. Nothing in the
security division's existing tooling is thrown away — it is promoted to the
requirements layer.

**Running during development:**

```bash
# Run all sudo scenarios against the test image
SUDO_TEST_USER=devuser uv run pytest security/features/step_definitions/test_sudo.py -v

# Run a specific scenario by name
uv run pytest security/features/step_definitions/test_sudo.py -v \
  -k "approved package"

# Run with full output on failure
uv run pytest security/features/step_definitions/test_sudo.py -v --tb=long
```

**Expected first run:** Most scenarios will fail. This is correct. The test image
does not yet have the sudoers configuration that implements the policy. The
failures are the specification. The OS developer now implements until all
scenarios pass.

### 2.6 Step 5: The CI Gate (Week 6)

This is the most important step. Without it, BDD is documentation.

**Add to your CI pipeline (GitLab CI example):**

```yaml
# .gitlab-ci.yml
verify_sudo_policy:
  stage: security-verify
  image: your-kvm-runner-image
  script:
    - uv run pytest security/features/step_definitions/test_sudo.py
        --tb=short --junitxml=reports/sudo-policy.xml
  artifacts:
    reports:
      junit: reports/sudo-policy.xml
  rules:
    - if: '$CI_PIPELINE_SOURCE == "push"'
```

**Gate image delivery:**

```yaml
build_image:
  stage: build
  needs:
    - job: verify_sudo_policy    # image build waits for policy verification
  script:
    - make build-image
```

**The enforcement logic:** If `verify_sudo_policy` fails, `build_image` does not
run. The image is not delivered. A failing scenario means "this image does not
meet the security requirement." This is not a soft warning — it blocks delivery.

**What failing looks like in CI:**

```
FAILED security/features/step_definitions/test_sudo.py::test_developer_blocked_from_unapproved_package
  AssertionError: Expected exit code 1, got 0.
  Package 'netcat-traditional' was installed despite the policy.
```

This failure message tells the developer exactly what is wrong: the sudoers
policy does not block the unapproved package. The fix is in the sudoers
configuration, not in the test.

### 2.7 Step 6: Security Division Review and Sign-Off (Weeks 7–8)

Schedule a 45-minute review. Bring:

1. The `.feature` file open on screen — this is their policy document.
2. A passing CI run report — this is the acceptance report.
3. A deliberately-broken test image run — show what failure looks like.

**The conversation you want to have:**
- "Does this scenario match what you intended to permit?"
- "Is there a case we missed?" (There always is — that becomes a new scenario.)
- "If this scenario fails in CI, image delivery stops. Is that the right
  enforcement level?"

**The sign-off:** Security division formally approves the `.feature` file as the
authoritative policy document for the sudo domain. This approval is documented
in the commit message or PR that merges the feature file to the main branch.

**Why this matters:** From this point on, the `.feature` file is the source of
truth. Not the Confluence page (which may be updated or ignored). Not the email
thread. The file that CI enforces.

---

## Part 3: Phase 2 — PAM & Identity (Weeks 9–16)

Phase 2 applies the same process to a new domain. The process is identical —
the value of Phase 1 is that you do not need to invent it again.

### 3.1 Domains in this phase

| Domain | What it covers | Key OS commands to wrap |
|--------|----------------|------------------------|
| PAM password policy | Minimum length, complexity, expiry, lockout after N failures | `pam_tally2`, `/etc/pam.d/`, `chage` |
| SSSD integration | LDAP/AD user resolution, group membership, offline cache | `sssctl`, `id`, `getent passwd` |
| SSH access control | Allowed users, key-only auth, root login disabled | `sshd -T`, `/etc/ssh/sshd_config` |

### 3.2 Reusing Phase 1 patterns

The step `the user is a member of the '<group>' group` from `test_sudo.py`
is reusable in PAM and SSH scenarios. Extract shared steps to a
`step_definitions/common_steps.py` module:

```python
# step_definitions/common_steps.py
from pytest_bdd import given, parsers
import subprocess

@given(parsers.parse("the user is a member of the '{group}' group"))
def check_user_in_group(group: str, context: dict) -> str:
    test_user = context.get("user", _test_user())
    result = subprocess.run(["getent", "group", group], capture_output=True, text=True)
    members = result.stdout.strip().split(":")[-1].split(",") if result.returncode == 0 else []
    assert test_user in members
    context["user"] = test_user
    context["group"] = group
    return group
```

Import this in both `test_sudo.py` and `test_pam.py`. The Three Amigos session
for PAM will go faster because the security division already knows how to read
Gherkin — Phase 1 trained them.

### 3.3 Example PAM feature (draft)

```gherkin
Feature: PAM Password Policy
  The workstation enforces password security requirements for all local accounts
  as defined in the security division's password policy (ref: SEC-POL-003).

  Scenario: Password shorter than minimum length is rejected
    Given the PAM password module is configured with minlen=12
    When a user attempts to set a password of length 8
    Then the password change is rejected
    And the user receives an error message referencing minimum length

  Scenario: Account is locked after 5 consecutive failed logins
    Given the PAM tally module is configured with deny=5
    When a user enters an incorrect password 5 times consecutively
    Then the account is locked
    And the lockout is recorded in /var/log/auth.log

  Scenario: Locked account is not unlocked by time alone
    Given the account has been locked due to failed login attempts
    When 30 minutes elapse
    Then the account remains locked
    And an administrator action is required to unlock it
```

Note the `ref: SEC-POL-003` in the Feature description. Cross-reference your
existing policy documents. The Gherkin file becomes the *executable* version
of the policy document, not a replacement for it.

---

## Part 4: Phase 3 — Package Policy (Weeks 17–22)

Phase 3 shifts the gate from post-build verification to build-time integration.

### 4.1 The new capability: build-time gate

In Phases 1–2, Gherkin ran *after* the image was built. In Phase 3, Gherkin
gates run *during* the build pipeline, before the image is committed.

```
build pipeline:
  1. Assemble package list
  2. [NEW] verify_package_policy (Gherkin gate)  ← blocks if policy violated
  3. Install packages into image
  4. Run post-build verification (sudo, PAM gates from Phase 1–2)
  5. Deliver image
```

### 4.2 Package policy scenarios

```gherkin
Feature: Package Policy
  Only approved packages from trusted repositories are installed.
  No package that provides a prohibited capability may be present.

  Scenario: All installed packages are on the approved list
    Given the image package manifest is generated
    When each installed package is checked against the approved list
    Then every package in the manifest appears in the approved list

  Scenario: No package providing a network backdoor is installed
    Given the prohibited capabilities list includes "network-backdoor"
    When the image is scanned for packages with this capability
    Then no package with this capability is found installed

  Scenario: All packages come from the official repository mirror
    Given the repository configuration points to [INTERNAL_MIRROR]
    When the package source for each installed package is checked
    Then every package is sourced from [INTERNAL_MIRROR] only

  Scenario: Version-pinned packages are at the correct version
    Given the version pin file specifies openssl=3.0.11
    When the installed openssl version is checked
    Then the installed version is exactly 3.0.11
```

### 4.3 Wrapping the security division's assessment scripts (fully)

By Phase 3, the security division's existing assessment scripts should be
fully wrapped as step definitions. The pattern:

```python
# Their existing script: /opt/security/check_packages.sh
# Returns 0 if policy compliant, 1 with details if not

@when("each installed package is checked against the approved list")
def run_package_policy_check(context: dict):
    result = subprocess.run(
        ["/opt/security/check_packages.sh", "--manifest", context["manifest_path"]],
        capture_output=True, text=True
    )
    context["result"] = result
    context["violations"] = result.stdout.splitlines() if result.returncode != 0 else []
```

Their script is the oracle. The step definition is the adapter. The Gherkin
scenario is the policy statement. The CI gate is the enforcement. Each layer
has a clear responsibility.

---

## Part 5: Phase 4 — fapolicyd (Weeks 23–30)

`fapolicyd` (file access policy daemon) is the most complex domain because it
requires the application to be *running* in enforcing mode during tests.

### 5.1 Why this is different

PAM and sudo tests check configuration files and command exit codes. fapolicyd
tests check whether a specific binary or script can *execute*. This requires:

- fapolicyd running in enforcing mode in the test image
- The binary under test to actually be invoked
- The trust database to reflect the policy

### 5.2 Test environment requirement

fapolicyd tests require a full QEMU/KVM snapshot with fapolicyd in enforcing
mode. Add a separate CI job with a fapolicyd-enabled image:

```yaml
verify_fapolicyd_policy:
  stage: security-verify
  image: your-fapolicyd-kvm-runner
  script:
    - uv run pytest security/features/step_definitions/test_fapolicyd.py -v
```

### 5.3 Example scenarios

```gherkin
Feature: Application Allow-listing (fapolicyd)
  Only binaries in the trust database may execute on workstations.
  Unsigned or untrusted executables are denied at the kernel level.

  Background:
    Given fapolicyd is running in enforcing mode
    And the fapolicyd trust database is populated from the approved package list

  Scenario: An approved binary executes successfully
    When the user runs "/usr/bin/python3 --version"
    Then the command exits with code 0

  Scenario: An unsigned script in /tmp is denied execution
    Given an unsigned shell script exists at /tmp/test_script.sh
    When the user attempts to execute /tmp/test_script.sh
    Then execution is denied
    And fapolicyd logs the denial with the file path and user identity

  Scenario: A binary not in the trust database is denied
    Given a binary exists at /usr/local/bin/custom_tool
    And /usr/local/bin/custom_tool is not in the fapolicyd trust database
    When the user attempts to run /usr/local/bin/custom_tool
    Then execution is denied with a permission error
```

---

## Part 6: Phase 5 — GUI Layer & Cross-Cutting (Weeks 31–38)

### 6.1 Workstation profiles as Background context

Physical and virtual workstations have different security profiles. Use the
`Background:` block to parameterize at the Feature level:

```gherkin
Feature: Screensaver Lock Policy — Physical Workstations
  Background:
    Given the workstation is a physical workstation
    And the workstation profile is 'employee-desktop'

  Scenario: Screen locks after 5 minutes of inactivity
    Given no user input has occurred for 5 minutes
    When the screensaver timeout is checked
    Then the screen lock is active
```

```gherkin
Feature: Screensaver Lock Policy — Virtual Workstations
  Background:
    Given the workstation is a virtual workstation
    And the workstation profile is 'developer-vm'

  Scenario: Screen lock timeout is 15 minutes for virtual workstations
    ...
```

Two feature files, same step definitions, different Background. The step
`the workstation is a physical workstation` checks a configuration flag or
DMI data — it verifies the test is running in the right context.

### 6.2 Cross-domain scenarios

By Phase 5 you have step definitions for sudo, PAM, packages, and fapolicyd.
Cross-domain scenarios combine them:

```gherkin
Scenario: Developer on physical workstation cannot install unapproved tools
  Given the workstation is a physical workstation
  And the user is a member of the 'developers' group
  When the user runs "sudo apt install wireshark"
  Then the command exits with code 1
  And fapolicyd logs no execution attempt for wireshark binaries
```

This scenario touches sudo policy AND fapolicyd in one test. It is only
possible because both step definition sets exist and share the same context
fixture.

---

## Part 7: Phase 6 — AI Agent Integration (Weeks 20–ongoing)

Start Phase 6 in parallel with Phase 3, after Gherkin patterns are stable.

### 7.1 Meeting notes → draft feature file

The first AI use case: give the agent meeting notes or an email thread,
get back a draft `.feature` file for Three Amigos review.

**Input prompt pattern:**
```
You are a BDD analyst helping a security team adopt Gherkin.
Here are the notes from a requirements session about USB restriction policy:

[paste meeting notes]

Generate a draft Gherkin feature file using this vocabulary:
[paste glossary from Phase 0]

Constraints:
- One scenario per distinct requirement
- Include both permitted and denied paths
- Use the Background block for preconditions common to all scenarios
- Mark uncertain requirements with a # TODO comment
```

**Important:** The AI draft is input to the Three Amigos session, not a
replacement for it. The security division reviews and corrects the draft.
The value is that the session starts from a concrete artifact, not a blank page.

### 7.2 Gherkin as the AI contract

When using AI to generate configurations (sudoers fragments, PAM snippets,
fapolicyd rules), the Gherkin test suite becomes the verification gate:

```bash
# AI generates a sudoers fragment
# Before merging, run the full test suite against it:
uv run pytest security/features/step_definitions/ -v

# If tests pass: AI output meets the policy. Safe to merge.
# If tests fail: AI output violates the policy. Reject it.
```

This is "never trust, always verify" applied to AI-generated infrastructure.
The Gherkin scenarios are the policy oracle. Any artifact — human or AI — must
pass them.

### 7.3 Conflict detection

As the scenario library grows, ask the AI to compare new user stories against
existing scenarios before the Three Amigos session:

```
Here is our existing sudo.feature file: [paste file]

A user has requested: "As a developer, I need to run docker commands with sudo
so that I can build container images."

Does this user story conflict with any existing scenario? What new scenarios
would this require? What denied paths must we cover?
```

The AI identifies that `docker` group membership effectively grants root access
— which conflicts with "No role can gain an unrestricted root shell." This
surfaces the conflict before the Three Amigos session, making the session
a confirmation conversation rather than a discovery conversation.

---

## Part 8: Critical Success Factors (Detailed)

### 8.1 Security division authorship (not just consumption)

The most common failure mode: BDD becomes "the developer's test suite" and the
security division receives reports. Within three months, the `.feature` files
are out of date with policy — exactly the problem BDD was supposed to solve.

**Concrete actions to prevent this:**
- In the Three Amigos session, the architect types but the security division
  dictates. They say "the condition is X," you write `Given X`. Never write
  a scenario without their verbal confirmation of each step.
- The security division's formal sign-off goes in a PR comment. The PR is not
  merged without it.
- When policy changes, the security division opens the PR that updates the
  `.feature` file. They do not submit a ticket asking the developer to update it.

### 8.2 Step definitions must test real state

Mock-based BDD tests prove that the test passes, not that the system meets the
requirement.

```python
# This test will always pass and proves nothing:
@then("the command exits with code 1")
def assert_denied(context):
    assert context["result"].returncode == 1  # mocked result

# This test proves the actual sudo policy blocks the command:
@then("the command exits with code 1")
def assert_denied(context):
    result: subprocess.CompletedProcess = context["result"]
    assert result.returncode == 1, (
        f"Expected denial (exit 1), got {result.returncode}.\n"
        f"This means the sudoers policy permitted the command.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
```

The error message is the diagnostic. When a scenario fails, the developer
should know immediately *what policy rule is missing or wrong* — not just
that a test failed.

### 8.3 One domain at a time

Writing feature files for all domains simultaneously before any step
definitions exist creates a mountain of unverifiable specifications.
The CI gate has no teeth until step definitions exist and run.

The sequence is strict:
```
Phase 1 complete (step defs running, CI gate active) → start Phase 2
Phase 2 complete → start Phase 3
Phase 3 complete → start Phase 4 + Phase 6 in parallel
```

---

## Part 9: Quick Reference

### Gherkin keyword cheatsheet

| Keyword | Purpose | Example |
|---------|---------|---------|
| `Feature:` | Domain description + stakeholder context | `Feature: Sudo Privilege Division` |
| `Background:` | Preconditions shared by all scenarios in the file | `Given the audit daemon is running` |
| `Scenario:` | One concrete requirement (one action) | `Scenario: Developer installs approved package` |
| `Scenario Outline:` | Parametrized scenario with multiple data rows | `Scenario Outline: No role gains root shell` |
| `Examples:` | Data table for Scenario Outline | `\| role \| command \|` |
| `Given` | Precondition (state before the action) | `Given the user is in 'developers' group` |
| `When` | The action under test (one per scenario) | `When the user runs "sudo apt install X"` |
| `Then` | Expected outcome assertion | `Then the command exits with code 0` |
| `And` | Continuation of previous keyword | `And /var/log/auth.log contains an entry` |
| `#` | Comment (not executed, for humans) | `# User story: As a developer...` |

### pytest-bdd decorator cheatsheet

```python
from pytest_bdd import scenario, given, when, then, parsers

# Bind a test function to a scenario
@scenario("../sudo.feature", "Scenario name exactly as written")
def test_function_name(): pass

# Literal step match
@given("the audit daemon is running and writes to /var/log/auth.log")
def step_impl(context): ...

# Parametrized step match
@given(parsers.parse("the user is a member of the '{group}' group"))
def step_impl(group: str, context: dict): ...

# Step that produces a fixture value
@when(parsers.parse('the user runs "{command}"'), target_fixture="result")
def step_impl(command: str, context: dict) -> subprocess.CompletedProcess: ...
```

### CI commands

```bash
# Run all security feature tests
uv run pytest security/features/step_definitions/ -v

# Run a specific feature file's tests
uv run pytest security/features/step_definitions/test_sudo.py -v

# Run with test user override
SUDO_TEST_USER=devuser uv run pytest security/features/step_definitions/ -v

# Generate JUnit XML for CI reporting
uv run pytest security/features/step_definitions/ --junitxml=reports/security.xml

# Show collected scenarios without running
uv run pytest security/features/step_definitions/ --collect-only -q
```

### Phase checklist

- [ ] **Phase 0**: Glossary written → Role mapping agreed → Tooling installed → `security/features/` directory created
- [ ] **Phase 1**: User stories collected → Three Amigos session done → `sudo.feature` written → Step defs written → CI gate active → Security division sign-off received
- [ ] **Phase 2**: `pam.feature` + `test_pam.py` → CI gate extended → Sign-off received
- [ ] **Phase 3**: `package_policy.feature` → Build-time gate added → Assessment scripts wrapped → Sign-off received
- [ ] **Phase 4**: `fapolicyd.feature` → KVM runner with fapolicyd → Sign-off received
- [ ] **Phase 5**: GUI + cross-domain scenarios → Workstation profile Background blocks
- [ ] **Phase 6**: AI drafting workflow established → Conflict detection prompt tested → AI-generated configs gated by test suite

---

*This document is the learning companion to:*
- `security/features/sudo.feature` — the Phase 1 pilot feature file
- `security/features/step_definitions/test_sudo.py` — the Phase 1 step definitions
- `misc/plans/plan_20260218_gherkin-adoption-debian-fork.md` — the concise roadmap
