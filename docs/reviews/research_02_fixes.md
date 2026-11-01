---
title: Research 02 - how far the incumbents' own fixes go - CUDA graphs, compilers, speculative decoding, quantisation, disaggregation (1 Nov 2026)
tags: [spark, review, research, cuda-graphs, torch-compile, speculative-decoding, vllm]
---

# Research 02: the incumbents' fixes

Labels as in [hardware](research_02_hardware.md). **Most of this note rests on search summaries [S]**, plus the two verbatim papers cited there. Accessed 1 Nov 2026.

| fix | what it fixes | cost to developers | measured effect | what is left | read depth |
|---|---|---|---|---|---|
| CUDA graphs | Launch gaps between small kernels | Capture per batch shape; engines pad batches up to captured sizes; memory held per graph | H100 batch 1: **1.259x** (20.6% less time); L4: 1.028x; at batch 4 on H100: 1.04x to 1.11x depending on context | At batch 1 the H100 is still near 39% of its weights-only floor (DERIVED, [hardware](research_02_hardware.md)) | MEASURED, arXiv 2605.30571 [S for batch 4] |
| Default use in engines | Same | None for the user | vLLM's default mode captures a full graph for pure-decode batches and piecewise graphs otherwise; a given attention backend must support it, otherwise the engine downgrades the mode | Backend coverage is uneven: one attention backend supports the unified full mode, others only pure decode | PUBLISHED docs, [S] [vLLM design page](https://docs.vllm.ai/en/latest/design/cuda_graphs/) (v0.10-era text, may be out of date) |
| torch.compile and fusion | Memory round trips between operators, launch count | Compile time; fragile on new model code | Integrated by default in vLLM V1 per its blog; **no before/after number found** (the one paper that tried it excluded its failed cells) | UNKNOWN | [S] [vLLM blog](https://vllm.ai/blog/torch-compile) |
| Speculative decoding | Idle compute at small batch: several tokens verified per pass | Needs a draft model or head; tuning | 2.9x at batch 1 and 2.65x at batch 3 on a 7B-class model, one consumer GPU (the method's own paper); another paper reports it becomes **slower than plain decoding above batch 32**; a third cites vLLM measurements falling from 1.3x to 0.7x between batch 2 and 48 | Gains vanish where batching already fills the GPU: it helps exactly the low-batch, low-latency case | PUBLISHED [S] [EAGLE](https://arxiv.org/pdf/2401.15077), [agent serving](https://arxiv.org/pdf/2608.24004), [large-batch EAGLE](https://arxiv.org/html/2508.08192v1) |
| Low-bit weights | Bytes read per token | Calibration; quality checks | On L4 batch 1: 62.3 ms bf16, 59.4 ms 4-bit NF4 with an on-the-fly kernel, 45.2 ms 4-bit AWQ, **17.4 ms 4-bit GPTQ with an optimised kernel** (3.6x). The same bit width varies 3.4x by kernel | Kernel quality, not bit width, decides the gain | MEASURED [V abstract], arXiv 2605.30571 |
| Disaggregated prefill and decode | Prefill and decode fight for one GPU | Orchestration software, fast links | Beats combined serving "at almost all interactivity levels" on throughput per GPU; **hurt AMD FP4 at high interactivity for lack of tuned kernels** | Needs rack-scale links; software maturity | MEASURED by SemiAnalysis, [P] in [Research 01 compute](research_01_compute.md) |
| FP8 and FP4 | Bytes and matrix throughput | Checkpoints per format | See [Research 01 numerics](research_01_numerics.md) (weak evidence) | | |

## Reading

1. **The single biggest "weakness" in Jarvis's first pass, launch overhead, is already mostly addressed by default in serving engines,** and where it is not, the headroom measured so far is one fifth of step time on one GPU class, in one paper. A fix that cannot beat a free software flag is not a product.
2. **The remaining loss at batch 1 is large (about 61% of the weights-only floor on H100) but is not explained by this evidence.** The paper measures the gap and removes one cause; it does not say what the rest is. Candidates (not tested here): launch gaps not removed by graphs, kernel inefficiency, attention, framework overhead. Identifying which is the cheapest useful experiment.
3. **Speculative decoding is the incumbent fix aimed at exactly our regime** (low batch, high per-user speed). Anything a new machine claims at batch 1 has to be compared with an H100 running it, which gives about 2x to 3x. The project's comparisons have not included it.
4. **Kernel quality is the dominant variable** (3.4x between 4-bit kernels). This favours incumbents with large kernel teams, and favours open kernel projects.

## Gaps in this note

I did not read the vLLM documentation or the engines' source myself beyond search summaries. I found no measured cost-to-developer figure (hours, lines) for any fix: **UNKNOWN**, who could answer: engine maintainers and teams that deploy them.

Related: [Research 02 summary](research_02_summary.md), [Hardware weaknesses](research_02_hardware.md), [Research 01 compute](research_01_compute.md), [Research 01 numerics](research_01_numerics.md), [Reviews index](README.md)
