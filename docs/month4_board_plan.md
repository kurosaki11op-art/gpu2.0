---
title: Month 4 board plan
tags: [spark, cortex, plan, board]
---

# Month 4: the first MEASURED results on the Tang Nano 20K

Goal: turn the simulated results into measured ones on your board, in one sitting of about 2 hours.
Everything runs from `D:\gpu2.0` after `git pull`.

## What you need

- Tang Nano 20K + USB-C cable; the PC with Python 3.
- A USB power meter (inline "USB tester" with a display, about Rs 300-800) between the PC and the board.
  Optional: the INA219 + ESP32 logger already in `hw/board/esp32_ina219_logger` for logged readings.
- `python -m pip install -r hw\board\requirements.txt`; `openFPGALoader` (or the Gowin Programmer).

## Steps and what each one proves

| # | Run | Proves | Expected (from simulation) |
|---|---|---|---|
| 1 | `python hw\board\cortex_host.py --dry-run --per-class 300 --data D:\cortex_data` | the PC side works | stage 5 about 0.91; "matches the integer chip model exactly: True" |
| 2 | Program `hw\pnr_cortex\cortex_tangnano20k.fs` (unzip the `.gz`); check the pin TODOs in `tangnano20k.cst` | board configured | LEDs: heartbeat blinking |
| 3 | `cortex_host.py --port COMx --per-class 300 --data D:\cortex_data` | **the chip learns in stages without forgetting, MEASURED** | the same numbers as step 1, digit for digit (the chip is bit-exact) |
| 4 | same with `--onchip-encode` | **the chip senses raw pixels itself** | identical to step 3 |
| 5 | `cortex_transfer.py --port COMx --per-class 300` | **memory transfer between sessions, MEASURED** | 0-4 alone ~0.51, merged ~0.79, after one night ~0.91 |
| 6 | `cortex_bench.py --port COMx --seconds 30` with the USB meter | **power and energy per operation, MEASURED** | see below |
| 7 | `cortex_demo.py --port COMx --preload 200 --classes 0-7` | live demo works on hardware | teach a symbol in ~10 strokes |
| 8 (optional) | step 3 with `--economy` | the energy / accuracy dial on hardware | ~3x fewer dreams, about 0.5-1 point lower |

If step 3 differs from step 1 in any digit, stop and send me the output: it means a hardware or link problem (wrong pin,
UART noise), because the design is bit-exact in simulation.

## Reading the power numbers honestly

`cortex_bench.py` prints operations per second for each phase and asks for the meter reading. Energy per operation
above the link cost = (P_phase - P_link) / (operations per second).

- The FPGA board draws most of its power just being on (regulators, FPGA static power, the USB bridge). Expect
  P_idle around 0.3-0.6 W and the differences between phases to be small (milliwatts). A cheap meter with 0.01 W
  resolution may not see them; then report "below the meter's resolution" rather than a number.
- The UART limits speed (each command waits for a round trip), so operations per second are set by the link, not the
  chip. The core itself needs ~1,600 cycles per decision (~60 us at 27 MHz) and ~25,000 per dream (~1 ms).
- These are FPGA board numbers. They do not test the ASIC energy estimate (`hw/results/cortex_energy_estimate.md`),
  which assumes a custom chip; say so when presenting them.

## After the session

Send me the console output of steps 3-6 and the CSV from step 6. I will write them into the results as MEASURED,
next to the simulated numbers, and update the claims sheet.

Related: [Overnight report](overnight_report_2026-10-15.md), [Board README](../hw/board/README.md), [Claims sheet](cortex_claims_sheet.md)
