---
title: Redesign test 5 - a hidden layer on L's code (sparse first layer): can L reach a tuned network? Pre-set bars (31 Oct 2026)
tags: [spark, new-start, redesign, accuracy, hidden-layer, sparse, test-plan, bars]
---

# Redesign test 5: a nonlinear head on the code (31 Oct 2026)

**Written before any run.** [Test 4](step19_k4_result.md) showed that no linear readout lifts L's code above about 88.9% on clothing. An earlier measurement found a nonlinear network on the same 4,608-bit code at **90.92%** ([gap diagnosis](../hw/results/gap_diagnosis.md)); it was set aside under the 28 Oct no-multiplier rule, which the founder withdrew on 31 Oct 2026. Script: [`k5_hidden_layer.py`](experiments/k5/k5_hidden_layer.py). CPU, cloud container.

## Design

The fixed encoder produces the 4,608-bit code (about 580 bits on). **Head:** hidden layer of 256 units, ReLU, then 10 outputs (4,608-256-10). **The first layer needs no multiplier at inference: it is the sum of the table rows of the 580 active bits (sparse, event-driven, as in the chip's own table lookups); only the 256 x 10 output layer multiplies.** Trained by backpropagation on a host (the rule: training off the chip), Adam, dropout 0.2, 25 epochs with the epoch chosen on a held-out tenth of the labels, then refitted on all labels for that many epochs. Ablations declared in advance: hidden 1,024; two hidden layers 512 and 256.

## Pre-set bars (judged on the main 4,608-256-10 head, 2 seeds)

| id | bar |
|---|---|
| **K5-a** clothing | test accuracy at least 90.5% (between the shipped 88.85% and the earlier 90.92%, and level with a tuned small network at 89.9% to 90.7%) |
| **K5-b** digits | test accuracy at least 98.9% |
| **K5-c** chip realism | int8 weights in both layers (per-tensor symmetric) lose at most 0.3 points on each task |
| **K5-d** inference | counted inference energy per image (encoder, 580 x 256 8-bit adds, 256 x 10 8-bit multiply-adds; raw constants, then multiplied by 28 as the conservative layout factor) at most the small network's 1.0 uJ |
| **K5-e** training | reported, with a limit: counted training energy (dense backpropagation, L-side not multiplied) at most 5 times the tuned network's (2.5 J) |

A miss is reported as a miss; no bar changes after the run.

## What this test also decides

If K5-a to K5-d pass, the design becomes two tiers: the counting recipe for cheap learning on the device (88.85%, 20x to 350x less training compute than a network), and an offline-trained hidden-layer head for the best accuracy (about 90.9% on clothing) with inference still far below a convolutional network. Training energy of the head is expected to be higher than the counting recipe's and is reported honestly in K5-e.

## Limits stated in advance

Weights int8 but activations float in the test (a fully integer pipeline is not tested); counted, not measured, energy; two small image tasks; a strong network (91.75%) is not the target of this test; hidden size and dropout fixed in advance.

Related: [Step 19 test 4 result](step19_k4_result.md), [Gap diagnosis](../hw/results/gap_diagnosis.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
