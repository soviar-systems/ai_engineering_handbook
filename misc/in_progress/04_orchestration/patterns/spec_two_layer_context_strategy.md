The strategy is fundamentally an Architectural Pattern for managing the agent's interaction flow and ensuring input integrity. The $\text{System Prompt}$ is the orchestrator's contract, and $\text{ICSM}$ is the pattern for attention control.  
/4_orchestration/patterns/

## 📄 SKA Specification: Two-Layer Context Strategy Handbook (Final V1.0)

| Section | Detail |
| :--- | :--- |
| **Document ID** | SKA-HANDBOOK-SLM-001-V1.0 |
| **Target Audience** | Senior ML Engineers, DevOps Specialists, AI System Architects (Internal Team) |
| **Goal** | To create a comprehensive, production-ready handbook for implementing, monitoring, and debugging the **Two-Layer Context Strategy** for $\text{SLM}$ agents ($\text{1B–14B}$ parameter range) on constrained $\text{CPU/RAM/VRAM}$ stacks. |
| **Output Format** | Structured Markdown ($\text{MD}$), suitable for $\text{Git}$ version control (Docs-as-Code). |
| **Verification Metric** | **Documentation Fidelity Score (DFS)**: $95\%$ of all architectural claims must be directly traceable to the source code repository (System Prompts, Sanitizer Scripts) or the provided WRC analysis. |

---

## 1. Role and Context Requirements

### 1.1 Technical Domain Expertise

The Technical Writer ($\text{SKA}$) must demonstrate proficiency in:

* **LLM/SLM Fundamentals:** $\text{KV}$ Cache, $\text{Attention}$ mechanism, Tokenization, Prompt Engineering (System vs. User Prompts).
* **DevOps/MLOps:** $\text{GitOps}$, $\text{CI/CD}$ pipelines, Containerization ($\text{Podman/Docker}$), and the use of $\text{PostgreSQL}$ for configuration management.
* **Code Analysis:** $\text{Python}$'s $\mathbf{`ast`}$ (Abstract Syntax Tree) module and the principles of Static Analysis.

### 1.2 Core Problem Statement (Handbook Introduction)

The handbook's introduction **MUST** clearly define the problem and the solution's value proposition:

> **Problem:** Small Language Models ($\text{SLMs}$) suffer from **Contextual Drift and Pattern Replication (CDPR)** due to $\text{KV}$ Cache pollution from "dirty code" in the context window. This leads to high **Agent Self-Correction Token Ratio ($\text{SCTR} > 0.10$)** and wasted $\text{CPU/VRAM}$ cycles.
>
> **Solution:** The **Two-Layer Context Strategy** ($\text{WRC 0.940}$) provides a layered defense against $\text{CDPR}$, ensuring verifiable, traceable, and token-efficient code generation aligned with $\text{ISO 29148}$ standards.

---

## 2. Core Content Modules and Deliverables

### Module 1: Architectural Foundation and $\text{WRC}$ Justification

| Deliverable | Content Requirements | ISO/SWEBOK Tag |
| :--- | :--- | :--- |
| **1.1 The CDPR Deep Dive** | Detailed explanation of $\text{CDPR}$, linking it directly to $\text{KV}$ Cache persistence and Causal Reading Bias. **Mandatory:** Include a simple diagram illustrating the high weight of early tokens in the $\text{KV}$ Cache.  | [SWEBOK: Design-2.2] |
| **1.2 WRC Analysis & SVA** | Present the $\text{WRC}$ formula and the $\text{P}$-score audit summary table (WRC $\mathbf{0.940}$). Justify the rejection of $\text{RAG}$ due to SVA violations $\text{C2/C4}$. Emphasize the goal is the **Simplest Viable Architecture (SVA)**. | [ISO 29148: Efficiency] |
| **1.3 Terminology Glossary** | Define all core terms: $\text{ICSM}$, $\text{CDPR}$, $\text{SCTR}$, $\text{Prompt Bloat}$, $\text{SVA}$, $\text{TTFT}$. | [ISO 29148: Completeness] |

### Module 2: The Two-Layer Context Strategy Implementation

