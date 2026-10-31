---
title: Redesign test 4 result - a prototype layer with a closed-form readout does not lift the ceiling of L's code (31 Oct 2026, MEASURED accuracy, COUNTED energy)
tags: [spark, new-start, redesign, accuracy, prototypes, readout, result, failure]
---

# Redesign test 4: result (31 Oct 2026)

**Accuracy MEASURED on the cloud container's CPU, full 60,000 labels; energy COUNTED.** Plan and pre-set bars: [step 19 plan](step19_k4_plan.md). Script [`k4_prototype_layer.py`](experiments/k4/k4_prototype_layer.py), [log](experiments/k4/results/k4_run.log), [json](experiments/k4/results/k4_results.json).

| design (60,000 labels) | clothing | digits |
|---|---|---|
| shipped recipe (reference, test 2) | 88.85% | 98.60% |
| R1 ridge on the 4,608-bit code | 88.62% | 97.75% |
| R2 1,000 prototypes + ridge | 87.75% (2 seeds) | 97.69% |
| **R3 (main) 3,000 prototypes + ridge** | **88.67%** (88.64, 88.70) | **97.70%** |
| R3 with an int8 readout | 88.06% | 97.73% |
| R3 with a 5-bit readout | 32% to 52% (collapses) | 95.3% to 95.8% |

## Bars (pre-set, judged on R3)

- **K4-a (clothing at least 90.0%): FAIL** (88.67%).
- **K4-b (digits at least 98.9%): FAIL** (97.70%, below the shipped recipe's 98.60%).
- **K4-c (counted inference at most 1.0 uJ): PASS** (86 nJ per image, raw constants).
- **K4-d (counted training at most one fifth of the tuned network's, 0.5 J): FAIL** (1.23 J: the clustering of 60,000 images into 3,000 prototypes costs more than the counting recipe).
- **K4-e (int8 readout loses at most 0.5 points): FAIL on clothing** (0.61 points; digits lose none); a 5-bit readout is unusable.

## What this says

- **At full data the readout is not the bottleneck.** A linear readout on L's code, whether the shipped counting rule, ridge regression, or ridge on 3,000 learned prototypes, stays at 88.6% to 88.9% on clothing. The code itself caps any linear readout at about 88.9%, which agrees with the earlier finding that an offline table is no better ([gap diagnosis](../hw/results/gap_diagnosis.md)). The few-label gain of [test 3](step18_k3_result.md) was a small-N effect and does not carry to full data.
- **The earlier measurement points to the fix:** a nonlinear network on the same 4,608-bit code (4,608-256-10, float) reached **90.92%** ([gap diagnosis](../hw/results/gap_diagnosis.md)), about 1.2 points above the shipped system and level with a tuned small network. That path was set aside on 28 Oct because it needs multipliers; **the rule was withdrawn on 31 Oct 2026**, so it is open again. Next: test 5, a hidden layer on the code (the input is sparse: about 580 of 4,608 bits are on, so the first layer is a sum of 580 table rows), with its own pre-set bars.

Related: [Step 19 plan](step19_k4_plan.md), [Step 18 test 3 result](step18_k3_result.md), [Gap diagnosis](../hw/results/gap_diagnosis.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
