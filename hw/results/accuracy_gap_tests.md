---
title: Accuracy gap tests - better detectors and a multiplier-based stage (both negative or no better than L Deep)
tags: [spark, l-deep, accuracy, energy, negative-result]
---

# Accuracy gap tests (28 Oct 2026)

Question from the founder: why is accuracy still 89.7% after the hybrid, and what is the energy-efficient way to raise it. Context: L alone 88.85%; on the 20% of images routed to L Deep, L is 60.5% right and Deep 64.9%; the 80% not routed are 95.9% right ([L Deep build](l_deep_build.md)). **SIMULATED accuracy; energy ESTIMATED with the project's 45 nm constants (int8 multiply-add 0.2 pJ, SRAM read 10 to 22 pJ per 64-bit word by size); every number is a model, none is measured.**

## Test 1: detectors fitted on all ten classes (zero inference cost) - NO GAIN

The shipped detectors are fitted on T-shirt and Trouser images only. [detector_fit_test.py](../brain/experiments/month5/detector_fit_test.py) refits them on all classes and retrains the table the same way:

| detector fit | L alone accuracy | Shirt recall |
|---|---|---|
| shipped (classes 0 and 1, 12,000 images) | 88.85% | 0.638 |
| all ten classes, 12,000 images | 88.87% | 0.612 |
| all ten classes, 30,000 images | 88.80% | 0.634 |

The fit data is not the limit. A fixed 5x5-window code with 4,608 bits seems to cap L near 88.9%; better unsupervised detectors do not move it. Recorded as a failure of the cheapest idea.

## Test 2: a small multiplier-based (int8 dense) stage on raw pixels, routed images only - NOT BETTER THAN L DEEP PER JOULE

[dense_stage_test.py](../brain/experiments/month5/dense_stage_test.py) trains a dense model on the training pixels and applies it only to the same routed 20% (hybrid component, would need multipliers). Energy per routed image = multiply-adds at 0.2 pJ plus every weight read once from SRAM; the average per image is 0.2 of it.

| stage | routed accuracy | total accuracy | extra energy per image on average (ESTIMATED) |
|---|---|---|---|
| L alone | 60.5% | 88.85% | 0 |
| **L Deep (2,000 clauses)** | **64.9%** | **89.73%** | **about 19 nJ** (49 nJ total against L's about 30 nJ) |
| logistic, 784x10 | 54.5% | 87.65% (worse than L) | 2.3 nJ |
| MLP 784-32-10 | 61.5% | 89.04% | 13.7 nJ |
| MLP 784-64-10 | 65.0% | 89.74% | 30.0 nJ |
| MLP 784-128-10 | 66.5% | 90.04% | 60.0 nJ |

At equal accuracy (89.7%) the dense stage costs about 30 nJ against Deep's 19 nJ, and it needs multipliers and a 50 KB weight store; getting to 90.0% costs 60 nJ. So the multiplier stage is not worth building under the 28 Oct rule (a hybrid component only where a test shows it pays). The logistic stage is cheap but hurts. Caveat: the dense models were trained briefly (30 iterations, not converged), no int8 quantisation loss was applied, and no sparsity (skipping zero pixels) was credited; either could move the dense numbers somewhat, not by the 1.5x needed to beat Deep.

## Conclusion

The energy-efficient point is the one already built: L Deep with 2,000 clauses and 20% routing. Further accuracy costs energy steeply (about 3 nJ more per image for each 0.1 point beyond 89.7%, from the dense curve; the clause frontier in [L Deep build](l_deep_build.md) results 6 and 9 shows the same shape). The remaining untested directions are new detector learning rules (supervised or discriminative, a Cortex change) and a better routing signal.

Related: [L Deep build](l_deep_build.md), [Results index](INDEX.md), [Journal](../../docs/journal.md)
