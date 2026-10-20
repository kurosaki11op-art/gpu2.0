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
| Learns new classes in stages without forgetting | after 5 stages (16 Oct, all adopted options, 5 seeds): digits 95.8, clothing 78.3, words 82.9 (earlier, before word alignment / margin 32 / LOOK AGAIN: 94.6 / 78.3 / 71.2) vs a network that forgets: 19.5 / 20.0 / 15.9 | SIMULATED, 5 seeds | [month 2](../hw/results/cortex_month2.md), [noise floor](../hw/brain/experiments/month4/noise_floor.md) |
| One class at a time | 10 stages: 93.0 / 78.7 / 71.2 (3 seeds, measured 15 Oct before word alignment and margin 32; not re-run) vs network ~10 | SIMULATED | [month 3](../hw/results/cortex_month3.md) |
| Knowledge moves between chips | two chips' memories merged: 91.4% after one night (board demo); hand-over (copy A's memory into B, B learns on): 95.6 / 82.7 / 71.6 vs merge 93.3 / 81.4 / 64.3 | SIMULATED, bit-exact board design, 3 seeds | [board README](../hw/board/README.md), [merge vs hand-over](../hw/brain/experiments/month4/merge_variants.md) |
| New condition of known classes | context memory: upright digits kept at 85% (45% without) | SIMULATED, in RTL | [new condition](../hw/results/cortex_new_condition.md) |
| Hears words better: word alignment | sound 71.9 -> 82.5 all at once, 72.0 -> 80.7 in 5 stages (5 seeds); in noise 80.3 / 72.4 / 58.9 / 47.1 (clean / 20 / 10 / 5 dB) | SIMULATED, in RTL (bit-exact) | [noise floor + alignment](../hw/brain/experiments/month4/noise_floor.md) |
| Learns a new class from 1 example after shipping (IMPRINT + short sleep) | 1 example per new class, accuracy on all 10: digits 54.1 -> 69.9, clothing 49.7 -> 64.0, words 45.2 -> 48.3; old classes kept within 1-5 points; after shipping the chip beats a network (fine-tuned, or kept on all old data) on all 10 classes at every size, digits / clothing / words | SIMULATED, in RTL (bit-exact) | [redesign 1](../hw/brain/experiments/month4/fewshot_imprint.md) |
| Slow table (ASIC option; Redesign 6, K = 5, 18-19 Oct) | 5 seeds, single view / LOOK AGAIN, all at once: clothing 83.4 / 84.8 -> **87.6 / 88.3**, words 83.1 / 84.7 -> **86.4 / 87.5**, digits 97.0 / 98.0 -> **97.8 / 98.4**; **in 5 stages: clothing 78.4 -> 81.6, digits 94.9 -> 95.0, words 82.0 -> 82.6** | SIMULATED, in RTL (bit-exact, option CORTEX_SLOW) | [limits and slow table](../hw/brain/experiments/month4/slow_table_and_staged_limits.md) |
| **New spoken words with the embedding path (ASIC option; Redesign 8, 20 Oct)** | a new word is described by its table scores over 15 known words (5 + 10 digits) and stored as a prototype; 1 / 2 / 5 recordings per new word, all ten words 50.2 / 56.4 / 62.3 vs 48.0 / 50.0 / 51.5 for new table rows; new words 12.6 / 27.0 / 40.4 vs 11.1 / 12.7 / 18.5; old words 86.8 / 85.1 / 83.6 vs 84.0 / 86.3 / 83.6 | SIMULATED, in RTL (bit-exact, option CORTEX_EMBED), 3 draws | [new-word note, section 12](../hw/brain/experiments/month4/multiproto_dreams.md) |
| Learns its own senses without labels | 94.5 / 80.0 vs 95.0 / 79.2 with PC-learned detectors | SIMULATED, in RTL | [on-chip detectors](../hw/brain/experiments/month3/onchip_detectors.md) |
| Holds up in noise (sound) | trained clean, white noise at 20 / 10 / 5 dB: 63.9 / 54.0 / 46.6 with the noise floor vs 56.2 / 44.0 / 32.1 without | SIMULATED, 3 seeds | [input noise](../hw/brain/experiments/month4/input_noise.md) |; with the K = 5 slow table (5 stages, word alignment, clean / 20 / 10 / 5 dB): 82.7 / 75.2 / 64.4 / 52.3 vs 82.1 / 74.3 / 63.0 / 50.4 without it (SIMULATED, 3 seeds)
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

## Update 19-20 Oct (SIMULATED, 3 seeds; details in [redesign tests](../hw/results/brain_strict_redesign.md))

| Change | Result |
|---|---|
| Update margin 256, 1,500 dreams per old class, 1 night pass (was 32 / 6,000 / 2), no extra memory | staged / all at once: digits 94.1 / 97.0 -> **95.5 / 97.5**; clothing 80.8 / 86.0 -> **83.3 / 86.55**; spoken words clean 68.5 -> **73.35**, last-stage words 50.6 -> 57.1; RTL bit-exact at margin 256 |
| Training on noisy copies (words) | clean / 20 / 10 / 5 dB 69.2 / 62.7 / 47.5 / 33.5 -> 73.3 / 73.3 / 65.6 / 56.4, old words level; control "same clips twice" 71.7 / 64.5 / 52.2 / 36.8 |
| Few labels, digits | 5% labels 95.0 vs 95.5 fully labelled (2%: 94.7); clothing about 79 vs 83.3 at 10% labels (limited by label count) |
| RTL hooks (top margin, write counter) | bit-exact, 0 mismatches over 200 lines |
| Process fixes | detectors learned on the chip, sleep from the chip's own surprise count, weak-synapse pruning (19-30% of synapses kept) |

Open and failed items are listed honestly in Q&A 17.

## Say these limits first

1. Not the first continual-learning chip (HDC accelerators, Intel Loihi 2): what is new is the combination - dreams
   from counters, self-ending sleep, no multipliers, bit-exact from raw senses to decisions.
2. Learning everything at once (5 seeds; network = MLP 784-256-10 on the same codes / pictures): today's chip: digits 98.0 vs network 97.8; clothing 84.8 vs 87.3; words 84.7 vs 85.5
   (LOOK AGAIN costs 4-5 decisions' work per answer). **With the slow table (ASIC option, K = 5): digits 98.4, clothing 88.3, words 87.5, so level with that network on all
   three** (a floating-point MLP we trained on raw clothing pixels in one run reached 88.4 and a small CNN 89.2, so say "level with a small network", not "better").
   In stages the slow table (K = 5) lifts clothing from 78.4 to 81.6 (digits 95.0, words 82.6): it damps the recency bias; dream fidelity is still the other limit (prototype dreams: +0.7 more on the finer grid).
3. Few-shot from scratch: behind a small network at 5 examples per class (digits 62.8 vs 67.4). After shipping (new
   classes added to known ones) the chip keeps old and new; words from 1-5 recordings stay weak (new words 11-18% with new table rows; 13-40% with the embedding path, which needs a base vocabulary of about 15 known words; the GPU-style baseline we trained reaches 25-49%).
4. The layout energy is ~20-28x above the operation count: say "74x less energy per operation needed", not per chip.
5. Nothing measured on hardware yet.

Related: [Claims sheet](cortex_claims_sheet.md), [Overnight report](overnight_report_2026-10-15.md), [Project memory](PROJECT_MEMORY.md)
