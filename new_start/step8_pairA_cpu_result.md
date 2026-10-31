---
title: Cascade on real language models, pair A stage A on CPU - the margin trigger misses its quality bars (31 Oct 2026, MEASURED on CPU)
tags: [spark, new-start, cascade, language-model, result, failure]
---

# Pair A, stage A (CPU, 31 Oct 2026)

**MEASURED** (teacher-forced, fp32, on the cloud container's CPU; not on the founder's GPU, which still has to run stage B and the speed and energy bars). Script [`cascade_lm_test.py`](experiments/lm_cascade/cascade_lm_test.py), [log](experiments/lm_cascade/results/pairA_cpu_stageA.log), [json](experiments/lm_cascade/results/pairA_cpu_stageA.json). Text: the first 10,220 tokens of the WikiText-2 test set. Pair A: a 0.5B and a 1.5B model of one open-weight family. Bars: [step 8 plan](step8_cascade_lm_plan.md), written before the run.

| escalated | cascade NLL | x large model | gap closed | random gating closes | oracle closes | bytes / large alone |
|---|---|---|---|---|---|---|
| 10% | 2.902 | 1.107 | 0.17 | 0.11 | 0.88 | 0.42 |
| 20% | 2.856 | 1.090 | 0.31 | 0.20 | 1.25 | 0.52 |
| **30%** | **2.814** | **1.074** | **0.43** | **0.28** | 1.45 | **0.62** |
| 50% | 2.737 | 1.044 | 0.66 | 0.50 | 1.61 | 0.82 |
| 75% | 2.645 | 1.009 | 0.93 | 0.75 | 1.61 | 1.07 |
| 100% | 2.621 | 1.000 | 1.00 | 1.00 | 1.00 | 1.32 |

Small model NLL 2.961, large 2.621 nats per token.

## Bars

- **P1 (the large model at least 8% better): pass.** The large model is 11.5% lower.
- **C1 (within 1% of the large model at 30% escalation or less): FAIL.** At 30% the cascade is 7.4% worse than the large model; the first fraction within 1% is about 75%.
- **C3 (margin gating closes at least 2x what random gating closes at 30%): FAIL.** It closes 0.43 against 0.28, 1.6x.
- **C2 (bytes at most 0.5x the large model alone): not met either** (0.62 at 30%, as expected for a 3x weight ratio; pair B is where it is meant to be judged).
- **C4 to C6 (live fidelity, speed, energy): not run yet** (they need the GPU stage B).

## Reading

The small model's low margin is only a weak sign that the large model would do better: it closes about 1.6x the gap that chance closes. The oracle row shows the potential is large (choosing the right 30% of positions beats the large model alone), so the trigger is the problem, not the idea. A likely cause: positions where the small model is unsure are often positions where nothing is predictable (a name, a number), where the large model gains little.

## What to do about it (a lever, not yet tested, to be given a bar first)

A **learned router**: a small classifier on features the small model already has (margin, entropy, top-k mass, position, hidden-state summary), trained on one slice of text to predict whether the large model would be better by a set amount, and evaluated on a separate slice. It costs almost nothing at run time. It needs its own bar, written before it is run: at 30% escalation, cascade NLL within 1% of the large model, or at least 2x the margin trigger's closed gap with a held-out test.

Until then the pitch claim ("quality near the large model at a fraction of its cost, triggered by confidence") is **not supported on language**; on images it was (91.24% against 91.53%). The founder's GPU run will repeat stage A in half precision and add the live stage B; the quality numbers should agree to within noise.

Related: [Step 8 plan and bars](step8_cascade_lm_plan.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
