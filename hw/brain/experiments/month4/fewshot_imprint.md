---
title: Redesign 1 - learning a new class from a few examples after shipping (IMPRINT + short sleep)
date: 2026-10-15
tags: [month4, few-shot, redesign, simulated, rtl]
---
# Redesign 1: a new class from a few examples after shipping (15 Oct 2026, night)

**The failure.** The chip knows classes 0-4 (all their examples) and then meets 5-9 with k examples each. Old rows
of the table sit near +-15 after thousands of updates, a new row gets a few +1 steps, so the new class is outvoted:
1 example per new digit reaches 6.5% on the new digits. Research: [new class from few examples](../../../../docs/research_fewshot_class_incremental.md).

**The fix (in the chip model and the RTL, bit-exact).**
1. **IMPRINT** (novelty-gated prototype imprint, after C-FSCIL / weight imprinting / dopamine-gated learning): while a
   class has seen at most 8 examples, raise its table row to its mean code x4: W[c,b] = max(W[c,b], min((on[c,b] << 2)
   >> floor(log2 n[c]), 15)). The dream counters already hold the class's mean code, so no new memory: one command,
   shifts and compares, 3 cycles per code bit. RTL: `cortex_core.v` build option `CORTEX_IMPRINT`, MEM arg 4.
2. **Short sleep** after an imprint: 300 dreams per known class (plain DREAM commands): old classes' dreams push the
   new rows back on the bits where they wrongly win (consolidation). Model: `CortexInt(imprint=4, imprint_sleep=300)`.
Check: `hw/rtl/cortex/run_check_cortex_imprint.py` (plain and pipelined, in `run_all_checks.sh`): 0 mismatches.

**Results (SIMULATED, exact integer chip model, 3 seeds; accuracy on all 10 classes, old classes in brackets).**

| Examples per new class | digits today | digits fixed | clothing today | clothing fixed | words today | words fixed |
|---|---|---|---|---|---|---|
| 1 | 54.1 (99.0) | **69.9** (97.1) | 49.7 (87.5) | **64.0** (86.3) | 45.2 (88.4) | 48.3 (83.3) |
| 2 | 62.5 (98.7) | **76.4** (96.8) | 57.8 (87.5) | **67.5** (86.2) | 46.1 (88.3) | 49.5 (84.7) |
| 5 | 72.7 (97.9) | **81.0** (96.0) | 67.9 (87.1) | **70.1** (86.4) | 48.8 (87.7) | 52.5 (82.1) |
| 10, 20 | unchanged (the gate turns IMPRINT off above 8 examples) | | | | | |

(Words use the aligned sound codes. Sources: `fewshot_fixes*.py` rounds 1-6 and their logs/JSON,
`fewshot_imprint_confirm.py` 5 seeds for IMPRINT alone.)

**What was tried and rejected on the way.**
- Plain imprint (no 1/n step): fixes 1 example, swamps old classes from 5 (round 1).
- Weight aligning by power-of-two norm shifts: breaks old classes (round 1).
- Hippocampus gate on stored examples: never fires usefully (rounds 2-3).
- Imprinting distinct bits only: protects old classes but gains less (rounds 3-4).
- Blurred imprint (both axes, time only, frequency only): helps digits at 1 example only, hurts elsewhere (rounds 5-6).

**Still failing.** Words from 1-5 recordings: new words reach 12-22% with old words kept; the same word from different
speakers varies too much for a few clips. Network comparison and pattern separation (mushroom-body expansion) are
being tested next.

## Against a network on words (same setting, `fewshot_after_shipping.py speech`, 3 seeds, SIMULATED)

Chip = IMPRINT alone (this run predates the short sleep). Network = MLP 784-256-10 on the aligned sound pictures,
trained on words 0-4, then either fine-tuned on the k new recordings (continual, like the chip) or retrained on all
old data plus the k new ones (needs every old example kept).

| Recordings per new word | chip all (old / new) | network fine-tuned all (old / new) | network, all old data kept |
|---|---|---|---|
| 1 | **45.4** (64.7 / 25.6) | 21.2 (1.3 / 41.5) | 46.1 (90.9 / 0.0) |
| 5 | **50.0** (56.4 / 43.4) | 32.5 (0.1 / 65.6) | 45.0 (88.8 / 0.1) |
| 20 | **61.4** (85.5 / 36.7) | 36.4 (0.4 / 73.4) | 50.6 (91.1 / 9.0) |

The network either forgets the old words completely or never learns the new ones; the chip is the only one that
keeps both. Few-shot words are hard for every method here, not a chip-only failure.

## Against a network on clothing (full recipe: IMPRINT + short sleep; `fewshot_after_shipping.py fashion`, 3 seeds)

| Examples per new class | chip all (old / new) | network fine-tuned all (old / new) | network, all old data kept |
|---|---|---|---|
| 1 | **64.0** (86.3 / 41.6) | 38.3 (22.5 / 54.2) | 44.6 (89.1 / 0.0) |
| 5 | **70.1** (86.4 / 53.8) | 37.2 (1.7 / 72.7) | 56.0 (89.2 / 22.8) |
| 20 | **76.1** (85.7 / 66.6) | 41.8 (2.2 / 81.4) | 71.5 (89.3 / 53.8) |

SIMULATED. After shipping, the chip is ahead of both network set-ups at every size on clothing.

Related: [month4 index](INDEX.md), [few-shot note](fewshot_saccades.md), [research](../../../../docs/research_fewshot_class_incremental.md), [Project memory](../../../../docs/PROJECT_MEMORY.md)
