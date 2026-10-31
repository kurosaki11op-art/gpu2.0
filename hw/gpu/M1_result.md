---
title: Our GPU, milestone M1 result - the functional simulator runs a CNN and a transformer and matches PyTorch (31 Oct 2026, SIMULATED)
tags: [spark, gpu, m1, simulator, result, int8]
---

# M1 result (31 Oct 2026)

**SIMULATED** (functional simulator on the cloud container's CPU; no hardware). Instruction set and programming model: [ISA note](ISA_M1.md). Simulator [`gpu_sim.rs`](sim/gpu_sim.rs) (Rust, standard library only), exporter and mapper [`export_models.py`](m1/export_models.py), checks [`m1_check.py`](m1/m1_check.py), results in [`m1/results/`](m1/results/m1_check.json). Bars (written before the work, [charter](../../docs/own_gpu_charter.md)): **(a)** outputs match PyTorch fp32 within a relative error of 1e-2; **(b)** with INT8 weights, top-1 agreement at least 99% on 1,000 inputs; **(c)** counted multiply-adds and SRAM bytes per layer within 5% of the analytic model.

## What was run

- **A convolutional network** (two 3x3 convolutions with ReLU and pooling, then a linear layer; 87% accuracy on Fashion-MNIST after 3 epochs of training): 1,000 test images through 3 tiles of a 2 x 2 mesh. Instructions used: `W`, `CONV`, `RELU`, `MAXPOOL2`, `FLATTEN`, `MM`.
- **A character-level transformer decoder** (2 layers, d = 256, 4 heads, feed-forward 1,024, context 64, 128 characters; about 1.7 million weights; trained for 900 steps on WikiText-2 text to a training loss of 1.77 nats): 16 held-out text windows, 1,024 positions, through 4 tiles. Instructions used: `GATHER`, `LN`, `MM`, `ATTN`, `GELU`, `ADD`.
- **Three numeric modes:** `fp32` (reference), `w8` (INT8 weights per output channel, FP32 activations), `int8` (W8A8: INT8 weights and per-row INT8 activations inside each matrix operation, INT32 accumulation).
- **Independent test of the INT8 matrix path:** an 8 x 16 by 16 x 8 product compared with a separate numpy W8A8 emulation: **maximum difference 0.0 (exact)**; the fp32 path differs by 1e-6.

## Results

| model | mode | relative error vs PyTorch fp32 | top-1 agreement with PyTorch fp32 |
|---|---|---|---|
| CNN, 1,000 images | fp32 | 7.8e-7 | 100% |
| CNN | INT8 weights (w8) | 4.0e-3 | **99.9%** |
| CNN | W8A8 (int8) | 6.0e-3 | 99.8% |
| transformer, 1,024 positions | fp32 | 6.8e-7 | 100% |
| transformer | INT8 weights (w8) | 5.1e-3 | **99.41%** |
| transformer | W8A8 (int8) | 1.48e-2 | **98.73%** |

**Counters.** Multiply-adds executed by the simulator equal the analytic model of the layer dimensions for every layer (CNN 662,912 per image; transformer 104,890,368 per 64-token sequence, with causal attention counted as the lower triangle only), and so do the SRAM bytes read and written per layer in the INT8 configuration (activations 2 bytes, weights 1 byte), all within 5% (exactly equal). Mesh traffic per sequence: 458,752 byte-hops (transformer, 2 x 2 mesh), 8,608 per image (CNN). The analytic byte counts were derived from the model dimensions with the counting rules stated in the check script, written separately from the program; they agree by construction of the same rules, so this checks that the simulator implements the stated rules, not that the rules match hardware.

## Bars

- **(a) PASS:** fp32 relative error 7e-7 on both models (bar 1e-2).
- **(b) PASS as worded (INT8 weights):** 99.9% on the CNN and **99.41%** on the transformer. **Not met in the stricter W8A8 configuration on the transformer: 98.73%** (13 of 1,024 positions differ from the fp32 choice). All 13 disagreements are near-ties: the fp32 gap between the top two characters at those positions is at most 0.036 (median 0.014), while the median gap over all positions is 0.96. The CNN meets 99% in both configurations. The bar as I wrote it said "INT8 weights"; the ISA's INT8 configuration is W8A8, which is stricter, so both results are reported and the W8A8 miss is not hidden.
- **(c) PASS:** all layers of both models match.

## What this shows and what it does not

- **Shows:** a programming model and instruction set small enough to express a convolutional network and a transformer decoder; a weights-stationary mapping of both onto a mesh of tiles with per-tile SRAM capacity checked; INT8 inference with the accuracy of the model preserved (CNN: 86.8% accuracy against 86.9% in fp32; transformer: 99.4% agreement in weight-only INT8); counters (multiply-adds, SRAM bytes, mesh byte-hops) that the M2 energy model can use.
- **Does not show:** any hardware result; timing (the simulator is functional: there are no cycles); the energy model (M2); a compiler (the mapper is a Python script written for these two models); large models (the test models are tiny and trained briefly); non-causal or grouped attention, key-value caching across steps, other precisions, training.

## Status of milestone M1

**Passed on bars (a), (b) as worded and (c); with one honest miss: transformer W8A8 top-1 agreement 98.73% (near-ties only).** Next: M2, the cycle and energy model validated against the simulator for batch-1 and batch-64 decode of a 1B-parameter model (the charter's bars); it needs the simulator extended with a time model (key-value cache growth, one token per step) and the energy constants of the existing models.

Related: [ISA note](ISA_M1.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Hardware index](../HARDWARE_INDEX.md), [Workload map](../../docs/gpu_workload_map.md), [Journal](../../docs/journal.md)
