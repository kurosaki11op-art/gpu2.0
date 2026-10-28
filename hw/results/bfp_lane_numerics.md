---
title: L Forge block floating-point lane numerics (mantissa, block size, accumulator, rounding)
tags: [spark, result, simulated, l-forge, precision]
---

# L Forge multiply-accumulate lane numerics (28 Oct 2026)

Sizing the multiply-accumulate lane of the L Forge tile ([design](../../docs/L_forge_design.md)): operand mantissa bits m, block size (values sharing one exponent), accumulator width and the rounding of the mantissas. Script and log: [bfp_lane_numerics.py](../brain/experiments/month5/bfp_lane_numerics.py), `bfp_lane_numerics.log`. **SIMULATED (numpy emulation), a 64 x 256 by 256 x 64 matrix product, relative Frobenius error against fp64, one seed, normal and heavy-tailed (Student t, 2 degrees of freedom) data.** A lane forms exact integer products and an exact integer sum inside each block, scales by the block exponents, and adds block sums into an accumulator that keeps A mantissa bits with round-to-nearest.

| operand mantissa m | error, normal data | accumulator needed (error within 10% of the exact-accumulator floor) |
|---|---|---|
| 4 | 1.7e-1 | 8 bits |
| 5 | 8.4e-2 | 8 bits |
| 6 | 4.2e-2 | 8 bits |
| **8** | **1.0e-2** | **11 bits** (8 bits costs 10% more error) |
| 10 | 2.6e-3 | 11 bits |
| 12 | 6.6e-4 | 16 bits (11 bits gives 8.8e-4) |

- **The accumulator needs only about m + 3 to 4 mantissa bits, far below fp32's 24.** Error is set by the operand mantissa, as expected from the earlier primitive test (8-bit blocks, about 1e-2).
- **Block size: smaller is more accurate,** 8.8e-3 (block 8) to 1.3e-2 (block 64) on normal data and 1.7e-2 to 3.3e-2 on heavy-tailed data, because one outlier sets the exponent for its whole block. Block 16 is a middle choice (exponent overhead 0.5 bit per value); block 8 for heavy-tailed data.
- **Round to nearest, not truncation:** truncating the mantissas doubles the error (1.0e-2 to 2.5e-2 on normal, 1.9e-2 to 3.7e-2 on heavy-tailed data), because it biases every product.
- **Design reading (SIMULATED):** an L Forge lane with 8-bit mantissas, 16-value blocks, an 11-bit-mantissa accumulator and round to nearest gives about 1e-2 matrix-product error; for solver kernels the refinement loop recovers full accuracy, for direct kernels 12-bit mantissas and a 16-bit accumulator give about 1e-3.

Limits: random matrices only; the accumulator model is floating-point style (a fixed-point accumulator aligned to the maximum exponent would behave differently); no area or energy numbers (those need synthesis); one seed.

Related: [Results index](INDEX.md), [FFT and Kalman routing](fft_kalman_routing.md), [Refinement loop](refinement_loop.md), [Arithmetic primitive shoot-out](arithmetic_primitive_test.md), [L Forge design](../../docs/L_forge_design.md)
