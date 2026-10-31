---
title: First run on a real ESP32 - the L algorithm, bit-exact, 25 ms per image (31 Oct 2026)
tags: [spark, esp32, measured, firmware]
---

# First run on a real ESP32 (31 Oct 2026)

The founder flashed `hw/mcu/esp32_mode0` (an ESP32 Dev Module on COM7, 240 MHz, Wi-Fi and Bluetooth off) and sent the serial output:

`1000 images in 25049939 us = 25.050 ms per image, 39.9 images per second; checksum 4500; identical to the model on 1000 of 1000; accuracy on the embedded images 92.5%; routed 150, flagged 275`

**MEASURED on a real ESP32 (software, not the chip):** the whole L pipeline (encoder, counting table, dispatcher, L Deep clauses, reject flag) runs bit-exactly: 1,000 of 1,000 predictions identical to the model, the checksum and the routed (150) and flagged (275) counts identical to the PC run. Time: **25.05 ms per image, 39.9 images per second.** This is a time, not an energy; the USB meter is still to come.

Reading: the PC runs the same code in about 0.21 ms, about 120 times faster. The likely cause is the encoder's bit counting: the ESP32's Xtensa core has no popcount instruction and `__builtin_popcount` calls a slow library routine, about 76,000 times per image (576 spots, four channels, 33 counts each). Fix applied the same day: a shift, mask and add version (no multiply, no table) in `l_core.c`, verified bit-exact on the PC (200 images, 0 mismatches; the stand-in run of the sketch 1,000 of 1,000 identical, checksum 4500). The ESP32 time with it is to be remeasured; the 25.05 ms figure is kept here as the before value. The CNN baseline (MODE 1) is expected to be far slower on the ESP32 and is set to one pass of 40 images per report line.

## Second and third run (31 Oct 2026)

**Version 2 (shift-add popcount):** MEASURED 18.34 ms per image, 54.5 images per second (from 25.05 ms), checksum 4500, 1,000 of 1,000 identical to the model. Two upload mix-ups cost a round trip: the IDE first ran a mixed build (new `l_core.c`, old sketch banner), so the stage timing was missed; the per-stage line then arrived with the correct build.

**MEASURED per-stage time on the ESP32 (version 2, 18.53 ms per image with the timing on):** receptors 0.68 ms (4%), **detectors 16.36 ms (88%)**, stage 1 0.86 ms (5%), stage 2 0.62 ms averaged over all images (about 4.1 ms per routed image, 150 of 1,000 routed). The detectors take about 3.9 million cycles per image, about 53 cycles per template match (74,000 matches).

**Version 3 (table popcount, -O3):** the Arduino ESP32 build compiles with -Os; `l_core.c` and `cnn_core.c` now ask for -O3 and the bit count is two lookups into an 8 KB table. PC checks: L core 200 of 200 bit-exact (0.09 ms per image on the PC), CNN 200 of 200 identical to the numpy int8 model (1.46 ms per image on the PC with -O3; it was 6.02 ms at -O2, so the PC ratio between the two is now about 16x). The ESP32 time with version 3 is to be measured. Self-contained sketch folders for the meter day: `esp32_mode0` (L), `esp32_mode1` (CNN), `esp32_mode2` (idle).

## Version 3 results on the ESP32 (31 Oct 2026, MEASURED, software, not the chip)

| | time per image | images per second | checks |
|---|---|---|---|
| L algorithm, version 1 (library popcount) | 25.05 ms | 39.9 | 1,000 of 1,000 identical to the model |
| L algorithm, version 2 (shift-add popcount) | 18.53 ms | 54.0 | same |
| **L algorithm, version 3 (table popcount, -O3)** | **8.69 ms** | **115.1** | same; checksum 4500; routed 150, flagged 275 |
| **small int8 CNN, version 3 (-O3)** | **255.2 ms** | **3.92** | checksum 180 (equals the PC run); accuracy on the 40 embedded images 92.5% |

Per stage, version 3: receptors 0.47 ms, detectors 6.64 ms (76%), stage 1 0.88 ms, stage 2 0.69 ms averaged over all images. **Measured time ratio: the CNN takes 29 times longer per image than the L algorithm on the same processor, both built with -O3.** The energy ratio is not measured yet: with similar power while the processor is busy it would be close to the time ratio (an expectation, not a result); the USB meter decides. Mode 2 (idle) runs and prints "idle". The 40-image accuracies (both 92.5%) are a tiny sample; on the 10,000-image set the algorithm gets 89.7% and this CNN 91.5%.

Related: [MCU port](mcu_port.md), [hw/mcu README](../mcu/README.md), [Results index](INDEX.md)
