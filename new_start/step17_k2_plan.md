---
title: Row K test 2 - stronger baselines, more seeds, a second task and conservative energy accounting - pre-set bars (31 Oct 2026)
tags: [spark, new-start, training, data-efficiency, test-plan, bars, row-k]
---

# Row K, test 2: closing the limits of test 1 (31 Oct 2026)

**Written before any run.** [Test 1](step16_k1_result.md) passed its bars but with a basic baseline, two seeds, one task and optimistic energy counting. Script: [`k2_strong_baselines.py`](experiments/k2/k2_strong_baselines.py). CPU, cloud container.

## What changes

- **Baselines (labelled, not components of L):** (1) the small convolutional network, now tuned: learning rate chosen from {0.001, 0.003} on a held-out 10% of the labels, weight decay 0.0001, data augmentation (random shifts of up to 2 pixels, plus horizontal flips for clothing), at least 600 gradient steps; (2) k nearest neighbours on pixels (k chosen from {1, 3, 5} on the held-out part); (3) softmax regression on pixels; (4) 4,096 random ReLU features with ridge regression. The best of the four on each (task, N) is the reference.
- **Seeds:** 5 different random subsets (and recipe seeds) for N up to 3,000, 3 for 10,000, 1 for 60,000; means and standard deviations reported; a difference counts as real only if it exceeds twice the standard error of the mean.
- **Tasks:** Fashion-MNIST and MNIST. For MNIST the 128-detector encoder is fitted without labels on 12,000 digit images of the first two classes, the same protocol as the shipped clothing encoder.
- **Energy, conservative:** L's counted energy is multiplied by 28 (the upper end of the 20x to 28x ratio between the earlier SKY130 layout estimate and the operation count of the Cortex chip) and the network's counted energy is **not** increased for memory traffic, which favours the network. Constants as in test 1 (16-bit multiply-add 1.5 pJ, 8-bit add 0.03 pJ, XNOR and bit count 0.003 pJ). Measured wall time on the same CPU is reported next to it.

## Pre-set bars (all must pass for "less training for comparable accuracy" to stand)

| id | bar |
|---|---|
| **K2-a** strong baselines | Fashion-MNIST, N = 1,000 and 3,000: L's mean accuracy is at least the best baseline's mean minus 1 point |
| **K2-b** energy, conservative | Fashion-MNIST, at the largest N where L and the tuned network both average at least 85%: the tuned network's counted training energy is at least 20 times L's counted energy multiplied by 28 |
| **K2-c** full data | Fashion-MNIST, N = 60,000: L within 3 points of the best baseline |
| **K2-d** second task | MNIST: K2-a at N = 1,000 and K2-c at N = 60,000 (same margins) |

A miss is reported as a miss; the bars are not changed after the run.

## Limits that remain (cannot be fixed in this session)

Energy is counted, not measured (needs a power meter on a real machine); the recipe is the numpy integer model, not the chip (the chip's own training is bit-exact in RTL simulation, see the [on-chip training result](../hw/results/l_deep_build.md)); two small image tasks, not language or large models; the baselines are small tuned models, not the best possible networks (no ensembles, no pre-training).

Related: [Step 16 test 1 result](step16_k1_result.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
