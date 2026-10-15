---
title: SPARK Cortex results at a glance
tags: [spark, cortex, pitch, summary]
---

# SPARK Cortex: results at a glance (15 Oct 2026)

A brain-principled chip that keeps learning after it ships: it senses (eyes, ears), learns each example once without
backprop, dreams and sleeps to keep what it knew, and copies its knowledge to another chip. No multiplier anywhere.
Labels: SIMULATED = our exact chip model or RTL simulation; ESTIMATED = from layout tools or arithmetic; **nothing is
MEASURED on hardware yet** (the board run is next: [month 4 plan](month4_board_plan.md)).

## What it does

| | Result | Label | Evidence |
|---|---|---|---|
| Learns new classes in stages without forgetting | after 5 stages: digits 94.6, clothing 78.3, sound 71.2 (chip cochlea with noise floor; 69.4 with the earlier float cochlea) vs a network 19.5 / 20.0 / 15.9 | SIMULATED, 3-5 seeds | [month 2](../hw/results/cortex_month2.md), [noise floor](../hw/brain/experiments/month4/noise_floor.md) |
| One class at a time | 10 stages: 93.5 / 78.7 / 70.5 vs network ~10 | SIMULATED | [month 3](../hw/results/cortex_month3.md) |
| Knowledge moves between chips | two chips' memories merged: 91.4% after one night | SIMULATED, bit-exact board design | [board README](../hw/board/README.md) |
| New condition of known classes | context memory: upright digits kept at 85% (45% without) | SIMULATED, in RTL | [new condition](../hw/results/cortex_new_condition.md) |
| Learns its own senses without labels | 94.5 / 80.0 vs 95.0 / 79.2 with PC-learned detectors | SIMULATED, in RTL | [on-chip detectors](../hw/brain/experiments/month3/onchip_detectors.md) |
| Holds up in noise (sound) | trained clean, white noise at 20 / 10 / 5 dB: 63.9 / 54.0 / 46.6 with the noise floor vs 56.2 / 44.0 / 32.1 without | SIMULATED, 3 seeds | [input noise](../hw/brain/experiments/month4/input_noise.md) |
| Spoken words on today's Tang Nano bitstream | 60.1 after 5 stages (PC cochlea -> sound picture -> board) vs network 15.9 | SIMULATED | [sound on board](../hw/brain/experiments/month4/sound_on_board.md) |
| Hears raw sound | live samples -> cochlea -> encoder -> learning core, whole chain bit-exact | SIMULATED (RTL) | [sound chip](../hw/results/cortex_sound_chip.md) |
| Ahead of the closest prior art (HDC) | digits +2.2, sound +5.7 (both on the new sound codes), clothing level | SIMULATED | [vs HDC](../hw/results/cortex_vs_hdc.md) |

## What it costs

| | Result | Label | Evidence |
|---|---|---|---|
| Memory | 84 KB for images (137x smaller than month 1); 422 KB for sound | design fact | [month 2](../hw/results/cortex_month2.md) |
| Tang Nano 20K ($25 FPGA) | fits: 89% logic, 46/46 block RAM, 0 multipliers, 69.8 MHz max at 27 MHz | SIMULATED (place and route) | [board README](../hw/board/README.md) |
| Energy per decision, operation count | 9.4 nJ vs 696 nJ for an 8-bit network (~74x) | ESTIMATED | [energy](../hw/results/cortex_energy_estimate.md) |
| Energy per decision, SKY130 layout | ~0.18-0.26 uJ (clock-gated, pipelined; global-route estimate) | ESTIMATED | [ASIC estimate](../hw/results/cortex_asic_estimate.md) |
| Energy per learned example, SKY130 layout | digits 45-62 uJ; "economy" setting ~3x less for -0.6 to -0.8 points | ESTIMATED | [energy per example](../hw/brain/experiments/month4/energy_per_example_layout.md), [dream budget](../hw/brain/experiments/month4/dream_budget.md) |
| Chip area, SKY130 | images ~18.8 mm^2 (95% open SRAM macros; logic < 1 mm^2); sound memories ~90 mm^2 with open macros | ESTIMATED | [ASIC](../hw/results/cortex_asic_estimate.md), [sound chip](../hw/results/cortex_sound_chip.md) |

## Say these limits first

1. Not the first continual-learning chip (HDC accelerators, Intel Loihi 2): what is new is the combination - dreams
   from counters, self-ending sleep, no multipliers, bit-exact from raw senses to decisions.
2. Learning everything at once, a network is ahead (97.8 vs 96.6 digits, 87.3 vs 83.7 clothing; sound: network 75.5 on
   the float cochlea's pictures vs the chip 71.9 with its own cochlea).
3. Few-shot: behind a small network at 5 examples per class (digits 62.8 vs 67.4).
4. The layout energy is ~20-28x above the operation count: say "74x less energy per operation needed", not per chip.
5. Nothing measured on hardware yet.

Related: [Claims sheet](cortex_claims_sheet.md), [Overnight report](overnight_report_2026-10-15.md), [Project memory](PROJECT_MEMORY.md)
