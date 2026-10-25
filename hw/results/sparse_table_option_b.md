---
title: Option B - a counting table that is sparse by construction (slots and sketch)
tags: [l, memory, sparse, scaling, counting-table]
---

# Option B: sparse by construction (25 Oct 2026)

SIMULATED, EMNIST-balanced (up to 47 classes, 40,000 training and 10,000 test images, L's 4,608-bit code, about 638 active bits per image), one seed, 8 epochs, my own integer margin learner (not L's CortexSlow, which scores 82.9% at 47 classes; this learner's full table scores 79 to 80%). Scripts and logs: [slot_table.py](../brain/experiments/month5/slot_table.py) ([47 classes](../brain/experiments/month5/slot_table_emnist47.log), [sweep](../brain/experiments/month5/slot_table_sweep.log)), [sketch_table.py](../brain/experiments/month5/sketch_table.py) ([47 classes](../brain/experiments/month5/sketch_table_emnist47.log)), [scaling](../brain/experiments/month5/slot_sketch_scaling.log).
- **Slots**: each bit keeps at most M (class, signed 6-bit weight) pairs; a class with no slot adds 0; the margin rule raises the true class's weight (taking a free or weak slot, or wearing the weakest slot down) and lowers the best wrong class's weight.
- **Sketch**: each bit keeps R counters; class c uses counter hash(bit, class) (hash assumed to be a few XOR-rotate gates, not stored); collisions average out across bits. No class index is stored.
- Adds only (no multiplies) in both; bits read per decision = active bits x row size x bits per entry (slots also carry a class index).

| Classes | Full table accuracy | Slots M=4 | Slots M=8 | Sketch R=4 | Sketch R=8 | Sketch R=16 |
|---|---|---|---|---|---|---|
| 10 | 97.2 | 97.1 | 97.2 | 96.5 | 96.9 | n/a (R above K) |
| 24 | 88.3 (slots), 87.9 (sketch) | 83.9 | 86.5 | 82.0 | 84.8 | 86.7 |
| 47 | 80.2 (slots), 78.7 (sketch) | 69.4 | 76.9 | 64.9 | 72.2 | 75.1 |

At 47 classes: slots M=8 read 61 kbit per decision (2.9 times fewer than a full 6-bit table; table 54 KB against 159 KB) for -3.3 points; sketch R=8 read 31 kbit (5.9 times fewer; 27 KB) for -6.5 points; two slots collapsed to 11% (the classes thrash over the slots). A wider weight range helped (cap 63 rather than 15: M=8 from 73.9 to 76.9); margin 4 and 16 were no better than 8.

## Reading
- **At 10 classes sparse rows are nearly free**: 4 slots or 4 to 8 counters per bit lose 0.1 to 0.6 points and read 1.5 to 2.5 times fewer bits.
- **The saving does not grow with the number of classes in this task**: at a fixed row size the loss grows with K (sketch R=8: -0.2, -3.1, -6.5 points at 10, 24, 47 classes), so the row size needed for a loss of about 2 points grows roughly as K/2. Evidence for the many letters is spread over many classes, so a few slots per bit cannot carry it.
- Compared at equal bits read: sketch is better at the small end (about 31 kbit: 72.2% against 69.4% for slots), slots slightly better at the larger end (about 61 kbit: 76.9% against 75.1%).
- **Verdict**: not yet a win-win at 47 classes (about 3 times fewer reads costs 2 to 3 points); useful at about 10 classes. The sketch still performs K adds per active bit (cheap compared with reads).
- Next candidate to make reads grow with the **logarithm** of the classes: two-stage routing (decide a coarse group, then read only that group's rows), with classes grouped by confusion; ESTIMATED cost near 2 times the square root of K rows instead of K.

Related: [Results index](INDEX.md), [MEM-C1 compression](table_compression_mem_c1.md), [Memory at scale synthesis](../../docs/research/memory_at_scale_synthesis.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
