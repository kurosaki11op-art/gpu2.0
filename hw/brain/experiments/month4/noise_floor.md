---
title: Noise floor in the cochlea (auditory adaptation)
tags: [spark, cortex, sound, experiment]
---

# Removing the background noise: a per-resonator noise floor (15 Oct 2026, 09:00 IST)

The user asked to "remove the noise and improve the results". The spoken-word clips carry background noise that the
cochlea turns into a grey haze in every sound picture. Hearing adapts to a steady background; here each resonator
estimates its own floor from the clip's quietest frames and subtracts it from every frame sum before the integer log.
Integer cochlea, same detector learning, exact integer chip model, month-2 rule, sound after 5 stages.
Script `noise_floor.py`; logs `noise_floor.log`, `noise_floor_2.log`, `noise_floor_3.log`, `noise_floor_5seeds.log`.

| Floor (subtracted from every frame sum) | 3 seeds | 5 seeds |
|---|---|---|
| none (before) | 69.9 | 69.6 (69.9, 70.0, 69.8, 69.7, 68.6) |
| quietest frame | 69.3 | |
| mean of 4 quietest | 70.7 | |
| 2x mean of 4 quietest | 71.0 | |
| 2x mean of 8 quietest | 70.8 | |
| 3x mean of 4 quietest | 70.8 | |
| **4x mean of 4 quietest** | **72.0** | **71.2** (71.3, 73.0, 71.8, 69.2, 70.7) |
| 6x mean of 4 quietest | 71.5 | 70.8 |
| 8x mean of 4 quietest | 70.3 | |

SIMULATED. Adopted: 4x the mean of the 4 quietest frames, **+1.6 points on sound over 5 seeds** (better on 4 of 5).
In hardware it is the sum of the 4 quietest frame sums with the two low bits cleared: 4 compares per frame and one
subtraction per pixel. Now the default in `hw/brain/cochlea_int.py` (`noise_floor`) and in
`hw/rtl/cortex/cortex_cochlea.v`, bit-exact (`check_cochlea_floor.log`).

Also tried, on top of the floor: lateral inhibition across neighbouring resonators (each subtracts a share of its
two neighbours, sharpening the spectrum): neighbours / 4: 67.7, neighbours / 8: 70.5 (3 seeds; floor alone 72.0).
Rejected - it removes information the detectors use (`lateral_inhibition.log`).

Related: [Cochlea in RTL](cochlea_rtl.md), [Month 4 experiments](INDEX.md)
