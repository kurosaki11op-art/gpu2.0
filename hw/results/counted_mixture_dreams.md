---
title: Counted-mixture dreams with teacher labels in staged learning
tags: [spark, results, continual, dreams]
---

# Counted-mixture dreams with teacher labels (26 Oct 2026)

SIMULATED, Fashion-MNIST, 6 old + 4 new classes, unfrozen rehearsal as in [the staged note](append_only_clause_staged.md), 150,000 steps, one share-rule offset per run (label-free). Part 1 of the thinking plan. Script `hw/brain/experiments/month5/staged_mixture.py`, logs `staged_mixture_*.log`. The earlier dreams (independent bits, tree, clause-forced) all failed; the research notes pointed to a mixture level and teacher labels, which we built our own way:

- **Counted sub-prototypes.** Each old class keeps K clusters of its stage-1 data, each stored only as one frequency per bit (counters, no images). A dream picks a cluster (by size) then draws every bit from that cluster's frequencies: a mixture of products, so bits that go together inside a cluster stay together.
- **Teacher label and boundary filter.** The frozen stage-1 banks score each dream; the dream's label is the teacher's answer, not the generating class, and only dreams near the teacher's boundary (margin below the median) are kept (about half of the 18,000 generated).
- Old-class rehearsal draws come from these dreams with probability PD, otherwise from the stored images (recombined as before).

| run (150,000 steps, label-free share-rule offset) | seed 0 | seed 1 | seed 2 | mean |
|---|---|---|---|---|
| 20 stored images, no dreams (baseline) | 84.2 | 83.8 | 83.3 | 83.7 |
| 20 stored + dreams, K=8, PD 0.5 | 84.4 | 85.4 | not run | 84.9 (two seeds; baseline on the same two: 84.0) |
| 1 stored + dreams only, K=8, PD 1.0 | 85.3 (85.5 and 85.0 in two earlier runs) | 84.7 | 82.7 | 84.2 |
| 20 stored + dreams, K=32, PD 0.5 | 85.1 | not run | not run | |
| 1 stored + dreams only, K=4, PD 1.0 | 84.8 | not run | not run | |
| joint training (same code, 4 epochs, earlier) | 85.8 | | | |

Correction of the first writeup: the first runs used an offset grid that started at 0, which could never favour the new classes (it forced +0 on seed 1 and gave Shirt recall 0.20); with the grid extended to negative offsets the seed-1 results moved from 84.3 to 85.4 (stored + dreams) and from 84.2 to 84.7 (dreams only), and the label-free rule picks sensible offsets (from -15 to +10). The per-class share rule (each of the ten classes should receive about a tenth of the predictions) was added and printed beside the old/new share rule; it picked the same or a nearby offset and no better accuracy, so it is not adopted.

- **A small, consistent gain, not a large one.** Stored images plus dreams beat stored images alone by +0.9 on the two seeds where both were run (84.9 against 84.0); dreams alone (one stored image per class, so no real old images kept) match the 20-stored-images baseline on average (84.2 against 83.7, +0.4) but vary by seed (82.7 to 85.3). With a run-to-run spread of about 1 point, only the combination looks like a gain; the dreams-only result is parity.
- **The value of dreams is mainly that the old images need not be kept**: parity with 20 stored images per class without storing any, restoring the exemplar-free property, and a smaller offset (about -15 to +10 against +30 to +35) because the dreams keep old and new classes balanced.

- **Memory (ESTIMATED).** K=8 clusters of 6,176 frequencies per class: 8 bits each is 49 KB per class (296 KB for six), 4 bits each 25 KB per class; larger than 20 stored images (about 10 KB per class), which is the price of dreams. A stored-prototype form (one code plus a mask per cluster) would be smaller (about 62 KB for K=8 in the research note's estimate); not built.
- Not yet tested: dreams on EMNIST, a cheaper online clustering instead of k-means at stage 1, a seed-2 run of stored + dreams.

Related: [Append-only clause banks in stages](append_only_clause_staged.md), [Thinking synthesis](../../docs/research/thinking_synthesis.md), [Results index](INDEX.md)
