---
title: Cost and power as limitations - why a memory-rich chip costs so much, and what we can work on
tags: [spark, result, estimate, accelerator, cost, power]
---

# Cost and power as limitations (28 Oct 2026)

**Note (28 Oct 2026):** the 1M to 4B-parameter model sizes discussed here belong to a future language model (L Language), not to L Deep, which is the clause layer (about 60 KB). The cost and power arithmetic is unaffected.

Founder's request: take the cost of building a chip with 1 to 2 GB of SRAM, why placing memory in a chip costs so much, and why such chips use so much power, as the limitations, and work on them. **ESTIMATED throughout; inputs are the assumed or unverified ones listed in [cost by node](cost_by_node.md); rupees at an assumed 85 per dollar.** Script and log: [cost_constrained_design.py](../brain/experiments/month5/cost_constrained_design.py), `cost_constrained_design.log`. A first version of the script scaled logic by node squared and gave absurd die counts (60 dies at 28 nm); fixed with assumed density ratios (logic x12 at 28 nm, x5 at 16 nm relative to 5 nm).

## 1. What 1 to 2 GB costs (ESTIMATED)

| node | memory | silicon per chip, Rs thousands: add-only tile 0.005 mm2 / Cerebras-size tile 0.025 mm2 | dies |
|---|---|---|---|
| 28 nm | 1 GB | 13 / 44 | 5 / 13 |
| 28 nm | 2 GB | 28 / 88 | 9 / 26 |
| 16 nm | 1 GB | 11 / 31 | 2 / 6 |
| 16 nm | 2 GB | 21 / 61 | 4 / 12 |
| 5 nm | 1 GB | 16 / 32 | 1 / 2 |
| 5 nm | 2 GB | 33 / 73 | 2 / 3 |

The silicon of one chip is **tens of thousands of rupees, not lakhs**, unless many dies are needed. The earlier "$216, one die" for 1 GB assumed 150 mm2 of shared logic; with logic beside every 48 KB bank (the Cerebras style) the same 1 GB is 2 dies at 5 nm and 6 to 13 dies on mature nodes.

**The lakhs and crores are the one-time cost (NRE: masks, design, IP, verification):** Rs 12.8 crore (28 nm), 23.8 crore (16 nm), 85 crore (5 nm) in the low case; Rs 382, 850 and 4,080 crore in the high case. Per-chip price including NRE (add-only tile, 1 GB, 2.5x package and margin): at 100,000 chips Rs 35k (28 nm), 29k (16 nm), 49k (5 nm) with low NRE; at 1,000 chips Rs 161k to 891k with low NRE and crores with high NRE. So **one chip with 1 to 2 GB is a tens-of-crores project at best; it is not reachable with Rs 70 to 80k and it should not be the first chip.**

## 2. Why it costs so much (the cost drivers)

1. **NRE dominates:** one set of masks, the design team, licensed IP, verification, test chips. It is paid once, so it is cheap per chip only at volume.
2. **SRAM area:** a bit costs a fixed area (0.021 um2 cell, about 24 Mb per mm2 usable) and the bit cell stopped shrinking at 5 nm and 3 nm; 1 GB is 8.6 billion bits.
3. **Yield:** big dies fail more often, so die cost rises faster than area; many small dies avoid this but need links.
4. **Logic beside the memory:** every bank needs compute, and for 21,800 banks that logic is as large as the memory itself.
5. **Packaging, test, power delivery, cooling:** 2.5x on silicon is an assumption; Cerebras needs over 20,000 A and liquid cooling.

## 3. Why it uses so much power (the power drivers, with our own evidence)

1. **Moving data, not arithmetic:** external memory is 74 to 98% of energy in memory-bound kernels (tile model); reading weights is 91% of L Deep's energy per token.
2. **Reads from big arrays cost more:** 10 pJ per word at 8 KB against 100 pJ at 1 MB (45 nm constants); the energy of a read grows with array size.
3. **Clocking and leakage:** our own layout spent about 6 nJ every clock cycle clocking 20,000 flip-flops and clock buffers; SRAM macros are charged per clock edge whether selected or not; leakage grows with bits (0.2 to 1.6 W per GB, assumed 20 to 200 pW per bit).
4. **Overhead the operation count hides:** Cortex's layout is 20 to 28 times above its operation count.

## 4. What we can work on (levers, each with a test; hypotheses until run)

| lever | what it attacks | evidence so far | test |
|---|---|---|---|
| Store fewer bits: ternary 2-bit or packed 1.58-bit, event-indexed tables, compression | SRAM area, reads | 4B parameters = 4 GB int8, 1 GB ternary, 0.8 GB packed (arithmetic) | bytes per class of an event-indexed table on our own code (measurable now) |
| Smaller tile logic: add-only tiles, no multiplier | logic beside memory, the largest hidden cost at 1 to 2 GB | 0.005 mm2 is an assumption; Cerebras core is 0.05 mm2 | synthesise an add-only tile in the open flow and measure its area |
| Mature node plus fewer dies | NRE and wafer cost | SRAM per GB is about half the cost at 16 and 28 nm (cost by node) | quote request; energy per access at the node |
| Denser or non-volatile memory cells | SRAM area, leakage, reload | gain cell 1.5 to 2x, MRAM 2 to 3x (paper claims, unverified); not in cheap shuttles | model with refresh and write energy |
| Keep a small working set on chip and the bulk in cheap external memory | cost per GB (SRAM is 10 to 60x HBM per byte) | brings the memory wall back; sparse reads (13% active) may keep traffic low | traffic per task for event-indexed tables against dense |
| Share the one-time cost across layers and products | NRE | layer kit halves NRE ([layered product line](layered_product_line.md)) | reuse count and interface design |
| Banking, clock gating, skipping, retention | power | 3 to 5x banking (model); layout power 366 to 47 mW with gating (ESTIMATED) | close the Cortex layout gap, then run the dispatch system test |
| Open-source flow and mature-node open IP | design cost | our own SKY130 flow already exists | list the IP we would otherwise license |

## 5. How a chip that costs lakhs can still be efficient

Efficiency (energy per task) and cost (rupees) are separate axes. A GPU also costs lakhs (an H100 is reported at roughly $25,000 to 30,000, unverified, about Rs 21 to 26 lakh); the question is cost per task: price over the chip's life plus electricity and cooling. Our model says energy per task can be far lower for sparse recognition (35.8x, ESTIMATED), but **cost per task cannot be computed yet because throughput is not modelled**. That is a gap to close before any claim of cost advantage.

## 6. Recommendation

1. Treat cost as a design constraint with a number: target a stated chip price at a stated volume, and let that set the memory per chip.
2. Work in this order: store fewer bits (test now), measure the add-only tile area, close the Cortex layout power gap, then the system dispatch test.
3. Keep the pitch chip small and on FPGA; present 1 to 2 GB as a projection with its cost range and unknowns stated.

Related: [Results index](INDEX.md), [Cost by node](cost_by_node.md), [SRAM area and cost model](sram_area_cost_model.md), [Layered product line](layered_product_line.md), [One chip, three layers](one_chip_three_layers.md), [GPU and memory concept study](../../docs/concept_study_gpu_and_memory.md)
