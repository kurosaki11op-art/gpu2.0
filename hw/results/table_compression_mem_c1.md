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
