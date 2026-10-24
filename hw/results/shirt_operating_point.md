---
title: Shirt recall is an operating-point effect (24 Oct 2026)
tags: [l, clothing, shirt, analysis, results]
---

# Where the Shirt errors go, and why L's Shirt recall looks 15 points behind a CNN's (MEASURED/SIMULATED, Fashion-MNIST, single view, one seed)

> **PARTIAL CORRECTION (24 Oct, `shirt_pr.py`, `shirt_pr.log`):** a stronger, better-trained CNN ranks Shirt better than L, so the gap is NOT only an operating-point effect. Shirt-versus-rest average precision: L 0.753, CNN (3 epochs, wider) 0.822, CNN (10 epochs + augmentation) 0.840; precision at 80% Shirt recall: L 0.56, CNN 0.65 / 0.70; four-class cluster accuracy: L 80.6, CNN 83.2 / 85.1; 2-way T-shirt vs Shirt: L 87.0, CNN 87.4 / 89.2. The "equal inside the cluster" statement below (79.0 against 79.2) used a smaller, 3-epoch CNN; the operating point explains part of the Shirt-recall difference, a real ranking gap of about 5 points of cluster accuracy and 0.09 of average precision remains.

`hw/brain/experiments/month5/shirt_row.py` (log `shirt_row.log`), `bias_calib2.py` (`bias_calib2.log`), `receptive_fields.py` (`receptive_fields.log`). Small CNN trained 3 epochs (ruler only, never in the chip) and the shipped L code; both at nearly equal overall accuracy (L 88.85%, CNN 89.09%).

**1. The 1,000 test Shirts are called:**

| Called | L | CNN |
|---|---|---|
| Shirt (recall) | 638 | **773** |
| T-shirt | 147 | 76 |
| Coat | 93 | 45 |
| Pullover | 86 | 64 |
| Dress | 22 | 30 |

**2. And the other classes called Shirt (per 1,000):** T-shirt 59 (L) against 147 (CNN); Pullover 68 against 72; Coat 86 against 136.

**3. Accuracy inside the four-class cluster {T-shirt, Pullover, Coat, Shirt}: L 79.0%, CNN 79.2%.**

**Reading.** At the same overall accuracy the CNN reaches a higher Shirt recall (77.3 against 63.8) only by calling Shirt more often: it mislabels 147 T-shirts and 136 Coats as Shirt, against 59 and 86 for L. Inside the cluster the two are equally good at separating the classes (79.0 against 79.2). **The Shirt "gap" is mostly where each model sets its decision boundary (class priors), not how well it separates Shirt from the others.** This corrects the earlier statement that L is 15 points behind a CNN on Shirt.

**4. Confirmed by moving L's own operating point** (per-class offsets, one integer add per class, learned on 10,000 held-out training images, table trained on the other 50,000):

| Offsets chosen to maximise | Accuracy | Shirt | T-shirt | Pullover | Coat |
|---|---|---|---|---|---|
| none | 88.61 | 65.8 | 83.2 | 83.5 | 82.9 |
| overall accuracy | 88.59 | 66.0 | 82.7 | 83.2 | 84.3 |
| mean class recall | 88.65 | 65.5 | 82.3 | 83.1 | 84.0 |
| **Shirt + T-shirt recall** | 85.02 | **84.0** | 84.2 | 63.2 | 54.7 |

The shipped table is already calibrated for overall accuracy (offsets change nothing). Raising Shirt recall to 84% costs 3.6 points overall and drops Pullover to 63% and Coat to 55%: a zero-sum trade inside the cluster, exactly the CNN's behaviour.

**5. Larger detector patches do not help:** patch 9 / step 2: 86.38% (Shirt 56.2); patch 13 / step 2: 84.04% (Shirt 48.7), both below the shipped 5 x 5 (88.85%).

**What this means:** (a) comparing L and a CNN by Shirt recall alone is misleading; compare precision and recall together (Shirt F1 about 0.69 for L and 0.72 for the CNN, rough) or per-class numbers at the same overall accuracy; (b) the remaining real gap is overall, about 1 to 2 points (L 88.9 to 90.4 with teams, CNN ruler 91.1) and the cluster is genuinely ambiguous at 28 x 28 for both; (c) L can offer a **tunable Shirt operating point** at the price of one add per class (for example 84% Shirt recall when missing a shirt matters more than a false alarm), which is a chip feature, not a fix of the discrimination.

**Limits.** One seed, a CNN trained only 3 epochs (the 6-epoch ruler is 91.1 overall), the F1 values are my arithmetic from the counts above (ESTIMATED), no 2-way (Shirt/T-shirt only) comparison with the CNN.

Related: [Results index](INDEX.md), [Failure analysis](../../docs/failure_analysis_clothing.md), [Clothing accuracy round](clothing_features_round.md), [Shirt specialist](shirt_specialist.md), [Journal](../../docs/journal.md)
