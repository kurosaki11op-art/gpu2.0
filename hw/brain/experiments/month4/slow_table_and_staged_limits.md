---
title: What limits the scores - code ceiling, slow table, staged-learning diagnosis
date: 2026-10-18
tags: [month4, redesign, slow-table, staged, simulated]
---
# What limits the scores (18 Oct 2026): code ceiling, slow table (Redesign 6), staged-learning diagnosis

All numbers SIMULATED (exact integer chip model, 2-3 seeds) unless marked as a floating-point diagnostic (not part of the chip).

## 1. Is it the senses or the readout? (`code_ceiling.py`, floating-point diagnostic, 1 seed, 8 epochs)

A floating-point network with backprop trained on the chip's own sparse code (4608 bits) vs on raw pixels:

| | linear on code | MLP on code | MLP on pixels | small CNN on pixels | chip (all at once) |
|---|---|---|---|---|---|
| clothing | 87.9 | 88.6 | 88.4 | 89.2 | 83.4 (3 seeds, today) |
| digits | 98.3 | 98.3 | (not run) | (not run) | 97.0 |

**Finding (corrects the 18 Oct chat answer that blamed the senses).** The code itself allows 87.9% (clothing) and 98.3% (digits) with a plain linear
readout, as good as an MLP on raw pixels. The chip's own readout (a 5-bit table trained online, one pass, margin rule) loses 3-4 points on clothing and
about 1.3 on digits. So the main limit of all-at-once accuracy is the readout / learning rule, not the senses.

## 2. Redesign 6: a slow consolidating table (`cortex_slow.py`, `slow_table.py`, `slow_staged.py`)

The fast table is trained online, so its final weights reflect the last examples (about 1 point between seeds). A second table S (8-bit entries, 4 fractional
bits) follows the fast table W: every CH practise ticks, S += (16 W - S) >> K. Prediction reads S. Shifts and adds only; costs a second table (8 bits x 4608 x 10
= 46 KB for images, ~1.5x the fast table) and one table sweep every CH ticks (~92 cycles per example at CH = 500).

| Test (3 seeds) | today | slow table | change |
|---|---|---|---|
| clothing, all at once (CH 500, K 3) | 83.4 | 86.7 | **+3.3** |
| words, all at once (CH 100, K 3) | 82.6 | 85.3 | **+2.6** |
| digits, all at once (CH 500, K 3) | 97.0 | 97.6 | +0.5 |
| clothing, 5 stages | 78.6 | 78.4 | -0.2 |
| words, 5 stages | 82.1 | 82.2 | 0.0 |
| digits, 5 stages | 94.9 | 94.8 | -0.1 |

Few-shot after shipping (imprint; `fewshot_slow.py`, clothing, 3 seeds, k = 1 / 5 / 20): copying S := 16 W after a small stage reproduces today's numbers exactly;
copying only the new classes' rows is slightly better (all 10 classes 64.2 / 70.5 / 77.1 vs 63.3 / 70.2 / 76.6). Nothing is lost.
**Verdict: the slow table is a real gain for learning everything at once (+2.6 to +3.3 on clothing and words, ~+0.5 on digits), none in stages.** Model only; RTL not yet.

## 3. What limits staged learning? (`staged_diag.py`, `recency_bias.py`, clothing, 2 seeds)

- Per class, staged vs all at once: the classes of the LAST stage (8, 9) gain (98.6 / 99.1 vs 96.2 / 90.8); earlier classes lose 3-20 points. The largest new confusions are
  older classes read as last-stage classes: 7 -> 9 +21 points, 6 -> 8 +10, 0 -> 8 +8, 3 -> 8 +7.
- Own-row scores: real test images score 8 to 44 below dreams of the same class (largest for older classes), so the table fits dreams a little better than real images.
- Oracle test: subtracting a bias from recent classes raises staged clothing from 78.4 to 81.8 (ramp, 320): a recency bias worth about 3.5 points exists.
- Earlier result (multiproto_dreams.md): K = 8 prototypes in floating point gets staged clothing to 83.9, the all-at-once level. So the gap is the fidelity of dreams
  (which real structure they keep), not the margin rule or the number of dreams.

## 4. Cheap on-chip fixes for the staged gap tried today - all failed or small

| Idea | Staged clothing (today 78.4-78.6) | Verdict |
|---|---|---|
| more own-class daydreams (2, 4) | 78.4 / 78.2 | no gain |
| margin 16 / 64 | 78.6 / 78.5 | no gain |
| group-structured dreams (`cortex_group.py`: cap on bits per position group, refill empty active groups by roulette) | 78.3 (cap 4), 77.3 (cap 4 with refill), 76.6 / 75.3 (cap 3), 70.0 (cap 2) | worse |
| self-calibrated bias from dream scores (alpha x (mean dream score - mean)) | 79.2 best (alpha 0.5) | +0.9 |
| homeostasis: bias steered so each class's prediction rate matches its training share | 79.2 | +0.8 (and assumes the deployment mix) |
| oracle recency bias (ramp 320, needs hand tuning) | 81.8 | upper bound, not a rule |

**Conclusion.** Staged accuracy is limited by dream fidelity: which features occur together in a class. The only fix that works so far is prototypes (K = 2: +1.6, K = 4:
+2.8, at 2-4x dream memory). Cheap structural dreams, bias tricks and more sleep do not.

Related: [month4 index](INDEX.md), [multi-prototype dreams](multiproto_dreams.md), [Redesign 1 note](fewshot_imprint.md), [Project memory](../../../../docs/PROJECT_MEMORY.md)
