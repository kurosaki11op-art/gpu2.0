---
title: Where L Cortex loses on clothing (24 Oct 2026)
tags: [l, clothing, limits, results]
---

# Per-class view of the clothing limit (SIMULATED, exact integer slow-table model, stride-1 code, look-again, ONE seed)

`hw/brain/experiments/month5/clothing_confusion.py`, log `clothing_confusion.log`. All at once 88.9 %, five stages 81.4 % (seed 1; the five-seed means in the memory file are a little lower, so treat per-class numbers as indicative).

| Class | All at once | 5 stages | Main confusion (all at once -> staged) |
|---|---|---|---|
| Shirt | 63.1 | 61.7 | T-shirt (155 of 1000) -> Coat |
| Pullover | 82.6 | 72.1 | Coat -> Shirt |
| Coat | 82.6 | 77.3 | Shirt |
| T-shirt | 88.2 | 70.9 | Shirt (53 -> 157) |
| Dress | 88.7 | 78.6 | Shirt |
| Trouser | 97.8 | 85.6 | Dress (14 -> 70) |
| Sandal | 97.0 | 85.7 | Sneaker (22 -> 104) |
| Sneaker | 96.4 | 84.4 | Boot (20 -> 151) |
| Bag / Boot | 97.7 / 95.1 | 98.8 / 98.6 | - |

**Reading.**
1. The all-at-once limit is the upper-body garments: Shirt, Pullover, Coat and T-shirt are separated only by fine texture and sleeve/collar detail that a 4,608-bit pooled code smooths away. This is a feature limit, not a memory limit (earlier work: a float readout on the same code reaches 87.9 %).
2. The staged loss (about 7.5 points here) falls on classes that are similar to a class from another stage: Trouser/Dress, Sandal/Sneaker/Sneaker/Boot, T-shirt/Shirt. A class learned in an early stage is only held by its dreams, and dreams of similar pairs blur together. This is the replay-fidelity limit already recorded.
3. Direction for development (not tried yet, so NO result): finer features for the upper-body group only (more detectors at higher resolution, spending the extra memory only where the confusion is), and pair-aware dreaming (dream the nearest other-stage class together with each old class). Both must pass the no-regression rule before adoption.

**Limits.** One seed, one data set; confusion counts per 1,000 test images per class.

Related: [Results index](INDEX.md), [Journal](../../docs/journal.md), [Project memory](../../docs/PROJECT_MEMORY.md)
