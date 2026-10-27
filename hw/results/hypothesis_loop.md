---
title: Hypothesis loop (propose, test, keep) on L's counting table
tags: [spark, results, thinking, hypothesis]
---

# Hypothesis loop: propose, test, keep (26 Oct 2026)

SIMULATED, Fashion-MNIST, one seed. Part 3 of the thinking plan (design from the research notes, adapted by us). Script `hw/brain/experiments/month5/hypothesis_loop.py`, logs `hypothesis_loop_bug_run.log`, `hypothesis_loop_v1_diag.log`, `hypothesis_loop_v2.log`, `hypothesis_loop_v3.log`.

Loop: Shirt is confused with T-shirt, Pullover and Coat. A contrast counter grows 2 to 4 literal clauses (bit on or off, over the 4,608 detector bits and 1,568 raw pixel bits) that fire on Shirt and not on the other class (only adding literals when a clause fires on the wrong class). Each candidate is tested on a held set of 20,000 images not used to propose it: Wilson lower bound of the Shirt firing rate minus the upper bound on the other class above 0.05, coverage at least 3%, and firing on at most 12% of all other classes (damage budget). Accepted clauses are added as bits to the table input; the batch is kept only if held-set Shirt recall rises by at least 0.01 and accuracy falls by at most 0.2 points, otherwise it is halved (undo). Control: random clauses with matching length and Shirt coverage through the same loop.

| version | what was proposed | passed the test | test set: accuracy / Shirt recall / AP |
|---|---|---|---|
| L alone | none | | 88.85 / 0.638 / 0.753 |
| 0 (bug) | only 6 candidates (candidate count shadowed by the class id) | 0 | not a result |
| 1 | 180 contrasts against the paired class | 0 (they fire on 48% of other classes) | unchanged |
| 2 | 180 contrasts against the paired class and all other classes | 5 | 88.72 / 0.626 / 0.752 (held set: Shirt recall +0.016, did not carry to test) |
| 3 | 180 clauses from L's own missed Shirts (the ones it assigns to the paired class) | 0 (they fire on the paired class 79% of the time against 51% on Shirt: margin negative) | unchanged |
| random control | | 3 after the undo | 88.74 / 0.618 / 0.747 |

- **No gain in any version.** The loop itself works (it proposes, rejects what breaks the damage budget, undoes a batch that does not help, and a random control passes less often), but the rules it finds do not raise Shirt recall on the test set.
- **Why, from our own diagnostics (not from papers):** the Shirts that L misses look like the class they are confused with: no 2 to 4 literal conjunction over these bits fires on them more than on the paired class (version 3: 79% on the paired class, 51% on missed Shirts). The information to separate them is not available in short conjunctions of this code, which agrees with the earlier finding that the picture-only Shirt ceiling is near.
- Held-set gains that vanish on the test set (version 2) show why the separate test matters.
- Not tried: longer conjunctions (more than 4 literals), a different feature level (clause bits instead of pixels), a second look with finer detectors on the confused region only.

### Version 4: longer clauses and a looser damage budget (27 Oct 2026, SIMULATED; `hypothesis_loop_v4.log`)

MAXLEN 8 literals, damage budget 20%. 94 of 180 candidates pass the held-set test; the batch of 94 hurts (held-set Shirt recall -0.035), halving reaches 11 clauses with held-set Shirt recall +0.032, but on the test set: accuracy 88.82, Shirt recall 0.627, AP 0.742, against L alone 88.85 / 0.638 / 0.753. The random-clause control (9 clauses) gives Shirt recall 0.658 on the test set, above the loop's own clauses, so the held-set gains here are within the noise of choosing among many candidates.

**Conclusion: part 3 closed as no gain in four versions.** Short and medium conjunctions over L's code and raw pixels do not separate the missed Shirts from the classes they are confused with; the loop mechanics (propose, held-set test, damage budget, undo) work, but the proposals carry no usable signal at this feature level. Reopen only with a different feature level (for example finer detectors on the confused region).

### Ceiling check: how much could any proposer find? (27 Oct 2026, SIMULATED; `part3_ceiling.py`)

Trained only on the four confusable classes (T-shirt, Pullover, Coat, Shirt) and scored on the same four classes of the test set (reference networks are a GPU-style baseline, not our chip):

