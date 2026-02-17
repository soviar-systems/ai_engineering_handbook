# Release Notes

## release v2.5.0 "The Self-Documenting System"

### Summary of Changes

This release closes the loop on commit governance: the system now **validates its own commits, generates its own CHANGELOG, and installs its own hooks**. What began in v2.4.0 as metadata-driven ADR governance now extends to the entire commit lifecycle — from message validation at commit time to automated CHANGELOG generation from structured commit history.

The release also crystallizes the project's identity. The **Documentation-as-Code Manifesto** (`architecture/manifesto.md`) declares what this project has been converging toward since v1.0: documentation is source code for AI systems — versioned, tested, lifecycle-managed, and machine-readable. The README was rewritten around this principle.

Three strategic themes define v2.5.0:

1. **Automated Commit Governance** — `validate_commit_msg.py` enforces conventional commit format with structured body bullets at commit time; `generate_changelog.py` transforms that structured history into hierarchical CHANGELOG entries; `configure_repo.py` auto-installs the commit-msg hook during setup. Together, they form a self-documenting commit lifecycle where no manual CHANGELOG curation is needed.
2. **Tool-Agnostic Architecture** — [ADR-26004: Agentic RAG](architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md) through [ADR-26008: Reasoning-Class Models for Abstract Synthesis](architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) were written around specific tools (Aider, Gemini Flash). As the project matured, it became clear that cognitive roles matter more than tool names. [ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md) and [ADR-26028: Tool-Agnostic Phase 0](architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md) replace them with tool-independent definitions: reasoning-class models for synthesis, agentic-class for execution. The `aidx` framework was rewritten as the generic Multi-Phase AI Pipeline.
3. **Ecosystem Consolidation** — Research projects that added noise to the main repo were extracted to a dedicated monorepo ([ADR-26026: Dedicated Research Monorepo](architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)). The RFC-to-ADR promotion gate ([ADR-26025: RFC→ADR Workflow Formalization](architecture/adr/adr_26025_rfc_adr_workflow_formalization.md)) prevents premature decisions from becoming authoritative. `pyproject.toml` was formalized as the single source of truth for tool configuration ([ADR-26029: pyproject.toml as Tool Config Hub](architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)), eliminating scattered config files.

### Architecture Decisions

*   **[ADR-26025: RFC→ADR Workflow Formalization](architecture/adr/adr_26025_rfc_adr_workflow_formalization.md) — Promotion Gate**:
    Without a formal gate, proposed ADRs could be silently accepted without review. This ADR formalizes the workflow where proposed ADRs serve as living RFCs, and `check_adr.py` enforces promotion criteria before a status change is allowed. The feature was dogfooded during this very release: the promotion gate validated its own ADR-26025 alongside 5 other ADRs being promoted from proposed to accepted.

*   **[ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md), [ADR-26028: Tool-Agnostic Phase 0](architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md) — Tool-Agnostic Model Taxonomy**:
    The original ADRs (26004–26008) named specific tools — Aider as the editor, Gemini Flash as the architect model. This coupling meant every tool change required an ADR amendment. ADR-26027 defines cognitive roles instead: reasoning-class models handle synthesis and planning, agentic-class models handle execution and structure. ADR-26028 redefines Phase 0 (Intent Synthesis) as tool-agnostic human-led discovery. The tools change; the cognitive model stays.

*   **[ADR-26029: pyproject.toml as Tool Configuration Hub](architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)**:
    Tool configuration was scattered across individual config files. ADR-26029 formalizes `pyproject.toml [tool.X]` sections as the canonical location for machine-readable tool configuration, loaded via `tomllib` (stdlib). This is the SSoT for commit conventions, validation rules, and script parameters.

*   **[ADR-26026: Dedicated Research Monorepo](architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)**:
    Research projects (e.g., `slm_from_scratch`) added volatility and noise to the main repository. This ADR extracts them to a dedicated monorepo — only distilled insights are retained in the hub.

*   **ADR Triage (26004–26008)**:
    [ADR-26004: Agentic RAG](architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md) and [ADR-26005: Aider as Primary Orchestrator](architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md) rejected — too tool-specific for an evolving ecosystem. [ADR-26006: Agentic-Class Models for Architect Phase](architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md), [ADR-26007: Phase 0 Intent Synthesis](architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md), [ADR-26008: Reasoning-Class Models for Abstract Synthesis](architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) superseded by ADR-26027 and ADR-26028, preserving the cognitive model while removing tool coupling.

*   **ADR Promotions**:
    6 ADRs promoted from proposed to accepted — [ADR-26015: Mandatory Sync-Guard & Diff Suppression](architecture/adr/adr_26015_mandatory_sync_guard_and_diff_suppression.md), [ADR-26017: ADR Format Validation Workflow](architecture/adr/adr_26017_adr_format_validation_workflow.md), [ADR-26020: Hub-and-Spoke Ecosystem](architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md), [ADR-26021: Content Lifecycle Policy](architecture/adr/adr_26021_content_lifecycle_policy_for_rag_consumed.md), [ADR-26022: GitHub Pages Hosting](architecture/adr/adr_26022_standardization_of_public_documentation_hosting.md), [ADR-26025: RFC→ADR Workflow](architecture/adr/adr_26025_rfc_adr_workflow_formalization.md) — marking the transition from exploratory proposals to authoritative architecture.

### New Features and Articles Added

*   **Documentation-as-Code Manifesto**:
    `architecture/manifesto.md` — the foundational document that articulates what this project is: a system where documentation is the primary input for AI agents, and therefore must be treated with the same engineering rigor as production code. This is not a new idea — it is the formalization of the principle the project has been building toward since v1.0. The README was fully rewritten to reflect this identity.

