---
title: Results index
tags: [spark, index, results]
---

# Results index

Labels: MEASURED, SIMULATED, ESTIMATED, PROJECTED. JSON files beside each note hold the raw numbers.

## SPARK Cortex (Phase C, now)

- [Month 2 results](cortex_month2.md): memory 137x smaller, one rule, integer chip model + RTL bit-exact (SIMULATED).
- [Month 2 running log](cortex_month2_log.md): every memory-shrink test, including failures (SIMULATED).
- [Month 1](cortex_month1.md): accuracy gap closed on digits, clothing, spoken words (SIMULATED).
- [First proof](cortex_proof.md): no forgetting, exact merge, few-shot loses (SIMULATED).

## Matrix-free lookup core and real-model drafting (Phase B)

- [Token-level lookup on a real model](token_lookup_real.md): tables tie prompt lookup; chat model 1.04 on prose (MEASURED).
- [Matrix-free predictor](matrix_free.md): lookup tables match the network on bytes, hash corrections (SIMULATED).
- [Size study](size_study.md): shrinking the network before fabrication (SIMULATED).

## SPARK v1/v2 beside a GPU (Phase A)

- [Real 9B model, first test](real_model_test_qwen3.5_9b.md): draft 1.51 tokens/pass, answer mode ~6% (MEASURED).
- [Real 9B model, test 3](real_model_test3_qwen3.5_9b.md): copy 2.12, SPARK 1.58, multi 2.17 (MEASURED).
- [Real 3B model, test 3](real_model_test3_qwen2.5-coder_3b.md): multi 2.28, energy estimate.
- [Activation sparsity on 3B](activation_sparsity_qwen2.5-coder_3b.md): cheap predictor far from oracle (MEASURED).
- [Round 4 limits](round4_limits.md): SPARK's own limits vs decode limits (SIMULATED).
- [System simulation](system_simulation.md): SPARK beside a GPU model.
- [Model accuracy](model_accuracy.md): 41% to 74% byte accuracy (MEASURED in software).
- [Energy estimate](energy_estimate.md): energy per token from operation counts (ESTIMATED).
- [Power simulation](power_simulation.md): switching-activity power, 2.4-6.2x less energy per byte (SIMULATED).
- [Synthesis](synthesis.md): Tang Nano 20K place-and-route.
- [Pre-fabrication verification](prefab_verification.md): SKY130 gate-level checks, 0 mismatches.
- [RTL simulation results](sim_results.md) and [with trained weights](sim_results_trained.md).

Related: [Home](../../README.md), [Project memory](../../docs/PROJECT_MEMORY.md)
