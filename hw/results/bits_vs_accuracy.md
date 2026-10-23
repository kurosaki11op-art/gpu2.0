---
title: Does fewer bits cost accuracy? (23 Oct 2026)
tags: [l, memory, accuracy, results]
---

# Counter width against accuracy (SIMULATED, integer model of L Cortex)

`hw/brain/experiments/month5/bits_vs_accuracy.py` (logs `bits_vs_accuracy.log`, `bits_vs_accuracy_fashion.log`). Shipped settings with the slow table, 2,000 training images per stage, 2 seeds, 3,000 test images (so about plus or minus 0.5 to 1 point of noise). Margin held at 256 (not retuned for each width). "Staged" = 5 stages of 2 classes; "all at once" = one stage.

**Digits (MNIST)**

| What changes | Bits | Staged % | All at once % |
|---|---|---|---|
| fast table | 2 | 9.73 | 9.73 |
| fast table | 3 | 91.52 | 93.97 |
| fast table | 4 | 95.13 | 96.75 |
| fast table (shipped) | 5 | 93.65 | 96.93 |
| fast table | 6 | 94.68 | 96.90 |
| fast table | 8 | 94.72 | 96.85 |
| dream counts | 6 | 94.18 | 96.88 |
| dream counts | 8 | 95.08 | 96.85 |
| dream counts | 12 | 94.88 | 96.93 |

**Clothing (Fashion-MNIST), the harder task**

| What changes | Bits | Staged % | All at once % |
|---|---|---|---|
| fast table | 2 | 10.23 | 10.23 |
| fast table | 3 | 77.23 | 79.45 |
| fast table | 4 | 80.20 | 84.63 |
| fast table (shipped) | 5 | 81.48 | 85.67 |
| fast table | 6 | 81.75 | 85.73 |
| fast table | 8 | 81.45 | 86.17 |
| dream counts | 6 | 79.55 | 85.45 |
| dream counts | 8 | 81.15 | 85.55 |
| dream counts | 12 | 81.38 | 85.67 |

**Reading.**
- **Yes, fewer bits cost accuracy, and more on the harder task.** On clothing, a 4-bit fast table loses about 1.3 (staged) and 1.0 (all at once) against the shipped 5 bits, 3 bits loses 4 to 6 points, 2 bits collapses; 6-dream-count bits loses about 2 points staged. On digits 4 bits is as good as 5 (within noise).
- **The shipped widths (5-bit table, 10-bit counts) are near the knee**; going wider gains at most a few tenths of a point (6 to 8 bits: +0.3 staged, +0.5 to 0.5 all at once on clothing).
- So **narrowing the counters is not a free way to a bigger memory**; the lossless limit is 1.7 times at best ([lossless storage](table_storage_lossless.md)); a much larger memory needs a denser memory.
- Limits: one data split, 2 seeds, margin not retuned, digits and clothing only.

Related: [Results index](INDEX.md), [Lossless table storage](table_storage_lossless.md), [Journal](../../docs/journal.md)
