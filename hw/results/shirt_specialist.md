---
title: Specialist for the confusable upper-body classes (24 Oct 2026)
tags: [l, clothing, limits, results]
---

# Can a second look at finer detail separate Shirt from T-shirt? (SIMULATED, one seed)

`hw/brain/experiments/month5/shirt_specialist.py`, logs `shirt_specialist_part1.log` and `shirt_specialist_fine.log`. The main model (slow-table integer model, look-again, 88.92% overall) decides first; when its answer is T-shirt, Pullover, Coat or Shirt, a specialist trained only on those four classes decides among them. "Within group" = 4-way accuracy on test images whose true class is one of the four.

| Specialist code | Code bits | Within group | Overall |
|---|---|---|---|
| main model restricted to the four | 4,608 | 80.77 | 88.92 |
| same code, group-only training | 4,608 | 80.90 | 88.95 |
| detectors fitted on the group, same size | 4,608 | 80.90 | 88.99 |
| **finer detectors fitted on the group (32 detectors, pooled by 2)** | **18,432** | **82.50** | **89.64** |

**Reading.**
- A second decision with the same kind of code gains nothing: the limit is the features, not the decision.
- Finer detail helps but only a little: +1.7 points within the group, +0.7 overall, for a four times larger code on the group. The four classes are still only about 82% separable, so **Shirt against T-shirt remains the weak spot**; this does not make the model "always clear" on them.
- The cost is real: 18,432 bits means four times the table rows for these four classes, plus a second encoder pass.

**Not tried.** Pooling by 1 (full resolution), larger patches (the run with 7 x 7 patches and 64 detectors ran out of memory), shoulder and neck region only, edge/shape cells, and a multi-seed repeat. A different kind of evidence (outline, sleeve length) is the likely next step.

## Round 2: hand-made shape cues, and a CNN ruler (24 Oct 2026)

`shirt_shape.py` (log `shirt_shape.log`): bits that look like what a person uses to tell the garments apart, all compare/count only, appended to the group specialist's code (silhouette width per row, left and right edge per row, column height, dark pixels inside the silhouette = placket/collar, the neck and shoulder rows at full resolution, edges).

| Extra cues | Extra bits | Within group | Shirt recall | T-shirt recall | Overall |
|---|---|---|---|---|---|
| none (control) | 0 | 81.13 | 68.7 | 85.6 | 89.05 |
| silhouette profile | 784 | 81.00 | 68.1 | 86.5 | 89.03 |
| dark pixels inside | 168 | 81.20 | 70.4 | 85.3 | 89.07 |
| neck and shoulder rows, full resolution | 560 | 80.93 | 70.3 | 87.3 | 88.92 |
| edges | 392 | 80.73 | 67.4 | 86.0 | 88.93 |
| profile + inside | 952 | 81.75 | 70.9 | 86.4 | 89.32 |
| profile + inside + top | 1,512 | 81.50 | 74.3 | 85.4 | 89.18 |
| all four | 1,904 | 81.55 | 70.5 | 87.2 | 89.19 |

**Failure recorded:** none of the hand-made cues helps beyond about +0.6 within the group (+0.3 overall), which is inside seed noise. The best Shirt recall (74.3%) came with a lower T-shirt recall.

**The ruler.** `shirt_cnn_ruler.py` / `shirt_cnn_ruler.log` (MEASURED, torch on CPU, a small CNN trained with backprop on all 60,000 images, 6 epochs, one seed): overall 91.1%, **Shirt recall 79.4%**, T-shirt 84.2%, 83 of 1,000 shirts called T-shirt, 122 of 1,000 T-shirts called Shirt. So even a CNN with backprop and all data does not separate these two cleanly at 28 x 28 pixels: **a large part of this confusion is in the data (tiny pictures, ambiguous labels), not only in L.** L's Shirt recall is 63 to 74% (about 5 to 15 points below the CNN); L's T-shirt recall 85 to 87% is level with it.

**What this means for the goal "never confused":** that is not reachable on this data set by any model tried here. The honest target is to close the gap to the CNN on Shirt (about 10 points), not to reach 100%. A cleaner answer needs more evidence than a 28 x 28 grey picture (colour, higher resolution, or the second sense: a name from sound or text, already studied as the simulated ear in the memory file).

**Limits.** One seed, one data set; 0.7 points overall is within what seeds can move; the specialist is not yet in the RTL.

## Round 3: a pair-only specialist (24 Oct, SIMULATED, one seed)

`pair_test.py`, `pair_test.log`: a model that sees only T-shirt and Shirt (6,000 images each), accuracy among test images of those two classes (50% by always answering T-shirt):

| Model | 2-way accuracy | Shirt recall | T-shirt recall |
|---|---|---|---|
| Main model restricted to the pair | 86.95 | 83.1 | 90.8 |
| Pair specialist, detector code | 87.50 | 88.0 | 87.0 |
| + HOG-style bits | 88.25 | 87.7 | 88.8 |
| + 20,000 counted pairwise ANDs | 88.05 | 88.4 | 87.7 |

Even with only the two classes in play and all the extra features, the best 2-way accuracy is about 88%, a floor for these features. (An earlier version of this note blamed label overlap; the papers do not support that: whole-test-set irreducible error is about 3 to 4%, so the gap is mostly features. How much of the Shirt/T-shirt error is label overlap is not measured.) Real colour photos separate the pair better ([shirt_real_photos.md](shirt_real_photos.md)).

Related: [Results index](INDEX.md), [Where L loses on clothing](clothing_confusion.md), [Journal](../../docs/journal.md)
