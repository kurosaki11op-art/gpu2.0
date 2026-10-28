---
title: L Forge lane RTL, tile model and tile-to-tile traffic
tags: [spark, result, simulated, estimate, l-forge, rtl]
---

# L Forge lane, tile model and fabric traffic (28 Oct 2026)

Three steps of the [L Forge design](../../docs/L_forge_design.md) build order: the arithmetic lane in RTL, a bit-exact model through which kernels can be run, and the tile-to-tile traffic that the earlier tile model left out. Files: [forge_lane.v](../rtl/forge/forge_lane.v), [forge_lane_golden.py](../brain/experiments/month5/forge_lane_golden.py), [forge_tile_model.py](../brain/experiments/month5/forge_tile_model.py), [forge_traffic_model.py](../brain/experiments/month5/forge_traffic_model.py) and their logs.

## 1. The lane is in RTL and bit-exact (SIMULATED)

A block of 16 signed 8-bit mantissa pairs plus block exponents per cycle, exact integer dot product, floating accumulator with a 16-bit mantissa magnitude and round to nearest (sizing from the [lane numerics](bfp_lane_numerics.md)). **3,288 random operations in sequences, including exponent gaps above 40 bits, 0 mismatches between the RTL and the integer golden model.** A vectorised emulation matches the scalar golden model on 300 random sequences (0 mismatches).

## 2. A matrix product through the lane (SIMULATED)

128 x 256 by 256 x 128: error against fp64 **1.03e-2 on normal data and 1.87e-2 on heavy-tailed data**, the same as the numpy emulation of the format (1.0e-2 and 1.9e-2), so the earlier format studies are valid for the real lane arithmetic, at least for matrix products. 262,144 block operations: one lane takes that many cycles, 1,024 tiles take 256.

## 3. Tile-to-tile traffic (ESTIMATED, assumptions stated in the script)

1,024 tiles as a 32 x 32 mesh on 3 dies; link energy per bit per hop swept 0.02, 0.05 and 0.2 pJ (reasoned from wire energy, not measured); die-to-die link 0.7 pJ per bit (assumed). Gain over a mixed-precision GPU baseline at 2 GB, before and after fabric energy, at 0.05 pJ per bit per hop:

| kernel | gain without fabric | gain with fabric (0.02 / 0.05 / 0.2 pJ per bit per hop) |
|---|---|---|
| Dense matrix multiply | 4.0x | 3.9 / 3.9 / 3.8x |
| 3D FFT | 5.1x | 4.8 / 4.6 / 3.9x |
| Poisson CG | 32.8x | 32.4 / 32.0 / 30.0x |
| CFD stencil | 8.2x | 8.1 / 8.1 / 7.6x |
| 1B language model, int8 | 48.2x | 24.4 / 23.7 / 20.6x |
| Ray tracing | 3.4x | 1.5 / 1.1 / 0.4x |
| Kalman, small network, sparse recognition | 2.5x, 20.6x, 35.8x | unchanged (no fabric traffic) |

Reading (ESTIMATED): **neighbour-exchange kernels (stencils, Poisson, matrix multiply) lose almost nothing to the fabric, the FFT loses 10 to 25%, the language model loses half (mostly from crossing dies, not the mesh: a model that fits on one die would keep most of its gain), and ray tracing, with its random fetches, falls to about 1x or below** and should be left to a GPU or dropped from the acceptance list. The conclusion rests on the assumed link energies; a layout-level estimate would replace them.

## 4. Lane synthesis (yosys, Gowin family; ASIC area ESTIMATED)

The lane synthesises to about 2,630 LUT4, 359 carry cells, 30 flip-flops and **16 9 x 9 multipliers**, with the wide aligner and normaliser (64-bit shifts) taking most of the logic. Rough ASIC size: about 39,000 NAND2-equivalent gates (LUT4 about 8, carry cell about 20, 9 x 9 multiplier about 700; a rough conversion) at an assumed 0.06 um2 per gate at 5 nm including routing gives **about 0.002 to 0.006 mm2 for the lane**, within the assumed tile logic of 0.005 to 0.015 mm2 (the tile also needs a router, control and bank interfaces, not designed yet). Narrowing the alignment shift from 40 to about 24 bits would cut the aligner roughly in half at negligible numeric cost (not done).

## 5. A tile that runs a matrix product in RTL, and the Kalman filter through the lane (SIMULATED)

[forge_tile_mm.v](../rtl/forge/forge_tile_mm.v) is a first tile: block memories for A and B (136-bit words: exponent plus 16 mantissas), the lane, an address generator and an output memory. [forge_tile_mm_check.py](../brain/experiments/month5/forge_tile_mm_check.py) runs a 16 x 128 by 128 x 16 product in iverilog: **0 of 256 outputs differ from the lane golden model; error against fp64 9.6e-3; 2,051 cycles for 2,048 block operations (32,768 multiply-accumulates), i.e. the lane is busy 99.9% of the time, 16 multiply-accumulates per cycle.** [forge_kalman_lane.py](../brain/experiments/month5/forge_kalman_lane.py): the 12-state Kalman filter with every matrix product through the bit-exact lane differs from the fp64 filter by 2.7e-2 to 3.5e-2 (3 seeds) and gives the same error against the truth (RMSE 1.030 against 1.028 for fp64). These are the first two of the four hand-mapped kernels (matrix multiply in RTL, Kalman through the lane arithmetic); the FFT and Poisson refinement are emulated at the format level only (earlier notes), not yet through the lane.

## Limits

Traffic volumes are first-order formulas for standard decompositions, not a simulated schedule; no contention, latency or buffering; the 1,024-tile grouping is a choice; the lane is verified alone, not inside a tile with memory and routing; no area or timing from synthesis yet.

Related: [Results index](INDEX.md), [L Forge design](../../docs/L_forge_design.md), [Lane numerics](bfp_lane_numerics.md), [FFT and Kalman routing](fft_kalman_routing.md), [Refinement loop](refinement_loop.md), [Forge RTL](../rtl/forge/README.md)
