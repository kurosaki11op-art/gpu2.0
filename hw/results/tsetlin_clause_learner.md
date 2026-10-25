---
title: A faithful Tsetlin-style clause learner on L's code (local feedback, no error passing)
tags: [l, tsetlin, clauses, local-learning, shirt]
---

# Tsetlin-style clause learner on L's 4,608-bit code (25 Oct 2026)

Script [tm_faithful.py](../brain/experiments/month5/tm_faithful.py), logs [sweep](../brain/experiments/month5/tm_faithful_sweep.log), [200 clauses](../brain/experiments/month5/tm_faithful_c200_s3.log), [400 clauses](../brain/experiments/month5/tm_faithful_c400_s3.log). SIMULATED, Fashion-MNIST, single view, one seed, trained on all 60,000 images, scored on the 10,000 test images.
A clause is an AND of included literals (a bit being on, or a bit being off); each class has C clauses, half voting for and half against; every literal has a counter (1 to 200, included above 100). Learning is local to each clause (Type I feedback reinforces literals that agree with the image when the clause fires and forgets with probability 1/s; Type II pushes false literals towards inclusion when a clause fires wrongly); the target class and one random other class are updated per image. No gradients, no multiplies, no matrices, no error passing between layers. This replaces my earlier clause learner (66%), which had no "bit is off" literals.

| Clauses per class | Specificity s | Epochs | Accuracy | Cluster | Shirt recall | Shirt AP | Included literals per clause |
|---|---|---|---|---|---|---|---|
| 100 | 8 | 6 | 74.6 | 64.6 | 0.43 | 0.48 | 61 |
| 100 | 4 (half epoch) | 0.5 | 79.8 | 68.3 | 0.41 | 0.49 | 24 |
| 100 | 2 (1.3 epochs) | 1.3 | 83.0 | 72.9 | 0.58 | 0.52 | 8 |
| 200 | 3 | 7 | 86.0 | 76.6 | 0.63 | 0.613 | 9 |
| 400 | 3 | 3.5 | 86.1 | 76.6 | 0.41 | 0.648 | 3.8 |
| (reference) L counting table | n/a | 1 | 88.6 | 80.8 | 0.658 | 0.741 | n/a |

## Reading
- **Local feedback learns this task**: 86% accuracy with clauses of only about 4 to 9 included bits each, no error passing and no multiplies. The earlier failure was my implementation (no negated literals), not the idea.
- **Lower specificity is the main setting** (s 15: 62%, s 8: 71 to 75%, s 4: 80%, s 3 to 2: 83 to 86%); more clauses raise Shirt AP (0.58 at 200 clauses, 0.648 at 400 at equal epochs).
- **Still below L's table** (88.6, AP 0.741) and still rising slowly with clauses and epochs; not yet tried: more clauses, clause weights, the convolutional form of the published method (CTM 88.25 to 90.65 at 250 to 8,000 clauses).
- Cost (ESTIMATED): inference tests each included literal of each clause: 4,000 clauses of about 4 literals is at most 16,000 single-bit tests (early exit cuts this), against about 590 table rows for L.

Related: [Results index](INDEX.md), [Boolean error transport](boolean_error_transport.md), [Tsetlin paper notes](../../docs/research/papers_notes/tsetlin_papers.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
