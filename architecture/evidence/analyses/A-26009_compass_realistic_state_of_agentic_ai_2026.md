---
id: A-26009
title: "Compass — The Realistic State of Agentic AI Architectures in Early 2026"
date: 2026-03-08
status: active
tags: [architecture, context_management, governance, security]
sources: []
produces: [ADR-26038, ADR-26034]
---

# A-26009: Compass — The Realistic State of Agentic AI Architectures in Early 2026

## Problem Statement

The agentic AI ecosystem has reached a paradox: the tooling has never been richer, but production success remains rare and concentrated in the simplest architectures. Only about 5% of enterprises surveyed have AI agents live in production[^cleanlab], and stack churn is extreme — respondents describe rebuilding their agent stack on timescales of months. The frameworks that work — Claude Code, Cursor, simple tool-use loops — share a common trait: they resist the elaborate multi-agent orchestration that most "Agentic OS" designs aspire to. Anyone designing an OS-like layer for agents must contend with overwhelming evidence that **context engineering, not architectural sophistication, is the actual bottleneck** in production agent systems.

This analysis covers eight dimensions of the landscape to ground a peer review of an Agentic OS design concept, drawing on surveys, postmortems, benchmarks, and production case studies from 2024–2026.

## Key Insights

### The demo-to-production gap is severe and well-documented

The LangChain State of AI Agents Report[^langchain-state] (late 2025, n=1,340) found that 57% of respondents have agents in production, but **quality is the #1 barrier** — 32% cite accuracy, relevance, and consistency as top blockers. The Cleanlab/MIT survey[^cleanlab] paints a starker picture: only 95 out of 1,837 respondents (roughly 5%) had agents actually live. Stack churn is extreme. One respondent described "moving from LangChain to Azure in two months, only to consider moving back again."

The documented production pain points cluster into four categories. **Prompt drift** is the silent killer: even "fixed" model versions change behavior without notice. A developer on the OpenAI community forum reported that gpt-4o-2024-08-06 had shifted behavior, writing: "I can accept an outage... but if the model changes behavior that scares me." A travel-tech startup's booking agent began misreading dates and calling wrong APIs — logs showed green, but support tickets climbed. **Context window failures** compound this: Chroma Research[^context-rot] (July 2025) tested 18 frontier LLMs on trivially simple tasks and found performance "grows increasingly unreliable as input length grows." Databricks found correctness drops around **32,000 tokens** for Llama 3.1 405B, and earlier for smaller models. **Tool composition degrades as you add tools**: Cubic's code review agent became confused and generated excessive false positives when given more tools — the fix was removing tools. Shopify's Sidekick hit a "tool complexity wall" scaling from 20 to 50+ tools. And the MIT/Kellogg finding that cuts deepest: **80% of the work in production agent projects is consumed by data engineering, governance, and workflow integration**, not the AI itself.

These aren't growing pains. Informatica[^informatica] reports that over 80% of AI projects still fail, twice the rate of traditional technology programs, and 91% of AI models experience quality degradation over time. Forrester's 2026 predictions[^forrester] reinforce this concern: enterprises will defer 25% of planned AI spend to 2027, and only 15% of AI decision-makers reported an EBITDA lift — fewer than one-third can tie AI value to P&L changes. Agent failures do not follow the patterns of traditional software bugs; they emerge from ambiguity, miscoordination, and unpredictable system dynamics.

---

### Nine frameworks, three real architectural patterns

The framework landscape has consolidated around three architectural patterns despite surface-level diversity. **Graph-based state machines** (LangGraph, ~25K GitHub stars, 38M monthly PyPI downloads) model agents as nodes with typed state passing and automatic checkpointing. **Role-based multi-agent systems** (CrewAI, ~45K stars, 450M monthly workflows) organize agents into crews with delegation and hierarchical processes. **Minimalist tool-loop architectures** (OpenAI Agents SDK, ~16K stars) use just four primitives: agents, handoffs, guardrails, and sessions. Then there are the **protocol/ecosystem approaches** — Anthropic's MCP + Skills + Claude Agent SDK — which avoid prescribing orchestration patterns entirely.

