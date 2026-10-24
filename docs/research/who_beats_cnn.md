---
title: Who scores 96 to 99 percent, are they like us, and how do they win (24 Oct 2026)
tags: [l, research, analysis, cnn]
---

# Who scores 96 to 99.3%, are they matrix- and multiply-free, and how do they win?

Built only from the full-paper notes ([papers_notes](papers_notes/INDEX.md)) and the Fashion-MNIST benchmark README (read in full; submissions are unverified by the maintainers). Numbers marked UNVERIFIED in the notes are not repeated as fact.

## 1. The scores, split by what kind of machine produced them

| Score | Data set | Model | Multiplies? | Matrices? | Size | How it got there |
|---|---|---|---|---|---|---|
| **96.7%** | Fashion-MNIST | WRN40-4 (wide ResNet) | yes | yes (dense convolution) | 8.9 M parameters | deep supervised CNN with backprop, standardisation, random crops and flips |
| 96.3% / 95.9% | Fashion-MNIST | WRN-28-10 with / without Random Erasing | yes | yes | about 36 M | same, plus erasing augmentation (+0.4) |
| 95.4% | Fashion-MNIST | DenseNet-BC | yes | yes | 768 K | same family |
| **92.5%** | Fashion-MNIST | 2-conv CNN | yes | yes | under 100 K | backprop; the best tiny model |
| 92.6% | Fashion-MNIST | HOG features + SVM | SVM yes | SVM kernel | hand features | no backprop, fixed edge features |
| **94.68 / 93.19 / 92.18%** | Fashion-MNIST | Fuzzy-Pattern Tsetlin Machine (8,000 / 20 / 2 clauses per class) | **no** | **no** (bit tests, popcount) | tiny: at most 48 KB, small 80 KB, big 4.8 MB (derived) | rich 59,584-bit input code, 1,000 epochs, big model also 6x augmentation |
| 99.23 / 99.35% | MNIST | LogicTreeNet M / L (convolutional logic-gate trees) | **no** | **no** (gates, gathers, popcount) | 566 K / 1.27 M gates | gradient-trained relaxed gates, then argmax gates; weight-shared conv gate trees |
| 99.4% | MNIST | AdderNet | no multiplies in convolution, but batch-norm multiplies | **yes** (dense L1 convolution) | LeNet-5 size | breaks our matrix-free rule |
| 99.4% / 99.2% | MNIST | convolutional Tsetlin machine / 2-conv CNN | TM no, CNN yes | TM no | | |
| 86.29% | CIFAR-10 | LogicTreeNet L | no | no | 61 M gates | needs a teacher CNN for the big models |
| 97.9 to 98.6% | MNIST | NeuraLUT-Assemble (lookup tables) | no multiplies at inference | table lookups | | dense float sub-networks during training only |
| 89.12% | Fashion-MNIST | DWN (weightless lookup network) | no | no | 7.8 KiB | gradient-trained lookup tables |

**So: the 96 to 96.7% Fashion-MNIST scores belong to ordinary CNNs (multiplies, dense matrices, millions of parameters, augmentation). The matrix- and multiply-free models reach 92 to 94.7% on Fashion-MNIST (Tsetlin family) and 99.2 to 99.35% on MNIST (logic-gate trees). Nothing matrix-free is reported above 94.7% on Fashion-MNIST.** (A 99.65% MNIST-style claim in a journal paper was not read and is unverified.)

## 2. How the matrix-free winners win (what they all do)

