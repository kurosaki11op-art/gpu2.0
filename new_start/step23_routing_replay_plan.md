---
title: Step 23 plan - replay real expert-routing traces against the step 22 speed bar (bars written before the run, 1 Nov 2026)
tags: [spark, new-start, moe, routing, expert-cache, plan, vision-research-03]
---

# Step 23 plan: expert-cache ceiling check on open traces

Why: [Vision research 03](../docs/reviews/research_03_summary.md) Part B. The step 22 speed bar needs at least 82% of each token's reads from SRAM at a cache of 1.06 times the experts one token uses. Published demand-cache numbers at about 2 times are 60% to 66% (LRU) and 79% (offline optimum, one layer). Vision's proposed first step: replay the offline-optimal policy on open traces; if it is under 0.82 the demand-cache route stops.

## Test

- **Data:** [CMU-FLAME/FLAME-MoE-Traces](https://huggingface.co/datasets/CMU-FLAME/FLAME-MoE-Traces), the 1.7B-class model (64 routed experts, top-6, shared experts always resident), final checkpoint listed (`iter_11000`), the `indices` column, streamed from the first 100,000 consecutive tokens of each of eight MoE layers (layers 2, 4, 6, 8, 10, 12, 14, 16). Consecutive rows are consecutive tokens of the pretraining stream (sequence order within documents is assumed; recorded during training, not decoding: **MEASURED routing, SIMULATED cache**).
- **Cache:** per layer, capacity of **7 routed experts** (1.06 times the 6 active, rounded up), and for comparison 13 (2.1 times, the smallest ratio in published results). Hit rate = fraction of routed-expert accesses found in the cache; every miss counts as a read over the tier (no prefetch credit, Vision's definition).
- **Policies:** offline-optimal (Belady, evict the expert used furthest in the future), LRU, and LFU over a sliding window.

## Bar (Vision's pass line, fixed now)

At capacity 7: **overall offline-optimal hit rate at least 0.82 and the 10th-percentile layer at least 0.60.** If the offline optimum is below 0.82, the demand-cache route (the speed bar of step 22) **stops**, and the result says so.

## Limits

One small model with 64 experts (a 1T-class model has more, finer experts); training-order tokens, not decode traces; batch 1 equivalent (no other requests interleaved); 100,000 tokens per layer; 1.06 times is 10.9% of experts here against 3.4% in the step 22 chip, so the comparison is by ratio to the active experts, not by share.

Related: [Step 22 result](step22_tier_result.md), [Research 03 summary](../docs/reviews/research_03_summary.md), [Research 03 Part B](../docs/reviews/research_03_routing.md), [Docs index](../docs/INDEX.md)
