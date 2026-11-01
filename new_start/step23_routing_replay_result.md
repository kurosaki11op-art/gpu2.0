---
title: Step 23 result - on open routing traces an expert cache of 1.17 times the active experts reaches 34 percent, far below the 82 percent bar (1 Nov 2026, routing MEASURED, cache SIMULATED)
tags: [spark, new-start, moe, routing, expert-cache, result, vision-research-03]
---

# Step 23 result (1 Nov 2026)

**Routing MEASURED by others (recorded during pretraining), cache SIMULATED by us.** Plan and bar written before the run: [step 23 plan](step23_routing_replay_plan.md). Script [`step23_routing_replay.py`](experiments/step23_routing_replay.py), [log](experiments/step23_routing_replay.log). Data: [CMU-FLAME/FLAME-MoE-Traces](https://huggingface.co/datasets/CMU-FLAME/FLAME-MoE-Traces), the 1.7B-class model (64 routed experts, top-6), checkpoint `iter_11000`, the first 100,000 consecutive tokens of eight layers, streamed (no full download). Every miss is counted as a tier read; no prefetch credit.

## Result

| cache per layer | x active | offline optimum (Belady): overall / 10th-percentile layer | LRU: overall / p10 | windowed LFU: overall / p10 |
|---|---|---|---|---|
| **7 experts** (the bar) | 1.17 | **0.341 / 0.328** | 0.086 / 0.085 | 0.118 / 0.108 |
| 13 experts | 2.17 | 0.522 / 0.491 | 0.177 / 0.176 | 0.224 / 0.210 |

- **Bar: FAIL.** The offline optimum at 1.17 times the active experts is 0.341 overall and 0.328 in the weakest tenth of layers, against 0.82 and 0.60. By the pre-set rule **the demand-cache route stops** for the step 22 speed bar.
- **Routing here is almost flat.** The top 7 of 64 experts carry 12% of reads in every layer (uniform would be 10.9%), the top 13 carry 22% (uniform 20.3%). A cache has little to hold on to; LRU at 1.17 times (0.086) is below random placement (7 of 64 is 0.109).

## What disagrees with the published numbers, and why this result does not close the question

- Vision's table has **LRU 60% to 66% and offline optimum 79% at about 2.1 times active** (30B-class models with 128 experts, top-8; one layer and 8,000 tokens of code text for the optimum). Here, at 2.17 times, LRU is 0.18 and the optimum 0.52. **That is a large unexplained gap.** Candidate causes, none tested: (1) these traces are **pretraining-order tokens** and consecutive rows may come from mixed documents, not one decoding stream; (2) FLAME's training may enforce expert load balance, which flattens usage; (3) 64 coarse experts against 128 or more finer ones; (4) the published numbers are for one layer and one domain.
- So: **on the only open traces that exist the bar fails by a factor of 2.4, and the published best case at a similar ratio is also below 0.82**; neither source supports 82% at 1.06 to 1.17 times. What the result does not show is how a **1T-class model decoded on real prompts** behaves; no such trace exists.

## What it does to the design

- Step 22's speed bar (4x) needed 82% to 95% of reads from SRAM. On this evidence a tiered chip gets about 0.3 to 0.5 of reads from SRAM, which means **speed about 1x the GPU cluster's, not 4x**, with the energy gain 1.3x to 1.8x (step 22 table at h about 0.25 to 0.5).
- A tiered chip is then **a GPU-like card that competes on chip count and cost, where our costs are unsourced** and an incumbent already ships the same trade. Pure SRAM keeps the speed (17x in the model) but needs 329 chips (47x the GPUs) for a 1T model.
- **Neither variant has shown an advantage that survives its pre-set bar.**

## Limits

One small model, one checkpoint, 100,000 tokens per layer, pretraining order, top-6 of 64 routed experts, 8 of 17 layers; cache sizes by ratio to active experts, not by share; offline optimum is an upper bound for an online cache but not for a predictor that prefetches (Vision's definition excludes prefetch credit for bytes that cross the tier).

Related: [Step 23 plan](step23_routing_replay_plan.md), [Step 22 result](step22_tier_result.md), [Research 03 summary](../docs/reviews/research_03_summary.md), [Docs index](../docs/INDEX.md)
