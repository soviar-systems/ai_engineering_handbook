# AI System Layers — Component Catalog

This directory is an **engine parts catalog** — each layer represents a deliberate component boundary in the architecture of production-grade AI systems.

Layers are components that compose into an AI agent. The agent itself lives at repo root in `ai_agents/` — the assembled product, not another layer.

## The Five Layers

| Layer | Directory | Focus |
|-------|-----------|-------|
| 1 | `1_execution/` | CPU/GPU optimization, VRAM/RAM management, CUDA pipelines |
| 2 | `2_model/` | SLM selection, tokenization, embeddings |
| 3 | `3_prompts/` | Prompts-as-Infrastructure, consultant prompts, token economics |
| 4 | `4_orchestration/` | RAG, agent workflows, structured output |
| 5 | `5_context/` | Vector stores, hybrid retrieval, indexing strategies |

Read more in [A Multi-Layered AI System Architecture](/0_intro/a_multi_layered_ai_system_architecture.ipynb).
