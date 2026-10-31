---
title: Our GPU, milestone M3 - RTL of one tile (INT8 matrix engine): plan and pre-set bars (31 Oct 2026)
tags: [spark, gpu, m3, rtl, plan, bars]
---

# M3: RTL of one tile, first slice (31 Oct 2026)

**Written before the work.** Charter milestone M3 (*RTL of one tile, synthesised for the open 130 nm flow; bit-exact with the simulator on a layer; area, cells and cycle count reported*), moved ahead of M4 in the [finish plan](../../docs/product_finish_plan.md) because it can confirm or break the silicon-level constants every earlier model assumes.

## The slice

**`tile_mm`: the INT8 matrix engine of a tile.** Interface: the tile logic is synthesisable on its own; the weight memory (`w_addr`, `w_data`: one word of `LANES` int8 weights per read) and the activation memory (`a_addr`, `a_data`: one int8 per read) are outside it (a testbench model here; the tile's SRAM macros in a real chip), each with one cycle of read latency. For `m` activation rows, `k` reduction length and `nb` blocks of `LANES` output columns the engine streams `k` steps per (row, block), multiplies the broadcast activation by `LANES` weights, accumulates in `LANES` 32-bit accumulators and emits the accumulator vector with its (row, block) index. Pipeline: read, multiply, accumulate (3 stages). Parameters: `LANES` (synthesised at 64 and 256). Activation quantisation, dequantisation, bias and the vector operations stay in the vector unit (not in this slice), as in the instruction-set note.

## Pre-set bars

| id | bar |
|---|---|
| **M3-a** bit-exact | the RTL accumulators equal a numpy integer matrix product exactly (zero mismatches) on: the 8 x 16 x 8 self-test of M1; the query projection of the M1 transformer (64 rows, k = 256, n = 256, real INT8 weights of layer 0); the feed-forward up projection (16 rows, k = 256, n = 1,024, real INT8 weights); for both `LANES` = 64 and 256; and the dequantised result of the self-test equals the simulator's output |
| **M3-b** cycles | measured cycles for each case within 2% of `m x ceil(n / LANES) x k` plus the pipeline depth; for decode (one row, k = 256, n = 256) at `LANES` = 256 the utilisation (multiply-adds divided by cycles x lanes) is at least 90% |
| **M3-c** synthesis | the design synthesises to `sky130_fd_sc_hd` (typical corner) with Yosys without errors at both `LANES`; cells, flip-flops, area and the critical-path delay (OpenSTA) are reported |
| **M3-d** model consistency | the achieved tile rate (multiply-adds per cycle) and the 130 nm area per lane are reported next to the M2 constants (368 multiply-adds per cycle per 4 MB tile, 0.25 pJ per 8-bit multiply-add at the target node); the M2 decode model is rerun with the tile rate of the RTL; the modelled 1B decode energy per token must stay within 20% of its M2 value (energy is dominated by SRAM bytes), and the new latency range is reported |

A miss is reported as a miss; the bars are not changed after the run.

## Limits stated in advance

130 nm timing and area do not transfer directly to the modelled node (the 1 GHz clock of the M2 model is not reachable in 130 nm; any scaling to a modern node is an assumed ratio, labelled); no power analysis (energy per multiply-add is not measured here); the weight and activation memories are models, not macros; only the matrix engine is in the slice (no vector unit, no mesh interface, no control program); no place and route.

Related: [Finish plan](../../docs/product_finish_plan.md), [Own GPU charter](../../docs/own_gpu_charter.md), [M2 result](M2_result.md), [ISA note](ISA_M1.md), [Hardware index](../HARDWARE_INDEX.md)
