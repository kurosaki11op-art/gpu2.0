---
title: New start step 1 - how much does a GPU waste on irregular kernels (result, 30 Oct 2026)
tags: [new-start, step1, model, negative-result]
---

# Step 1 result: GPU waste on graph and sparse kernels

Charter step 1 ([charter](README.md)): at least 5x more bytes moved than useful, or lane utilisation below 20%, on a skewed graph, else the target (irregular and sparse workloads) is dropped. **MODEL, trace-driven, not a measurement of any GPU.** Program [step1_gpu_waste_model.rs](experiments/step1_gpu_waste_model.rs) (Rust, standard library only, rustc 1.97; the whole sweep runs in about 52 s; the first Python draft needed minutes), log [step1_gpu_waste_model.log](experiments/step1_gpu_waste_model.log).

Model: 32-lane warps; 32-byte memory sectors; a 16-way LRU sector cache (L2) of 2 MB (and 64 MB for comparison); 4-byte elements; kernels BFS (level-synchronous) and SpMV (CSR) on generated graphs, skewed R-MAT and uniform random, up to 33.5 million directed edges (footprints 144 MB and 279 MB). "Waste" = DRAM bytes moved by the cache model divided by the ideal bytes (each distinct 4-byte word touched, moved once). The figure in square brackets processes the vertices in random order, the worst case for cache locality (a real GPU interleaves thousands of threads; in-order is generous to the GPU).

| graph (2^20 vertices) | lane utilisation: naive thread-per-vertex / warp-per-vertex | BFS waste, 2 MB L2 [shuffled] / 64 MB | SpMV waste, 2 MB L2 [shuffled] / 64 MB |
|---|---|---|---|
| skewed | 12.3% / 67.8% | 2.88x [2.91x] / 1.02x | 1.93x [2.34x] / 1.01x |
| uniform | 72.3% / 68.8% | 5.60x [5.70x] / 1.09x | 3.37x [3.91x] / 1.00x |

(smaller graphs, 2^16 and 2^18 vertices: waste between 1.0x and 1.7x everywhere.)

## Reading against the pre-set bar

1. **Lane utilisation: the 12.3% pass belongs to the naive mapping only.** With one warp per vertex, which good GPU libraries use, utilisation on the same skewed graph is about 67%, far above the 20% bar. Divergence is not a deep GPU weakness here.
2. **Memory waste on the skewed graph is 1.9x to 2.9x at 2 MB, at most 2.9x in the worst-case ordering, below the 5x bar.** With a 64 MB cache the waste disappears (about 1.0x), so a GPU with a large last-level cache already moves close to the minimum on these kernels.
3. **Only the uniform graph reaches 5x** (BFS, 5.6x, 5.7x shuffled) and only with the small 2 MB cache; the bar names the skewed graph.
4. **Even the ideal here is generous to a new machine**: it assumes all 144 to 279 MB of data sits in on-chip memory, which is costly SRAM, so the real attainable gain is below the waste factors shown.

**Verdict by the rule set before the test: step 1 FAILS for the skewed graph. Target 2 (irregular and sparse workloads) is dropped as a first target.** Caveats stated, not used to overturn the rule: the model ignores DRAM row-buffer and atomics effects and uses one cache geometry; a real measurement on the founder's RTX 3050 (charter step 2) could differ, but the model gives no reason to expect a 5x memory waste.

## What it means for the new start

The three weaknesses tested so far all point the same way: on every kernel and task where we tested it, a GPU's inefficiency is a modest factor, not a large one, except where data fits on the chip and the work is sparse and small (version 1's recognition niche, ESTIMATED). That is a finding, not a failure of the method: it says where not to build. Remaining candidates from the [target options](../docs/new_start_target_options.md): target 3 (batch-1 language inference, memory-bound; to be tested the same way, cheaply, in Rust before anything else) or a refined target 1 after the measurements.

Related: [New start charter](README.md), [Target options](../docs/new_start_target_options.md), [GPU workload census](../docs/gpu_workload_census.md), [Docs index](../docs/INDEX.md)
