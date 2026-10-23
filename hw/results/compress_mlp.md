---
title: Shrinking a standard network without losing accuracy (23 Oct 2026)
tags: [l, memory, compression, results]
---

# How far can an existing kind of model be shrunk, and how does it compare with L Cortex? (SIMULATED, numpy)

`hw/brain/experiments/month5/compress_mlp.py` (log `compress_mlp.log`): a standard 784-256-128-10 MLP (ReLU, Adam, 12 epochs) on Fashion-MNIST: 234,752 weights, **917 KB** in 32-bit, test accuracy **88.92%** (89.60% with the same 2 extra epochs, the fair baseline for the fine-tuned rows). Weights shrunk after training (per-row scale), then a 2-epoch quantisation-aware fine-tune; pruning is post-training only (no retraining).

| Shrink | Storage | After shrinking | After 2-epoch fine-tune | Fine-tuned change vs float + 2 epochs |
|---|---|---|---|---|
| 8-bit weights | 229 KB | 88.88 | 89.51 | -0.09 |
| 5-bit weights | 143 KB | 88.80 | 89.61 | +0.01 |
| **4-bit weights** | **115 KB** (entropy limit 85 KB) | 88.07 | **89.52** | **-0.08** |
| 3-bit weights | 86 KB (entropy limit 52 KB) | 86.49 | 89.17 | -0.43 |
| 2-bit weights | 57 KB | 31.53 | 85.34 | -4.26 |
| prune 50% (post-training) | 272 KB | 87.14 | - | -1.78 |
| prune 70% (post-training) | 163 KB | 78.44 | - | -10.48 |

**Reading.**
- **Existing models can be shrunk 8 times (917 to 115 KB, 4-bit) with no measurable accuracy loss** (-0.08, within noise) when a short quantisation-aware fine-tune follows; 3 bits costs about 0.4 point; 2 bits breaks. Post-training pruning without retraining is poor (it needs fine-tuning, not tested here). The 1.7 times lossless-coding limit of L's tables is similar in spirit: the entropy limit of the 4-bit network is about 85 KB.
- **The honest comparison: at the same memory the standard network is more accurate on clothing.** L Cortex tables are 129 KB for 85.7% (all at once); the 4-bit MLP is 115 KB for 89.5%, the 3-bit MLP 86 KB for 89.2%. So L's case is not accuracy per kilobyte on a fixed task; it is learning in stages without forgetting (a network forgets: 19.6% on digits in stages, measured on the GPU), learning in place, no multiplier and no gradients, and energy per example. A fair next test is the staged protocol for the compressed network.
- **Consequence for the plan:** the route of "alter an existing model to fit on chip" is realistic at 4 bits (8 times smaller), and the rest of the memory wall must come from a denser memory and several chips.

**Limits.** One small network, one dataset, numpy training (12 epochs), one seed, per-row scales, no activation quantisation, no real compute cost counted; large language models behave differently (published results suggest 4-bit is near lossless at billions of parameters, verify).

Related: [Results index](INDEX.md), [Bits against accuracy](bits_vs_accuracy.md), [Lossless table storage](table_storage_lossless.md), [Journal](../../docs/journal.md)
