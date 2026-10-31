---
title: M1 fix - the W8A8 transformer miss (98.73%): per-layer activation precision chosen on a calibration set, bar written before the change (31 Oct 2026)
tags: [spark, gpu, m1, quantisation, fix, bars]
---

# M1 fix: the W8A8 transformer miss (31 Oct 2026)

**Written before any change.** [M1 result](M1_result.md): in the instruction set's W8A8 configuration the transformer agrees with the fp32 top-1 on 98.73% of 1,024 positions (bar 99%); all 13 disagreements are near-ties. Founder: fix the M1 failures first.

## Hypothesis and fix

A few matrix operations carry activations whose range is dominated by outliers (typical of the inputs to the output projection and to the second feed-forward matrix after GELU), so a per-row INT8 scale loses the small values. **Fix (a hardware-plausible mixed-precision rule):** each weight tensor gets an activation precision, default INT8, optionally INT16 (the matrix array runs 8 x 16 for that operation at about twice the multiply-add energy). The simulator gets the annotation `W name tile a16` (and `af` for FP activations, used only to measure sensitivity).

## Procedure (fixed in advance, so that the fix is not chosen on the test positions)

1. **Calibration set:** 16 windows of the held-out text at offsets that do not overlap the earlier evaluation windows; reference = the simulator's fp32 outputs (equal to PyTorch to 7e-7).
2. **Sensitivity:** for each of the 13 weight tensors, set only that tensor to FP activations and record the gain in top-1 agreement on the calibration set.
3. **Choice:** add tensors to the INT16 list in order of gain until the calibration agreement is at least 99.5% (a margin above the bar), with a limit of 5 tensors.
4. **Evaluation:** the original 1,024 evaluation positions and a **fresh set** of 1,024 positions (16 new windows), neither used in the choice.

## Pre-set bar

| id | bar |
|---|---|
| **M1F-a** | top-1 agreement of the mixed-precision configuration with the fp32 reference is at least 99% on **both** evaluation sets (the original and the fresh one) |
| **M1F-b** | at most 5 of the 13 weight tensors need INT16 activations; the counted multiply-adds in INT16 are reported as a share of the total, with the multiply-add energy overhead at 2x for those |
| **M1F-c** | the CNN stays at 99% or above in the same configuration (no INT16 needed) |

A miss is reported as a miss; no bar changes after the run.

Related: [M1 result](M1_result.md), [ISA note](ISA_M1.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Hardware index](../HARDWARE_INDEX.md)
