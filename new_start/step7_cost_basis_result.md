---
title: Cost closed the hard way - on a like-for-like basis the SRAM system has no cost advantage; the blocker is SRAM price per GB (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, sram, hbm, correction, model]
---

# Cost, like for like (31 Oct 2026)

**MODELLED, not measured; inputs are third-party estimates.** Output: [log](experiments/step7_cost_basis.log), from [`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs) with the GPU priced by env override (`GPU_PRICE_ABS`). The founder asked to close the cost question first. I searched for the packaged-chip cost, and the search exposed an error in my comparison.

## What the sources say (third-party estimates, not disclosures)

- **H100 SXM5 manufacturing cost about $3,320** ([Silicon Analysts](https://siliconanalysts.com/data/ai-chip-costs)): logic die about $300, HBM about $1,350 (about $17 per GB; [a per-stack figure of $200 per 24 GB stack](https://siliconanalysts.com/market-data/hbm-pricing) agrees in order of size), CoWoS packaging about $750 (another page of the same site quotes about $70 for a standard interposer, a tenfold spread). The DGX view puts the **selling price** at $25,000-35,000 per GPU; the gap is margin, development and software.
- **Groq LPU:** about $20,000 per chip is quoted by one unsourced hardware site, and a 2024 thread says the company called that too high; per-card power sources disagree (275 or 375 W). No die cost or bill of materials was found.
- **A packaged chip without HBM or CoWoS:** no per-unit price found for an 800 mm2 flip-chip package, board share, power delivery or cooling ([substrate price trend only](https://www.wing.vc/content/the-abf-substrate-bottleneck)). **The $1,000 per chip is still unsourced.** Supplier quotes or a teardown are the only way to close it.

## The error this exposed

Steps 5 and 6 compared **our cost** ($330 die plus an assumed $1,000, about $1,330 per chip) against the **GPU's selling price** ($25,000 per GPU, $15,000 in the worst corner). Those are different quantities. Like for like, one of these must hold: both at manufacturing cost (GPU about $3,320) or both at selling price (ours would carry a similar margin).

## Results, reticle-chip option, 1T mixture-of-experts, 4-bit, SRAM 0.55 pJ/bit

| GPU priced at | central: cost advantage | worst corner (GPU 100 W, latency x2.7): cost advantage |
|---|---|---|
| **$3,320 (manufacturing cost, like for like with our $1,330 per chip)** | **1.02x, parity** | **0.61x (the GPU is 1.6x cheaper)** |
| $8,000 | 2.15x | 1.37x |
| $25,000 (selling price, but ours at cost) | 6.27x | 4.13x |

At like-for-like prices the cost bar (at least 2x cheaper) **fails in both corners**. At a like-for-like selling price our chips would need the same margin multiple (about 7.5x of cost, about $10,000 per chip), which loses outright (see the $5,330 row of [step 6](step6_sram_energy_result.md), 0.5x to 1.6x).

## Why: capacity per dollar

The 1T model with its cache at batch 1,024 needs about 960 GB, and the SRAM version buys it as silicon at about **$175 per GB of die** (330 dollars for 1.88 GB) against **$17 per GB** for HBM, **10 times more per GB**, before any packaging. The SRAM machine is about 10x faster per sequence (320-950 against 49 tokens per second) and moves about 10x the tokens per system, which roughly pays for the extra memory cost and no more. This is also the answer to "why does nobody just add memory": on manufacturing cost, SRAM capacity does not win against HBM; what wins is speed per user and energy per token.

## Verdict

- **Pre-set cost bar W1: FAIL on a like-for-like basis.** Not closable by a lower packaging price: even at zero packaging cost the die alone is about $175 per GB against $17.
- **What the SRAM approach does deliver on the model:** energy per token 6x to 13x lower (reticle-chip option) and speed per user about 7x to 20x higher, at roughly cost parity with a GPU cluster (1.0x central, 0.6x worst). That is a speed-and-energy claim, not a cost claim. I will not move the bar to make it pass; a new claim needs its own bar, written first.
- **Levers on the capacity cost that would change the answer** (each to be tested, and each also helps a GPU, so the comparison must give both the lever): the 16-bit key-value cache is about half of the 960 GB, so 4-bit cache halves capacity and traffic; fewer bits per weight; storing cold experts in cheaper memory and streaming them.

Related: [Workload map](../docs/gpu_workload_map.md), [Step 6 result](step6_sram_energy_result.md), [Step 5 result](step5_worst_case_result.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