The most telling metric is what's actually surviving in production. LangGraph powers Klarna's customer support (85M users), Elastic's security AI, and Replit. But 45% of developers who experimented with LangChain never deployed to production, and 23% who deployed eventually removed it (Adaline community analysis, late 2025). CrewAI's role-based paradigm is easy to prototype but consumes **nearly 3x the tokens and time** of LangChain for simple tasks (AIMultiple benchmark) — teams frequently prototype in CrewAI then migrate to LangGraph. Microsoft's AutoGen (~55K stars) entered maintenance mode in October 2025[^autogen], merging with Semantic Kernel into the "Microsoft Agent Framework" (GA targeted Q1 2026). The project's confusing four-way split (microsoft/autogen, AG2 fork, Semantic Kernel, Microsoft Agent Framework) is a cautionary tale about organizational complexity seeping into architecture.

The standout newcomer is **Mastra**[^mastra] (~22K stars, 300K+ weekly npm downloads), a TypeScript-first framework from the Gatsby.js team (YC W25). Its "Observational Memory" system compresses text 3-6x and tool outputs 5-40x, cutting token costs 4-10x while outperforming RAG on long-context benchmarks. Mastra's 1.0 shipped January 2026 with production use at Replit, WorkOS, and Fireworks AI. It signals strong demand for TypeScript-native agent tooling as TypeScript overtook Python in GitHub's 2025 language report.

**Google ADK** provides a modular, multi-language approach (Python, TypeScript, Go, Java) with three agent types — LLM, Workflow, and Custom — but remains tightly coupled to the Gemini/Vertex AI ecosystem. **DSPy** (~23K stars) remains the most intellectually distinctive framework, treating prompts as a compilation target rather than an authoring surface, but its production footprint is thin. The industry-wide pattern is clear: **frameworks that impose the least architectural opinion and maximize context control tend to survive production contact.**

---

### The "agent OS" metaphor has been explored, but no one has built Unix

The OS-for-agents metaphor has been proposed repeatedly, but **no project has combined all OS primitives into a coherent, widely-adopted system**. The landscape fragments into three camps.

**Rutgers' AIOS**[^aios] is the most complete academic implementation. Published at COLM 2025, it maps every major OS concept — kernel (LLM), scheduling (syscall dispatcher), memory management (context manager), file system (semantic file system with 20-24% higher retrieval accuracy), access control (privilege-based hashmap), and system calls — to agent equivalents. Agents from ReAct, AutoGen, and MetaGPT run on AIOS without code modification, achieving up to **2.1x faster execution** under concurrent load. But AIOS remains primarily academic, without significant industry adoption.

**Andrej Karpathy's "LLM OS" vision**[^karpathy] (November 2023) was the conceptual catalyst that launched this thinking. His diagram — LLM as CPU, context window as RAM, embeddings as file system, tools as system libraries — received 2.4M views and spawned multiple open-source implementations. It remains the most influential framing, even though it was explicitly labeled "still cooking." **MemGPT/Letta**[^letta] provides the most elegant single-concept mapping: virtual memory paging for context management. Just as an OS pages data between RAM and disk, Letta pages information between the context window and external storage. The company raised $10M, has 19K GitHub stars, and ships production features including Context Repositories (git-backed memory, February 2026) and Sleep-Time Compute (background processing while idle).

Enterprise players have adopted the branding without the architecture. PwC launched "Agent OS" as an enterprise orchestration product. Beam AI markets "AgentOS" as a multi-agent platform. AControlLayer defines four "kernel primitives" (state/memory, permissions, scheduling, observability) but remains early-stage. Marc Bara's comprehensive analysis[^bara] (March 2026) captures the state precisely: "I went looking for the OS that treats agents as first-class processes. What exists today is fragments, not systems." He notes that **no existing project solves all four required capabilities** — process isolation, scheduling, shared memory, and permissions — simultaneously.

