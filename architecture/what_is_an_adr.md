# What is an ADR?

---

title: "What is an ADR?"
author: rudakow.wadim@gmail.com
date: 2026-02-10
options:
  version: 1.1.0
  birth: 2026-01-06

---

**ADR (Architecture Decision Record) is a simple text document capturing a key architectural decision made within a project.** An ADR describes:

* How and why the decision was made,
* Which alternatives were considered,
* And what consequences this choice entails for the project.

ADR helps to:

* Preserve the team's "collective memory" (the entire history of decisions remains in the repository, even if members change),
* Quickly onboard new developers through transparency of decisions,
* Mitigate risks — recurring questions are resolved once and documented,
* Maintain architectural consistency as the project evolves.

Each ADR is a separate file dedicated to one significant architectural topic (e.g., choice of database, integration pattern, framework, etc.).

## Creating an ADR

All ADRs live in `architecture/adr/` as a flat directory — files are never moved to an archive folder ({term}`ADR-26016`).

To create a new ADR:

1. Copy the [ADR template](/architecture/adr/adr_template.md).
2. Follow the structure, required fields, valid statuses, and tags defined in [`adr_config.yaml`](/architecture/adr/adr_config.yaml) — this file is the Single Source of Truth for all ADR validation rules.
3. The `check_adr.py` script validates ADRs against the config automatically.

## The RFC→ADR Workflow

In this project, `proposed` ADRs serve as RFCs (Requests for Comments). There is no separate RFC document type — the ADR itself is the living design document that collects discourse before promotion. See {term}`ADR-26025` for the full specification.

**Key points:**

* **RFC = Proposed ADR.** Draft a new ADR with `status: proposed`. Iterate on `## Alternatives` and `## Context` as analysis progresses.
* **Promotion gate** (proposed → accepted). The `check_adr.py` script enforces criteria that must be met before an ADR can transition to `accepted` — see {term}`ADR-26025` for the full list.
* **AI consultation records.** Raw Gemini/Claude transcripts are working files — not committed to the repo. All analytical value is absorbed into the ADR's `## Alternatives` section (Fat ADR pattern).
* **Stale proposals.** ADRs remaining `proposed` >90 days without updates trigger a CI warning.

## For Further Study

* **Book:** "Documenting Software Architectures: Views and Beyond" — Clements et al. Provides a systematic approach to architectural documentation and decision rationale.
* **Documentation:** Michael Nygard's [adr.github.io](https://adr.github.io/). Describes the classic ADR format — recognized as an industry standard.
