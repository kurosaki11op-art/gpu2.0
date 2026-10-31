---
title: L algorithm and a reference CNN on an ESP32 - firmware and the USB-meter measurement procedure
tags: [spark, esp32, measurement, energy, firmware]
---

# L on a microcontroller (hw/mcu), 30 Oct 2026

Purpose: turn the energy claim into a **MEASURED** number on a real device, with equipment the founder has ordered (a USB power meter) and an ESP32. What is measured is **the algorithm in software on a microcontroller, not the chip**: the L pipeline (encoder, counting table, dispatcher, L Deep clauses, reject flag) in portable C against a small int8 CNN in portable C, on the same ESP32, same clock, same images. It says how much energy the two methods cost on one real processor; it does not say what the custom chip would cost.

## Files

| file | what |
|---|---|
| `l_core.c`, `l_core.h` | the L chip algorithm in C, integer only, 145 KB of tables; bit-exact with the RTL model |
| `cnn_core.c`, `cnn_core.h` | the small reference CNN (conv 32, conv 64, fully connected), int8 weights, uint8 activations, int32 accumulators, about 3.9 million multiply-adds per image |
| `gen_tables.py`, `gen_cnn.py` | generate `l_tables.h`, `l_testimg.h`, `test_images.bin` and `cnn_tables.h` (the CNN is trained and quantised here) |
| `main_pc.c`, `main_pc_cnn.c` | PC checks: L core against the model's expected scores, CNN against the numpy int8 model |
| `esp32_bench/esp32_bench.ino` | the ESP32 sketch: MODE 0 = L algorithm, 1 = CNN, 2 = idle baseline (includes the cores from the parent folder; use PlatformIO or copy the files next to it) |
| `esp32_mode1/`, `esp32_mode2/` | self-contained Arduino sketch folders for MODE 1 (the CNN: esp32_mode1.ino, cnn_core.c, cnn_core.h, cnn_tables.h, l_testimg.h) and MODE 2 (idle baseline: one file); open each folder the same way as esp32_mode0 |
| `esp32_mode0/` | a self-contained Arduino sketch folder for MODE 0 only (L algorithm): esp32_mode0.ino, l_core.c, l_core.h, l_tables.h, l_testimg.h; open this folder in the Arduino IDE; its logic was compiled and run on a PC against an Arduino stand-in, 1,000 of 1,000 identical to the model |

PC checks (done): L core 200 images, 0 mismatches against the model in routed flag, all ten scores and prediction; the CNN checks are in the results note.

## Measurement procedure (to run when the meter arrives)

1. Flash the sketch three times with `MODE` 0, 1 and 2 (same board, same USB cable, same power source for all three; Wi-Fi and Bluetooth are off in the sketch; CPU fixed at 240 MHz).
2. Put the USB meter between the power source and the ESP32 board. Note the meter model and its resolution and sampling rate.
3. For each mode: let it run for 60 seconds so the reading settles, then record the meter's average power over at least 60 further seconds (or the accumulated energy in mWh over a timed window), three times. Record the board temperature if the meter shows it.
4. From the serial monitor take the printed `ms per image` and the checksum (it must stay the same across reports; for MODE 0 the line also says how many predictions are identical to the model: 100%).
5. Energy per image: **E = (P_mode - P_idle) x time per image**, where P_idle is MODE 2. Also report the gross figure P_mode x time per image. Report the three runs as a mean with the spread.
6. What the meter includes: the whole board (regulator, USB-to-serial chip, LED); the net figure subtracts the idle mode, the gross figure does not. Use the same board for all three modes.
7. Record the results in a note with the label MEASURED (microcontroller, software) and never as chip energy.

Expected from the operation counts (an expectation, not a result): the L pipeline is about 4 times faster on the PC than the CNN would be if multiplies dominate; on an ESP32 the encoder (about 0.2 ms on a PC) is the main cost of L; the measurement decides.

Related: [Hardware index](../HARDWARE_INDEX.md), [Cascade demo](../results/cascade_demo.md), [Measurement protocol](../../docs/measurement_protocol.md), [Project memory](../../docs/PROJECT_MEMORY.md)