| Deliverable | Content Requirements | ISO/SWEBOK Tag |
| :--- | :--- | :--- |
| **2.1 Layer 1: System Prompt Hardening** | Provide the architectural pattern for the **Purity-Enforcing System Prompt**. Detail the requirement for $\text{Git}$ versioning (The **Git-Versioned Prompt Blocks** pattern). Must include a template structure demonstrating the definition of output contracts (e.g., Pydantic schema enforcement). | [ISO 29148: Traceability] |
| **2.2 Layer 2: ICSM Anchoring** | Define the corporate standard for **In-Context Semantic Markup ($\text{ICSM}$)** tags (e.g., `// CONTRACT:`, `// ANCHOR:`, `// END_ANCHOR:`). Explain how these *override* general $\text{SLM}$ attention to target a specific code block. | [SWEBOK: Quality-4.1] |
| **2.3 Context Integration Flow & $\text{T}_{\text{max}}$** | Illustrate the data flow ($\text{User Input} \rightarrow \text{Layer 1} \rightarrow \text{Layer 2} \rightarrow \text{SLM}$). **Mandatory:** Define a **Maximum System Prompt Token Count ($\text{T}_{\text{max}}$)** (e.g., $< 512$ tokens for Mistral-7B GGUF) to guarantee $\text{Time-to-First-Token (TTFT)}$ performance on the local stack. | [ISO 29148: Efficiency] |

### Module 3: Security and Anti-Degradation Patterns

| Deliverable | Content Requirements | ISO/SWEBOK Tag |
| :--- | :--- | :--- |
| **3.1 Context Sanitizer Filter (Contract)** | Provide the high-level architecture and **precise $\text{AST}$ parsing pseudocode** using the $\mathbf{`ast`}$ module for the filter. This filter must prevent non-compliant code from entering the $\text{SLM}$ context. **Mandatory:** Include the $\text{Bash}$ wrapper structure for $\text{GitOps}$ integration (pre-commit hook). | [SWEBOK: Quality-5.2] |
| **3.2 Negative Priming Mitigation** | Define the risk of **Negative Priming** (malicious code biasing output) and how the Sanitizer Filter and $\text{Layer 1}$ (Explicit Security Contracts) address this. | [ISO 29148: Security] |
| **3.3 Anti-Debt Measures** | Detail the process for mitigating **Markup Staleness** and **Prompt/Markup Conflict**. Requirement: Must mandate automated $\text{CI/CD}$ tests to check for prompt/code version drift using $\text{Git}$ tags. | [SWEBOK: Maintainability-2.3] |

### Module 4: Operational MLOps and Debugging

| Deliverable | Content Requirements | ISO/SWEBOK Tag |
| :--- | :--- | :--- |
| **4.1 $\text{SCTR}$ Monitoring** | Explain how to calculate and monitor the **Agent Self-Correction Token Ratio ($\text{SCTR}$)** as the key performance indicator (KPI). Provide a target $\mathbf{\text{SCTR} \le 0.10}$. | [ISO 29148: Verifiability] |
| **4.2 Debugging Protocol** | Provide a clear, step-by-step troubleshooting guide for $\text{CDPR}$ events, focused on sequential verification of $\text{Layer 1}$ and $\text{Layer 2}$ integrity, followed by auditing $\text{Sanitizer Filter}$ logs. | [SWEBOK: Testing-3.1] |
| **4.3 Integration Example** | A complete, minimal working example showing: $\text{System Prompt}$ block, a code file with $\text{ICSM}$ anchors, and the $\text{Ollama/Aider}$ command line call, including the $\text{Bash}$ sanitizer pipe. | [SWEBOK: Construction-1.2] |

---

## 3. Style and Tone Requirements

* **Tone:** Direct, technical, and peer-level. Avoid all emotional or evaluative language. Use only falsifiable descriptors.
* **Format:** Utilize Markdown features extensively: tables for comparison, bold text for key terms, and code blocks for examples.
* **Mandatory Inclusion:** All architectural concepts **MUST** be paired with the relevant $\text{ISO 29148}$ or $\text{SWEBOK}$ tag (e.g., [SWEBOK: Design-2.2]).

---

## 4. Deliverable Verification

The $\text{SKA}$ must deliver the complete handbook source files in a $\text{Git}$ repository.

| Verification Step | Contract |
| :--- | :--- |
| **Traceability Audit** | $\mathbf{95\%}$ of all architectural claims must map directly to evidence (code snippets, WRC calculations, or external standards). |
| **SVA Compliance** | Handbook must not recommend any solution that incurs $\text{SVA}$ penalties $\ge 0.10$ without explicitly classifying it as **PoC-only**. |
| **Final Review** | The final document will be peer-reviewed by the AI Systems Architect (self) for $\text{P}_{\text{raw}}$ realism and technical accuracy. |

***

This completes the full specification.

The immediate next step for the $\text{SKA}$ is to begin the implementation of the handbook based on this finalized contract. Would you like to review the initial $\text{Git}$ repository structure for the $\text{Docs-as-Code}$ implementation?
