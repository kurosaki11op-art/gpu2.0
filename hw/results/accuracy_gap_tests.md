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

## Test 3: a better routing signal and combining the two answers - AT MOST 0.1 POINT (SIMULATED)

[routing_signal_test.py](../brain/experiments/month5/routing_signal_test.py) runs both stages on every test image (integer scores from the RTL memory files), then lets each signal pick the images to route at the same share (same energy):

| accuracy at routed share | 10% | 15% | 20% | 30% | 40% |
|---|---|---|---|---|---|
| margin (shipped) | 89.62 | 89.82 | 89.73 | 89.71 | 89.68 |
| margin, confusable top class only | 89.42 | 89.50 | 89.39 | 89.37 | 89.38 |
| margin / top score | 89.69 | 89.75 | 89.76 | 89.73 | 89.73 |
| learned router: P(L wrong), cross-fitted | 89.45 | 89.65 | 89.72 | 89.70 | 89.69 |
| learned router: P(Deep fixes L), cross-fitted | 89.56 | 89.81 | 89.77 | 89.69 | 89.67 |
| ORACLE: route exactly where Deep fixes L (not realisable) | 91.74 | 91.68 | 91.51 | 91.37 | 91.16 |

L alone 88.85%; Deep on every image 89.67%. Deep fixes 2.9% of all images but also breaks 2.1% that L had right, which is why the oracle stops at 91.7% and why no realisable signal gains more than about 0.1 point (the shipped margin is already within noise of the best, and 15% routed is as accurate as 20%, a slightly cheaper operating point). Adding L's scores to Deep's on routed images instead of replacing them (weights 1:1, 1:2, 1:4, 2:1) moves accuracy by at most 0.08 point. Class-pair routing is worse than the margin.

## Tests 4 to 6: three attempts to fix L Deep itself - NONE WORKED (SIMULATED)

L Deep fixes 2.8% of all images and breaks 1.9% (test 3). Three fixes, all against the same routing (L's margin, 20% routed) and the same 2,000 shipped clauses unless stated:

| fix | routed accuracy | total accuracy | fixes / breaks (% of all images) |
|---|---|---|---|
| shipped | 64.9% | 89.73% | 2.80 / 1.92 |
| **4. stage-2 table trained on the hard images only** (lowest 20 / 40 / 60% of cross-fitted margins; [deep_fix_test.py](../brain/experiments/month5/deep_fix_test.py)) | 63.5 / 64.4 / 64.9% | 89.45 / 89.63 / 89.72% | 3.09 / 2.49, 2.94 / 2.16, 2.87 / 2.00 |
| all images plus the hard 30% repeated twice | 64.9% | 89.73% | 2.97 / 2.09 |
| **5. residual Deep**: keep L's scores, add only a clause correction trained on cross-fitted scores (softmax regression, int8 weights times 2^k; [deep_residual_test.py](../brain/experiments/month5/deep_residual_test.py)) | 61.1 to 61.9% | 88.97 to 89.12% | 2.18 to 2.81 / 1.91 to 2.69 |
| **6. specialist clauses**: 3,000 more clauses trained only on the 40% of training images L is least sure about, added to the 2,000 ([deep_specialist_test.py](../brain/experiments/month5/deep_specialist_test.py), clause training `tm_faithful.py` with HARDQ=0.4) | 65.4% (+1,000) / 65.6% (+3,000) | 89.82% / 89.87% | 2.82 / 1.85, 2.82 / 1.80 |
| specialist clauses instead of the shipped ones | 63.1% | 89.37% | 2.55 / 2.03 |

Reading: the training set of the table does not matter (test 4); keeping L's scores and adding a clause correction is worse than retraining the table jointly (test 5, about 0.7 point lower); a clause layer aimed at the hard images adds at most 0.14 point and costs far more per clause (25 literals per clause against about 7 for the shipped ones, so 3,000 more clauses would add roughly 3x the stage-2 energy). The specialist layer alone reaches only 86.3% on all images. So the limit is not how Deep is trained on this input: the information in the 4,608-bit code plus pixel thresholds and the local-feedback clause learner seems to cap the system near 89.7 to 89.9%. Remaining untested: a richer input code for the hard classes (the notes list edge-map and multi-code variants as not yet done), a different clause learner, or accepting the cap and making the chip cheaper instead.

## Conclusion

The energy-efficient point is the one already built: L Deep with 2,000 clauses and 20% routing. Further accuracy costs energy steeply (about 3 nJ more per image for each 0.1 point beyond 89.7%, from the dense curve; the clause frontier in [L Deep build](l_deep_build.md) results 6 and 9 shows the same shape). Routing signals and score combining are also exhausted (Test 3). The remaining lever is the quality of Deep itself (it breaks 2.1% of images while fixing 2.9%) and the detector learning rule (a Cortex change), neither tested yet.

Related: [L Deep build](l_deep_build.md), [Results index](INDEX.md), [Journal](../../docs/journal.md)
