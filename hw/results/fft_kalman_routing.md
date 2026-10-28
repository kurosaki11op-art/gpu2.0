---
title: L Forge precision routing for the FFT and the Kalman filter
tags: [spark, result, simulated, l-forge, precision]
---

# FFT and Kalman precision routing (28 Oct 2026)

Next gate for difference D2 of the [L Forge design](../../docs/L_forge_design.md). Scripts and logs: [fft_kalman_routing.py](../brain/experiments/month5/fft_kalman_routing.py), [kalman_truth_check.py](../brain/experiments/month5/kalman_truth_check.py), `fft_kalman_routing.log` (same folder). **SIMULATED (numpy emulation of the number formats), small problems, one to three seeds.** Block floating point (BFP) uses a block of 16 values with a shared exponent; the number is the mantissa bits.

## FFT (n = 1024 complex, rounded after every stage)

| format | error against fp64 |
|---|---|
| BFP5 | 2.0e-1 |
| BFP8 / int8 / bfloat16 | 2.4e-2 / 2.6e-2 / 3.4e-2 |
| BFP10 | 5.9e-3 |
| BFP12 | 1.4e-3 |
| fp16 | 7.2e-4 |
| BFP16 | 9.2e-5 |
| BFP24 / fp32 | 3.7e-7 / 9.4e-8 |

Error falls about a factor of 4 for every 2 extra mantissa bits. **A bare FFT cannot be refined, so its precision has to be chosen by the tolerance of the job**: BFP8 for about 2% (imaging, audio, rough spectra), BFP12 to BFP16 for 1e-3 to 1e-4.

**FFT as the inner solver of a refinement loop** (periodic screened Poisson 64 x 64, solved spectrally in low precision, residual in fp64, target 1e-12): BFP8 reaches it in 23 outer steps, BFP12 in 7, fp16 in 5, bfloat16 in 12; BFP5 and int8 fail (int8's single scale per tensor is poor for the FFT's dynamic range). **But a single fp64 spectral solve reaches 2e-15 directly, and 23 low-precision solves move about three times the bytes of one fp64 solve** (even BFP12 at 7 steps and fp16 at 5 steps cost more bytes than one fp64 pass by a rough count). So refinement does not pay for a constant-coefficient FFT solve; it would pay only where the FFT is an approximate preconditioner for a problem the FFT cannot solve directly (untested).

## Kalman filter (12 states, 6 measurements, 1000 steps, 3 seeds)

Relative difference of the estimate from the fp64 filter, all stages in the format: BFP8 3.6e-2, int8 2.9e-2, bfloat16 9.9e-2, fp16 1.2e-3, fp32 1.3e-7. Keeping the covariance update in fp64 (29% of the flops) changes the error by under 2%; keeping the whole covariance in fp64 (67% of the flops) reduces it by about 12 to 25% in the 8-bit formats; the Joseph form gives no gain. The covariance stayed positive definite in every case. **The error is set by the format of the state and gain path, and routing the covariance to fp64 buys little for its cost.**

**Against the truth, which is what an estimator is for**, the all-low filter is as good as fp64 (RMSE of the estimate, 3 seeds): fp64 1.028, fp32 1.028, fp16 1.028, int8 1.027, BFP8 1.032, bfloat16 1.035. The filter's own noise floor hides the rounding error.

## What it means (SIMULATED, with limits)

1. **FFT: no refinement shortcut.** L Forge should store FFT data in a block format with the width the job needs (8 to 16 mantissa bits) and use no high-precision share unless the FFT sits inside a larger solver.
2. **Kalman: no fp64 needed for this well-conditioned 12-state case;** BFP8 or int8 everywhere gives the same accuracy against the truth. Square-root forms and fp32 would be needed for ill-conditioned systems (untested).
3. **Precision routing helps iterative solvers (Poisson, about 2x on traffic) and almost nothing for direct transforms and small filters.** The 10% fp64 share assumed in the tile model should be applied only to solver-type kernels. The honest D2 claim is therefore narrower than in the design note.

Limits: one problem size per test; no ill-conditioned or non-stationary filters; no 2D or 3D FFT of realistic size; traffic comparisons are rough byte counts; accumulation width in hardware is assumed wide.

## Next

Block floating-point multiply-accumulate lane numerics (accumulator width, rounding, block size), then the bit-exact integer model of the tile.

Related: [Results index](INDEX.md), [Refinement loop](refinement_loop.md), [L Forge design](../../docs/L_forge_design.md), [Arithmetic primitive shoot-out](arithmetic_primitive_test.md)
