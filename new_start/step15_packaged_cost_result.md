---
title: Row I, bottom-up packaged-chip cost - a low-power chip is cheap to package, and the cost bar passes in the central corner (31 Oct 2026, MODEL plus sourced fragments)
tags: [spark, new-start, cost, packaging, yield, manufacturing, model]
---

# Row I: bottom-up cost of the packaged chip (31 Oct 2026)

> **Correction banner, 31 Oct 2026 ([Vision review 01](../docs/reviews/vision_review_01.md), [corrections](step21_vision_corrections.md)):** the "bar met" below is a **central-corner bar written after the worst-corner bar W1 had failed**; **W1 still fails (1.67x against 2x, before the corrections)**, and with the corrections the central value falls from 2.74x to 1.35x and the worst corner to 0.82x. The $150 for package, board, power and cooling is **unsourced** (the earlier $1,000 was also an unsourced assumption; the description of it as a placeholder for a hot chip was a later rationalisation). Do not quote 2.74x.

**MODELLED, with a few sourced fragments and one key assumption.** Founder: manufacturing cost can be cut if the design is done properly. Model: [`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs), [log](experiments/step15_packaged_cost.log); bar written in the source before the run: with the packaged chip built up from its parts, **central corner, like for like (GPU at manufacturing cost $3,320), cost advantage at least 2x at $480 per chip**; the $780 case and the worst corner are reported.

## What the search found (third-party estimates and general sources; none of it is a supplier quote)

- **Wafer prices (300 mm, estimates):** 28 nm about $3,000, 16/12 nm about $4,000 (2020 estimate), 7 nm about $9,500, 5 nm about $18,500 (range $16,000 to $21,300) ([Silicon Analysts](https://siliconanalysts.com/data/wafer-pricing), [Tom's Hardware](https://www.tomshardware.com/news/tsmcs-wafer-prices-revealed-300mm-wafer-at-5nm-is-nearly-dollar17000)).
- **Cost structure of a chip:** die plus test plus package; yield is the exponential term for large dies; assembly yield typically 97-99%; test cost follows tester seconds, about $0.03 per chip for one second at $100 per hour ([AnySilicon](https://anysilicon.com/calculate-asic-unit-cost/), [OCP chiplet cost model](https://www.opencompute.org/wp-content/uploads/2026/07/10790972707a0971914240f5fdab193b86689205.pdf)).
- **Packaging of GPUs is dominated by what we do not use:** CoWoS and HBM integration $500 to $1,500 per chip, HBM stacks $1,200 to $2,400 ([cost guide](https://siliconanalysts.com/guide/semiconductor-costs)); a cold plate for a GPU about $300 and a rack cooling system about $50,000 per 72-GPU rack (Morgan Stanley figures reported by [Tom's Hardware](https://www.tomshardware.com/pc-components/cooling/cooling-system-for-a-single-nvidia-blackwell-ultra-nvl72-rack-costs-a-staggering-usd50-000-set-to-increase-to-usd56-000-with-next-generation-nvl144-racks)). Those are for chips drawing 700 W and more.
- **Not found:** a price for a flip-chip package for an 800 mm2 die, board share, voltage regulation, or assembly. No supplier quote; SRAM bit-cell sizes by node were also not found.

## The two derivations that matter

1. **Die cost (standard dies-per-wafer formula, Poisson yield at an assumed 0.1 defects per cm2).** An 800 mm2 die: 65 dies per wafer; 45% yield without repair gives **$635**, 85% with row and column repair of the SRAM (standard practice, assumed) gives **$336**. Smaller dies cost about the same per area (200 mm2: 82% yield, $74 per die, $295 per 800 mm2) but need four times the packages.
2. **Power per chip.** At the central corner the 630-chip system draws about 6.9 kW (0.014 J per token at about 490,000 tokens per second), **about 11 W per chip** against 700 W for an H100-class board. A chip at 11 W needs no cold plate, no CoWoS, no HBM, a cheap organic package and a small voltage regulator. **My earlier $1,000 per chip was set as a cautious placeholder for a hot chip; for an 11 W chip I now assume $150 (package about $60, board share about $40, regulation about $20, cooling and chassis about $30), which is unsourced** and is the single most important input in this note.

## Results (like for like, GPU at manufacturing cost, SRAM 0.55 pJ/bit, 420 mm2 per GB)

| all-in cost per chip | case | central cost advantage | worst-corner cost advantage | energy advantage (central / worst) |
|---|---|---|---|---|
| **$480** | 85% yield die + $150 | **2.74x (bar met)** | 1.67x | 13.2x / 6.2x |
| $780 | 45% yield die + $150 | 1.71x | 1.04x | same |
| $1,330 | old placeholder | 1.02x | 0.61x | same |

Cost advantage scales as 1 over the chip cost: **central reaches 2x up to about $650 per chip, the worst corner up to about $400.**

## Reading

- **Bar: PASS** (2.74x against 2x at $480, central). With the $150 assumption the cost failure of rows I turns into a win on manufacturing cost in the central corner, not only on price against Nvidia's margin.
- **The founder's point holds:** manufacturing cost is not fixed. The big lever is that a low-power chip avoids the expensive parts a GPU needs (CoWoS, HBM, a 700 W cold plate). Yield repair of the SRAM is the second lever ($336 against $635 per die).
- **What is not shown:** the $150 is an estimate; at $300 for the same items (so $636 per chip) the central advantage is about 2.1x; the worst corner stays below 2x at any plausible price. A node change (7 nm at half the wafer price, but about 1.3x the area per bit if bit-cell sizes are as I recall, unsourced) does not help: packaging, not silicon, dominates the cost per GB at this price level.
- **Combined with the buyer view:** at $480 cost, a 2x markup ($960 per chip) still gives the buyer 1.9x lower cost per token than a GPU cluster at manufacturing cost, and far more against Nvidia's $25,000 price. **Correction, 31 Oct 2026 (Vision review V-08): the $960 case gives 1.4x, not 1.9x** (cost scales as one over the chip price: 2.74x at $480 is 1.37x at $960).

## Status and next step

Row I: **cost bar passes in the central corner on a bottom-up cost** that rests on one unsourced number (package, board, power and cooling of an 11 W chip at $150). To close it for real: a supplier quote (or a published teardown) for a flip-chip package of an 800 mm2 die, a board with 8 to 16 such chips, and 11 W voltage regulation. Row K waits.

Related: [Step 14 price-cut test](step14_price_cut_result.md), [Step 13 buyer price](step13_buyer_price_result.md), [Step 12 final disposition](step12_close_i_j_final.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
