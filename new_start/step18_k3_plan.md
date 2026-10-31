---
title: Row K test 3 - the few-label weakness: methods that use unlabelled images, pre-set bars (31 Oct 2026)
tags: [spark, new-start, training, few-labels, semi-supervised, test-plan, bars, row-k]
---

# Row K, test 3: the few-label weakness (31 Oct 2026)

**Written before any run.** [Test 2](step17_k2_result.md) found L 6 to 14 points behind at 100 to 300 labels (a linear model on clothing, the tuned network on digits) and 1.9 points behind on digits at 1,000. Script: [`k3_few_labels.py`](experiments/k3/k3_few_labels.py). CPU, cloud container.

## Hypotheses (what to test)

The recipe learns each class from the few labelled codes alone. Two things can help without more labels: (1) a **better readout** on the same code when examples are few; (2) a **feature layer learned without labels** from the 60,000 unlabelled training images (clustering the 4,608-bit code into 300 prototypes), then a small readout trained on the few labels, which is the brain-like division (unsupervised categories from experience, labels only to name them).

## Methods (the main one is fixed in advance; the others are reported as ablations)

- **M0** the shipped recipe (as in test 2).
- **M1** nearest class mean of the code.
- **M2** ridge regression on the 4,608-bit code, the penalty chosen by exact leave-one-out on the labelled examples.
- **M3a** cluster then name: 300 clusters (3 passes of k-means on the unlabelled training codes), each cluster named by the majority of the labelled examples that fall in it, clusters without a label inherit that of the nearest named cluster.
- **M3b (MAIN)** ridge regression on the 300 cluster similarities, penalty by leave-one-out.

Each method uses the same 5 random labelled subsets as test 2 (and the same test set). The unlabelled images carry no labels at any stage.

## Pre-set bars (judged on M3b; all must pass)

| id | bar |
|---|---|
| **K3-a** clothing, 100 and 300 labels | mean accuracy at least the best test 2 baseline's (69.0% and 75.0%) |
| **K3-b** digits, 100 and 300 labels | mean accuracy within 3 points of the tuned network's in test 2 (79.5% and 91.2%) |
| **K3-c** 1,000 labels, both tasks | within 1 point of the best test 2 baseline (79.3% clothing, 94.5% digits) |
| **K3-d** compute | at 100 and 300 labels the counted total training energy (conservative, L-side x28, **including encoding the 60,000 unlabelled images and the clustering passes**) is at most the tuned network's counted energy |

A miss is reported as a miss; no bar changes after the run. Energy constants as in tests 1 and 2 (XNOR and bit count 0.003 pJ, 8-bit add 0.03 pJ, 16-bit multiply-add 1.5 pJ); clustering counted as 3 passes x 60,000 x 300 x 4,608 bit operations; the readout as a few multiply-adds, negligible.

## Limits stated in advance

Counted, not measured, energy; the clustering and ridge run on a host (not on the chip); two small image tasks; 300 clusters and 3 passes are fixed choices, not tuned per task; the code is the fixed encoder of the shipped chip.

Related: [Step 17 test 2 result](step17_k2_result.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
