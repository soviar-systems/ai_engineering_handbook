---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Choosing Model Size for Chats, Workflows, and Agents: Model Size, Reasoning, and Optimization

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.2  
Birth: 2025-10-19  
Last Modified: 2026-01-10

---

+++

The size of the Large Language Model (LLM) affects its performance, resource requirements, and suitability for specific applications. Larger models offer deeper understanding, better reasoning, and more nuanced outputs—at the cost of increased inference compute, memory, and latency.


See also: 
- [LLM Usage Patterns: Chats, Workflows, and Agents in AI](/ai_system/4_orchestration/patterns/llm_usage_patterns.md)

+++

## 1. The Decision Matrix: Tiers & Use Cases

| Pattern | Best Model Size | Why? |
| --- | --- | --- |
| **Chats** | **3B – 8B** | **Low Latency.** Users want responses in <200ms. Small models are "snappy." |
| **Workflows** | **8B – 14B** | **Consistency.** Good at following "if/then" steps without needing massive compute. |
| **Agents** | **14B – 70B+** | **Planning.** High-parameter counts are needed for tool selection and self-correction. |

+++

## 2. The "Short-Term Memory" Tax (KV Cache)

+++

When you choose a model size, you aren't just buying space for the "brain" (Weights). You are also buying space for its "short-term memory" (**KV Cache**).

* **The Problem:** If a model fits on your GPU but the conversation gets long, the model will run out of memory and crash (**OOM - Out of Memory**).
* **The Rule of Thumb:** For an 8B model, budget **~1.5GB of VRAM** for every 8,000 words (tokens) of conversation history.

+++

## 3. Schema-Guided Reasoning (SGR): The "Safety Harness"

+++

SGR is the technique of forcing a model to output a specific format (like JSON). This allows a **Small model** to behave as reliably as a **Large model**.

+++

### **The "Scratchpad" Requirement**

+++

To make SGR work, your JSON schema **must** start with a "thought" field.

> **Example:** `{"thought": "User wants a summary, I will identify key points...", "summary": "..."}`

* **Why?** It forces the model to think before it acts. Without this, small models often "hallucinate" or skip logic to finish the task faster.

+++

## 4. Advanced Production Patterns

+++

### **Pattern A: The Verifier Cascade**

+++

Instead of one slow, expensive 70B model, use two fast ones:

1. **The Drafter (3B):** Writes a quick, "rough" answer.
2. **The Verifier (8B):** Checks the answer against your rules/schema.

* **Benefit:** You get 70B quality at 3B speed.

+++

### **Pattern B: Hybrid Routing**

+++

Use a tiny model (1B) as a "gatekeeper" to sort incoming user requests.

* **Simple requests** (e.g., "Hello") go to your **Small local model**.
* **Complex requests** (e.g., "Write a legal brief") are routed to a **Large Cloud API**.

+++

## 5. Implementation Summary (Actionable Checklist)

+++

1. **Select Tier:** 8B for most tasks, 14B+ for Agents.
2. **Quantize:** Use **4-bit (Q4_K_M)** for most deployments. It reduces size by 50% with only a ~1% loss in logic.
3. **Calculate VRAM:** `Model Size + 2GB (Headroom)`. If you have 12GB of VRAM, stick to 8B models.
4. **Enforce SGR:** Use libraries like *Pydantic* or *Outlines* to ensure the model doesn't output broken text.
5. **Audit:** Test with the longest possible user input to ensure the "KV Cache Tax" doesn't crash your server.
