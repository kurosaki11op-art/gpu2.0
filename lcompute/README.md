---
title: L Compute - our own CUDA-like compute platform, built layer by layer (project start, 2 Nov 2026)
tags: [spark, lcompute, cuda, platform, compiler, runtime, project-start]
---

# L Compute (project start, 2 Nov 2026)

Founder's instruction (2 Nov 2026): start from scratch and build the CUDA-like platform step by step, properly. This folder is a **new, self-contained project**; the earlier engine ([`sw/engine`](../sw/engine/engine_plan.md)) is the correctness reference for model code, and [`sw/stack/minicuda.rs`](../sw/stack/K0_result.md) was the throw-away first experiment this design replaces.

## What it is

A compute platform with the layers CUDA has, designed by us from public specifications (no CUDA code, no CUDA libraries; the PTX document is public and is the only NVIDIA specification used; a lawyer must check the licence boundary before any release, see the [CUDA study](../docs/cuda_study_jarvis.md)):

| layer | CUDA's version | ours | status |
|---|---|---|---|
| 1. Programming model | kernels, grid, blocks, threads, memory spaces, barriers | [SPEC](docs/SPEC.md) | step 0 written |
| 2. Intermediate language | PTX | our IR ([`src/ir.rs`](src/ir.rs)) | step 1 built |
| 3. Reference execution | none public | our interpreter, the ground truth for semantics ([`src/interp.rs`](src/interp.rs)) | step 1 built |
| 4. Kernel front end | nvcc, CUDA C++ | a Rust builder API ([`src/builder.rs`](src/builder.rs)), a text language later | step 1 built (builder) |

Step 1 result: [lc_step1_result](docs/lc_step1_result.md) (first run 16 of 17, one missed the written bar by a hair; fixed with two-level summation; second run 17 of 17, worst error 2.9e-6).
| 5. Back ends | PTX to machine code | CPU native, PTX for NVIDIA GPUs, a second non-NVIDIA route | steps 3 to 5 |
| 6. Runtime and driver API | cudaMalloc, memcpy, launch, streams | device, buffers, in-order streams, checked errors ([`src/runtime.rs`](src/runtime.rs)) | step 2 built; step 3 fast back end built, speed bar missed ([step 3](docs/lc_step3_result.md)); ([result](docs/lc_step2_result.md)) |
| 7. Libraries | cuBLAS, cuDNN and others | matmul, softmax, layer norm, attention first | step 6 |
| 8. Autodiff for training | frameworks on top | gradients as IR transforms | step 7 |

## Method

Every step has a **bar written before the code** ([ROADMAP](docs/ROADMAP.md)), a **conformance test against an independent reference**, and a result note with its label (MEASURED / SIMULATED / and so on). The interpreter defines what a kernel means; every back end must agree with it on the whole test suite.

## Run

```
cd lcompute/src && rustc --edition 2021 -O main.rs -o /tmp/lcompute && /tmp/lcompute
```

Documents: [index](docs/INDEX.md), [WHY](docs/WHY.md).

Related: [Stack plan](../sw/stack/stack_plan.md), [CUDA study](../docs/cuda_study_jarvis.md), [Engine plan](../sw/engine/engine_plan.md), [Docs index](../docs/INDEX.md)
