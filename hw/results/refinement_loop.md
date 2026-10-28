---
title: L Forge refinement loop - low-precision solves refined to fp64 accuracy
tags: [spark, result, simulated, l-forge, precision]
---

# L Forge refinement loop (28 Oct 2026)

Gate test for difference D2 of the [L Forge design](../../docs/L_forge_design.md): can bulk work run in cheap low-precision arithmetic while a small share in fp64 brings the answer to full accuracy? Problem: 2D Poisson, five-point stencil, random right-hand side, target relative residual 1e-12. Method: outer loop in fp64 (true residual, update); inner conjugate-gradient solve with every stored vector rounded to the format, stopping at a 1e-2 residual drop or 60 iterations. Baseline: fp64 CG. Script and log: [refinement_loop.py](../brain/experiments/month5/refinement_loop.py), `refinement_loop.log`. **SIMULATED accuracy and iteration counts (numpy emulation of the formats); one seed; the traffic figure is an ESTIMATED proxy** (vector passes times bytes per element; compute energy not counted).

## Results

| grid (unknowns) | fp64 CG iterations | format | outer steps | inner iterations | reached 1e-12 | traffic vs fp64 CG | share of traffic in fp64 |
|---|---|---|---|---|---|---|---|
| 32 x 32 (1,024) | 128 | BFP8 | 12 | 339 | yes | 0.43 | 19% |
| | | int8 | 13 | 363 | yes | 0.44 | 20% |
| | | bfloat16 | 13 | 431 | yes | 0.93 | 9% |
| | | BFP5 | 36 | 1,486 | yes | 1.23 | 19% |
| | | fp16 | 60 | 3,383 | **no** (7e-8) | 6.99 | 5% |
| 64 x 64 (4,096) | 249 | BFP8 | 15 | 709 | yes | 0.43 | 12% |
| | | int8 | 17 | 781 | yes | 0.45 | 13% |
| | | bfloat16 | 16 | 864 | yes | 0.92 | 6% |
| | | BFP5 | 60 | 3,590 | **no** (1e-11) | 1.44 | 14% |
| | | fp16 | 60 | 3,600 | **no** (7e-8) | 3.81 | 5% |
| 128 x 128 (16,384) | 494 | BFP8 | 32 | 1,920 | yes | 0.57 | 9% |
| | | int8 | 32 | 1,920 | yes | 0.54 | 10% |
| | | bfloat16 | 28 | 1,680 | yes | 0.90 | 5% |
| | | BFP5 | 60 | 3,600 | **no** (5e-6) | 0.73 | 14% |
| | | fp16 | 60 | 3,600 | **no** (9e-8) | 1.92 | 5% |

## What it shows (SIMULATED, one seed)

1. **The idea works: an 8-bit inner solve (BFP8 or int8) refined in fp64 reaches full fp64 accuracy on all three grids.** With the traffic proxy it moves about 0.43 to 0.57 of the vector bytes of a plain fp64 CG (a saving of roughly a half, not an order of magnitude).
2. **The share of work in fp64 is 9 to 20% of the traffic and falls as the problem grows** (19%, 12%, 9% for BFP8), consistent with the 10% assumed in the tile model.
3. **Format limits:** BFP5 fails on the larger grids; bfloat16 converges but saves almost nothing (2 bytes per value); **fp16 fails everywhere** (stalls near 1e-7). The fp16 failure is not diagnosed: it may be underflow of small corrections (a scaling problem) and not lack of precision.
4. **Cost of refinement:** inner iterations are 2.6x, 2.8x and 3.9x the fp64 CG count, and on the 128 grid every inner solve hit the 60-iteration cap, so the saving is shrinking with size.

## Limits and what is not tested

One seed, one problem (constant-coefficient Poisson, no preconditioner); the inner cap limits the largest grid; dot products assume a wide exact accumulator (needs hardware support); compute energy, fabric traffic and the cost of block-exponent logic are not counted; no FFT or Kalman refinement yet; the capacity benefit (inner vectors are 8x smaller, so more problem fits on chip) is not modelled.

## Next

Raise the inner cap and test a simple preconditioner on the 128 grid; diagnose the fp16 failure with residual scaling; routed precision for FFT and the Kalman filter; then the block floating-point multiply-accumulate lane numerics.

Related: [Results index](INDEX.md), [L Forge design](../../docs/L_forge_design.md), [Arithmetic primitive shoot-out](arithmetic_primitive_test.md), [Build plan](../../docs/L_build_plan_dec_jan.md)
