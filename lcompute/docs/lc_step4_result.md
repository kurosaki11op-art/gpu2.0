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
