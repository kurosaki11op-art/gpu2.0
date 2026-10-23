---
title: How much table memory is really needed, lossless (23 Oct 2026)
tags: [l, memory, results]
---

# Lossless storage of the trained tables (SIMULATED, integer model of the chip)

**Question.** Can the table memory shrink with no change to any stored value, so with no accuracy cost? `hw/brain/experiments/month5/table_storage_lossless.py` (log `table_storage_lossless.log`) trains the integer model on MNIST in 5 stages (2,000 images per stage, shipped settings, slow table; 94.15% on 2,000 test images) and measures the stored tables.

| Table | Entries | Stored bits | Non-zero | Largest value used | Entropy | Dense | Entropy limit (ideal lossless coding) |
|---|---|---|---|---|---|---|---|
| Fast table W | 46,080 | 5 | 68.4% | 15 | 3.80 bits | 28.1 KB | 21.4 KB |
| Slow table S | 46,080 | 8 | 53.9% | 105 | 3.97 bits | 45.0 KB | 22.4 KB |
| Dream counts | 46,080 | 10 | 71.0% | 833 | 5.94 bits | 56.2 KB | 33.4 KB |
| **Total** | | | | | | **129.4 KB** | **77.2 KB (1.7 times smaller at the very best)** |

**Reading.**
- The tables are mostly used (54 to 71% non-zero) and every stored width is really needed (the largest values fill 5, 8 and 10 bits), so trimming widths saves nothing.
- Even an ideal lossless code saves at most about **1.7 times**, and real hardware would not reach it. So **lossless coding cannot give a large memory increase**; a larger memory needs a denser memory, not a smarter code.
- Some code bits (8 to 20%) are unused by every class; rows for them could be dropped, a small saving.

**Limits.** One run, digits only, 10,000 training images; the figures change with the data. The dream counts (10-bit) are the largest single table.

Related: [Results index](INDEX.md), [Counting language model](counting_lm.md), [L accelerator design](../../docs/L_accelerator_design.md), [Journal](../../docs/journal.md)
