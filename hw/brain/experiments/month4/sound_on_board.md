---
title: Spoken words on the Tang Nano (same bitstream)
tags: [spark, cortex, sound, board]
---

# Spoken words on the Tang Nano's image chip (15 Oct 2026, 11:00 IST)

The full sound chip (10 receptor channels x 64 detectors, 422 KB) does not fit the Tang Nano. But a sound picture is
a 28x28 byte picture like a digit, so the board's image chip can learn words as they are: the PC turns each 1 s clip
into a sound picture with the chip's integer cochlea (noise floor on) and sends it; the board encodes it with its
fixed image receptors (> 50, > 150, ON, OFF) and 32 detectors per channel learned from sound pictures, then learns,
dreams and sleeps as for digits.

| Set-up | Sound after 5 stages | Code bits | Label |
|---|---|---|---|
| full sound chip (ASIC) | 71.2 (5 seeds) | 23,040 | SIMULATED |
| **Tang Nano image chip, today's bitstream** | **60.1** (60.3, 60.6, 59.4) | 4,608 | SIMULATED |
| same with sound-tuned receptor thresholds (110, 200; would need an RTL change) | 60.9 | 4,608 | SIMULATED |
| network, 5 stages (month 2) | 15.9 | | SIMULATED |

`sound_on_image_chip.py`, log `sound_on_image_chip.log`. Host support: `cortex_host.py --task sound` (needs Speech
Commands v0.01 in `<data>/speech` and scipy); its emulator run over the full data gives **60.0%** and matches the
chip model exactly (`host_sound_dryrun.log`). On the board this would be the first MEASURED sound result; optional
step 9 of the [board plan](../../../../docs/month4_board_plan.md).

Related: [Sound chip](../../../results/cortex_sound_chip.md), [Noise floor](noise_floor.md), [Month 4 experiments](INDEX.md)
