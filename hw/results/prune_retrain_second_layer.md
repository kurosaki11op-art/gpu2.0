---
title: Prune-then-retrain second layer (accuracy per byte read)
tags: [l, second-layer, shirt, energy]
---

# Second layer on L's code, pruned and retrained (24 Oct 2026)

Criterion set beforehand: at least +1 accuracy, +2 cluster, and at most about 3 to 4 times L's bytes read. SIMULATED, Fashion-MNIST, single view, one seed. Script and log: [decision_test4.py](../brain/experiments/month5/decision_test4.py), [decision_test_prune_retrain.log](../brain/experiments/month5/decision_test_prune_retrain.log). L's reference on the same code: accuracy about 0.880 to 0.891, cluster 0.806, Shirt AP 0.716 to 0.757.

| Hidden layer (1,024 binary units) | Accuracy | Cluster | Shirt recall | Shirt AP | Memory | Adds per image |
|---|---|---|---|---|---|---|
| dense, float (upper bound) | 0.9040 | 0.835 | 0.704 | 0.811 | n/a | dense |
| pruned fan-in 64, 4-bit | 0.8779 | 0.798 | 0.692 | 0.728 | 42 KB | about 8,400 |
| pruned fan-in 128, 4-bit | 0.8851 | 0.816 | 0.681 | 0.765 | 74 KB | about 16,700 |
| pruned fan-in 256, 4-bit | 0.8938 | 0.823 | 0.687 | 0.782 | 138 KB | about 33,500 |

## Reading
- **Fails the criterion.** L reads about 590 active rows per image; the pruned layer needs 8,400 to 33,500 adds, i.e. roughly 14 to 55 times more. Only at 33,500 adds does it beat L clearly (+0.5 to +1.3 accuracy, +1.7 cluster, Shirt AP +0.03 to +0.07), so this is again a win-lose trade (accuracy for energy).
- At the affordable end (fan-in 64) it is worse than L on accuracy and cluster.
- Even the dense float upper bound (AP 0.811) stays under the strong CNN (0.84): one extra layer on this fixed code does not close the Shirt gap.
- Cause of the cost: the hidden units read the code densely; the gain comes from many weighted connections, which is what the byte count measures.

Related: [Results index](INDEX.md), [Claims ledger](../../docs/claims_ledger.md), [Knockout screen](knockout_screen.md), [Journal](../../docs/journal.md)
