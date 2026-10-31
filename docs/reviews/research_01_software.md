---
title: Research 01 - software and lock-in, and what porting to a new chip really costs (31 Oct 2026)
tags: [spark, review, research, software, cuda, competitors]
---

# Research 01: software and lock-in

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026.

## What and why

- **Nvidia:** CUDA, plus an inference engine, a disaggregation layer and tuned kernels. It took about two decades, and it is why any model tends to run on Nvidia first. Its specialised inference engine and attention kernels are reported to have no AMD equivalent ([S] [secondary, 2026](https://www.spheron.network/blog/rocm-vs-cuda-gpu-cloud-2026/)).
- **Cerebras:** a compiler from PyTorch, "eliminating the need for CUDA" in its own words (VENDOR, [P] [S-1](https://www.sec.gov/Archives/edgar/data/2021728/000162828026025762/cerebras-sx1april2026.htm)). In practice it sells inference as a service, which hides the stack from the customer. Hardware was still about 70% of 2025 revenue (DERIVED from the S-1).
- **Tenstorrent:** open source; each model must be supported.
- **Open serving engines:** two common open engines now give non-Nvidia chips a route to users without CUDA.

## What porting really costs: evidence

| case | finding | label and source |
|---|---|---|
| AMD, training, Dec 2024 | Reached within 75% of H100/H200 only with several AMD teams fixing bugs; public releases worse per unit of cost, despite lower cost of ownership | MEASURED, [S] [SemiAnalysis](https://semianalysis.com/2024/12/22/mi300x-vs-h100-vs-h200-benchmark-part-1-training/) |
| AMD, inference, Feb 2026 | Competitive per unit of cost at FP8 on an open engine with Nvidia's GPU on the same engine; not competitive at FP4 with multi-node features | MEASURED, [P] [InferenceX v2](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs) |
| AMD, academic, 2025 | 37% to 66% of H100/H200 realised LLM inference performance | MEASURED, [S] [paper](https://arxiv.org/pdf/2510.27583) |
| Tenstorrent, Nov 2025 | Setup script failed, compiler in beta; 45 minutes to convert a model; tested models appear to leave 76 of 140 cores idle (reviewer's inference) | MEASURED by reviewer, [P] [Register](https://www.theregister.com/on-prem/2025/11/27/blackhole-quietbox-tenstorrents-ai-workstation-reviewed/2113269) |
| Graphcore | Revenue $4M in 2023 against a founder forecast of $1B for 2024; sold for about $600M, below $700M raised | PUBLISHED accounts and press, [S] [Sifted](https://sifted.eu/articles/graphcore-company-accounts-2023-news), [S] [EE Times](https://www.eetimes.com/ai-chip-startup-graphcore-acquired-by-softbank/). The founder blamed lack of investment; software as the cause was not shown in what I read |
| Untether AI | Receivers appointed Feb 2026 | [S] [tracker](https://killedbyai.net/funding/) |

**A dollar figure for a buyer's cost to migrate: UNKNOWN.** No public source states one. Buyers who have ported could answer. **Staff size of these stacks: UNKNOWN** from the sources read.

## Reading

1. **The moat is thinner for serving a few popular models than for everything else.** AMD's gain shows that open engines can close the gap on FP8 within a few years, with AMD's budget and vendor engineers on site.
2. **The moat is a moving target.** Software alone moved Nvidia's and AMD's results 2x in months, and one feature moved cost by about 21x (see [compute](research_01_compute.md)). **A fixed 2x to 7x hardware claim against today's GPU cost is not safe.** The project's model has no term for this.
3. **Service sidesteps lock-in.** A token API is a much cheaper interface than CUDA: the buyer changes one web address. But it needs owned hardware, and so capital.

## Flaw, and the cheapest fix a newcomer could make

- **Flaw:** vendors' tools favour their own hardware, and support is uneven. **Fix for a solo founder:** do not build a CUDA-class stack. Support one family through an existing open engine or a narrow importer (as in M4). An importer for one model family is feasible; a general stack is not, on the evidence above.
- **What stops Nvidia copying:** nothing technical. Openness conflicts with its commercial interest, though it does contribute to open engines.

## What they cannot do

Nvidia does not serve buyers who require open, inspectable software all the way down. Tenstorrent targets them, so that gap is occupied, too. How many buyers truly pay for this: UNKNOWN.

## Consequence for the deep study plan

"A wafer-scale processor with its own software stack (a CUDA-class layer)" ([plan](../gpu_deep_study_plan.md)) is out of proportion to the evidence: AMD still has gaps after years with far greater resources. The plan does say that CUDA source compatibility is not promised. It should go further and limit scope to one importer.

Related: [Research summary](research_01_summary.md), [Compute](research_01_compute.md), [Deep study plan](../gpu_deep_study_plan.md), [Reviews index](README.md)
