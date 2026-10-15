---
title: Overnight report 15 Oct 2026
tags: [spark, cortex, report]
---

# Overnight report (14-15 Oct 2026): what was done while you slept

Everything below is committed on `claude/zealous-turing-lsg561` and linked from the [home page](../README.md).
Labels: SIMULATED = our simulator or chip model; ESTIMATED = arithmetic on stated assumptions; nothing here is
MEASURED on hardware yet (that needs your board).

> [!NOTE]
> **Read this first (06:00 IST).** New since you went to sleep, in one breath: the bitstream now has dream batches
> and still fits (89% of logic); the chip can learn its own senses without labels (RTL, bit-exact); the fix for the
> "new condition" forgetting is in the RTL (ASIC build, bit-exact); the SKY130 layout gives an honest energy figure,
> ~0.2-0.26 uJ per decision after clock gating and a faster (pipelined) core, which means the "74x less energy" claim must be said as "per operation
> needed". Section 3b has the details; section 5 is what to run on the board today (`git pull` first: the host
> program changed).

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
| Bitstream `hw/pnr_cortex/cortex_tangnano20k.fs.gz` | placed and routed with timing met (89% of logic, 69.8 MHz max at 27 MHz; rebuilt 15 Oct with dream batches); 0 hardware multipliers used |

Details: [month 3 results](../hw/results/cortex_month3.md), [board README](../hw/board/README.md).

## 3. Evidence for the pitch (all SIMULATED or ESTIMATED)

- **Against the closest prior art** (hyperdimensional computing chips, which also never forget): ahead on digits
  (+2.2) and sound (+5.9), level on clothing, with less memory and ~1,000x fewer additions per example
  ([details](../hw/results/cortex_vs_hdc.md)).
- **Energy** (ESTIMATED, 45 nm figures): ~74x less per decision than an 8-bit network; ~200x less per learned example
  including sleep, counting the operations a decision needs ([details](../hw/results/cortex_energy_estimate.md));
  see limit 9 for the layout figure.
- **Memory transfer**: one chip learns 0-4, then (wiped) 5-9; memories merged on the PC and loaded: 91.4% on all ten
  digits after one short night.
- **Live demo**: draw a new symbol, teach it in 10 strokes (0.1 s), it is recognised and old digits are kept (90%).
- **ASIC (SkyWater 130 nm) estimate**: logic under 1 mm^2; ~18.8 mm^2 with open-source SRAM macros; the core is
  bit-exact with the real SRAM macro models ([details](../hw/results/cortex_asic_estimate.md)).
- **Few-shot narrowed** (simulation): with "spread" population codes the chip matches a small network with 1 example
  per class and beats it with 20 on digits; still behind with 5, and on clothing.

## 3b. Later the same night (after 02:00 IST)

- **Dream batches** (board command 45): up to 256 dreams per USB message, ~250x fewer round trips; a host/model
  schedule mismatch found and fixed (new check `hw/board/check_host_schedule.py`).
- **The chip can learn its own senses**: a streaming, label-free rule for the 128 sensory detectors, now in the
  encoder RTL as build option `ENC_LEARN`, bit-exact with its model. One pass over the first day's images: digits 94.5,
  clothing 80.0 after 5 stages, vs 95.0 / 79.2 with detectors learned on the PC (SIMULATED; ASIC build only, the Tang
  Nano is full) ([note](../hw/brain/experiments/month3/onchip_detectors.md)).
- **SKY130 layout estimate** (OpenROAD placement, clock tree, global routing): ~43 MHz; 355 mW for the logic, almost
  all of it the SRAM macros and clock tree being clocked every cycle. Per-memory clock gating (encoder memories and
  every SRAM port, 130 gates, bit-exact) and a lighter clock tree bring it to 33-47 mW; a pipelined core (264 instead of 1,243 cycles per decision,
  ASIC build only, bit-exact) brings a decision to ~0.18-0.26 uJ;
  the rest is mostly the clock tree of a spread-out die ([details](../hw/results/cortex_asic_estimate.md)).
- Few-shot fusion (episodic recall + table): small gains at 20 examples, the 5-example gap remains; not adopted.
- **Context memory in the RTL**: the frozen dream copy that fixes the new-condition limit is now a build option of
  the core (`CORTEX_CONTEXT`), bit-exact with the chip model, also with the SKY130 SRAM models. ASIC only (+36 SRAM
  macros); the Tang Nano has no room ([details](../hw/results/cortex_new_condition.md)).
- **Bitstream rebuilt with dream batches**: the first attempt did not fit (94% of logic, placement failed with four
  seeds and two placers); packing the encoder's code map 4 bits per word freed space: 89% LUT4, 69.8 MHz max at
  27 MHz, 0 multipliers, board design bit-exact. The host batches dreams by default; `--no-batch` works with an older
  bitstream.

## 3c. Daytime 15 Oct (after the status check)

- **Energy**: pipelined ASIC core ~0.18-0.26 uJ per decision; 45-62 uJ per learned example on digits (ESTIMATED);
  an "economy" dream budget gives ~3x less learning energy for 0.6-0.8 points (`--economy`).
- **Sound, noise removed**: a per-resonator noise floor in the cochlea lifts sound from 69.6 to 71.2 (5 seeds).
- **The chip hears raw sound**: cochlea and a general encoder in RTL; the whole chain (raw samples -> word decisions,
  with learning, dreams and a night) is bit-exact ([details](../hw/results/cortex_sound_chip.md)). A streaming
  cochlea listens live (no sample buffer: 1.52 mm^2 instead of 11.2 in SKY130).
- **Noise** (you asked to remove the noise that hurts accuracy): the cochlea's noise floor is the chip's noise
  protection - trained on clean speech and tested at 5 dB SNR it keeps 46.6% vs 32.1% without it; learning from some
  noisy examples adds +5 to +11 more in noise. Images: the chip already shrugs off pixel noise; an optional speckle
  filter adds +1.3 to +2.1 on clothing ([details](../hw/brain/experiments/month4/input_noise.md)).
- **Spoken words on your board's current bitstream**: 60.1% after 5 stages (PC cochlea -> sound picture -> chip);
  `cortex_host.py --task sound`, board plan step 9; a voice demo `cortex_sound_demo.py` (new words need many
  repetitions - honest numbers in [sound on board](../hw/brain/experiments/month4/sound_on_board.md)).
- Board-day helpers: `hw/board/preflight.py` (step 0) and `sh hw/run_all_checks.sh` (15 bit-exact checks, all pass).
- Tried and rejected today: lateral inhibition in the cochlea, retinal adaptation for images (within noise), few-shot
  replay and saccades. ASIC detailed routing did not converge (72k violations after 3 passes); floorplan needs rework.
- Few-shot: saccades rejected; top-2 voting small gain; the 5-example gap remains.

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
   85%), costs 2x dream memory; now in the RTL as an ASIC build option, bit-exact (no room on the FPGA)
   ([details](../hw/results/cortex_new_condition.md)).
7. The sequence memory (earlier lookup core) also partly forgets across text domains (keeps 32-60% of what it learned),
   so month 6 needs more capacity or the same context trick.
8. A second sensory layer (V2) did not improve accuracy; rejected.
9. **The energy claim needs care**: the SKY130 layout draws ~355 mW without clock gating and 35-49 mW with it;
   with the pipelined core ~0.18-0.26 uJ per decision, still far above the 9.4 nJ counted from the operations. The 74x is "per operation
   needed", not "per chip" (section 3b).

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
