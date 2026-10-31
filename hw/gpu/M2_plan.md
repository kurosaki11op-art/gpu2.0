---
title: Our GPU, milestone M2 - cycle and energy model validated against the simulator, applied to 1B-parameter decode: plan and pre-set bars (31 Oct 2026)
tags: [spark, gpu, m2, cycle-model, energy-model, plan, bars]
---

# M2: cycle and energy model (31 Oct 2026)

**Written before the work.** Charter: [own GPU charter](../../docs/own_gpu_charter.md), milestone M2: *cycle and energy model validated against the simulator for batch-1 and batch-64 decode of a 1B-parameter model (4-bit); bars: energy per token within 20% of the step 6 model's value at the same constants, speed within 20% of the latency model.* The founder asked for M2 after M1 and its fix ([M1 result](M1_result.md), [M1 fix](M1_fix_result.md)).

## What is built

1. **Simulator extension (Rust, `sim/gpu_sim.rs`):** decode with a key-value cache (`KVAPP` appends the new key or value row to a cache held in the tile's SRAM, `ATTNC` attends one query over the cache), a **time model** (cycles per instruction from compute, SRAM and mesh limits) and an **energy model** (picojoules per multiply-add, SRAM byte, vector operation and mesh byte-hop, plus static power over the elapsed cycles). Parameters (all ASSUMED, from the earlier models): clock 1 GHz; per tile 368 multiply-adds per cycle (the 10 PMAC/s per 46,225 mm2 figure scaled to a 4 MB tile) and 2,000 SRAM bytes per cycle (the per-GB bandwidth of the wafer model); 64 vector lanes; mesh links 64 bytes per cycle, 2 cycles per hop; SRAM read and write 0.55 pJ per bit; 8-bit multiply-add 0.25 pJ (4-bit 0.12 pJ, 16-bit-activation operations 0.5 pJ); vector operation 0.4 pJ; mesh 0.1 pJ per bit per hop; static 1.6 W per GB of SRAM.
2. **Analytic model (Python, `m2/m2_model.py`):** per-token counts, cycles and energy of a dense decoder from its dimensions (layers, width, feed-forward width, heads, vocabulary, context, batch, weight bits, cache bits), with the same constants.
3. **Decode program** for the M1 transformer (2 layers, d = 256) run for 64 steps in the simulator, and the analytic model for a **dense 1B-parameter decoder** (16 layers, d = 2,048, feed-forward 8,192, vocabulary 32,000, context 2,048, 4-bit weights, 16-bit cache) at batch 1 and 64.

## Pre-set bars

| id | bar |
|---|---|
| **M2-a** counts | for the small transformer decoded for 64 steps (context 1 to 64): analytic multiply-adds and SRAM bytes per layer group (embedding, attention, feed-forward, head), summed over steps, within 5% of the simulator's |
| **M2-b** time | analytic cycles per token within 20% of the simulator's, mean over the 64 steps |
| **M2-c** decode equals full pass | the logits of the 64 decoded steps (key-value cache) equal the full-sequence logits of M1 for the same window, relative error at most 1e-4 in fp32 |
| **M2-d** energy | dense 1B model, 4-bit, context 2,048, batch 1 and 64: the model's energy per token within 20% of the step 5 model's value at the same constants (SRAM 0.55 pJ/bit, 420 mm2 per GB, 4-bit multiply-add 0.12 pJ, leakage 1.6 W/GB), central corner |
| **M2-e** speed | the same two cases: latency per token (batch 1) and step time (batch 64) within 20% of the latency model (step 4 and 5, with its calibration factor 1.8) |

A miss is reported as a miss; the bars are not changed after the run. **Known difference in scope:** the new model also charges mesh energy and tile-level static power that the step 5 model does not itemise, so M2-d may differ by more than 20% for that reason; if it does, the miss is reported with the breakdown.

Related: [Own GPU charter](../../docs/own_gpu_charter.md), [M1 result](M1_result.md), [M1 fix result](M1_fix_result.md), [ISA note](ISA_M1.md), [Hardware index](../HARDWARE_INDEX.md)
