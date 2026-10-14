---
title: On-chip detector learning (streaming rule)
tags: [spark, cortex, experiment, detectors]
---

# The chip can learn its own sensory detectors from a stream (15 Oct 2026, 04:00 IST)

Question: today the 32 detectors per channel are learned on the PC (200,000 random patches, batch updates of 1,000)
and loaded into the chip. Can a rule the chip could run (one update per patch, in arrival order, no random sampling,
no stored patch set) learn equally good detectors?

Rule (`onchip_detectors.py`, integer only):
- seed the 32 detectors with the first 32 non-blank 5x5 patches (signs);
- for every non-blank patch in arrival order: winner = detector with the most agreeing bits (first max wins, the same
  comparison the encoder already does); its 25 six-bit counters step +1 / -1 toward the patch, clipped to +-31;
- after each pass, re-seed detectors that never won with the latest non-blank patches.

Data: the first day's images only (classes 0 and 1, first 12,000), the same as the PC fit. Then the exact 5-stage
integer chip model runs on codes from both detector sets.

| Detectors | Digits, stages 1-5 | Clothing, stages 1-5 |
|---|---|---|
| PC fit (current) | 99.9 / 96.7 / 95.9 / 95.8 / **95.0** | 98.6 / 90.5 / 85.2 / 77.2 / **79.2** |
| On-chip rule, 3 passes | 100 / 97.0 / 96.0 / 95.3 / **94.4** | 99.0 / 90.3 / 84.9 / 76.5 / **79.3** |
| On-chip rule, 1 pass (true stream, nothing stored) | 99.9 / 96.7 / 96.0 / 95.7 / **93.9** | 98.7 / 90.6 / 85.3 / 76.9 / **79.2** |

SIMULATED (integer chip model, one seed). Logs: `onchip_detectors_p3.log`, `onchip_detectors_p1.log`; JSON per run.

Result: a single streaming pass over the first day's images gives detectors as good as the PC's on clothing and 1.1
points lower on digits. **The whole chip, senses included, can learn on its own without labels.** Cost in hardware:
4 channels x 32 detectors x 25 counters x 6 bits = 19,200 bits of counters (2.4 KB) plus one add/clip per bit for the
winner; the winner search already exists in `cortex_encoder.v`.

## Hardware rule and RTL (same night, 05:00 IST)

The rule above re-reads its seed patches and re-seeds once per pass. The chip version (`hw/brain/detector_learn.py`)
is defined for a stream: a window used as a seed is not learned from; re-seeding is a separate command (e.g. at the
end of a day) and takes windows from a ring of the last 32 learned ones. Accuracy with this exact rule, one pass over
the first day's 12,000 images, one reseed at the end (`onchip_detectors_hw.py`, log `onchip_detectors_hw.log`):

| Detectors | Digits after 5 stages | Clothing after 5 stages |
|---|---|---|
| PC fit (current) | 95.0 | 79.2 |
| Chip rule (hardware version) | **94.5** | **80.0** |

SIMULATED (integer chip model, one seed). Reseeding every 1,000 images instead: 94.5 / 80.0 (no change).

RTL: `cortex_encoder.v` built with `ENC_LEARN` (inputs `learn`, `lclear`, `reseed`; 16,770 cycles to learn from one
image, 32 cycles per reseed). Check `hw/rtl/cortex/run_check_encoder_learn.py` compares all 128 x 25 counters and the
codes of test images encoded with the learned detectors: **0 mismatches** on digits (200 images, reseed after 100) and
clothing, and on a run with frequent reseeds (21 detectors reseeded); the normal build still passes
`run_check_encoder.py` (log `check_encoder_learn.log`). SIMULATED (RTL simulation). Cost: 22,528 bits of extra state
(counters, ring, win marks), in flip-flops as written; ASIC only for now (the Tang Nano build is full).

Related: [Month 3 results](../../../results/cortex_month3.md), [Few-shot fusion](fewshot_fusion.md), [Month 3 experiments](INDEX.md)
