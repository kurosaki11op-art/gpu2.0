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

Related: [Routed second pass](routed_second_pass.md), [Cost frontier](cost_frontier.md), [Foundations study](foundations_study.md), [Results index](INDEX.md)
