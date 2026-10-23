---
title: L deployed table size against accuracy (24 Oct 2026)
tags: [l, memory, results]
---

# How small can the deployed L table be? (SIMULATED, Fashion-MNIST full 60,000 images, one seed)

`hw/brain/experiments/month5/l_deployed_memory.py`, log `l_deployed_memory.log`. Slow-table integer model, stride-1 code; the table S (10 x 4,608, signed 8-bit, 11.4% zeros) is requantised by right shift to fewer bits after training.

| Bits per entry | Deployed table | Single view | Look-again |
|---|---|---|---|
| 8 | 45.0 KB | 88.85 | 88.92 |
| 6 | 33.8 KB | 88.88 | 88.92 |
| 4 | 22.5 KB | 88.78 | 88.86 |
| 3 | 16.9 KB | 88.71 | 88.66 |
| 2 | 11.2 KB | 88.65 | 88.65 |

Against the compressed MLP of [compress_mlp.md](compress_mlp.md) (different script, 12 epochs): 4-bit 115 KB 89.52, 3-bit 86 KB 89.17, 2-bit 57 KB 85.34. So at equal deployed memory L is about 10 times smaller for 0.9 points less (11 KB 88.65 against 115 KB 89.52), and above the 2-bit MLP at one fifth of its size.

**Correction of an earlier reading:** the "129 KB for 85.7%" figure in `compress_mlp.md` counted L's learning state (fast table, dream counts, slow table) and came from another data protocol; it is not the deployed size. Both are needed: learning state is for the chip while it learns, the deployed table is what inference reads.

**Limits.** The two models were not re-run in one script with the same split and seeds; the small detector layer (templates) is not included in the L size; the MLP deployed size excludes its (larger) training state, as L's does; one seed; the extra passes test (`l_passes.log`) shows more reading of the same images does not change accuracy (88.9%), so the remaining gap to a CNN (91.1% in the ruler) is features and readout, not memory or passes.

Related: [Results index](INDEX.md), [Shrinking a standard network](compress_mlp.md), [Where L loses on clothing](clothing_confusion.md), [Journal](../../docs/journal.md)
