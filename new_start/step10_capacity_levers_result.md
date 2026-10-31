---
title: Capacity levers do not fix the SRAM cost failure - what would (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, capacity, levers, kv-cache, quantisation, failure, model]
---

# Capacity levers on the cost failure (31 Oct 2026)

**MODELLED.** Same model as [steps 5 to 7](step7_cost_basis_result.md) ([`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs) with two new switches, `KV_BITS` and `W_BITS`), [log](experiments/step10_capacity_levers.log). The bar was written in the source before the run: with the levers applied **equally to both machines**, the GPU priced at its estimated manufacturing cost ($3,320, third-party), the worst corner (GPU 100 W, latency x2.7), the reticle-chip option at $1,330 per chip: **cost advantage at least 2x.**

## Result

1T mixture-of-experts model, batch 1,024, SRAM 0.55 pJ/bit, 420 mm2 per GB, cost advantage = GPU cost per token / ours (below 1 means the GPU is cheaper):

| key-value cache | weights | chips | GPUs | cost advantage, central | cost advantage, worst | energy advantage, worst |
|---|---|---|---|---|---|---|
| 16-bit | 4-bit | 630 | 14 | 1.02x | 0.61x | 6.2x |
| 8-bit | 4-bit | 479 | 11 | 1.06x | 0.64x | 6.0x |
| 4-bit | 4-bit | 404 | 9 | 0.99x | 0.60x | 5.6x |
| 4-bit | 3-bit | 322 | 7 | 0.94x | 0.57x | 5.1x |
| 4-bit | 2-bit | 240 | 6 | 0.87x | 0.53x | 4.7x |

**The bar fails in every combination (no row reaches 2x; the best worst-corner value is 0.64x).** The levers shrink both machines at the same rate, so the ratio does not move. Going to 2-bit weights also loses the energy bar (4.7x against 5x), and weights below 4-bit change a model's accuracy, which is not tested here.

## What would fix it (derived, not tested)

The gap is the price of fast memory per GB, not how many bytes must be stored. In this model the worst-corner cost is almost all capital (energy under 2%). To reach the 2x bar the reticle-chip system's cost per token must fall by a factor of about 3.3, which means **an all-in cost of about $410 per packaged chip, about $215 per GB** of fast on-chip memory (against $1,330 and about $707 per GB now; HBM on a GPU is about $62 per GB all in, from $3,320 x 1.5 over 80 GB). Silicon alone is $330 per chip ($175 per GB), so no packaging saving can reach it; the memory itself must become 3 to 5 times cheaper per bit at SRAM-like read energy and speed. Candidate routes, each needing sourced numbers before any claim: denser memory cells (eDRAM or gain-cell, MRAM, RRAM), at the cost of refresh, endurance or read energy; **3D stacking does not help the silicon cost per GB** (each layer still costs a wafer area).

## Status of the failure

**Cost (row I) stays failed, and is structural for an SRAM-based system.** What the SRAM approach still shows on the model is a speed and energy advantage at roughly cost parity (central) or a 1.6x cost disadvantage (worst corner). I will not change the bar. Open directions: a sourced study of denser memory technologies against the $215 per GB requirement, or accept a speed-and-energy claim with its own pre-set bar.

Related: [Step 7 cost result](step7_cost_basis_result.md), [Step 6 SRAM energy result](step6_sram_energy_result.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
