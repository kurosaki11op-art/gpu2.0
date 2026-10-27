---
title: Cost frontier and the 2x ceiling
tags: [spark, results, energy, cost]
---

# Cost frontier and the 2x ceiling (27 Oct 2026)

Founder's concern: every fix raises memory and power. Rule adopted: every accuracy number carries its cost, compared on one consistent model, with a ceiling of about 2 times L's cost today, and judged against the best add-only baseline at the same accuracy (not only against a dense GPU network). Script `hw/brain/experiments/month5/cost_frontier.py` (log `cost_frontier.log`), combination test `clause_on_rich_eval.py` (log `clause_on_rich_eval.log`). Energies are ESTIMATED with the project's 45 nm constants (Horowitz 2014): front end 576 positions x 32 detectors x channels x 0.23 pJ; table = active bits x (SRAM word read for the table size, 20 pJ up to 32 KB rising to 100 pJ at 1 MB, plus 10 adds). Accuracies are SIMULATED, one seed.

| variant | accuracy | energy | x L | inside 2x ceiling |
|---|---|---|---|---|
| L as shipped (4 channels) | 88.85 | 29.9 nJ | 1.00 | yes |
| shipped + two-level output (levels 1, 4) | 89.45 | 36.3 nJ | 1.21 | yes |
| 7 channels | 89.48 | 50.9 nJ | 1.70 | yes |
| 7 channels, two-level (1, 3) | 89.73 | 67.9 nJ | 2.27 | no |
| 7 channels, two-level (1, 2) | 89.95 | 73.5 nJ | 2.46 | no |
| 10 channels | 89.82 | 73.3 nJ | 2.45 | no |
| L + clause layer (4,000), every image (measured) | 89.73 | 110.7 nJ | 3.70 | no |
| L + clause layer, routed to 30% of images | 89.71 | 53.7 nJ | 1.79 | yes |
| reference: add-only ternary network (256 hidden) | 89.40 | about 199 nJ | 6.6 | |
| reference: small float CNN | 91.28 | about 1,970 nJ | 65.7 | |
| reference: dense float network | 89.15 | 64,549 nJ | 2,156 | |

## Judgement

- **At the accuracy of the add-only ternary network (89.4) we use 36 nJ against about 199 nJ: 5.5 times less** (the fair, matrix-free comparison). Against the small float CNN at about 89.7 our best inside the ceiling (53.7 nJ) is about 37 times cheaper, but the CNN reaches 91.3 and we do not. Against a dense float network, about 1,200 to 1,800 times less. The ceiling therefore keeps us at 5 to 37 times below the matrix-free and small-CNN references; the 10 to 20 times target holds against the CNN and the dense network, and about 5 times against the best matrix-free baseline.
- **Inside the ceiling the best accuracy is 89.7** (clause layer routed to 30%: 89.71 at 1.79 times; shipped code with the two-level output: 89.45 at 1.21 times is the cheapest gain). The richer options (89.8 to 89.95) cost 2.3 to 2.5 times and are over the ceiling; they stay as measured upper points, not adopted.
- **The clause layer on the richer code (stopped)**: clauses over a 17,700-literal richer code were over budget by design (clause training and reads grow with literals), so the run was stopped after the first 30,000 images.

## Combination test: routed clause layer on the two-level code

The existing clause state fires unchanged (L's shipped code is exactly the level-1 bits of the two-level code, checked). Table on the two-level code (levels 1 and 4) plus the kept clause bits:

| | accuracy | cluster | Shirt recall | Shirt AP | clauses firing |
|---|---|---|---|---|---|
| two-level code alone | 89.45 | 81.6 | 0.613 | 0.772 | 0 |
| + 2,000 clauses, every image / routed 30% | 89.68 / 89.69 | 82.4 / 82.5 | 0.645 / 0.646 | 0.787 / 0.783 | 512 |
| + 4,000 clauses, every image / routed 30% | 89.70 / 89.73 | 82.4 / 82.4 | **0.677 / 0.676** | 0.791 / 0.787 | 1,046 |

- **The two gains overlap, they do not add**: the clause layer lifts the shipped code by +0.9 but the two-level code by only +0.25 (89.45 to 89.70), ending at the same 89.7 as the clause layer alone (89.71 at 1.79 times). The best Shirt recall so far (0.676, Shirt AP 0.787 to 0.791) comes from this combination, but its estimated cost (about 2.0 times with routing) is no better than clauses alone.
- **Conclusion: inside the 2x ceiling we are at about 89.7.** Further gains from more of the same (more channels, more levels, more clauses) cost more than they give; the remaining gap to the CNN (91.3) needs a different kind of change, or an efficiency gain that buys room (cheaper table, shared work, smaller codes) first.

## Correction: the CNN reference at int8 (27 Oct 2026)

The table above compared only against a float32 CNN. With the same constants the small CNN (32 shared 3 by 3 filters, about 248,768 multiply-adds per image) costs about **2,300 nJ in float32** (the 1,970 nJ in the table was a rougher count) and about **260 nJ at int8** (multiply-add 0.23 pJ, 53 KB of weights read once from SRAM, activations through small SRAM): 8.7 times L's 29.9 nJ. So the fair comparison for a CNN deployed on a GPU or accelerator at low precision is about 260 nJ at 91.3%. Against it our options inside the ceiling are about 5 to 7 times cheaper (54 nJ at 89.7% routed clauses; 36 nJ at 89.45%) but 1.5 to 1.9 points less accurate. The 10 to 20 times target holds against float networks (37 to 77 times against the float CNN), not against an int8 CNN (5 to 7 times), and the gap in accuracy to that CNN is the 1.3 to 1.6 points measured. A figure of about 69 nJ for the CNN is not supported by this model; 67.9 nJ is our own 7-channel two-level variant.

## Update (27 Oct 2026): routed second pass moves the frontier

The routed second pass with 64 informative detectors per channel (see [routed second pass](routed_second_pass.md)) reaches **90.0 to 90.35% at an estimated 40.6 nJ (1.36 times L)**, inside the 2 times ceiling and above every earlier inside-ceiling point (best before: 89.71 at 53.7 nJ). Against the int8 CNN (about 260 nJ, 91.28%) this is about 6 times cheaper at 0.9 to 1.3 points less accuracy; against the float CNN about 56 times cheaper.

Related: [Multi-threshold front end](multi_threshold_front_end.md), [Energy and tiles](best_version_energy_tiles.md), [Foundations study](foundations_study.md), [Results index](INDEX.md)
