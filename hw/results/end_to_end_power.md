---
title: End to end power, picture to answer (23 Oct 2026)
tags: [l, power, benchmark, results]
---

# Energy and power per image, encoder included (ESTIMATED chip, MEASURED GPU)

**Why this note.** The chip rows of `benchmark.py` (55.7 us, 11.7 us) and my earlier layout figure (0.18 to 0.26 uJ) are the **decision from the sparse code only**. Turning the picture into that code (the encoder) takes **21,378 cycles per image** (RTL simulation, [ASIC estimate](cortex_asic_estimate.md)), about 0.79 ms at 27 MHz or 0.43 ms at 50 MHz, far more than the 317 cycles (pipelined) or 1,504 cycles (FPGA build) of the decision. The GPU CNN does the whole image. This note gives the end-to-end numbers.

## Chip, from the routed SKY130 layout (OpenROAD power analysis, typical corner, 50 MHz clock, gated clocks)

Two phases: **encode** (encoder clock gates on every cycle, SRAM ports idle) and **decide** (encoder idle, SRAM read ports on one bank in nine). Switching activity is a guess bracket (5% and 10% of cycles; not yet measured from simulation). Files: `hw/asic/cortex/signoff/power_phase.tcl`, `power_*.log`.

| Phase | Power at 5% / 10% activity | Energy per cycle | Cycles | Energy per image |
|---|---|---|---|---|
| Encode | 92 / 104 mW | 1.85 / 2.08 nJ | 21,378 | **39.5 to 44.5 uJ** |
| Decide (pipelined core) | 45 / 55 mW | 0.91 / 1.10 nJ | 317 | 0.29 to 0.35 uJ |
| **Image to answer** | about 90 to 100 mW while running | | about 21,700 | **about 40 to 45 uJ** (99% in the encoder) |

Time per image: about 0.43 ms at 50 MHz, 0.54 ms at the 40 MHz the layout reaches, 0.80 ms at 27 MHz (the FPGA clock); the FPGA build's slower decision (1,504 cycles) adds 0.06 ms.

## GPU, same job (the CNN reads the raw image), MEASURED on the RTX 3050 6GB laptop GPU

| Run | Batch 1 | Batch 1024 | Average power while running (energy / time) |
|---|---|---|---|
| 22 Oct (first) | 1,809 us, 69.3 mJ | 22,226 images/s, 1.95 mJ | about 38 W and 43 W |
| 23 Oct (second) | 421 us, 12.56 mJ | 98,427 images/s, 0.294 mJ | about 30 W and 29 W |
| Idle floor (nvidia-smi) | | | about 11.8 W |

## Ratio, energy per image (chip ESTIMATE against GPU MEASURED)

| | GPU 12.56 mJ (batch 1, 23 Oct) | GPU 0.294 mJ (batch 1024, 23 Oct) | GPU 69.3 mJ (batch 1, 22 Oct) | GPU 1.95 mJ (batch 1024, 22 Oct) |
|---|---|---|---|---|
| Chip about 42 uJ | about 300 times | about 7 times | about 1,650 times | about 46 times |

**Reading.** End to end, the layout estimate is roughly **7 to 1,650 times** less energy than the GPU, depending on the GPU's power state and batch size, not the 57,000-fold figure obtained when the encoder was left out. The operation-count figure (9.3 nJ including the encoder) is a lower bound that leaves out the clock tree, control and leakage; the layout estimate includes them.

**Limits.** Switching activity is a bracket (5% to 10%), not yet measured from a simulated image; the OpenRAM macros' energy is taken from their library; the encoder, which dominates, was designed for area, not energy, and an energy-lean or parallel encoder is the obvious improvement; power analysis is for the typical corner and 50 MHz; the chip is not built, so this is an estimate until the board run. GPU power is energy divided by time from the energy counter, not a separate meter reading.

Related: [Results index](INDEX.md), [ASIC estimate](cortex_asic_estimate.md), [Journal](../../docs/journal.md)
