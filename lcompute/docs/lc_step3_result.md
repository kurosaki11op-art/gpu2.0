---
title: L Compute step 3 result - fast CPU back end; first run missed C4 (13x), after the IR optimiser all of C1 to C5 pass, C4 at 21x to 24x (2-3 Nov 2026, MEASURED)
tags: [spark, lcompute, result, step3, backend]
---

# Step 3 result (2 Nov 2026, re-run 3 Nov 2026)

**Status: first run (2 Nov) PASSED C1 to C3 and MISSED C4 (12.9x to 15.0x against 20x). After the optimiser ([`opt.rs`](../src/opt.rs), 3 Nov) the same bars all pass: C4 measured 22.5x, 24.0x, 23.5x, 21.0x in four runs (bar 20x, so the margin is small). The original miss analysis below is kept as written.** The bar was not changed.

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

## Fix: the IR optimiser (3 Nov 2026, MEASURED)

[`opt.rs`](../src/opt.rs) runs inside the fast back end on every launch (the interpreter always runs the kernel as written, so bar C1 compares optimised-fast against unoptimised-reference, bit for bit). Passes: (1) full unrolling of short constant-trip-count loops with straight-line bodies; (2) one forward pass per straight-line region: constant folding, "register + constant" becomes the new instruction `AddImm`, repeated pure computations removed (value numbering); (3) a temporary followed by a Mov is fused; (4) pure instructions whose result is never read are removed. Loads, stores, barriers and integer division are never removed or merged, so errors still surface.

What it changed, step by step (C4, same kernel): optimiser alone 13.5x (no gain: unrolling cut the executed instruction count about 3.8x, COUNTED with callgrind at 128x128x128, but the time did not follow); single-thread timing then showed the cost was in the shared-memory loads, which were done as 8-lane gathers (about one cycle per lane); recognising a group of 8 lanes that read 8 consecutive floats (one vector load) or one float (broadcast) in `ld_dense` brought C4 to 21x to 24x. Lesson recorded: the first guess (instruction count) was wrong; a measurement of where the time went found the real cost. Threads scale linearly (1 / 2 / 4 threads: 0.565 / 0.286 / 0.138 s before the load fix).

Final C4 numbers: interpreter about 2.2 s (0.12 GFLOP/s), fast about 0.10 s (2.5 to 2.8 GFLOP/s). C5 unchanged in kind: vec_add 4.5x, block_reduce 1.5x (barrier-bound; not a bar). The optimiser did not shrink the matmul instruction list (86 to 160, it grew because loops were unrolled), registers 61 to 50 used.

Honest limits: a 20x pass with a 21x worst run is a thin margin on a shared cloud CPU; the speed number will move on other machines. The 'fast' back end is still a CPU interpreter of the IR, about 2.5 GFLOP/s against a single core's native peak of tens of GFLOP/s.

Related: [ROADMAP](ROADMAP.md), [Step 2 result](lc_step2_result.md), [Docs index](INDEX.md), [README](../README.md)
