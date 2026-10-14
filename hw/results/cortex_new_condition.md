---
title: SPARK Cortex, new conditions for known classes
tags: [spark, cortex, results, limits]
---

# New conditions for classes the chip already knows (domain shift), SIMULATED

Test (`hw/brain/domain_shift.py`, integer chip model, month-2 rule): day 1 = all ten classes upright; day 2 = all ten
classes rotated 90 degrees (different images), like a camera remounted sideways. Accuracy after day 2:

| | Digits upright | Digits rotated | Clothing upright | Clothing rotated |
|---|---|---|---|---|
| Neural network, fine-tuned day by day | 26.9 | 95.4 | 10.1 | 84.2 |
| Chip, month-2 rule | 44.8 | 95.3 | 25.1 | 82.7 |

**Limit found:** "never forgets" holds when new *classes* arrive, not when known classes come back under a new
*condition*. On day 2 every class is "new" again, so no old class is dreamed, and each class's dream counts blend the
two conditions into one blurred average.

## Fix tested: context memory (float simulation, `experiments/month3/m4b.py`)

The brain keeps memories of different contexts apart. Here: when a day brings classes the chip already knows, the
dream counts are frozen as "yesterday's" copy; during the day and at night the table also practises dreams from that
frozen copy.

| After day 2 | Digits upright | Digits rotated | Clothing upright | Clothing rotated |
|---|---|---|---|---|
| Month-2 rule | 41.8 | 96.8 | 13.7 | 83.1 |
| Dreaming the live (mixed) counts, no copy | 43.2 | 96.3 | 12.2 | 82.6 |
| **Frozen copy of yesterday's counts** | **86.1** | 95.9 | **75.4** | 80.3 |
| Frozen copy + a fresh bank for today | 86.1 | 95.9 | 75.4 | 80.3 |

On the exact integer chip model (`CortexInt(..., context=True)`: when known classes return, the dream counts are
frozen; day dreams come from the frozen copy, night dreams alternate live / frozen), one pass per example:

| After day 2 | Digits upright | Digits rotated | Clothing upright | Clothing rotated |
|---|---|---|---|---|
| Chip, month-2 rule | 44.8 | 95.3 | 25.1 | 82.7 |
| **Chip with context memory** | **85.3** | 95.5 | **73.4** | 81.5 |
| Neural network | 26.9 | 95.4 | 10.1 | 84.2 |

Cost: a second copy of the dream counts (+56 KB for images). It does not fit the Tang Nano's block RAM next to the
current design; it fits the board's PSRAM or an ASIC. Not in the RTL yet. Only one new condition tested; several
contexts would need one frozen copy each, or a smarter shared store.

Related: [Month 3 results](cortex_month3.md), [Prior art](../../docs/prior_art_cortex.md), [Results index](INDEX.md)
