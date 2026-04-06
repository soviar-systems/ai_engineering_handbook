# ADR Index

## **Active Architecture**

### architecture

:::{glossary}
ADR-26020
: [Hub-and-Spoke Ecosystem Documentation Architecture](/architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md)

ADR-26037
: [Smallest Viable Architecture (SVA) Constraint Framework](/architecture/adr/adr_26037_smallest_viable_architecture_constraint_framework.md)

:::

### ci

:::{glossary}
ADR-26015
: [Mandatory Sync-Guard & Diff Suppression](/architecture/adr/adr_26015_mandatory_sync_guard_and_diff_suppression.md)

:::

### context_management

:::{glossary}
ADR-26038
: [Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md)

  Single-agent architecture with skill dispatch over multi-agent systems; context quality determines agent success, not orchestration complexity.

:::

### development

:::{glossary}
ADR-26045
: [AI-Native Development — Code as Primary Documentation](/architecture/adr/adr_26045_ai_native_development_code_as_primary_documentation.md)

  Contract docstrings are mandatory for all code in all languages across the ecosystem. Code structure is the primary documentation layer for both human and agent consumers.

:::

### devops

:::{glossary}
ADR-26016
: [Metadata-Driven Architectural Records Lifecycle](/architecture/adr/adr_26016_metadata_driven_architectural_records_life.md)

ADR-26022
: [Standardization of Public Documentation Hosting on GitHub Pages](/architecture/adr/adr_26022_standardization_of_public_documentation_hosting.md)

ADR-26040
: [Podman Kube YAML as Deployment Standard](/architecture/adr/adr_26040_podman_kube_yaml_as_deployment_standard.md)

:::

### documentation

:::{glossary}
ADR-26014
: [Semantic Notebook Pairing Strategy](/architecture/adr/adr_26014_semantic_notebook_pairing_strategy.md)

:::

### git

:::{glossary}
ADR-26001
: [Use of Python and OOP for Git Hook Scripts](/architecture/adr/adr_26001_use_of_python_and_oop_for_git_hook_scripts.md)

ADR-26002
: [Adoption of the Pre-commit Framework](/architecture/adr/adr_26002_adoption_of_pre_commit_framework.md)

:::

### governance

:::{glossary}
ADR-26017
: [ADR Format Validation Workflow](/architecture/adr/adr_26017_adr_format_validation_workflow.md)

ADR-26021
: [Content Lifecycle Policy for RAG-Consumed Repositories](/architecture/adr/adr_26021_content_lifecycle_policy_for_rag_consumed.md)

ADR-26023
: [MyST-Aligned Frontmatter Standard](/architecture/adr/adr_26023_myst_aligned_frontmatter_standard.md)

ADR-26025
: [RFC→ADR Workflow Formalization](/architecture/adr/adr_26025_rfc_adr_workflow_formalization.md)

ADR-26026
: [Dedicated Research Monorepo for Volatile Experimental Projects](/architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)

ADR-26029
: [pyproject.toml as Tool Configuration Hub](/architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)

ADR-26035
: [Architecture Knowledge Base Taxonomy](/architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md)

:::

### model

:::{glossary}
ADR-26027
: [Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic](/architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md)

:::

### workflow

:::{glossary}
ADR-26013
: [Just-in-Time Prompt Transformation](/architecture/adr/adr_26013_just_in_time_prompt_transformation.md)

ADR-26024
: [Structured Commit Bodies for Automated CHANGELOG Generation](/architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md)

ADR-26028
: [Tool-Agnostic Phase 0: Intent Synthesis](/architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md)

:::

## **Evolutionary Proposals**

### architecture

:::{glossary}
ADR-26041
: [Client-Side Logic with Server-Side Retrieval](/architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md)

ADR-26046
: [External Product Repos as Research Directories](/architecture/adr/adr_26046_external_product_repos_as_research_directories.md)

  Governance for directories containing nested git repos of external products used for comparative source-level research — centralized path registry with relocation safety.

:::

### context_management

