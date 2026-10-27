---
title: Choosing detectors by what separates the classes, and where the gap to the CNN is
tags: [spark, results, front-end, cnn-gap]
---

# Choosing detectors by what separates the classes, and where the gap to the CNN is (27 Oct 2026)

SIMULATED, Fashion-MNIST, one seed (spread about 0.3). Founder's direction: close the accuracy gap to the CNN and improve Shirt recall by making L learn what is common and uncommon across classes, so that it confuses less. Scripts in `hw/brain/experiments/month5/`: `detector_selection.py` (logs `detector_selection_stage1.log`, `detector_selection.log`), `cnn_recall.py` (`cnn_recall.log`), `per_class_gap.py` (`per_class_gap.log`).

## Test 1: choose L's detectors by class information (counting only, no multiply)

Each of L's four channels gets an overcomplete pool of 128 Hebbian detectors (same recipe as shipped); the detectors with the highest mutual information between their pooled bits and the class label (summed over the 36 window positions, computed from counts at learning time) are kept. The chip then runs the same number of detectors as today.

| detectors per channel | accuracy | cluster | Shirt recall | Shirt AP | bits | active bits | est. energy |
|---|---|---|---|---|---|---|---|
| shipped: unsupervised 32 (reference) | 88.85 | 80.6 | 0.638 | 0.753 | 4,608 | 589 | 29.9 nJ |
| **most informative 32 of 128** | **89.03** | 81.0 | 0.654 | 0.745 | 4,608 | 430 | **26.5 nJ** |
| 32 random of 128 (control) | 87.87 | 79.2 | 0.617 | 0.706 | 4,608 | 189 | |
| 32 least informative (sanity) | 81.70 | 71.2 | 0.494 | 0.537 | 4,608 | 62 | |
| most informative 16 | 87.61 | 79.6 | 0.595 | 0.704 | 2,304 | 271 | |
| **most informative 64 (2x front end)** | **89.76** | 82.4 | **0.691** | 0.772 | 9,216 | 642 | 50.6 nJ |
| whole pool 128 (4x front end, upper bound) | 89.82 | 82.3 | 0.637 | 0.778 | 18,432 | 829 | |
| 32 global + 16 chosen within the confusable group | 89.42 | 81.6 | 0.649 | 0.760 | 6,912 | 534 | |
| 48 global (control for the same count) | 89.59 | 82.2 | 0.645 | 0.766 | 6,912 | 549 | |
| 32 global + 32 chosen within the group | 89.62 | 82.3 | 0.659 | 0.768 | 9,216 | 630 | |
| 32 chosen within the group only | 89.15 | 81.7 | 0.652 | 0.753 | 4,608 | 391 | |

- **Information-based selection works, and it is cheaper:** the signal is real (random 87.87, least informative 81.70, most informative 89.03). At the same 32 detectors per channel it gives 89.03 against 88.85 with 27% fewer active bits (est. 26.5 nJ against 29.9 nJ), so it moves up the accuracy and cost frontier at the same time. With 64 per channel it reaches 89.76 and Shirt recall 0.691 at an estimated 50.6 nJ (1.7 times), better than seven channels (89.48 at 50.9 nJ).
- **Choosing detectors for the confusable group specifically does not beat choosing globally** at the same detector count (89.42 against 89.59 at 48; 89.62 against 89.76 at 64). The group-only top 32 (89.15) is on par with the global top 32 within noise.
- Caveat: the selection was scored on the training labels only and evaluated on the test set once per configuration; one seed.

## Test 2: where is the gap to the CNN?

The small float CNN (32 shared 3 by 3 filters, backprop, 20 epochs, 91.28%) per class, against L shipped and the richer L (7 channels, two-level output, 89.95):

| class | CNN | L shipped | L rich | CNN minus L rich |
|---|---|---|---|---|
| T-shirt | 0.891 | 0.878 | 0.865 | +0.026 |
| Trouser | 0.978 | 0.974 | 0.977 | +0.001 |
| Pullover | 0.856 | 0.827 | 0.840 | +0.016 |
| Dress | 0.936 | 0.887 | 0.916 | +0.020 |
| Coat | 0.870 | 0.818 | 0.860 | +0.010 |
| Sandal | 0.984 | 0.967 | 0.968 | +0.016 |
| **Shirt** | **0.707** | 0.638 | 0.669 | **+0.038** |
| Sneaker | 0.958 | 0.969 | 0.971 | -0.013 |
| Bag | 0.975 | 0.978 | 0.976 | -0.001 |
| Boot | 0.973 | 0.949 | 0.953 | +0.020 |

- **The CNN's own Shirt recall is only 0.707.** Our best (0.691 with 64 informative detectors per channel, 0.677 with clauses on the two-level code) is already within 0.02 to 0.03 of it; the Shirt target is therefore about 0.70 to 0.71, not 0.9. The CNN loses Shirt images to T-shirt (141), Coat (65), Pullover (41) and Dress (36) too.
- **The remaining accuracy gap (89.95 against 91.28, 1.3 points) is spread, not concentrated on Shirt:** the four upper-body classes carry 68% of it (Shirt 0.38 points of accuracy, T-shirt 0.26, Pullover 0.16, Coat 0.10), Dress and Boot 0.20 each, Sandal 0.16. We already match or exceed the CNN on Trouser, Sneaker and Bag. Largest confusions of the richer L: Shirt to T-shirt (116), Shirt to Coat (99), T-shirt to Shirt (81), Shirt to Pullover (80).
- Reading: closing the gap to the CNN fully needs gains across several classes and costs more than the 2x ceiling allows today; the part that is realistically reachable inside the ceiling is Shirt recall toward 0.70 and about +0.5 to +0.8 accuracy.

Related: [Cost frontier](cost_frontier.md), [Multi-threshold front end](multi_threshold_front_end.md), [Foundations study](foundations_study.md), [Results index](INDEX.md)
