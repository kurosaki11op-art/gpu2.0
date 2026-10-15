---
title: Retinal adaptation for images
tags: [spark, cortex, experiment, images]
---

# Retinal adaptation: thresholds that follow each image's brightness (15 Oct 2026, 10:30 IST)

The brightness receptors' thresholds follow each image's brightest pixel, thr' = (max x thr) >> 8, instead of fixed
50 / 150 (ON/OFF cells unchanged). Same detector learning, exact integer chip model, month-2 rule, after 5 stages.
`retina_adapt.py`; logs `retina_adapt.log` (3 seeds), `retina_adapt_5seeds.log`.

| | Clothing, 3 seeds | Clothing, 5 seeds | Digits, 3 seeds |
|---|---|---|---|
| fixed thresholds | 78.3 | 78.4 | 94.6 |
| adapted thresholds | 79.2 | 79.0 (better on 3 of 5 seeds) | 94.6 |

SIMULATED. +0.6 on clothing over 5 seeds is within the seed spread (+2.7 on one seed, -0.4 to +0.7 on the others);
digits unchanged. Not adopted: not a clear win for the extra pass over the image.

## More receptor types (same day)

Three brightness receptors (30, 100, 170) instead of two (50, 150), ON/OFF cells unchanged: 5 channels, 5,760-bit
code (+25% memory). `receptor_types.py`, logs `receptor_types.log`, `receptor_types_s45.log`.

| | Clothing, 5 seeds | Digits, 3 seeds |
|---|---|---|
| 50 / 150 (current) | 78.4 | 94.6 |
| 30 / 100 / 170 | 79.1 (better on 4 of 5) | 94.3 |

SIMULATED. A small real gain on clothing (+0.8) for 25% more memory and a small loss on digits. Not adopted on the
Tang Nano (its block RAM is full); kept as an option for an ASIC with memory to spare.

Related: [Noise floor (sound)](noise_floor.md), [Month 4 experiments](INDEX.md)
