---
title: SRAM bank energy model - the energy failure of the worst case is fixed on the model, the cost failure is not (31 Oct 2026, MODEL)
tags: [spark, new-start, sram, energy, bank, model, worst-case]
---

# SRAM bank energy model (31 Oct 2026)

> **Correction, same day ([like-for-like cost](step7_cost_basis_result.md)):** the cost thresholds in this note ($1,700 per chip, $190k per wafer) compare our cost with the GPU's selling price. Like for like, the cost bar fails in both corners. The energy results here stand.

**MODELLED, not measured.** Rust model [`step6_sram_bank_energy_model.rs`](experiments/step6_sram_bank_energy_model.rs), [log](experiments/step6_sram_bank_energy_model.log), and the feed into step 5 ([log](experiments/step6_feed_into_step5.log)). Bars were written at the top of the source before the first run. Question: can a weight-stationary SRAM read cost 1.6 pJ/bit or less, all in, so that the worst corner of [step 5](step5_worst_case_result.md) meets the 5x energy bar?

## The model and what supports it

Energy to read one weight bit from its bank to the multiplier beside it = macro access energy per bit, times a periphery overhead, plus wire energy from the bank to the multiplier. Macro energy scales with the square root of the bank size (ASSUMED); one **cited** datapoint anchors it: a 3 nm 563 kbit SRAM at **3.89 pJ per access** (from a web-search summary of a 3 nm FinFET dual-rail SRAM paper; **I did not open the paper, so the source is unconfirmed**; access width not stated, 64 bit ASSUMED). Overhead 1.3 and wire energy 0.056 pJ per bit per mm (0.2 fF/um, 0.75 V) are ASSUMED textbook values. Smaller banks lose density to periphery (ASSUMED efficiency steps). **I found no other sourced SRAM energy figure.**

**Cross-check (not independent evidence):** a widely quoted 45 nm table I recall from memory and have not verified (8 KB 0.16, 32 KB 0.31, 1 MB 1.56 pJ/bit per 64-bit read). After scaling the model's reference by one factor fitted to the 1 MB point, it gives 0.18, 0.36 and 2.04 for the same three sizes: the shape over bank size is consistent, which supports the square-root scaling, but the absolute level at the advanced node rests on one datapoint.

## Results against the pre-set bars

| bar | result |
|---|---|
| **S1:** a design point at or under 1.6 pJ/bit with area per GB within 1.25x of the project figure | **Pass, by a wide margin.** Every scanned point is 0.03 to 0.92 pJ/bit; the best within the area limit is a 128 KB bank, 256-bit access, 0.1 mm to the multiplier: **0.077 pJ/bit** at 420 mm2 per GB (1.23x the project 341). A 1 MB bank with 64-bit access at 0.5 mm: 0.33 pJ/bit at 341 mm2 per GB |
| **S3:** still under 1.6 with the parameters at their pessimistic ends (reference energy x2, overhead 1.6, wire 0.11 pJ/bit/mm, 32-bit reference width) | **Pass:** 0.30 pJ/bit; with the access cut to 32 bit 0.54 pJ/bit |
| **S2:** the worst corner of step 5 meets the energy bar (facility energy at least 5x below the GPU) | **Pass at every value tried.** Reticle-chip option, worst corner: **8.0x** at 0.077 pJ/bit, **6.2x** at 0.55 pJ/bit (the 32-bit pessimistic point), **5.1x** at 1.0 pJ/bit. The wafer option gives 13.4x, 9.0x and 6.9x |

So the earlier assumption of 2.78 pJ/bit was far too pessimistic for a weight-stationary design with local banks; the energy bar in the worst corner holds up to about 1.0 pJ/bit all in, and the model's own range is 0.08 to 0.55. **The energy failure of step 5 is fixed on the model**, at the price of 23% more silicon per GB (630 reticle chips instead of 511 for the 1T model with its cache at batch 1,024).

## What this does NOT fix

- **The cost failure (W1) stands.** In the worst corner the wafer system still costs about 6.5x more per token than the GPU cluster at the cited price and needs about **$190,000 per wafer system**. The reticle-chip option meets the 2x cost bar (2.5x cheaper) only while the all-in cost per packaged chip stays under about **$1,700** (the model assumes $1,330: $330 die plus $1,000 for package, board share, power and cooling, the $1,000 unsourced). At $2,330 it is 1.4x, and at $5,330 it loses.
- **The energy figure covers the weight read and its wire, plus compute, static power and the link energy already in step 5.** It does not cover clock distribution, the cache memory's own energy beyond the same constants, test and repair circuits, or power delivery losses. A 256-bit-wide bank also needs 64 multipliers per bank, and their area is not charged against density here.
- **One datapoint, one process node.** A measured macro from the chosen process would replace the cited figure.

## Status after this step

Row J (power and heat) energy: **worst-case bar passes on the model.** Row I (cost): **open on one number, the all-in price of a packaged SRAM chip (about $1,700 or less is needed).** Row B (capacity): unchanged. Next: source the packaged-chip cost (package, board share, power delivery, cooling) from suppliers or published cost breakdowns; measure GPU decode power when the RTX 3050 is idle.

Related: [Workload map](../docs/gpu_workload_map.md), [Step 5 result](step5_worst_case_result.md), [Step 2 result](step2_wafer_sram_result.md), [SRAM area and cost model](../hw/results/sram_area_cost_model.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
