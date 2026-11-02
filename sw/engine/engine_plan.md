---
title: Our own inference engine - scope, milestones, bars and stop rule (plan written before any code, 2 Nov 2026)
tags: [spark, engine, software, plan, build]
---

# Our own inference engine (plan, 2 Nov 2026)

Founder's decision (2 Nov 2026): build the inference software layer ourselves, software first and a chip later, and treat the open projects as competitors to beat ([decision](../../docs/PROJECT_MEMORY.md)). Reservations on record: no buyer evidence yet, free engines already cover much of this ([CUDA study](../../docs/cuda_study_jarvis.md), [research 04](../../docs/reviews/research_04_summary.md)). So the build has a narrow scope, bars written first, and a stop rule.

## Scope

A small, dependency-free engine (Rust, standard library only, like the rest of the project) that loads a public decoder model from a safetensors file and generates tokens. First target: the GPT-2 family (the earlier M4 plan), then a modern decoder family. First backend: CPU (the same start as the best-known one-person engine); later a GPU backend through an existing path, chosen after the CPU numbers exist. Not in scope: training, CUDA compatibility, a compiler.

## Milestones and bars (fixed now)

- **E1 correctness (fp32):** next-token logits for 16 fixed prompts match PyTorch within a maximum absolute error of 1e-3 at every position, and the greedy next token agrees at every position. Model: a 6-layer, 768-wide public checkpoint (82 tensors) plus a tiny test checkpoint.
- **E2 INT8 weights:** loss increase against fp32 of at most 0.01 nats per token on a fixed text sample (paired interval, at least 64 windows), and weight memory at most 0.3 times the fp32 size.
- **E3 speed against the best free engine on the same CPU and the same model file converted to its format:** at least **0.8x of llama.cpp's generation speed (batch 1) with INT8 weights**; reported with the CPU model and threads used. A miss is reported as a miss.
- **E4 incremental decoding with a key-value cache:** the same outputs as full recompute (E1 bar) and per-token cost independent of position within 20%.
- **E5 a GPU back end** only after E3 is met; its bar is written then.

## Stop rule and dates

- E1 and E4 by 9 Nov 2026, E2 by 16 Nov, E3 by 30 Nov. **If E3 is below 0.5x of llama.cpp on 30 Nov, the engine stops as a competitor project** and is kept as a learning artefact and a base for the accelerator simulator. Dates are my proposal; the founder may change them before the first run, not after.

## Limits

A CPU engine does not address the small-GPU pain directly; it is the first step with the least risk. Free competitors are mature; matching 0.8x on CPU would already be a result for a first version. No tokenizer in E1 (token ids come from a script); a tokenizer is added before any demo.

Related: [CUDA study](../../docs/cuda_study_jarvis.md), [Project memory](../../docs/PROJECT_MEMORY.md), [Small GPU plan](../../hw/gpu/small_gpu/small_gpu_plan.md), [Docs index](../../docs/INDEX.md)
