# What is an ADR?

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

Maintaining and approving ADRs is often the responsibility of Tech Leads or Senior Developers.

# Organizational Approach

* **Allocate a dedicated folder** (`docs/adr/` or `architecture/decisions/`) in the repository to store all ADR files.
* **Use a template**: Create all records using a single structured template for transparency and ease of searching.
* **One architectural decision per ADR**: If a decision changes, create a new ADR and mark the old one as obsolete (`Superseded`, `Replaced`).
* **Immutability**: Once created, an ADR is not edited — changes are only made via a new ADR.
* **Decision Status**: Mark all files with the current status: `Proposed`, `Accepted`, `Rejected`, `Deprecated`, `Superseded`.
* **Discussion via Pull Request**: Format all ADRs as pull requests; they should be discussed and approved by colleagues similarly to code.
* **Revision**: Review ADRs for relevance at least once a quarter — if a decision has changed, create a new ADR.
* **Responsibility**: The Tech Lead or an experienced developer is responsible for drafting the ADR, while the team participates in preparing and verifying the content.

## ADR Template in Russian

Use the file `./0001-template.md` as a template.

## Best Practices for Using ADR in Git

* Store ADRs as Markdown files in a separate folder — for example, `docs/adr/` or `architecture/decisions/` within the repository.
* The filename should start with a number (with leading zeros) and contain a brief description of the decision, e.g., `0001-use-postgresql.md`.
* Treat an ADR as an immutable historical document; if a decision changes, create a new ADR, referencing the previous one as "superseded."
* Leverage Git capabilities: discuss, review, and approve ADRs via pull requests, just like regular code.
* Indicate the decision status (Proposed, Accepted, Deprecated, Superseded) to track its lifecycle stage.
* Each ADR should contain only one architectural decision — this simplifies understanding and searching.
* Regularly (e.g., once a month) review ADRs to check the relevance of assumptions and document new decisions in separate files.

# For Further Study

* **Book:** “Documenting Software Architectures: Views and Beyond” — Clements et al.
*Why:* Provides a systematic approach to architectural documentation and decision rationale.
* **Documentation:** Michael Nygard's [adr.github.io](https://adr.github.io/)
*Why:* Describes the classic ADR format — recognized as an industry standard.
