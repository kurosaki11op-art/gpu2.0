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
- Target 3 (batch-1 language-model decode) step 1 run 30 Oct 2026: **failed the pre-set bar (3.6x at the pessimistic SRAM energy, 5x needed; passes at the middle value; capacity fits)**; dropped as a first target. See [step 1 result, target 3](step1_lm_result.md). Two of two new targets failed their first step: the premise "a different architecture beats a GPU by a wide margin on general workloads" is not supported by our models.

## Folder

`new_start/experiments/` holds scripts and logs of each step; results get a note in `new_start/` and are linked from here and from the [docs index](../docs/INDEX.md).

Related: [Lessons from L version 1](../docs/lessons_L_v1.md), [GPU workload census](../docs/gpu_workload_census.md), [New start target options](../docs/new_start_target_options.md), [Project memory](../docs/PROJECT_MEMORY.md), [Home](../README.md)
