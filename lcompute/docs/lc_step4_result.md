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
