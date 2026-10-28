---
title: Arithmetic primitive shoot-out (multiplier alternatives on matmul, FFT, CG, Kalman)
tags: [spark, result, simulated, estimate, accelerator]
---

# Arithmetic primitive shoot-out (28 Oct 2026)

Question (founder): can a primitive other than multiplication and ternary weights do everything GPUs and models do? Test: emulate each multiplier alternative in numpy, keep accumulation exact, run four kernels against an fp64 truth. Script and log: [arithmetic_primitive_test.py](../brain/experiments/month5/arithmetic_primitive_test.py), `arithmetic_primitive_test.log`. **Error is SIMULATED; energy per multiply is ESTIMATED** (fp32 3.7, fp16 1.1, int8 0.2 pJ are Horowitz 2014 reference values; every other energy is our assumption, and is the weakest part of this table). One seed, small sizes (matmul 128, FFT 1024, CG 32x32, Kalman 4 states).

| primitive | matmul | FFT | CG final residual (iterations to 1e-6) | Kalman | pJ per multiply |
|---|---|---|---|---|---|
| fp32 | 4e-8 | 7e-8 | 7e-8 (85) | 7e-8 | 3.7 |
| fp16 | 3e-4 | 5e-4 | 1.2e-2 (96) | 5e-4 | 1.1 |
| bfloat16 | 6e-3 | 2e-2 | 4e-3 (120) | 4e-2 | 1.0 (assumed) |
| int8 | 1.4e-2 | 2.0e-2 | 2.5e-2 (107) | 1.0e-2 | 0.2 |
| block floating point, 8-bit mantissa | 7.9e-3 | 2.0e-2 | 1.8e-2 (98) | 1.7e-2 | 0.22 (assumed) |
| block floating point, 5-bit mantissa | 6e-2 | 1.5e-1 | 2e-1 (never) | 1.4e-1 | 0.08 (assumed) |
| int4 lookup table | 2.5e-1 | 3.7e-1 | 425 (diverges) | 4.6e-1 | 0.05 (assumed) |
| logarithmic number, 8 steps per octave (multiply = add) | 3.5e-2 | 6.7e-2 | 9e-2 (172) | 2.2e-1 | 0.15 (assumed) |
| logarithmic number, 3 steps per octave | 9e-2 | 2.2e-1 | 1.3 (never) | 6e-1 | 0.10 (assumed) |
| stochastic, N=256 | 1.1 | 0.75 | 0.86 (never) | broke (nan) | 0.2 (assumed) |
| stochastic, N=4096 | 2.8e-1 | 1.8e-1 | 1.7e-1 (never) | 1.6e-1 | 3.2 (assumed) |
| analog, 1% noise | 1.8e-1 | 1.2e-1 | 1.0e-1 (161) | 1.0e-1 | 0.07 (assumed) |
| analog, 5% noise | 8.9e-1 | 6.0e-1 | 0.44 (never) | broke (nan) | 0.07 (assumed) |

## Reading it (SIMULATED error; the energy column is assumption-heavy)

1. **No alternative does everything.** Logarithmic numbers, stochastic and analog all lose one or more kernels (CG never converges or Kalman breaks) at the settings where their energy is lower than int8's. The only formats that pass all four with error at 1e-2 or better are fp16, bfloat16, int8 and block floating point with an 8-bit mantissa.
2. **Block floating point 8-bit is the best cheap all-rounder here:** matmul error half of int8's at about the same assumed energy. int8 is already near the floor of the table for cost.
3. **The logarithmic multiplier saves nothing against int8:** its assumed 0.15 pJ is close to int8's 0.2, and its error is 2 to 20 times worse.
4. **Even the good low-precision formats stall CG at a true residual of 1e-2** (fp16 1.2e-2, int8 2.5e-2); physics needs a high-precision refinement step, as the tile model's routed-precision assumption already said.
5. Together with the [tile model](../../docs/L_numeric_tile_study.md) (the multiplier is 1 to 12% of memory-bound kernel energy): the primitive is a minor lever. The levers are capacity, locality and skipping.

## Caveats

Energies other than Horowitz's are assumed. Stochastic and analog noise is set relative to the largest product in the tensor, a harsh choice that a real design would soften with per-block scaling, so their rows are pessimistic. Accumulation was exact; real formats also round accumulators. One seed, small sizes.

Related: [Results index](INDEX.md), [Numeric tile study](../../docs/L_numeric_tile_study.md), [Project memory](../../docs/PROJECT_MEMORY.md)
