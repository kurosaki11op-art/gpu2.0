---
title: Staged learning of a standard network (23 Oct 2026)
tags: [l, forgetting, results]
---

# Does the compressed standard network forget in stages like L Cortex does not? (SIMULATED, numpy)

`hw/brain/experiments/month5/staged_mlp.py` (logs `staged_mlp_fashion.log`, `staged_mlp_mnist.log`): the same staged protocol as the earlier CNN test (5 stages, 2 classes each, accuracy on ALL classes after each stage), with the 784-256-128-10 MLP in float32 and in 4-bit weights.

| Data | Network | After stage 1..5 (all classes) |
|---|---|---|
| Clothing | float32 MLP | 19.4, 19.1, 19.9, 19.9, 19.9 % |
| Clothing | 4-bit MLP | 19.4, 19.1, 19.9, 19.9, 19.9 % |
| Digits | float32 MLP | 21.1, 19.4, 18.2, 19.6, 18.4 % |
| Digits | 4-bit MLP | 21.1, 19.5, 18.2, 19.6, 18.7 % |
| Both | L Cortex (2,000 images per stage) | digits 94.2 %, clothing 81.5 % |

**Reading.** Shrinking to 4 bits does not change forgetting: the standard network, compressed or not, ends near 20 % (it only knows the last two classes), while L Cortex keeps 81.5 to 94.2 %. This is the fair counterpart to [Shrinking a standard network](compress_mlp.md): the compressed MLP wins at equal memory when all data is available at once, L Cortex wins when data arrives in stages.

**Limits.** No replay, no regularisation (those would reduce forgetting at extra cost); one seed; small network.

Related: [Results index](INDEX.md), [Shrinking a standard network](compress_mlp.md), [Journal](../../docs/journal.md)
