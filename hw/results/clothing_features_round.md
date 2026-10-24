---
title: Clothing accuracy round - features and readout (24 Oct 2026)
tags: [l, clothing, limits, results]
---

# What limits L on clothing, and what moves it? (SIMULATED, Fashion-MNIST full 60,000 images, one seed, single view)

Scripts in `hw/brain/experiments/month5/`: `l_passes.py`, `l_hog_bits.py`, `l_readout_ceiling.py`, `l_conjunction_ceiling.py`, `l_conjunction_counting.py` (logs beside them: `l_passes.log`, `l_hog_bits.log`, `l_readout_ceiling.log`, `l_conjunction_ceiling.log`, `l_conjunction_counting2.log`). Baseline: L slow-table integer model on the 4,608-bit learned-detector code: **88.85%, Shirt recall 63.8%**. Small CNN ruler (backprop, all data): 91.1%, Shirt 79.4%.

| Test | Accuracy | Shirt recall | Bits | Verdict |
|---|---|---|---|---|
| Read the images 1 to 4 times | 88.85 to 89.05 | 59 to 65 | 4,608 | one-pass rule is not the limit |
| HOG-style edge bits only, 2x2 cells (compares, counts, no learned detectors) | 88.76 | 61.7 | 4,704 | as good as the learned detectors with a simpler, label-free encoder |
| HOG bits + detector code | 89.76 | 66.2 | 9,312 | +0.9 |
| **Float linear readout** on detector code / HOG bits / both | 88.06 / 88.77 / 89.97 | 74.1 / 64.6 / 70.0 | | the counting readout is NOT the bottleneck: a float readout on the same bits gives the same accuracy |
| Float linear + 10k / 30k random pairwise ANDs | 90.39 / 91.30 | 68.6 / 73.0 | 19k / 39k | nonlinear (conjunction) features lift the ceiling about 1.3 points; random 3-way ANDs (30k): 90.50, worse |
| **Counting readout + conjunctions chosen by counting** (best of candidate ANDs by in-class minus out-of-class frequency, no gradients) 10k of 100k | 90.53 | 70.0 | 19,312 | +0.8 over 89.76 |
| 20k of 200k | 90.04 | 66.3 | 29,312 | within noise |
| 40k of 400k | 90.67 | 70.2 | 49,312 | +0.9; table 10 x 49,312 bytes = 482 KB at 8 bits (about 120 KB at 2 bits) |

**Reading.**
1. The limit is not memory, not passes, not the counting rule: a single layer of binary features with a linear readout (counting or float) tops out near 90%.
2. Nonlinear features (conjunctions, the same idea as Tsetlin clauses) give about +1 to +1.5 points, and L's counting rule can use them without gradients (+0.8 to +0.9, Shirt 66 to 70%). It costs 2 to 5 times the table (120 to 480 KB), so this reaches roughly the CNN ruler's overall accuracy (90.7 against 91.1) only by giving up the memory advantage over the 115 KB MLP.
3. **Shirt stays at 66 to 74% in every variant** against 79.4% for the CNN and with a likely ceiling set by the overlapping definitions of the T-shirt/top and Shirt classes (research report).
4. Single seeds, differences of 0.3 are inside noise (the 20k variant came out below the 10k one).

**What would be needed to match the CNN with lookups only:** a trained hidden layer of conjunctions or lookup tables, learned with gradients on a GPU and deployed as tables (the DWN / convolutional Tsetlin / logic-gate-network family, reported at 89 to 94% on Fashion-MNIST in the research report, second-hand). That is the accelerator path, not L Cortex. Not started.

## Gradient-trained lookup layer (accelerator path, first try)

`lut_net.py`, `lut_net.log`: one layer of weightless lookup tables on the same 9,312 input bits: L = 10 x N LUTs, each reading 6 fixed random input bits as a table index and returning one bit; class score = number of 1-bits in its group; table entries trained with Adam through a sigmoid relaxation (training on a GPU or CPU), deployed as 1-bit tables (inference: index, lookup, popcount; no multiply, no matrix).

| LUTs per class | Tables | Accuracy (hard tables) | Shirt recall |
|---|---|---|---|
| 200 | 15.6 KB | 85.96 | 59.6 |
| 1,000 | 78.1 KB | 88.86 | 61.8 |

**Result: no gain over L** (88.85% at 11 to 45 KB): a single trained lookup layer is as limited as a single binary layer with a readout. The 8-input variant was stopped. The literature figures for the stacked version (DWN about 89% on Fashion-MNIST, convolutional Tsetlin 90 to 94%) are second-hand and also do not clearly exceed the tiny-CNN 92.5%. A multi-layer or convolutional trained lookup network is the remaining open route and has not been built.

## FPTM-style rich code with L's counting readout (24 Oct, `fptm_code.py`, `fptm_code.log`; SIMULATED, one seed, 30,000 training images, test on all 10,000)

Code copied from the Fuzzy-Pattern Tsetlin Machine (raw pixels in 4 quantile levels + 8 fixed edge maps in 9 sign-split quantile bits = 59,584 bits per image), read by L's counting table:

| Code | Bits | Active bits per image | Accuracy | Shirt recall |
|---|---|---|---|---|
| raw 4-level thermometer only | 3,136 | 974 | 82.52 | 53.3 |
| edge maps only | 56,448 | 11,882 | 89.47 | 62.5 |
| raw + edge maps | 59,584 | 12,857 | 89.45 | 66.4 |

**Result:** the rich code alone gives only about +1 point over L's own 4,608-bit code and costs 22 times more active rows per image. The Tsetlin machine's 92 to 94.7% therefore comes largely from its **learner** (learned conjunction clauses trained by feedback for up to 1,000 epochs), not from the code alone; the paper itself does not isolate the two (UNVERIFIED split), this is our measurement with a counting readout. Also the 20-clause FPTM model is at most about 80 KB deployed but its code touches about 13,000 bits per image.

Related: [Results index](INDEX.md), [Where L loses on clothing](clothing_confusion.md), [Specialist for Shirt/T-shirt](shirt_specialist.md), [Real colour photos](shirt_real_photos.md), [Research report](../../docs/research/matrix_free_vs_cnn_report.md), [Journal](../../docs/journal.md)
