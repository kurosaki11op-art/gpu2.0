---
title: Rows I and J, fair comparison and worst case - the earlier "closed" was too generous (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, power, wafer, chips, model, correction]
---

# Rows I and J: fair comparison and worst case (31 Oct 2026)

**MODELLED, not measured.** Rust model [`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs), [log](experiments/step5_worst_case_model.log), [first run, wafer only](experiments/step5_run1_wafer_only.log). Bars were written at the top of the source before the first run. The founder's instruction: closing means fixing the failures and solving the problem, not passing at the central assumptions.

## Correction: the earlier "closed on the model" overstated the case

[Steps 3 and 4](step4_close_i_j_result.md) compared both machines at 64 sequences. A GPU cluster also gets cheaper per token with a bigger batch. With **each machine at its own best batch** (64 to 1,024 sequences, at least 30 tokens per second per sequence), the GPU cluster serves the 1T-parameter model for **$0.10 to $0.17 per million tokens** (14 GPUs, batch 1,024), not $1.34. The step 3 and step 4 cost advantages were mostly that batching gap. **Do not quote the cost figures of steps 3 and 4.** Their latency model and thresholds remain as inputs.

## Results (1T mixture-of-experts, 4-bit, MODELLED)

| corner | GPU cluster $/Mtok | wafer system $/Mtok | cost advantage | energy advantage |
|---|---|---|---|---|
| central (GPU 350 W, $25k; latency x1.8; wafer at the bottom-up price $169k) | 0.172 | 0.027 | 6.3x | 6.8x |
| **worst for us** (GPU 100 W, $15k; latency x2.7; wafer at the cited $2.5M) | 0.103 | 0.591 | **0.17x (wafer costs 5.8x more)** | **3.5x** |
| worst, but wafer at the bottom-up price | 0.103 | 0.041 | 2.5x | 3.5x |

Pre-set bars in the worst corner: **W1 (cost at most 0.5x the GPU) fails; W2 (facility energy at least 5x lower) fails.** Rows I and J are therefore **not closed**.

## What fixes each failure (levers, and what is still unproven)

1. **Cost: the wafer-scale system price is the problem, not the memory.** The wafer option beats the GPU cluster by 2x only if the whole system costs **at most about $214,000 per wafer** (9% of the cited $2.5M). Nobody has shown that for a 7.6 kW wafer-scale system with power delivery and cooling. **Option B: many ordinary reticle-size SRAM chips instead of one wafer** (no wafer-scale packaging; die about $330 on the third-party N5 wafer price, package/board/cooling $1,000 per chip ASSUMED, no source). It needs 511 chips for the 1T model with its cache at batch 1,024. In the worst corner it costs 2.9x less than the GPU cluster at $1,330 per chip, 1.7x less at $2,330 (misses the 2x bar), and 0.7x at $5,330 (loses). **The all-in cost per chip must stay under about $1,900.** That figure rests on the assumed packaging cost and is the number to obtain from a supplier quote.
2. **Energy: the SRAM read energy.** The worst corner gives 3.0x to 3.5x; the first scanned setting that reaches 5x is **1.6 pJ/bit** reads (the project range is 0.495 to 2.78). This is a circuit question: a weight-stationary bank read with short wiring. Next step is a bank-level SRAM energy model to see whether 1.6 pJ/bit is achievable.
3. **Still unmeasured:** GPU decode power (the worst corner assumes 100 W), real packaging and cooling cost, and whether the 80% SRAM part can be built.

## Reading

The memory problem is not solved by more SRAM alone. The model now says: SRAM-resident serving can save energy per token (3x to 7x depending on inputs) and per-sequence speed (300 to 900 against 49 tokens per second), but **cost per token against a well-batched GPU cluster depends on the all-in price of the silicon system, which is the item least supported by evidence.** The honest status of rows I and J is **partly covered, with a failing worst case and two named levers.**

Related: [Workload map](../docs/gpu_workload_map.md), [Step 4 result](step4_close_i_j_result.md), [Step 3 result](step3_cost_power_result.md), [Step 2 result](step2_wafer_sram_result.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
