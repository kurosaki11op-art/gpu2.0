---
title: SRAM area and cost model for the numeric tile
tags: [spark, result, estimate, accelerator, cost]
---

# SRAM area and cost model (28 Oct 2026)

Question: the [tile study](../../docs/L_numeric_tile_study.md) showed the big gains (Poisson 33x, 1B-parameter LLM 48x) only when about 1 GB fits on chip, with area and cost not modelled. This note models them. **ESTIMATED, order of magnitude, no foundry quote and no layout.** Script and log: [sram_area_cost_model.py](../brain/experiments/month5/sram_area_cost_model.py), `sram_area_cost_model.log`.

Inputs. REFERENCE (public reporting, not verified by us): N5 and N3E high-density bitcell 0.021 um2, macro density about 31.8 Mb/mm2 ([Tom's Hardware on N3E SRAM scaling](https://tomshardware.com/news/no-sram-scaling-implies-on-more-expensive-cpus-and-gpus), [WikiChip IEDM 2022](https://fuse.wikichip.org/?p=7343)); SRAM barely shrinks from N5 to N3 ([Bits&Chips](https://bits-chips.com/article/going-from-n5-to-n3-sram-barely-scaled-at-tsmc/)). VENDOR CLAIM: Cerebras WSE-3, 44 GB on 46,225 mm2, which is 7.6 Mb/mm2 whole-wafer. ASSUMPTIONS, unsourced and swept over three scenarios: usable density 16 to 31.8 Mb/mm2, wafer $12k to $25k, defect density 0.07 to 0.15 per cm2, HBM $10 to $25 per GB (my search found no sourced HBM price), leakage 20 to 200 pW per bit, 150 mm2 of logic, 600 mm2 maximum die.

## Result (silicon cost of the chip, base scenario; range across scenarios in brackets)

| on-chip capacity | SRAM area | dies | silicon cost | same bytes as HBM | SRAM versus HBM per byte | leakage | holds 1B int8 LLM |
|---|---|---|---|---|---|---|---|
| 64 MB | 21 mm2 | 1 | $57 ($37 to $99) | $1.0 | 60x | 0.03 W | no |
| 256 MB | 85 mm2 | 1 | $84 ($50 to $173) | $3.8 | 22x | 0.12 W | no |
| 1 GB | 341 mm2 | 1 ($108 to $443; 2 dies pessimistic) | $223 | $15 | 14x | 0.5 W | yes |
| 4 GB | 1,365 mm2 | 3 | $696 ($351 to $1,971) | $61 | 11x | 2 W | yes |
| 44 GB (Cerebras scale) | 14,667 mm2 | 25 | $7,365 ($3,340 to $21,162) | $660 | 11x | 21 W | yes |

## Reading it (ESTIMATED)

1. **Per byte, SRAM costs about 10 to 60 times what HBM does** in every scenario; the ratio is worst for small capacities because the fixed logic dominates. The gap does not close by choosing optimistic numbers (8x at best).
2. **The 1 GB tile is affordable in silicon (about $110 to $440), not impossible.** That is a single large die or two, so the 48x LLM and 33x Poisson gains cost an extra few hundred dollars of silicon, not a wafer. Against HBM that is 10 to 20 times the price of the same bytes, bought once instead of per energy bill.
3. **Capacity is not a power problem:** leakage is 0.2 to 1.6 W per GB across scenarios, small against dynamic energy.
4. **Beyond a few GB, SRAM becomes multi-die and chip-to-chip links dominate,** which this model does not price (no interconnect energy or cost). The Cerebras figure of 7.6 Mb/mm2 whole-wafer shows that real wafers spend most area on non-SRAM.
5. Consequence for the roadmap: a 1 GB class memory-on-chip design is the sensible target for the physics and LLM workloads; below 256 MB the tile is about a GPU (1.1 to 4x), so do not claim more than that for small chips.

## Caveats

Every cost is an assumption except the cited density. No packaging, test, power delivery, interconnect, design (NRE) or software cost. Yield ignores SRAM redundancy, which would improve it. A memory-heavy chip also needs bandwidth between banks and compute, not modelled. Treat ratios as direction.

Related: [Results index](INDEX.md), [Numeric tile study](../../docs/L_numeric_tile_study.md), [Arithmetic primitive shoot-out](arithmetic_primitive_test.md), [Project memory](../../docs/PROJECT_MEMORY.md)
