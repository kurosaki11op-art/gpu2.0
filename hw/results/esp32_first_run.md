---
title: First run on a real ESP32 - the L algorithm, bit-exact, 25 ms per image (31 Oct 2026)
tags: [spark, esp32, measured, firmware]
---

# First run on a real ESP32 (31 Oct 2026)

The founder flashed `hw/mcu/esp32_mode0` (an ESP32 Dev Module on COM7, 240 MHz, Wi-Fi and Bluetooth off) and sent the serial output:

`1000 images in 25049939 us = 25.050 ms per image, 39.9 images per second; checksum 4500; identical to the model on 1000 of 1000; accuracy on the embedded images 92.5%; routed 150, flagged 275`

**MEASURED on a real ESP32 (software, not the chip):** the whole L pipeline (encoder, counting table, dispatcher, L Deep clauses, reject flag) runs bit-exactly: 1,000 of 1,000 predictions identical to the model, the checksum and the routed (150) and flagged (275) counts identical to the PC run. Time: **25.05 ms per image, 39.9 images per second.** This is a time, not an energy; the USB meter is still to come.

Reading: the PC runs the same code in about 0.21 ms, about 120 times faster. The likely cause is the encoder's bit counting: the ESP32's Xtensa core has no popcount instruction and `__builtin_popcount` calls a slow library routine, about 76,000 times per image (576 spots, four channels, 33 counts each). Fix applied the same day: a shift, mask and add version (no multiply, no table) in `l_core.c`, verified bit-exact on the PC (200 images, 0 mismatches; the stand-in run of the sketch 1,000 of 1,000 identical, checksum 4500). The ESP32 time with it is to be remeasured; the 25.05 ms figure is kept here as the before value. The CNN baseline (MODE 1) is expected to be far slower on the ESP32 and is set to one pass of 40 images per report line.

Related: [MCU port](mcu_port.md), [hw/mcu README](../mcu/README.md), [Results index](INDEX.md)
