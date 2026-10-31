---
title: Row K test 3 result - using unlabelled images fixes most of the few-label weakness (one bar missed by 0.02 points) (31 Oct 2026, MEASURED accuracy, COUNTED energy)
tags: [spark, new-start, training, few-labels, semi-supervised, result, row-k]
---

# Row K, test 3: the few-label weakness (31 Oct 2026)

**Accuracy MEASURED on the cloud container's CPU; energy COUNTED (as in tests 1 and 2: L side x28, network unchanged).** Plan and pre-set bars: [step 18 plan](step18_k3_plan.md). Script [`k3_few_labels.py`](experiments/k3/k3_few_labels.py), [log](experiments/k3/results/k3_run.log), [json](experiments/k3/results/k3_results.json). Five random labelled subsets as in [test 2](step17_k2_result.md); the 60,000 training images are used without labels; the code is the fixed 4,608-bit code of the shipped chip. **M3b (main, fixed in advance) = ridge regression on the similarities to 300 prototypes learned without labels (3 passes of k-means).** M0 = the shipped recipe; M1 = nearest class mean; M2 = ridge on the code; M3a = cluster, then name each cluster from the labelled examples (ablations, not graded).

## Test accuracy (%, mean of 5 subsets)

| task, labels | M0 shipped | M1 class mean | M2 ridge on code | M3a cluster+name | **M3b prototypes+ridge** | best test 2 baseline | M3b minus best baseline |
|---|---|---|---|---|---|---|---|
| clothing 100 | 60.7 | 69.2 | **73.2** | 68.8 | 68.9 +- 1.2 | 69.0 (linear) | **-0.02** |
| clothing 300 | 68.9 | 75.0 | 79.7 | 73.3 | **79.9 +- 0.7** | 75.0 (linear) | +4.9 |
| clothing 1,000 | 78.3 | 75.8 | 81.9 | 76.1 | **84.3 +- 0.4** | 79.3 (linear) | +5.0 |
| digits 100 | 66.0 | 82.0 | 86.6 | **87.1** | 82.9 +- 1.5 | 79.5 (network) | +3.5 |
| digits 300 | 82.5 | 89.0 | 93.5 | 90.0 | **94.6 +- 0.2** | 91.2 (network) | +3.4 |
| digits 1,000 | 92.6 | 90.9 | 95.1 | 93.1 | **96.3 +- 0.1** | 94.5 (network) | +1.8 |

## Bars (pre-set, judged on M3b)

- **K3-a (clothing, 100 and 300 labels: at least the best test 2 baseline): FAIL by 0.02 points.** At 300 labels it is +4.9; at 100 labels it is 68.94% against 69.0% for the linear model, a tie within noise, but the bar is a bar.
- **K3-b (digits, 100 and 300 labels: within 3 points of the tuned network): PASS** (it is ahead of the network by 3.5 and 3.4 points).
- **K3-c (1,000 labels, both tasks: within 1 point of the best baseline): PASS** (+5.0 and +1.8).
- **K3-d (counted total training energy, including encoding the 60,000 unlabelled images and the clustering, at most the tuned network's): PASS** (34 mJ against 62 to 116 mJ for clothing at 100 and 300 labels, 70 to 106 mJ for digits; the network costs 1.8x to 5x more).

## What this says

- **The few-label weakness is mostly a weakness of the shipped recipe's readout, not of the code.** Replacing the counting-and-dreams readout by a ridge readout on the same code (M2) gains 5 to 12 points at 100 to 300 labels, and prototypes learned from unlabelled images (M3b) gain another 1 to 2.5 points from 300 labels on. At 300 and 1,000 labels M3b beats every baseline of test 2 by 2 to 5 points on both tasks.
- **Below 300 labels the picture is mixed:** the plain ridge on the code (M2: 73.2% clothing, 86.6% digits at 100 labels) and cluster-then-name (M3a: 87.1% digits) beat the declared main method M3b. That is a finding, not a bar result: M3b was fixed in advance as the graded method and misses K3-a by 0.02 points. A rule that picks between M2 and M3b by their leave-one-out error would likely meet the bars, but it was not tested and must get its own bar before it is claimed.
- **The compute advantage shrinks:** using the unlabelled images costs about 34 mJ counted (L side x28), only 1.8x to 5x below the tuned network (instead of 17x to 350x for the shipped recipe at the same label counts). M2 uses no unlabelled data and costs almost nothing beyond the encoder fit.

## Limits

Counted energy; the readout is trained on a host in floating point: **the chip's table is small integers (5-bit fast table, 8-bit slow table), and an earlier test found an offline float table loses accuracy when quantised** ("the readout gap", F4), so a quantised version must be tested before any chip claim; clustering and ridge are not on the chip; 300 clusters and 3 passes were fixed in advance; two small image tasks.

## Status of row K

**Narrowed and improved:** with a ridge readout and unlabelled images, the few-label weakness is largely closed from 300 labels (+3 to +5 points over every baseline), with one bar missed by 0.02 points at 100 labels on clothing. Open: a pre-set selection rule for the smallest label counts, a quantised-table test, measured energy.

Related: [Step 18 plan](step18_k3_plan.md), [Step 17 test 2 result](step17_k2_result.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
