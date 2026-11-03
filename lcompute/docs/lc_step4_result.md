---
title: L Compute step 4 result - PTX back end; P1, P2, P3 pass on a real T4 (17 of 17 bit-identical); P4 ours is 0.10x of cuBLAS (3 Nov 2026, MEASURED)
tags: [spark, lcompute, result, step4, ptx]
---

# Step 4 result (3 Nov 2026)

**Status: P1, P2, P3 PASS; P4 reported: our tiled matmul is 0.10x of cuBLAS.** Run on a Colab Tesla T4 (compute capability 7.5), 3 Nov 2026, pre-generated suite from this repository, runner [`gpu_runner.py`](../tools/gpu_runner.py).

Bars (written first): [ROADMAP](ROADMAP.md) step 4. Code: [`ptx.rs`](../src/ptx.rs) (IR to PTX text), [`gpusuite.rs`](../src/gpusuite.rs) (exports PTX plus inputs and the interpreter's outputs for 17 cases), [`gpu_runner.py`](../tools/gpu_runner.py) (runs them on a GPU through the CUDA driver API with ctypes, no compiler needed).

## What is verified and what is not

| Bar | Status |
| --- | --- |
| P1: ptxas accepts every generated file for sm_75 and sm_86, no errors or warnings | **PASS, MEASURED** here with NVIDIA ptxas 12.9 on all 5 kernels (3 kernels + 2 negative kernels), both targets. A negative control (a deliberately wrong instruction type) is rejected by the same command, so the check does reject bad PTX; a cubin of 5088 bytes was produced for matmul_tiled; the matmul PTX contains no fused multiply-add. |
| P2: 16 launches bit-identical on a real GPU | **PASS, MEASURED on a Tesla T4:** all 16 launches (vec_add x5, matmul x6, block_reduce x5) bit-identical to the interpreter. |
| P3: out-of-range reported through the error word on a GPU | **PASS, MEASURED on the T4:** error word 2 (instruction 1), the access skipped, buffers unchanged as in the interpreter (17 of 17 cases pass). Barrier divergence cannot be detected on a GPU (a stated limit, not a pass). |
| P4: our matmul against cuBLAS at 1024^3 (report only) | **MEASURED on the T4:** ours 8.60 ms = 250 GFLOP/s; cuBLAS (PyTorch, TF32 off) 0.84 ms = 2568 GFLOP/s; **ours / cuBLAS = 0.10**; max difference from cuBLAS 4.5e-07 of the largest value (different summation order, as expected). |

P1 proves the text is valid PTX; P2 and P3 on the T4 show the generated kernels compute the same bits as the interpreter and report the bad access.

**What P4 says:** a first, plain 16 x 16 tiled kernel with one output per thread, plus a bounds check on every access, runs at one tenth of the vendor library. Step 6 carries a bar of 0.5x vendor, so this is a gap of five times still to close; the likely levers are larger tiles with several outputs per thread, vector loads and fewer checks (not yet measured, so not claimed). The timing includes a synchronise after each launch (a small part of 8.6 ms). One GPU, one run; not repeated.

## Step 4b: register-blocked matmul on the T4 (3 Nov 2026, MEASURED)

Bars Q1 to Q4: [ROADMAP](ROADMAP.md). Kernel `matmul_reg` (64 x 64 block tile, 4 x 4 outputs per thread, same summation order; 64 registers, no spills by ptxas).

| Bar | Result |
| --- | --- |
| Q1 bit-identical to `matmul_tiled` on CPU (interpreter and fast back end), 8 shapes | PASS |
| Q2 GPU bit-identical to the interpreter | PASS: 25 of 25 cases on the Tesla T4, and `matmul_reg` equals `matmul_tiled` bit for bit at 1024^3 on the GPU |
| Q3 at least 0.25x of cuBLAS at 1024^3 | **PASS: matmul_reg 2.10 ms = 1024 GFLOP/s; cuBLAS 0.74 ms = 2911 GFLOP/s; ratio 0.35** (matmul_tiled in the same run: 329 GFLOP/s, 0.11; an earlier run had cuBLAS at 2568, so cuBLAS timing varies between runs by about 10 percent) |
| Q4 at least 0.5x with a fused multiply-add instruction | **MISS: matmul_fma 2.00 ms = 1076 GFLOP/s; cuBLAS 0.83 ms = 2586 GFLOP/s; ratio 0.42** (same run: matmul_tiled 327 GFLOP/s = 0.13, matmul_reg 1044 GFLOP/s = 0.40). 30 of 30 cases bit-identical to the interpreter, including the fused kernel. |

One T4, best of three timing loops of 20 launches each, one session.

**Reading of the Q4 miss:** the fused instruction gave only 3 percent (1044 to 1076 GFLOP/s), so the kernel is not limited by floating-point instruction count. Reasoning from the design (not measured yet): each thread does 8 shared-memory loads per 16 multiply-adds, which at the T4's shared-memory rate costs about as much issue time as the arithmetic, and the global-to-shared tile loads recompute index arithmetic (divisions) every tile. Next attempt (bar Q5 in the ROADMAP, written before the work): hoist the loop-invariant index arithmetic, and an 8 x 8 outputs-per-thread version (64 multiply-adds per 16 loads).

## Step 4c: second attempt at 0.5x (bar Q5, 3 Nov 2026)

CPU part (MEASURED here, before the GPU run): the three fused kernels (`matmul_fma`, `matmul_fma4`, `matmul_fma8`) equal the interpreter bit for bit on the fast back end on all 15 runs. **The accuracy bar as first written (1e-5 relative error against float64) failed on 2 of 15 runs** (`matmul_fma4` and `matmul_fma8` at 1 x 768 x 2304, both 1.0e-5): the same mis-specification as step 1 (a sequential fp32 sum over 768 terms rounds to about 1e-5). Re-specified, as in step 1b, with the rounding-bound rule (error within k x 6e-8 x the sum of absolute terms): all 15 pass, the worst at 0.143 of the bound. This is a re-specification, not a pass of the first bar, and I should have applied the step 1b rule when writing Q5. ptxas: `matmul_fma4` 70 registers, `matmul_fma8` 163 registers (one block of 256 threads per multiprocessor on the T4), no spills. 

**GPU result (Colab Tesla T4, 3 Nov 2026, MEASURED, suite 4): 40 of 40 cases bit-identical to the interpreter. Q5 speed bar (at least 0.5x of cuBLAS): MISSED by about 1 percent.** Same run, 1024^3 fp32, cuBLAS (TF32 off) 0.83 ms = 2588 GFLOP/s:

| kernel | ms | GFLOP/s | ours / cuBLAS |
| --- | --- | --- | --- |
| matmul_tiled | 6.56 | 327 | 0.13 |
| matmul_reg | 2.04 | 1053 | 0.41 |
| matmul_fma | 2.00 | 1074 | 0.42 |
| matmul_fma4 | 1.98 | 1082 | 0.42 |
| **matmul_fma8** | **1.68** | **1281** | **0.495** |

`matmul_fma8` is 0.495 of cuBLAS (the tool printed 0.50 after rounding; the bar was written as 'at least 0.5x', so this is not counted as met). What the numbers say: hoisting the index arithmetic (`matmul_fma` to `matmul_fma4`) gave nothing (1074 to 1082), so tile-load index arithmetic was not the limit; going to 8 x 8 outputs per thread gave +18 percent (1082 to 1281). The remaining gap (about 2x to the vendor library) is not yet explained by measurement. Untried levers: overlapping the next tile's loads with the current tile's arithmetic (double buffering), vector shared-memory loads, a deeper k tile, and the low occupancy of the 163-register kernel (one block of 256 threads per multiprocessor). One T4, one session; cuBLAS varied 2568 to 2911 GFLOP/s across the three sessions, so ratios carry about 10 percent uncertainty.

## Step 4c, bar Q6: four more matmul variants (3 Nov 2026)

Bar Q6 ([ROADMAP](ROADMAP.md), written before the work): best new kernel at least 0.6x of cuBLAS on the T4. Kernels from one generator (`matmul_v3`): `matmul_fma8db` (double-buffered shared tiles), `matmul_fma8x4` (8 x 4 outputs per thread, 128 x 64 tile), `matmul_fma8x4db` (both), `matmul_fma8k32` (k tile 32). **Q6a (CPU, MEASURED):** 24 of 24 runs (4 kernels x 6 shapes) bit-identical to `matmul_fma8` and to their own interpreter run. ptxas (no spills for any): fma8db 178 registers and 32 KB shared memory, fma8x4 116 registers and 12 KB, fma8x4db 128 registers and 24 KB, fma8k32 241 registers and 32 KB. **Q6b and Q6c (T4): not yet run**, suite 5 sent.

## Step 4c result for bar Q6 (3 Nov 2026, Colab Tesla T4, MEASURED, suite 5)

64 of 64 cases bit-identical to the interpreter (Q6b passes). cuBLAS (TF32 off) 0.83 ms = 2590 GFLOP/s at 1024^3. **Q6c (at least 0.6x) MISSED: best 0.515x.**

| kernel | GFLOP/s | ours / cuBLAS |
| --- | --- | --- |
| matmul_fma8 (previous best) | 1283 | 0.50 |
| matmul_fma8db (double buffering) | 1315 | 0.51 |
| matmul_fma8x4 (8 x 4 tile) | 1279 | 0.49 |
| **matmul_fma8x4db** | **1334** | **0.52** |
| matmul_fma8k32 (k tile 32) | 1271 | 0.49 |

Double buffering gained 2 to 4 percent, a smaller tile for occupancy nothing, a deeper k tile nothing. All four levers I had guessed at were small, so the limit is elsewhere. Note that this run measured `matmul_fma8` at 0.495x (1283 / 2590) again: the Q5 bar (0.5x) stays recorded as missed.

**Where the time goes (COUNTED, machine code):** disassembling the ptxas output of `matmul_fma8x4db` (sm_75) shows, per inner k step, 32 multiply-adds and 12 shared loads against about 85 other instructions (integer multiplies and compares, predicated error stores, selects): the bounds checks. The multiply-adds are about 27 percent of the issued instructions, and the k loop is not unrolled. So the limit is probably the checking code, not memory or arithmetic. That is a hypothesis; bar Q7 ([ROADMAP](ROADMAP.md)) tests it with check modes full / cheap / none and loop unrolling.

## Bar Q7: what the bounds checks cost (3 Nov 2026, Colab Tesla T4, MEASURED, suite 6)

**Q7a: 113 of 113 cases bit-identical to the interpreter** (every check-mode and unrolling variant, on 3 shapes each), and the out-of-range **load and store** tests are reported in both the full and the cheap check mode (error words 2 and 3, access skipped).

1024^3 fp32, one session, cuBLAS (TF32 off) 0.83 ms = 2590 GFLOP/s. Best of three loops of 20 launches (a synchronise after each launch):

| kernel variant | full checks | cheap checks | no checks | cheap, unrolled k loop | no checks, unrolled |
| --- | --- | --- | --- | --- | --- |
| matmul_fma8db (128 x 128 tile) | 1315 (0.51x) | 2784 (1.07x) | 2874 (1.11x) | 2631 (1.02x) | 3828 (1.48x) |
| matmul_fma8x4 (128 x 64 tile) | 1288 (0.50x) | 1913 (0.74x) | 2095 (0.81x) | 1802 (0.70x) | 3514 (1.36x) |
| matmul_fma8x4db | 1237 (0.48x; 1334 = 0.52x in the previous session) | 1896 (0.73x) | 2176 (0.84x) | 1816 (0.70x) | 3510 (1.36x) |

Full checks with the k loop unrolled: fma8db 1632 (0.63x), fma8x4 1247 (0.48x), fma8x4db 1184 (0.46x). Earlier kernels in the same run: matmul_tiled 325, matmul_reg 1052, matmul_fma 1054, matmul_fma4 1077, matmul_fma8 1270, matmul_fma8k32 1216 GFLOP/s.

**Q7b as first judged (single non-interleaved run): looked like a pass; RETRACTED after the controlled repeat below (0.58x at 1024^3, a miss).** In that first run every cheap-check variant was at 0.70x or more; the best, `matmul_fma8db` with cheap checks, is 2784 GFLOP/s (1.07x in this run). The hypothesis is confirmed: the full bounds checks (about 85 extra instructions per 32 multiply-adds) were what held the kernel at 0.5x. Cheap checking (one unsigned compare per access, the error code kept in a register and written once at the end, loads on a clamped index, stores predicated, 32-bit shared addressing) costs about 3 to 7 percent against no checks for the 128 x 128 kernel and about 12 percent for the 128 x 64 kernel (fma8x4 cheap 1913 against none 2095), and is 2.1x faster than full checking.

**Not to be believed yet: results above 1.0x of cuBLAS (up to 1.48x).** A hand-written kernel from our own IR beating the vendor library by that much is extraordinary and may be an artefact of the measurement: the cuBLAS number (2590 GFLOP/s, 0.83 ms) is low for this GPU class, which suggests clock or power throttling that differed between the cuBLAS loop (run first) and our loops; the two were not interleaved; sizes other than 1024^3 were not tried; and cuBLAS may simply pick a poor kernel for this one shape. The outputs agree with cuBLAS to 1.6e-6 (the results are right). A controlled re-measurement (interleaved runs, clocks logged, CUDA event timing, several sizes) is the next step; until it is done the honest statement is: **with cheap checks the kernel is at 0.70x to 1.07x of cuBLAS in this one run, and the comparison needs a controlled repeat.** Run-to-run variation seen so far: the same kernel measured 0.52x and 0.48x in two sessions.

### Controlled repeat (3 Nov 2026, same T4, MEASURED, [gpu_verify.py](../tools/gpu_verify.py)): the above-1.0x results were an artefact

cuBLAS and six of our variants interleaved over 5 rounds, 20 launches per timing, CUDA event timing, clocks logged. The GPU starts idle (585 MHz, 27 W) and ramps to about 1500 MHz: the first cuBLAS call of the first run (0.83 ms at 1024^3) was a cold-clock timing; steady cuBLAS at 1024^3 is 0.35 ms (6170 GFLOP/s, rounds: 0.830 0.523 0.445 0.348 0.350). Medians of 5 rounds (ours / cuBLAS in brackets):

| size | cuBLAS GFLOP/s | fma8db full | fma8db cheap | fma8db cheap, unrolled | fma8db no checks, unrolled | fma8x4 cheap | fma8x4db cheap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 512 | 2015 | 341 (0.17) | 533 (0.26) | 579 (0.29) | 905 (0.45) | 767 (0.38) | 691 (0.34) |
| 1024 | 4821 | 1047 (0.22) | 2785 (0.58) | 2659 (0.55) | 4463 (0.93) | 2112 (0.44) | 2070 (0.43) |
| 2048 | 5182 | 1422 (0.27) | 2772 (0.53) | 2676 (0.52) | 4390 (0.85) | 2090 (0.40) | 1958 (0.38) |
| 4096 | 4102 | 1476 (0.36) | 2609 (0.64) | 2574 (0.63) | 3896 (0.95) | 1902 (0.46) | 1776 (0.43) |

(Clock range during the runs 585 to 1575 MHz, power 27 to 118 W; the early rounds include the clock ramp, which is why 512 and 1024 are noisy. At 1024^3 using the best round of each instead of the median, cuBLAS 6170 GFLOP/s against fma8db cheap 2970 (0.48x) and no-check unrolled 4740 (0.77x).)

**Corrected conclusions.**
- **No kernel beats cuBLAS.** The 1.07x to 1.48x of the first run came from a cold-clock cuBLAS timing and are withdrawn.
- **Bar Q7b is MISSED under the controlled measurement:** the best cheap-check variant is 0.58x at 1024^3 (the size the bar names), 0.53x at 2048^3, 0.64x at 4096^3 (the only size at or above 0.6x), 0.26x at 512^3. The first judgement of Q7b as passed was based on the throttled comparison and is retracted.
- What stands: full bounds checking is the main cost (full 1047 against cheap 2785 GFLOP/s at 1024^3, 2.7x), and the best no-check kernel reaches 0.85x to 0.95x of cuBLAS at 1024^3 and above, which is a strong result for a kernel generated from our own IR (a plain 128 x 128 tile, scalar shared loads, no vector instructions).
- The check cost is 30 to 40 percent once the loop is unrolled: cheap checks cost 3 percent against no checks without unrolling (suite 6: 2784 against 2874), but unrolling helps the no-check kernel by 33 percent (2874 to 3828) and the cheap-check kernel not at all (2784 to 2631): the compiler cannot optimise the unrolled loop around the per-load compare and clamp.
- Small sizes are poor: at 512^3 the 128 x 128 tile gives only 16 blocks for the 40 multiprocessors of the T4.

Next lever (not started): remove checks that can be proved safe at code generation time (the index ranges inside the unrolled loops come from thread ids and constants), keeping the check only where it cannot be proved. That is a range analysis; it needs the thread-block shape declared in the kernel.

Semantics note on the cheap mode: loads past the end read a clamped (wrong but defined) element and set the error word, stores past the end are skipped, and the error code of the last failing access is written when the thread exits; unlike the full mode, a failing kernel keeps running to its end. The error word is zero if and only if no access was out of range.

## Step 4d: range analysis removes the provably unnecessary checks (bar Q8, 3 Nov 2026)

Bar Q8 ([ROADMAP](ROADMAP.md), written before the work). Code: [`range.rs`](../src/range.rs) (interval analysis over the IR), launch bounds in the kernel (`B::launch_bounds`, enforced by the interpreter, the fast back end and the runtime; `.reqntid` in the PTX), `ptx.rs` (`to_ptx_opts(.., prove, ..)`), tests [`step4d.rs`](../src/step4d.rs).

**Q8a coverage (CPU, MEASURED): PASS.** Shared-memory accesses proved safe: `matmul_fma8db` 48 of 48 as written and 288 of 288 after unrolling; `matmul_fma8x4` 24 of 24 and 204 of 204; `matmul_fma8x4db` 36 of 36 and 216 of 216 (bar: at least 95 percent). Global-memory accesses are never proved (their sizes are run-time values) and keep their checks.

**Q8b soundness (CPU, MEASURED): PASS.** A fuzz test of 20,000 random kernels (index expressions over thread ids, constants, add, subtract, multiply, divide, remainder, shifts, masks, min, max; straight line, one loop, and two nested loops; 8 block shapes, 8 array sizes, some kernels without declared bounds): the analysis proved 11,334 safe, the reference interpreter reported 6,384 genuinely out of range, and **there was not one case that was proved safe and out of range**. The negative kernel (index = thread id + 1 on an array exactly as long as the block) is not proved and is reported; launching a kernel that declares 16 x 16 with an 8 x 8 block is rejected by the interpreter, the fast back end and the runtime.

**How the analysis got there (misses on the way, recorded):** the first version proved only 12 of 24 (`matmul_fma8x4`) and 16 of 48 (`matmul_fma8db`) accesses, below the bar. Three precision bugs, each found by looking at the actual intervals, none a soundness bug (the fuzz stayed clean throughout): (1) widening was applied at every instruction instead of only at loop heads, so the inner loop counter was widened past its loop bound; (2) after widening, the loop counter incremented past the top of the 32-bit range and became unknown; (3) an outer loop counter creeping through the head of an inner loop was widened there, and an ascending fixpoint with narrowing cannot undo a bound that feeds itself around a loop. Fixes: widen only at labels that a later branch jumps back to, and only the registers that the loop writes, plus a narrowing pass (recompute every state from its predecessors, intersect, six rounds).

**What the machine code looks like (COUNTED, ptxas sm_75):** share of multiply-adds among all instructions of `matmul_fma8db` variants: cheap checks 4 percent, proved shared checks 4 percent (not unrolled: the loop body repeats once), cheap checks with unrolled loop and proved shared checks 37 percent, no checks and unrolled 45 percent, full global checks and proved shared checks unrolled 32 percent. All 46 generated PTX files assemble without errors.

**Q8c and Q8d (T4): not yet run**, suite 7 sent.

## Design notes

- ABI: a buffer is two parameters (device pointer, length in floats), a scalar one parameter, and a last pointer to a u32 error word. Every global and shared access is bounds checked in the generated code; a failing access is skipped and the instruction number + 1 is written to the error word. Integer division by zero is reported and made harmless.
- Floats use explicit `.rn` rounding so ptxas cannot fuse multiply and add, which keeps results equal to the interpreter. `exp` and `tanh` use PTX approximations (not bit-identical; no suite kernel uses them).
- The translator reads the kernel as the builder wrote it (not the optimised IR); ptxas does its own optimisation.
- Cost of the checks (extra compare and predicated access per memory operation) is not yet measured; P4 will show it.

## How to run P2 to P4 (Colab T4 or your RTX 3050)

On a machine with an NVIDIA GPU, Rust and Python with numpy (PyTorch optional for the cuBLAS comparison):

```
git clone <this repository> && cd gpu2.0 && git checkout claude/sharp-davinci-wrwazg
cd lcompute/src && rustc --edition 2021 -O main.rs -o /tmp/lcompute && /tmp/lcompute --emit-gpu /tmp/suite
python3 ../tools/gpu_runner.py /tmp/suite
```

(Colab has no Rust by default: `curl https://sh.rustup.rs -sSf | sh -s -- -y` then `source ~/.cargo/env`.) (Colab can also run the pre-generated suite zip without Rust: upload it, `!unzip` it, `!python3 gpusuite/gpu_runner.py gpusuite`. That is how the T4 run was done.)

Related: [ROADMAP](ROADMAP.md), [Step 3 result](lc_step3_result.md), [Docs index](INDEX.md), [README](../README.md)
