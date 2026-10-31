---
title: Row K test 1 - how much training (labels and compute) to reach a given accuracy, counting rule against gradient descent - pre-set bars (31 Oct 2026)
tags: [spark, new-start, training, data-efficiency, test-plan, bars, row-k]
---

# Row K, test 1: training cost to reach an accuracy (31 Oct 2026)

**Written before any run.** Row K of the [workload map](../docs/gpu_workload_map.md): a system that needs less training. This first test is on the one task where we have both systems: Fashion-MNIST. Script: [`k1_data_efficiency.py`](experiments/k1/k1_data_efficiency.py). Runs on CPU in the cloud container.

## What is compared

- **L:** the shipped L Cortex recipe (`train_table` in the month-5 setup: the integer slow-table model, one pass, a dream after every example, no gradients). The code is produced by a **fixed encoder of 128 detectors fitted without labels on 12,000 images** (the first 12,000 images of two classes, as in the shipped build); that fitting is a fixed pre-training cost, reported separately and counted in the totals.
- **Reference network (a labelled baseline, not a component of L):** a small convolutional network (two convolution layers, about 0.66 million multiply-adds per example forward), Adam, early stopping on 10% of the labelled subset held out, up to 15 epochs. Two seeds for 3,000 labels or fewer.
- **Labelled examples N:** 100, 300, 1,000, 3,000, 10,000, 60,000 (random subsets with the same seed for both). Test set: the 10,000 test images.
- **Training compute** counted by operations, then weighted by assumed energies: 16-bit multiply-add 1.5 pJ (project value), 8-bit add 0.03 pJ (assumed), one XNOR and bit count 0.003 pJ (assumed). L: about 26 adds per active code bit per example (count, score, update, dream, score; estimated from the model's loops), plus the encoder (576 positions x 128 templates x 25 bits per image) and, once, the fitting of the encoder. CNN: 3 x forward multiply-adds per example per epoch run, plus the validation passes.

## Pre-set bars

| id | bar |
|---|---|
| **K1-a** data efficiency | at 1,000 and at 3,000 labels, L's test accuracy is at least the network's minus 1 point (it matches or beats it) |
| **K1-b** compute | at the largest N at which both reach at least 85% test accuracy, L's total training energy (including the encoder, per-example and fitting) is at most one twentieth of the network's |
| **K1-c** ceiling | at 60,000 labels L is within 3 points of the network |

**Protocol note (added after a dry run on N = 100 and 300, whose numbers are not results):** the first network protocol gave only 30 gradient steps at N = 100 and failed to learn; every network run now gets at least 600 gradient steps and early-stopping patience of at least 150 steps, so the network is not handicapped at small N. The bars are unchanged.

**All three must pass for the claim "less training for comparable accuracy" to stand on this task.** A miss is reported as a miss; the bars are not changed after the run.

## Limits stated in advance

One small task (clothing images), one reference network and recipe (not tuned beyond the stated one), operation counts and assumed energies, not measured joules; the L recipe was tuned earlier on the full training set (the network's settings are not tuned per N); the fixed encoder was fitted on 12,000 unlabelled images in all cases; accuracy of L on this task is known to sit about 1 to 3 points below a small convolutional network (about 88.9% against 89.9% to 90.7% measured earlier), so K1-c and K1-a at large N are the risky bars. Nothing here says anything about large models.

Related: [Workload map](../docs/gpu_workload_map.md), [Step 14 price-cut test](step14_price_cut_result.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
