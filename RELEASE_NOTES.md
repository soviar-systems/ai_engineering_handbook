# Release Notes

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