Two distinct meanings of "Agent OS" have emerged and any design must choose between them: (a) the LLM itself as kernel, with agents as applications running on it (AIOS, Karpathy), or (b) an infrastructure layer that manages agents as processes, analogous to how Linux manages programs (AControlLayer, HFS Research). These are complementary but architecturally different.

---

### MCP is real infrastructure, but security remains the open wound

The Model Context Protocol[^mcp] has achieved something genuinely rare in AI: **cross-vendor adoption at scale**. Launched by Anthropic in November 2024, MCP now has **97 million monthly SDK downloads**, over 10,000 published servers, and first-class client support in Claude, ChatGPT, Cursor, Gemini, Microsoft Copilot, VS Code, and JetBrains IDEs. In December 2025, Anthropic donated MCP to the Agentic AI Foundation (AAIF) under the Linux Foundation[^agents-md], with platinum members including AWS, Google, Microsoft, OpenAI, Bloomberg, and Cloudflare. Jensen Huang called MCP's impact on the landscape "revolutionary."

The "USB-C for AI" metaphor is accurate for its scope: MCP standardizes tool connectivity (agent-to-tool), collapsing the M*N integration problem into M+N. It does not address agent-to-agent communication — that's **Google's A2A protocol** (launched April 2025, 50+ technology partners, also under Linux Foundation). Google frames the distinction clearly: "MCP is the protocol for structured action. A2A is for ongoing multi-agent conversation and coordination." Notably, **Anthropic and OpenAI are not listed as A2A partners**, suggesting the agent-to-agent layer remains contested territory.

Production deployments are real. Block (Square/Cash App) is an AAIF co-founder with deep MCP integration. Cursor reached **$500M ARR** by June 2025[^cursor-arr] with heavy MCP usage. CData Software runs 1,000+ live MCP connectors for enterprise data. The MCP.so marketplace directory lists 18,217 servers; FastMCP tracks 8,590+.

The critical weakness is security. **CVE-2025-6514**[^cve-6514] in the mcp-remote package compromised 437,000+ developer environments. **CVE-2025-49596**[^cve-49596] in Anthropic's own MCP Inspector enabled browser-based remote code execution. Tool descriptions go directly to the AI model, creating prompt injection surfaces. Token storage across MCP servers means one breach grants access to everything. The Snyk ToxicSkills study[^snyk] found that **36% of community-published skills have security flaws** (n=3,984 skills scanned). For any Agentic OS design, the lesson is stark: MCP is the right connectivity standard, but wrapping it in a serious permission and sandboxing model is non-negotiable.

---

### Skills packaging is converging faster than expected

The most surprising finding in this research is genuine cross-vendor convergence on agent capability packaging. Anthropic's **SKILL.md format** — YAML frontmatter plus Markdown instructions in a directory with optional scripts and references — was released as an open standard in December 2025, and **OpenAI adopted the same format** for Codex CLI and ChatGPT. This is the closest the industry has come to a portable, reusable skill format.

The architecture is worth studying for any OS design. Skills use **progressive disclosure**: at startup, Claude sees only metadata (~100 tokens per skill). When a skill is relevant, the full SKILL.md loads (~5K tokens). Bundled resources (scripts, templates, references) load on demand. This is an elegant solution to the tool-count problem that plagued Shopify and Cubic. Skills are not sub-agents or separate processes — they're "injected instructions that guide behavior within the main conversation," achieving on-demand prompt expansion without modifying the core system prompt.

In parallel, **AGENTS.md**[^agents-md] has achieved remarkable adoption: 60,000+ open-source projects, supported by 20+ tools including OpenAI Codex, GitHub Copilot, Cursor, Devin, Gemini CLI, and VS Code. Stewarded by the AAIF under the Linux Foundation, AGENTS.md provides vendor-neutral project instructions for AI coding agents. OpenAI's own monorepo contains 88 AGENTS.md files. The practical pattern emerging: AGENTS.md for shared instructions, CLAUDE.md for Claude-specific features (@imports, auto-memory), and tool-specific files only when necessary.

