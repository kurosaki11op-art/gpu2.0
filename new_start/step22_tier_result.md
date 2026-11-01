---
title: Step 22 result - an SRAM plus DRAM tier fixes the chip count but the speed advantage needs 82 to 95 percent of reads from SRAM (1 Nov 2026, MODELLED)
tags: [spark, new-start, tier, capacity, result, vision-research-02, vision-research-01]
---

# Step 22 result (1 Nov 2026)

**MODELLED, not measured.** Plan and bars (written before the run): [step 22 plan](step22_tier_plan.md). Model [`step22_tier_model.rs`](experiments/step22_tier_model.rs), [log](experiments/step22_tier_model.log). Every parameter is ASSUMED unless the plan says otherwise. 1T mixture-of-experts, 32B active, 4-bit, context 4,096, batch 1.

## Numbers

- **GPU cluster:** 7 H100-class GPUs hold the weights and cache (500.4 GB); one token reads 16.4 GB; at 80% of the memory floor the cluster gives **1,141 tokens/s per user**, 0.755 J per token.
- **Our chip with no tier (SRAM only):** 329 chips (47x the GPUs), 19,787 tokens/s (17x), 0.072 J per token. Fails the count bar by a wide margin, as before.
- **With a DRAM tier per chip (HBM-class):**

| tier per chip | chips | x GPUs | count bar (at most 2x) | SRAM hit rate h needed for 4x speed (0.8 / 1.6 TB/s tier) |
|---|---|---|---|---|
| 24 GB | 20 | 2.9x | **FAIL** | 0.84 / 0.67 |
| 48 GB | 11 | 1.6x | **PASS** | 0.91 / 0.82 |
| 96 GB | 6 | 0.9x | **PASS** | 0.95 / 0.90 |

- **The speed bar (at least 4x) is met only if 82% to 95% of the bytes read per token come from SRAM.** h is UNKNOWN. A mixture-of-experts token reads 16 GB of a 500 GB model (3.2%); the SRAM of the 11 chips holds 17 GB (3.4% of the weights). If routing spreads reads evenly over the experts, **h is about 3 to 4%, and the speed is 0.5x to 1x the GPU cluster's** (the h = 0 to 0.25 rows: 0.46x to 1.17x), not 4x. Only strongly skewed routing, with the hottest 3% of the weights serving more than 80% of reads, would reach the bar. I know of no evidence for that skew; the real routing statistics of any specific model are not in these notes.

## Verdict on the bars

- **G3-count: PASS** at 48 GB or more of tier per chip.
- **G3-speed: not met on any evidence in hand.** It holds only at an SRAM hit rate of 0.82 or more, which is unsupported. **Both bars together: not shown.**
- **What a tiered chip is:** a GPU-like card (an HBM-class stack next to a large SRAM cache) whose advantage is **chip count and cost, not speed** unless caching is very good. At h of 0.5 the energy per token is 1.8x lower than the GPU's, at h of 0.9 5.4x (not the 10x of the SRAM-only case).

## Caveat added the same day, after a literature search ([watch list](../docs/watch_radar.md))

The "uniform routing gives h of 3 to 4%" reading above ignores **time locality and prediction**. Published work reports much higher hit rates for small expert caches: 72% to 92% with predicted routing (ExpertFlow, MoE-Beyond), and an ICLR 2026 study of 20 models says a cache of about twice the active experts is a good balance for most of them. Our 17 GB of SRAM is about 1.06 times the 16 GB of weights one token reads, so h is plausibly well above 4% but is **not established at 82% or more**. The sources disagree on how skewed popularity is, and they measure different things (hit rate over short windows, per layer, with prediction). So the correct statement is: **h is unknown between a few percent and about 90%**; the speed bar needs 82% to 95%; the next step is to read the primary papers and compute h for a 1T-class model's routing trace.

## Cost (reported beside the bars, weak)

Cost per million tokens: GPU cluster $0.51 (manufacturing-cost basis, $3,320 per GPU) to $3.68 (selling-price basis, $25,000). Tier chip at 48 GB and 1.6 TB/s: $0.255 at h = 0 down to $0.037 at h = 0.9. **Do not quote this as a cost advantage.** It rests on an assumed $605 per chip (die plus host adder) plus $15 per GB of tier memory, against an H100-class cost of $3,320 that is itself an estimate; both are unsourced for our volume, and Vision's research suggests the real costs are higher for a new entrant.

## What it means

- A tier solves capacity the way the incumbents do: more memory next to each chip. That erases the large-capacity gap but also the unique selling point, which was on-chip speed. The remaining value is whatever our cost and energy per bit are, and those are still unsourced.
- **The result depends entirely on h.** The cheapest next step is to measure it: take the expert-routing statistics of a public mixture-of-experts model from published work or a run on a small one, and compute the hit rate a 3%-of-weights cache would reach. If routing is near-uniform, tiering gives no speed advantage; if it is skewed enough, the design survives. That is a one-script task with a pre-set bar (h at least 0.82).
- **Limits:** no contention or queueing; the 50 microsecond overhead is assumed; batch 1 only (at batch 64 and above a mixture-of-experts model touches almost every expert, so h falls further); tier energy is a per-bit figure; GPU speed is a floor-based estimate at 80%.

Related: [Step 22 plan](step22_tier_plan.md), [Weakness A result](../hw/gpu/weakness_A_result.md), [Step 21 corrections](step21_vision_corrections.md), [Research 01 summary](../docs/reviews/research_01_summary.md), [Docs index](../docs/INDEX.md)
