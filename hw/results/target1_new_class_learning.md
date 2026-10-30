---
title: Target 1 first test - learning new classes on the device against a CNN (30 Oct 2026)
tags: [spark, new-start, target1, on-device-learning, negative-result]
---

# Target 1, first decisive test: new classes from a few examples (30 Oct 2026)

Question: does the chip's on-device learning (no backprop, no stored old data) beat a GPU-style network when new classes arrive with few examples? Fashion-MNIST; the chip (integer model of L Cortex, bit-exact with the RTL) and a small reference CNN (two conv layers) are trained on 8 classes, then two new classes arrive with k examples each (3 random draws averaged). Scripts [new_class_learning_test.py](../brain/experiments/target1/new_class_learning_test.py) and [new_class_dream_ablation.py](../brain/experiments/target1/new_class_dream_ablation.py), logs next to them. **SIMULATED accuracy, one seed of the base networks; update time ESTIMATED from the simulated cycle counts.**

## Result 1: against the CNN (the chip dreams the old classes; the CNN either forgets or replays 20 stored examples per old class)

Accuracy on all 10 classes at k = 1 / 5 / 20 / 100 examples per new class:

| new classes | chip | CNN fine-tuned on new data only | CNN with a replay buffer (160 stored images) |
|---|---|---|---|
| Bag, Ankle boot (easy) | 67.5 / 77.4 / 81.0 / 82.2% | 22.8 / 19.5 / 19.9 / 19.9% (old classes forgotten: 0 to 9%) | 71.7 / 80.9 / 86.3 / 85.9% |
| Coat, Shirt (hard, confusable) | 75.7 / 77.7 / 81.7 / 83.4% | 21.9 / 15.4 / 15.8 / 16.6% | 76.4 / 79.8 / 82.8 / 78.3% |

1. **Without any stored data, the CNN collapses** (catastrophic forgetting); the chip keeps 79 to 94% on the old classes with no raw example stored.
2. **A CNN with a small replay buffer is as good or better than the chip**: 4 to 5 points ahead on the easy classes for k of 5 or more, about equal on the hard ones, ahead on the new classes at k = 20 (91.4% against 81.6% on Bag, Boot). The chip's advantage is only that it needs no stored images; but its dream counters are themselves about 57 KB of statistics (against about 125 KB for 160 stored images), so this is not "no memory".
3. **Few-shot is weak**: at 5 examples the chip learns the new classes to 58% (easy) and 12% (hard); at 1 example, 8% and 1%.

## Result 2: how many night dreams does a new class need (ablation, 2 draws)

The test above used 6,000 dreams per old class per night (96,000 dreams per update). Reducing it 100-fold changes accuracy by about 1 to 2 points at most, and the best accuracy is usually at 300 per class:

| k | dreams per old class | all-class accuracy, Bag/Boot | Coat/Shirt | dreams per update |
|---|---|---|---|---|
| 20 | 6,000 / 1,500 / 300 / 60 | 80.7 / 81.3 / 83.7 / 82.7% | 82.2 / 81.1 / 82.0 / 81.7% | 96,000 / 24,000 / 4,800 / 960 |

At 13,569 cycles per learn-and-dream pair (the measured on-chip training cost, an upper bound for one dream), 960 dreams cost under 13 million cycles, about 0.26 s at 50 MHz, so an update takes well under a second (ESTIMATED); the 96,000-dream recipe would take about 26 s. So **the speed bar (a new class in under a second) is met, once the dream count is cut to about 60 per class.**

## Against the bars set in advance ([target options](../../docs/new_start_target_options.md))

- Update time under one second: **met** (ESTIMATED, with 60 to 300 dreams).
- "A new class learned from 5 examples": **not met in accuracy** (58% on easy, 12 to 23% on hard classes).
- Better than a GPU-style network at on-device learning: **not shown**; a CNN with a small replay buffer is at least as accurate. What remains is cost per update, not measured yet (the CNN fine-tune here took 100 full gradient steps, about 2 giga multiply-adds, against about 13 million chip cycles).

Conclusion: the on-device learning claim, as tested, is weaker than hoped. It stands only as "learns new classes with no stored images and a small update cost", and is not an accuracy win.

Related: [New start target options](../../docs/new_start_target_options.md), [Lessons from L version 1](../../docs/lessons_L_v1.md), [Gap diagnosis](gap_diagnosis.md), [Results index](INDEX.md)
