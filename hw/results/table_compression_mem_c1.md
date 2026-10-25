---
title: MEM-C1 - store only the differences between classes, prune, share codes
tags: [l, memory, compression, energy, counting-table]
---

# MEM-C1: difference-only, pruned, quantised counting table (25 Oct 2026)

Script [mem_c1.py](../brain/experiments/month5/mem_c1.py), log [mem_c1.log](../brain/experiments/month5/mem_c1.log). SIMULATED, Fashion-MNIST, single view, one seed, L's 4,608-bit code, trained table (values about -104 to +105). Idea from the EIE and Deep Compression reading: a row's part that is common to all classes never changes which class wins, so it is removed (row centred on its median; accuracy unchanged: 88.85%, Shirt AP 0.753); the differences are pruned by size, coded in b bits, and stored in a compressed row of (4-bit class index, b-bit code) pairs plus an 8-bit row pointer. A decision reads only the active bits' rows. Counts, not energy.

| Code bits | Fraction of differences kept | Accuracy | Shirt AP | Bits read per decision | Dense b-bit table reads | Table size |
|---|---|---|---|---|---|---|
| 2 | all that survive (10.6%) | 86.8 | 0.696 | 9,214 | 11,763 | 8.3 KB |
| 3 | 0.5 | 88.7 | 0.747 | 26,769 | 17,645 | 23.1 KB |
| 3 | 0.2 | 88.25 | 0.728 | 13,777 | 17,645 | 12.1 KB |
| 4 | 0.3 | 88.26 | 0.742 | 20,255 | 23,527 | 17.3 KB |
| 4 | 0.2 | 88.26 | 0.733 | 15,073 | 23,527 | 13.1 KB |
| (reference) dense full precision | | 88.85 | 0.753 | | | |

## Reading
- **At 10 classes the saving is only about 10 to 25%** (for example 3 bits with 20% kept: 13.8 kbit read against 17.6 kbit dense, accuracy -0.6). A row has only 10 entries, so the class index (4 bits) and row pointer (8 bits) cost as much as the values they save. My earlier "15 to 30 times" estimate was for tables with many classes per row and does **not** hold at 10 classes: corrected.
- **The common part carries no information** (centring is lossless), and about 90% of the centred entries are non-zero: the table is dense in differences at 10 classes.
- My uniform global quantiser is crude (2-bit 86.8%; the project's own 2-bit deployed table reaches 88.65%, see [l_deployed_memory](l_deployed_memory.md)); a better code would improve the 2-bit rows.
- **Where it should pay (not tested)**: with hundreds of classes a row holds hundreds of entries of which a few matter, so pointer overhead fades and savings approach classes divided by entries kept. The scaling test needs a data set with many classes.

Related: [Results index](INDEX.md), [Memory at scale synthesis](../../docs/research/memory_at_scale_synthesis.md), [Hardware landscape](../../docs/research/hardware_landscape_synthesis.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)

## Many-class test: EMNIST-balanced, 47 classes (25 Oct 2026, SIMULATED, one seed)
Script [emnist_c1.py](../brain/experiments/month5/emnist_c1.py), logs [encode](../brain/experiments/month5/emnist_c1_step1.log), [analysis](../brain/experiments/month5/emnist_c1_step2.log). EMNIST-balanced (digits, upper- and lower-case letters, 28x28): 40,000 training and 10,000 test images drawn at random, L's code with detectors fitted on 12,000 unlabelled images (635 active bits per image), table trained with margin updates on the first K classes. Kept entries cost ceil(log2 K) bits for the class index plus the code; every active row costs an 8-bit pointer (and 8 more for a per-row scale).

| Classes K | L's table, dense full precision | Non-zero differences after centring | 2-bit global code, no pruning | 3-bit, 30% kept | 3-bit, 10% kept |
|---|---|---|---|---|---|
| 10 | 97.3 | 68% | 88.6 (bits read 6.8k against 12.7k dense, 1.87 times fewer) | 96.6 (1.02 times) | 95.2 (1.78 times) |
| 24 | 88.7 | 81% | 82.7 (1.90 times) | 87.8 (0.97 times) | 83.9 (2.20 times) |
| 47 | 82.9 | 83% | 75.9 (1.46 times) | 81.2 (0.90 times) | 73.8 (2.31 times) |

- **The hypothesis failed.** The differences stay dense as classes are added (68% then 81% then 83% of centred entries are non-zero), so a row does not shrink to a few important entries. At 47 classes pruning to a read saving costs accuracy fast: 10% kept gives 2.3 times fewer bits read but 9 points lower accuracy; 30% kept saves nothing (0.9 to 1.0 times) and still loses 1.7 points.
- **What was not tried**: Deep Compression prunes **and then retrains** with the mask; here the table was pruned after training with no retraining, so the recipe is only half tested. Retraining with a masked margin learner is the proper test.
- **Scaling datum for L**: the unchanged counting table on L's 4,608-bit code scores 97.3% (10 EMNIST classes), 88.7% (24) and 82.9% (47 classes, 40,000 training images); a dense 2-bit table for 47 classes is about 54 KB. Dense tables grow linearly with the number of classes: 4,608 x K entries.
