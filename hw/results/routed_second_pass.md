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

## Follow-up (28 Oct 2026): better routers and clauses in the second pass (`second_stage_extras.py`, `second_stage_extras_seed0.log`; seed 0, SIMULATED accuracy, ESTIMATED energy)

Second pass = the 64-informative front end; routers use only the first (shipped) pass. At 20% routed, accuracy / Shirt recall / est. energy:

| router | stage-2 only | + 2,000 clauses | + 4,000 clauses |
|---|---|---|---|
| margin (used so far) | 90.35 / 0.668 / 40.6 nJ | 90.47 / 0.675 / 48.8 nJ | 90.25 / 0.676 / 57.2 nJ |
| cluster-aware (bonus for T-shirt, Pullover, Coat, Shirt) | 90.40 / 0.674 / 40.6 nJ | 90.38 / 0.679 / 48.8 nJ | 90.16 / 0.682 / 57.2 nJ |
| class-relative (margin over the predicted class's usual margin) | 90.29 / 0.680 / 40.6 nJ | 90.50 / 0.687 / 48.8 nJ | 90.19 / 0.692 / 57.2 nJ |

- **No router beats the margin router in accuracy** (90.29 to 90.40 against 90.35, inside the 0.3 to 0.4 spread); the class-relative router lifts Shirt recall from 0.668 to 0.680 at the same cost.
- **Clauses in the second pass add almost nothing to accuracy** (+0.12 with 2,000 clauses, -0.10 with 4,000) and raise Shirt recall by up to 0.024 (0.692 with 4,000 clauses and the class-relative router, against the CNN's 0.707 SIMULATED) at +16 nJ (1.91 times L).
- Conclusion: the plateau at about 90.3 to 90.5% is again an information overlap, not a routing or readout limit. Cheapest best point stays the stage-2 routed pass at 20% (90.35 at 40.6 nJ); Shirt recall can be bought (0.69 at 1.9 times L) but accuracy cannot.

## Follow-up (28 Oct 2026): redundancy-aware selection and a two-level output on the stage-2 detectors (seed 0; SIMULATED accuracy, ESTIMATED energy; `detector_selection3.py`, `stage2_twolevel.py`)

**Redundancy-aware detector choice** (greedy: class information minus lambda times redundancy with the detectors already chosen; 64 of 128 per channel, installed alone):

| choice | accuracy | cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|
| top class information (reference) | **90.26** | 83.1 | 0.675 | 0.785 |
| redundancy-aware, lambda 0.5 / 1.0 / 2.0 | 89.79 / 89.93 / 89.79 | 82.0 / 82.4 / 82.3 | 0.687 / 0.675 / 0.659 | 0.775 / 0.773 / 0.781 |

No gain: choosing complementary detectors does not beat choosing the most informative ones; the "overlap" is not removable by selection from this pool.

**Two-level output on the stage-2 detectors, routed** (levels = pooled-window count thresholds; second pass on the least-sure share of images):

| levels | routed share | accuracy | cluster | Shirt recall | Shirt AP | est. energy |
|---|---|---|---|---|---|---|
| 1 (reference) | 20% | 90.35 | 83.1 | 0.668 | 0.774 | 40.6 nJ (1.36x) |
| 1, 4 | 20% | 90.08 | 82.9 | 0.652 | 0.774 | 42.5 nJ (1.42x) |
| 1, 2, 4 | 10% | 90.12 | 82.5 | 0.677 | 0.771 | 38.3 nJ (1.28x) |
| 1, 2, 4 | 20% | 90.32 | 83.1 | **0.697** | 0.784 | **46.7 nJ (1.56x)** |
| 1, 2, 4 | 30% | 90.25 | 83.2 | **0.704** | 0.781 | 55.0 nJ (1.84x) |

- **Shirt recall reaches 0.697 to 0.704, level with the CNN's 0.707 (SIMULATED: our own numpy CNN)**, at 1.56 to 1.84 times L's cost; accuracy stays at the plateau (90.3). So the Shirt target set by the measured CNN is met inside the 2 times ceiling.
- **Accuracy plateaus at about 90.3% (seed 0; seed 1 gave 90.0) for every variant inside the ceiling** (routers, clauses, redundancy-aware selection, two-level output). The remaining gap to the CNN (91.28, SIMULATED) is 0.9 to 1.3 points. Selection from a bigger pool (256) and joint training of the features are the untested levers; the foundations study suggests the CNN's last point needs features and readout trained together with graded activations.

Related: [Detector selection and the gap](detector_selection_and_gap.md), [Cost frontier](cost_frontier.md), [Foundations study](foundations_study.md), [Results index](INDEX.md)
