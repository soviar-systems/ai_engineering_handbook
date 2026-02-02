---
id: YY001
title: "Short Description"  # Always quote titles (may contain colons)
date: YYYY-MM-DD
status: proposed  # Valid values defined in adr_config.yaml
superseded_by: null
tags: [architecture]  # Valid tags defined in adr_config.yaml
---

# ADR-{{ id }}: {{ title }}

## Date
{{ date }}

## Status

{{ status }}
{% if status == "superseded" %}Superseded: {{ superseded_by }}{% endif %}

## Context
Describe the problem or situation that necessitates a decision. 
Specify constraints, business priorities, and technical or team-specific factors. 
Provide the necessary background so that the rationale behind the decision is clear.

## Decision
State the chosen decision clearly and unambiguously. 
Use affirmative language, for example: "PostgreSQL will be used as the primary database." 
Be concise and stay on point.
"We will implement..." (State the falsifiable action).

## Consequences

### Positive
- Benefit 1

### Negative / Risks
- Note potential drawbacks, risks, or costs associated with this decision. **Mitigation**: 
- Include any follow-up tasks or impacts on other decisions. **Mitigation**: 
- Risk 1. **Mitigation:** [Link to Issue/Ticket]

## Alternatives
Briefly describe other options that were considered and why they were rejected.
- **Option A:** Description. **Rejection Reason:** Empirically failed on [Metric].

## References
Links to supporting documents, discussions, patterns, or research that influenced the decision.
- [Source Title](URL)

## Participants

List of personnel who participated in the decision.

1. Name1 
2. ...
