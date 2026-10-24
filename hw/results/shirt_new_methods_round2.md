---
title: Shirt new methods, round 2 (pair detectors, thin-structure cues)
tags: [l, shirt, clothing, methods, failures]
---

# New methods for Shirt, round 2 (24 Oct 2026)

Run by the user on their PC (full data, one seed, SIMULATED). Script: [shirt_pair_features.py](../brain/experiments/month5/shirt_pair_features.py); log: [shirt_pair_features.log](../brain/experiments/month5/shirt_pair_features.log). Success criteria set beforehand: Shirt AP +0.03 or more, accuracy not lower, active rows at most 1.5 times the baseline (about 880).

| Variant | Bits | Active rows | Accuracy | Cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|---|---|
| baseline L | 4,608 | 586 | 0.8885 | 0.806 | 0.638 | 0.753 |
| + detectors learned from the four confusable classes (pool 4) | 9,216 | 1,192 | 0.8924 | 0.818 | 0.621 | 0.762 |
| + the same, pool 2, 16 per channel | 13,824 | 1,451 | 0.8923 | 0.814 | 0.611 | 0.771 |
| + thin-structure cues (lines, silhouette width) | 5,203 | 845 | 0.8876 | 0.807 | 0.606 | 0.746 |

## Reading
- **Both ideas fail the criteria.** Pair detectors give +0.009 and +0.018 AP at 2.0 and 2.5 times the active rows; the cues give no gain (AP -0.007, accuracy -0.1) at 1.4 times the rows.
- The +0.4 accuracy of the pair detectors is about what simply doubling the number of generic detectors gave earlier (64 per channel: 89.89), so the pair targeting adds almost nothing beyond more bits.
- Shirt recall falls in every variant: the extra bits help ranking slightly but not the decision.
- Lesson: the Shirt/T-shirt information is not missing as a small-scale local pattern that these detectors and cues can see; adding bits of that kind buys the same small gain as any other bits. Combined with round 1 and the dense-layer result, the remaining gap needs features built from combinations across the image (depth), which costs energy, or label-free information from another sense.

Related: [Results index](INDEX.md), [Round 1](shirt_new_methods_round1.md), [Clothing accuracy round](clothing_features_round.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
