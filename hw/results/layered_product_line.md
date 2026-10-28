---
title: Layered product line - separate layers, pay and power only for what a customer uses
tags: [spark, result, estimate, accelerator, cost, architecture]
---

# Layered product line (28 Oct 2026)

Founder's idea: build separate layers (L Cortex, L Deep, and new layers for dense matrices, physics, rendering, big memory), so that each customer receives, powers and pays for only the layers needed. This note tests the economics before anything is designed. **ESTIMATED, with ASSUMED inputs** (16 nm-class node, same wafer, density and defect inputs as [cost by node](cost_by_node.md); layer sizes, 10% link overhead per chiplet, $20 packaging per chiplet and the two design-cost cases are ours). Script and log: [layered_product_model.py](../brain/experiments/month5/layered_product_model.py), `layered_product_model.log`.

Layers (SRAM MB, logic mm2, assumed): Cortex 0.5 and 30; Deep 4 and 40; Dense 64 and 90; Physics 256 and 110; Render 256 and 100; Memory block 1,024 and 10. Products: A edge sensor (Cortex), B assistant (Cortex, Deep), C vision and language server (Cortex, Deep, Dense, 1 GB memory), D science (Physics, Dense, 1 GB), E everything. 10,000 chips per product.

## Result (price per chip = 2.5 x silicon + packaging + NRE share)

| product | silicon needed | custom die per product | chiplet kit | one universal die |
|---|---|---|---|---|
| A edge sensor | 30 mm2 | $246 | $434 | $644 |
| B assistant | 73 mm2 | $374 | $463 | $644 |
| C vision and language | 794 mm2 | $1,005 | $686 | $644 |
| D science | 978 mm2 | $1,185 | $714 | $644 |
| E everything | 1,297 mm2 | $1,916 | $851 | $644 |

(lean design-cost case, $0.03M per new logic mm2; with the IBS-like $0.3M case every price is 4 to 6x higher and the ranking is the same: universal $2,696, kit $2,486 to $2,903, custom $1,056 to $12,176.)

Total one-time cost (NRE): five custom dies $39M (lean) or $272M (IBS-like); one universal die $16M or $119M; the chiplet kit $20M or $123M.

## What it shows (ESTIMATED)

1. **The layered idea cuts the one-time cost roughly in half against building a separate die for each product ($272M down to $123M, or $39M down to $20M), because each layer is designed once and reused.** That is the main economic benefit, and it is exactly the cost that blocks a small company.
2. **It does not beat one universal die on total NRE** (about the same), and it loses on the large products to the universal die when volume is shared, because of link overhead and packaging. Its advantage is that a customer who needs only A or B does not pay for 1.3 GB of silicon, and the company can ship the first layer long before the others exist.
3. **Power is not a reason by itself.** All the memory powered idles at about 0.77 W; a monolithic die can also power-gate unused blocks, and GPUs already partition and gate. Event-driven layers draw almost nothing when idle either way. The saving from not including a layer is silicon cost, not watts.
4. **The real risks are not in this model:** energy and latency of traffic between chiplets (not modelled), a common layer interface and compiler (software cost), and the fact that each new layer is a new design that must first win its own test. A layer earns its place only if a test shows it beats the GPU on its job, as for L Cortex (about 36x in the model); for physics and rendering the model shows only 1.3 to 4x at realistic capacity, so those layers are not yet justified.

## Recommendation (for discussion, not a decision)

Adopt the layer idea as the product architecture: a fixed interface and a memory block shared by all layers; build in the order Cortex, Deep, memory block; add a dense, physics or render layer only after its own energy and accuracy test passes. Do not promise "everything a GPU does" until each layer has its test.

## Caveats

Layer areas are guesses; die-to-die energy and bandwidth, thermal limits, test cost of multi-chip packages, and software are not modelled; NRE allocation across products is a choice (equal split here).

Related: [Results index](INDEX.md), [Cost by node](cost_by_node.md), [SRAM area and cost model](sram_area_cost_model.md), [Numeric tile study](../../docs/L_numeric_tile_study.md), [Accelerator design](../../docs/L_accelerator_design.md)
