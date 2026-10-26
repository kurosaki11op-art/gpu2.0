---
title: Counted-mixture dreams with teacher labels in staged learning
tags: [spark, results, continual, dreams]
---

# Counted-mixture dreams with teacher labels (26 Oct 2026)

SIMULATED, Fashion-MNIST, 6 old + 4 new classes, unfrozen rehearsal as in [the staged note](append_only_clause_staged.md), 150,000 steps, one share-rule offset per run (label-free). Part 1 of the thinking plan. Script `hw/brain/experiments/month5/staged_mixture.py`, logs `staged_mixture_*.log`. The earlier dreams (independent bits, tree, clause-forced) all failed; the research notes pointed to a mixture level and teacher labels, which we built our own way:

- **Counted sub-prototypes.** Each old class keeps K clusters of its stage-1 data, each stored only as one frequency per bit (counters, no images). A dream picks a cluster (by size) then draws every bit from that cluster's frequencies: a mixture of products, so bits that go together inside a cluster stay together.
- **Teacher label and boundary filter.** The frozen stage-1 banks score each dream; the dream's label is the teacher's answer, not the generating class, and only dreams near the teacher's boundary (margin below the median) are kept (about half of the 18,000 generated).
- Old-class rehearsal draws come from these dreams with probability PD, otherwise from the stored images (recombined as before).

| run | seed 0: all / old / new / Shirt (offset) | seed 1: all / old / new / Shirt (offset) |
|---|---|---|
| 20 stored images, no dreams (baseline) | 84.2 / 83.8 / 84.8 / 0.58 (+35) | 83.8 / 84.7 / 82.5 / 0.49 (+30) |
| 20 stored + dreams, K=8, PD 0.5 | 84.9 / 85.2 / 84.5 / 0.51 (+0) | 84.3 / 89.3 / 76.7 / 0.20 (+0) |
| 20 stored + dreams, K=32, PD 0.5 | 85.1 / 85.2 / 85.0 / 0.57 (+5) | not run |
| 1 stored + dreams only, K=8, PD 1.0 | **85.5** / 85.9 / 84.9 / 0.55 (+10) | not run |
| joint training (same code, 4 epochs, earlier) | 85.8 | |

- **The first dreams that help.** Dreams raise the result by +0.7 (seed 0) and +0.5 (seed 1) over the stored-images-only baseline at 20 images per class; run-to-run spread is about 1 point, so this is a small gain in the same direction on both seeds, not yet a settled one.
- **Dreams alone (one stored image per class) reach 85.5, above the 20-stored-images baseline (84.2) and within 0.3 of joint training**, one seed. If it holds on a second seed, the continual-learning claim becomes exemplar-free again (no real old images kept), at the price of the cluster counters.
- **The offset the chip needs shrinks to about +0 to +10 with dreams** (against +30 to +35 without), meaning the dreams keep old and new classes balanced by themselves; with dreams at seed 1 the offset rule picked +0 and the result was unbalanced (old 89.3, new 76.7, Shirt 0.20), a weakness of the share rule when the share curve is flat.
- **Memory (ESTIMATED).** K=8 clusters of 6,176 frequencies per class: 8 bits each is 49 KB per class (296 KB for six), 4 bits each 25 KB per class; larger than 20 stored images (about 10 KB per class), which is the price of dreams. A stored-prototype form (one code plus a mask per cluster) would be smaller (about 62 KB for K=8 in the research note's estimate); not built.
- Not yet tested: dreams-only on a second seed and on EMNIST, smaller K, a cheaper online clustering instead of k-means at stage 1.

Related: [Append-only clause banks in stages](append_only_clause_staged.md), [Thinking synthesis](../../docs/research/thinking_synthesis.md), [Results index](INDEX.md)
