---
title: Cost by process node - can we afford to build it (silicon, NRE, volume)
tags: [spark, result, estimate, accelerator, cost]
---

# Cost by process node (28 Oct 2026)

Founder's fear: after all the design, can we still beat today's GPUs on efficiency, and can we afford to fabricate? $220 for 1 GB of SRAM and about $7,000 for a Cerebras-scale part felt too high. This note separates **the cost of one chip** from **the cost of the right to make any chip**, and tries cheaper nodes. **ESTIMATED; wafer prices are REFERENCE figures from public reporting that disagree between sources and are not verified by us; densities, defect rates and the 2.5x package/test/margin multiplier are our assumptions.** Script and log: [cost_by_node.py](../brain/experiments/month5/cost_by_node.py), `cost_by_node.log`. Sources found: [wafer prices by node](https://siliconanalysts.com/data/wafer-pricing), [design and NRE cost by node](https://siliconanalysts.com/market-data/nre-design-cost), [Tom's Hardware on 3nm wafer pricing](https://www.tomshardware.com/tech-industry/tsmcs-wafer-pricing-now-usd18-000-for-a-3nm-wafer-increased-by-over-3x-in-10-years-analyst). Mask-set figures conflict between sources, and no source for shuttle (MPW) prices was found.

## 1. The $220 is the cost of one chip, not the cost to start

$220 (5 nm, 1 GB on chip) is the manufacturing cost of one die. The cost to start is the one-time NRE: masks, design, IP and verification. Reported ranges: aggregator mask-plus-NRE about $1.5M to $10M from 28 nm to 5 nm; IBS-style full-design estimates about $40 to 50M at 28 nm and $450 to 540M at 5 nm (REFERENCE, the two views differ by 10 to 50x). What a small team with licensed IP and a mature node would really pay is unknown. NRE, not the die, is what a small company cannot afford at 5 nm.

## 2. Silicon cost by node (die only, ESTIMATED)

| node | 64 MB | 256 MB | 1 GB | $ per GB of SRAM at 1 GB |
|---|---|---|---|---|
| 28 nm | $30 | $41 (2 dies) | $101 (3 dies) | $99 |
| 16 nm | $26 | $39 | $83 (2 dies) | $81 |
| 7 nm | $38 | $55 | $144 | $141 |
| 5 nm | $56 | $81 | $216 | $211 |

SRAM stopped shrinking while wafers kept getting dearer, so **mature nodes are cheaper per byte of SRAM** (about $80 to 100 per GB at 16 and 28 nm against $211 at 5 nm), at the price of more dies, more area, slower and hungrier access (the energy gap is not in this table). The 1 MB rows are dominated by an assumed logic area and are not meaningful.

## 3. Per-chip price including NRE spread over volume (1 GB chip, 2.5x package/test/margin, low and high NRE)

| node, NRE case | 1,000 chips | 10,000 | 100,000 | 1,000,000 |
|---|---|---|---|---|
| 28 nm low ($1.5M) | $1,753 | $403 | $268 | $255 |
| 28 nm high ($45M) | $45,253 | $4,753 | $703 | $298 |
| 16 nm low | $3,008 | $488 | $236 | $211 |
| 7 nm high | $270,360 | $27,360 | $3,060 | $630 |
| 5 nm low | $10,540 | $1,540 | $640 | $550 |
| 5 nm high ($480M) | $480,540 | $48,540 | $5,340 | $1,020 |

Reading (ESTIMATED): at volume the per-chip cost of a 1 GB design is a few hundred dollars on any node; **what separates a startup from a GPU maker is how many chips share the NRE.** Below about 10,000 chips only the mature node with low NRE gives a sane price.

## 4. The small chip is the affordable one

A recognition chip in the L Cortex class (about 0.5 MB of tables, 30 mm2 of logic assumed generously) costs about **$5 to $9 per die** in silicon at any node (28 nm $4.73, 5 nm $8.54). It needs no HBM and no big package, so the cost story that scares us for a 1 GB physics tile does not apply to our niche, where the model already says about 36x lower energy than a GPU-style baseline on sparse recognition (ESTIMATED).

## 5. Answers to the fears (honest)

1. **Will we stay more efficient than GPUs?** Not proven. Every number is an estimate; no GPU was measured and no chip built. Where the estimate is strong: sparse event-driven recognition (about 36x). Where it is weak: dense physics and large models at realistic capacity (about 1.1 to 4x), and GPUs keep improving. Claim only the first until silicon or a cycle-accurate model plus a GPU measurement exists.
2. **Can we afford to fabricate?** The die is cheap; the NRE and volume are the risk. The route that keeps risk low: prototype in FPGA and simulation (done), then a shared-shuttle test chip on a mature node (cost to be quoted, not found), then decide.
3. **Cost is a feature.** A user pays chip price plus electricity; a $5 to $9 recognition die with 30x lower energy is a different product from a GPU, and cost per task is a claim we can later measure.

## 6. Caveats

Wafer prices, densities, defect densities and NRE are inputs that move the answer by large factors; throughput per chip is not modelled, so cost per task cannot yet be computed; no yield learning, no test cost, no software cost.

Related: [Results index](INDEX.md), [SRAM area and cost model](sram_area_cost_model.md), [GPU and memory concept study](../../docs/concept_study_gpu_and_memory.md), [Numeric tile study](../../docs/L_numeric_tile_study.md), [Project memory](../../docs/PROJECT_MEMORY.md)
