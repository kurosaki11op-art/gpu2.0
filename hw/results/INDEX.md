---
title: Results index
tags: [spark, index, results]
---

# Results index

Labels: MEASURED, SIMULATED, ESTIMATED, PROJECTED. JSON files beside each note hold the raw numbers.

## L Cortex (Phase C, now)

- [Month 3 results](cortex_month3.md): RTL bit-exact, bitstream with timing met, host + demo, 10-stage test (SIMULATED).
- [Month 2 results](cortex_month2.md): memory 137x smaller, one rule, integer chip model + RTL bit-exact (SIMULATED).
- [New conditions for known classes](cortex_new_condition.md): limit found (domain shift) and the context-memory fix (SIMULATED).
- [Brain-strict redesign tests](brain_strict_redesign.md): few-label learning, sleep from inside, on-chip detectors, pruning, and the failures (19 Oct, SIMULATED).
- [Sound chip (raw sound in)](cortex_sound_chip.md): cochlea + general encoder + core in RTL, whole chain bit-exact (SIMULATED).
- [L Cortex vs HDC](cortex_vs_hdc.md): ahead of the closest prior art on digits and sound, level on clothing (SIMULATED).
- [ASIC estimate (SKY130)](cortex_asic_estimate.md): ~18.8 mm2 with open SRAM macros, logic < 1 mm2; bit-exact with the SRAM models (ESTIMATED).
- [Energy estimate](cortex_energy_estimate.md): ~74x less energy per decision, ~200x per learned example incl. sleep (ESTIMATED).
- [Month 2 running log](cortex_month2_log.md): every memory-shrink test, including failures (SIMULATED).
- [Month 1](cortex_month1.md): accuracy gap closed on digits, clothing, spoken words (SIMULATED).
- [First proof](cortex_proof.md): no forgetting, exact merge, few-shot loses (SIMULATED).

## Matrix-free lookup core and real-model drafting (Phase B)

- [Token-level lookup on a real model](token_lookup_real.md): tables tie prompt lookup; chat model 1.04 on prose (MEASURED).
- [Matrix-free predictor](matrix_free.md): lookup tables match the network on bytes, hash corrections (SIMULATED).
- [Size study](size_study.md): shrinking the network before fabrication (SIMULATED).

## L v1/v2 beside a GPU (Phase A)

- [Real 9B model, first test](real_model_test_qwen3.5_9b.md): draft 1.51 tokens/pass, answer mode ~6% (MEASURED).
- [Real 9B model, test 3](real_model_test3_qwen3.5_9b.md): copy 2.12, L 1.58, multi 2.17 (MEASURED).
- [Real 3B model, test 3](real_model_test3_qwen2.5-coder_3b.md): multi 2.28, energy estimate.
- [Activation sparsity on 3B](activation_sparsity_qwen2.5-coder_3b.md): cheap predictor far from oracle (MEASURED).
- [Round 4 limits](round4_limits.md): L's own limits vs decode limits (SIMULATED).
- [System simulation](system_simulation.md): L beside a GPU model.
- [Model accuracy](model_accuracy.md): 41% to 74% byte accuracy (MEASURED in software).
- [Energy estimate](energy_estimate.md): energy per token from operation counts (ESTIMATED).
- [Power simulation](power_simulation.md): switching-activity power, 2.4-6.2x less energy per byte (SIMULATED).
- [Synthesis](synthesis.md): Tang Nano 20K place-and-route.
- [Pre-fabrication verification](prefab_verification.md): SKY130 gate-level checks, 0 mismatches.
- [RTL simulation results](sim_results.md) and [with trained weights](sim_results_trained.md).
- [Sensory node](sensory_node.md): two senses (picture + sound) in one chip, sleep cleaning with the chip's own scores and a neighbour unit, bit-exact; a heard word names pictures with no labels (SIMULATED; CNN reference MEASURED).
- [Counting language model, first test](counting_lm.md): online one-pass character model from hashed counters; 4.8 to 1.8 bits per character as memory grows 8 KB to 8 MB (SIMULATED algorithm test).
- [End to end power, encoder included](end_to_end_power.md): picture-to-answer energy and power, chip layout estimate against the measured GPU (about 40 uJ against 0.3 to 69 mJ).
- [Lossless table storage](table_storage_lossless.md): trained tables are 54 to 71% non-zero and use their full widths; ideal lossless coding saves at most 1.7 times (SIMULATED).
- [Counter width against accuracy](bits_vs_accuracy.md): fewer bits cost accuracy, more on clothing than digits; the shipped widths sit near the knee (SIMULATED).
- [Multi-chip counting language model](multichip_lm.md): the 8 MB table split over 1 to 64 chips; traffic, load balance, latency and energy per token (SIMULATED, assumptions stated).
- [Hot-row copies](hot_rows.md): copying 0.02% of the table to every chip removes the load imbalance (2.12 to 1.06 at 64 chips) and cuts remote lookups to 56% (SIMULATED).

Related: [Home](../../README.md), [Project memory](../../docs/PROJECT_MEMORY.md)
