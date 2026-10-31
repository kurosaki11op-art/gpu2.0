---
title: Workload map - what a chip must do to replace a GPU, one mechanism, one bar and one status per row (31 Oct 2026)
tags: [spark, gpu, workloads, map, plan, accelerator]
---

# Workload map (31 Oct 2026; a plan, no experiment was run for it)

Founder's goals (31 Oct 2026): the chip should do what a GPU does, but not in the way a GPU does it: more efficient, more effective, if possible more accurate and more reliable. **New constraint, same day: the chip must run all existing models (dense transformers and the rest), not only ternary ones.** Reason, in the founder's words: ternary models have not been shown to be reliable or to beat a transformer on accuracy, the L chip won on efficiency but lost on accuracy, and the L model is failing on accuracy too. A chip that only runs models nobody has validated cannot replace a GPU.

This note is the successor to the [workload census](gpu_workload_census.md) (the 19 patterns). It groups them into rows a design can answer, and for each row writes the mechanism, the evidence we hold, the bar and the status. **Every status is "not covered" or "partly covered" until a test with a pre-set bar passes; nothing here is a result.**

## What "run existing models" changes

1. **The matrix-free default stops being the base.** Existing models are trained with multiply-accumulate in mind (FP16, BF16, INT8, INT4 weights). Running them unchanged needs a multiplier and matrix path. Under the founder's 28 Oct rule that is a labelled **hybrid component**, and for this row it is the main component, not an exception. The add-only counting paths stay as the route for the workloads and layers where a test shows they pay.
2. **The efficiency win cannot come from removing multiplies.** It has to come from where the GPU actually wastes energy: moving weights from external memory (the capacity and bandwidth problem), precision chosen per layer, skipped zeros and skipped experts, and keeping data on chip. Our own [GPU problem analysis](gpu_problem_analysis.md) and the [target 3 model](../new_start/step1_lm_result.md) point the same way: 3.6x energy per token at pessimistic SRAM, 9.8x at optimistic (MODELLED), bar 5x.
3. **Accuracy is then inherited, not claimed.** An existing model run at its trained precision gives the same answers as on a GPU (the pass criterion is bit-exact or within a stated tolerance against the GPU run). Lower precision (INT8, INT4) changes answers; its accuracy loss is measured per model, never assumed. "More accurate than a GPU" is only possible where our flag or a cascade decides which answers to trust (as in the recognition cascade: 91.24% against 91.53% for the fallback alone, MEASURED on the ESP32 run, flagged images going to the stronger model).
4. **Reliability is a hypothesis to test**, not a property: a fault-injection run (flip stored bits at a stated rate, measure accuracy) on a counting table, a dense INT8 layer and an ECC-protected store, side by side.

## The map

Status words: **not covered** (no mechanism tested), **partly** (some evidence below the bar), **covered** (a passing test exists). No row is "covered" today for existing large models.

| # | row (census patterns) | mechanism we would use | evidence held (label) | bar to beat, written before any test | status |
|---|---|---|---|---|---|
| A | **Existing-model inference, dense** (14, 1) | INT8 / INT4 multiply-add array as a labelled hybrid unit; weights stationary in on-chip memory; per-layer precision; same answers as the GPU | Lane/mesh matrix multiply, bit-exact in v1 (SIMULATED RTL, dropped design); no large-model run | a real model's outputs match the GPU run (INT8: accuracy within 0.5 point of the float model, measured), energy per token at least 5x below a GPU at batch 1 with the SRAM constants stated | not covered |
| B | **Capacity: models of billions to trillions of parameters** (14) | weight tiers: hot weights on chip, the rest in dense memory read ahead; MoE so only active experts move; low-bit storage (INT4, entropy coding); many chips with stationary weights | target 3 model: 3.6x / 9.8x (MODELLED), bar missed at pessimistic SRAM; wafer-scale capacity arithmetic in the journal (about 200 GB for 1T ternary, about one wafer of SRAM) | energy per token and chip count for a 1T-parameter mixture-of-experts model against a GPU with HBM, at least 5x at the pessimistic SRAM value | partly (model only) |
| C | **Attention and long context** (14) | key-value cache kept compressed and on chip; sparse or retrieval attention where a test shows equal accuracy | none yet | perplexity within 1% of full attention at the same context, with less memory traffic | not covered |
| D | **Sparse and irregular work** (2, 9, 6, 12) | event-driven row lookups, hash tables, scans (the L Cortex path) | graph waste model 1.9-2.9x (MODELLED), bar 5x missed; recognition 36x (ESTIMATED, small tasks only) | 5x less memory traffic on R-MAT graphs at equal results | partly (below bar) |
| E | **Small on-device recognition with confidence** (14) | L Cortex + L Deep + reject flag | 89.73% (SIMULATED bit-exact, MEASURED on ESP32: 8.69 ms vs 255.2 ms CNN); synthesis 0.186 mm2 logic (ESTIMATED) | already set in the cascade demo | covered at small scale, accuracy 1-2 points below a CNN |
| F | **Training** (15) | the chip does not train; training stays on a GPU | counting-rule learning on chip (SIMULATED), no backprop | none set | not covered, by decision |
| G | **Exact numerics: FP32/FP64, spectral, N-body, grids** (3, 4, 5, 7) | a floating-point unit, not our mechanism; best case is equal results at lower energy | v1 lane model only | identical results to an FP64 reference within a stated error, energy against a GPU | not covered |
| H | **Graphics and fixed-function** (16, 17, 18, 19, 8, 13) | dedicated blocks, as on a GPU | none | n/a: a dedicated block per job is already cheap on a GPU, so no efficiency claim is available without a design | not covered, likely out of scope |

