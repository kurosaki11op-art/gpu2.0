---
title: SPARK Cortex month 3 results
tags: [spark, cortex, results, rtl]
---

# SPARK Cortex month 3: from simulation to a placed-and-routed chip design

Month 3 of the plan (RTL bit-exact with the model) was reached early, during the night of 14-15 Oct.

## What exists now

| Piece | File | Status |
|---|---|---|
| Integer chip model (reference) | `hw/brain/cortex_int.py` | integers only, one pass per example, numba optional |
| Core RTL | `hw/rtl/cortex/cortex_core.v` | **bit-exact**: 0 mismatches over 5,058 compared lines x 2 configurations (`run_check_cortex.py`) |
| Tang Nano 20K top (UART) | `hw/board/cortex_board_top.v` | **bit-exact over UART**: 101 commands, 161 reply bytes, 0 mismatches (`check_cortex_board.py`) |
| Sensory encoder RTL | `hw/rtl/cortex/cortex_encoder.v` | **bit-exact** with `Features.encode` (0 mismatching images, digits and clothing), ~21,400 cycles (0.8 ms) per image, no multiplier or divider |
| Bitstream (core + encoder + UART) | `hw/pnr_cortex/cortex_tangnano20k.fs.gz` | placed and routed (open-source flow): 46/46 BSRAM, 18,335 LUT4 (88%), 5,604 FF (36%), **0 multipliers**, 66.2 MHz max at a 27 MHz clock, no hold violations; raw images in, answers out; board design bit-exact over UART (115 commands, 0 mismatches) |
| Host program | `hw/board/cortex_host.py` | runs the full day/night schedule; dry run matches the chip model exactly |
| Live demo | `hw/board/cortex_demo.py` | draw, teach, ask, sleep, test old digits; board or emulator |

Design fixes found on the way (each re-verified bit-exact): single-port list buffer (the open-source placer could not
place the dual-port RAM cells), all block-RAM inputs re-registered on the falling clock edge (removed 1,732 hold
violations), CLEAR command (memories can be wiped after a reset).

## Evidence gathered this month (SIMULATED unless marked)

- Harder protocol, 10 stages of one new class each (`hw/brain/stages10.py`): chip 93.5 / 78.7 / 70.5 (digits /
  clothing / sound) vs a fine-tuned network 10.1 / 14.0 / 9.8, i.e. chance level.
- Seed spread, 5 stages (3 seeds): digits 94.4-94.8, clothing 77.7-78.7, sound 69.0-70.0 (`cortex_seeds_*.json`).
- Against the closest prior art, hyperdimensional computing ([details](cortex_vs_hdc.md)): ahead on digits (+2.2) and
  sound (+5.9), level on clothing, with less memory and ~1,000x fewer additions per example.
- Energy, ESTIMATED from operation counts and 45 nm per-operation energies ([details](cortex_energy_estimate.md)):
  ~74x less per decision than an 8-bit network; ~200x less per learned example including sleep.
- Self-regulated sleep: one rule for all three tasks (the night ends when dreams keep surprising the table).
- Split dreams (counts kept per pattern of 2-3 split bits): clothing 79.7 -> 82.6, digits 94.5 -> 95.6, sound 68.2 ->
  70.3 (float sim), but 4-8x the dream memory; needs the board's PSRAM. Not in the RTL yet.
- Few-shot: still behind the network with 1-5 examples; detectors learned from more data and wider pooling did not fix
  it; with 20 examples the chip is level or ahead on digits.

## Still open

1. A run on the real board and measured power (month 4; needs the user's Tang Nano and a USB power meter).
2. Learning the sensory detectors on the chip (today they are learned on the PC, without labels, and loaded; the
   encoding itself runs on the chip).
3. Split dreams via PSRAM (and sound on the board: 422 KB does not fit block RAM).
4. Few-shot with 1-5 examples.

Related: [Month 2 results](cortex_month2.md), [SPARK Cortex vs HDC](cortex_vs_hdc.md), [Energy estimate](cortex_energy_estimate.md),
[Board README](../board/README.md), [Results index](INDEX.md)
