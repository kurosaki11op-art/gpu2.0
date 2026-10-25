---
title: Difference-learning ideas for Shirt (residual layer, split where confused, label-free contrastive gates)
tags: [l, shirt, clothing, methods, failures, self-supervised]
---

# Learning differences without labels: three ideas, all failed on Shirt (25 Oct 2026)

Premise (founder): the architecture has a weakness in telling similar things apart, which will repeat everywhere, so the design should learn which is which from the data without stored examples. Tested on L's 4,608-bit code, counting-table readout, SIMULATED, Fashion-MNIST, single view, one seed. Scripts and logs: [shirt_residual_split.py](../brain/experiments/month5/shirt_residual_split.py) ([log](../brain/experiments/month5/shirt_residual_split.log)), [bool_contrastive.py](../brain/experiments/month5/bool_contrastive.py) ([log](../brain/experiments/month5/bool_contrastive.log)). Success criterion set beforehand: Shirt AP at least 0.80 (L: 0.753) at no more than 1.5 times the active rows.

| Variant | Bits | Active rows | Accuracy | Cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|---|---|
| baseline L | 4,608 | 586 | 0.8885 | 0.806 | 0.638 | 0.753 |
| 1a residual layer only (what 64 prototypes do not explain, plus prototype id) | 9,280 | 434 | 0.8857 | 0.808 | 0.658 | 0.748 |
| 1b L code + prototype id | 4,672 | 587 | 0.8882 | 0.807 | 0.624 | 0.749 |
| 2a L code + features from splitting the ambiguous region (unsupervised) | 4,692 | 621 | 0.8889 | 0.809 | 0.630 | 0.739 |
| 2b control: same features from a random region | 4,692 | 623 | 0.8888 | 0.810 | 0.640 | 0.749 |
| 3a label-free contrastive gate features alone (5 epochs) | 3,000 | 960 | 0.7885 | 0.687 | 0.449 | 0.505 |
| 3b L code + label-free gate features | 7,608 | 1,546 | 0.8808 | 0.803 | 0.593 | 0.717 |

## Why they failed (what the numbers show)
- **Residual layer (1):** the residual plus the prototype id is just a re-coding of the same image, so it holds the same information (accuracy 0.8857, AP 0.748 against 0.753) and no more. The residuals are large (271 extra bits and 162 missing bits against 586 active), so the 64 unsupervised prototypes explain little of an image: what remains is mostly position jitter and thickness, not collars. Side finding: the residual code reaches the same accuracy with 26% fewer active rows (434 against 586) but needs a table twice as large; not a win-win.
- **Split where confused (2):** the split features add nothing over the random-region control (AP 0.739 against 0.749). The biggest unsupervised axis inside the ambiguous region is size, shape and brightness, not the class difference: unsupervised learning follows variance, and nothing tells it which differences matter.
- **Contrastive gates (3):** after 5 epochs the codes of two views of one image disagree in 13.9% of bits, but codes of different images in only 23.9% (0.5 would be fully spread), so the code is barely discriminative; features alone give 0.505 AP and hurt when added. This first version of the objective is under-trained and untuned, so it is not a verdict on label-free contrastive learning, only on this version.

## What all failures so far share
Information about *which differences matter* has to come from somewhere: labels (the table gets them, but the single-layer features cannot compose them), or invariances (what must not change: shifts, noise), which only the third idea uses and that version does not separate images enough. Unsupervised structure (Hebbian detectors, k-means prototypes, residuals, splits) follows the largest variation and carries neither signal.

Related: [Results index](INDEX.md), [Shirt new methods round 2](shirt_new_methods_round2.md), [Frozen-encoder tests](frozen_encoder_tests.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