## Update, 31 Oct 2026: rows B and A run

The model was run ([result](../new_start/step2_wafer_sram_result.md), MODELLED): **row B capacity passes its bar** (2.46x the cited 44 GB wafer; 5 wafers for a 1T model at 4-bit against 12), **row A energy misses its bar** (3.4x against 5x at the pessimistic SRAM energy; 9.2x at 1.0 pJ/bit; 5x needs 1.87 pJ/bit or less). Both rows stay "partly covered"; the open question is the real read energy per bit of weight-stationary SRAM, and the GPU's real decode power.

## Founder's additions, 31 Oct 2026: cost, power and cooling, training (rows I, J, K; bars not yet written, nothing run)

The founder asked for a chip that is also cheaper than a wafer-scale machine, lighter on power, heat and cooling water, and needs less training. Correction recorded the same day: **memory is not "solved"**. Rows B and A are a model; the capacity result is an area-share calculation, the energy bar failed (3.4x against 5x at the pessimistic SRAM energy), and the model has no cost, yield, power-delivery, latency or software terms, which are the likely reasons wafer-scale machines do not simply add more SRAM.

| # | row | what is known (labels) | what a test must show | status |
|---|---|---|---|---|
| I | **Cost per token and per GB** | SRAM about $174-223 per GB in the project cost model (ESTIMATED); HBM per GB not yet sourced; wafer cost, yield and defect redundancy not modelled | cost per million tokens of a 1T model against a GPU cluster, from sourced wafer, memory and yield figures | not covered |
| J | **Power, heat and cooling** | energy per token is the lever (heat is the energy used); cited wafer about 23 kW per system (vendor claim); the model gives the energy per token only | watts per mm2 against what air or liquid cooling can remove, and energy per token including the cooling overhead; any water figure must be sourced | not covered |
| K | **Training cost / learning with little training** | counting rules learn a small task in one pass (60,000 images in about 16 s at 50 MHz, SIMULATED) at 88.85% against 90-92% for CNNs; counting tables 2.33 bits per character against 2.25-2.28 for an undertrained transformer on Tiny Shakespeare (MEASURED, a toy); a new class learned from dreams costs 0 to 5 points against replay | energy and data to reach a stated accuracy, ours against a standard model trained with a stated budget, at one task bigger than a toy | not covered |

## Order of work (proposal, for the founder to confirm)

1. **Row B, then A** (the capacity and dense paths, because they decide whether "run existing models" can beat a GPU at all). First test: extend the Rust decode model of target 3 with the weight-tier axis and the dense multiply-add unit, **with the founder's models and existing ones (for example a 7B and a 70B dense model, one mixture-of-experts model) as inputs**. Bar above; written before the run.
2. **Row A accuracy check on a real small model** (an INT8-quantised model run against its float version on the founder's RTX 3050 when it is idle), to measure the accuracy loss instead of quoting it.
3. **Reliability test** (fault injection), small and cheap, on rows A and E.
4. Rows C and D follow whichever of A or B survives. Rows F, G, H stay stated gaps unless a bar is passed.

## What this means for the existing L chip

The recognition chip (row E) remains valid and stays as the on-device recognition option with the confidence flag. It is not the answer to rows A and B; those need the hybrid multiply path and the memory-tier design, and they are untested.

Related: [GPU workload census](gpu_workload_census.md), [GPU problem analysis](gpu_problem_analysis.md), [New start charter](../new_start/README.md), [Target 3 decode model](../new_start/step1_lm_result.md), [Founder ternary context](founder_ternary_lm_context.md), [Status, 31 Oct 2026](status_31oct.md), [Docs index](INDEX.md)
