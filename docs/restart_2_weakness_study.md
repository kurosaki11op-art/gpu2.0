---
title: Restart 2 - weakness-first study of GPUs and CUDA (1 Nov 2026, first pass, web sources unverified)
tags: [spark, gpu, restart, weakness, cuda, study]
---

# Restart 2: weakness-first study (1 Nov 2026)

Founder's decision (1 Nov 2026): start again from scratch on the right path: study GPUs and CUDA, their weak spots and the public controversies, find the weakness worth attacking, then build and prove it in simulation, then look for money. Nobody has to win quickly; the order matters. Method (standing rule): for each weakness, evidence, who suffers, what incumbents already do about it, our candidate fix, a test with a bar written first. **This note is a first pass from web search; every item is a lead until a primary source is read.** Vision is doing an independent pass ([research task 02](vision_research_task_02.md)).

> **Correction, 1 Nov 2026 ([Vision research 02](reviews/research_02_summary.md), [response](reviews/jarvis_response_research_02.md)):** W1 was overstated. Our runs used eager mode with no CUDA graphs, so launch overhead was never isolated; the 1.1B-class model on the laptop GPU reached 78% of the weights-only floor. Several rows below (the licence wording, the French probe, the 92% versus 30% figure, the Gartner and challenger claims) are corrected in the response. The batch-1 check is planned in [graphs_test/PLAN](../hw/gpu/graphs_test/PLAN.md).

## What the first pass found

| # | weakness | evidence (label) | what incumbents already do | our measured or built evidence |
|---|---|---|---|---|
| W1 | Small-batch decode leaves the GPU idle; host-side kernel launch overhead becomes the bottleneck on fast GPUs | arXiv 2605.30571 ([via emergentmind](https://www.emergentmind.com/papers/2605.30571), summary only); SARATHI [arXiv 2308.16369](https://arxiv.org/pdf/2308.16369) on decode under-using compute; a characterisation of LLM inference on GPUs (summarised at [themoonlight](https://www.themoonlight.io/en/review/a-systematic-characterization-of-llm-inference-on-gpus)) | batching, chunked prefill, CUDA graphs and compiled runtimes (unverified how far they close the gap) | **MEASURED by us** on an RTX 3050 laptop and a Colab T4: about 1.0 to 1.5 ms per layer regardless of model size ([RESULT](../hw/gpu/energy_predict/RESULT.md)); the CUDA-graphs comparison is not yet run |
| W2 | Decode is memory-bound and wastes compute; energy per token falls 8 to 14x with batching but users get slower | SARATHI (above); a Towards Data Science piece quotes about 92% versus 30% compute use for prefill versus decode on one GPU (secondary, illustrative only) | disaggregating prefill and decode onto different machines | **MEASURED by us:** 8 to 14x less energy per token at batch 16 on both GPUs |
| W3 | Power, grid and water are the limit on data-centre growth | Gartner via [Data Centre Magazine](https://datacentremagazine.com/news/gartner-ai-drives-26-data-centre-power-surge-to-565twh): about 565 TWh in 2026, up 26%, AI servers about 31%; water mostly indirect (secondary sources, figures vary) | liquid cooling (about 40% of AI data centres by one forecast), efficiency claims by vendors | our energy figure is **MODELLED** and shrinks from about 7x to about 2x per prompt |
| W4 | Software lock-in: CUDA's strength is the ecosystem (libraries, tooling, developer time), and its licence reportedly bans translation layers | [Tom's Hardware, March 2024](https://www.tomshardware.com/pc-components/gpus/nvidia-bans-using-translation-layers-for-cuda-software-to-run-on-other-chips-new-restriction-apparently-targets-zluda-and-some-chinese-gpu-makers) (clause scope disputed by commenters); Jim Keller's "swamp, not a moat" comment ([Tom's Hardware forum summary](https://forums.tomshardware.com/threads/jim-keller-slams-nvidias-cuda-x86-%E2%80%94-cuda%E2%80%99s-a-swamp-not-a-moat-x86-was-a-swamp-too.3837140/page-3), opinion); AMD's ROCm gap is software maturity ([TechInsights](https://techinsights.com/ja/node/61535)); a French competition probe reported by one site only (unconfirmed) | AMD ROCm, Triton, SYCL, retargeting projects | **BUILT by us:** a simulator and ISA that run a CNN and a transformer from PyTorch exports; no importer for real pretrained models yet (M4) |
| W5 | Challenger chips lose on software maturity and programmability | an arXiv comparison of eight AI hardware platforms ([arXiv 2604.10852](https://arxiv.org/html/2604.10852v1), excerpts only) | n/a | none |
| W6 | Capacity: fast on-chip memory is small (SRAM-only designs) | [Vision research 01](reviews/research_01_summary.md) | HBM stacking, DRAM tiers | our design has this weakness |

## Reading

- **W1 is the best lead and our own measurement matches published work.** If CUDA graphs and compiled runtimes close most of it, the lead is gone; if not, it is a real GPU weakness that a statically scheduled machine avoids by construction. The test costs one script and one hour.
- **W4 is the biggest moat and the worst thing to fight head on** (legal and ecosystem risk). Attack above it: compile from PyTorch/ONNX/Triton for one model family.
- **W3 is the strongest need but is shared by every competitor;** it is a reason buyers will listen, not a differentiator.
- Nothing here is new to Nvidia, Google or Cerebras. The question for each weakness is whether a small team can show a fix they cannot easily copy.

## Next steps (in order)

1. W1 test: CUDA graphs and a compiled model on the founder's RTX 3050 and the Colab T4, same bars style as G1; script to be written.
2. Read the primary sources behind W1, W2, W5 (not summaries).
3. Update the GPU baseline to current-generation hardware from primary sources.
4. Merge Vision's pass, rank weaknesses by evidence and by whether we can show a fix, pick one.
5. Only then: define the product in simulation, with a pre-registered bar for the fix.

Related: [Research 01 summary](reviews/research_01_summary.md), [Deep study plan](gpu_deep_study_plan.md), [Watch list](watch_radar.md), [Test G1 result](../hw/gpu/energy_predict/RESULT.md), [Own GPU charter](own_gpu_charter.md), [Docs index](INDEX.md)
