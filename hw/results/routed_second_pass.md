---
title: Routed second pass with informative detectors (closing the gap to the CNN inside the cost ceiling)
tags: [spark, results, front-end, routing, cnn-gap]
---

# Routed second pass with informative detectors (27 Oct 2026)

> **Labels of the reference numbers (27 Oct 2026):** every figure marked "reference" or "CNN" is labelled by origin. CNN accuracy and per-class recall (91.28, Shirt 0.707) are SIMULATED: a small CNN trained here in numpy (32 shared 3 by 3 filters, 20 epochs, one seed), not a published or GPU-measured result. Reference energies (CNN float32 and int8, add-only ternary network, dense float network) are ESTIMATED with the project's 45 nm per-operation constants, not measured on hardware. Our own accuracies are SIMULATED, our own energies ESTIMATED.


SIMULATED accuracy (Fashion-MNIST, two detector seeds), ESTIMATED energy (the cost model of [cost frontier](cost_frontier.md)). Founder's direction: close the gap to the CNN cleanly, with new concepts learned from the failures. Scripts in `hw/brain/experiments/month5/`: `detector_selection2.py`, `routed_rich_eval.py`, `routed_selected_eval.py` (logs `detector_selection2*.log`, `routed_rich_eval.log`, `routed_selected_eval_seed{0,1}.log`).

## Lessons from our own failures that shaped this

1. The gains from more channels, two-level codes and clauses **overlapped** (they re-read the same features), so stacking them paid little.
2. The only thing that ever kept a gain at a fraction of its cost was **routing**: spend extra compute only on images the cheap pass is unsure about.
3. Choosing detectors by class information looked free in my first test, but that test kept bits computed with all 128 detectors competing; installed alone the 32 best are no better than 32 random ones (88.77 against 88.75). That claim is **withdrawn** (see the correction in [detector selection](detector_selection_and_gap.md)). Selection does matter once there is room to choose: 64 of 128 installed alone give 90.26 (seed 0) and 89.97 (seed 1) against 89.31 for 64 random (seed 0).

## Deployable detector selection (installed alone, winner-take-all among the chosen detectors only)

| per channel | accuracy | cluster | Shirt recall | Shirt AP | bits | active |
|---|---|---|---|---|---|---|
| shipped unsupervised 32 (reference) | 88.85 | 80.6 | 0.638 | 0.753 | 4,608 | 589 |
| 32 most informative of 128 / 32 random | 88.77 / 88.75 | 80.0 / 80.6 | 0.618 / 0.609 | 0.733 / 0.736 | 4,608 | 632 |
| 48 most informative | 89.42 | 81.5 | 0.633 | 0.762 | 6,912 | 708 |
| 64 most informative, seed 0 / seed 1 | **90.26 / 89.97** | 83.1 / 82.2 | 0.675 / 0.656 | 0.785 / 0.778 | 9,216 | 760 |
| 64 random of 128 (control, seed 0) | 89.31 | 81.3 | 0.654 | 0.763 | 9,216 | 746 |
| 96 most informative | 89.86 | 82.2 | 0.665 | 0.770 | 13,824 | 810 |

Running 64 detectors per channel everywhere costs an estimated 53.4 nJ (1.79 times L: front end doubles).

## Routed second pass (the new result)

First pass: L as shipped on every image. Second pass: the 64-informative front end, run only on the images the shipped table is least sure about (smallest margin) and used to re-score them; everything else keeps the shipped answer.

| share of images routed | seed 0: accuracy / cluster / Shirt recall / Shirt AP | seed 1: accuracy / cluster / Shirt recall / Shirt AP | est. energy | x L |
|---|---|---|---|---|
| none (shipped) | 88.85 / 80.6 / 0.638 / 0.753 | same | 29.9 nJ | 1.00 |
| 10% | 90.13 / 82.4 / 0.658 / 0.765 | 90.03 / 82.2 / 0.655 / 0.767 | 35.3 nJ | 1.18 |
| **20%** | **90.35** / 83.1 / 0.668 / 0.774 | **90.02** / 82.2 / 0.654 / 0.768 | **40.6 nJ** | **1.36** |
| 30% | 90.34 / 83.2 / 0.674 / 0.779 | 89.98 / 82.1 / 0.655 / 0.774 | 46.0 nJ | 1.54 |
| 50% | 90.26 / 83.1 / 0.675 / 0.786 | 89.96 / 82.1 / 0.655 / 0.781 | 56.7 nJ | 1.89 |
| all images (reference) | 90.26 | 89.97 | 53.4 nJ | 1.79 |

Routing the richer 7-channel two-level code (no selection) shows the same effect: 20% of images give 89.98 at 43.0 nJ (1.43 times), against 89.95 for all images at 73.5 nJ.

- **A clean result inside the 2 times ceiling: 90.0 to 90.35% at 1.36 times L's cost (about 41 nJ)**, +1.2 to +1.5 points over shipped (88.85) on two detector seeds; the earlier best inside the ceiling was 89.71 at 1.79 times. Cluster accuracy 83.1 on seed 0 equals the CNN's (83.1); Shirt recall 0.654 to 0.668 (CNN 0.707).
- **Gap to the CNN (91.28):** now 0.9 to 1.3 points (was 2.4), at about 41 nJ against about 260 nJ for the int8 CNN (6 times cheaper) and about 2,300 nJ for the float CNN (56 times).
- Routing at 20% captures the whole gain of the second pass (the 10 to 20% least-sure images are where the extra detail matters); more routing adds nothing.
- Caveats: two seeds (seed-to-seed spread about 0.3 to 0.4); the estimated energy counts the second pass at full cost for each routed image and assumes the router's margin comes free from the first table read; the router and the selection were evaluated on the same test set once per configuration; not yet tested on EMNIST or combined with the clause layer.

Related: [Detector selection and the gap](detector_selection_and_gap.md), [Cost frontier](cost_frontier.md), [Foundations study](foundations_study.md), [Results index](INDEX.md)
