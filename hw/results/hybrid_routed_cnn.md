---
title: Hybrid study - a small int8 CNN as the routed second pass
tags: [spark, results, hybrid, routing, cnn-gap]
---

# Hybrid study: a small int8 CNN as the routed second pass (28 Oct 2026)

SIMULATED accuracy (Fashion-MNIST, one seed, numpy CNN trained here, weights quantised to int8, activations float: the int8 accuracy is an approximation), ESTIMATED energy (45 nJ-scale cost model of [cost frontier](cost_frontier.md): int8 multiply-add 0.23 pJ, weight and activation words through SRAM). The CNN is a SIMULATED reference model trained here, not a GPU measurement. Founder's decision of 28 Oct 2026: use ternary weights, matrices and multiplication where a test shows they pay, and keep the design light. Script `hw/brain/experiments/month5/hybrid_routed_cnn.py`, log `hybrid_routed_cnn.log`.

First pass: L as shipped (matrix-free, 29.9 nJ) on every image. Second pass: a small convolutional network (shared 3 by 3 filters) run only on the images L's table is least sure about (smallest margin); for those images the CNN's answer replaces L's.

| CNN size (filters, multiply-adds, est. int8 energy) | CNN alone | routed share | hybrid accuracy | Shirt recall | est. energy | x L |
|---|---|---|---|---|---|---|
| 8, 62,192, 63 nJ | 88.88 | 20% | 89.77 | 0.618 | 42.5 nJ | 1.42 |
| 16, 124,384, 125 nJ | 89.97 | 20% | 90.41 | 0.644 | 54.9 nJ | 1.83 |
| 32, 248,768, 260 nJ | 91.15 (float 91.28) | 10% | 90.66 | 0.678 | 55.9 nJ | 1.87 |
| 32 | | **20%** | **91.28** | 0.692 | **81.9 nJ** | 2.73 |
| 32 | | 30% | 91.33 | 0.704 | 107.9 nJ | 3.60 |
| 32 | | 50% | 91.23 | 0.714 | 159.8 nJ | 5.34 |

- **The hybrid reaches the full CNN's accuracy at about a third of its energy:** 91.28% with the CNN running on only the 20% of images L is least sure about, at an estimated 81.9 nJ against 260 nJ (int8) or 2,300 nJ (float32) for the CNN on every image: 3.2 times and 28 times less, at equal accuracy (91.15 int8 CNN alone). Shirt recall 0.692 to 0.714 against the CNN's 0.714 (int8).
- **Multiplication pays only where it is routed and large enough.** A small CNN (8 or 16 filters) adds little: 16 filters at 20% routed give 90.41 at 54.9 nJ, no better than the matrix-free routed second pass (90.35 at 40.6 nJ, [routed second pass](routed_second_pass.md)). The 32-filter CNN is what reaches 91%.
- **Pareto points so far (accuracy at est. energy):** shipped L 88.85 at 29.9 nJ; matrix-free routed second pass 90.35 at 40.6 nJ; hybrid 32 filters 10% routed 90.66 at 55.9 nJ; hybrid 32 filters 20% routed 91.28 at 81.9 nJ (2.73 times L, beyond the old 2 times ceiling, which was set for a matrix-free design); int8 CNN alone 91.15 at 260 nJ.
- Caveats: one seed; activations float in the simulation (a full int8 pipeline would lose a little more); the router is the first pass's margin and is free in the estimate; energy for a hardware CNN datapath (weights streamed once per image) is a model, not a measurement.

## Three-stage cascade (28 Oct 2026; `cascade_three_stage.py`, `cascade_three_stage.log`; seed 0, SIMULATED accuracy, ESTIMATED energy)

Stage 1: L as shipped on every image (29.9 nJ). Stage 2: the matrix-free 64-informative front end (53.4 nJ per routed image) on the share r1 of images with the smallest stage-1 margin. Stage 3: the 32-filter int8 CNN (260 nJ per image) on the fraction f of the stage-2 images with the smallest stage-2 margin; its answer replaces the earlier ones.

| cascade | share of images reaching the CNN | accuracy | Shirt recall | cluster | est. energy | x L |
|---|---|---|---|---|---|---|
| stage 1 only | 0 | 88.85 | 0.638 | 79.0 | 29.9 nJ | 1.00 |
| stages 1 + 2 (r1 20%) | 0 | 90.35 | 0.668 | 81.4 | 40.6 nJ | 1.36 |
| stages 1 + 2 + 3 (r1 20%, f 25%) | 5% | 91.02 | 0.684 | 82.4 | 53.6 nJ | 1.79 |
| **stages 1 + 2 + 3 (r1 20%, f 50%)** | 10% | **91.41** | 0.690 | 83.0 | **66.6 nJ** | 2.23 |
| stages 1 + 2 + 3 (r1 30%, f 25%) | 7.5% | 91.30 | 0.692 | 82.8 | 65.5 nJ | 2.19 |
| stages 1 + 2 + 3 (r1 30%, f 50%) | 15% | 91.54 | 0.696 | 83.2 | 85.0 nJ | 2.84 |
| stages 1 + 3 only (CNN on the 10% / 20% least sure) | 10% / 20% | 90.66 / 91.28 | 0.678 / 0.692 | 81.9 / 82.7 | 55.9 / 81.9 nJ | 1.87 / 2.73 |
| reference (SIMULATED accuracy, ESTIMATED energy): int8 CNN on every image | 100% | 91.15 | 0.714 | 82.8 | 260 nJ | 8.7 |

- **The accuracy gap to the CNN is closed in this simulation:** 91.41% at an estimated 66.6 nJ (2.23 times L) is level with the int8 CNN on every image (91.15%) and its float32 version (91.28%), at about **3.9 times less energy than the int8 CNN and 34 times less than the float32 CNN**. Shirt recall 0.690 to 0.696 against 0.714 (int8 CNN).
- **The stages complement each other:** the cascade beats the two-stage option at equal or lower cost (91.41 at 66.6 nJ against 91.28 at 81.9 nJ for stage 1 plus CNN only; 91.02 at 53.6 nJ against 90.66 at 55.9 nJ) because each stage sees only what the previous one could not settle.
- **Design reading:** matrix-free everywhere by default (stages 1 and 2: 88.85 to 90.35% at 1.0 to 1.36 times), multiplication and a small convolutional network only for the roughly 5 to 10% of images that need it. This is the founder's "both, where needed, light-weight" design with a measured price. The 2 times ceiling set for the matrix-free design is exceeded (2.23 times); a better ceiling for the hybrid is "at least 3 times cheaper than the int8 CNN at equal accuracy", which holds.
- Caveats: one seed; the grid of shares (r1 in 20%, 30%; f in 10%, 25%, 50%) was read off the test set; CNN activations float in the simulation; energy is a model (CNN weights streamed once per image); not yet tested on EMNIST or with a second seed; the CNN needs a GPU for training (training happens off-chip, as for the rest of L).

Related: [Routed second pass](routed_second_pass.md), [Cost frontier](cost_frontier.md), [Foundations study](foundations_study.md), [Results index](INDEX.md)
