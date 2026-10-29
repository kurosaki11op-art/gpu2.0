---
title: Where the accuracy gap comes from - diagnosis on clothing (28 Oct 2026)
tags: [spark, accuracy, diagnosis, negative-result, cnn-reference]
---

# Gap diagnosis (28 Oct 2026)

Founder's question: find what causes the accuracy gap before fixing it. **SIMULATED accuracy on the 10,000 Fashion-MNIST test images, one seed per network; networks other than L are reference baselines only (not parts of L, per the no-CNN rule).** Script [gap_diagnosis.py](../brain/experiments/month5/gap_diagnosis.py), log [gap_diagnosis.log](../brain/experiments/month5/gap_diagnosis.log); the offline-table test is [offline_table_test.py](../brain/experiments/month5/offline_table_test.py).

## Findings

| measurement | accuracy |
|---|---|
| L alone (on-chip counting table) | 88.85% |
| L + L Deep (shipped) | 89.73% |
| **offline-trained softmax table on the same code**, float / int8 (same inference hardware) | 86.0 to 86.7% (worse than the chip's own rule) |
| **unrestricted network (4608-256-10, float) on L's code** | **90.92%** |
| reference: MLP 784-256-10 on raw pixels | 88.30% |
| **reference: small CNN, 2 conv layers, 8 epochs, raw pixels (measured here)** | **89.91%** |

1. **The learning rule is not the cause.** A proper offline rule on the same linear table is worse (86.0 to 86.7%) than the chip's counting rule (88.85%).
2. **The code is not the main limit either, but it caps a linear readout.** A nonlinear network on the same 4,608-bit code reaches 90.92%, 1.2 points above the shipped system; so the code holds about 91%, and the linear table plus clauses recovers about 1.2 points less than that.
3. **The errors are concentrated.** Shirt alone is 31.4% of all errors (recall 67.8%); the four pairs T-shirt/Shirt (19%), Coat/Shirt (17%), Pullover/Shirt (14%) and Pullover/Coat (11%) are 61% of all errors. Trousers, sandals, bags and boots are 96 to 98% right. Shirt-like classes are hard for every method.
4. **Correction to my earlier statement.** I said we were 3 to 5 points below a CNN (93 to 95%, from the literature as I remembered it, not measured). A plain small CNN trained here for 8 epochs scores 89.91%, 0.2 point above L + Deep. The 93 to 95% figures belong to deeper, longer-trained, augmented networks; the gap is real against those, not against a small CNN at comparable size. One seed and short training: a tuned version of this small CNN would score higher, so this is a floor for the reference, not its best.

## Energy at comparable accuracy (ESTIMATED, operation count only, same 45 nm constants)

The small CNN above needs about 3.9 million multiply-adds per image (conv1 226k, conv2 3.61M, fully connected 31k). At the int8 multiply-add constant used throughout the project (0.2 pJ), that is about 0.77 microjoule per image counting the multiplies alone, with no memory or activation traffic and assuming int8 holds the accuracy. L + L Deep is about 49 nJ per image by the same style of count (adds and table reads). So at near-equal accuracy the operation-count ratio is **about 16x in L's favour (ESTIMATED, a lower bound for the CNN)**. Caveats: the CNN here was trained in float and not quantised; L's own layout-based energy for the Cortex part is 20 to 28 times its operation count (0.18 to 0.26 microjoule, [Cortex energy estimate](cortex_energy_estimate.md)), which must be applied to both sides before any claim; nothing here is measured on a board or a GPU.

## What it means for the pitch

The defensible statement is a matched comparison: against a CNN of similar accuracy (a small one), L + L Deep uses far fewer operations, and the benchmark for that is measured on an FPGA board and a GPU. Against a deep, tuned CNN (93 to 95%) we are behind by 3 to 5 points; the notes say so. What would close that gap is not the learning rule (tested, negative) and not Deep's training (tested, negative) but information the code does not hold for the shirt-like classes.

## Selective answering: fewer wrong results at no extra cost (SIMULATED)

[risk_coverage.py](../brain/experiments/month5/risk_coverage.py): the chip answers only when the margin of its final scores is above a threshold and flags the rest for a fallback (a person, a GPU, another look). The margin is already computed, so there is no extra energy. All 10,000 test images:

| share flagged | accuracy on the answered images | errors per 1,000 answered |
|---|---|---|
| 0% | 89.73% | 103 |
| 5% | 91.92% | 81 |
| 10% | 93.83% | 62 |
| 20% | 95.80% | 42 |
| 30% | 97.19% | 28 |
| 40% | 98.13% | 19 |

The 20% least-sure images hold 67% of all errors. So accuracy among the images the chip is sure about can exceed what a deep CNN reaches on every image, at the price of handing 10 to 20% to a fallback. Caveat: a CNN can also decline by its softmax confidence and would show a similar curve; that comparison is not done here (the reference networks did not save their scores), so this shows the chip has a usable confidence signal, not that it beats a CNN at it.

Related: [Accuracy gap tests](accuracy_gap_tests.md), [L Deep build](l_deep_build.md), [Results index](INDEX.md), [Journal](../../docs/journal.md)
