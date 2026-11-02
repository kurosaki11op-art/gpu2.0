---
title: Stack milestone K0 - a CUDA-style programming model and runtime running on the CPU, first kernels correct (2 Nov 2026, MEASURED)
tags: [spark, software, stack, result, k0, runtime]
---

# Stack K0 result (2 Nov 2026)

**MEASURED** on the cloud container's CPU (4 worker threads). Plan: [stack plan](stack_plan.md). Code: [`minicuda.rs`](minicuda.rs) (Rust, standard library only, about 60 lines of runtime).

## What it is

The first two layers of a CUDA-like stack, on the CPU:
- **Programming model:** a kernel is a function run once per thread; each thread knows its block index, thread index, block size and grid size (`blockIdx`, `threadIdx`, `blockDim`, `gridDim` as in CUDA); kernels are launched over a grid of blocks.
- **Runtime:** device buffers, copy to device, copy to host, `launch(grid, block, kernel)` which spreads blocks over the cores and waits until all are done.

## Results

- **Vector add**, 1,000,000 elements, blocks of 256 threads: max error 0, 3.2 ms.
- **Matrix multiply**, one thread per output element, 16 x 16 blocks, five shapes including a batch-1 row (1x768x2304) and an odd shape (257x100x191): **max relative error 0.0 against a plain CPU reference on every shape**; 2.4 to 6.5 GFLOP/s (naive kernels; not a speed claim).

## What it does not have yet

No shared memory or barriers between the threads of a block (needed for tiled matrix multiply and reductions); no compiler: kernels are Rust closures. **Next layer:** a kernel description that a code generator turns into PTX for a real NVIDIA GPU (K2: run on the Colab T4 and the founder's RTX 3050), then the same kernels written once for a second route. The kernels written here (vector add, matrix multiply) are the first test programs for it.

Related: [Stack plan](stack_plan.md), [CUDA study](../../docs/cuda_study_jarvis.md), [Docs index](../../docs/INDEX.md)
