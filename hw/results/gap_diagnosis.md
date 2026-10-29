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

## Update 29 Oct 2026: the CNN's confidence curve, fixability, and the cascade (SIMULATED accuracy, ESTIMATED energy)

Scripts [cnn_confidence.py](../brain/experiments/month5/cnn_confidence.py) and [cascade_test.py](../brain/experiments/month5/cascade_test.py), logs next to them. Two reference CNNs, one seed each: a small one (8 epochs) and a stronger one (4 conv layers, shift and flip augmentation, 12 epochs). **The small CNN scored 90.70% this time against 89.91% in the first run (different seed and batch order), so seed noise is about 0.8 point and "level with L + Deep" above should read "within about 1 point".** The strong CNN reaches 91.75%, not the 93 to 95% of the literature (heavier networks and longer training).

**Confidence curves** (accuracy on the answered images when the least-sure share is flagged):

| share flagged | 0% | 5% | 10% | 20% | 30% | 40% |
|---|---|---|---|---|---|---|
| chip (L + L Deep), margin | 89.73 | 91.92 | 93.83 | 95.80 | 97.19 | 98.13 |
| small CNN, logit margin | 90.70 | 92.86 | 94.70 | 97.21 | 98.57 | 99.42 |
| strong CNN, logit margin | 91.75 | 93.78 | 95.31 | 97.69 | 99.00 | 99.73 |

The chip's curve is below both CNNs by about 1 to 2 points at 20% flagged: it is a usable confidence signal, not a better one.

**Fixability.** The chip makes 1,027 errors. The strong CNN gets 42.2% of them right (small CNN 34.5%), so a stronger model could fix up to about 4.3 points of the 10.3; on the chip's flagged 20% the strong CNN scores 74.8% against the chip's 65.4%. **594 errors (5.9% of all images) are wrong for both**, 210 of them Shirt, then Pullover 91, T-shirt 84, Coat 73, Dress 57: these look hard for any model at this resolution (oracle chip-or-strong-CNN accuracy 94.06%). So the errors are partly fixable (by a stronger second opinion) and partly not.

**Cascade** (chip answers what it is sure about, the least-sure share goes to the strong CNN as a fallback, e.g. a GPU or a person; energy per image = first stage + share x fallback, operation counts only, so lower bounds for the CNNs, chip first stage 49 nJ):

| flagged to fallback | chip -> strong CNN accuracy | energy per image | vs strong CNN alone (91.75%, 3.8 uJ) | small CNN -> strong CNN: accuracy, energy |
|---|---|---|---|---|
| 10% | 91.27% | 0.43 uJ | 8.9x less | 91.62%, 1.15 uJ |
| 15% | 91.42% | 0.62 uJ | 6.1x less | 91.79%, 1.34 uJ |
| 20% | 91.60% | 0.81 uJ | 4.7x less | 91.85%, 1.53 uJ |

At 15 to 20% flagged the chip-first cascade is within 0.2 to 0.4 point of the CNN-only cascade at about 2x less energy, and within 0.2 to 0.5 point of the strong CNN alone at about 5 to 6x less. Caveats: the fallback must exist (the chip then removes 80 to 90% of its load, it does not replace it); the chip's layout energy is 20 to 28 times its operation count (apply to both sides before any claim); CNN energies exclude memory traffic; nothing is measured on a board or a GPU.

### Limits revisited (29 Oct 2026, ESTIMATED): CNN memory traffic and the chip's first-stage energy

[cascade_energy_model.py](../brain/experiments/month5/cascade_energy_model.py), log next to it. Weight reads and activation traffic added to the CNN energies (project SRAM constants; the strong CNN has 0.87 M parameters, mostly in its first fully connected layer, so at batch 1 its weights cost more to read than its multiplies):

| CNN energy per image (uJ) | small CNN | strong CNN |
|---|---|---|
| multiplies only | 0.77 | 3.80 |
| + traffic, weights amortised over a batch of 64 | 1.03 | 4.18 |
| + traffic, batch 1, large SRAM at 4 pJ/byte | 1.03 | 7.49 |
| + traffic, batch 1, large SRAM at 22 pJ/byte | 1.03 | 23.16 |

At 15% flagged the chip -> strong CNN cascade (91.42%) uses 0.62 to 3.5 uJ against 3.8 to 23 uJ for the strong CNN alone (6.1x to 6.6x less) and is 1.3x to 2.5x cheaper than the small -> strong CNN cascade. **Break-even:** the chip cascade only loses if its first stage costs more than the small CNN (about 1.0 uJ, 21 times the 49 nJ operation-count estimate) against the CNN-only cascade, or more than 3.2 to 20 uJ (66 to 400 times) against the strong CNN alone. The Cortex layout estimate (0.18 to 0.26 uJ) is inside that margin, so the cascade advantage survives the layout adjustment on the chip side, but it is a margin of 4x to 5x, not of orders of magnitude, against the CNN-only cascade. GPU measurement kit: `gpu_energy_baseline.py` now takes `--net small|strong` (the two networks above) and is smoke-tested on the CPU path only; it still has to be run on a real GPU by the founder.

Related: [Accuracy gap tests](accuracy_gap_tests.md), [L Deep build](l_deep_build.md), [Results index](INDEX.md), [Journal](../../docs/journal.md)
