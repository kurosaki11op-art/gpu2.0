---
title: Our GPU, milestone M3 result - the INT8 tile engine is bit-exact with the simulator, its rate recalibrates the M2 model, and the latency gap closes (31 Oct 2026, SIMULATED RTL and SYNTHESISED)
tags: [spark, gpu, m3, rtl, synthesis, result]
---

# M3 result (31 Oct 2026)

**RTL simulated with Icarus Verilog; synthesised with Yosys to `sky130_fd_sc_hd` (typical corner); timed with OpenSTA; no place and route, no power analysis, no hardware.** Plan and pre-set bars: [M3 plan](M3_plan.md). Files: [`rtl/tile_mm.v`](rtl/tile_mm.v) (the engine), [`rtl/tb_tile_mm.v`](rtl/tb_tile_mm.v), [`rtl/m3_check.py`](rtl/m3_check.py), results [`rtl/results/m3_check.json`](rtl/results/m3_check.json), synthesis scripts, statistics and timing logs in [`rtl/syn/`](rtl/syn/) (the large netlists are not kept). The engine streams `k` steps per (row, block): per step one word of `LANES` INT8 weights times one broadcast INT8 activation into `LANES` 32-bit accumulators; pipeline of three stages; weight and activation memories are outside the module.

## Bars (pre-set)

| id | bar | result |
|---|---|---|
| **M3-a** bit-exact | RTL accumulators equal a numpy integer matrix product (zero mismatches) on the self-test (8 x 16 x 8), the query projection (64 x 256 x 256, real INT8 weights of layer 0) and the feed-forward up projection (16 x 256 x 1,024), for 64 and 256 lanes; the self-test dequantised equals the simulator | **PASS**: 0 mismatches in all six runs (all output vectors present); the dequantised self-test equals the simulator's output (maximum difference 0.0) |
| **M3-b** cycles | within 2% of `m x ceil(n / LANES) x k` + pipeline; decode (one row, k = 256, n = 256, 256 lanes) utilisation at least 90% | **PASS**: 1.5% on the small self-test (133 against 131 cycles, the start handshake), 0.00% to 0.01% on the real layers (65,541 and 16,389 cycles); decode utilisation **98.1%** (261 cycles for 65,536 multiply-adds on 256 lanes) |
| **M3-c** synthesis | synthesises at both lane counts; cells, flip-flops, area and the critical path reported | **PASS** (below) |
| **M3-d** model consistency | rerun the M2 decode model with the RTL tile rate: 1B decode energy per token within 20% of the M2 value; new latency range reported | **PASS**: energy changes by **+0.3% (batch 1) and +0.8% (batch 64)**; latency below |

## Synthesis (130 nm, typical corner, memories outside the module)

| design | cells | area | flip-flops | critical path |
|---|---|---|---|---|
| 1 lane + control | 1,777 | 15,434 um2 | 343 | **7.04 ns** (reg to reg, ideal wires; the 8 x 8 multiplier into the product register) |
| 64 lanes | 46,198 | **355,421 um2 (0.36 mm2)** | 30% of the area | not meaningful, see below |
| 256 lanes | 181,476 | **1,397,070 um2 (1.40 mm2)** | 30% of the area (20,743 flip-flops) | not meaningful, see below |

- **Per lane about 5,400 um2** (the lane count slope: (1,397,070 - 355,421) / 192 = 5,425 um2; roughly 1,450 two-input-gate equivalents), of which the three register sets (16-bit product, 32-bit accumulator, 32-bit result copy, 80 flip-flops) are about 30%. The 32-bit result copy is an optional register that could be removed (about 12% of the area); the engine is not optimised.
- **Timing of the full netlists is not a valid number:** OpenSTA without buffering reports a violation of 208 ns (64 lanes) because one flip-flop drives the broadcast to every lane without buffers; place and route inserts the buffer tree. The valid timing figure is the single-lane path: **7.04 ns at 130 nm, about 140 MHz unpipelined**, with an array multiplier that the synthesiser built from the behavioural `*`. Pipelining the multiplier (not done) is the usual way to roughly halve it.
- **To the modelled node (ASSUMED ratios, not measured):** logic density about 100 times that of 130 nm (my recollection of published density figures, unsourced) puts a lane near 55 um2 and a 256-lane engine near 0.014 mm2, about **1% of the area of a 4 MB SRAM tile** (about 1.3 mm2 at the project's SRAM density). The assumed 1 GHz clock at that node (the multiplier path of 7 ns at 130 nm would be roughly 1.4 ns scaled by 5, so a pipelined multiplier is needed) remains an assumption.

## What changed in the M2 model (the point of doing M3 first)

The M2 constants (368 multiply-adds and 2,000 SRAM bytes per cycle per tile) were inconsistent: at batch 1 every multiply-add needs one weight byte, so a tile cannot use more SRAM bandwidth than it has lanes. The RTL tile runs **256 multiply-adds per cycle on 256 bytes per cycle**; the M2 decode model rerun with those two numbers gives:

| dense 1B decoder, 4-bit | earlier M2 constants | RTL tile rate | corrected reference model (35.6 us at batch 1, 92.7 us at batch 64) |
|---|---|---|---|
| batch 1, operations on occupied tiles | 21.4 us | **31.7 us** | ratio **0.89** |
| batch 64 | 66.8 us | **93.0 us** | ratio **1.00** |
| energy per token | 3.26 mJ / 1.41 mJ | 3.27 mJ / 1.42 mJ | within 0.3% to 0.8% |

**With constants taken from the RTL, the bottom-up latency now agrees with the corrected earlier latency model within 11% (batch 1) and 0.3% (batch 64): the M2-e bar (within 20%), which failed before, is met on this re-evaluation.** This is a re-evaluation with new constants after M3, not a retroactive pass of the original M2-e result (which stays recorded as a fail). **Caution:** the agreement may be partly a coincidence: the earlier model includes an overhead factor of 1.8 calibrated on vendor figures; the bottom-up model has no overhead factor and now lands at the same value. Planning range for the 1B decoder, from the two ends of variants A and B: about **19 to 32 microseconds per token at batch 1** (31,000 to 54,000 tokens per second per user) and **90 to 93 microseconds per step at batch 64**. The vendor cross-check (informational): 70B 2,730 tokens per second (vendor 2,100), 405B 744 (vendor 969).

## Status of milestone M3

**Passed on all four bars** for the first slice. **Not covered by this slice (stated gaps):** the vector unit, the mesh interface, the control program and sequencing across layers, the SRAM macros themselves, a pipelined multiplier, place and route, power (energy per multiply-add is **not measured**; 0.25 pJ is still an assumed constant), and timing at the modelled node. **Next:** M4 (compiler front end, real model), then the hardware gate.

**Correction after Vision review 01 (31 Oct 2026), V-01):** the planning range of 19 to 32 microseconds per token (batch 1) and the agreement with the reference latency model assume a striped mapping of every matrix over all tiles of the chip, which the instruction set and the simulator cannot express; both models share that assumption, so their agreement is not evidence for it. As implemented (a matrix on as few tiles as it needs) the 1B decoder takes about **2.4 milliseconds per token** at the RTL tile rate. The RTL result itself (bit-exact accumulators, cycles, synthesis) is unaffected.

Related: [M3 plan](M3_plan.md), [M2 result](M2_result.md), [ISA note](ISA_M1.md), [Finish plan](../../docs/product_finish_plan.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Hardware index](../HARDWARE_INDEX.md)
