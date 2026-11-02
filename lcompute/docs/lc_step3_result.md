---
title: L Compute step 3 result - fast CPU back end; C1, C2, C3 pass, C4 speed bar MISSED at 13x to 15x against 20x (2 Nov 2026, MEASURED)
tags: [spark, lcompute, result, step3, backend]
---

# Step 3 result (2 Nov 2026)

**MEASURED** on the cloud container (4 cores, AVX2). Bars (written first): [ROADMAP](ROADMAP.md) step 3. Code: [`fast.rs`](../src/fast.rs), tests [`step3.rs`](../src/step3.rs), full log [`step3_run.txt`](../logs/step3_run.txt). Build: `rustc --edition 2021 -O -C target-cpu=native main.rs` (the native flag matters: without it the loops are not vectorised).

## What was built

A lockstep block executor. The threads of a block run together; each IR instruction is applied to all active threads as a loop over a register row. Divergent branches split the lanes; the lanes at the lowest instruction run first so they re-join; barriers are waiting points and divergence at a barrier is an error. Blocks run in parallel over CPU threads. The runtime now takes a back end (`Backend::Interp` or `Backend::Fast`).

## Results

| Bar | Result | Verdict |
| --- | --- | --- |
| C1 bit-identical outputs on all 16 step 1 launches | 16 of 16 identical | PASS |
| C2 both negative tests detected, same kind of message | both detected | PASS |
| C3 step 2 suite R1 to R5 on the fast back end | all pass | PASS |
| C4 512x512x512 tiled matmul at least 20x faster than the interpreter | **12.9x** in the logged run (earlier runs of the same code 13.2x and 15.0x; interpreter 2.2 s = 0.12 GFLOP/s, fast 0.17 s = 1.6 GFLOP/s), outputs identical | **MISS** |
| C5 (report only) 1e6 elements | vec_add 4.7x (0.0076 s); block_reduce 1.3x (0.114 s) | reported |

## The miss, and what the optimisation steps showed

The bar was not moved. History of C4 for the same kernel: first correct version 1.5x; lazy per-lane program counters 2.2x; unchecked register and shared access 2.9x then 3.2x; native vector instructions alone changed nothing (3.3x) because the loops were not written in a vectorisable form; vectorised arithmetic/compare helper 7.0x; dense Mov and dense branch test 15.0x; dense shared-load check 13.2x (no gain, within noise). Honest reading: each multiply-add costs about 17 IR instructions in this kernel (index arithmetic is recomputed inside the inner loop), so the executor does 17 lane operations per multiply-add. The remaining gap needs fewer instructions (an IR optimiser: constant folding, hoisting loop-invariant index arithmetic) or fusing instruction sequences, not a faster loop. That is a separate piece of work and is not claimed here.

Other honest notes: the interpreter is itself parallel over blocks, so the 20x bar compared against a fairly quick baseline; block_reduce gains little because it is dominated by barriers and partial-lane steps, which run on the slower per-lane path.

Related: [ROADMAP](ROADMAP.md), [Step 2 result](lc_step2_result.md), [Docs index](INDEX.md), [README](../README.md)
