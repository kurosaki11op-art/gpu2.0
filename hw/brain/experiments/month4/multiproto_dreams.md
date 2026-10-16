---
title: Dreams that keep co-occurrence, and virtual examples for new words
date: 2026-10-16
tags: [month4, dreams, continual-learning, few-shot, simulated]
---
# Multi-prototype dreams and virtual examples (16 Oct 2026, morning)

Research behind it: [weak spots](../../../../docs/research_weak_spots.md). All numbers SIMULATED (exact integer chip model, margin 32, 3 seeds).

## 1. Dreams with K prototypes per class (`hw/brain/cortex_proto.py`, `proto_dreams.py`, `dream_variants.py`)

**Problem.** Learning in 5 stages loses accuracy against learning everything at once (clothing 78.7 vs 83.5, words 82 vs 83)
because a dream draws each code bit independently from its class on-rate and so loses which features occur together.
**Fix tested.** The dream memory keeps K count-sets per class; an example goes to the prototype with the highest normalised
overlap (a shifted counter sum, no divide), a dream picks a prototype in proportion to its example count and then draws bits
from it with the chip's L-bit random draws. Integer, no multiplies.

| Dataset | 5 stages, today (K=1) | K=2 | K=4 | K=8 | all at once (K=1 / K=8) |
|---|---|---|---|---|---|
| clothing | 78.7 | 80.3 | **81.5** | **82.1** | 83.3 / 83.9 |
| digits | 94.9 | 94.1 | 94.7 | 94.8 | 97.0 / 97.2 |
| words | 82.0 | 81.7 | **83.0** | 82.7 | 83.1 / 82.9 |
| dream memory (images) | 0.46 Mbit | 0.92 | 1.84 | 3.69 | |

With floating-point rates (an upper bound) staged clothing reaches 82.4 (K=4) and 83.9 (K=8). Replaying stored real
examples instead (10-20 per class) recovers only 1-2 points; cue-and-complete 1.5-2. Narrower prototype counters lose the
gain (K=4 with 8-bit counters 80.2; K=8 with 7-bit 81.7; 5-bit 77.7).
**Verdict.** +2.8 to +3.4 points staged on clothing, +1 on words, nothing on digits, for 4-8x the dream memory (the
largest memory of the chip): an **optional "high-fidelity dreams" setting for clothing-like data**, not a default; no RTL
(it needs K counter sets and a K-way overlap pass per learned example).

## 2. Clothing encoder ideas from the literature (`clothing_gap.py`) - all rejected

Today 83.4 all at once / 78.6 staged. Histogram-quantile brightness thresholds (same memory): 83.4 / 77.4. Three quantile
channels: 82.8 / 77.9. Coarse 5x5 centre-surround pair (+50% bits): 83.5 / 78.5. Two tables with different encoders summed
(2.5x memory): 84.8 / 79.2. The gap to the network (87.3) is capacity, not these knobs.

## 3. New spoken words from a few recordings (`fewshot_words_aug.py`)

Every new recording is also presented with its word start moved to frames 5 and 7 (virtual examples), then IMPRINT + sleep.
Accuracy over all 10 words (old words 5, new words 5), single view / LOOK AGAIN:

| Recordings per new word | none | virtual examples 5,6,7 |
|---|---|---|
| 1 | 48.2 / 49.2 | 49.5 / **51.1** |
| 2 | 49.5 / 49.7 | 49.6 / **51.7** |
| 5 | 51.4 / 53.5 | 51.0 / **55.5** |

New words alone: 1 recording 11.5 -> 22.2%, 5 recordings 18.1 -> 26.3% (with LOOK AGAIN). A small, cheap gain (+2); the
real gap to a network is a learned word embedding, which this chip does not have.

Related: [month4 index](INDEX.md), [Redesign 1 note](fewshot_imprint.md), [Research: weak spots](../../../../docs/research_weak_spots.md), [Project memory](../../../../docs/PROJECT_MEMORY.md)