| model | 4-way accuracy | Shirt recall |
|---|---|---|
| L's counting table (4 classes only) | 81.1 | 0.687 |
| one-hidden-layer network (256 units) on raw pixels | 81.1 | 0.702 |
| one-hidden-layer network on L's code bits | 83.5 | 0.739 |

- Even a dense specialist trained only on the confusable group gets Shirt recall 0.70 to 0.74 against 0.687 for L's table, so on this input the whole headroom is about +0.02 to +0.05 Shirt recall (and +2.4 points of four-way accuracy at most). The loop's target (Shirt recall of at least 0.67 from 0.638) was already at the level of L's own 4-class table; four versions found nothing because there is almost nothing left for short rules to find, not because the loop is faulty.
- The short-rule loop does not recover the gap (see the specialist below, which does).

### Fix: a clause specialist for the confusable group, used as extra table inputs (27 Oct 2026, SIMULATED; `part3_specialist.py`, logs `part3_specialist_*.log`)

The failure of the loop was its proposer (short conjunctions), not the idea of a second, stronger look at the group. The hypothesis "these four classes need their own look" is now built from our own primitives: a Tsetlin-style clause specialist trained ONLY on T-shirt, Pullover, Coat and Shirt (24,000 images, over L's code plus raw pixel bits, 400 clauses per class, 3 epochs, no matrix, no backprop), whose firing bits are added to L's counting table input (the recipe that worked for the all-class clause layer). Used on its own, as a classifier or as a hard replacement inside the group, the specialist is poor and unstable (4-way 67 to 77% against 80.6 for L's table; its raw class sums swing) so it is only used as table input.

| system (Fashion-MNIST test) | accuracy | Shirt recall | cluster accuracy | Shirt AP | clauses firing per image |
|---|---|---|---|---|---|
| L alone | 88.85 | 0.638 | 80.6 | 0.753 | 0 |
| L + 1,600 specialist clauses, run 1 / 2 / 3 (seed 0 twice, seed 1) | 89.35 / 89.24 / 89.35 | 0.654 / 0.666 / 0.658 | 81.7 / 81.6 / 81.8 | 0.786 / 0.782 / 0.779 | 203 / 208 / 202 |
| L + 3,200 specialist clauses (800 per class) | 89.37 | 0.650 | 81.6 | 0.780 | 415 |
| routed: specialist evaluated only on the 40% of images L assigns to the group, two runs | 89.22 / 89.50 | 0.638 / 0.637 | 81.5 / 81.9 | 0.777 / 0.777 | 86 |
| for comparison: L + best 4,000 all-class clauses (two seeds) | 89.73 / 89.76 | 0.649 / 0.667 | 82.1 / 82.4 | 0.780 / 0.786 | 1,035 |

- **A win on efficiency and on the Shirt target.** With 1,600 clauses (and 24,000 training images) the specialist reaches the Shirt AP and recall of the full 4,000-clause layer (AP 0.779 to 0.786 against 0.780 to 0.786, recall 0.654 to 0.666 against 0.649 to 0.667) while only about 205 clauses fire per image instead of 1,035 (5 times fewer) and it needs 2.5 times fewer clauses. Against L alone: +0.4 to +0.5 accuracy, +0.016 to +0.028 Shirt recall, +1.0 cluster accuracy, +0.03 Shirt AP, on all three runs. Overall accuracy stays 0.4 below the all-class layer (89.3 against 89.75).
- The original success criterion (Shirt recall at least 0.67 with accuracy down by at most 0.2) is reached in one of three runs (0.666, accuracy up): partly met. The dense network ceiling from `part3_ceiling.py` (Shirt recall 0.74 in 4-way, trained on the group) is not reached.
- Doubling the clauses does not help (800 per class: no better), so the cheap version is the right size. Routing to the images L assigns to the group (86 firing clauses per image) keeps accuracy and AP (+0.4 to +0.65, AP 0.777) but loses the Shirt recall gain (0.638).
- Caveats: three runs, two seeds, spread about 0.01 in recall; the specialist's group is chosen by hand (the confusable classes found earlier by the chip's own confusion counts could choose it: not done); the memory of 1,600 clauses is small (about 1,600 times a few literals).

Related: [Append-only clause banks](append_only_clause_staged.md), [Shirt difference-learning ideas](shirt_difference_layers.md), [Results index](INDEX.md)
