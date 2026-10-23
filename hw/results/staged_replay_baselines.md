---
title: Fair continual-learning baselines for the staged test (24 Oct 2026)
tags: [l, forgetting, baselines, results]
---

# Does L's staged-learning advantage survive replay and EWC? (MEASURED on CPU, torch, 3 seeds)

`hw/brain/experiments/month5/staged_replay.py`; logs `staged_replay_fashion.log`, `staged_replay_mnist.log`. Same protocol as the L Cortex staged test: five stages of two classes, 2,000 images per stage, accuracy on ALL classes after the last stage; MLP 784-256-128-10, 10 epochs per stage, mean of 3 seeds. Replay memory = stored 8-bit pixels (784 bytes per image).

| Method | Replay memory | Clothing % | Digits % |
|---|---|---|---|
| Fine-tuning | 0 | 19.9 | 19.2 |
| EWC (lambda 100 and 10,000) | Fisher + copy of weights | 19.9 | 19.4 / 19.3 |
| Replay 10 per class | 77 KB | 51.4 | 47.1 |
| Replay 50 per class | 383 KB | 68.9 | 81.2 |
| Replay 200 per class | 1,531 KB | 80.3 | 92.1 |
| Replay 1,000 per class | 7,656 KB | 85.3 | 96.0 |
| Joint training on the same data (upper reference) | all data | 84.4 | 94.9 |
| **L Cortex (earlier runs, stores no examples)** | deployed table 11 to 45 KB + learning state | **81.5** | **94.2** |

**Reading.**
- EWC does nothing in this class-incremental setting (about 20%), as the literature predicts; the "MLP and CNN end near 20%" statement holds only for no protection and EWC.
- **Replay is the fair opponent, and it beats L when given enough memory**: 200 stored examples per class (1.5 MB) already reaches 80.3 / 92.1, level with L, and 1,000 per class (7.7 MB) exceeds L and even the joint reference by a little.
- L's advantage is therefore **memory at equal accuracy**, not accuracy: L reaches 81.5 / 94.2 with a learning state of about 130 KB and a deployed table of 11 to 45 KB, while replay needs about 1.5 MB (clothing) for the same accuracy, roughly 10 times more, and L keeps no raw images (privacy, no buffer management). Against a small replay buffer (383 KB) L is far ahead (81.5 against 68.9 clothing).
- Caveats: the L runs and these runs used the same protocol but not the same script, seeds or code path; the MLP was not tuned; no other strong method (generative replay, distillation, iCaRL) was tried; the 130 KB learning-state figure is from the earlier memory study and counts the fast, dream and slow tables.

**Pitch consequence.** Claim "at equal accuracy L learns in stages with about one tenth of the memory of replay and with no stored examples", not "L does not forget while networks do".

Related: [Results index](INDEX.md), [Staged learning of a standard network](staged_mlp.md), [L deployed table size](l_deployed_memory.md), [Research report](../../docs/research/matrix_free_vs_cnn_report.md), [Journal](../../docs/journal.md)
