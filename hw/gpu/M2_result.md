---
title: Our GPU, milestone M2 result - the cycle and energy model matches the simulator and the earlier energy model; its latency does not match the earlier latency model (31 Oct 2026, SIMULATED and MODELLED)
tags: [spark, gpu, m2, cycle-model, energy-model, result]
---

# M2 result (31 Oct 2026)

**SIMULATED (decode of the small transformer on the simulator) and MODELLED (the 1B-parameter case).** Plan and pre-set bars: [M2 plan](M2_plan.md). Simulator [`gpu_sim.rs`](sim/gpu_sim.rs) now has decode with a key-value cache (`KVAPP`, `ATTNC`), a time model and an energy model; decode program [`export_decode.py`](m2/export_decode.py); analytic model [`m2_model.py`](m2/m2_model.py); outputs [`m2/results/`](m2/results/m2_model.json). The earlier M1 results are unchanged by the extension (W8A8 and INT8-weight agreements reproduced). Constants (ASSUMED, from the earlier notes): clock 1 GHz; per tile 368 multiply-adds and 2,000 SRAM bytes per cycle, 64 vector lanes, 64-byte mesh links with 2 cycles per hop; SRAM 0.55 pJ per bit, 8-bit multiply-add 0.25 pJ (4-bit 0.12), vector operation 0.4 pJ, mesh 0.1 pJ per bit per hop; static 1.6 W per GB of SRAM.

## Results against the pre-set bars

| id | bar | result |
|---|---|---|
| **M2-a** counts | analytic multiply-adds and SRAM bytes per layer group within 5% of the simulator (small transformer, 64 decode steps) | **PASS**: equal in every group (embedding, 2 x attention, 2 x feed-forward, head); 104,890,368 multiply-adds, 108,626,176 bytes read |
| **M2-b** time | analytic cycles per token within 20% of the simulator's | **PASS**: 4,603 against 4,735 cycles per token (ratio 0.97); the model leaves out mesh transfer cycles (about 2% in the simulator) |
| **M2-c** decode equals full pass | the 64 decoded steps equal the full-sequence logits of M1 within 1e-4 | **PASS**: maximum difference 0 (identical) |
| **M2-d** energy | dense 1B model, 4-bit, context 2,048: energy per token within 20% of the step 5 model at the same constants | **PASS** at both batches: **batch 1: 3.26 mJ against 3.91 mJ (ratio 0.83)**; **batch 64: 1.41 mJ against 1.47 mJ (ratio 0.96)** |
| **M2-e** speed | latency per token within 20% of the step 4 and 5 latency model (calibration 1.8) | **FAIL** at both batches: **batch 1: 21 microseconds against 122 (ratio 0.18)**; **batch 64: 67 microseconds against 159 (ratio 0.42)** |

## What the numbers say

- **Energy is consistent across two independent builds.** The bottom-up model (per-operation counts times unit energies, static power of the occupied tiles) lands within 4% to 17% of the earlier chip-level model for the same 1B decoder; most of the energy is the same quantity in both: SRAM reads of the weights (0.44 GB read per token at batch 1, 4.4 pJ per byte) and of the key-value cache. At batch 1 the weights dominate (3.2 mJ of 3.3); at batch 64 the cache reads dominate (the weights are shared by 64 sequences). The 17% gap at batch 1 comes from the model size: the step 5 model reads 1.0 billion weights, this decoder (the dimensions fixed in the plan) 0.87 billion.
- **Latency does not agree, and the disagreement is informative.** The earlier latency model charges 6 synchronisation phases per layer at 0.5 microsecond of link time plus a wire term, calibrated by a factor 1.8 on vendor figures for multi-wafer machines; for a model that fits on one chip that link term does not exist, so it predicts 122 microseconds per token. The bottom-up cycle model, with the 1B decoder spread over 168 tiles, has 6 phases per layer of about 100 cycles of mesh latency (0.1 microsecond each) and about 1 microsecond of compute per layer, and predicts 21 microseconds (about 47,000 tokens per second per user). **Which is closer to a real chip is not settled by either model: the bottom-up model has no software, scheduling or imperfect-overlap overheads; the earlier model was calibrated on a different class of machine.** M3 (RTL of a tile) and M5 (a test chip) are what can decide.
- **Informational cross-check, not a bar:** the same cycle model on the two dense models for which a vendor reported per-user speeds on wafer-scale machines (16-bit weights, batch 1, short context, vendor figures: about 2,100 tokens per second for a 70B model and 969 for a 405B model, from the step 4 sources) gives **2,800 and 750 tokens per second (ratios 1.33 and 0.77)**: the right order, within about 35% either way, although the vendor configurations and the model's hypothetical mesh are not the same.

## Status of milestone M2

**Partly passed:** counts, cycles, decode equivalence and energy pass; **the speed bar against the earlier latency model fails (a factor of 2.4 to 5.7 faster in the new model)**. M2 delivers the cycle and energy model and its validation against the simulator; the open item is which latency figure to trust at small scale. Proposal for the next steps: keep both numbers (the bottom-up 21 microseconds and the conservative 122 microseconds) as a range for a 1B model on one chip until M3 gives cycle counts from RTL.

## Limits

All constants assumed; the simulator is functional with a coarse time model (no overlap of operations, no contention); the small model is a 2-layer transformer; the 1B case is analytic only (not simulated); no hardware.

Related: [M2 plan](M2_plan.md), [M1 result](M1_result.md), [M1 fix result](M1_fix_result.md), [ISA note](ISA_M1.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Hardware index](../HARDWARE_INDEX.md)
