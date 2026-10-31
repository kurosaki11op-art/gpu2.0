---
title: Rows I and J, final disposition - J closed (passes), I closed as failed with a stated way to reopen it (31 Oct 2026, MODEL plus one MEASURED calibration)
tags: [spark, new-start, cost, power, heat, closure, failure, final]
---

# Rows I and J: final disposition (31 Oct 2026)

> **Correction banner, 31 Oct 2026 ([Vision review 01](../docs/reviews/vision_review_01.md), [corrections](step21_vision_corrections.md)):** row J ("closed, passes") does not stand: the worst-corner energy advantage is 3.5x after the corrections, below the 5x bar (V-03, V-04), and "floor confirmed by one measurement" over-reads a laptop GPU in an unoptimised Python loop (V-15). Row I stays failed.

> **Update, same day:** the founder reopened row I (no row K before winning on I). The like-for-like cost failure below stands; the [buyer's price view](step13_buyer_price_result.md) makes row I a conditional win (3.2x at central assumptions at a 2x markup, 1.26x in the worst corner, bar missed).

Founder's instruction: fix the I and J failures and close them. This note fixes what can be fixed, tests the last remaining route for cost, and closes each row with an honest status. Models: [`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs) with the new `SLA` switch, [log](experiments/step12_equal_speed.log). Bars written in the source before the run.

## Row J (power, heat, energy): CLOSED, passes

- **Energy bar (at least 5x below the GPU cluster, worst corner):** passes after the bank-level model ([step 6](step6_sram_energy_result.md)): 6.2x at 0.55 pJ/bit for the reticle-chip option, 5.1x at 1.0 pJ/bit, 8.0x at 0.077.
- **Heat:** average 0.16 W/mm2 while serving at the central corner ([step 4](step4_close_i_j_result.md)), against 0.62 for the assumed GPU boards.
- **New measured calibration (RTX 3050 laptop, 1.5B model in half precision, batch 1, [pair A](step8_pairA_gpu_result.md)):** 1.375 J per token gross at 31.4 tokens/s = **43 W while decoding**, 13 W idle. The model's energy for the same operation (HBM energy over the 3.09 GB read, plus the measured idle power for the token time) is about 0.56 J per token: **the measurement is about 2.4x higher** (1.4x higher even against the pure bandwidth time of 18 ms). So the GPU energy in my model is a floor, not an optimistic figure; the real GPU is less efficient than modelled, which widens the energy advantage. Caveat: one laptop GPU, an unoptimised Python loop, no H100 measurement.
- **Not covered (stays a limit, not a failure):** clock distribution, test circuits, power-delivery losses, water (no figure claimed), hot spots. A wafer or a rack still needs a cooling design; the energy advantage reduces what that design has to remove.

## Row I (cost): CLOSED AS FAILED

**Last route tested: cost at equal per-user speed.** A new claim with its own bar (written before the run, the old 30 tokens/s bar stays failed): at 100 and 200 tokens per second per user, worst corner, GPU at manufacturing cost, reticle chips at $1,330, cost advantage at least 2x and energy advantage at least 5x.

| per-user speed floor | GPUs needed | GPU cost per million tokens | ours, central / worst |
|---|---|---|---|
| 30 | 14 | $0.028 | $0.027 / $0.041 |
| 100 | 29 | $0.028 | same |
| 200 | 58 | $0.028 | same |
| 400 | 115 | $0.028 | $0.027 / $0.048 |

**Result: FAIL.** In the model a GPU cluster meets any per-user speed by adding GPUs, at the same cost per token, so a speed floor gives no cost advantage (central 1.02x, worst 0.52x to 0.61x). This model **ignores the communication time between GPUs, which favours the GPU**; in practice that time caps the speed a GPU cluster can reach. If so, the SRAM system's advantage is a **capability** (speeds a GPU cluster cannot reach) and not a cost advantage, and its value is a price premium for speed that needs a customer, not a model.

**Disposition of row I:** the cost claim is closed as **failed**: on a like-for-like basis (GPU at manufacturing cost) the SRAM system has no cost advantage at any speed floor, at any batch, with equal capacity levers ([step 10](step10_capacity_levers_result.md)), and the failure is structural (SRAM silicon about $175 per GB against about $17 per GB for HBM). **How it could be reopened:** a fast memory with at least about 4.2x the bits per area of SRAM at the same chip price, read energy 1.0 pJ/bit or lower, bandwidth at least 0.3x SRAM, standby at most 1.6 W/GB ([memory study](step11_memory_technology_study.md)); the missing evidence is foundry eMRAM macro data. **What survives:** energy per token 5x to 13x lower and per-user speed 7x to 20x higher than a well-batched GPU cluster (MODELLED), at cost parity at best, with no verified buyer for the speed.

## Summary of rows B, A, I, J after this note

| row | status |
|---|---|
| B capacity | partly covered: more fast memory per wafer area (modelled) but not cheaper per GB |
| A energy/dense inference | modelled advantage in energy and speed; accuracy inherited, never tested on a real model on our hardware |
| **I cost** | **closed as failed** (structural), reopen condition stated |
| **J power and heat** | **closed, passes on the model**, GPU energy floor confirmed by one measurement |

**Correction after Vision review 01 (31 Oct 2026), V-15):** the 1.375 J per token is real (43 W, 31.4 tokens/s) but it is one GDDR laptop GPU in an unoptimised Python loop at batch 1; it says nothing about an HBM data-centre GPU at batch 1,024, and 'GPU energy floor confirmed' is withdrawn. Measure an optimised engine, then a data-centre GPU.

Related: [Step 11 memory technology study](step11_memory_technology_study.md), [Step 10 capacity levers](step10_capacity_levers_result.md), [Step 7 cost result](step7_cost_basis_result.md), [Step 6 SRAM energy](step6_sram_energy_result.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
