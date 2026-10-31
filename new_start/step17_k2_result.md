---
title: Row K test 2 result - less training compute holds against stronger baselines, less data does not (bar K2-d fails on MNIST) (31 Oct 2026, MEASURED accuracy, COUNTED compute)
tags: [spark, new-start, training, data-efficiency, result, row-k, failure]
---

# Row K, test 2: result (31 Oct 2026)

**Accuracy MEASURED on the cloud container's CPU; training energy COUNTED (operation counts times assumed per-operation energies), L's figure multiplied by 28 and the network's not increased.** Plan and pre-set bars: [step 17 plan](step17_k2_plan.md). Script [`k2_strong_baselines.py`](experiments/k2/k2_strong_baselines.py), [log](experiments/k2/results/k2_run.log), [json](experiments/k2/results/k2_results.json). Baselines: a tuned small network (learning rate chosen on held-out labels, weight decay, shift and flip augmentation, both learning-rate runs counted in its energy), k nearest neighbours, softmax regression, 4,096 random features with ridge. Means over 5 seeds (N up to 3,000), 3 seeds (10,000) or 1 seed (60,000); plus-minus is the standard deviation of L across seeds.

## Fashion-MNIST (test accuracy, %)

| labels | L | tuned network | k-NN | linear | random features | best baseline | L minus best | energy ratio, network / (L x28) |
|---|---|---|---|---|---|---|---|---|
| 100 | 60.7 +- 4.9 | 61.8 +- 5.2 | 63.4 | 69.0 | 67.8 | linear | -8.3 | 17x |
| 300 | 68.9 +- 1.9 | 72.4 +- 1.6 | 69.7 | 75.0 | 73.9 | linear | -6.1 | 31x |
| **1,000** | 78.3 +- 0.5 | 74.9 +- 2.5 | 74.9 | 79.3 | 78.9 | linear | **-0.9** | 41x |
| **3,000** | 83.1 +- 0.3 | 80.0 +- 0.9 | 78.6 | 81.6 | 81.5 | linear | **+1.5** | 59x |
| 10,000 | 86.7 +- 0.4 | 85.4 +- 0.4 | 81.6 | 83.4 | 85.1 | network | +1.3 | 143x |
| **60,000** | 88.85 | 88.2 | 85.5 | 84.5 | 85.8 | network | **+0.6** | **352x** |

## MNIST (test accuracy, %)

| labels | L | tuned network | k-NN | linear | random features | L minus best | energy ratio |
|---|---|---|---|---|---|---|---|
| 100 | 66.0 +- 7.4 | 79.5 +- 4.3 | 70.2 | 73.1 | 68.4 | -13.5 | 19x |
| 300 | 82.5 +- 2.5 | 91.2 +- 1.8 | 81.2 | 83.1 | 80.0 | -8.7 | 28x |
| **1,000** | 92.6 +- 0.5 | 94.5 +- 0.3 | 88.6 | 87.5 | 87.1 | **-1.9** | 44x |
| 3,000 | 95.7 +- 0.3 | 96.9 +- 0.1 | 92.5 | 89.6 | 92.3 | -1.2 | 56x |
| 10,000 | 97.4 +- 0.1 | 98.1 +- 0.2 | 94.9 | 91.5 | 94.6 | -0.7 | 138x |
| **60,000** | 98.6 | 98.95 | 96.9 | 92.7 | 94.7 | **-0.35** | 316x |

## Bars (pre-set)

- **K2-a (Fashion-MNIST at 1,000 and 3,000 labels, L at least the best baseline minus 1 point): PASS, narrowly** (-0.93 and +1.51). The 1,000-label value is 0.07 points inside the margin and within the seed spread.
- **K2-b (conservative energy: network at least 20x L's counted energy x28, at the largest size where both reach 85%): PASS** (352x at 60,000).
- **K2-c (60,000 labels within 3 points of the best baseline): PASS** (+0.6).
- **K2-d (MNIST: the K2-a margin at 1,000 labels and the K2-c margin at 60,000): FAIL.** At 1,000 labels L is 1.9 points behind the tuned network (bar 1); at 60,000 it is 0.35 behind (passes).

## What this says

- **Less training compute: supported.** Even with L's energy multiplied by 28 and no memory overhead on the network, the counted training energy ratio is 17x to 352x on clothing and 19x to 316x on digits, rising with the number of labels. At 100 labels the ratio is under 20x because the fixed cost of fitting the encoder (12,000 unlabelled images) dominates L's total. Wall time on the same CPU is 8 to 50 times shorter at 60,000 labels (7 seconds against 371 for clothing, against 230 for digits).
- **Less data: not supported.** With strong baselines, L is **8 to 14 points behind at 100 labels and 6 to 9 at 300** (a linear model on clothing, the tuned network on digits). On clothing L overtakes the baselines only from about 3,000 labels; on digits the tuned network stays ahead at every size (by 0.35 to 13.5 points). The 1,000-label lead seen in test 1 was an effect of its weak baseline.
- **Accuracy at full data is comparable:** within 0.35 points of the tuned network on digits, 0.6 points ahead on clothing. **Caution on the 60,000 clothing figure:** the tuned network here (88.2%, one seed, at most 15 epochs with augmentation) scored below the plain network of test 1 (89.4%), so it is under-trained at this size; against the test 1 network L would be 0.5 points behind, still inside the 3-point bar.

## Limits that remain

Energy counted, not measured (waiting for the power meter and a real machine); the recipe is the numpy integer model, not the chip; two small image tasks, no language or large models; baselines are small models (no ensembles, no pre-training, no long tuning), and the tuned network is weaker than it could be at 60,000 labels; one seed at 60,000.

## Status of row K

**Narrowed and partly supported:** the claim that survives is **"much less training compute (about 20x to 350x counted, conservative) for accuracy within about 1 point of a tuned small network once there are a few thousand labels"**. The claim "less data" fails at small N. Open: measured energy; a task where labels are scarce and a method that fixes the small-N weakness (the earlier work on few-label learning, [F2](../docs/PROJECT_MEMORY.md), is the starting point); bigger tasks.

Related: [Step 17 plan](step17_k2_plan.md), [Step 16 test 1 result](step16_k1_result.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
