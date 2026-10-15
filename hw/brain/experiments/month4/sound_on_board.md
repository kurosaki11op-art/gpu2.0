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

## Live sound demo (`hw/board/cortex_sound_demo.py`)

Teach a new word by saying it (microphone via `sounddevice`, or wav files), ask, sleep, test. Headless check
(emulator, bit-exact with the chip; words 0-7 pre-taught from 300 clips each, then word 8 "stop" taught from
dataset clips of many different speakers, a short night, then unseen clips):

| Clips used to teach "stop" | New word, unseen clips | All known words | Label |
|---|---|---|---|
| (before) | - | 61.0% (words 0-7) | SIMULATED |
| 10 | 15.5% | 51.2% | SIMULATED |
| 30 | 24.7% | 56.8% | SIMULATED |
| 60 | 44.0% | 57.8% | SIMULATED |

Honest reading: a new word needs many repetitions on this small code (the few-shot limit again, harder for sound
than for drawn digits, where 10 strokes gave 73.5%). One person repeating their own word is likely easier than many
speakers, but that is not tested. For the pitch, the digits drawing demo is the stronger live demo; the sound demo
shows the same chip learning words and should be introduced with these numbers.

Rehearsal (more daydreams of the new word after each taught clip; `new_word_rehearsal.py`, log
`new_word_rehearsal.log`, one run each): 10 clips -> 14.7 / 20.0 / 18.7% (1 / 5 / 20 daydreams); 30 clips -> 24.7 /
44.0 / 24.7%, the 44% at the cost of the old words (49%). Inconsistent, no reliable gain - not adopted. Teaching a new
spoken word on the small 4,608-bit code stays the weak spot.

Related: [Sound chip](../../../results/cortex_sound_chip.md), [Noise floor](noise_floor.md), [Month 4 experiments](INDEX.md)
