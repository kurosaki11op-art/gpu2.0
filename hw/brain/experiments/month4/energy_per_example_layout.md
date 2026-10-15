---
title: Energy per learned example from the layout
tags: [spark, cortex, energy, asic]
---

# Energy per learned example and per decision, from the SKY130 layout (15 Oct 2026, 07:10 IST)

`energy_per_example_layout.py`: operations of the full 5-stage run (exact integer model, month-2 rule: one daydream
per example, interleaved dreams of old classes, self-ending night) x cycles per operation in the pipelined RTL
(PREDICT 264, LEARN 2,465, DREAM 7,109) x energy per cycle from the clock-gated, pipelined layout (0.70-0.98 nJ at
50 MHz; `hw/results/cortex_asic_estimate.md`). Log `energy_per_example_layout.log`, JSON per dataset.

| | Digits | Clothing |
|---|---|---|
| Real examples | 60,000 | 60,000 |
| Day dreams | 180,000 | 180,000 |
| Night dreams | 336,000 | 123,648 |
| Cycles per learned example | 63,602 | 38,442 |
| **Energy per learned example** | **45-62 uJ** | **27-38 uJ** |
| **Energy per decision** | **0.19-0.26 uJ** | 0.19-0.26 uJ |

ESTIMATED. Learning is ~95% dreams (about 9 dreams of ~7,100 cycles per real example; a dream walks all 4,608 code
bits). The operation-count estimate for the same work is far lower (`hw/results/cortex_energy_estimate.md`); the gap
is clock and control overhead of this open 130 nm layout. There is no layout of the comparison network, so these
figures are not a ratio against it. Fewer dream cycles would need a dream that skips code bits (not bit-exact with
the current rule) - not tried.

Related: [ASIC estimate](../../../results/cortex_asic_estimate.md), [Energy estimate](../../../results/cortex_energy_estimate.md), [Month 4 experiments](INDEX.md)
