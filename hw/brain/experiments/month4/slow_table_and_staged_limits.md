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
| clothing | 87.9 | 88.6 | 88.4 | 89.2 | 83.4 today (5 seeds) / 86.9 with the slow table |
| digits | 98.3 | 98.3 | (not run) | (not run) | 97.0 today / 97.6 with the slow table |

**Finding (corrects an earlier chat answer that blamed the senses).** The code itself allows 87.9% (clothing) and 98.3% (digits) with a plain linear
readout, as good as an MLP on raw pixels. The chip's own readout (a 5-bit table trained online, one pass, margin rule) loses 3-4 points on clothing and
about 1.3 on digits. So the main limit of all-at-once accuracy is the readout / learning rule, not the senses.

## 2. Redesign 6: a slow consolidating table (`cortex_slow.py`, `slow_table.py`, `slow_staged.py`, `slow_confirm.py`, `slow_precision.py`, `final_numbers.py` with SLOW=1)

The fast table is trained online, so its final weights reflect the last examples (about 1 point between seeds; 5-seed spread 82.3 to 84.7 on clothing). A second table S follows the fast table W:
every CH ticks (a tick = one real example or one night dream) S += (((W << FR) - S) + 2^(K-1)) >> K, shifts and adds only, with CH = 500 (100 for sound), K = 3, FR = 3 (8-bit entries), round to nearest.
Prediction reads S. Costs a second table (8 bits x 4608 x 10 = 46 KB for images, 1.6x the fast table) and one table sweep per CH ticks (~14k cycles per sweep, ~28 cycles per example at CH = 500).
Precision (mnist, 3 seeds, 5 stages / all at once): FR 1 no rounding 93.5 / 97.5; FR 1 + rounding 93.9 / 97.6; FR 2 94.4 / 97.6; FR 3 94.7 / 97.6; FR 4 94.8 / 97.6 (today 94.9 / 97.0).
FR 0 loses 2 points; the floor-shift bias of a coarse S hurts staged learning, rounding plus 3 fractional bits removes it.

Final numbers, 5 seeds, margin 32, exact integer model (`final_numbers_*_slow.json`), single view / LOOK AGAIN:

| Test | today | slow table |
|---|---|---|
| clothing, all at once | 83.4 / 84.8 | **86.9 / 87.9** |
| words, all at once | 83.1 / 84.7 | **85.7 / 87.2** |
| digits, all at once | 97.0 / 98.0 | **97.6 / 98.3** |
| clothing, 5 stages | 78.4 / 78.3 | 78.5 / 78.5 |
| digits, 5 stages | 94.9 / 95.8 | 94.6 / 95.5 |
| words, 5 stages | 82.0 / 82.9 | see log |

Few-shot after shipping (imprint; `fewshot_slow.py`, clothing, 3 seeds, k = 1 / 5 / 20): copying S := W << FR after a stage shorter than 2 CH reproduces today's numbers exactly (all 10 classes 63.3 / 70.2 / 76.6);
copying only the new classes' rows is slightly better on clothing (64.2 / 70.5 / 77.1) but on words it trades old for new words (old 84 -> 69, new 11 -> 25, total 48.0 -> 47.4), so the plain copy is used.
**RTL.** Build option `CORTEX_SLOW` in `hw/rtl/cortex/cortex_core.v` (MEM arg 5 FOLLOW, arg 6 SCOPY, arg 7 read S; PREDICT reads S). Bit-exact against `CortexSlow` in the new check
`run_check_cortex_slow.py` (3 scenarios, plain, pipelined and with the SKY130 SRAM macro models): every prediction, update flag, dream length, the table, counters, counts and every S word, 0 mismatches.
It is an ASIC build option (the Tang Nano is full). **Verdict: a real gain for learning everything at once (+3.5 clothing, +2.6 words, +0.6 digits single view), none in stages, small cost.**

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
| larger margin for dreams only (`cortex_dm.py`, dmargin 64 / 128 / 256, real margin 32) | 79.5 / 79.0 / 78.9 | +1.0 at best, near noise |
| oracle recency bias (ramp 320, needs hand tuning) | 81.8 | upper bound, not a rule |

**Conclusion.** Staged accuracy is limited by dream fidelity: which features occur together in a class. The only fix that works so far is prototypes (K = 2: +1.6, K = 4:
+2.8, at 2-4x dream memory). Cheap structural dreams, bias tricks and more sleep do not.

## 5. Prototype dreams together with the slow table (`cortex_proto_slow.py`, `proto_slow.py`, 3 seeds, single view, FR = 1 version of the slow table)

| | 5 stages | all at once | dream memory |
|---|---|---|---|
| clothing, today | 78.6 | 83.4 | 1x |
| clothing, slow table alone | 77.4 | 86.6 | 1x (+ 1.2x table) |
| clothing, K = 2 + slow | 79.2 | 86.6 | 2x |
| clothing, K = 4 + slow | **80.7** | 86.7 | 4x |
| words, slow alone / K = 2 / K = 4 + slow | 81.9 / 81.7 / 82.5 | 85.2 / 85.6 / 85.1 | 1x / 2x / 4x |

The two redesigns combine without hurting each other: staged clothing +2.1 (K = 4) for 4x dream memory, words +0.5. This is the optional "high-fidelity dreams" setting; no RTL for prototypes yet
(it needs K counter sets, a K-way overlap pass per learned example and a divider-free prototype pick by rejection sampling instead of a modulo).

Related: [month4 index](INDEX.md), [multi-prototype dreams](multiproto_dreams.md), [Redesign 1 note](fewshot_imprint.md), [Project memory](../../../../docs/PROJECT_MEMORY.md)
