---
title: Overnight report 15 Oct 2026
tags: [spark, cortex, report]
---

# Overnight report (14-15 Oct 2026): what was done while you slept

Everything below is committed on `claude/zealous-turing-lsg561` and linked from the [home page](../README.md).
Labels: SIMULATED = our simulator or chip model; ESTIMATED = arithmetic on stated assumptions; nothing here is
MEASURED on hardware yet (that needs your board).

## 1. Month 2 finished: memory shrunk to chip size, one rule for every task

- Memory for images **11.5 MB -> 84 KB (137x smaller)**; fits the Tang Nano 20K's on-chip RAM. Sound 28 MB -> 422 KB.
- One rule for digits, clothing and spoken words: the fast table always decides; dreams come from tiny counters
  (synaptic scaling); **the chip ends its own night** when dreams stop agreeing with what the day taught.
- Exact integer chip model, every example seen once, after 5 learning stages (3 seeds):
  **digits 94.6, clothing 78.3, sound 69.4** vs a normal neural network 19.5 / 20.0 / 15.9.
- Harder test, 10 stages of one new class each: **93.5 / 78.7 / 70.5** vs network 10.1 / 14.0 / 9.8.
- Lost vs month 1 (big memory): 2.6 / 7.6 / 2.1 points in stages. Main cause: dreams with independent bits.
  "Split dreams" win back ~3 points on clothing but need 4-8x memory (the board's PSRAM; not built).
- Details: [month 2 results](../hw/results/cortex_month2.md), [month 2 log](../hw/results/cortex_month2_log.md).

## 2. Month 3 done early: the chip design exists and is verified

| Piece | Status |
|---|---|
| Core (learn, dream, sleep, decide) `hw/rtl/cortex/cortex_core.v` | bit-exact with the chip model (0 mismatches) |
| Sensory encoder (eyes) `hw/rtl/cortex/cortex_encoder.v` | bit-exact (0 mismatching images); the chip now takes raw pixels |
| Memory transfer (export / import what the chip knows) | bit-exact over UART (0 mismatches) |
| Tang Nano 20K top `hw/board/cortex_board_top.v` | bit-exact over UART: 131 commands, 0 mismatches |
| Bitstream `hw/pnr_cortex/cortex_tangnano20k.fs.gz` | placed and routed with timing met (93% of logic, 73 MHz max at 27 MHz); 0 hardware multipliers used |

Details: [month 3 results](../hw/results/cortex_month3.md), [board README](../hw/board/README.md).

## 3. Evidence for the pitch (all SIMULATED or ESTIMATED)

- **Against the closest prior art** (hyperdimensional computing chips, which also never forget): ahead on digits
  (+2.2) and sound (+5.9), level on clothing, with less memory and ~1,000x fewer additions per example
  ([details](../hw/results/cortex_vs_hdc.md)).
- **Energy** (ESTIMATED, 45 nm figures): ~74x less per decision than an 8-bit network; ~200x less per learned example
  including sleep ([details](../hw/results/cortex_energy_estimate.md)).
- **Memory transfer**: one chip learns 0-4, then (wiped) 5-9; memories merged on the PC and loaded: 91.4% on all ten
  digits after one short night.
- **Live demo**: draw a new symbol, teach it in 10 strokes (0.1 s), it is recognised and old digits are kept (90%).
- **ASIC (SkyWater 130 nm) estimate**: logic under 1 mm^2; ~18.8 mm^2 with open-source SRAM macros; the core is
  bit-exact with the real SRAM macro models ([details](../hw/results/cortex_asic_estimate.md)).
- **Few-shot narrowed** (simulation): with "spread" population codes the chip matches a small network with 1 example
  per class and beats it with 20 on digits; still behind with 5, and on clothing.

## 4. Honest limits (say these before a judge does)

1. **Not the first chip that keeps learning**: HDC accelerators and Intel Loihi 2 also do continual learning without
   backprop ([prior art](prior_art_cortex.md)). Our combination (dreams from counters, self-ending sleep, no
   multipliers, bit-exact on a $25 FPGA) is what is new.
2. Few-shot: behind a small neural network with 5 examples per class (and on clothing); level or ahead with 1 and 20 on
   digits after the spread-code fix (simulation only, not in the chip).
3. Accuracy all-at-once is below a neural network (digits 96.6 vs 97.8, clothing 83.7 vs 87.3, sound 71.1 vs 75.5).
4. Nothing is measured on hardware yet. Energy numbers are estimates.
5. The FPGA is nearly full (about 90% of logic); bigger versions need the PSRAM or a bigger FPGA.
6. **New conditions of known classes** (e.g. the same digits rotated): the chip forgets the old condition (digits
   upright 95 -> 45%). Fix found and confirmed on the exact chip model (keep a frozen copy of the dream memory: back to
   85%), costs 2x dream memory; not in the RTL yet ([details](../hw/results/cortex_new_condition.md)).
8. The sequence memory (earlier lookup core) also partly forgets across text domains (keeps 32-60% of what it learned),
   so month 6 needs more capacity or the same context trick.
7. A second sensory layer (V2) did not improve accuracy; rejected.

## 5. What you can do today (about 30 minutes)

1. `git pull`, then work in `D:\gpu2.0`.
2. `python -m pip install -r hw\board\requirements.txt` (numpy, pyserial; numba makes dry runs fast).
3. Dry run, no board: `python hw\board\cortex_host.py --dry-run --per-class 300 --data D:\cortex_data`
   expected: about 0.91 at stage 5 and "emulator matches the integer chip model exactly: True".
4. Program the board: unzip `hw\pnr_cortex\cortex_tangnano20k.fs.gz`, then
   `openFPGALoader -b tangnano20k cortex_tangnano20k.fs` (check the pin TODOs in `hw\board\tangnano20k.cst` first).
5. Real run: `python hw\board\cortex_host.py --port COM5 --per-class 300 --data D:\cortex_data` (COM port from
   Device Manager). It must print the same numbers as the dry run. If it does, that is the first MEASURED result.
6. Then: `cortex_transfer.py --port COM5` (memory transfer) and `cortex_demo.py --port COM5` (live drawing demo).
7. For month 4: a USB power meter between the PC and the board, then `cortex_bench.py` (full plan:
   [month 4 board plan](month4_board_plan.md)).

Related: [Project memory](PROJECT_MEMORY.md), [Journal](journal.md), [Home](../README.md)
