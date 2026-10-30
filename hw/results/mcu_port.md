---
title: L algorithm and a reference CNN in portable C for an ESP32 - PC verification (30 Oct 2026)
tags: [spark, esp32, firmware, verification, measurement-prep]
---

# MCU port: verification done on a PC, energy measurement waiting for the meter (30 Oct 2026)

The founder ordered a USB power meter; with an ESP32 it gives a **MEASURED** energy per image for the algorithm in software on a real microcontroller (not the chip). Everything that needs no hardware is done and checked here; the ESP32 sketch and procedure are in [hw/mcu](../mcu/README.md). **Nothing has been run on an ESP32 yet.**

## What was checked (SIMULATED on a PC, bit-exact)

| item | result |
|---|---|
| **L chip algorithm in C** ([l_core.c](../mcu/l_core.c): encoder, counting table, dispatcher, L Deep clauses, reject flag; integer only; 145 KB of tables) against the model's expected values (`sys_exp.txt`, the file the RTL checks use) | **200 images: 0 mismatches** in routed flag, all ten final scores and prediction (38 routed) |
| **Small reference CNN in C** ([cnn_core.c](../mcu/cnn_core.c): int8 weights, uint8 activations, int32 accumulators, fixed-point requantisation, about 3.9 million multiply-adds, 50 KB of weights), trained 10 epochs and quantised ([gen_cnn.py](../mcu/gen_cnn.py)) | float 91.52%, **int8 91.52%** on the 10,000 test images (no loss from quantisation); the C code agrees with the numpy int8 model on **200 images, 0 mismatches** |
| time per image on this container's CPU (plain C, `gcc -O2`, no vectorisation or hand tuning in either) | L algorithm 0.21 ms, CNN 6.02 ms, about 29 times; **a time on a PC, not an energy figure and not an ESP32 figure** |

Both cores are deliberately plain; the CNN loops have bounds checks in the inner loops and could be sped up with tuning, so the 29x is a rough indication, not a claim. The ESP32 measurement (energy per image = (power running minus power idle) times time per image, three runs, meter model and resolution recorded) decides what the two methods really cost on one processor.

## Memory fit (ESP32: 520 KB SRAM, flash for constants)

L: 145 KB of constant tables (flash) plus about 11 KB of working arrays. CNN: 50 KB of weights plus about 47 KB of activation buffers. Both fit.

Related: [hw/mcu README](../mcu/README.md), [Cascade demo](cascade_demo.md), [Results index](INDEX.md), [Hardware index](../HARDWARE_INDEX.md), [Measurement protocol](../../docs/measurement_protocol.md)
