---
title: Failure analysis - why L stays behind on clothing (24 Oct 2026)
tags: [l, clothing, failures, analysis, research]
---

# Why L stays behind a CNN on clothing: past failures, causes, what the literature says, what to try

Written before proposing further fixes, as asked. Numbers are SIMULATED unless marked; literature numbers come from web-search summaries only (paper sites are blocked from the cloud container, so no paper has been read in full yet) and must be checked against the papers.

## 1. What failed, and the most likely cause

| Attempt | Result | Likely cause (evidence) |
|---|---|---|
| More passes over the data | no change (88.9) | the readout had already converged; not a data-volume or one-pass problem ([l_passes.log](../hw/brain/experiments/month5/l_passes.log)) |
| Float readout instead of counting | same accuracy (88.1 to 90.0 on the same bits) | **the readout is not the bottleneck**; a single layer of binary features with a linear readout caps near 90% ([clothing_features_round](../hw/results/clothing_features_round.md)) |
| Specialist with the same code | 80.8 to 80.9 within the group | a second decision on the same evidence adds nothing |
| Finer detectors on the four classes | +1.7 within group, 4x code | features carry the information; more bits help slowly |
| Hand-made shape cues (profile, inside, neck, edges) | at most +0.6 | the cues I chose were not the discriminating ones, or the information is not in 28 x 28 pixels |
| HOG-style bits, conjunction features chosen by counting | +0.9 and +0.9 (90.7 best) at 2 to 5x memory | nonlinear features help (float ceiling 91.3), at a memory price |
| Pair-only model T-shirt vs Shirt | 88.25 at best (2-way) | **a floor of about 88% even for a model that sees only these two classes**: label overlap at this resolution |
| CNN ruler | Shirt recall only 79.4 | even backprop with all data does not separate them: part of the confusion is in the labels (Cleanlab: over 100 Shirt images look like T-shirt/top, since T-shirt/top covers general tops; company source) |
| Real colour photos | Shirt recall 61 to 80 on the pair, no gain on the 4-way task | colour is real independent evidence for the pair; small noisy data, possible colour bias |
| Gradient-trained lookup layer, conv lookup net | 88.9 at 78 KB; about 75 at 3 epochs | one layer is limited like the rest; free table entries with straight-through gradients trained badly (unstable, slow) |
| Sparse / dense binary conv nets | 88.4 / 89.7 | binary activations plus overfitting and noisy training; dense variant about 200x the operations of L, against the design principle |
| Cascade (second look when unsure) | validated +0.9, Shirt no gain | stage 2 moves the Shirt/T-shirt boundary instead of separating the classes |

## 2. Process failures of mine (also failures)

- A spoken name used at test time is the label: the "second sense" test was an oracle experiment and was withdrawn.
- A cascade gate chosen on the test images and a one-pass memory comparison with unlike things (learning state against deployed size) gave optimistic claims; both corrected.
- One seed everywhere; differences of 0.3 are noise.
- "74 times less energy" was against a small int8 MLP in an operation-count model, not a CNN.

## 3. What the literature says (search summaries, to be read in full)

- Unsupervised Hebbian-style learning with a simple readout lands at 88.9% on Fashion-MNIST (3-layer MLP 89.5%) ([arXiv 2406.04733](https://arxiv.org/pdf/2406.04733)); a cerebellum-inspired sparse code 90.5% ([listing](https://econpapers.repec.org/RePEc:plo:pcbi00:1014595)). **L sits where this family sits.**
- Hyperdimensional computing 84 to 85% ([Frontiers 2024](https://www.frontiersin.org/journals/big-data/articles/10.3389/fdata.2024.1371518/text), [arXiv 2601.20061](https://arxiv.org/pdf/2601.20061)): L is already better.
- Convolutional Tsetlin machine 91.5% ([arXiv 1905.09688](https://arxiv.org/pdf/1905.09688)); Fuzzy-Pattern Tsetlin Machine 92.18% with 2 clauses per class and 94.68% with 8,000 ([arXiv 2508.08350](https://arxiv.org/pdf/2508.08350)), where **the convolutional preprocessing sits in the booleanisation stage, not in the learner**: the input encoding is the lever.
- Hard winner-take-all sparse Hebbian coding generalises and scales badly with depth ([arXiv 2501.17266](https://arxiv.org/pdf/2501.17266)); soft (k-winner) coding beat hard by about 8 points in earlier CIFAR work (from the research notes, second-hand).
- AdderNet (additions instead of multiplications) matches a CNN on MNIST (99.4%) and is within about 0.1 point on CIFAR-10 with VGG-small, at about 2x the operation count ([arXiv 1912.13200](https://arxiv.org/pdf/1912.13200)); no Fashion-MNIST figure found.
- ULEEN (weightless, lookup-table network) 98.5% on MNIST with 262 KiB ([arXiv 2304.10618](https://arxiv.org/pdf/2304.10618)); no Fashion-MNIST figure found.

## 4. Reading of the failures together

1. Everything we tried is a single layer of binary features with a linear or counting readout. The literature puts that family at 88 to 90.5% and says so in independent work: **we are at the ceiling of the architecture, not failing at tuning it.**
2. The models above 91% change the **input encoding** (richer booleanisation, convolutional patches, soft coding) or add depth with gradients.
3. About 12% of the T-shirt/Shirt pair appears unrecoverable at 28 x 28 by any model tried; a fair target is closing the gap to the CNN (about 79% Shirt recall), not 100%.

## 5. Ideas that fit the evidence (in order), and status

1. **Richer, softer encoding** (k winners per spot, more detectors, multiple scales): in test now ([feat_grid.py](../hw/brain/experiments/month5/feat_grid.py)).
2. **Fuzzy-pattern / clause-style evidence** (patterns with graded matching, counted without gradients), after reading the FPTM paper properly: blocked on paper access.
3. **Gradient-trained hidden layer exported as tables** (accelerator path), only with a better trainer than straight-through free tables (needs the DWN paper's training method).
4. **Colour or higher resolution** where the application allows.
5. Dropped: HDC (below L), spoken-name second sense (label leakage), dense binary convolution (operation count).

Related: [Docs index](INDEX.md), [Clothing accuracy round](../hw/results/clothing_features_round.md), [Research report](research/matrix_free_vs_cnn_report.md), [Status report](status_report_24oct.md), [Journal](journal.md)