:::{glossary}
ADR-26030
: [Stateless JIT Context Injection for Agentic Git Workflows](/architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md)

ADR-26032
: [Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG](/architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md)

ADR-26039
: [pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md)

ADR-26044
: [Skills as Progressive Disclosure Units](/architecture/adr/adr_26044_skills_as_progressive_disclosure_units.md)

:::

### devops

:::{glossary}
ADR-26009
: [Adoption of Ansible for Idempotent Configuration Management](/architecture/adr/adr_26009_adoption_of_ansible_for_idempotent_confi.md)

:::

### governance

:::{glossary}
ADR-26012
: [Extraction of Documentation Validation Engine](/architecture/adr/adr_26012_extraction_of_docs_validation_engine.md)

ADR-26033
: [Virtual Monorepo via Package-Driven Dependency Management](/architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md)

ADR-26036
: [Config File Location and Naming Conventions](/architecture/adr/adr_26036_config_file_location_and_naming_conventions.md)

ADR-26042
: [Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md)

ADR-26043
: [Ecosystem Package Boundary](/architecture/adr/adr_26043_ecosystem_package_boundary.md)

ADR-26054
: [JSON as Governance Config Format](/architecture/adr/adr_26054_json_as_governance_config_format.md)

:::

### testing

:::{glossary}
ADR-26010
: [Adoption of Molecule for Automated Ansible Role Validation](/architecture/adr/adr_26010_adoption_of_molecule_for_automated_ansib.md)

:::

## **Rejected**

### context_management

:::{glossary}
ADR-26004
: [Implementation of Agentic RAG for Autonomous Research](/architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md)

ADR-26034
: [Agentic OS Paradigm: Skills as Composable Applications](/architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md)

:::

### git

:::{glossary}
ADR-26003
: [Adoption of `gitlint` for Tiered Workflow Enforcement](/architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md)

  gitlint adoption for tiered Git commit validation was rejected in favor of a custom Python validator capable of the conditional Tier 3 ArchTag logic that gitlint could not express.

:::

### governance

:::{glossary}
ADR-26031
: [Prefixed Namespace System for Architectural Records](/architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md)

:::

### workflow

:::{glossary}
ADR-26005
: [Formalization of Aider as the Primary Agentic Orchestrator](/architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md)

:::

## **Superseded**

### governance

:::{glossary}
ADR-26011
: [Formalization of the Mandatory Script Suite Workflow](/architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md) — superseded by {term}`ADR-26045`

ADR-26018
: [Universal YAML Frontmatter Adoption for Machine-Readable Documentation](/architecture/adr/adr_26018_universal_yaml_frontmatter_adoption.md) — superseded by {term}`ADR-26023`

  YAML frontmatter is mandated as the universal machine-readable interface for all documentation artifacts, requiring owner, version, and last_modified fields on every file.

ADR-26019
: [Mirroring YAML Metadata to Document Body for Human Verification](/architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md) — superseded by {term}`ADR-26023`

  A pre-commit hook automatically mirrors YAML frontmatter fields into a prose reflection block in the document body, making metadata visible on the MyST-rendered static site.

:::

### model

:::{glossary}
ADR-26006
: [Requirement for Agentic-Class Models for the Architect Phase](/architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md) — superseded by {term}`ADR-26027`

  Agentic-Class models (high instruction adherence) are required for the aidx Architect phase to prevent instruction drift in generated plans.

ADR-26008
: [Selection of Reasoning-Class Models for Abstract Synthesis (Phase 0)](/architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md) — superseded by {term}`ADR-26027`

  Reasoning-Class models (high abstract synthesis) are required for Phase 0 to resolve requirements ambiguity before the aidx pipeline engages local hardware.

:::

### workflow

:::{glossary}
ADR-26007
: [Formalization of Phase 0: Intent Synthesis (Requirements Engineering)](/architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md) — superseded by {term}`ADR-26028`

  Phase 0 Intent Synthesis is a mandatory human-lead + reasoning-model gateway before any aidx session, producing a Mission artifact that grounds all subsequent phases.

:::
