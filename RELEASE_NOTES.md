# Release Notes

## release v1.4.0

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

## release v1.3.0

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

## release v1.2.0

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


## release v1.1.0

### New Features and Articles Added

#### Model Training
- **Directory**: `2_model/training`
- **Articles**:
  - `custom_tokenizer_and_embedding.md`: Guide on creating custom tokenizers and embeddings.
  - `why_rust_for_tokenizers.md`: Discusses the benefits of using Rust for tokenizers.
  - `right_tool_for_right_layer.md`: Provides guidance on choosing the right tools for different layers in AI stack.
  - `python314_parallelism_game_changer.md`: Highlights the improvements in Python 3.14 for parallelism.

## release v1.0.0

### Initial Release
- **Tree Structure Prepared**: The repository structure was prepared to accommodate new articles.
- **Articles Added**:
  - `nvidia_gpu_optimization.md` under `1_execution`.
  - `embeddings_for_small_llms.md` under `2_model`.
