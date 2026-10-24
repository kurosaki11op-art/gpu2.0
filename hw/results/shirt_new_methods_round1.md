---
title: Shirt new methods, round 1 (flip augmentation, exemplar second opinion, sub-class tables)
tags: [l, shirt, clothing, methods, failures]
---

# New methods for Shirt, round 1 (24 Oct 2026)

Chosen from what the failures say: a single layer of binary features caps near 89 to 90; the rich 59,584-bit code gave only +1 (so the learner, not the code, is the lever); local nonlinear readouts are the cheap thing not yet tried. SIMULATED, Fashion-MNIST, single view, one seed (TENTATIVE at best). Scripts and logs: [setup](../brain/experiments/month5/shirt_new_methods_setup.py), [methods1](../brain/experiments/month5/shirt_new_methods1.py) ([log](../brain/experiments/month5/shirt_new_methods1.log)), [methods2](../brain/experiments/month5/shirt_new_methods2.py) ([log](../brain/experiments/month5/shirt_new_methods2.log)).

| Method | Accuracy | Cluster | Shirt recall | Shirt AP | Verdict |
|---|---|---|---|---|---|
| baseline L | 0.8885 | 0.806 | 0.638 | 0.753 | |
| M1 table trained with horizontally flipped copies | 0.8814 | 0.802 | 0.597 | 0.735 | worse |
| M2 test-time flip added (table not trained on flips) | 0.8110 | 0.812 | 0.638 | 0.734 | worse (detectors are not flip-symmetric) |
| M1+M2 | 0.8884 | 0.815 | 0.615 | 0.746 | no gain |
| M3 nearest exemplar (top-10 of 24,000 cluster images) alone, cluster | | 0.806 | | | level with the table |
| M3 table + exemplar vote, weight 1 | 0.8908 | 0.821 | 0.654 | 0.771 | +0.2 / +1.5 / +0.018, but needs 24,000 stored codes (about 14 MB) and the weight was picked on test |
| M3 weight 3 / 10 | 0.878 / 0.713 | 0.826 / 0.829 | 0.659 / 0.663 | 0.769 / 0.690 | accuracy collapses |
| M5 sub-class tables (K=3 styles per cluster class, max) | 0.8907 | 0.810 | 0.665 | 0.757 | within noise |

## Reading
- Augmentation by flipping fails because L's detectors are learned from unflipped images and are not mirror-symmetric; the table has to spend capacity on two code families (win-lose).
- A local nonlinear readout (exemplars) lifts the cluster by 1.5 points at best, with a memory cost about 1,000 times the table (win-lose), and its weight was chosen on the test set, so even that gain is unproven.
- Splitting classes into styles gives nothing: Shirt errors are not a multi-modal-class problem.
- Together with the earlier failures this says the missing piece is in the **features that separate the pair** (placket, collar, sleeve length at small scale), not in the readout of the current code.

Related: [Results index](INDEX.md), [Clothing accuracy round](clothing_features_round.md), [Prune-retrain](prune_retrain_second_layer.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
