★ Insight ─────────────────────────────────────
Structured commit bodies as a knowledge graph: The - Verb: target — why/impact format from ADR-26025 turns each commit into a queryable knowledge record. Future agents can grep commits for "Restored:" to find reverted decisions, "Replaced:" for architectural migrations, or "Removed:" for DRY cleanups. This is significantly more useful than prose commit messages for both humans doing retrospectives and AI agents doing codebase archaeology.

Structural coupling as a gate: In meta-prompts, sibling objects in a sequence are weakly ordered — LLMs can skip ahead. But phases within a single object are strongly ordered — the LLM must process phase 1 to encounter phase 2. This is why embedding file generation inside guidance_and_generation is more robust than having it as a separate file_generation_protocol.


★ Insight ─────────────────────────────────────
Pre-commit generates hook scripts with a hardcoded INSTALL_PYTHON path at pre-commit install time. When a repo directory is moved/renamed, these paths break silently — the hook only fails at commit time. The fix is to re-run pre-commit install to regenerate the hooks with the correct path.



In traditional software, "defense in depth" (redundant safety checks) is good engineering —
each layer catches what others miss. But in prompt engineering for LLMs, redundant instructions have a cost: they consume attention budget and can push the LLM from "execute mode" into "analyze mode." The analog in traditional engineering would be if adding too many safety interlocks to a machine made the operator unable to actually use it. The sweet spot is: fix functional gaps (missing placeholders), don't add redundant markers for things the compiler already knows.



From v0.30 postmortem:
- "Predictability comes from constraints, not instructions."
- "Instructions don't scale. Each additional instruction increases the probability of failure somewhere else."
- "Self-validation is theater." — LLMs will say "I have verified X" without actually verifying X.
- v0.31.0 separated roles into separate files, minimized output, made operations append-only

The real insight from the postmortem is that the template itself should be the constraint—the LLM modifies a template rather than generating freely. In the old monolith, the template and output were the same file, so the LLM's modifications were inherently constrained by the structure it was given.

Looking back at the postmortems, the core problem isn't the architecture—it's that asking the LLM to generate a 230-line file is inherently risky. Every token is a chance for error, and full regeneration of that mentor template is exactly the kind of design smell the postmortems flagged. Even if the LLM is "copying" the template, it's still outputting 233 lines of tokens, which multiplies the failure surface.





is it a good idea to keep this system prompt in json? I have chosen this format because it can be easily validated using jq or Python, but it contains too much service tokens that compete for attention as like as the real tokens

● That's a really important question, and it ties directly into ADR-26003 (instruction budget). Let me give you an honest analysis.

The Two Files Have Different Audiences

mentor_generator.json (meta-prompt) — read once by the compiler AI during generation. JSON is justified:
- Needs structural validation (jq, Python)
- Development artifact you maintain
- Precise field paths referenced by file_generation.steps ("Copy the ENTIRE object at templates.mentor_system_prompt")
- Compiler needs unambiguous structure to do placeholder substitution

mentor_system_prompt (generated output) — read by the mentor AI every session. This is where JSON hurts:

"patience_with_attempts": {
"rule": "Give the student two attempts to answer before simplifying",
"on_first_miss": "Guide toward understanding with a hint or different angle - don't give the answer",
"on_second_miss": "Simplify the explanation and try a different approach - never skip the concept"
}
vs.
### Patience with Attempts
- **Rule**: Give the student two attempts to answer before simplifying
- **On first miss**: Guide toward understanding with a hint or different angle - don't give the answer
- **On second miss**: Simplify the explanation and try a different approach - never skip the concept

The JSON version carries {}, "", :, , on every line — roughly 20-30% of the tokens are structural noise. For a ~300-line file,
that's 60-90 lines worth of tokens that do nothing but mark structure that ## headings and - bullets convey just as well.

The Deeper Problem

LLMs are trained heavily on Markdown. When they read Markdown, they parse it as instructions naturally. When they read JSON,
there's a subtle mode-switch toward "this is data to analyze" rather than "these are instructions to follow." This is exactly the
drift problem you documented in the v0.40.0 postmortem — and JSON formatting amplifies it.

