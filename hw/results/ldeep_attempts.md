---
title: L-Deep attempts - weight-shared gate trees (25 Oct 2026)
tags: [l, l-deep, gate-network, shirt, failures]
---

# L-Deep: weight-shared gate trees as a front end for L Cortex (25 Oct 2026)

Goal (founder): a deeper learned front end for the same counting table, no matrices, no multiplies, no multiply-accumulate. SIMULATED, Fashion-MNIST, one seed. Scripts and logs: [bool_conv.py](../brain/experiments/month5/bool_conv.py) ([v1](../brain/experiments/month5/bool_conv_v1.log), [v2](../brain/experiments/month5/bool_conv_v2.log), [v3](../brain/experiments/month5/bool_conv_v3.log), [v4](../brain/experiments/month5/bool_conv_v4.log)), [conv_select.py](../brain/experiments/month5/conv_select.py) (logs: [sparse step 2](../brain/experiments/month5/conv_select_sparse_step2.log)).

## v1: trees learned by integer error passing (failed)
16 filters; each a tree of 7 two-input gates over a 5x5 window of the two threshold planes, shared over all 24x24 positions, OR pooling over 4x4 blocks, then two flat gate layers, integer margin error.
| Run | What was tried | Result |
|---|---|---|
| v1 | train everything | collapse to one class (chance) |
| frozen-tree check | random trees held fixed | pipeline learns (64% at 400 steps): the tree updates cause the collapse |
| v2 | upper layers first, trees later, every 5th step, dead zone | 64% then chance as soon as trees learn (root bits firing 23% to 52%) |
| v3 | OR-pool error routed to one random non-firing position (balanced) | still collapses at the moment trees start learning (root bits 66%) |
| v4 | probabilistic counter steps (move with probability equal to how one-sided the evidence is) | trees barely change (firing 27%) yet accuracy still falls 60% to chance |
Diagnosis (hypothesis, consistent with all four): the flat layers above read exact bits; any change to a shared tree changes every position of a filter at once, and the hard-gate layers cannot track it. Error passing through shared trees is not stable in this form.

## v2: trees chosen by counted information (works, does not beat L)
Random trees (random wiring and gates) are applied, each scored by the mutual information of its 36 pooled bits with the class, the best are kept; no gradient. The information spread is large (best 8.2 nats, median 0.48), so selection matters.
| Features read by L's counting table (30,000 training images) | Bits | Active rows | Accuracy | Cluster | Shirt AP |
|---|---|---|---|---|---|
| 64 best trees (dense: 60% of bits fire) | 2,304 | 1,399 | 80.6 | 67.5 | 0.497 |
| 64 trees + L's code | 6,912 | | 87.1 | 78.4 | 0.675 |
| 128 best sparse trees (under 30% firing, from 1,024) | 4,608 | 446 | 84.3 | 74.2 | 0.598 |
| 128 sparse trees + L's code | 9,216 | | 88.2 | 80.1 | 0.723 |
| L's code alone (reference, same images) | 4,608 | 586 | 88.5 | 80.9 | 0.733 |

## Reading
- Selected sparse trees give 84.3% with fewer active rows than L (446 against 586) and no gradient or error passing, but stay 4 points below L's own detectors and add nothing on top of them. Dense OR-pooled trees hurt.
- **L-Deep has not met its criteria** (accuracy at least 88.6, Shirt AP at least 0.78). Failures recorded: error-passing trees (unstable), random-selected trees (84%).
- Not tried: a second tree layer over the pooled maps (depth), AND-type pooling, information-per-active-bit with redundancy removal, trees seeded from L's Hebbian detectors.

Related: [Results index](INDEX.md), [Boolean error transport](boolean_error_transport.md), [L-Genome design](../../docs/L_genome_design.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
