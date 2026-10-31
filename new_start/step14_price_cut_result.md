---
title: Row I price-cut test - the buyer's price advantage survives a 40% Nvidia cut at about 1.9x and disappears at about 69% (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, price, nvidia, sensitivity, model]
---

# Row I: Nvidia price-cut test (31 Oct 2026)

**MODELLED.** Same model as [step 13](step13_buyer_price_result.md); [log](experiments/step14_price_cut.log). Bars written in the source before the run: **PC1** after a 40% Nvidia cut ($15,000 per GPU) the buyer still pays at least 2x less per token at our price of $2,660 per chip (central corner); **PC2** the largest cut at which the buyer still pays less (advantage above 1x, central corner) is at least 50%; **PC3** the cut at which the advantage falls to 1x is printed for both corners.

GPU price per GPU is applied to both corners here (so the "worst" column at $25,000 is 2.1x, not the 1.26x of step 13, where the worst corner also lowered the GPU price to $15,000); in the worst corner the GPU draws 100 W and our latency is 1.5x the calibrated model. Cost advantage = GPU cluster cost per token (price x 1.5 host and network) / ours.

| GPU price | cut vs $25k | central, we sell at $2,660 | central, at $1,330 (our cost) | worst, at $2,660 | worst, at $1,330 |
|---|---|---|---|---|---|
| $25,000 | 0% | 3.16x | 6.27x | 2.08x | 4.13x |
| $20,000 | 20% | 2.55x | 5.06x | 1.67x | 3.32x |
| **$15,000** | **40%** | **1.94x** | 3.85x | 1.26x | 2.51x |
| $12,500 | 50% | 1.63x | 3.24x | 1.06x | 2.10x |
| $10,000 | 60% | 1.33x | 2.64x | 0.85x | 1.70x |
| **$7,900** | **68%** | **1.07x** | 2.13x | 0.68x | 1.36x |
| $6,640 | 73% | 0.92x | 1.82x | 0.58x | 1.15x |
| $5,000 | 80% | 0.72x | 1.42x | 0.45x | 0.89x |
| $3,320 (its cost) | 87% | 0.51x | 1.02x | 0.31x | 0.61x |

## Bars

- **PC1: FAIL, narrowly.** After a 40% cut the central advantage is 1.94x (bar 2x).
- **PC2: PASS (central).** The advantage stays above 1x until a cut of about **69%** (GPU price about $7,700); in the worst corner only until about **51%**.
- **PC3:** break-even cut about 69% central, 51% worst, as above. Selling at cost ($1,330 per chip) holds an advantage in the central corner at every price down to Nvidia's own manufacturing cost (1.02x), but that leaves us no margin.

## Reading

- **The price advantage is real but not durable.** A GPU priced at about $7,700 (a gross margin of about 57% on a $3,320 cost) erases it at our 2x markup. Nvidia has that room; whether it would use it against a small entrant is a market question this model cannot answer.
- **What a price cut does not erase:** energy per token (5x to 13x lower), heat, and per-user speed (7x to 20x higher), which are properties of the design. A defensible position is one that sells on those, with the price advantage as a bonus, not the other way round.
- **Margin trade-off:** every 10% we cut our own price adds about 11% to the advantage, so a price war can be met only by giving up the margin we need for the design cost (about 113 systems at 2x markup for an assumed $150M).

## Status of row I

Conditional win on price, fragile to a Nvidia price cut (survives 40% at 1.9x, breaks even at 69%), no win on manufacturing cost. Open inputs: the packaged-chip cost ($1,000 assumed, unsourced) and the design cost ($150M assumed). Row K still waits.

Related: [Step 13 buyer price](step13_buyer_price_result.md), [Step 12 final disposition](step12_close_i_j_final.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
