---
title: Local error correction and neurogenesis (write new, do not overwrite) in staged learning
tags: [l, accelerator, continual-learning, neurogenesis, forgetting]
---

# Local layers and neurogenesis against forgetting (25 Oct 2026)

Two user ideas, tested on the hard-gate integer learner ([boolean_error_transport](boolean_error_transport.md)): (1) each layer checks and fixes only its own errors, no error passed between layers (LOCAL); (2) neurogenesis: freeze old nodes, add new nodes for the new classes, write only into them (GROW). MNIST, class-incremental (classes 0-4, then 5-9, no stored images), 500 + 500 hidden and 1,000 output gates, 4 epochs per stage, one seed, SIMULATED. Script [bool_local_growth.py](../brain/experiments/month5/bool_local_growth.py), log [bool_local_growth.log](../brain/experiments/month5/bool_local_growth.log). DREAM = stage 2 also trains on old-class "dreams" (bits drawn from stored per-bit rates, 30% of each batch), as L does.

Accuracy after stage 2 among all 10 classes (old = classes 0-4, new = 5-9):

| Arm | Dreams | Old | New | All |
|---|---|---|---|---|
| end-to-end error, overwrite | no | 0.0 | 84.9 | 41.3 |
| local, overwrite | no | 0.0 | 76.3 | 37.1 |
| end-to-end, **grow** | no | 11.0 | 82.4 | 45.7 |
| local, grow | no | 3.5 | 80.5 | 41.0 |
| end-to-end, overwrite | yes | 56.4 | 79.2 | 67.5 |
| local, overwrite | yes | 34.4 | 76.4 | 54.8 |
| end-to-end, **grow** | yes | **64.5** | 78.3 | **71.2** |
| local, grow | yes | 49.9 | 78.2 | 63.6 |

## Reading
- Overwriting forgets everything without rehearsal (old 0.0): the user's diagnosis is confirmed.
- **Growing helps but does not solve it**: old classes are not damaged (frozen), yet without dreams old accuracy is only 11%. The old classes fail because the new class's nodes learn "fire" with no example of what not to fire on, so they fire on old images and win the vote. Writing new nodes removes overwriting, not competition.
- With dreams, growth gives 71.2 against 67.5 (+3.7, one seed, TENTATIVE).
- **Local-only error is worse than end-to-end here** (-8 to -15 points with dreams): each layer's own readout does not give hidden layers a useful goal. The local idea is not adopted.
- The literature in the project notes agrees: expansion and mask methods (DEN, Progressive, PackNet, HAT, SupSup) are task-incremental and need a task id; FlyModel works class-incrementally because its writes are associative (only the target class's weights change, nothing is pushed down for wrong classes; error-driven decreases let shared units be hijacked by the newest class).

Related: [Results index](INDEX.md), [Boolean error transport](boolean_error_transport.md), [Forgetting-free adaptation papers](../../docs/research/papers_notes/forgetting_free_adaptation_papers.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
