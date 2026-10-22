---
title: L Cortex energy estimate
tags: [spark, cortex, results, energy]
---

# L Cortex energy per decision and per learning step (ESTIMATED)

Script: `hw/brain/energy_cortex.py`; numbers `cortex_energy_estimate.json`. Operation counts come from the design
(active code bits measured on the digit test images: 246 on average; memory words from the RTL). Energy per operation
from Horowitz, ISSCC 2014 (45 nm): 8-bit add 0.03 pJ, 32-bit add 0.1 pJ, 8-bit multiply 0.2 pJ, float add 0.9 pJ,
float multiply 3.7 pJ, 64-bit SRAM read 10 pJ (8 KB) / 20 pJ (32 KB) / 100 pJ (1 MB). These are estimates for a custom
chip, not FPGA numbers and not measurements. Board power is measured in month 4.

| | L Cortex | Neural network 784-256-10 | Ratio |
|---|---|---|---|
| One decision | **9.4 nJ** (4.2 sensing + 5.2 deciding) | 696 nJ (8-bit weights) / 11,100 nJ (float) | **~74x** (vs 8-bit) |
| Learning one real example | 29 nJ (sense, count, decide, update) | 33,300 nJ per example per training pass (float, forward + backward + update) | ~1,100x per pass |
| Learning, sleep included (last stage of digits: ~15 dreams per real example, 53 nJ each) | ~0.8 uJ per example | ~166 uJ per example (5 training passes) | **~200x** |

Where the difference comes from: the network reads all 200 KB of its weights for every decision and multiplies each
one. The chip reads one small table word (50 bits) per active code bit, about 246 words, and only adds. Learning is
counting plus a few counter nudges when surprised; there is no backward pass.

Caveats:
1. The network figure assumes its weights sit in on-chip SRAM. On a GPU they come from DRAM (about 1-2 nJ per 64 bits),
   which makes the network's numbers larger, not smaller.
2. Control logic, clocking and leakage are not counted for either side.
3. The chip's sensory layer was costed for 4 channels x 32 detectors x 144 spots; a bigger sensory layer costs more.
4. Accuracy is not equal: all data at once the network is 1.2 points better on digits (97.8 vs 96.6); learning in
   stages the chip is 75 points better (94.6 vs 19.5).

Related: [Month 2 results](cortex_month2.md), [Results index](INDEX.md)
