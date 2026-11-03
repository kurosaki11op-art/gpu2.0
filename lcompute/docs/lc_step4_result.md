---
title: L Compute step 4 result - PTX back end; P1 passes (ptxas accepts all PTX); P2 to P4 need a GPU and are not yet run (3 Nov 2026)
tags: [spark, lcompute, result, step4, ptx]
---

# Step 4 result (3 Nov 2026)

Bars (written first): [ROADMAP](ROADMAP.md) step 4. Code: [`ptx.rs`](../src/ptx.rs) (IR to PTX text), [`gpusuite.rs`](../src/gpusuite.rs) (exports PTX plus inputs and the interpreter's outputs for 17 cases), [`gpu_runner.py`](../tools/gpu_runner.py) (runs them on a GPU through the CUDA driver API with ctypes, no compiler needed).

## What is verified and what is not

| Bar | Status |
| --- | --- |
| P1: ptxas accepts every generated file for sm_75 and sm_86, no errors or warnings | **PASS, MEASURED** here with NVIDIA ptxas 12.9 on all 5 kernels (3 kernels + 2 negative kernels), both targets. A negative control (a deliberately wrong instruction type) is rejected by the same command, so the check does reject bad PTX; a cubin of 5088 bytes was produced for matmul_tiled; the matmul PTX contains no fused multiply-add. |
| P2: 16 launches bit-identical on a real GPU | **NOT RUN** (no GPU in this container). Not claimed. |
| P3: out-of-range reported through the error word on a GPU | **NOT RUN**. Barrier divergence cannot be detected on a GPU (a stated limit). |
| P4: our matmul against cuBLAS at 1024^3 | **NOT RUN**, report only. |

P1 proves the text is valid PTX. It does not prove the kernels compute the right numbers; only P2 does.

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

(Colab has no Rust by default: `curl https://sh.rustup.rs -sSf | sh -s -- -y` then `source ~/.cargo/env`.) Paste the output back; the numbers go into this file, whatever they are.

Related: [ROADMAP](ROADMAP.md), [Step 3 result](lc_step3_result.md), [Docs index](INDEX.md), [README](../README.md)