Skill marketplaces are nascent but real. **SkillsMP** hosts 31,000+ agent skills. Oracle, ServiceNow, and Salesforce have launched enterprise agent marketplaces. Integration platforms like **Composio** (250-850+ pre-built tool integrations, SOC 2 compliant) and **Nango** (600+ APIs, open-source) solve the auth and connectivity pain that plagues custom integrations. The "agent app store" concept is materializing, though quality control and security remain unsolved.

---

### Memory architectures are production-ready but context window size is a red herring

The industry has converged on a **three-tier memory model**: working memory (current context window), episodic memory (session/interaction history), and semantic memory (long-term knowledge). Multiple production systems implement this with real benchmarks.

**Zep** uses temporal knowledge graphs (the Graphiti engine) to synthesize unstructured conversation data with structured business data while tracking historical relationships. It achieves **94.8% on the DMR benchmark** (vs. MemGPT's 93.4%), with sub-200ms retrieval latency and 90% latency reduction versus baselines. **Mem0** offers the simplest API — three lines of code — and reports zero hallucination errors and 15% fewer harmful actions in a two-month production deployment. **Mastra's Observational Memory**[^mastra] (shipped March 2026) compresses observations rather than using vector retrieval, hitting **94.87% on LongMemEval** while claiming 10x cost reduction versus RAG.

The critical insight for any OS design: **larger context windows do not reduce the need for memory management**. NVIDIA's RULER benchmark[^ruler] shows effective context is only 50-65% of advertised window size. Llama 3.1-70B accuracy drops from 96.5% at 4K tokens to 66.6% at 128K — a 30-point decline. The "lost in the middle" problem persists in all models: accuracy at early/late positions reaches 85-95%, but drops to 76-82% in the middle. Anthropic's Claude is best-in-class with less than 5% degradation across 200K tokens, but degradation is still present. And the cost multiplier is brutal: agentic applications re-send context 10-50x per session. A 20-call session at GPT-4.1 prices with 500K average context costs **$20 in input tokens alone**.

Letta's approach[^letta] — letting agents manage their own context via tool calls (memory_replace, memory_insert, archival_memory_search) — is the most architecturally interesting for an OS design. Their February 2026 Context Repositories feature adds git-backed memory with version tracking, enabling concurrent subagents to manage divergence through standard git operations. LangGraph's checkpointer pattern (PostgresSaver, Redis for sub-1ms latency) is the most battle-tested for thread-level persistence. The known failure modes to design around: context poisoning from outdated memories, memory sprawl without garbage collection, summarization drift from repeated compression, and retrieval failures at scale requiring hybrid semantic + keyword + graph approaches.

---

### The evidence overwhelmingly favors simplicity over elaborate architectures

This is the finding most relevant to peer-reviewing an Agentic OS concept. The evidence from 2024-2026 consistently shows that **simpler architectures outperform complex ones in production**.

The most striking case study is **Vercel's text-to-SQL agent**[^vercel]. They stripped it from 15+ specialized tools to just 2 (bash and SQL execution). Results: success rate jumped from **80% to 100%**, tokens dropped 40% (102K to 61K), average steps fell from 12 to 7. Their worst-case scenario under the old architecture — 724 seconds, 100 steps, 145,463 tokens, then failure — became 141 seconds, 19 steps, 67,483 tokens, success. Their conclusion: "We were doing the model's thinking for it."

A UC Berkeley team published the first systematic failure taxonomy for multi-agent systems[^mast] at NeurIPS 2025, analyzing **1,600+ annotated traces across 7 popular frameworks**. They identified 14 unique failure modes and found that "despite enthusiasm for MAS, their performance gains on popular benchmarks are often minimal." The state-of-the-art open-source multi-agent system ChatDev had correctness **as low as 25%** — meaning three out of four task traces ended in failure. Best-effort interventions yielded only +14% improvement — "insufficient for real-world deployment."

Cognition[^devin-arr] (Devin, $73M ARR by June 2025) published "Don't Build Multi-Agents"[^cognition] in June 2025, arguing that multi-agent systems are inherently fragile due to **context isolation** — sub-agents making incompatible decisions because neither has the other's context. Their solution: single-threaded, linear agents with whole-conversation-history passing. Anthropic's own "Building Effective Agents"[^anthropic-agents] post warns that frameworks "often create extra layers of abstraction that can obscure the underlying prompts and responses" and recommends starting with direct LLM API calls. A January 2026 study[^skills-vs-multi] provides direct evidence: single agents with skill libraries "substantially reduce token usage and latency while maintaining competitive accuracy on reasoning benchmarks" compared to multi-agent approaches — but identifies a **phase transition** where performance drops sharply as skill libraries grow, driven by semantic confusability among similar skills rather than library size alone.

An important distinction has crystallized in production: **multi-agent swarms** (independent agents negotiating with each other, as in AutoGen or CrewAI) are architecturally different from **subagent patterns** (a parent agent forking child processes with subset context for parallel tasks, as in Claude Code's Agent tool). The latter is a controlled fork-and-join within a single-agent architecture — the parent retains full context and synthesizes results. Gartner[^gartner] reports a 1,445% surge in multi-agent system inquiries from Q1 2024 to Q2 2025, but also predicts that over 40% of agentic AI projects will be canceled by end of 2027 due to escalating costs and unclear business value. The hype cycle is running ahead of the evidence.

Simon Willison's[^willison] working definition captures the pattern that actually works: "An LLM agent runs tools in a loop." Claude Code[^claude-code-arr], credited with $1B in run-rate revenue for Anthropic, is fundamentally this pattern. Cursor[^cursor-arr] reached $1B ARR by November 2025 with the same architecture.

For an Agentic OS designer, this creates a tension: you need enough architecture to manage context, permissions, and persistence, but **every additional abstraction layer is a liability** until proven otherwise. Harrison Chase[^chase] (LangChain) articulates the hard-won lesson at ODSC AI West 2025: "Put all complexity in the prompt. Don't add pre-processing steps or wrapper logic."

---

### Documentation is becoming load-bearing infrastructure for agents

The final piece of the landscape addresses how agents discover and consume knowledge. Three standards are emerging at different layers. **llms.txt** (proposed by Jeremy Howard, September 2024) places LLM-friendly Markdown at `/llms.txt` on websites. Adoption is growing fast — from 15 sites in the Majestic Million in February 2025 to 105 by May, with ~784+ listed in community directories — but remains negligible in the broader web. No major LLM provider has confirmed consuming llms.txt files. Mintlify auto-generates it for 5,000+ companies, making it de facto documentation infrastructure for the dev tools ecosystem.

**AGENTS.md**[^agents-md] has far more traction: 60,000+ open-source projects, supported by 20+ tools, governed by the AAIF. It addresses project-level agent instructions (build commands, test patterns, code conventions, architecture boundaries). **SKILL.md** handles capability packaging with progressive disclosure. Together with MCP[^mcp] for runtime tool access and OpenAPI for API documentation, a real stack is crystallizing.

The most rigorous treatment of documentation-as-infrastructure is the **"Codified Context" paper**[^codified] (arXiv:2602.20478, February 2026). A single developer built a 108,000-line C# distributed system in ~70 days using AI agents, with a three-tier context architecture: hot memory (always-loaded project constitution), 19 specialized domain-expert agents with embedded knowledge, and cold memory (34 on-demand specification documents served via MCP). The total context infrastructure was ~26,000 lines — an order of magnitude beyond typical manifest files. The key finding: **"Single-file manifests (.cursorrules, CLAUDE.md, AGENTS.md) do not scale beyond modest codebases."** A 1,000-line prototype fits in one prompt; a 100,000-line system requires structured, tiered, relational documentation. Nobody has yet built a production-grade relational/typed documentation system for agent navigation, but the Codified Context paper demonstrates the need exists and the pattern works.

### Synthesis

Five hard truths define the realistic picture for any Agentic OS concept in early 2026.

**Context engineering is the actual product.** Every production success story — Claude Code[^claude-code-arr], Cursor[^cursor-arr], Vercel's stripped-down agent[^vercel] — traces back to superior context management, not architectural elegance. Context windows have grown dramatically (Claude 4.6: 1M tokens, Gemini 3 Pro: 1M tokens), but Chroma's "Context Rot" study[^context-rot] shows the fundamental problem persists: performance degrades non-uniformly as input length grows, even on trivially simple tasks, regardless of model generation. Larger windows shift the boundary but do not eliminate the engineering challenge. An Agentic OS that doesn't make context engineering its core primitive is solving the wrong problem.

**The permission and security model is the hardest unsolved problem.** MCP's CVEs[^cve-6514][^cve-49596], the 36% skill security flaw rate[^snyk], and the absence of a real agent permission model anywhere in the ecosystem represent the gap where an OS abstraction could add genuine value — process isolation, capability-based security, auditable tool access.

**Multi-agent swarms remain unproven; subagent patterns are emerging as a middle ground.** The Berkeley MAST taxonomy[^mast], Vercel's tool reduction[^vercel], Cognition's anti-multi-agent stance[^cognition], and the MAST correctness data all converge: independent agents negotiating with each other fail at production-grade reliability. The best-performing open-source multi-agent system (ChatDev) achieved only 25% correctness on MAST benchmarks — meaning three out of four task traces ended in failure. However, **fork-and-join subagent patterns** — where a parent agent delegates parallel subtasks to child processes while retaining full context — are proving viable in production (Claude Code Agent Teams, Codex). This is architecturally distinct from multi-agent swarms: one orchestrator, controlled delegation, synthesized results. The decision boundary between injecting a skill into the main context versus forking a subagent remains an open research question. Start with a single agent, add subagents only for genuinely parallelizable work, avoid swarm patterns until the evidence changes.

**The standards stack is settling.** MCP[^mcp] for tool connectivity, A2A for agent-to-agent communication, SKILL.md for capability packaging, AGENTS.md[^agents-md] for project instructions — all under Linux Foundation governance via the AAIF. An Agentic OS should compose with these standards rather than compete with them.

**The Unix analogy is apt but incomplete.** As Marc Bara[^bara] observed, "Unix did not create any of its individual concepts. It combined them into a coherent system with a small set of composable primitives." The agent ecosystem has the individual concepts — virtual memory (Letta[^letta]), scheduling (AIOS[^aios]), tool connectivity (MCP[^mcp]), capability packaging (Skills), process isolation (Claude Cowork's containers). What's missing is the coherent combination. But the evidence also warns that the winner is likely to "emerge from a working runtime that accretes capabilities because developers keep needing one more thing" — not from a grand architectural vision designed top-down.

## References

### Internal
- [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) — produced from this analysis
- [ADR-26034: Agentic OS Paradigm — Skills as Composable Applications](/architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md) — produced from this analysis (rejected)
- [A-26005: Document Type Interfaces and Unified Validation](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) — OS metaphor and VFS model
- [A-26006: Agent Runtime Architecture and RAG Infrastructure](/architecture/evidence/analyses/A-26006_agent_runtime_architecture_rag_infrastructure.md) — complements this analysis with implementation patterns

### External

[^cleanlab]: [Cleanlab/MIT Enterprise AI Agent Survey](https://cleanlab.ai/ai-agents-in-production-2025/) (2025, n=1,837)
[^langchain-state]: [LangChain State of AI Agents Report](https://www.langchain.com/state-of-agent-engineering) (late 2025, n=1,340)
[^mast]: UC Berkeley MAST: [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (NeurIPS 2025, 1,600+ traces)
[^cognition]: [Cognition — "Don't Build Multi-Agents"](https://cognition.ai/blog/funding-growth-and-the-next-frontier-of-ai-coding-agents) (June 2025)
[^anthropic-agents]: [Anthropic — "Building Effective Agents"](https://www.anthropic.com/research/building-effective-agents) (December 2024)
[^vercel]: [Vercel — "We Removed 80% of Our Agent's Tools"](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools) — text-to-SQL agent simplification case study
[^ruler]: [NVIDIA RULER Benchmark](https://arxiv.org/abs/2404.06654) — effective context window measurement
[^context-rot]: [Chroma Research — "Context Rot"](https://research.trychroma.com/context-rot) (July 2025, 18 frontier LLMs)
[^bara]: Marc Bara — Agent OS landscape analysis (March 2026, Medium)
[^codified]: ["Codified Context" paper](https://arxiv.org/abs/2602.20478) (February 2026)
[^mcp]: [Anthropic MCP — Model Context Protocol](https://modelcontextprotocol.io/) specification
[^aios]: [AIOS — Rutgers University](https://arxiv.org/abs/2403.16971) (COLM 2025)
[^karpathy]: Andrej Karpathy — ["LLM OS" vision](https://x.com/karpathy/status/1707437820045062561) (November 2023)
[^letta]: [MemGPT/Letta](https://docs.letta.com/concepts/memgpt/) — context paging and Context Repositories
[^mastra]: [Mastra](https://github.com/mastra-ai/mastra) — Observational Memory system (v1.0, January 2026)
[^agents-md]: [AGENTS.md — AAIF vendor-neutral project instructions standard](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation) (60,000+ projects)
[^snyk]: [Snyk ToxicSkills study](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) — 36% of community skills have security flaws (February 2026, n=3,984)
[^cve-6514]: [CVE-2025-6514](https://nvd.nist.gov/vuln/detail/CVE-2025-6514) — mcp-remote package compromise (CVSS 9.6)
[^cve-49596]: [CVE-2025-49596](https://nvd.nist.gov/vuln/detail/CVE-2025-49596) — MCP Inspector RCE (CVSS 9.4)
[^informatica]: [Informatica CDO Insights 2025](https://www.cio.com/article/4083265/why-80-of-ai-projects-fail-and-how-smart-enterprises-are-finally-getting-it-right.html) — 80% AI project failure rate
[^forrester]: [Forrester Predictions 2026](https://www.forrester.com/predictions/) — AI hype-to-reality transition, 25% spend deferral
[^gartner]: [Gartner Multiagent Systems](https://www.gartner.com/en/articles/multiagent-systems) — 1,445% inquiry surge Q1 2024–Q2 2025; [40% of agentic projects canceled by 2027](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)
[^skills-vs-multi]: [Single-Agent with Skills vs Multi-Agent Systems](https://arxiv.org/abs/2601.04748) (January 2026) — phase transition in skill library scaling
[^cursor-arr]: [Cursor $500M+ ARR](https://techcrunch.com/2025/06/05/cursors-anysphere-nabs-9-9b-valuation-soars-past-500m-arr/) (TechCrunch, June 2025; [$1B by November 2025](https://www.saastr.com/cursor-hit-1b-arr-in-17-months-the-fastest-b2b-to-scale-ever-and-its-not-even-close/))
[^claude-code-arr]: [Claude Code $1B run-rate revenue](https://www.anthropic.com/news/anthropic-acquires-bun-as-claude-code-reaches-usd1b-milestone) (Anthropic announcement)
[^devin-arr]: [Devin/Cognition $73M ARR](https://sacra.com/c/cognition/) (Sacra, June 2025)
[^autogen]: [AutoGen maintenance mode, merged into Microsoft Agent Framework](https://venturebeat.com/ai/microsoft-retires-autogen-and-debuts-agent-framework-to-unify-and-govern) (October 2025)
[^willison]: Simon Willison — ["Agents are models using tools in a loop"](https://simonwillison.net/2025/May/22/tools-in-a-loop/) (May 2025)
[^chase]: Harrison Chase — ["Put all complexity in the prompt"](https://opendatascience.com/harrison-chase-on-deep-agents-the-next-evolution-in-autonomous-ai/) (ODSC AI West 2025)
