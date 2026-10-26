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

Related: [Append-only clause banks](append_only_clause_staged.md), [Shirt difference-learning ideas](shirt_difference_layers.md), [Results index](INDEX.md)
