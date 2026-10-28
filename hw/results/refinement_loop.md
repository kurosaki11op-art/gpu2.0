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

Done in round 2: inner cap, preconditioner, fp16 diagnosis. Still to do: routed precision for FFT and the Kalman filter; the block floating-point multiply-accumulate lane numerics; a looser outer schedule to cut the fp64 share; variable-coefficient and anisotropic problems.

## Round 2 (28 Oct 2026): bigger cap, multigrid preconditioner, fp16 fix

Script and log: [refinement_loop2.py](../brain/experiments/month5/refinement_loop2.py), `refinement_loop2.log`. SIMULATED, one seed, grids 31, 63, 127 (multigrid needs 2^k - 1), target 1e-12. The preconditioner is one multigrid V-cycle built only from stencil operations (weighted Jacobi smoothing, full-weighting restriction, bilinear interpolation, exact solve on a 3 x 3 coarse grid), run in the low-precision format. Traffic is an ESTIMATED proxy (multigrid-preconditioned iteration 29 vector passes).

| fix | result |
|---|---|
| **fp16 fix (scale the inner residual by a power of two, unscale the correction)** | **fp16 now converges on every grid** (it stalled at 7e-8 before). Diagnosis confirmed: the stall was the fp16 subnormal floor (6e-8), underflow of small corrections, not a precision limit. With plain CG fp16 still moves 0.58 to 0.92 of fp64's bytes (2 bytes per value) |
| **Bigger inner cap (60 to 250)** | only matters on the largest grid: BFP8 traffic 0.64 to 0.53, outer steps 35 to 22; no change on the smaller grids |
| **Multigrid preconditioner** | inner iterations fall from 321 / 706 / 2,100 (BFP8, plain CG) to **27 / 30 / 30**; outer steps 9 to 10; BFP8 and int8 reach 1e-12 on all grids; BFP5 reaches it too (24 to 43 outer steps, traffic 0.32 to 0.43); fp16 and bfloat16 also converge |

**The fair comparison matters.** Against plain fp64 CG the traffic proxy looks like 0.15, 0.08 and 0.04 (BFP8, multigrid), but most of that is multigrid itself (13 fp64 multigrid iterations against 122 to 484 plain CG iterations). Against an equally preconditioned fp64 multigrid-CG (13 iterations, 3,016 traffic units) the BFP8 refinement uses **0.49, 0.54 and 0.54** of the bytes. So: **multigrid, which is stencil adds and shifts, gives the large algorithmic saving; 8-bit precision routing gives about a further factor of 2 in traffic**, not an order of magnitude. The share of traffic in fp64 is 43% for BFP8 with multigrid (higher than the 10% assumed in the tile model, because the inner solve is now short); a looser outer schedule (fewer fp64 residual steps) is untested.

Caveats unchanged: one seed, constant-coefficient Poisson, wide exact accumulation assumed in dot products, compute energy and fabric traffic not counted, multigrid in low precision is only approximately symmetric.

Related: [Results index](INDEX.md), [L Forge design](../../docs/L_forge_design.md), [Arithmetic primitive shoot-out](arithmetic_primitive_test.md), [Build plan](../../docs/L_build_plan_dec_jan.md)
