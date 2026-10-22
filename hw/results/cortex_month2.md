---
title: L Cortex month 2 results
tags: [spark, cortex, results]
---

# L Cortex month 2: memory shrunk to chip size, one rule for every task

All numbers SIMULATED on the **exact integer chip model** (`hw/brain/cortex_int.py`), which the RTL matches bit for
bit (`hw/rtl/cortex/run_check_cortex.py`, 0 mismatches) and which the board design matches over UART
(`hw/board/check_cortex_board.py`, 0 mismatches). Every real example is seen **once**, as a streaming chip sees it.
Script: `hw/brain/month2_final.py`; raw numbers `cortex_month2_final_<task>.json`. Step-by-step search, including
everything that failed: [month-2 log](cortex_month2_log.md).

## The design (one rule for digits, clothing and spoken words)

| Part | What it is | Brain principle |
|---|---|---|
| Sensory code | 32 learned detectors per channel (images, 4,608 bits) / 64 (sound, 23,040 bits) | competitive Hebbian learning |
| Fast table | 5-bit signed counters per (class, bit); **makes every decision**; written only on surprise | dopamine-style surprise learning |
| Dream memory | per class, a 10-bit count of how often each bit fired; halved when full | synaptic scaling |
| Day | each real example: count it, practise it, then one daydream of its class; dreams of old classes interleaved | daydreaming, replay |
| Night | up to 2 passes of dreams of every known class; **ends itself** after a block of 256 dreams with more than 2 surprises | sleep that stops when dreams stop making sense |

Arithmetic: adds, compares, shifts, XOR. No multiplier, no divider, no backprop.

## Results

| | Digits | Clothing | Spoken words |
|---|---|---|---|
| Network, all data at once (best case for it) | 97.8 | 87.3 | 75.5 (our pictures) / 76.2 (FFT log-mel) |
| **Chip, all data at once (one pass)** | 96.6 | 83.7 | 71.1 |
| Network, 5 stages | 19.5 | 20.0 | 15.9 |
| Network + replay of 20 stored examples per old class | 49.6 | 37.8 | 27.8 |
| **Chip, 5 stages (no examples stored)** | **94.6** | **78.7** | **69.7** |
| Merge: chip A (classes 0-4) + chip B (5-9), one night | 93.0 | 82.3 | 62.6 |
| Network weight averaging, same split (first proof) | 82.8 | 62.0 | n.a. |

Memory: images 28 KB table + 56 KB dream counts = **84 KB** (month 1: 11.5 MB, 137x smaller), fits the Tang Nano
20K's 103 KB block RAM. Sound: 141 KB + 281 KB = 422 KB (month 1: 28 MB, 66x smaller); does not fit block RAM; the
board's 8 MB PSRAM would hold the dream counts (not yet built).

FPGA synthesis of the core (yosys, GW2AR-18, image size, before place and route): 46/46 block RAMs (100%), about
12,500 LUT4 + dedicated muxes, about 1,840 flip-flops, 0 multipliers. Fits on paper, but block RAM is full.

## Against month 1 and the month-2 goals

| Goal | Result |
|---|---|
| Shrink memory ~100x | images 137x (84 KB), sound 66x (422 KB) |
| Keep month-1 accuracy | not fully: 5 stages digits 94.6 (month 1: 97.2), clothing 78.7 (86.3), sound 69.7 (71.8) |
| One decision rule | done: the fast table always decides; the night length regulates itself |
| Few-shot at least equal to the network | **not met**: 1/5/20 per class digits 37/56/82 vs 39/67/81, clothing 39/49/69 vs 44/63/74 (float table, v3 suite) |

## Honest limits

1. The accuracy loss against month 1 comes mostly from dreams in which bits are independent: they can only teach what
   a per-bit model knows (~79 on clothing). Mixture dreams (concept cells) reached 84 but need multi-pass sorting or
   more memory. Open problem.
2. The merge night stopped after 256 dreams in all three tasks (dreams surprised the merged table); a full night gave
   95.8 on digits in the float version. A merge may deserve its own rule.
3. Few-shot remains worse than the network.
4. Spread over 3 seeds (arrival order and random lanes; `hw/brain/seeds_check.py`, `cortex_seeds_<task>.json`) after
   5 stages: digits 94.4-94.8 (mean 94.6), clothing 77.7-78.7 (78.3), sound 69.0-70.0 (69.4). Other rows are one seed.
5. Feature detectors are learned in software from stage-1 images and loaded; on-chip feature learning is not built.
6. Time on the board (ESTIMATED from the RTL cycle counts at 27 MHz): about 1 ms per dream, 1-2 minutes for a full
   night; learning over UART at 115,200 baud is ~50 ms per example (the host link, not the core, is the bottleneck).

Related: [Month-2 log](cortex_month2_log.md), [Month 1](cortex_month1.md), [L Cortex redesign](../../docs/cortex_redesign.md),
[Brain code](../brain/README.md), [Results index](INDEX.md)
