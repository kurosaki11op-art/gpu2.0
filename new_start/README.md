---
title: New start - charter (30 Oct 2026)
tags: [new-start, charter, plan]
---

# New start: charter

Written 30 Oct 2026 after the founder dropped version 1 ("we were losing and going in a wrong path"). **Clean rules for this project:** no version 1 code is imported (version 1 is kept untouched as an archive and as a lesson, see [lessons](../docs/lessons_L_v1.md)); every claim carries MEASURED / SIMULATED / ESTIMATED / MODEL; the target, its bar and its kill rule are written before any building; the incumbent (the GPU) is measured on the same task before any claim; a failed test is recorded as prominently as a pass and ends or redirects the work.

## Problem (the founder's list of GPU weaknesses)

Power, heat and cooling, memory, cost, heavy training, large stored knowledge, and inefficiency on work that does not fit a GPU's regular wide pattern. Goal: find where a different machine is clearly better, then build only that, and state every GPU workload it does not cover ([census](../docs/gpu_workload_census.md)).

## Target chosen for the clean start: irregular and sparse workloads (census rows 2, 9, 10)

Graph traversal, sparse matrix-vector product, sequence matching. Reason: it is the one target that does not reuse version 1, and the one where a GPU's design (wide lock-step lanes, large memory transactions) is a poor fit (general knowledge; to be tested here, not assumed). **Risk stated up front: no evidence yet; the GPU may already do well; the energy bar may fail.**

## Bars and kill rules (set before any experiment)

| step | test | pass | if it fails |
|---|---|---|---|
| 1 | **How much of a GPU's work and memory traffic is waste on these kernels** (trace-driven model, no hardware needed) | at least 5x more bytes moved than useful, or lane utilisation below 20%, on a skewed graph | the target is dropped: GPUs are not wasteful here |
| 2 | **Same kernels on the founder's RTX 3050** (idle, full-speed GPU, patched measurement script): measured throughput and energy | measured utilisation and energy consistent with step 1 | the model was wrong; fix the model or drop the target |
| 3 | **An event-driven fine-grain tile modelled in simulation** on the same traces | at least 5x better energy per useful operation than the measured GPU, counting memory | the target is dropped |
| 4 | Only now: design and bit-exact RTL of the winning tile, with the coverage matrix of which census rows it passes | passing rows only are claimed | stated as not covered |

## Status

- Step 1 run 30 Oct 2026: **failed the bar on the skewed graph; target 2 dropped as a first target.** See [step 1 result](step1_result.md). Experiments are written in Rust (standard library only) where speed matters.

- Rows B and A of the [workload map](../docs/gpu_workload_map.md), run 31 Oct 2026 (existing models on an SRAM wafer, against a GPU cluster and a Cerebras-class wafer): capacity 2.46x the cited wafer (pass), energy 3.4x at the pessimistic SRAM value against a 5x bar (fail; 5x needs reads at 1.87 pJ/bit or less); see [step 2 result](step2_wafer_sram_result.md).
- Rows I and J of the workload map, run 31 Oct 2026 (cost, yield, power, heat of an SRAM wafer): silicon is under 1% of the cited system price; the wafer wins on cost per token only with a step latency near 1 ms and a system price well under $2-3M, neither shown; see [step 3 result](step3_cost_power_result.md).
- Rows I and J, 31 Oct 2026: the first "closed on the model" was withdrawn after a fair comparison (each machine at its best batch); worst case fails cost and energy, with two named levers; see [step 5 result](step5_worst_case_result.md) and the superseded [step 4](step4_close_i_j_result.md).
- Row K test 2 result, 31 Oct 2026: compute claim holds, data claim fails at small N; see [result](step17_k2_result.md).
- Row K test 2 plan, 31 Oct 2026: see [bars](step17_k2_plan.md).
- Row K test 1 result, 31 Oct 2026: all bars pass on Fashion-MNIST; see [result](step16_k1_result.md).
- Row K test 1 plan, 31 Oct 2026: see [bars](step16_k1_plan.md).
- Row I bottom-up packaged cost, 31 Oct 2026: cost bar passes centrally at $480 per chip; see [note](step15_packaged_cost_result.md).
- Row I price-cut test, 31 Oct 2026: see [note](step14_price_cut_result.md).
- Row I buyer price view, 31 Oct 2026: conditional win at central assumptions; see [note](step13_buyer_price_result.md).
- Rows I and J final disposition, 31 Oct 2026: J closed (pass), I closed as failed; see [note](step12_close_i_j_final.md).
- Memory technology study, 31 Oct 2026 (MODELLED + sourced facts): see [study](step11_memory_technology_study.md).
- Capacity levers, 31 Oct 2026 (MODELLED): do not fix the cost failure; see [result](step10_capacity_levers_result.md).
- Diagnosis and learned router, 31 Oct 2026 (MEASURED): R1 and R2 fail, language cascade claim dropped by the stop rule; see [result](step9_router_result.md) and [bars](step9_router_plan.md).
- Cascade, pair A on the RTX 3050, 31 Oct 2026 (MEASURED): see [result](step8_pairA_gpu_result.md).
- Cascade, pair A stage A on CPU, 31 Oct 2026: margin trigger fails C1 and C3, see [result](step8_pairA_cpu_result.md).
- Cascade test plan for real language models, 31 Oct 2026 (the claim the pitch would lead with): see [step 8 plan](step8_cascade_lm_plan.md); runs on the laptop.
- Target 3 (batch-1 language-model decode) step 1 run 30 Oct 2026: **failed the pre-set bar (3.6x at the pessimistic SRAM energy, 5x needed; passes at the middle value; capacity fits)**; dropped as a first target. See [step 1 result, target 3](step1_lm_result.md). Two of two new targets failed their first step: the premise "a different architecture beats a GPU by a wide margin on general workloads" is not supported by our models.

## Folder

`new_start/experiments/` holds scripts and logs of each step; results get a note in `new_start/` and are linked from here and from the [docs index](../docs/INDEX.md).

Related: [Lessons from L version 1](../docs/lessons_L_v1.md), [GPU workload census](../docs/gpu_workload_census.md), [New start target options](../docs/new_start_target_options.md), [Project memory](../docs/PROJECT_MEMORY.md), [Home](../README.md)
