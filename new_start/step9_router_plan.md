---
title: Diagnosis and learned router for the language cascade - pre-set bars (31 Oct 2026)
tags: [spark, new-start, cascade, router, language-model, test-plan, bars]
---

# Diagnosis and learned router: bars written before the run (31 Oct 2026)

**Written before any run.** Context: [pair A on the RTX 3050](step8_pairA_gpu_result.md): the margin trigger misses C1 and C3. Script: [`router_test.py`](experiments/lm_cascade/router_test.py). It runs on CPU in the cloud container (fp32, the same 0.5B and 1.5B pair), so the founder's GPU is not needed.

## Data (no overlap between slices)

- **Train slice:** about 20,000 tokens from the WikiText-2 training split (the last fifth used to choose the regression strength).
- **Test slice:** the first 10,220 tokens of the WikiText-2 test split (the text of the earlier CPU run).
- **Second held-out slice:** about 5,000 tokens of the WikiText-2 validation split. The router is trained once, on the train slice only, and judged on both held-out slices.

## Part 1: diagnosis (no new model, computed on the test slice)

Per token: the small model's margin, the large model's gain (large log-probability minus small log-probability of the true next token). Reported: rank correlation of margin and gain; mean gain per margin decile; among the 30% lowest-margin positions, the share where the gain is under 0.05 nats and the large model's mean top-1 probability. Hypothesis to test: *many low-margin positions are unpredictable for both models, so escalating there gains little.* The hypothesis is **supported** if the rank correlation is below 0.3 in absolute value and at least a quarter of the lowest-margin 30% have gain under 0.05; otherwise it is reported as not supported and the explanation stays open.

## Part 2: the learned router

Escalate the positions with the highest predicted gain. Main router **B**: ridge regression on the small model's own signals (margin, top-1 probability, entropy, mass of the top 5, and the last hidden state, 896 numbers), predicting the large model's gain; the ridge strength is chosen on the last fifth of the train slice. Ablation **A**: the scalar signals only (declared as the ablation before the run; the bars are judged on B).

## Bars (judged on test and on the second slice; both must pass)

| id | bar |
|---|---|
| **R1** | at 30% escalation, router B's cascade NLL is within 1% of the large model's |
| **R2** | at 30% escalation, router B closes at least 2x the NLL gap the margin trigger closes on the same slice |
| **R3** | router B closes more of the gap than the margin trigger at every escalation fraction from 10% to 50% |

R1 is the original C1 bar. R2 and R3 are checks that the improvement is real. **No bar is changed after the run.**

## What each outcome means

- **R1 and R2 pass on both slices:** the language cascade claim survives with a learned router; the next step is the live test (pair B, overhead-free engine, thresholds set on generated text).
- **R2 passes but R1 fails:** the router helps but quality near the large model is only reached at a higher escalation fraction; the claim is restated at that fraction (with its bytes cost) and a new bar is written before another run.
- **R2 fails:** the stop rule applies: the language cascade claim is dropped from the pitch; the image cascade (measured) and the recognition chip remain the evidence, and the large-model system stays a modelled study.

**Limits:** one text domain, one model pair, quality by perplexity not by task accuracy, teacher-forced (not live generation), the router is a linear model (a nonlinear router is a possible follow-up, not part of this test).

Related: [Step 8 pair A GPU result](step8_pairA_gpu_result.md), [Step 8 plan](step8_cascade_lm_plan.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
