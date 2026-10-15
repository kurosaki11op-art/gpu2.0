---
title: Dream budget vs accuracy (economy setting)
tags: [spark, cortex, energy, experiment]
---

# Fewer dreams: an energy / accuracy dial (15 Oct 2026, 07:30 IST)

Learning energy is ~95% dreams ([layout estimate](energy_per_example_layout.md)), so how much accuracy do the dreams
buy? Exact integer chip model, 5 stages, month-2 rule except `ndream` (dreams per old class in a day and per class in
a night pass) and the number of night passes.

One seed, sweep (`dream_budget.py`, log `dream_budget.log`; energy from the pipelined layout, ESTIMATED):

| ndream x night passes | Digits | Dreams / example | uJ / example | Clothing | Dreams / example | uJ / example |
|---|---|---|---|---|---|---|
| 6000 x 2 (month-2 rule) | 94.6 | 8.6 | 45-62 | 78.7 | 5.1 | 27-38 |
| 3000 x 2 | 94.1 | 4.8 | 26-36 | 78.4 | 2.9 | 16-23 |
| 6000 x 1 | 93.9 | 5.8 | 31-43 | 78.6 | 4.0 | 22-31 |
| 3000 x 1 | 94.1 | 3.4 | 19-26 | 76.9 | 2.6 | 14-20 |
| **1500 x 1** | **94.0** | **2.2** | **13-18** | **79.2** | **1.8** | **11-15** |
| 750 x 1 | 92.9 | 1.6 | 10-14 | 76.3 | 1.3 | 8-12 |

Three seeds (example order and random lanes; `dream_budget_seeds.py`, log `dream_budget_seeds.log`):

| | Digits | Clothing | Sound | Dreams / example (digits, clothing, sound) |
|---|---|---|---|---|
| 6000 x 2 (month-2 rule) | 94.6 | 78.3 | 69.4 | 8.6, 5.1, 6.7 |
| 1500 x 1 (economy) | 94.0 | 77.7 | 68.6 | 2.2, 1.7, 2.5 |

SIMULATED accuracy; energy ESTIMATED. Result: the economy setting costs 0.6-0.8 points on every task for 3-4x fewer
dreams, i.e. ~3x less learning energy (digits ~13-18 uJ per learned example instead of 45-62). Both are host-side
settings (the host decides how many dreams to send), so the chip supports either without change. Not adopted as the
default; offered as a mode.

Related: [Energy per learned example](energy_per_example_layout.md), [Month 2 results](../../../results/cortex_month2.md), [Month 4 experiments](INDEX.md)
