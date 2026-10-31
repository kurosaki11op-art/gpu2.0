---
title: Row I from the buyer's side - price against price turns the cost failure into a conditional win (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, price, margin, buyer, model, nre]
---

# Row I, buyer's price view (31 Oct 2026)

> **Correction banner, 31 Oct 2026 ([Vision review 01](../docs/reviews/vision_review_01.md), [corrections](step21_vision_corrections.md)):** corrected buyer-price results are in step 21 (1.87x centrally and 0.75x in the worst corner at $2,660 per chip, not 3.16x); the design-cost recovery arithmetic below was wrong and is corrected inline (V-08).

**MODELLED.** Same model as [steps 5 to 12](step12_close_i_j_final.md); [log](experiments/step13_buyer_price.log). Founder: no row K before winning on I. The like-for-like comparison (both machines at manufacturing cost) stays failed ([step 7](step7_cost_basis_result.md)). A buyer, though, compares **prices**: our selling price against the GPU cluster's selling price. Bar written in the source before the run: **at 2x our cost ($2,660 per chip, a 50% gross margin), worst corner, cost per token to the buyer at least 2x below the GPU cluster and energy at least 5x below.**

## Inputs and labels

- GPU price: $25,000 per GPU central, $15,000 worst corner, times 1.5 for host and network. The DGX-class figure of $25,000 to $35,000 per GPU is a third-party estimate; the cost to make one is about $3,320 (third-party), so the selling price carries a margin of about 7.5x.
- Our cost: $1,330 per chip ($330 die from the third-party N5 wafer price plus **$1,000 assumed for package, board, power and cooling, unsourced**). Reticle-chip option, 1T mixture-of-experts model, 4-bit, batch 1,024, SRAM 0.55 pJ/bit, 420 mm2 per GB.

## Results (cost advantage = GPU cluster cost per token / ours, at our selling price)

| our price per chip | markup over cost | central corner | worst corner |
|---|---|---|---|
| $1,330 | 1.0x (at cost) | 6.3x | 2.5x |
| **$2,660** | **2.0x** | **3.2x (bar met)** | **1.26x (bar missed)** |
| $3,990 | 3.0x | 2.1x | 0.84x |
| $5,330 | 4.0x | 1.6x | 0.63x |

Energy advantage at every price: 13.2x central, 6.2x worst (the bar of 5x is met).

**Bar result: FAIL in the worst corner (1.26x against 2x), PASS in the central corner (3.2x).** The worst corner stacks every pessimistic input at once (GPU at $15,000 and 100 W, our latency 1.5x the calibrated model). The markup that just reaches 2x is about **1.26x in the worst corner** (about $1,670 per chip) and about **3.2x in the central corner** (about $4,200).

## What this means

- **Row I is a conditional win for the buyer, not a manufacturing-cost win.** At a 2x markup the buyer's cost per token is about 3.2x below an H100-class cluster at central assumptions and 1.26x below in the worst corner, with energy 6x to 13x lower. The win comes from Nvidia's margin, not from cheaper silicon.
- **It is fragile against a price response.** The advantage scales with the GPU price: if Nvidia cut its price to half, the central 3.2x becomes 1.6x and the worst 1.26x becomes 0.6x.
- **Our own business needs the margin.** At 2x markup the gross profit is about $1,330 per chip and about $840,000 per 630-chip system. Recovering a design cost of, say, $150 million (**assumed**, covering a leading-node tape-out, a design team and software) takes about 113 systems, about 71,000 chips, so volume, not unit cost, decides viability. **Correction, 31 Oct 2026 (Vision review V-08): this arithmetic was wrong. $150 million / $1,330 profit per chip = 112,782 chips = 179 systems of 630 chips (113 systems recover only $94.7 million).** Volume still decides viability, at 179 systems.
- **The input that moves this most is still unsourced:** the $1,000 per chip. Each $500 of it changes the central advantage at 2x markup by about 17%.

## Status

Row I: **reopened by the founder's instruction and now conditional**: manufacturing-cost basis fails, buyer-price basis passes at central assumptions and misses the pre-set worst-corner bar. To firm up: a sourced packaged-chip cost, a sourced design-cost estimate, and a test against a Nvidia price cut. Row K stays untouched until row I is settled.

Related: [Step 12 final disposition](step12_close_i_j_final.md), [Step 11 memory study](step11_memory_technology_study.md), [Step 7 cost basis](step7_cost_basis_result.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
