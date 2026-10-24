---
title: Learning with few examples - two brains (24 Oct 2026)
tags: [l, few-shot, results, design]
---

# Few labelled examples per class, and the two-brain design (SIMULATED/MEASURED on CPU, Fashion-MNIST, 3 to 4 random draws of the labelled examples, accuracy on all 10,000 test images)

Scripts `hw/brain/experiments/month5/learning_curve.py`, `learning_curve2.py`, `learning_curve3.py` (logs `learning_curve_fashion.log`, `learning_curve2_fashion.log`, `learning_curve3_f32.log`). All methods see the same labelled examples. **Caveat:** L and the code baselines learn their detectors from 12,000 unlabelled training images (no labels); the CNN gets no unlabelled data, so the CNN is handicapped.

## 1. Finding: L's counting table is the weak part with few examples (failure)

| Examples per class | L counting table | L + IMPRINT + short sleep | Class means on L's code | CNN (raw pixels, flip/shift) |
|---|---|---|---|---|
| 1 | 27.2 | 48.4 | 51.8 | 42.1 |
| 5 | 46.8 | 58.6 | 66.3 | 64.3 |
| 10 | 55.9 | 55.9 | 70.0 | 69.6 |
| 50 | 73.9 | 73.9 | 75.2 | 75.8 |
| 300 | 83.7 | 83.7 | 75.8 | 77.5 |

The code is good (class means on it beat the CNN at 1 to 5 examples); the counting table needs many examples, IMPRINT (made for up to 4 examples per class) rescues only 1 to 5 and is inert beyond, and the table is erratic in the middle (72.5 +- 5.4 at 100).

## 2. Design: two brains (as in complementary learning systems)

- **Fast brain (hippocampus-like, episodic):** one write per example, no training. Two forms: class-mean codes (cost: 10 x 4,608 counters, about 46 KB) and stored exemplars (about 590 active-bit indices per image, about 1.2 KB each at 16-bit indices; 300 per class = 3.5 MB: a replay-like memory, so state that cost).
- **Slow brain (cortex-like, statistical):** L's existing counting table with consolidation (slow table, dreams).
- **Arbitration:** below about 10 examples per class the fast brain alone; above, a z-scored sum of the three scores (class means, best exemplar match, counting table).

| Examples per class | Fast: class means | Fast: exemplars | Slow: counting table | **Two brains: sum of 3** | CNN |
|---|---|---|---|---|---|
| 1 | 52.2 | 52.2 | 29.7 | 48.9 (use fast alone: **52.2**) | 42.1 |
| 2 | 59.3 | 58.8 | 41.0 | 53.8 (fast alone **59.3**) | 52.6 |
| 5 | 65.7 | 66.9 | 51.8 | 62.0 (fast alone **66.9**) | 64.3 |
| 10 | 68.7 | 69.8 | 61.9 | 69.4 (fast alone **69.8**) | 69.6 |
| 20 | 71.6 | 72.9 | 63.5 | **72.9** | 73.4 |
| 50 | 74.8 | 76.0 | 74.7 | **79.1** | 75.8 |
| 100 | 75.4 | **78.7** | 72.5 | 77.3 | 75.5 |
| 300 | 75.6 | 81.1 | 83.7 | **84.0** | 77.5 |

(Detectors fitted on 12,000 unlabelled images of all classes, 32 per channel; fitting on all classes instead of only classes 0 and 1 changed the fast brain by under 0.5 points.)

## 3. Reading

- Few examples: the two-brain rule (fast brain alone) gives 52, 59, 67% at 1, 2, 5 examples per class, **9 to 10 points above the CNN at 1 example and 2 to 7 points at 2 and 5**; from 10 to 20 examples it is level with the CNN; at 50 it is **+3.3** and at 300 **+6.5** above it (84.0 against 77.5).
- This is a modest advantage, not a breakthrough: with 1 example per class still only 52% (the best published prototype-style few-shot methods use pretrained deep features; not compared here), and the arbitration rule is picked from the same 3 draws (needs a validation protocol).
- The chip implication: the "fast brain" is cheap (class means: one add per active bit per example, no training), the "slow brain" is what L has. The z-score uses a division and a standard deviation; a hardware version needs shifts and an approximation (not yet designed).

## 4. Not done

Consolidation from the fast brain to the slow table by replay (sleep), IMPRINT beyond 4 examples, a validation-chosen arbitration, other data sets (MNIST, real photos), unlabelled-pretrained CNN baseline.

Related: [Results index](INDEX.md), [Few-shot imprint (month 4)](../brain/experiments/month4/fewshot_imprint.md), [Failure analysis](../../docs/failure_analysis_clothing.md), [Journal](../../docs/journal.md)
