---
title: Big models on a 6 GB GPU - baseline test and bar for candidate 2 (plan written before any run, 1 Nov 2026)
tags: [spark, gpu, small-gpu, offload, plan, solution-candidate]
---

# Candidate 2: running a model that does not fit on a small GPU (plan and bar first)

Founder-accepted candidate (1 Nov 2026, [decision](../../../docs/PROJECT_MEMORY.md)). Pain: the loudest community complaint is models that do not fit in 4 to 8 GB of VRAM ([leads](../../../docs/watch_radar.md); secondhand). Hardware: the founder's RTX 3050 6 GB laptop GPU (122.9 GB/s copy bandwidth, [results](../energy_predict/results_3050/)). Everything here is **MEASURED once run**; nothing has been run.

## Step 1: baseline with the best free tool (no code of ours)

Tool: llama.cpp with a CUDA build (a release binary for Windows), a model in GGUF format. Model: a **13B-class decoder at 4-bit** (about 7.9 GB, does not fit 6 GB; the founder chooses a public checkpoint and records it) and, as a control that fits, a 7B-class at 4-bit (about 4.4 GB).
1. For the 13B-class model, sweep the number of layers placed on the GPU (`-ngl`) from 0 up to the largest that fits; at each setting record tokens per second for generation (batch 1, 128 new tokens, prompt 256) and for prompt processing, and peak GPU memory.
2. **Baseline = the best setting from the sweep with default flags** (also record the CPU model and RAM speed; offloaded speed depends on them).
3. Control: the 7B-class model fully on the GPU, same measurements.

## Step 2: improvement candidates (each gets its own plan and bar before any run)

Examples to try only after the baseline exists: mixed quantisation (more bits on the layers that matter), cache placement choices, prefetching the next layer's weights while the current one computes, smaller context allocation. Nothing is promised.

## Bars (fixed now)

- **Baseline recorded** with the CPU and RAM details, three repeats per setting, spread reported.
- **Improvement bar:** a method of ours must reach **at least 1.3x the baseline's generation speed** on the 13B-class model with **no worse quality** (same model, same or higher bit width; quality checked by the loss increase on a fixed text sample, at most 0.01 nats per token, paired interval), reproduced on at least **two machines** (the founder's laptop and one friend's card).
- **Kill rule:** if the best free tool at its best setting is within 1.3x of anything we try after three distinct ideas, candidate 2 stops.
- **Demand check, separate:** give the result to 5 developers with small cards for a week; the real signal is whether they keep using it and what they say they would pay.

## Limits

One laptop; one model family; the offloaded speed depends strongly on the CPU and memory; llama.cpp changes fast and the baseline will move; not a general claim about all small GPUs.

Related: [Restart 2 study](../../../docs/restart_2_weakness_study.md), [Test G1 result](../energy_predict/RESULT.md), [Test B plan](../graphs_test/PLAN.md), [Project memory](../../../docs/PROJECT_MEMORY.md), [Hardware index](../../HARDWARE_INDEX.md)
