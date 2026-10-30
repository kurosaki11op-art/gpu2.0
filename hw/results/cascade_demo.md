---
title: Cascade demo - chip first, stronger fallback on the flagged images (30 Oct 2026)
tags: [spark, demo, cascade, reject-flag, estimate]
---

# Cascade demo (30 Oct 2026)

One runnable script, [cascade_demo.py](../virtual/cascade_demo.py): image, then the L chip (L Cortex + L Deep) with its reject flag, then (if flagged) a stronger fallback, then the final answer with the energy accounting. The fallback is the strong reference CNN (four conv layers, augmentation, 12 epochs) standing in for a GPU or a person; its logits are stored in [fallback_cnn_logits.npy](../virtual/results/fallback_cnn_logits.npy). The reject threshold is calibrated the way a host would, on **unlabelled** data: the first 2,000 test images (margins only) set it, and accuracy is computed on the other 8,000. **SIMULATED accuracy; energy ESTIMATED from operation counts (45 nm project constants): chip 0.049 uJ per image, strong CNN 3.8 uJ (multiplies only) or 4.18 uJ (with weight and activation traffic); nothing is measured.** Outputs: [cascade_demo.json](../virtual/results/cascade_demo.json), [cascade_demo.csv](../virtual/results/cascade_demo.csv) (one row per image), [cascade_demo.png](../virtual/results/cascade_demo.png). Run: `python hw/virtual/cascade_demo.py --flag-share 0.15 [--rtl N]`.

## Result (8,000 evaluation images, 15% requested flagged share, threshold 2,889, 16.3% actually flagged)

| | accuracy | energy per image (ESTIMATED) |
|---|---|---|
| chip alone, every image answered | 89.59% | 0.05 uJ |
| strong CNN alone | 91.53% | 3.80 uJ (4.18 with traffic) |
| **cascade: chip answers, fallback on the flagged** | **91.24%** | **0.67 uJ (0.73 with traffic)**, 5.7x less than the CNN alone |
| chip on the images it answers | 95.09% | |
| on the flagged images: chip / fallback | 61.4% / 71.5% | |

Threshold sweep (evaluation images): 6% flagged 90.5% at 13.9x less energy; 11% flagged 91.2% at 8.0x; 21% flagged 91.4% at 4.4x; 30% flagged 91.6% at 3.2x; 40% flagged 91.6% at 2.4x; all flagged equals the CNN alone. Sensitivity to the chip's first-stage energy (the Cortex layout energy is estimated at 20 to 28 times its operation count): 0.049 / 0.3 / 1.0 uJ gives 5.7x / 4.1x / 2.3x less than the CNN alone.

## RTL in the loop (the real l_cortex_deep.v, its reject_t input and flag output)

First 200 images, threshold set at the 20th percentile of their margins, run through `run_check_full.py`: **the RTL's predictions are identical to the model's, 0 mismatches**; 40 images flagged by the RTL; chip alone 89.0%, chip on the answered 95.6%, cascade using the RTL's own flags 91.5%, strong CNN alone 93.5% on this sample. The 200-image sample is small (about 2 points of noise), and on it the cascade is 2 points below the CNN alone, more than the 0.3 point on the 8,000 images; the larger run is the better estimate.

## What this shows and does not show

1. A chip-first cascade gets within about 0.3 point of the strong CNN at about 5.7 times less estimated energy, when 15 to 20% of images go to the fallback; the flag costs the chip ten comparators.
2. It does not remove the fallback: the chip reduces its load by about 84%, it does not replace it.
3. Every energy figure is an operation-count estimate; the chip's layout energy and the CNN's real GPU energy are not measured (the GPU baseline on the founder's RTX 3050 and the board power are still to be taken).

Related: [Gap diagnosis](gap_diagnosis.md), [L Deep build](l_deep_build.md), [Results index](INDEX.md), [Virtual device](../virtual/README.md), [Project memory](../../docs/PROJECT_MEMORY.md)
