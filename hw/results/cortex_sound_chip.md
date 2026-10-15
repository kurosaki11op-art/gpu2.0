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

Size: the sound core needs 23,040 x (50 + 100) bits of table and dream counters (~422 KB) - the Tang Nano's PSRAM or
an ASIC; the encoder's detector templates are 640 x 25 bits. Not placed and routed yet.

Related: [Cochlea in RTL](../brain/experiments/month4/cochlea_rtl.md), [Noise floor](../brain/experiments/month4/noise_floor.md), [Month 3 results](cortex_month3.md), [Results index](INDEX.md)
