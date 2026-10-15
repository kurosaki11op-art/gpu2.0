---
title: Removing input noise (sound gates, image speckle)
tags: [spark, cortex, experiment, noise]
---

# Removing the noise that affects accuracy (15 Oct 2026, afternoon)

The user asked to remove "the noise that affects accuracy and quality" completely. Input noise was attacked in both
senses; every variant is integer-only and measured on the exact integer chip model (5 stages, month-2 rule).

## Sound: beyond the noise floor (`noise_floor.py`, log `noise_gate.log`, 3 seeds, clean clips)

| Front end | Sound after 5 stages |
|---|---|
| noise floor alone (adopted earlier) | **72.0** |
| + noise gate: what is left below 2x the quiet level -> silence | 70.2 |
| + noise gate, 4x | 70.9 |
| + silence gate: frames 16x quieter than the loudest -> silence | 67.7 |
| + silence gate, 64x | 70.0 |

On clean clips every extra gate removes information the detectors use. The floor stays as it is. How the front ends
cope with real noise is measured separately (noisy test clips, below).

## Sound in real noise: trained clean, tested with white noise (`noisy_sound.py`, log `noisy_sound.log`, 3 seeds)

| Cochlea front end | Clean | 20 dB SNR | 10 dB SNR | 5 dB SNR |
|---|---|---|---|---|
| no noise removal | 69.9 | 56.2 | 44.0 | 32.1 |
| **noise floor (adopted)** | **72.0** | **63.9** | **54.0** | **46.6** |
| floor + gate 4x | 70.9 | 60.9 | 48.7 | 37.5 |
| stronger floor, 6x | 71.5 | 62.3 | 50.4 | 40.8 |
| stronger floor, 8x | 70.3 | 60.1 | 46.1 | 34.1 |
| floor + time smoothing 1-2-1 | 71.0 | 64.9 | 54.4 | 44.9 |
| floor + frequency smoothing 1-2-1 | 71.0 | 63.5 | 55.0 | 46.8 |

SIMULATED. The noise floor is what makes the chip hold up in noise: +7.7 points at 20 dB, +10.0 at 10 dB, +14.5 at
5 dB over no noise removal. Gates hurt here too. Noise is still costly (72.0 clean -> 46.6 at 5 dB): the floor
removes the noise's average level, not its fluctuations. Stronger floors (6x, 8x; `noisy_sound_2.log`) are worse
in noise as well: the 4x floor is best in every condition, clean and noisy. Smoothing after the floor
(`noisy_sound_3.log`) costs 1 point clean and moves the noisy results by less than 2 points either way - rejected.
**Result: the 4x noise floor is the noise removal; it stays as adopted.**

## Learning in noise (`noisy_train.py`, log `noisy_train.log`, 3 seeds)

Each training clip is heard once, clean or with white noise at 20 / 10 / 5 dB (one random condition per clip; here a
quarter of the clips clean); the detectors learn from the same mixed pictures. Same noisy test clips as above.

| Trained on | Clean | 20 dB | 10 dB | 5 dB | Mean of the four |
|---|---|---|---|---|---|
| clean clips (floor) | 72.0 | 63.9 | 54.0 | 46.6 | 59.1 |
| mixed clean / noisy clips (floor) | 67.0 | 68.7 | 64.0 | 58.0 | 64.4 |

SIMULATED. Hearing noisy examples while learning adds +4.8 to +11.4 points in noise and costs 5.0 on clean speech:
the noise has to be learned, not only filtered. Trade-off depends on where the chip will be used.

## Images: speckle removal by lateral support (`despeckle.py`, logs `despeckle.log`, `despeckle_5seeds.log`)

A receptor bit counts only if at least K of its 8 neighbours in the same channel are on.

| | Clothing, 3 seeds | Clothing, 5 seeds | Digits, 5 seeds |
|---|---|---|---|
| no speckle removal | 78.3 | 78.4 | 94.4 |
| K = 1 | 79.6 | 79.0 (4 of 5 better; one seed 76.2) | 94.5 |
| K = 2 | 78.9 | | 94.0 (3 seeds) |

SIMULATED. A small gain at no memory cost, but uneven across seeds; it needs an encoder RTL change on an FPGA at 89%
logic. Kept as a candidate, not adopted yet.

Related: [Noise floor](noise_floor.md), [Retinal adaptation](retina_adapt.md), [Month 4 experiments](INDEX.md)