*   **Automated Commit Validation & CHANGELOG Generation**:
    Before this release, commit messages were unstructured and CHANGELOG was manually curated — a process that doesn't scale and produces inconsistent results. `validate_commit_msg.py` enforces conventional commit format with structured body bullets as a commit-msg hook (68 tests). `generate_changelog.py` parses that structured history into hierarchical, grouped CHANGELOG entries (56 tests). Both read configuration from `pyproject.toml [tool.commit-convention]`, making the commit convention machine-readable and centrally managed.

*   **Format-as-Architecture v0.2.0**:
    The original article established that serialization format affects LLM attention budget. v0.2.0 adds empirical evidence: runnable `{code-cell}` blocks measuring actual BPE token costs across 4 formats with `cl100k_base` and `o200k_base` tokenizers. Now the claims are verifiable, not theoretical.

*   **ADR Section Whitelist Enforcement**:
    As the ADR count grew, inconsistent section naming crept in (e.g., "Rationale" vs. "Decision Rationale"). The whitelist (defined in `adr_config.yaml`) enforces a canonical set of section names, with conditional support (e.g., "Rejection Rationale" only for rejected ADRs) and code-fence awareness to avoid false positives on example sections inside fenced blocks.

*   **HTML/MHTML Text Extraction**:
    Working with AI models means accumulating web chat transcripts (Gemini, Qwen, ChatGPT sessions saved as HTML/MHTML). `extract_html_text.py` extracts clean text from these files — a token-saving mechanism that lets you feed conversation history to another model without the HTML overhead (36 tests, 85% coverage).

*   **Superseded Annotation in ADR Index**:
    When [ADR-26006: Agentic-Class Models](architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md) is superseded by [ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md), the generated index now shows this relationship explicitly. Without this, readers had to open each ADR to discover its status — breaking the "index as overview" contract.

### Updates in Existing Files

*   **check_adr.py**: Gains section whitelist validation, conditional section checks, duplicate section detection, and promotion gate enforcement (154 tests, 96% coverage). The most significant evolution of this script since its creation in v2.4.0.

*   **configure_repo.py**: Now auto-installs the commit-msg hook via `--hook-type commit-msg` during repository setup. This ensures new contributors get commit validation from the first commit — no manual hook installation required.

*   **README.md**: Full structural rewrite with Documentation-as-Code framing, Architectural Governance section, Hub-and-Spoke Ecosystem description, and tool-agnostic Methodology. All tool/model name references removed in favor of cognitive-role language.

*   **CLAUDE.md**: Updated with new scripts (`validate_commit_msg.py`, `generate_changelog.py`), tool configuration conventions ([ADR-26029: pyproject.toml as Tool Config Hub](architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)), ADR index management rules, and de-emphasized tool-specific references.

*   **CI/CD**: `deploy.yml` gated to `main` branch only — previously, pushes to any branch could trigger deployment. `quality.yml` gains dedicated test jobs for `validate_commit_msg.py` and `generate_changelog.py`.

### Existing Files Moved or Renamed

