---
title: Rows B and A - existing models on a wafer of on-chip SRAM, against a GPU cluster and a Cerebras-class wafer (31 Oct 2026, MODEL)
tags: [spark, new-start, sram, capacity, wafer, cerebras, energy, model]
---

# Rows B and A: existing models on an SRAM wafer (31 Oct 2026)

**MODELLED, not measured.** Rust model [`step2_wafer_sram_model.rs`](experiments/step2_wafer_sram_model.rs), output [log](experiments/step2_wafer_sram_model.log), GPU-power sensitivity [log](experiments/step2_gpu_power_sensitivity.log). The bars were written at the top of the source file before the first run. Models are architecture-class stand-ins (dense 7B, 70B, 405B; mixture-of-experts 671B/37B active and 1T/32B active; layer counts and widths from memory, not exact), at 16, 8 and 4-bit weights, batch 1 and 32, context 4,096.

## Cited figures used for the Cerebras-class wafer (vendor claims repeated by secondary sources, not verified here)

44 GB of on-wafer SRAM, a 46,225 mm2 wafer, 21 PB/s on-die SRAM bandwidth, about 23 kW per system (sources give 23 and 27 kW; one reports a newer variant at 43.2 PB/s). Sources: [Cerebras product page](https://cerebras.net/chip/), [TweakTown](https://www.tweaktown.com/news/96843/cerebras-wse-3-wafer-scale-ai-chip-57x-bigger-than-largest-gpu-with-4-trillion-transistors/index.html), [The Register](https://www.theregister.com/a/5289286), [Flopper spec sheet](https://flopper.io/gpu/cerebras-wse-3/spec-sheet). Groq: 230 MB SRAM per chip ([review](https://arxiv.org/html/2503.09650v1)); a 576-chip cluster for Llama-2 70B is quoted in a blog, with a caveat that it may not be the full model. Correction to the premise: these machines do run models above 13B, by adding chips or wafers; the limit is cost and chip count, not a hard size wall.

## Results against the four pre-set bars

| bar | result | verdict |
|---|---|---|
| **B1 capacity**: at least 2x the 44 GB of the cited wafer, today's technology | an SRAM-heavy wafer (80% of the area at the project's 341 mm2 per GB) holds **108 GB = 2.46x**; 217 GB (4.9x) only with two stacked memory layers, an option that needs 3D stacking and is not in the open flow. At the same density the cited wafer spends about 32% of its area on SRAM (derived, ASSUMED density). Parameters per wafer at 4-bit: 88 B (cited) against 217 B (ours) | **PASS**, but it is an area-share choice; the model does not show that the remaining 20% of the wafer can carry the compute and the routing |
| **B2 energy**: at least 5x below a GPU cluster on 70B dense and 1T mixture-of-experts, 4-bit, batch 1, pessimistic SRAM (2.78 pJ/bit) | **3.4x on both** (9.2x at 1.0 pJ/bit, 18x at 0.495) | **FAIL** |
| **B3 against the cited wafer**: energy no worse at the same SRAM energy, and at least 1.5x fewer wafers for the 1T model at 4-bit | energy is a tie (0.371 against 0.370 J per token; ours is higher by the static power it includes, so the bar as written fails by 0.3%); wafers 5 against 12 (**2.4x fewer**) | **FAIL as written** on a technicality; the wafer count part passes |
| **B4 speed**: 70B dense, 4-bit, batch 1, tokens per second per sequence at least the GPU cluster's | passes, but the figure (over 100,000 tokens per second) is only a bandwidth bound: it ignores layer-to-layer latency and synchronisation, so this bar tells us nothing | **PASS, not informative** |

## What the table says (the honest reading)

1. **The energy ratio is set by one number, the cost of reading a bit.** At batch 1 every machine reads every active weight bit once per token, so the ratio is simply HBM energy (5.74 pJ/bit) over SRAM energy per bit, softened by static power: **3.4x at 2.78 pJ/bit and 5x only if SRAM reads cost 1.87 pJ/bit or less.** Capacity does not change it: a bigger wafer lets bigger models stay on chip (more of the model is on SRAM instead of external memory), but each bit read still costs the SRAM figure.
2. **The result is very sensitive to the GPU's real power while decoding**, which I assumed as a 100 W floor (a loaded board draws more). With a board drawing 220 W during decode the ratio is 5.0x at the pessimistic SRAM energy; at 350 W it is 6.7x (bar passes); at 700 W it is 11.3x. **The 100 W floor is the weakest input in the model and favours the GPU.** Measuring a real GPU's power during batch-1 decode is the way to settle it (the founder's RTX 3050 can show the ratio of decode power to idle power; an H100-class figure would still be an assumption).
3. **Against Cerebras-class wafers the same energy constants give the same energy per token.** What differs is capacity per wafer (2.46x) and so the number of wafers for a 1T model (5 against 12). The cited 23 kW system draw, if it applies during a batch-1 step, adds only about 5% in the model, so power draw is not where a Cerebras-class wafer loses; it loses on how many wafers a trillion-parameter model needs.
4. **Batch 32 does not help the SRAM machine against the GPU** (ratios stay near 3.2 to 3.4x for 4-bit) because the model keeps both machines memory-bound and the same bit-read cost applies.
5. **Existing models need no special compute path in this model.** The multiply-add array is just part of the energy sum (0.12 pJ per 4-bit multiply-add, the assumed value, against 23 pJ to read the 4 bits of a weight from HBM or about 11 pJ from SRAM at 2.78). The memory read dominates by 100x, which is why the hybrid multiply path is not the issue.

## What this decides

- Row B is **partly covered**: capacity is a real lever (2.5x more than the cited wafer at today's SRAM density, 4.9x if stacking exists), and a 1T-parameter model at 4-bit needs 5 of our wafers against 12 of the cited ones.
- Row A energy is **not yet at its bar**: 3.4x at the pessimistic SRAM figure, 9.2x at the middle one. The question that decides it is now sharp and testable: **what does a weight-stationary SRAM read cost per bit in a real design (bank size, wiring to the MAC array)?** The project's range is 0.495 to 2.78 pJ/bit; the bar needs 1.87 or less.
- Levers not in this model, each to be tested before any claim: fewer bits per weight read (4-bit to 3-bit or entropy-coded weights; the GPU can use the same), skipping zero activations, mixture-of-experts expert caching, compute-in-memory arrays (where the read energy is largely avoided), and denser memory (eDRAM or gain cells, MRAM).

## Next step (proposal)

1. Replace the assumed 0.495 to 2.78 pJ/bit range with a bank-level SRAM read-energy model (bank size, wire length to the multiplier array) so that the 1.87 pJ/bit threshold can be judged by design rather than by a range. This is the cheapest test with the largest effect.
2. Measure decode power against idle power on a real GPU (the RTX 3050, when it is idle) to replace the 100 W assumption for the GPU side.

Related: [Workload map](../docs/gpu_workload_map.md), [Target 3 decode model](step1_lm_result.md), [New start charter](README.md), [SRAM area and cost model](../hw/results/sram_area_cost_model.md), [Docs index](../docs/INDEX.md)
