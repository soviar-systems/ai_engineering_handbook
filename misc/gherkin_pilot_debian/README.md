# Gherkin/BDD Pilot — Corporate Debian Fork

Reference implementation and learning materials for adopting Gherkin/BDD
as the executable requirements layer in a corporate Debian fork with strict
security requirements.

## Contents

```
misc/gherkin_pilot_debian/
├── README.md                               ← this file
├── ROADMAP.md                              ← full learning guide (start here)
└── security/features/
    ├── sudo.feature                        ← Phase 1 pilot: executable specification
    └── step_definitions/
        ├── conftest.py                     ← shared pytest fixtures
        └── test_sudo.py                    ← pytest-bdd step definitions
```

The concise roadmap is archived at:
`misc/plans/implemented/plan_20260218_gherkin-adoption-debian-fork.md`

## How to Use

**Start with `ROADMAP.md`** — a step-by-step learning guide organized as a
progression through all adoption phases. Each section explains *why* before
*how*, with concrete facilitation instructions and pitfall warnings.

| Part | Content |
|------|---------|
| Part 0 | Mental model: why passive docs fail, what BDD fixes structurally |
| Part 1 | Phase 0 foundation: glossary workshop, Three Amigos roles, tooling |
| Part 2 | Phase 1 sudo pilot: every sub-step with reasoning and examples |
| Part 3 | Phase 2 PAM & Identity: applying the pattern to the next domain |
| Part 4 | Phase 3 Package Policy: build-time gate integration |
| Part 5 | Phase 4 fapolicyd: VM-based execution environment testing |
| Part 6 | Phase 5 GUI layer and cross-domain scenarios |
| Part 7 | Phase 6 AI integration: meeting notes → draft `.feature` files |
| Part 8 | Critical success factors and failure mode prevention |
| Part 9 | Quick reference: keywords, decorators, CI commands, phase checklist |

## Using the Reference Implementation

`sudo.feature` and `test_sudo.py` are copy-ready artifacts for the Debian fork
repository. Copy the `security/` directory tree into that repo and install
the dependencies:

```bash
uv add --dev pytest pytest-bdd
```

Run the scenarios against a QEMU/KVM test image:

```bash
# All sudo scenarios
SUDO_TEST_USER=devuser uv run pytest security/features/step_definitions/test_sudo.py -v

# Specific scenario
uv run pytest security/features/step_definitions/test_sudo.py -v -k "approved package"

# With JUnit XML for CI
uv run pytest security/features/step_definitions/ --junitxml=reports/security.xml
```

The import errors shown by static analysis tools (Pyright, pylance) are expected
in this knowledge-base repo — `pytest` and `pytest-bdd` install in the target
Debian fork repo, not here.

## Key Concept

Gherkin does not generate configurations — it specifies and verifies behavior.

```
user story → Three Amigos session → .feature file → step definitions → CI gate
```

The `.feature` file is the **Definition of Done** for a security requirement.
When a scenario fails, the image build is blocked. When it passes, the
requirement is demonstrably met — not claimed, not documented, *verified*.