| Original | New |
| :--- | :--- |
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` | `multi_phase_ai_pipeline.md` (rewritten as tool-agnostic) |
| `misc/research/slm_from_scratch/` | Extracted to dedicated research monorepo ([ADR-26026: Dedicated Research Monorepo](architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)) |
| `BROKEN_LINKS_EXCLUDE_DIRS` (in `paths.py` + 10 files) | `VALIDATION_EXCLUDE_DIRS` |
| [ADR-26004: Agentic RAG](architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md), [ADR-26005: Aider as Primary Orchestrator](architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md) | Rejected (tool-agnostic shift) |
| [ADR-26006: Agentic-Class Models](architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md), [ADR-26007: Phase 0 Intent Synthesis](architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md), [ADR-26008: Reasoning-Class Models](architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) | Superseded by [ADR-26027: Model Taxonomy](architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md), [ADR-26028: Tool-Agnostic Phase 0](architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md) |

## release v2.4.0 "The Governed Architecture"

### Summary of Changes

This release shifts the project from a curated knowledge base to a **self-governing documentation ecosystem**. Every architectural decision now carries machine-readable metadata, enabling automated quality gates, RAG-aware lifecycle management, and reproducible validation — the same rigor we apply to production code, now applied to the knowledge base itself.

Three strategic themes define v2.4.0:

1. **Governance** — 7 new ADRs (26016–26022) and a full migration of all existing records establish a metadata-driven lifecycle where decisions are queryable, filterable, and auditable by both humans and AI agents.
2. **Ecosystem extraction** — The vadocs validation engine graduated from an in-repo prototype to a standalone package, proving the hub-spoke model where this repo serves as the standards hub and extracted tools become independent spokes.
3. **Content quality** — A formal content lifecycle policy now ensures that outdated articles are retired rather than left to mislead RAG pipelines, while two new companion articles deepen the Context layer.

### New Features and Articles Added

*   **Machine-Readable ADR Governance**:
    Every ADR now carries YAML frontmatter with status, date, and tags — making the entire decision history searchable by AI agents and filterable in RAG pipelines. The new `check_adr.py` enforces this standard automatically, catching formatting drift before it reaches the main branch.

*   **Content Lifecycle Policy (ADR-26021)**:
    Superseded articles are now deleted rather than accumulating as stale context. This directly improves RAG retrieval quality — AI agents no longer surface outdated patterns when querying the knowledge base. Git history serves as the archive.

*   **Hub-Spoke Ecosystem (ADR-26020)**:
    Establishes this repository as the architectural standards hub. Extracted packages (like vadocs) maintain their own implementation decisions while inheriting ecosystem-wide conventions. This enables teams to adopt individual tools without importing the entire monorepo.

*   **vadocs — Documentation Validation Engine**:
    Completed its full lifecycle within this release: designed, scaffolded, tested, and [extracted to its own repository](https://github.com/lefthand67/vadocs). Validates ADR structure, frontmatter completeness, and MyST cross-references — the same checks that protect this repo, now available to any documentation project.

*   **GitHub Pages Hosting (ADR-26022)**:
    Replaces the self-hosted Podman/Traefik/Nginx stack with GitHub Pages. Eliminates infrastructure maintenance, improves uptime, and simplifies the deployment pipeline to a single `myst build --html` step in CI.

*   **Layer 5 — Context (New Articles)**:
    *   `reflected_metadata_pattern.md` — Explains why custom YAML fields vanish from the published site and how the reflected-metadata pattern preserves them for both humans and machines.
    *   `yaml_frontmatter_for_ai_enabled_engineering.md` — Practical guide to designing frontmatter schemas that serve documentation builds, RAG retrieval, and CI validation simultaneously.

*   **Layer 2 — Model (Rewrite)**:
    *   `choosing_model_size.md` rewritten as a VRAM budgeting guide — now covers KV Cache sizing, quantization trade-offs, and production deployment patterns (Verifier Cascade, Hybrid Routing) aligned with the `aidx` pipeline and Jan 2026 model landscape.

### Updates in Existing Files

*   **ADR Migration**: All 17 existing ADRs standardized with YAML frontmatter and consistent formatting. The ADR index is now partitioned by status (Active Architecture vs. Evolutionary Proposals), making it easier to distinguish proven decisions from proposals under evaluation.

*   **Cross-Reference Integrity**: Fixed broken MyST `{term}` references across 14 files. These caused silent build errors — terms like `ADR 26001` failed to resolve because the glossary uses hyphenated `ADR-26001`. The new `--check-terms` flag prevents future regressions.

*   **ADR-26019 Corrected**: The original decision described an HTML-anchor mechanism that was never implemented. Rewritten to formalize the positional pattern already in use across 20+ articles — documenting what actually works rather than aspirational infrastructure.

*   **CI/CD Pipeline**: Updated for the `check_adr_index.py` → `check_adr.py` transition. `misc/` excluded from broken-link validation to prevent false positives on planning documents.

*   **Development Standards (CLAUDE.md)**: Strengthened TDD guidance (tests-first, Red → Green → Refactor) and added non-brittle test quality standards — test the contract, not the implementation.

*   **Onboarding**: Updated with metadata conventions section so new contributors understand the frontmatter requirements from day one.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `tools/scripts/check_adr_index.py` | `tools/scripts/check_adr.py` (Rewritten) |
| `tools/tests/test_check_adr_index.py` | `tools/tests/test_check_adr.py` (Rewritten) |
| `tools/docs/scripts_instructions/check_adr_index_py_script.md` | `tools/docs/scripts_instructions/check_adr_py_script.md` (Rewritten) |
| `packages/vadoc/*` | *Extracted to [github.com/lefthand67/vadocs](https://github.com/lefthand67/vadocs)* |
| `ai_system/4_orchestration/patterns/llm_usage_patterns.md` | *Deleted per ADR-26021 content lifecycle policy* |

## release v2.3.0 "The Validated Ecosystem"

### Summary of Changes

This release introduces a rigorous **"Semantic Notebook Versioning"** strategy, fundamentally changing how we handle Jupyter notebooks to make them AI-friendly and git-diff clean.

We have formalized the **"Script Suite"** concept (Code + Test + Doc) with automated enforcement to prevent documentation drift. Additionally, core tooling (`prepare_prompt`, `configure_repo`) has been refactored from Bash to Python for cross-platform reliability and better testability.

We also introduce **Just-in-Time prompt transformation** script to keep our repository clean of derivative artifacts, ensuring a Single Source of Truth (SSoT) for our prompt infrastructure.

### New Features and Articles Added

*   **Architecture & Standards**:
  *   **Semantic Notebook Pairing**: Adopted Jupytext to pair `.ipynb` files with `.md` files. This allows for clean git diffs and efficient LLM processing while preserving execution state. See `architecture/adr/adr_26014_semantic_notebook_pairing_strategy.md`.
  *   **Mandatory Script Suite**: Formalized the requirement that every utility script must have a corresponding test and documentation file, enforcedby CI. See `architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md`.
  *   **JIT Prompt Transformation**: Moved from storing YAML prompts to generating them on-the-fly from JSON source of truth to prevent artifact drift. See `architecture/adr/adr_26013_just_in_time_prompt_transformation.md`.
  *   **Docs Validation Engine**: Proposed extraction of validation logic into a standalone package for reuse. See `architecture/adr/adr_26012_extraction_of_docs_validation_engine.md`.

*   **Performance & Execution**:
  *   Added `1_execution/hybrid_cpu_gpu_execution_and_kv_cache_offloading.md` for advanced optimization strategies.

*   **Tooling Ecosystem Overhaul**:
  *   `check_script_suite.py`: A new validator that enforces the 1:1:1 rule (Script, Test, Doc) and ensures documentation is co-staged with code changes.
  *   `check_adr_index.py`: Automates the maintenance of `architecture/adr_index.md`, ensuring all ADRs are indexed, ordered, and correctly linked.
  *   `check_link_format.py`: Enforces the rule that Markdown files should link to `.ipynb` files (not `.md`) when a pair exists, ensuring correct rendering in the documentation site.
  *   `prepare_prompt.py`: A Python rewrite of the prompt preparation tool, now supporting JSON, YAML, TOML, and Markdown inputs with auto-detection.
  *   `configure_repo.py`: A Python rewrite of the setup script, adding dry-run capabilities and better error handling for environment provisioning.
  *   `jupytext_sync.py` & `jupytext_verify_pair.py`: Updated to fully support the Semantic Notebook Pairing strategy, ensuring consistent synchronization and staging of paired files.

*   **Documentation**:
  *   Added comprehensive instructions for all new and refactored scripts in `tools/docs/scripts_instructions/`, including `prepare_prompt.py`, `configure_repo.py`, `check_script_suite.py`, `check_adr_index.py`, `check_link_format.py`, `jupytext_sync.py`, and `jupytext_verify_pair.py`.
  *   Added `docs_validation_engine_development_plan.md` outlining the roadmap for tooling extraction.

### Updates in Existing Files

*   **CI/CD & Quality**:
  *   Updated `.pre-commit-config.yaml` and `quality.yml` to include the new validators (`check_script_suite`, `check_adr_index`, `check_link_format`)and enhance existing checks.
  *   Enhanced `check_api_keys.py` with file exclusion lists to prevent false positives in test files.
  *   Updated `check_broken_links.py` to scan all Markdown files in CI, preventing regression when files are renamed.
  *   **Dependency Management**: Updated `pyproject.toml` and `uv.lock` to reflect new and updated project dependencies.

*   **Project Configuration**:
  *   Updated `CONVENTIONS.md` and `CLAUDE.md` to reflect the new MyST, Jupytext, and Script Suite guidelines, providing clearer instructions for AI assistants and developers.
  *   Updated `0_intro/00_onboarding.md` to streamline the setup process and reference the new `configure_repo.py` script.
  *   Refactored `ai_system/3_prompts/README.md` to align with the "Prompts-as-Infrastructure" approach, detailing the use of structured prompt files and the `prepare_prompt.py` script.
  *   Updated `tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md` with detailed guidance on the new notebook pairing strategy, Git attributes, and pre-commit sync guards.
  *   Updated `tools/docs/scripts_instructions/README.md` to provide an overview of the new script suite and how to use the refactored Python scripts.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `security/password_management/*` | `misc/in_progress/security/password_management/*` |
| `tools/docs/scripts_instructions/precommit_ci_validation_system.md` | `tools/docs/git/03_precommit_ci_validation_system.md` |
| `ai_system/3_prompts/prepare_prompt.sh` | `tools/scripts/prepare_prompt.py` (Refactored) |
| `tools/scripts/configure_repo.sh` | `tools/scripts/configure_repo.py` (Refactored) |

## v2.2.0 "The Hardened Foundation"

### Summary of Changes

This release focuses on 
- security hardening, 
- CI/CD infrastructure improvements, and 
- repository reorganization.

Key updates include:
- the introduction of automated API key and JSON validation, 
- comprehensive documentation for secret management (including Ansible Vault and Shamir's Secret Sharing), and 
- the adoption of Ansible and Molecule for infrastructure automation.

Research materials and prompt consultants have been relocated to better align with the project's layered architecture.

### New Features and Articles Added

* **Security & Secret Management**:
    * Added `security/password_management/` containing guides on Ansible Vault setup, Shamir's Secret Sharing for digital safes, and AES-256 standards (polish needed, though).
* **Automated Validation Tooling**:
    * Introduced `tools/scripts/check_api_keys.py` to detect and prevent secret leakage.
    * Introduced `tools/scripts/check_json_files.py` to ensure configuration file integrity.
    * Added comprehensive documentation and test suites for both new validation scripts.
* **Infrastructure as Code**:
    * Added `architecture/adr/adr_26009_adoption_of_ansible_for_idempotent_confi.md`.
    * Added `architecture/adr/adr_26010_adoption_of_molecule_for_automated_ansib.md`.
* **Prompt Infrastructure**:
    * Added `ai_system/3_prompts/layer_3_prompts_as_infrastructure.md` and `ai_system/3_prompts/prepare_prompt.sh` for automated prompt sanitization.

### Updates in Existing Files

* **CI/CD Pipeline**: Refactored `.github/workflows/quality.yml` into modular jobs with file-change detection and added Jupytext synchronization validation.
* **Onboarding**: Updated `0_intro/00_onboarding.md` with a high-level architectural overview and documentation structure reference.
* **Link Validation**:
    * Updated `tools/scripts/check_broken_links.py` to resolve the git root as a basename for cleaner reporting.
    * `.md` files are default now.
* **Conventions**: Updated `CONVENTIONS.md` to mandate atomic commits.
* **Documentation Rendering**: Updated `myst.yml` to exclude research files from the main documentation build.

### Existing Files Moved or Renamed

| Original Path | New Path |
| :--- | :--- |
| `research/slm_from_scratch/` | `misc/research/slm_from_scratch/` |
| `tools/prompt_helpers/` | `ai_system/3_prompts/consultants/` |
| `tools/templates/Release_Notes.tmpl` | `ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl` |
| `tools/scripts/release_notes_data.sh` | `ai_system/4_orchestration/workflows/release_notes_generation/release_notes_data.sh` |
| `tools/scripts/sync_and_verify.py` | *Removed (replaced by jupytext_sync.py)* |

## v2.1.0 "The Agentic Architect"

### **Summary of Changes**

The update includes

* a new naming convention for Architecture Decision Records (ADRs),
* enhanced automated linting for MyST include directives via `tools/scripts/check_broken_links.py`, and
* comprehensive documentation for connecting to LLMs via free-tier API keys.

One of the **major advancements** is the presentation of the `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` called `aidx` ("aider extended"), transitioning toward a formal "Architect/Editor" model selection strategy where the Architect is a capable cloud model and the editor is the small local model.

Significant work was also done on repository stabilization, including fixing broken link detection and refining pre-commit hook logic in `.pre-commit-config.yaml`.

### **New Features and Articles Added**

The new ADRs are aimed at equipping the developer with the right tools for effective development workflow backed by AI tools.

* **Architecture Decision Records (ADRs)** in  `architecture/adr/`:
    * `adr_26004`: Implementation of Agentic RAG for Autonomous Knowledge Retrieval.
    * `adr_26005`: Formalization of Aider as the primary agentic editor.
    * `adr_26006`: Mandating Agentic-Class models (e.g., Gemini 3 Flash) for the Architect Phase.
    * `adr_26007`: Formalization of Phase 0: Intent Synthesis.
    * `adr_26008`: Selection of Reasoning-Class models for Abstract Synthesis.
    * `adr_index.md`: Created a centralized index for all architectural decisions.

The new articles support ADRs:

* **Model Selection & Orchestration** in `ai_system/`:
    * Added `2_model/selection/general_purpose_vs_agentic_models.md` article to guide model selection for Requirements Engineering vs. Implementation.
    * Added the `4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` documentation, detailing the Research-Apply pipeline.

Other articles covering daily work of the developer:

* **Documentation & AI Tools** in `tools/docs/ai_agents/`:
    * New guide: `03_vim_ollama_llm_tab_completion_nuances.md` covering LLM-based tab completion.
    * New guide: `04_connect_to_capable_llms_using_api_keys.md` providing detailed setup and usage limits for Gemini, GROQ, and OpenRouter.

* **Tooling**:
    * Added `tools/templates/Release_Notes.tmpl` for standardized release documentation.
    * Added Aider-specific configuration files `tools/configs/aider.conf.yml`. This config is now added to `.gitignore` and is installed locally to the dev working tree via `tools/scripts/configure_repo.sh`.
    * Added `misc/pr/tg_channel_ai_learning/2026_01_12_release_announcement_v2_0_0.md` for external communications.

### **Updates in Existing Files**

* **Onboarding**: Updated `0_intro/00_onboarding.md` to include references to the new ADR structure and renamed sections to emphasize essential reading and AI tool proficiency.
* **Broken Link Script**:
    * Updated `tools/scripts/check_broken_links.py` to support MyST `{include}` directive validation.
    * Fixed nested directory exclusion logic and improved verbose logging in `tools/tests/test_check_broken_links.py`.
    * Integrated a global check in `.pre-commit-config.yaml` to ensure renamed files don't break external references.

* **Aider Handout**: Updated `tools/docs/ai_agents/02_aider_commands_handout.md` with OpenRouter integration, updated model flags, and usage limit tables.
* **Configurations**:
    * `pyproject.toml`: Added `pytest-cov` library.
    * `.aider.conf.yml`: Set `map-tokens: 2048` to optimize repository map limits.
    * `myst.yml`: Updated to exclude specific Aider convention files.
    * `uv.lock`: Updated dependencies.

### Existing Files Moved or Renamed

| Original Path | New Path |
| --- | --- |
| `aider.CONVENTIONS` | `CONVENTIONS.md` |
| `architecture/adr/adr_0001_use_of_python_and_oop_for_git_hook_scripts.md` | `architecture/adr/adr_26001_use_of_python_and_oop_for_git_hook_scripts.md` |
| `architecture/adr/adr_0002_adoption_of_pre_commit_framework.md` | `architecture/adr/adr_26002_adoption_of_pre_commit_framework.md` |
| `architecture/adr/adr_0003_adoption_of_gitlint_for_tiered_workflow.md` | `architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md` |
| `architecture/adr/0001-template.md` | `architecture/adr/adr_template.md` |


## v2.0.0

### Summary of Changes

This release focuses on a major architectural restructuring to improve the separation of concerns between core AI system documentation and the operational processes surrounding it. 

A primary **ai_system** directory has been established to house the layered documentation (Execution, Model, Infrastructure, etc.). 

Additionally, this update introduces enhanced CI/CD quality gates, improved repository configuration for local development, and formalizes the project's licensing structure.

### Major Structural Changes

#### File Tree Refactor (REFACTOR-MIGRATION)

* **AI Layered Docs Migration**: The core architectural layers have been moved to the `ai_system/` directory to decouple the "what" (AI logic) from the "how" (process/tooling).
    * `1_execution/` → `ai_system/1_execution/`
* **Operational Tooling Consolidation**: The developer's tools, helper prompts, internal scripts and tests have been reorganized under `tools/`.

All less important stuff like drafts and public relations materials moved to `misc/`.

### MLOps and Repository Tooling

#### CI/CD and Quality Assurance

* **Pre-commit Hooks**: Added local hooks for broken link validation and script testing .
* **GitHub Actions:**
    * **New Workflow**: `quality.yml` introduced to automate broken link checks on pull requests and commits using `pytest` and custom scripts .
    * **Deployment Improvements**: The `deploy.yml` workflow now includes mandatory environment integrity checks using `uv` and notebook synchronization verification with `jupytext` .

#### Developer Experience

* **Aider Handout Expanded:** "Aider Integration with LLMs Using API Keys" workflow introduced in ["Aider Commands Handout"](/tools/docs/ai_agents/02_aider_commands_handout.ipynb).
* **Aider Configuration**: New `.aider.conf.yml` to automate Jupytext synchronization during AI-assisted coding sessions .
* **Deps updates**: New environment dependency added - `tiktoken` for analyzing token efficiency of our system prompts. 

### Changes to Existing Files

#### Licensing

* **LICENSE.md**: Updated to clarify the split-licensing model—GPLv3 for software/scripts and CC-BY-SA 4.0 for documentation/articles.


## v1.4.0

### Summary of Changes

This release significantly expands the **1_execution** and **4_orchestration** layers with deep-dives into high-performance computing standards (GEMM) and advanced MLOps architectural patterns. It also introduces a formal grounding of AI disciplines in alignment with ACM/IEEE curricula. A new GitHub Actions deployment workflow has been implemented to automate documentation builds using MyST.

### New Features and Articles Added

#### Foundation and Grounding

* **Directory**: `0_intro`
* **Articles**:
  *  `ai_systems_grounding_in_computing_disciplines.md`: Maps the AI lifecycle to global computing curricula standards.
  *  `ai_systems_grounding_in_computing_disciplines_diagram.png`: Visual representation of AI as a convergent layer of engineering and science.

#### Execution Layer (HPC Standards)

* **Directory**: `1_execution`
* **Articles**:
  *  `algebra_gemm_engineering_standard.md`:
    * Defines GEMM as the foundational standard for Deep Learning and HPC.
    * Includes detailed analysis of arithmetic intensity, tiling, and hardware-specific optimizations like Tensor Cores.

#### Orchestration and MLOps Workflows

* **Directory**: `4_orchestration/workflows`
* **Articles**:
  * `slm_backed_release_documentation_pipeline_architecture.md`: Describes modular processing and generation blocks for automated documentation.
  * `post-mortem_slm_non-determinism_in_commit_generation.md`: A critical analysis of why Small Language Models (1B-3B) struggle with high-frequency structured tasks in production.
  * `requirements_engineering_in_the_ai_era_the_gated_velocity.md`: Introduces the "Gated Velocity" pipeline for AI-assisted requirement flows.

#### Infrastructure and Tooling

* **Deployment**: Added `.github/workflows/deploy.yml` to automate MyST HTML builds and RSYNC deployment to production servers.
* **Scripts**: Added `md_check_broken_links.py` to maintain documentation integrity across the repository.

### Articles Moved or Renamed

To align with the new thematic structure, several files were reorganized:

| Original Path | New Path |
| --- | --- |
| `tools/vim/ai_tools_in_vim.md` | `tools/ai_agents/ai_tools_in_vim.md` |
| `tools/vim/handout_aider.md` | `tools/ai_agents/handout_aider.md` |
| `tools/python314_parallelism_game_changer.md` | `tools/languages/python314_parallelism_game_changer.md` |

### Improvements to Existing Content

* **ai_further_reading.md**: Updated with new sections for Small Language Models (SLMs) and modern agentic tools like CrewAI and Aider.
* **README.md**: Updated tree structure to reflect new specialized subdirectories in `tools/` and `4_orchestration/`.
* **Security Documentation**: Enhanced sections on OWASP Top-10 for LLMs and prompt injection mitigation.


## v1.3.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on MLOps workflows and Vim tools for AI-driven tasks. Additionally, it moves several existing articles to more appropriate locations.

### New Features and Articles Added

#### MLOps Workflows

- **Directory**: `mlops/workflows`
- **Articles**:
  - `git_three_major_workflows.md`: Provides a detailed comparison of three major Git workflows: Integration Manager, Gitflow, and GitHub Flow.

#### AI Tools for Vim

- **Directory**: `tools/vim`
- **Articles**:
  - `ai_tools_in_vim.md`: Describes how to set up Vim for AI-driven tasks using plugins like `gergap/vim-ollama` and CLI tools like Aider.
  - `handout_aider.md`: Provides a handout of essential Aider commands and usage instructions.

### Articles Moved

| Original Path | New Path |
| :--- | :--- |
| `2_model/training/python314_parallelism_game_changer.md` | `tools/python314_parallelism_game_changer.md` |
| `2_model/training/right_tool_for_right_layer.md` | `tools/right_tool_for_right_layer.md` |
| `2_model/training/why_rust_for_tokenizers.md` | `tools/why_rust_for_tokenizers.md` |
| `4_orchestration/patterns/llm_usage_patterns_p1.md` | `4_orchestration/patterns/llm_usage_patterns.md` |
| `4_orchestration/patterns/llm_usage_patterns_p2.md` | `2_model/selection/choosing_model_size.md` |

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.3.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.3.0 detailing the new articles, moved articles, and directory additions.


## v1.2.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on general AI systems, introductory materials, and orchestration patterns.

### New Features and Articles Added

#### General and Introductory Materials
- **Directory**: `0_intro`
- **Articles**:
  - `ai_systems_multilayer_approach.md`: Describes a multi-layered approach to building AI systems with DevSecOps considerations.

#### Orchestration Patterns
- **Directory**: `4_orchestration/patterns`
- **Articles**:
  - `llm_usage_patterns_p1.md`: Discusses the core distinctions between chats, workflows, and agents in AI.
  - `llm_usage_patterns_p2.md`: Explores model size considerations for chats, workflows, and agents, including Schema-Guided Reasoning (SGR).

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.2.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.2.0 detailing the new articles, moved articles, and directory additions.


## v1.1.0

### New Features and Articles Added

#### Model Training
- **Directory**: `2_model/training`
- **Articles**:
  - `custom_tokenizer_and_embedding.md`: Guide on creating custom tokenizers and embeddings.
  - `why_rust_for_tokenizers.md`: Discusses the benefits of using Rust for tokenizers.
  - `right_tool_for_right_layer.md`: Provides guidance on choosing the right tools for different layers in AI stack.
  - `python314_parallelism_game_changer.md`: Highlights the improvements in Python 3.14 for parallelism.


## v1.0.0

### Initial Release
- **Tree Structure Prepared**: The repository structure was prepared to accommodate new articles.
- **Articles Added**:
  - `nvidia_gpu_optimization.md` under `1_execution`.
  - `embeddings_for_small_llms.md` under `2_model`.


## v2.1.0

### **Summary of Changes**

The update includes

* a new naming convention for Architecture Decision Records (ADRs),
* enhanced automated linting for MyST include directives via `tools/scripts/check_broken_links.py`, and
* comprehensive documentation for connecting to LLMs via free-tier API keys.

One of the **major advancements** is the presentation of the `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` called `aidx` ("aider extended"), transitioning toward a formal "Architect/Editor" model selection strategy where the Architect is a capable cloud model and the editor is the small local model.

Significant work was also done on repository stabilization, including fixing broken link detection and refining pre-commit hook logic in `.pre-commit-config.yaml`.

### **New Features and Articles Added**

The new ADRs are aimed at equipping the developer with the right tools for effective development workflow backed by AI tools.

* **Architecture Decision Records (ADRs)** in  `architecture/adr/`:
    * `adr_26004`: Implementation of Agentic RAG for Autonomous Knowledge Retrieval.
    * `adr_26005`: Formalization of Aider as the primary agentic editor.
    * `adr_26006`: Mandating Agentic-Class models (e.g., Gemini 3 Flash) for the Architect Phase.
    * `adr_26007`: Formalization of Phase 0: Intent Synthesis.
    * `adr_26008`: Selection of Reasoning-Class models for Abstract Synthesis.
    * `adr_index.md`: Created a centralized index for all architectural decisions.

The new articles support ADRs:

* **Model Selection & Orchestration** in `ai_system/`:
    * Added `2_model/selection/general_purpose_vs_agentic_models.md` article to guide model selection for Requirements Engineering vs. Implementation.
    * Added the `4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` documentation, detailing the Research-Apply pipeline.

Other articles covering daily work of the developer:

* **Documentation & AI Tools** in `tools/docs/ai_agents/`:
    * New guide: `03_vim_ollama_llm_tab_completion_nuances.md` covering LLM-based tab completion.
    * New guide: `04_connect_to_capable_llms_using_api_keys.md` providing detailed setup and usage limits for Gemini, GROQ, and OpenRouter.

* **Tooling**:
    * Added `tools/templates/Release_Notes.tmpl` for standardized release documentation.
    * Added Aider-specific configuration files `tools/configs/aider.conf.yml`. This config is now added to `.gitignore` and is installed locally to the dev working tree via `tools/scripts/configure_repo.sh`.
    * Added `misc/pr/tg_channel_ai_learning/2026_01_12_release_announcement_v2_0_0.md` for external communications.

### **Updates in Existing Files**

* **Onboarding**: Updated `0_intro/00_onboarding.md` to include references to the new ADR structure and renamed sections to emphasize essential reading and AI tool proficiency.
* **Broken Link Script**:
    * Updated `tools/scripts/check_broken_links.py` to support MyST `{include}` directive validation.
    * Fixed nested directory exclusion logic and improved verbose logging in `tools/tests/test_check_broken_links.py`.
    * Integrated a global check in `.pre-commit-config.yaml` to ensure renamed files don't break external references.

* **Aider Handout**: Updated `tools/docs/ai_agents/02_aider_commands_handout.md` with OpenRouter integration, updated model flags, and usage limit tables.
* **Configurations**:
    * `pyproject.toml`: Added `pytest-cov` library.
    * `.aider.conf.yml`: Set `map-tokens: 2048` to optimize repository map limits.
    * `myst.yml`: Updated to exclude specific Aider convention files.
    * `uv.lock`: Updated dependencies.

### Existing Files Moved or Renamed

| Original Path | New Path |
| --- | --- |
| `aider.CONVENTIONS` | `CONVENTIONS.md` |
| `architecture/adr/adr_0001_use_of_python_and_oop_for_git_hook_scripts.md` | `architecture/adr/adr_26001_use_of_python_and_oop_for_git_hook_scripts.md` |
| `architecture/adr/adr_0002_adoption_of_pre_commit_framework.md` | `architecture/adr/adr_26002_adoption_of_pre_commit_framework.md` |
| `architecture/adr/adr_0003_adoption_of_gitlint_for_tiered_workflow.md` | `architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md` |
| `architecture/adr/0001-template.md` | `architecture/adr/adr_template.md` |


## v2.0.0

### Summary of Changes

This release focuses on a major architectural restructuring to improve the separation of concerns between core AI system documentation and the operational processes surrounding it. 

A primary **ai_system** directory has been established to house the layered documentation (Execution, Model, Infrastructure, etc.). 

Additionally, this update introduces enhanced CI/CD quality gates, improved repository configuration for local development, and formalizes the project's licensing structure.

### Major Structural Changes

#### File Tree Refactor (REFACTOR-MIGRATION)

* **AI Layered Docs Migration**: The core architectural layers have been moved to the `ai_system/` directory to decouple the "what" (AI logic) from the "how" (process/tooling).
    * `1_execution/` → `ai_system/1_execution/`
* **Operational Tooling Consolidation**: The developer's tools, helper prompts, internal scripts and tests have been reorganized under `tools/`.

All less important stuff like drafts and public relations materials moved to `misc/`.

### MLOps and Repository Tooling

#### CI/CD and Quality Assurance

* **Pre-commit Hooks**: Added local hooks for broken link validation and script testing .
* **GitHub Actions:**
    * **New Workflow**: `quality.yml` introduced to automate broken link checks on pull requests and commits using `pytest` and custom scripts .
    * **Deployment Improvements**: The `deploy.yml` workflow now includes mandatory environment integrity checks using `uv` and notebook synchronization verification with `jupytext` .

#### Developer Experience

* **Aider Handout Expanded:** "Aider Integration with LLMs Using API Keys" workflow introduced in ["Aider Commands Handout"](/tools/docs/ai_agents/02_aider_commands_handout.ipynb).
* **Aider Configuration**: New `.aider.conf.yml` to automate Jupytext synchronization during AI-assisted coding sessions .
* **Deps updates**: New environment dependency added - `tiktoken` for analyzing token efficiency of our system prompts. 

### Changes to Existing Files

#### Licensing

* **LICENSE.md**: Updated to clarify the split-licensing model—GPLv3 for software/scripts and CC-BY-SA 4.0 for documentation/articles.


## v1.4.0

### Summary of Changes

This release significantly expands the **1_execution** and **4_orchestration** layers with deep-dives into high-performance computing standards (GEMM) and advanced MLOps architectural patterns. It also introduces a formal grounding of AI disciplines in alignment with ACM/IEEE curricula. A new GitHub Actions deployment workflow has been implemented to automate documentation builds using MyST.

### New Features and Articles Added

#### Foundation and Grounding

* **Directory**: `0_intro`
* **Articles**:
  *  `ai_systems_grounding_in_computing_disciplines.md`: Maps the AI lifecycle to global computing curricula standards.
  *  `ai_systems_grounding_in_computing_disciplines_diagram.png`: Visual representation of AI as a convergent layer of engineering and science.

#### Execution Layer (HPC Standards)

* **Directory**: `1_execution`
* **Articles**:
  *  `algebra_gemm_engineering_standard.md`:
    * Defines GEMM as the foundational standard for Deep Learning and HPC.
    * Includes detailed analysis of arithmetic intensity, tiling, and hardware-specific optimizations like Tensor Cores.

#### Orchestration and MLOps Workflows

* **Directory**: `4_orchestration/workflows`
* **Articles**:
  * `slm_backed_release_documentation_pipeline_architecture.md`: Describes modular processing and generation blocks for automated documentation.
  * `post-mortem_slm_non-determinism_in_commit_generation.md`: A critical analysis of why Small Language Models (1B-3B) struggle with high-frequency structured tasks in production.
  * `requirements_engineering_in_the_ai_era_the_gated_velocity.md`: Introduces the "Gated Velocity" pipeline for AI-assisted requirement flows.

#### Infrastructure and Tooling

* **Deployment**: Added `.github/workflows/deploy.yml` to automate MyST HTML builds and RSYNC deployment to production servers.
* **Scripts**: Added `md_check_broken_links.py` to maintain documentation integrity across the repository.

### Articles Moved or Renamed

To align with the new thematic structure, several files were reorganized:

| Original Path | New Path |
| --- | --- |
| `tools/vim/ai_tools_in_vim.md` | `tools/ai_agents/ai_tools_in_vim.md` |
| `tools/vim/handout_aider.md` | `tools/ai_agents/handout_aider.md` |
| `tools/python314_parallelism_game_changer.md` | `tools/languages/python314_parallelism_game_changer.md` |

### Improvements to Existing Content

* **ai_further_reading.md**: Updated with new sections for Small Language Models (SLMs) and modern agentic tools like CrewAI and Aider.
* **README.md**: Updated tree structure to reflect new specialized subdirectories in `tools/` and `4_orchestration/`.
* **Security Documentation**: Enhanced sections on OWASP Top-10 for LLMs and prompt injection mitigation.


## v1.3.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on MLOps workflows and Vim tools for AI-driven tasks. Additionally, it moves several existing articles to more appropriate locations.

### New Features and Articles Added

#### MLOps Workflows

- **Directory**: `mlops/workflows`
- **Articles**:
  - `git_three_major_workflows.md`: Provides a detailed comparison of three major Git workflows: Integration Manager, Gitflow, and GitHub Flow.

#### AI Tools for Vim

- **Directory**: `tools/vim`
- **Articles**:
  - `ai_tools_in_vim.md`: Describes how to set up Vim for AI-driven tasks using plugins like `gergap/vim-ollama` and CLI tools like Aider.
  - `handout_aider.md`: Provides a handout of essential Aider commands and usage instructions.

### Articles Moved

| Original Path | New Path |
| :--- | :--- |
| `2_model/training/python314_parallelism_game_changer.md` | `tools/python314_parallelism_game_changer.md` |
| `2_model/training/right_tool_for_right_layer.md` | `tools/right_tool_for_right_layer.md` |
| `2_model/training/why_rust_for_tokenizers.md` | `tools/why_rust_for_tokenizers.md` |
| `4_orchestration/patterns/llm_usage_patterns_p1.md` | `4_orchestration/patterns/llm_usage_patterns.md` |
| `4_orchestration/patterns/llm_usage_patterns_p2.md` | `2_model/selection/choosing_model_size.md` |

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.3.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.3.0 detailing the new articles, moved articles, and directory additions.


## v1.2.0

### Summary of Changes
This release introduces several new articles and directories to enhance the documentation on general AI systems, introductory materials, and orchestration patterns.

### New Features and Articles Added

#### General and Introductory Materials
- **Directory**: `0_intro`
- **Articles**:
  - `ai_systems_multilayer_approach.md`: Describes a multi-layered approach to building AI systems with DevSecOps considerations.

#### Orchestration Patterns
- **Directory**: `4_orchestration/patterns`
- **Articles**:
  - `llm_usage_patterns_p1.md`: Discusses the core distinctions between chats, workflows, and agents in AI.
  - `llm_usage_patterns_p2.md`: Explores model size considerations for chats, workflows, and agents, including Schema-Guided Reasoning (SGR).

### Changes to Existing Files

#### README.md
- **Updated Structure**: The repository structure has been updated to reflect the new articles and directories added in version 1.2.0.

#### CHANGELOG
- **New Release Entry**: Added an entry for release 1.2.0 detailing the new articles, moved articles, and directory additions.


## v1.1.0

### New Features and Articles Added

#### Model Training
- **Directory**: `2_model/training`
- **Articles**:
  - `custom_tokenizer_and_embedding.md`: Guide on creating custom tokenizers and embeddings.
  - `why_rust_for_tokenizers.md`: Discusses the benefits of using Rust for tokenizers.
  - `right_tool_for_right_layer.md`: Provides guidance on choosing the right tools for different layers in AI stack.
  - `python314_parallelism_game_changer.md`: Highlights the improvements in Python 3.14 for parallelism.


## v1.0.0

### Initial Release
- **Tree Structure Prepared**: The repository structure was prepared to accommodate new articles.
- **Articles Added**:
  - `nvidia_gpu_optimization.md` under `1_execution`.
  - `embeddings_for_small_llms.md` under `2_model`.
