*"The real understanding comes when we get our hands dirty and build these things"* - says my first AI mentor Richard Feynman. 

The goal of this course is a preparation for AI-backend optimization (e.g., CUDA, tensor cores, memory hierarchy tuning).

I use my own mentor prompt generated with the help from my another prompt ["mentor_generator v0.24.3"](https://github.com/lefthand67/mentor_generator) to learn LLMs under the hood by building it from scratch. The idea stems from the [Stanford CS336 course](https://www.youtube.com/playlist?list=PLoROMvodv4rOY23Y0BoGoBGgQ1zmU_MT_) but this course is interactive though it needs hallucination checks.

This is already the third mentor I regenerated for the course. I run my current mentor in free Qwen3-Max chat in no reasoning mode, previous ones were in Deepseek.

***

*"What I cannot create, I do not understand."* - Richard Feynman

Hello, and welcome. We are beginning **“Building a Small LLM from First Principles”**, a depth-first course tailored to your profile:  
- You are a strong intermediate practitioner (NumPy backprop, CNNs, DL libraries).  
- Your goal is professional readiness as an **AI Architect**, with emphasis on **CUDA-aware design** and **bare-metal understanding**.  
- You operate in two environments: a high-VRAM GPU (RTX 4090ti, 16 GB) and a CPU-only Debian 13 system—so **VRAM and latency constraints** are central to every design decision.

### Entire Learning Plan

The entire curriculum is structured into five phases, designed to take you from the fundamental neuron to a fully functional, efficient 100M parameter LLM. Here is the roadmap.

| Phase | Focus | Hands-On | Estimated Time (1h/day) |
|------|--------|----------|--------------------------|
| **Phase 1** | Foundational Neurons & Backprop | NumPy: single neuron, activation, gradient descent | 5–7 days |
| **Phase 2** | Core Transformer Components | PyTorch: tokenization, positional encoding, attention | 10–14 days |
| **Phase 3** | Optimization & Architecture | KV Cache, Flash Attention, LayerNorm, AdamW | 10–12 days |
| **Phase 4** | Training & Alignment | Dataset prep, training loop, SFT, basic PPO/DPO | 12–15 days |
| **Phase 5** | Architectural Review & Deployment | Quantization (INT8), CPU inference, full system audit | 7–10 days |

*Total estimated commitment: **~50–60 hours**, paced by **mastery**, not calendar.*

### Goals & Practical Skills

By the end, you will:
- **Architect** a 100M-parameter LLM from scratch.
- **Explain** every component down to memory layout and gradient flow.
- **Optimize** for both VRAM (4090ti) and CPU (Debian 13) constraints.
- **Defend** your design choices in an AI Architect interview with mathematical and hardware-aware reasoning.

### Administrative Notes

- Each session is **~1 hour**.
- **No deadlines**—progress is gated solely by verified understanding.
- You must **demonstrate reasoning**, not just recall. Passive acknowledgment (“I get it”) is insufficient.
- We use **one small step at a time**, with micro-validation.

## Can I run this course on the weaker laptop?

**Hardware Requirements Analysis:**

| Component | RTX 4090ti | Weaker Laptop | Impact |
|-----------|------------|---------------|---------|
| **VRAM** | 16GB | Shared system RAM (8GB total) | Limits model size and batch size |
| **Compute** | High parallel throughput | Limited CPU cores | Slower training times |
| **Memory Bandwidth** | ~1 TB/s | ~50 GB/s | Significant bottleneck for matrix ops |
| **Practical Limits** | 100M param model feasible | ~10M param model maximum | Scales final project scope |

If you proceed with the weaker laptop, we'll need to adjust:

1. **Phase 1-3**: Completely feasible - these are algorithmic implementations
2. **Phase 4**: We'll target a smaller model (~10M parameters vs 100M)
3. **Training Time**: Expect 10-50x slower execution
4. **Batch Size**: Will need to be minimal (possibly 1)

The core concepts of computational graphs, backpropagation, and transformer mechanics remain identical. The implementation principles for CUDA optimization still apply - we just won't be able to run the full-scale final project.

The mathematical understanding and architectural insights are what matter for your CUDA preparation, not the absolute scale.

**Hardware Selection Rule:**

Use **only the Lenovo Legion 7 Pro (with RTX 4090ti)** for all active development, experimentation, and implementation during the course.

The **Dell (Debian 13, CPU-only)** is reserved for **Phase 5**, when we conduct deployment analysis, latency profiling, and efficiency testing under CPU-only constraints. Introducing it earlier would add unnecessary overhead and distract from the core goal: building and understanding the LLM on a capable system first.

Therefore:  
- **Phases 1–4**: Lenovo only (GPU-enabled, Fedora 42).  
- **Phase 5**: Both systems—Lenovo for reference, Dell for efficiency validation.

This aligns with your dual-environment goal while maintaining focus on deep learning fundamentals during the build phase.
