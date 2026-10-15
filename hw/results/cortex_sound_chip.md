---
title: SPARK Cortex sound chip (raw sound in, RTL)
tags: [spark, cortex, results, sound, rtl]
---

# The chip hears raw sound and learns words: whole chain in RTL, bit-exact (15 Oct 2026)

`hw/rtl/cortex/cortex_sound_top.v` joins three verified blocks:

| Block | File | What it does | Check |
|---|---|---|---|
| Cochlea | `cortex_cochlea.v` | 1 s of 16 kHz samples -> 28 shift-add resonators -> frame sums -> per-resonator noise floor -> 28x28 sound picture; 1.35 M cycles | `run_check_cochlea.py`: 10 clips, 0 mismatches |
| Sensory encoder | `cortex_encoder_gen.v` | 10 receptor channels x 64 label-free detectors, 2x2 pooling -> 23,040-bit code; 162k cycles | `run_check_encoder_gen.py`: 20 sound + 20 image pictures, 0 mismatches |
| Learning core | `cortex_core.v` (NB 23,040) | table, dream counters, dreams, night, decisions | `run_check_cortex.py` (images) |

Whole-chain check `hw/rtl/cortex/sound/run_check_sound_chain.py`: the chip hears 12 raw clips; stage 1 learns the
words "down"/"go" (2 clips each), stage 2 learns "left"/"no" with one daydream per clip, interleaved dreams of the
old words and a night; then it hears 4 test clips and decides. Compared with the Python chain (integer cochlea ->
`Features.encode` -> integer chip model): every update flag, dream length and decision, and the final table, dream
counters and counts - **23,082 lines, 0 mismatches** (`hw/brain/experiments/month4/check_sound_chain.log`).
SIMULATED (RTL simulation). The 4 test decisions (2 right) only show the chain runs: 2 clips per word is far too few
to measure accuracy; accuracy comes from the exact model on the full data: **71.2% after 5 stages** (5 seeds, with
the noise floor; `hw/brain/experiments/month4/noise_floor.md`).

## Size in SkyWater 130 nm (ESTIMATED, synthesis only)

| Part | How counted | Area |
|---|---|---|
| Core memories: table 50 bits, dream counters 100 bits, list 15 bits per code bit, 23,040 code bits | 45 banks x 7 columns = **315** open 2 KB SRAM macros (`sram_array`); the image chip needs 63 | ~90 mm^2 |
| Cochlea, every buffer as flip-flops (`hw/asic/sound/stat_cochlea.txt`) | 288k flip-flops, mostly the stored second of sound (256 kbit) | 11.2 mm^2 (upper bound) |
| Sound encoder, every buffer as flip-flops (`stat_encoder.txt`) | 53k flip-flops (code map, 640 detector templates, receptor map) | 2.1 mm^2 (upper bound) |
| Core logic | as the image core | < 1 mm^2 |

Reading: memory dominates, as in the image chip, and the open-source macros are large for what they hold (~3.8 Mbit
in ~90 mm^2). Two cheaper routes, not built: (1) a streaming cochlea - 28 shift-add resonators running side by side
on each sample as it arrives, so the second of sound never needs storing; (2) dense SRAM (a commercial 130 nm
compiler stores several times more per mm^2). The Tang Nano 20K's 8 MB PSRAM holds the core memories, but a PSRAM
controller is not written.

Related to the size: the noise floor adds 4 x 32-bit registers per resonator pass and 28 floor registers.

Related: [Cochlea in RTL](../brain/experiments/month4/cochlea_rtl.md), [Noise floor](../brain/experiments/month4/noise_floor.md), [Month 3 results](cortex_month3.md), [Results index](INDEX.md)
