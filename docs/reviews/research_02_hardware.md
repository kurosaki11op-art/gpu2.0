---
title: Research 02 - GPU hardware weaknesses with numbers - utilisation, bandwidth, launch overhead, reliability (1 Nov 2026)
tags: [spark, review, research, gpu, weaknesses, utilisation]
---

# Research 02: GPU hardware weaknesses

Labels: MEASURED (a paper's own measurement), PUBLISHED, VENDOR CLAIM, THIRD-PARTY ESTIMATE, DERIVED (my arithmetic), UNKNOWN. Read depth: **[V]** verbatim page text read; **[S]** only a summary (search result or the fetch tool's own summary of a truncated page). Accessed 1 Nov 2026. Models are described by size; arXiv numbers identify papers.

## 1. Batch-1 decode on a fast GPU: not bandwidth-limited, and launch overhead is real but partly fixed

Source: arXiv [2605.30571](https://arxiv.org/html/2605.30571), one author (KAIKAKU), May 2026, preprint. I read the first third verbatim [V]; the rest through the tool's summary [S].

| item | value | label |
|---|---|---|
| Setup | 7B and 8B-class decoders, bf16, batch 1, context 2,048 to 16,384; four GPUs on a rented cloud; PyTorch 2.4, plain library attention, not a serving engine | MEASURED [V] |
| Fraction of peak bandwidth at batch 1 | H100 about 27%; L4 about 81% (the paper also prints 79.4% for L4) | MEASURED [V] |
| Step time with and without CUDA graphs, H100 | 14.83 ms and 11.78 ms: **1.259x** (95% interval 1.253 to 1.267, 10 sessions) | MEASURED [V abstract, S for the times] |
| Same, L4 | 64.5 and 62.8 ms: 1.028x | MEASURED [V abstract] |
| One earlier headline of 1.72x | retracted by the authors in favour of 1.259x | MEASURED [S] |
| Per-kernel launch gap | **not measured**; about 30 microseconds is an illustration only | [S] |
| torch.compile effect | **not reported**; compile variants failed with allocator errors and were excluded | [S] |

**DERIVED:** weights-only floor on H100 = 15.23 GB / 3.35 TB/s = 4.55 ms. Eager reaches 31% of it, graphed 39% (the paper's own 27% includes more terms). So CUDA graphs recover about 21% of step time (the 25% that one search summary printed is wrong: 1 - 11.78/14.83 = 20.6%), and **even with graphs the H100 sits at about 39% of its weights-only floor at batch 1.** The same fix does nothing on the slower L4, which is already near 80%. The weakness belongs to fast GPUs at small batch.

**Limits:** one author, preprint, plain PyTorch path, one model size family, and the authors say "folk knowledge" about the launch-bound observation. Whether a production engine with compiled, fused kernels closes more of the 61% is **UNKNOWN from this source**; see [fixes](research_02_fixes.md).

## 2. Decode leaves compute idle by design

Source: arXiv [2609.12923](https://arxiv.org/html/2609.12923v1) (KTH, 11 Sep 2026, preprint); H100 NVL, one GPU, bf16, vLLM, 8B to 32B dense and a 30B mixture model. First 39,000 of 92,000 characters [V].

| item | value | label |
|---|---|---|
| Decode SM-busy, dense matrix kernels, batch 1 to 8 | 6.5% to 12.7%, mean 9.4% | MEASURED [V] |
| Same at batch 32 | 34% to 73% depending on model | MEASURED [S] |
| Device-wide compute throughput, decode | 7.9% of peak; prefill 92% when cold | MEASURED [S] |
| Decode DRAM throughput | about 64% of peak | MEASURED [S] |
| Matrix-unit fragment fill in decode | 1.6% to 12.5%: the SM-busy number "overstates useful matmul throughput by 8 to 64x" | MEASURED [V] |
| Launch overhead | analytic model, 5 microseconds per launch, up to about 30% of decode time | MODELLED by the authors [S] |

This is the stronger evidence for "decode wastes the GPU": useful matrix work is a few percent, memory is busy at about 64%. It does not support "launch-bound": this paper runs with graphs on and finds memory the limit.

**Cross-check with a memory-maker paper:** SK hynix's arXiv [2504.16112](https://arxiv.org/html/2504.16112) (v2, Dec 2025) [V]: on an A100 the matrix kernels turn compute-bound near batch 203 (DERIVED check: 312 TFLOPS / 1.55 TB/s = 201, consistent), but **attention stays memory-bound at every batch size**, because it is vector-matrix work on a cache that grows with each user. Their GPU-only baseline ran out of memory at batch 32 on a 48 GB card, and their coprocessor prototype claims 4.1x throughput (baseline ambiguous in the text) and 4.58x energy efficiency; the prototype is an FPGA, so projected end-to-end figures are not measurements. The authors sell memory, so they have a stake in this conclusion.

## 3. Reliability at scale

Source: the 405B-parameter training report from Meta, arXiv 2407.21783, section 3.3.4 and Table 5, read verbatim through the web edition [V] (the PDF edition returned no usable text).

| item | value | label |
|---|---|---|
| Cluster and window | up to 16,000 H100 GPUs at 700 W, 54 days | PUBLISHED [V] |
| Interruptions | 466 total: 47 planned, **419 unexpected** | PUBLISHED [V] |
| Rate | one unexpected interruption per about 3.1 hours (DERIVED: 1,296 h / 419) | DERIVED |
| Cause | about 78% attributed to confirmed or suspected hardware | PUBLISHED [V] |
| Largest rows | faulty GPU 148; GPU HBM3 72; software bug 54; network switch or cable 35; host maintenance 32 | PUBLISHED [V] |
| Effective training time | above 90%; manual intervention needed three times | PUBLISHED [V] |
| Thermal | 1% to 2% throughput swing by time of day from midday temperature; power swings "on the order of tens of megawatts" | PUBLISHED [V] |

**The paper's table is internally inconsistent:** 148 of 419 is 35.3%, not the printed 30.1%; the GPU-labelled rows sum to 268 (64.0%), not the 58.7% in the text. Counts sum to 419, so the percentages are what disagree. HBM3 alone is 17.2% of unexpected stops. This is training, where one fault stops a synchronous job. For inference the same fault takes out a replica, which is a smaller loss; no inference-fleet failure study was found: **UNKNOWN.**

## What this note supports, and what it does not

- **Supported (MEASURED, caveated):** small-batch decode on a fast GPU gets 27% to 39% of peak bandwidth and a single-digit share of compute; attention is memory-bound at any batch.
- **Not supported:** that launch overhead is the main loss today. Graphs recover about a fifth of step time, and are on by default in serving engines ([fixes](research_02_fixes.md)).
- **UNKNOWN, who could answer:** fleet-wide utilisation of production inference (hyperscalers); idle power by workload (one measurement in [power](research_02_power.md)); failure rates of inference-only fleets (cloud operators).

Related: [Research 02 summary](research_02_summary.md), [Incumbent fixes](research_02_fixes.md), [Power](research_02_power.md), [Research 01 compute](research_01_compute.md), [Reviews index](README.md)
