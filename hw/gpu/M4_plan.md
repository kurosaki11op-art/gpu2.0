---
title: Our GPU, milestone M4 - compiler front end and a real pretrained model: plan and pre-set bars (31 Oct 2026)
tags: [spark, gpu, m4, compiler, plan, bars]
---

# M4: compiler front end and a real model (31 Oct 2026)

**Written before the work.** Charter milestone M4 (*import a model and map it automatically; same tolerance as M1*), in the order of the [finish plan](../../docs/product_finish_plan.md). Version 1 of the front end covers what the instruction set already expresses: **decoder-only transformers of the GPT-2 family** (learned positions, layer normalisation, fused query-key-value projection, tanh GELU, tied output embedding) and **sequential convolutional networks** (convolution, ReLU, max pooling, linear). It reads the model's configuration and weights from a Hugging Face or PyTorch module, places each weight on a tile (first fit, 4 MB tiles, layer by layer) and emits the instruction list; **no hand-written mapping per model**. It is not a general graph compiler: models outside these families are out of scope and stated as such.

## Test models

- The two M1 models (small transformer, small CNN), exported through the new importer instead of the old scripts.
- **A real pretrained model: GPT-2 small (124 million parameters, 12 layers, d = 768, 12 heads)** from the Hugging Face hub, run through the simulator in fp32 and W8A8, on held-out WikiText-2 text (at least 64 windows of 128 tokens, a paired confidence interval and a tail measure of the per-position loss change; V-23).

## Pre-set bars

| id | bar |
|---|---|
| **M4-a** automatic mapping | the importer produces the program and tile placement for all three models from the model objects alone; per-model code in the importer is limited to the family description (no hard-coded sizes) |
| **M4-b** fp32 | simulator logits match PyTorch fp32 within a relative error of 1e-3 on GPT-2 small and 1e-4 on the M1 models |
| **M4-c** INT8 quality | W8A8 next-token loss on GPT-2 small exceeds the fp32 loss by at most 0.01 nats per token (the loss-increase bar adopted after the M1 fix) |
| **M4-d** counts | the simulator's multiply-adds and SRAM bytes per layer group equal the M2 analytic model's within 5% for GPT-2 small |
| **M4-f** 4-bit quality (added after Vision review 01, V-11) | the same loss-increase test with **4-bit weights** (per output channel) and 8-bit activations: at most 0.01 nats per token on the pretrained model and on the M1 model, with a paired confidence interval; **if it misses, every 4-bit energy, cost and capacity figure in the notes is marked unsupported** and 8-bit figures are published beside every 4-bit claim |
| **M4-g** strict widths (added after V-12) | a strict mode in which every stored value passes through its stated width (embeddings and weights at their integer widths, key-value cache and activations at 16 bits, attention scores as stated); M4-c and M4-f are run in both modes and both results reported |
| **M4-e** report | a one-page report per model: tiles used, SRAM bytes, multiply-adds, modelled energy per token and latency range (M2 model, labelled), and the measured loss in each mode |

A miss is reported as a miss; bars are not changed after the run.

## Limits stated in advance

Functional simulation only (no hardware); grouped-query or rotary-position models (the Llama family) are not covered in version 1; the held-out sample is small (2,048 tokens per mode); the energy and latency figures are the M2 model's assumed constants.

Related: [Finish plan](../../docs/product_finish_plan.md), [Own GPU charter](../../docs/own_gpu_charter.md), [M2 result](M2_result.md), [M1 fix result](M1_fix_result.md), [Hardware index](../HARDWARE_INDEX.md)
