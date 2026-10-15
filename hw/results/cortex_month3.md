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
| Bitstream (core + encoder + UART) | `hw/pnr_cortex/cortex_tangnano20k.fs.gz` | placed and routed (open-source flow): 46/46 BSRAM, 18,522 LUT4 (89%), 5,364 FF (34%), **0 multipliers**, 69.8 MHz max at a 27 MHz clock, no hold violations; raw images in, answers out, memory export/import, dream batches; board design bit-exact over UART (136 commands, 0 mismatches) |
| Host program | `hw/board/cortex_host.py` | runs the full day/night schedule; dry run matches the chip model exactly |
| Live demo | `hw/board/cortex_demo.py` | draw, teach, ask, sleep, test old digits; board or emulator |

Design fixes found on the way (each re-verified bit-exact): single-port list buffer (the open-source placer could not
place the dual-port RAM cells), all block-RAM inputs re-registered on the falling clock edge (removed 1,732 hold
violations), CLEAR command (memories can be wiped after a reset).

## Evidence gathered this month (SIMULATED unless marked)

- Harder protocol, 10 stages of one new class each (`hw/brain/stages10.py`): chip 93.5 / 78.7 / 70.5 (digits / (3-seed update 15 Oct: 93.0 / 78.7 / 71.2, `hw/brain/experiments/month4/stages10_seeds.log`)
  clothing / sound) vs a fine-tuned network 10.1 / 14.0 / 9.8, i.e. chance level.
- Seed spread, 5 stages (3 seeds): digits 94.4-94.8, clothing 77.7-78.7, sound 69.0-70.0 (`cortex_seeds_*.json`).
- Against the closest prior art, hyperdimensional computing ([details](cortex_vs_hdc.md)): ahead on digits (+2.2) and
  sound (+5.9), level on clothing, with less memory and ~1,000x fewer additions per example.
- Energy, ESTIMATED from operation counts and 45 nm per-operation energies ([details](cortex_energy_estimate.md)):
  ~74x less per decision than an 8-bit network; ~200x less per learned example including sleep.
- Self-regulated sleep: one rule for all three tasks (the night ends when dreams keep surprising the table).
- Split dreams (counts kept per pattern of 2-3 split bits): clothing 79.7 -> 82.6, digits 94.5 -> 95.6, sound 68.2 ->
  70.3 (float sim), but 4-8x the dream memory; needs the board's PSRAM. Not in the RTL yet.
- Few-shot: detectors learned from more data and wider pooling did not help. **Spread (population) codes did**: each
  active feature also lights the same feature in the neighbouring cells (3x3 OR) before matching
  (`experiments/month3/m4d.py`, float sim, 3 seeds). With episodic recall for few examples and the table for many:
  digits 40.5 / 61.3 / 86.6 at 1 / 5 / 20 examples per class vs network 39.1 / 67.4 / 81.2 (ahead at 1 and 20, behind
  at 5); clothing 42.8 / 53.3 / 70.2 vs 43.7 / 62.9 / 73.7 (level at 1, behind at 5 and 20). Not in the RTL.

- Sequence memory (the earlier lookup core) partly forgets across text domains: it keeps ~32-60% of what code taught
  it after reading prose ([note](../brain/experiments/month3/seq_forgetting.md)). Month 6 needs capacity or context memory.
- Context memory (frozen copy of the dream counts) fixes the new-condition limit on the exact chip model: rotated
  digits test, upright 44.8 -> 85.3 ([details](cortex_new_condition.md)); in the RTL as build option `CORTEX_CONTEXT`
  (bit-exact, ASIC only).

## Still open

1. A run on the real board and measured power (month 4; needs the user's Tang Nano and a USB power meter).
2. Learning the sensory detectors on the chip: **rule found in simulation** (one streaming pass over the first day's
   images matches the PC's detectors: digits 93.9 vs 95.0, clothing 79.2 vs 79.2,
   [note](../brain/experiments/month3/onchip_detectors.md)); in RTL as build option `ENC_LEARN`, bit-exact; hardware rule 94.5 / 80.0; ASIC only (the Tang Nano is full).
3. Split dreams via PSRAM (and sound on the board: 422 KB does not fit block RAM).
4. Few-shot with 1-5 examples (fusing episodic recall with the table helps at 20 examples, not at 5:
   [note](../brain/experiments/month3/fewshot_fusion.md)).
5. ASIC power: the first layout estimate (355 mW at 10% default activity, ~43 MHz) is far above the operation-count
   energy; clock gating, encoder memories in SRAM and a real switching activity are needed
   ([ASIC estimate](cortex_asic_estimate.md)).

Related: [Month 2 results](cortex_month2.md), [SPARK Cortex vs HDC](cortex_vs_hdc.md), [Energy estimate](cortex_energy_estimate.md),
[Board README](../board/README.md), [Results index](INDEX.md)
