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

[forge_tile_mm.v](../rtl/forge/forge_tile_mm.v) is a first tile: block memories for A and B (136-bit words: exponent plus 16 mantissas), the lane, an address generator and an output memory. [forge_tile_mm_check.py](../brain/experiments/month5/forge_tile_mm_check.py) runs a 16 x 128 by 128 x 16 product in iverilog: **0 of 256 outputs differ from the lane golden model; error against fp64 9.6e-3; 2,051 cycles for 2,048 block operations (32,768 multiply-accumulates), i.e. the lane is busy 99.9% of the time, 16 multiply-accumulates per cycle.** [forge_kalman_lane.py](../brain/experiments/month5/forge_kalman_lane.py): the 12-state Kalman filter with every matrix product through the bit-exact lane differs from the fp64 filter by 2.7e-2 to 3.5e-2 (3 seeds) and gives the same error against the truth (RMSE 1.030 against 1.028 for fp64). These are the first two of the four hand-mapped kernels (matrix multiply in RTL, Kalman through the lane arithmetic); Poisson refinement with its dot products computed by the bit-exact lane ([forge_poisson_lane.py](../brain/experiments/month5/forge_poisson_lane.py)) converges exactly as with exact accumulation (9 outer steps, 27 inner iterations, residual 1.9e-13 on 31 x 31 and 7.6e-13 on 63 x 63); the FFT is emulated at the format level only (earlier notes), and mapping it through the lane is wasteful at small sizes (a radix-2 butterfly fills 2 of the 16 lane slots; computing small DFTs as matrix products keeps the lane full but needs about 8 times more multiply-accumulates).

## 6. Synthesis of the whole first tile (yosys, Gowin family)

Lane plus the matrix-product control and its memories for the 16 x 128 x 16 test: about 2,960 LUT4, 479 carry cells, about 210 flip-flops, 16 9 x 9 multipliers and 8 block-RAM blocks, so a full tile with this control is not much bigger than the lane alone; a router, scheduler and the other kernels' control are not included.

## 7. The FFT through the lane (SIMULATED, with an ESTIMATED consequence)

[forge_fft_lane.py](../brain/experiments/month5/forge_fft_lane.py), log `forge_fft_lane.log`: small DFTs computed as real matrix products so the lane stays full, with an optional two-word split (x = xh + xl, three lane passes for about 16 mantissa bits). 64-point transforms (batch of 64): **error 9.3e-3 with one pass, 5.5e-5 with three passes**; four-step 256-point transforms (two 16-point stages, twiddles in fp64): 1.3e-2 and 6.7e-5. The cost: matrix-product DFTs need about **21 times (64-point) and 8 times (256-point) more lane block operations than an ideal radix-2 FFT at full lane use**, and three times more again for the 16-bit-class result. In the tile model the FFT's compute is 6% of its energy; multiplying it by 8 (one pass) or 24 (three passes) cuts the FFT gain at 2 GB from 4.6 times (with fabric) to about **3.6 times at 8-bit accuracy and about 2.1 times at 16-bit-class accuracy** (ESTIMATED from those factors). A radix-2 mapping would fill only 2 of 16 lane slots; a dedicated butterfly path would be needed to keep the ideal figure.

## 8. The Kalman inverse on the lane too (SIMULATED)

[forge_kalman_lane_inv.py](../brain/experiments/month5/forge_kalman_lane_inv.py): the 6 x 6 matrix inverse of the Kalman filter is computed by 8 Newton-Schulz iterations (X <- X (2I - S X), matrix products only, started from a scaled transpose), so every multiplication in the filter, including the inverse, runs on the lane and **no high-precision path is needed for it**. Result (3 seeds): difference from the fp64 filter 2.7e-2 to 3.4e-2, RMSE against the truth 1.031 against 1.028 for fp64, mean residual of the lane inverse ||S^-1 S - I|| 3.1e-2. Limits: a well-conditioned 12-state system; Newton-Schulz needs a fixed iteration count and a safe starting scale; ill-conditioned covariances are untested.

## 9. Check of the traffic assumption in RTL (SIMULATED)

[Tile mesh test](mesh_test.md): a 4 to 64 tile mesh with deliver-and-forward routers computes a distributed matrix product bit-exact; each word crosses one link per delivered copy (1.00 traversals per delivered word), as the traffic model assumed for broadcasts, but only if routers can forward while delivering; communication takes 17 to 19% of the cycles unless overlapped with compute. The FFT's all-to-all transpose through general routers is tested too: delivered correctly at 4 to 64 tiles, link traversals per flit equal to the mean Manhattan distance (2p/3) the model assumed, but with 3.5 to 6.8 blocked cycles per flit and 2.4 to 3 times the bisection bound in time.

## Limits

Traffic volumes are first-order formulas for standard decompositions, not a simulated schedule; no contention, latency or buffering; the 1,024-tile grouping is a choice; the lane is verified alone, not inside a tile with memory and routing; no area or timing from synthesis yet.

Related: [Results index](INDEX.md), [L Forge design](../../docs/L_forge_design.md), [Lane numerics](bfp_lane_numerics.md), [FFT and Kalman routing](fft_kalman_routing.md), [Refinement loop](refinement_loop.md), [Forge RTL](../rtl/forge/README.md)
