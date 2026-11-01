---
title: ESP32 energy run with the USB meter - repeat timing and first current readings (1 Nov 2026, MEASURED, software on a microcontroller, not the chip)
tags: [spark, esp32, measurement, energy, usb-meter]
---

# ESP32 energy run (1 Nov 2026), in progress

**MEASURED**, software on an ESP32 dev board (ESP32 Dev Module, 240 MHz, Wi-Fi and Bluetooth off), Arduino IDE 2.3.10, sketch [`esp32_bench.ino`](../mcu/esp32_bench/esp32_bench.ino) with `MODE 0` (the L algorithm). Procedure: [hw/mcu README](../mcu/README.md). Meter: the amiciSense 6-in-1 USB-C tester, current display in steps of 0.01 A.

## Repeat of the timing (serial monitor at 115200 baud)

`MODE 0: 1000 images in 8,211,720 us = **8.212 ms per image**, 121.8 images per second; checksum 4500; accuracy on the embedded images 92.5%; **identical to the model on 1000 of 1000**; routed 150, flagged 275` (three consecutive reports: 8.213, 8.212, 8.212 ms).

- Bit-exactness on hardware holds again (1,000 of 1,000 identical, checksum 4500, the same routed and flagged counts as the [first run](esp32_first_run.md)).
- The earlier run gave 8.69 ms; this one 8.21 ms, **5.5% faster**, same checksum. The spread between runs or builds (toolchain version, board, cable) is therefore at least about 5%; I do not know which factor caused it.
- First serial attempt showed garbage because the monitor was set to 921,600 baud instead of 115,200 (no board fault).

## Meter readings so far (L algorithm running, board powered through the meter from a wall charger)

Three photos: 5.11 V and 0.05 A; 5.10 V and 0.06 A; 5.1 V and 0.05 A, i.e. about **0.26 to 0.31 W for the whole board** (voltage times current as displayed; the current display steps in 0.01 A, about 0.05 W, so each reading is uncertain by about 20%). **This is not yet a result:** the idle baseline (MODE 2) and the CNN (MODE 1) are not measured, and the 0.01 A step is too coarse to see the difference between modes. Plan: 30-minute runs per mode reading the meter's accumulated energy and timer, order idle, L algorithm, CNN, same board, cable and charger.

## What is still to do

1. MODE 2 (idle), MODE 0 and MODE 1, 30 minutes each, photograph the timer and the accumulated energy at the end.
2. `ms per image` for MODE 1 from the serial monitor (the earlier run gave 255.2 ms).
3. Energy per image = (power in the mode minus idle power) times time per image; report the gross figure beside it and the meter's resolution.

Related: [First run on a real ESP32](esp32_first_run.md), [Measurement protocol](../../docs/measurement_protocol.md), [Hardware results index](INDEX.md), [Hardware index](../HARDWARE_INDEX.md)
