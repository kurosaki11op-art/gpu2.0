---
title: Connected structure (the DNA idea) as a counted generative classifier
tags: [l, connected-structure, generative, continual-learning, shirt]
---

# Connected structure: every bit judged by its neighbours (25 Oct 2026)

Founder's idea: DNA is a connected structure of parts, not a bag. Test: for each class keep counted tables P(bit | neighbouring bits) at every position of the two-threshold pixel bits (1,568 bits); an image is scored by the log-likelihood of all its bits under each class's connected model (table lookups and adds, no backprop, no stored images, no matrices). SIMULATED, Fashion-MNIST, single view, one seed, trained on 50,000 images. Scripts and logs: [connected_model.py](../brain/experiments/month5/connected_model.py) ([log](../brain/experiments/month5/connected_model.log)), [connected_model2.py](../brain/experiments/month5/connected_model2.py) ([log](../brain/experiments/month5/connected_model2.log)). The mixing weight with L's table is chosen on a validation split of the training images, never on test.

| Model | Neighbour bits per bit | Table entries per class | Accuracy | Cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|---|---|
| independent bits | 0 | 1,568 | 0.6747 | 0.542 | 0.241 | 0.260 |
| connected | 3 | 12,544 | 0.7902 | 0.691 | 0.487 | 0.519 |
| connected | 5 | 50,176 | 0.8222 | 0.713 | 0.526 | 0.552 |
| connected | 7 | 200,704 | 0.8311 | 0.721 | 0.550 | 0.578 |
| connected | 9 | 802,816 | 0.8361 | 0.727 | 0.559 | 0.599 |
| L counting table (50,000 images) | n/a | n/a | 0.8861 | 0.808 | 0.658 | 0.741 |
| L table + connected (9 bits), weight 1.5 | | | 0.8908 | 0.813 | 0.671 | 0.747 |

## Reading
- **Connection carries real information**: tying each bit to three neighbours lifts the same counted model from 67.5 to 79.0 accuracy and Shirt AP from 0.26 to 0.52; every added neighbour set helps (82.2, 83.1, 83.6), with diminishing steps. No learned features, no backprop.
- **It is continual by construction**: each class has its own tables and classes are compared by likelihood, so adding a class writes only its own tables, old classes cannot be overwritten, and there is no competition problem (no negatives needed). This is the generative-classifier route the papers found strongest for class-incremental learning without stored examples (FlyModel, generative classifiers). Staged accuracy therefore equals joint accuracy by construction (not run separately).
- **Not better than L alone**: 83.6 (9 neighbour bits) against 88.6, Shirt AP 0.60 against 0.74; added to L's table it gives +0.5 accuracy and +0.006 AP (validation-chosen weight), within what one seed can resolve.
- **Cost**: table size grows as 2 to the power of the neighbour count (0.8 million entries per class at 9 bits, about 8 million for ten classes), against L's 11 KB table; it needs hashing or pruning to be practical.
- Not tested: the same connected structure over L's learned detector bits and across scales (rather than raw pixels), which should carry more per connection.

Related: [Results index](INDEX.md), [Lessons from the failures](../../docs/lessons_from_failures_25oct.md), [Frozen-encoder tests](frozen_encoder_tests.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
