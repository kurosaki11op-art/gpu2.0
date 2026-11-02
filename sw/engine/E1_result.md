---
title: Engine milestone E1 - our own engine reproduces a real pretrained decoder's logits (2 Nov 2026, MEASURED)
tags: [spark, engine, software, result, e1]
---

# Engine E1 result (2 Nov 2026)

**MEASURED** on the cloud container's CPU. Plan and bars (written first): [engine plan](engine_plan.md). Code: [`engine.rs`](engine.rs) (Rust, standard library only, about 100 lines of logic: a minimal JSON reader for the safetensors header, layer norm, linear layers, causal attention, the GPT-2 activation function, tied output embedding) and the check [`check_e1.py`](check_e1.py).

## Result

- Model: the public 6-layer, 768-wide, 12-head GPT-2-family checkpoint, fp32 safetensors (82 tensors, 353 MB), loaded directly by our code.
- 16 fixed prompts (173 positions in all), tokenised by the reference tokenizer; our engine returns the logits of every position, compared with PyTorch fp32.
- **Maximum absolute logit error 3.81e-4 (bar 1e-3); greedy next-token agreement 173 of 173 positions (bar: all).**
- **E1: PASS.**
- Run time of the unoptimised engine: 8.3 s for 173 positions of prefill including the 50,257-way output layer (about 48 ms per position); **not a speed claim**: no threads, no blocking, no vector code, no cache.

## Limits

One model, one checkpoint; fp32 only; no tokenizer in the engine (ids come from a script); no key-value cache or sampling yet (E4); the tiny test checkpoint had no safetensors file, so only the larger model was run; the check ran on this container's CPU only.

## Next

E4 (incremental decoding with a key-value cache, same outputs), then E2 (INT8 weights with the 0.01 nats bar), then E3 (speed against llama.cpp, bar 0.8x). Dates and stop rule are in the plan.

Related: [Engine plan](engine_plan.md), [CUDA study](../../docs/cuda_study_jarvis.md), [Docs index](../../docs/INDEX.md)
