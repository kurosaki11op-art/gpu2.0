---
title: New start, target 3 step 1 - batch-1 language-model decode, GPU against weights-on-chip (result, 30 Oct 2026)
tags: [new-start, step1, language-model, model, negative-result]
---

# Target 3 step 1 result: a language-model decode model

Question, and the bar, both written into the program header before the first run: at batch 1 a GPU is memory-bound (every token re-reads all weights from DRAM). How much energy per token would a machine with the weights in on-chip SRAM save? **Pass bar:** for the smallest model of at least 1 billion parameters at 4-bit weights, batch 1, context 2,048: at least 5x lower energy per token using the PESSIMISTIC SRAM energy, and at most 1 GB of on-chip capacity (the one-die budget, about 341 mm2). If it fails, target 3 is dropped as a first target. **MODEL, analytic, every constant an assumption or a cited reference; only the 6 W idle power of the founder's laptop RTX 3050 is measured.** Program [step1_lm_decode_model.rs](experiments/step1_lm_decode_model.rs) (Rust, standard library only), log [step1_lm_decode_model.log](experiments/step1_lm_decode_model.log). Constants from the project's [SRAM cost model](../hw/results/sram_area_cost_model.md) (HBM 5.74 pJ/bit, large SRAM 0.495 to 2.78 pJ/bit, 341 mm2 per GB) and an RTX-3050-class card (168 GB/s, assumed).

## Result at batch 1, 4-bit weights, context 2,048 (chip uses the pessimistic 2.78 pJ/bit SRAM)

| model | GPU: energy per token, tokens per second | chip: energy per token | ratio (pessimistic / middle 1.0 pJ per bit) | capacity, area | note |
|---|---|---|---|---|---|
| 125M | 11.3 mJ, 1,217 tok/s | 3.1 mJ | 3.6x / 10.0x | 0.14 GB, 47 mm2 | fits easily |
| **1B (the bar)** | 62.9 mJ, 219 tok/s | 17.3 mJ | **3.6x** / 9.8x | **0.77 GB**, 262 mm2 | **FAIL: 3.6x is below 5x; capacity passes** |
| 7B | 374 mJ, 37 tok/s | 105 mJ | 3.6x / 9.5x | 4.6 GB, 1,560 mm2 | several dies, links not modelled |
| 70B | 3.3 J, 4.2 tok/s | 1.06 J | 3.1x / 6.9x | 40 GB, 13,766 mm2 | far beyond one die |

**Verdict by the pre-set bar: FAIL. Target 3 is dropped as a first target.**

## What the model says, and how firm it is

1. **The ratio is stable across model sizes and widths: about 3.6x pessimistic, about 10x with a middle SRAM value.** The outcome of the bar depends on one uncertain constant, the energy per bit of reading a 0.77 GB SRAM array: at 2.78 pJ/bit the bar fails; at 1.0 pJ/bit it passes (9.8x). That constant is a modelled range in the project, not a measurement, so the honest reading is "fails the pessimistic bar, passes the middle case", not a clear no.
2. **Where the chip's energy goes:** about 64% is still reading every weight from SRAM each token (11.1 of 17.3 mJ at 1B), 1% is arithmetic. A weight-stationary SRAM machine does not remove the weight read; it makes it cheaper per bit. Removing it needs compute in the memory itself, which is a different design (and an unproven one here).
3. **Where the GPU's energy goes at 1B and 4-bit:** about 36% DRAM traffic, about 43% the static power floor over the long step time (6 W idle, measured), the rest arithmetic. A smaller, low-static-power machine gains from that floor alone, independent of SRAM.
4. **Batching removes most of the gap.** At batch 8 the ratio is about 3.5x and at batch 64 about 3.1x (pessimistic): a data-centre GPU amortises the weight read across the batch, so the weights-on-chip idea matters at batch 1 (one user, one device) and shrinks above it. At 70B and batch 64 the chip is worse (0.3x) because the key/value cache dominates and is not shared.
5. **Throughput is the larger gap:** 10,000 tokens per second for the chip against 219 for the GPU at 1B (compute-bound at the assumed 10 tera multiply-adds per second against 168 GB/s of DRAM bandwidth), a time advantage of about 45x that does not turn into an energy advantage of the same size.
6. **Not modelled:** interconnect between dies, software, the cost of packaging and design, grouped-query attention (which would shrink the cache), and any analog or in-memory compute.

## What it means for the new start

Two of two new targets tested failed their pre-set first-step bars: irregular workloads ([step 1](step1_result.md): 1.9x to 2.9x memory waste) and language-model decode (3.6x pessimistic). In both, a GPU's inefficiency is a modest factor in a model that favours it, with large gains only when sparse or small work fits on the chip, which is the version 1 recognition niche. That consistent pattern is itself the finding: **the premise that a different architecture beats a GPU by a wide margin on general workloads is not supported by our models**; the credible claim is narrow (small, sparse, on-device work), with an energy edge that is mostly a chip projection.

Related: [New start charter](README.md), [Step 1 result (irregular workloads)](step1_result.md), [SRAM area and cost model](../hw/results/sram_area_cost_model.md), [Target options](../docs/new_start_target_options.md), [Docs index](../docs/INDEX.md)
