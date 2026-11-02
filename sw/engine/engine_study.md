---
title: Engine study before E2 and E3 - why decoding is memory-bound, what our engine already reaches, and a prediction for INT8 (2 Nov 2026)
tags: [spark, engine, study, quantization, memory-bound, plan]
---

# Study before E2 and E3 (2 Nov 2026)

Founder's correction (2 Nov 2026): build with knowledge and in the right manner. Method rule (CLAUDE.md): why a thing exists, how it is built, where it is used, its flaws, then our design, then a test with a bar. This note covers the part that decides engine speed. Web sources are summaries and blogs (leads, not facts); the measurements are ours.

## 1. Why decoding speed is set by bytes read (concept)

- Generating one token multiplies one vector by every weight matrix, so each weight byte is read once and used for one multiply-add. The time per token is then at least **bytes per token divided by memory bandwidth**; common guidance derates the ideal by 50% to 75% in real engines ([calculator](https://inventivehq.com/tools/llm-inference-speed-calculator), [explainer](https://www.hardware-corner.net/memory-bandwidth-llm-speed/), secondary sources). The same law explains our GPU runs (T4 at 95% of the floor with CUDA graphs).
- **Consequence:** the ways to go faster are (a) fewer bytes per weight (quantisation), (b) more bandwidth (threads and memory channels), (c) not wasting bandwidth (contiguous reads, no cache thrashing). Arithmetic speed (SIMD) matters only once the bytes are small enough that the multiplies become the limit.

## 2. What our engine already reaches (MEASURED, this container, one run each)

- Bytes per token for the 82-million-parameter model in fp32: the six layers hold about 170 MB and the tied output embedding **154 MB** (50,257 x 768 x 4 bytes, read in full for the logits of every token): **about 324 MB per token**.
- Single-thread streaming read on this virtual machine (a plain 256 MB float32 sum in numpy): **4.8 GB/s**; copy (read plus write) 1.6 GB/s; 4 vCPUs, Xeon at 2.1 GHz with AVX2 and AVX-512 flags.
- 324 MB at 4.8 GB/s is **67.5 ms per token; our engine measured 68 ms** ([E4](E4_result.md)). So **the engine is already at this machine's single-thread streaming limit**; the numpy sum is a rough proxy of bandwidth (it may under- or over-state the true limit), so this is a consistent reading, not a proof.
- Two details found by this: the output embedding is the **largest single tensor** (47% of the bytes per token); quantising only the layers would leave half of the bytes.

## 3. Quantisation design (concept, then ours)

- **Why it exists:** fewer bytes per weight cut the floor; accuracy must not suffer. **How it is built (from memory and summaries):** weights stored as 8-bit integers (or 4-bit) with a scale per small block or per output channel; the multiply-add runs on integers or on dequantised values. The mature engines use per-block scales (32 weights per block is a common size).
- **The known flaw:** large models develop a few outlier feature dimensions that break plain 8-bit quantisation, starting at about 6.7 billion parameters, and mixed-precision handling fixes it (the [LLM.int8() paper](https://arxiv.org/pdf/2208.07339v2.pdf), read as a summary). **At 82 million parameters this should not matter**; it will matter for larger models and must be tested then.
- **Our design for E2:** INT8 weights with **one scale per output column** (per output channel) for the layer matrices and **one scale per row** for the output embedding; activations stay fp32 (weight-only quantisation); the dot product accumulates in fp32 and multiplies by the scale once per output; position embeddings, biases and layer-norm parameters stay fp32 (tiny). Token lookup dequantises one row.

## 4. Predictions, written before the code (so they can be wrong)

- **P1 quality:** loss increase at most 0.01 nats per token against our own fp32 pass (the E2 bar), on 64 or more windows with a paired interval.
- **P2 memory:** weights at 0.26 to 0.30 times the fp32 size (8 bits plus scales), inside the 0.3 bar.
- **P3 speed:** if the engine is memory-bound as section 2 reads, bytes per token fall from 324 MB to about 82 MB, so time per token should fall from 68 ms to **about 17 ms (3.5x to 4x faster)**. If the measured gain is under 2x, the engine is not memory-bound at that point (the conversion from integer to float or the scalar loop is the limit) and the next step is SIMD, not more quantisation.

## 5. What this does not settle

Whether llama.cpp is faster on this machine (E3 measures it); thread scaling of this virtual machine's memory system; behaviour on larger models; the 4-bit case (ggml-style block formats were not read from primary sources: the search returned no usable page).

Related: [Engine plan](engine_plan.md), [E4 result](E4_result.md), [CUDA study](../../docs/cuda_study_jarvis.md), [Docs index](../../docs/INDEX.md)
