---
title: Redesign test 5 result - a hidden layer on L's code reaches about 90.0% on clothing and 98.75% on digits, below the pre-set bars (31 Oct 2026, MEASURED accuracy, COUNTED energy)
tags: [spark, new-start, redesign, accuracy, hidden-layer, result, failure]
---

# Redesign test 5: result (31 Oct 2026)

**Accuracy MEASURED on the cloud container's CPU; energy COUNTED.** Plan and pre-set bars: [step 20 plan](step20_k5_plan.md). Script [`k5_hidden_layer.py`](experiments/k5/k5_hidden_layer.py), [log](experiments/k5/results/k5_run.log), [json](experiments/k5/results/k5_results.json). Hidden layer on the fixed 4,608-bit code, trained on the full 60,000 labels.

| head | clothing | digits |
|---|---|---|
| **4,608-256-10 (main, 2 seeds)** | **90.02%** (89.99, 90.05) | **98.75%** (98.80, 98.69) |
| same, INT8 weights | 89.99% | 98.76% |
| 4,608-1,024-10 (ablation) | 90.60% | 98.72% |
| 4,608-512-256-10 (ablation) | 90.31% | 98.86% |
| reference: shipped counting recipe | 88.85% | 98.60% |
| reference: tuned small network (test 2) | 88.2% (under-trained) to 89.4% | 98.95% |

## Bars (pre-set, judged on the main head)

- **K5-a (clothing at least 90.5%): FAIL** (90.02%).
- **K5-b (digits at least 98.9%): FAIL** (98.75%).
- **K5-c (INT8 weights lose at most 0.3 points): PASS** (0.03 and -0.01).
- **K5-d (counted inference at most 1.0 uJ with the layout factor): PASS** (298 nJ; 10.6 nJ raw).
- **K5-e (counted training at most 5x the tuned network's): PASS** (8.8 J against 12.5 J allowed; about 3.5x the network's 2.5 J).

## What this says

- **A hidden layer lifts the code by about 1.2 points on clothing (88.85 to 90.0) and 0.15 on digits, and the code caps it there.** The wider head (1,024 units) reaches 90.6% on clothing, still far below a strong network (91.75%). The earlier 90.92% measurement was a longer-trained, different setup; this test did not reproduce it with the fixed, pre-set recipe.
- **The design is therefore not a route to the accuracy of GPU models.** At about 90% on clothing it equals a tuned small network, with INT8 weights unharmed and counted inference energy of 10 nJ raw (about 0.3 uJ with the conservative layout factor), but its training is dense backpropagation (about 3.5x the network's counted energy), so it gives up the cheap-training property of the counting recipe.
- **Conclusion for L:** every variant tested (shipped recipe, ridge, prototype layers, hidden layers) lands between 88.6% and 90.6% on clothing. Further gains need a learned front end, which is a decision for the founder (the 28 Oct rule against a CNN as a component of L). This is the end of the L accuracy work: on 31 Oct 2026 the founder set the goal to our own GPU, and L stays as the small recognizer it is.

**Correction after Vision review 01 (31 Oct 2026), V-20):** 'the code caps accuracy near 90%' is an inference, not a measured cap: accuracy still rises with head width (90.02%, 90.31%, 90.60%) and 90.92% was measured earlier. What is supported: linear readouts stop near 88.9%, and no route to higher accuracy was found with a fixed code. The reason for retiring the L accuracy work should read 'no route found', not 'capped'.

Related: [Step 20 plan](step20_k5_plan.md), [Step 19 test 4 result](step19_k4_result.md), [Own GPU charter](../docs/own_gpu_charter.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
