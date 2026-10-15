---
title: SPARK Cortex claims sheet
tags: [spark, cortex, pitch]
---

# SPARK Cortex claims sheet (15 Oct 2026)

One line per claim: what we can say, the number, its label, where it comes from, and the caveat to say with it.
MEASURED = real hardware; SIMULATED = our model or chip simulation; ESTIMATED = arithmetic on stated assumptions.
**Nothing is MEASURED on hardware yet**; the first board run (month 4) changes that.

## Safe to claim

| Claim | Number | Label | Source | Say with it |
|---|---|---|---|---|
| Learns new classes after deployment without forgetting old ones | 5 stages: digits 94.6, clothing 78.3, sound 69.4 (3-seed means) vs network 19.5 / 20.0 / 15.9 | SIMULATED (exact chip model) | `hw/results/cortex_month2.md`, `cortex_seeds_*.json` | holds for new classes; see the new-condition limit below |
| Even one class at a time | 10 stages: 93.5 / 78.7 / 70.5 vs network 10.1 / 14.0 / 9.8 | SIMULATED | `hw/results/cortex_month3.md` | |
| Stores no examples to do it | dreams are generated from 10-bit counters | design fact | `hw/rtl/cortex/cortex_core.v` | the replay baseline that stores 20 images/class reaches only 49.6 / 37.8 / 27.8 |
| Decides when to stop sleeping by itself | night ends after 256 dreams with > 2 surprises; one rule for all tasks | design fact + SIMULATED | `hw/results/cortex_month2.md` | |
| Knowledge moves between chips | two halves (0-4, 5-9) merged on the PC: 91.4% on all ten digits after one night | SIMULATED (emulator bit-exact with the chip) | `hw/board/cortex_transfer.py` | 300 examples per class; full-data merge 93.0 |
| No multiplier, no divider, no backprop | 0 of the FPGA's hardware multipliers used; dreams by rejection sampling | design fact | `hw/pnr_cortex/pnr.log` | the simulator itself uses numpy for speed |
| Fits a $25 FPGA, timing met | 46/46 block RAM, 89% LUT4, 69.8 MHz max at 27 MHz; raw images in | SIMULATED (place and route) | `hw/pnr_cortex/` | not yet run on the board |
| The chip design is verified | core, encoder, board top bit-exact with the model (0 mismatches); core also with SKY130 SRAM models | SIMULATED | `hw/rtl/cortex/run_check_*.py`, `hw/board/check_cortex_board.py` | |
| Memory 137x smaller than our first version | 11.5 MB -> 84 KB (images) | design fact | `hw/results/cortex_month2.md` | sound needs 422 KB (PSRAM) |
| Much less energy per decision | 9.4 nJ vs 696 nJ (8-bit network): ~74x; ~200x per learned example incl. sleep | ESTIMATED (45 nm op energies) | `hw/results/cortex_energy_estimate.md` | counts the work a decision needs only. SKY130 layout with clock gating: ~1.1-1.5 uJ per decision (33-47 mW, lighter clock tree), mostly clock tree; so say "per operation needed", not "per chip" |
| Can learn its own senses, without labels | one streaming pass over the first day's images: digits 94.5 vs 95.0 with PC-learned detectors, clothing 80.0 vs 79.2; RTL bit-exact | SIMULATED (integer chip model + RTL sim) | `hw/brain/experiments/month3/onchip_detectors.md` | ASIC build option only; the Tang Nano bitstream still loads detectors from the PC |
| Better than the closest prior art in this test | after 5 stages vs HDC: digits +2.2, sound +5.9, clothing +0.1 | SIMULATED | `hw/results/cortex_vs_hdc.md` | HDC staged retraining used 4,000 examples per stage |
| Small as a real chip | logic < 1 mm2 in SKY130; ~18.8 mm2 with open SRAM macros | ESTIMATED (synthesis + placement/global routing) | `hw/results/cortex_asic_estimate.md` | ~43 MHz after layout; no detailed routing or sign-off |

## Do NOT claim

| Tempting claim | Why not |
|---|---|
| "First chip that learns continuously" | HDC accelerators (Clo-HDnn, ImageHD) and Intel Loihi 2 exist (`docs/prior_art_cortex.md`) |
| "Never forgets" without qualification | a new condition of known classes (rotated digits) drops upright digits 95 -> 45%; fix (frozen dream memory, 85%) is in the RTL as an ASIC build option (bit-exact), not on the FPGA |
| "As accurate as deep learning" | all at once the network is ahead: 97.8 vs 96.6, 87.3 vs 83.7, 75.5 vs 71.1 |
| "Learns from one example like a child" | with spread codes (simulation only) it matches a small network at 1 example and beats it at 20 on digits, but is behind at 5, and behind on clothing at 5-20 |
| "Replaces GPUs / LLMs" | it is a small continual learner for sensors (images, sound); no language model |
| Any MEASURED power or speed on hardware | not yet measured |
| "74x less energy per chip" | the layout estimate (no clock gating) is far higher; the 74x is per operation needed |

Related: [Overnight report](overnight_report_2026-10-15.md), [Prior art](prior_art_cortex.md), [Project memory](PROJECT_MEMORY.md)
