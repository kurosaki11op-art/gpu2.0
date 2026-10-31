---
title: Row K test 1 result - the counting recipe reaches comparable accuracy with thousands of times less training compute on Fashion-MNIST (31 Oct 2026, MEASURED accuracy, COUNTED compute)
tags: [spark, new-start, training, data-efficiency, result, row-k]
---

# Row K, test 1: result (31 Oct 2026)

**Accuracy MEASURED on the cloud container's CPU; training compute COUNTED from operations and weighted by assumed energies (not measured joules).** Plan and pre-set bars: [step 16 plan](step16_k1_plan.md). Script [`k1_data_efficiency.py`](experiments/k1/k1_data_efficiency.py), [log](experiments/k1/results/k1_run.log), [json](experiments/k1/results/k1_results.json). L = the shipped counting recipe on the fixed 4,608-bit code (one pass, no gradients); the network = a small two-layer convolutional network trained with Adam (a labelled baseline, not a component of L). Test set: the 10,000 Fashion-MNIST test images.

| labelled examples | L accuracy | network accuracy (seeds) | network epochs | L training energy | network training energy | ratio |
|---|---|---|---|---|---|---|
| 100 | 63.95% | 50.0% (39.0, 61.1) | 94.5 | 133 uJ | 26.3 mJ | 197x |
| 300 | 69.15% | 69.8% (68.3, 71.3) | 54.0 | 135 uJ | 45.1 mJ | 335x |
| 1,000 | 78.65% | 72.9% (66.8, 78.9) | 27.5 | 139 uJ | 76.6 mJ | 552x |
| 3,000 | 83.38% | 80.3% (79.0, 81.7) | 14.0 | 151 uJ | 117 mJ | 776x |
| 10,000 | 86.08% | 85.0% (one seed) | 13.0 | 193 uJ | 362 mJ | 1,880x |
| 60,000 | 88.85% | 89.4% (one seed) | 15.0 | 492 uJ | 2,506 mJ | 5,096x |

## Bars (pre-set)

- **K1-a (L at least the network's minus 1 point at 1,000 and 3,000 labels): PASS** (78.7% against 72.9%, and 83.4% against 80.3%).
- **K1-b (training energy at most one twentieth, at the largest N where both reach 85%, here 60,000): PASS** (about 5,100x).
- **K1-c (within 3 points at 60,000): PASS** (0.5 points behind).

## How to read it, with the limits

- **The result supports the claim on this task:** the counting recipe reaches comparable accuracy (within about 0.5 point at full data, ahead at 1,000 to 10,000 labels) with about 200 to 5,000 times less counted training energy. A second effect, not part of the bars: the recipe is fast on a CPU (8 seconds at 60,000 against 84 for the network).
- **The network baseline is basic.** One architecture, Adam at a fixed rate, early stopping, no augmentation, no regularisation tuning, seeds vary a lot at small N (at 1,000 labels the two seeds are 66.8% and 78.9%), so the lead at 1,000 to 3,000 labels is within the seed spread. A stronger baseline (augmentation, weight decay, a tuned rate, an ensemble, or simple methods such as nearest neighbours or a linear model on random features) was not tested and could narrow or erase the accuracy lead; the earlier measured small network reached 89.9% to 90.7% with a better recipe, against L's 88.85%.
- **Compute is counted, not measured:** the ratio rests on assumed energies (16-bit multiply-add 1.5 pJ, 8-bit add 0.03 pJ, one XNOR and bit count 0.003 pJ) and on an operation count for L that I estimated from the model's loops (about 26 adds per active code bit). The L figure at small N is dominated by the **fixed cost of fitting the detector encoder (133 uJ, 12,000 unlabelled images)**, which is included. The network on a GPU would be faster in wall time than its operation count suggests; the energy per operation there is the project's value, not measured.
- **What was not tested:** any task bigger than a small image set, language, new classes after training (tested separately, see the [new-class learning note](../hw/results/target1_new_class_learning.md)), the hardware (the training here is the integer model in numpy, not the chip), and robustness.

## Status of row K

**Supported on one small task, with a basic baseline.** The next test to make it convincing is test 2: stronger baselines (augmentation, tuned training, nearest-neighbour and linear baselines) and a second task. Bars to be written before it.

**Correction after Vision review 01 (31 Oct 2026), V-13, V-21):** the 5,096x ratio is the end-of-training energy of a network that exceeds L's accuracy after 15 epochs; at equal accuracy the ratio is about 100x (see the step 17 correction). The detector encoder is labelled 'fitted without labels' but the 12,000 images are chosen by class (the first two classes of the training set): class selection uses labels, and its cost is not counted at N = 100 (V-21). No test-set leakage was found in these scripts (V-21).

Related: [Step 16 plan](step16_k1_plan.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
