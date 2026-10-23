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

**Limits.** One seed, one data set; 0.7 points overall is within what seeds can move; the specialist is not yet in the RTL.

Related: [Results index](INDEX.md), [Where L loses on clothing](clothing_confusion.md), [Journal](../../docs/journal.md)
