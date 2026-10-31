---
title: M1 fix result - mixed precision meets the 99% bar, but the real quality loss of W8A8 was already negligible (31 Oct 2026, SIMULATED)
tags: [spark, gpu, m1, quantisation, fix, result]
---

# M1 fix result (31 Oct 2026)

**SIMULATED.** Plan and pre-set bars: [M1 fix plan](M1_fix_plan.md). Scripts [`m1_fix.py`](m1/m1_fix.py) and [`m1_loss_check.py`](m1/m1_loss_check.py); outputs [`m1_fix.json`](m1/results/m1_fix.json) and [`m1_loss_check.json`](m1/results/m1_loss_check.json). The simulator gained the per-weight activation precision annotation (`a16`, `af`) and an INT16-activation matrix path; it still passes its earlier checks (W8A8 agreement unchanged at 98.73%).

## Procedure and result

Calibration on 16 new windows (not used in the evaluation); each of the 13 weight tensors was set in turn to FP activations to measure its sensitivity. **The sensitivity is flat: no tensor gains more than 0.7 points** (L0.wk 0.68, L0.wv, L0.w2, L1.wk, L1.wo 0.49 each, the rest 0.1 to 0.4): the near-tie errors are spread over all layers, not caused by one outlier layer, so the hypothesis of a dominant outlier layer is **not supported**. Greedy selection took the five most sensitive tensors (L0.wk, L0.wv, L0.w2, L1.wk, L1.wo; the limit) and reached 99.12% on the calibration set, short of the 99.5% target.

| set (1,024 positions each) | W8A8, all INT8 | mixed (5 tensors with INT16 activations) |
|---|---|---|
| original evaluation | 98.73% | **99.02%** |
| fresh evaluation | 99.41% | **99.80%** |
| calibration | 98.73% | 99.12% |

## Bars (pre-set)

- **M1F-a (at least 99% on both evaluation sets): PASS** (99.02% and 99.80%), narrowly on the original set.
- **M1F-b (at most 5 tensors with INT16 activations): PASS at the limit** (5 of 13). They carry **32% of all multiply-adds** (33.5 of 104.9 million), so with INT16 operations at an assumed 2x multiply-add energy the matrix-multiply energy rises by 1.32x.
- **M1F-c (the CNN stays at 99% or above): PASS** (99.8% in W8A8; the CNN program has no INT16 annotation).

## The more important finding: the agreement metric was misleading

- **W8A8 agreement varies by 0.7 points between three different sets of 1,024 positions** (98.73%, 98.73%, 99.41%): the mean of 98.96% sits on the bar, and the gain from mixed precision (3 to 4 positions per set) is inside that sampling spread. A disagreement only counts when the fp32 top two characters are nearly tied (gap at most 0.036), which carries almost no information.
- **The quantity that matters, the next-character loss on the held-out windows, is unchanged by quantisation** (nats per character; fp32 first):

| set | fp32 | INT8 weights | W8A8 | mixed |
|---|---|---|---|---|
| original evaluation | 1.7296 | 1.7296 (+0.0000) | 1.7288 (-0.0008) | 1.7293 (-0.0003) |
| fresh evaluation | 1.7400 | 1.7402 (+0.0002) | 1.7420 (+0.0019) | 1.7403 (+0.0003) |

  W8A8 changes the loss by at most 0.002 nats per character (0.1%), the mixed configuration by at most 0.0003. **The INT8 transformer on our mesh is as good as fp32 for the quantity a model is trained and judged on.**

## Verdict and recommendation

- **The M1 miss is resolved on the bar as written** (mixed precision, both sets at 99% or more), **and shown to be a metric artefact**: W8A8 already loses nothing measurable in loss. **Recommendation: keep plain W8A8 as the default configuration** (no INT16 energy overhead), keep the `a16` annotation as an optional per-layer setting, and **replace the agreement bar by a loss-increase bar (at most 0.01 nats per character) for later milestones**; this is a new bar for new work, not a re-grading of M1 (which passes as measured above).
- **Limits:** one small briefly trained model, character-level, 3 sets of 1,024 positions; the INT16 path's energy cost is assumed (2x), not designed; no hardware.

Related: [M1 fix plan](M1_fix_plan.md), [M1 result](M1_result.md), [ISA note](ISA_M1.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Hardware index](../HARDWARE_INDEX.md)
