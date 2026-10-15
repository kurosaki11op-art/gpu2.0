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
