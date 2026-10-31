---
title: Research 01 - compute and execution models, utilisation and independent results (31 Oct 2026)
tags: [spark, review, research, compute, competitors]
---

# Research 01: compute and execution model

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026.

## What and why

| vendor | execution model | why | source |
|---|---|---|---|
| Nvidia | Programmable parallel GPU with matrix units, sold since 2026 as a rack: 72 GPUs, 36 CPUs, one scale-up domain | Keeps one platform for training and inference; the installed software base follows it | [S] [10-K description](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm) |
| Nvidia and Groq | Statically scheduled dataflow on SRAM for decode, GPU for prefill | Decode is sequential and memory bound, prefill is parallel | [P] [ServeTheHome](https://www.servethehome.com/decoding-the-future-of-inference-at-nvidia-groq-lpus-join-vera-rubin-platform-for-low-latency-inference/2/) |
| Cerebras | Whole wafer, 900,000 cores with local SRAM on a mesh; pipeline parallel across wafers | Avoids off-chip movement | [P] [S-1](https://www.sec.gov/Archives/edgar/data/2021728/000162828026025762/cerebras-sx1april2026.htm), [P] [SemiAnalysis](https://newsletter.semianalysis.com/p/cerebrass-next-generation-cs-4-fast) |
| Google TPU | Matrix unit ASIC, pods up to 9,216 chips; next generation splits training and inference chips | Own workloads, own software | [S] [summary](https://thenextweb.com/news/google-ironwood-tpu-inference-cloud-next) |
| AMD | GPU, more memory per package | Compete on memory and price | [P] [InferenceX v2](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs) |
| Tenstorrent | Grid of RISC-V and Tensix cores, GDDR6, Ethernet between chips, open stack | Low price, open software | [P] [Register review](https://www.theregister.com/on-prem/2025/11/27/blackhole-quietbox-tenstorrents-ai-workstation-reviewed/2113269) |

## What independent results show

**The best public benchmark is InferenceX (formerly InferenceMAX), run by SemiAnalysis.** It is open source and useful, but not neutral: Nvidia and AMD supplied hardware and engineers, and the publisher sells the cost models behind it ([P] [Feb 2026](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs), [P] [Oct 2025](https://inferencex.semianalysis.com/blog/inferencemax-open-source-inference-benchmarking)). Its power figures come from component TDP, not measurement, and energy per token is not benchmarked. It uses random tokens with no prefix cache. Exact curve values and cost assumptions are paywalled or in images: UNKNOWN to me.

| result | value | label |
|---|---|---|
| H100 against GB200 rack, realised, at 75 tokens/s per user | up to 55x | MEASURED by SemiAnalysis |
| at 130 tokens/s per user, GB200 rack against single-node | nearly no advantage, more expensive per token | MEASURED by SemiAnalysis |
| multi-token prediction, 670B-class model, GB300 at 150 tokens/s per user | about $2.35 to $0.11 per million tokens (21x) | MEASURED by SemiAnalysis, relayed from a section I saw only as a summary |
| AMD software, Dec 2025 to Jan 2026 | up to 2x in under 2 months | MEASURED by SemiAnalysis |
| B200 on one open engine | throughput per GPU doubled at some interactivity levels in about 4 months | MEASURED by SemiAnalysis |
| tokens/s per provisioned MW, 120B model, FP4 | H100 900,000; B200 2.8M | MEASURED throughput over ESTIMATED power, summary-level read |
| MLPerf v5.1, Blackwell Ultra, per GPU | 5,842 offline, 2,907 server tokens/s | Vendor-derived division of an audited total, [S] [HPCwire](https://www.hpcwire.com/2025/09/10/mlperf-inference-v5-1-results-land-with-new-benchmarks-and-record-participation/) |
| Tenstorrent, four cards, 70B model | about 41% of theoretical peak; one card about half on 8B | MEASURED by The Register, Nov 2025 |
| Vendor claims not independently confirmed | Rubin 10x lower cost per token; LPX up to 35x tokens per watt; CS-4 up to 30x faster; Cerebras up to 15x | VENDOR CLAIMS |

## Efficient and effective? Measured energy

| measurement | value | label |
|---|---|---|
| One B200, 32B dense model, chat | 0.209 J per token at batch 128, 0.151 at batch 512 (GPU energy only) | MEASURED, [P] [Chung et al., Jan 2026](https://arxiv.org/html/2601.22076v1) |
| 235B MoE model, FP8, four B200s | about 0.4 J per token at the lowest point | same |
| Batch size effect | 3x to 5x lower energy per token, then a plateau | same |
| B200 against H100 | median 35% less energy in 63 of 72 LLM comparisons | same |
| FP8 against BF16 | worse at small batch (median +30% at batch 8 to 16), better at large (−11% at 65 to 256) | same |
| Google fleet, median text prompt, May 2025 | 0.24 Wh: active accelerators 58%, host CPU and DRAM 25%, idle machines 10%, overhead 8% | MEASURED, [P] [Elsworth et al., Aug 2025](https://arxiv.org/html/2508.15734) |
| Google fleet, one year | 33x lower energy per median prompt | same; a software, hardware and model mix |

**Utilisation:** in a 2023 production inference cluster, GPU and core utilisation stayed under 60% for over 99% of GPUs ([S] [MuxFlow](https://arxiv.org/pdf/2303.13803)). A 2026 trace of an inference cluster reports mean GPU memory utilisation of 43.48% ([S] [Harvest](https://arxiv.org/pdf/2602.00328)). No current fleet-wide average for frontier serving was found: UNKNOWN; hyperscalers could answer.

## The flaw, and what a newcomer could do

**Flaw 1: peak numbers mislead.** The gap between realised and peak is large on every machine, and the fastest gains come from software. **Fix:** measured joules and tokens at a stated per-user speed, which no public benchmark fully provides. Nobody would be stopped from copying this, but it is cheap and it is a gap today.

**Flaw 2: idle and host energy are outside the accelerator.** DERIVED, using Google's split: if only the accelerator part improves by 3.5x to 7.3x (the project's corrected [step 21](../../new_start/step21_vision_corrections.md) range), the total per prompt falls only **1.7x to 2.0x**. That split is one fleet, on a different mix of hardware, so treat this as an order of size.

## What they cannot do

- **GPUs:** decode at high per-user speed stays expensive (B200 about $0.56 at 50 and about $4 at 125 tokens/s per user on one coding workload, summary-level read). That is the opening which SRAM machines occupy.
- **Cerebras and LP30:** cheap service at high concurrency on the largest models; see [memory](research_01_memory.md). Training on LP30: none claimed.
- **Tenstorrent:** at the review date, not competing directly with Nvidia or AMD at the top end, by the reviewer's reading.

Related: [Research summary](research_01_summary.md), [Memory](research_01_memory.md), [Software](research_01_software.md), [Reviews index](README.md)
