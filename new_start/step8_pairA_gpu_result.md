---
title: Cascade on real language models, pair A on the RTX 3050 - cheaper in energy, but the margin trigger still misses the quality bars (31 Oct 2026, MEASURED)
tags: [spark, new-start, cascade, language-model, result, gpu, energy]
---

# Pair A on the founder's RTX 3050 (31 Oct 2026)

**MEASURED** (GPU idle before the run; half precision; 20,440 WikiText-2 test tokens for stage A; 12 prompts, 160 new tokens each, greedy, for stage B). Printed output transcribed in [`pairA_gpu_rtx3050_printed.txt`](experiments/lm_cascade/results/pairA_gpu_rtx3050_printed.txt) (the json file was not sent). Pair A: a 0.5B and a 1.5B model of one family. Bars: [step 8 plan](step8_cascade_lm_plan.md), written before the run. The speed and energy bars were written for pair B (weight ratio at least 6x); pair A has a 3x ratio, so those rows are reported, not binding.

## Stage A (teacher-forced), agrees with the CPU run

Small model 2.805 nats per token, large 2.446. **P1 pass** (large model 12.8% better). At 30% escalation the cascade is **1.082x the large model (C1 fail; within 1% only at about 75% escalation)** and margin gating closes **0.44 of the gap against 0.30 for random, 1.46x (C3 fail, bar 2x)**. The CPU run in fp32 gave 1.074x and 1.6x on half the text, so the finding does not depend on precision or hardware. The oracle closes 1.41 of the gap at 30%: the idea has room, the trigger is weak.

## Stage B (live generation, real cascade on the GPU)

| setting | tokens per second | J per token, gross | J per token, minus idle | share of tokens needing a large-model pass | agreement with the large model's choice |
|---|---|---|---|---|---|
| large alone | 31.4 | 1.375 | 0.954 | 100% | 99.8% (should be 100%; half-precision rounding) |
| small alone | 38.7 | 0.760 | 0.419 | 0% | 90.9% |
| cascade, nominal 10% | 36.1 | 0.813 | 0.447 | 3.2% | 92.0% |
| cascade, nominal 20% | 33.9 | 0.873 | 0.483 | 6.6% | 94.9% |
| cascade, nominal 30% | 31.3 | 0.973 | 0.551 | 14.0% | 94.7% |

Idle power implied by the gross and net columns is about 13 W.

## Reading each bar

- **C4 fidelity: the agreement part passes (92% to 95%, bar 90%) but does not discriminate:** the small model alone already agrees 90.9%. The cascade adds 1 to 4 points. **The second part, NLL of the generated text under the large model within 5% of the large model alone, fails as written** (0.445, 0.403, 0.552 against 0.522) **and the metric is flawed:** the small model's own text scores a lower NLL than the large model's (0.483), a sign of repetitive text, not of quality. This measure must be replaced before the next run.
- **C5 speed (bar 1.3x, written for pair B):** 1.15x, 1.08x, 1.00x. The speed gain is small because the small model alone is only 1.23x faster than the large one: at batch 1 on this laptop the Python generation loop, not memory, is the limit (about 26 ms per token for the 0.5B model, where reading its 1 GB would take about 6 ms). Speed cannot be judged until the loop is overhead-free (compiled graphs or a dedicated inference engine).
- **C6 energy (bar 0.75x of the large model, written for pair B):** gross 0.59x, 0.64x, 0.71x; minus idle 0.47x, 0.51x, 0.58x. **Energy savings are real and measured (29% to 41% gross), but most of the saving comes from the small model being cheaper: the small model alone saves 45%.** The cascade buys back quality (agreement 92% to 95% against 91%) for a modest energy cost.
- **Operating point mismatch:** a nominal 30% escalation (set on text) became 14% in live generation, because the model is more confident on its own text. Thresholds must be set on generated text, not on reference text.

## Verdict

**The cascade claim "quality near the large model at a fraction of its cost" is not supported by this pair with the margin trigger.** What is supported: measured energy and some speed savings, and a mild quality gain over the small model alone. Not yet tested: pair B (a 6x or larger weight ratio, where the bytes and energy bars apply), a learned router, an overhead-free engine for speed.

## Next (each needs its bar written first)

1. **Learned router** (margin, entropy, position and hidden-state features, trained on one slice of text and tested on another): bar at 30% escalation, within 1% of the large model.
2. **A better live fidelity measure** than NLL under the large model (for example the large model's NLL difference on a fixed reference continuation, or agreement counted only where the models differ).
3. **Pair B** on the GPU with an overhead-free engine, for the speed and energy bars as written.

Related: [Step 8 plan and bars](step8_cascade_lm_plan.md), [Pair A CPU result](step8_pairA_cpu_result.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
