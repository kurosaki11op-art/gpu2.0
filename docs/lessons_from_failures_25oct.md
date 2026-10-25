---
title: What the failures taught us (25 Oct 2026)
tags: [l, lessons, design, continual-learning]
---

# What the failures taught us, and the design they point to (25 Oct 2026)

Evidence behind each lesson is in the linked result notes; all numbers SIMULATED, mostly one seed.

| # | Lesson | Evidence |
|---|---|---|
| 1 | A learner needs a signal for **which differences matter**. Unsupervised structure (Hebbian detectors, k-means prototypes, residuals, splits) follows the largest variation, not the class difference. Relevance comes from labels or from invariances (what must not change). | [difference layers](../hw/results/shirt_difference_layers.md): residual AP 0.748, split 0.739 against a random-region control 0.749 |
| 2 | Local single-layer features cannot compose a hard distinction, so depth is needed; width saturates. | 64 to 128 detectors no gain; one extra layer +0.03 to +0.07 AP; float second layer 0.811 |
| 3 | The learning rule is no longer the blocker: an integer rule (graded error, one batch scale, sign-step counters, large batches, wide counter range) matches float backprop on a small gate network. | [error transport](../hw/results/boolean_error_transport.md): 79 to 80 against 81 to 82 (hard gates), 82.2 / 81.1 / 81.4 (soft forward) |
| 4 | Randomly wired two-input gates read a 4,608-bit code poorly; structure (weight sharing, locality) is what the published gate networks add. | gate network on L's code 78.8 against 88.9 |
| 5 | Forgetting has **two causes** needing two fixes: overwriting shared weights (freeze or grow) and competition (new units fire on old inputs; one-vs-rest units need negatives). | old classes 0.0% when overwriting; 11% with growth but no negatives; [staged growth](../hw/results/local_growth_staged.md) |
| 6 | Negatives for old classes must be made at the **feature level**, and the level of replay is also the level where plasticity stops. | feature dreams keep old 72.9 but new only 54; [frozen-encoder tests](../hw/results/frozen_encoder_tests.md) |
| 7 | Old-versus-new detection improves with closed-set accuracy (AUROC 0.78 to 0.82 for 89 to 92%); papers reach 0.99 with a 99% classifier. | [frozen-encoder tests](../hw/results/frozen_encoder_tests.md); [papers](research/exemplar_free_synthesis.md) |
| 8 | A frozen encoder needs **diverse** training; it was supervised on 5 classes only in our tests, and every paper uses half the classes or a pre-trained model. Diversity does not need labels. | [synthesis](research/exemplar_free_synthesis.md): cold-start losses of 15 to 23 points even for the best method |
| 9 | Process: criteria set before a run, a control per idea, a second seed before a claim. The random-region control showed idea 2 was null; withdrawn claims came from skipping this. | [claims ledger](claims_ledger.md) |

## Design these lessons point to (hypothesis, untested as a whole)
Two brains with sleep, now stated precisely:
- **Childhood (label-free):** lower gate layers learn from diverse unlabelled images by invariance plus spread (lesson 1, 8), then freeze.
- **Upper layers plastic:** learn new classes online by the integer rule (lesson 3), grown by new nodes (lesson 5), with feature-level dreams of old classes made from counted statistics (lesson 6).
- **Fast brain:** L's counting table for one-shot and few-shot classes, and as the old-versus-new gate when the upper classifier is strong (lesson 7).

Next test: label-free childhood on all-class unlabelled images (the contrastive learner, retuned to spread codes), freeze, then the staged 0-4 then 5-9 protocol with feature dreams, against the supervised-frozen result (old 72.9, new 54, all 63.6 to 65.3).

Related: [Docs index](INDEX.md), [Claims ledger](claims_ledger.md), [Synthesis of 25 papers](research/exemplar_free_synthesis.md), [Journal](journal.md)
