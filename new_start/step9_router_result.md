---
title: Diagnosis and learned router - the language cascade claim fails its stop rule (31 Oct 2026, MEASURED on CPU)
tags: [spark, new-start, cascade, router, language-model, result, failure, stop-rule]
---

# Diagnosis and learned router (31 Oct 2026)

**MEASURED** (teacher-forced, fp32, cloud container CPU, same 0.5B and 1.5B pair as [pair A](step8_pairA_gpu_result.md)). Bars: [step 9 plan](step9_router_plan.md), written and pushed before the run. Script [`router_test.py`](experiments/lm_cascade/router_test.py), [log](experiments/lm_cascade/results/router_pairA_cpu.log), [json](experiments/lm_cascade/results/router_pairA_cpu.json). Slices: 19,929 train tokens (WikiText-2 train), **9,709 test tokens**, **4,599 validation tokens**; the router is trained on the train slice only.

## Part 1: diagnosis (test slice)

- Rank correlation between the small model's margin and the large model's gain: **-0.18** (the sign is right, the strength is weak).
- Mean gain per margin decile (nats per token, lowest margin first): 0.58, 0.46, 0.41, 0.37, 0.39, 0.45, 0.33, 0.22, 0.09, 0.04. Low margin does pick higher-gain positions, but unevenly: the middle deciles are not ordered.
- Among the 30% lowest-margin positions, **37% have a gain under 0.05 nats**: for more than a third of the positions the trigger selects, escalating buys nothing. Mean gain there 0.48, against 0.27 for the rest.
- By the pre-set rule (correlation below 0.3 in size and at least a quarter of the selected positions with gain under 0.05) **the hypothesis is supported**: many unsure positions are positions where the large model does not know better either.

## Part 2: learned router (judged on both held-out slices)

| escalated | slice | margin trigger: x large model / gap closed | router A (scalar signals) | **router B (scalar + hidden state)** | random | oracle |
|---|---|---|---|---|---|---|
| 30% | test | 1.072 / 0.434 | 1.063 / 0.508 | **1.055 / 0.572** | 0.304 | 1.465 |
| 30% | validation | 1.078 / 0.498 | 1.064 / 0.589 | **1.056 / 0.640** | 0.315 | 1.379 |
| 50% | test | 1.043 / 0.662 | 1.033 / 0.745 | 1.029 / 0.770 | 0.508 | 1.626 |

## Bars (router B)

- **R1 (within 1% of the large model at 30% escalation): FAIL on both slices** (1.055 and 1.056).
- **R2 (closes at least 2x the margin trigger's gap at 30%): FAIL on both slices** (1.32x on test, 1.29x on validation).
- **R3 (closes more than the margin trigger at every fraction from 10% to 50%): PASS on both slices.**

## Reading

The router is a real but small improvement (the cascade moves from 1.072x to 1.055x the large model at 30% escalation). It stays far from the bar and far from the oracle, which closes 1.4x the gap. The reason is visible in the fit: the router explains about 6% of the variance of the large model's gain (held-out error 1.346 against a variance of 1.436; adding the hidden state beat the scalar signals only slightly, 1.346 against 1.356). **Where a large model does better than a small one is mostly not predictable from the small model's own state.**

## Decision by the pre-set stop rule

The plan said: *if R2 fails, the language cascade claim is dropped from the pitch.* **R2 failed on both slices, so the claim "a small model answers, a large model is called when the small one is unsure, with quality near the large model at a fraction of the cost" is dropped.** It stays in the record with these numbers. What remains true and measured: the image cascade (91.24% against 91.53% for the strong model alone, hardware cascade on the ESP32), and on language only a **price-for-quality trade** (energy per token 29% to 41% below the large model at 91% to 95% agreement with it, from the GPU run), which is not a claim of near-equal quality.

## Limits

One text domain and model pair, teacher-forced perplexity not task accuracy, a linear router only. A nonlinear router or a different kind of cascade (verification of drafted tokens, which gives the large model's output exactly and is an existing technique, not ours) are not covered by this test and would need their own bars.

Related: [Step 9 plan](step9_router_plan.md), [Step 8 pair A GPU result](step8_pairA_gpu_result.md), [Step 8 pair A CPU result](step8_pairA_cpu_result.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