Your own _template_notes.format already says: "JSON shown here, but content can be converted to YAML, Markdown, or plain text as
needed." The generated output was never required to be JSON.

Recommendation

┌───────────────────────────────────┬──────────────┬──────────────────────────────────────────────────────────────────────────┐
│               File                │    Format    │                                   Why                                    │
├───────────────────────────────────┼──────────────┼──────────────────────────────────────────────────────────────────────────┤
│ mentor_generator.json             │ JSON         │ Dev artifact, needs validation, compiler reads it                        │
├───────────────────────────────────┼──────────────┼──────────────────────────────────────────────────────────────────────────┤
│ mentor_system_prompt (generated)  │ Markdown     │ Mentor reads it every session, minimal noise, natural instruction format │
├───────────────────────────────────┼──────────────┼──────────────────────────────────────────────────────────────────────────┤
│ Session records in course_history │ JSON or YAML │ Structured data the mentor scans for specific fields                     │
└───────────────────────────────────┴──────────────┴──────────────────────────────────────────────────────────────────────────┘

The question is: do you want to tackle this now as part of v0.41.0, or ship v0.41.0 with the single-file merge (which is already a
big change) and convert format in v0.42.0?

★ Insight ─────────────────────────────────────
This is a case where format is architecture. The same content in JSON vs Markdown changes how an LLM processes it — not just
aesthetically, but behaviorally. JSON triggers "parse this data" mode; Markdown triggers "follow these instructions" mode. For a
file whose purpose is to instruct, the format should match the intent.



The core insight is: predictability comes from constraints, not instructions.
Instead of complex rules telling the mentor what to save, we give it an exact template to fill. No decisions = no confusion.


if the docs/ were in RAG, would it be better for your research work? or plain files in context are better?
this is for my future note

● Now I have all the data I need. Let me first answer your question about RAG, then write the comprehensive research document.

On RAG vs Plain Files

For this specific research task, plain files in context are significantly better. Here's why:

1. Post-mortems are narrative chains — they cross-reference each other ("validates Principle 3 from v0.30 postmortem"). RAG would
fragment these chains into disconnected chunks, losing the validated knowledge thread.
2. The docs are small enough (~20 pages total) — they fit comfortably in context. RAG adds latency and retrieval noise for no
benefit.
3. Cross-document reasoning is critical — I need to map Gemini's self-diagnosis against Qwen's behavior against ADR principles
simultaneously. RAG retrieves per-query, not per-reasoning-chain.
4. RAG would miss "negative evidence" — knowing that a post-mortem does NOT mention a problem is informative. RAG can't surface
absence.

When RAG would help: if you had 50+ ADRs, 20+ post-mortems, and 100+ test results. At that scale, retrieval beats full context.
Your current scale is ideal for direct context.






but do you think it is reasonable to add comments for future agents so the code becomes the doc?
⎿  Found 5 new diagnostic issues in 1 file (ctrl+o to expand)

● Good question. Looking at the existing patterns in this repo, there's already a solid convention:

- Test class docstrings describe the contract being tested (e.g., """Contract: extract_text(html_string) → plain text with tags
stripped.""")
- Module docstrings describe usage and exit codes
- Function docstrings describe args/returns

That's already agent-friendly documentation — future agents (and humans) can read the test file and immediately understand the
behavioral contracts. The tests I just wrote follow this pattern.

What I'd avoid is adding inline comments that explain what the code does (agents can read code). What's genuinely useful is the why
— design decisions, non-obvious constraints, and contract boundaries.

For this specific script, I think the existing pattern is sufficient. The test class docstrings like """Contract: is_mhtml(content)
→ True if content is MHTML multipart format.""" tell an agent exactly what to implement. The CLAUDE.md already documents the
higher-level conventions.


top-down structure: config → main → validation → discovery → helpers

★ Insight ─────────────────────────────────────
The pre-commit config follows a consistent pattern: validation hooks first (grouped together), then ---TESTS of HOOK SCRIPTS---
section. The CI workflow uses tj-actions/changed-files with files_yaml for selective triggering — logic group for script/test
changes (runs tests), docs group for content changes (runs the tool).

