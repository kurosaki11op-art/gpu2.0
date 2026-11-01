---
title: Step 22 plan - can an SRAM plus DRAM tier fix capacity without losing the speed advantage (bars written before the run, 1 Nov 2026)
tags: [spark, new-start, tier, capacity, plan, vision-research-02, vision-research-01]
---

# Step 22 plan: SRAM plus a larger, slower memory tier (bar G3)

Why: [Vision research 01](../docs/reviews/research_01_summary.md) gap G3 (capacity on SRAM machines) and wedge 5, and [weakness A result](../hw/gpu/weakness_A_result.md): our edge is aggregate bandwidth from on-chip memory, bought with capacity. Question: if each chip gets a DRAM tier (an HBM-class stack) to hold the weights that do not fit in SRAM, does the design keep a speed advantage over a GPU cluster, at a sensible chip count and cost?

## Model (new file `experiments/step22_tier_model.rs`, std only; MODELLED, every parameter ASSUMED unless marked)

- **Workload:** the step 5 model: 1T mixture-of-experts, 32B active, 61 layers, d 7168, 4-bit weights, 16-bit cache, context 4,096, batch 1 (the latency case), speed measured as tokens per second for one user.
- **GPU cluster (H100-class, 72 GB usable, 3.35 TB/s each):** chips needed to hold the weights and cache; at batch 1 each token reads the active weights plus the cache; speed = reads over the cluster's bandwidth at **80% of the memory floor** (our measured T4 with CUDA graphs reached 72% to 95%, [test B](../hw/gpu/graphs_test/PLAN.md)).
- **Our chip:** 800 mm2 die, 80% SRAM (1.52 GB), SRAM read bandwidth from the M3 tile rate (256 bytes per cycle per 4 MB tile at 1 GHz, about 93 TB/s per chip), plus a **tier** of C GB of DRAM with B TB/s per chip. A fraction **h** of the bytes read per token comes from SRAM (the rest from the tier); the two reads overlap; a fixed 50 microsecond per-token network and software overhead (ASSUMED; the striped simulation gave 33 to 70 microseconds).
- **Scan:** tier capacity per chip 0, 24, 48, 96 GB; tier bandwidth 0.8 and 1.6 TB/s; SRAM hit rate h from 0 to 1. h is **UNKNOWN**: it depends on how well a 15 GB SRAM can cache the experts a 500 GB mixture-of-experts model touches, and routing is close to uniform in the models I know of; the result is reported as the h needed, not as a guess of h.

## Bars (fixed now, from Vision's proposal)

- **G3-count:** our chip count is at most **2x** the GPU count.
- **G3-speed:** our speed per user at batch 1 is at least **4x** the GPU cluster's.
- **Pass** needs both, at some tier setting; the report states the SRAM hit rate h that the speed bar requires and the tier size that the count bar requires, and whether the two can hold together.
- Cost per million tokens and energy per token are reported beside, not bars.

## Not covered

Quality, batch above 1, tier energy beyond a per-bit figure, interconnect contention, real expert-routing statistics, the cost of the DRAM (an assumed price per GB from the step 3 notes, unsourced for our purchase volume).

Related: [Step 5 worst-case result](step5_worst_case_result.md), [Step 21 corrections](step21_vision_corrections.md), [Weakness A result](../hw/gpu/weakness_A_result.md), [Research 01 summary](../docs/reviews/research_01_summary.md), [Docs index](../docs/INDEX.md)