1. **They spend their bits on the input code, not on the learner.** FPTM: raw pixels in 4 quantile levels plus 8 fixed edge maps (3x3, 5x5, 7x7 Sobel-type kernels and a line detector, in two orientations), each in 9 sign-split quantile bits: 59,584 bits per image. Two clauses per class on that code beat 8,000 clauses on a plain 1-bit code (92.18 against about 91.2). Four different booleanisations used as a team reach 93.0 (Composites). Our code: 4,608 bits from learned detectors with hard winners, or 3,136 bits of thermometer: it is 13 times smaller and has no edge maps.
2. **They keep the readout position-specific and wide**, with fuzzy (saturating) matching of many bits, not a single linear sum of a small code.
3. **They train for a long time with gradients or feedback:** 1,000 epochs (FPTM), 100 epochs (DWN), 200 to 500 epochs (difflogic, LUT family). L reads each image once (one pass; extra passes did not help, because the code, not the passes, limits it).
4. **Logic-gate networks need weight sharing to reach image accuracy**: LogicTreeNet's convolutional gate trees (shared gate choices over positions), OR pooling, fixed edge detectors and a teacher. The flat difflogic net reaches only 62.14% on CIFAR-10 against 86.29% for the convolutional one.
5. **They add depth only with care** (residual initialisation z=5 on the pass-through gate; without it 76.18 instead of 84.99 on CIFAR-10).

## 3. How they handled the failures we also hit

| Failure we hit | What they did |
|---|---|
| One layer of binary features plateaus near 89 to 90 | richer fixed code (FPTM), or depth with weight sharing (LogicTreeNet), or teams of encodings (Composites) |
| Hard winner-take-all coding scales badly | soft or tuned winner-take-all; but hard wins on MNIST (98.29 against 97.87), so it depends on the data |
| Free lookup tables trained with straight-through gradients are unstable (our conv lookup net stuck at 75%) | DWN: extended finite-difference gradient (+1.1), learnable mapping in the first layer only (+2.2), spectral regularisation (+1.1), decayed learning rate 1e-2 to 1e-5, 100 epochs; difflogic: softmax relaxation of 16 gates with residual initialisation instead of straight-through |
| Random fixed wiring makes small nets vary (about 0.3 on MNIST S) | learned grouping (dense train, prune, retrain) in NeuraLUT-Assemble |
| Overfitting of tiny models | augmentation (6x for the big FPTM, flips, rotation, zoom), dropout in ULEEN |
| Fashion-MNIST Shirt confusion | **none of the six Tsetlin papers or the gate/LUT papers reports per-class Shirt accuracy**; nobody has solved or measured it, and the only measured ambiguity is a whole-test-set Bayes error of about 3 to 4% |

## 4. Where and why we fail (diagnosis, in order of weight)

1. **Input code too small and too crude (largest).** Evidence: raw 4-level thermometer alone gives 82.5%; our learned-detector code 88.9%; going from 32 to 64 detectors gave 89.9% (+1.0); the best matrix-free models use 13 times more bits with edge maps. Not yet tested: the FPTM code with our counting readout (running).
2. **Single layer, no weight sharing, no depth.** The matrix-free models above 92% either use a code as rich as a deep layer's output (FPTM) or convolutional weight sharing with learned gates (LogicTreeNet).
3. **Training length and method.** L's one-pass counting rule is sufficient for its own code but cannot make the code discriminative; the winners train 100 to 1,000 epochs.
4. **Augmentation.** Used by every top result; we use none (the 5 shifted views at test time are only a small part).
5. **Not the main cause:** label noise (about 3 to 4% of the whole test set), memory (4x memory gave +1.7 points), the readout type (float readout equals counting readout on the same bits).

## 5. What this says to do (in this order, nothing blind)

1. Test the FPTM-style rich code with L's counting readout (running now) to measure how much of the 92 to 94% is the code alone.
2. If the code is the lever, keep L's rules (counts, XNOR/popcount, compares, shifts) and enlarge the code: edge maps, quantile thermometers, multi-scale kernels; then test teams of codes and augmentation.
3. For the accelerator track (training on a GPU allowed): reimplement difflogic with residual initialisation, then convolutional gate trees; this is the only published matrix-free route to CNN-like accuracy on images.
4. Report honestly: matrix-free models reach 92 to 94.7% on Fashion-MNIST in the literature; no source shows 96% without a CNN.

Related: [Docs index](../INDEX.md), [Synthesis](papers_synthesis.md), [Paper notes](papers_notes/INDEX.md), [Failure analysis](../failure_analysis_clothing.md)
