---
title: Our own CUDA-like layer for inference - proposal: a small tensor compiler and runtime with several back ends (plan and bars, 2 Nov 2026, awaiting the founder's confirmation)
tags: [spark, software, stack, compiler, runtime, plan, cuda]
---

# A CUDA-like layer for inference: proposal (2 Nov 2026)

Founder's direction (2 Nov 2026): inference engines already exist; what companies need is a CUDA-like software platform. This plan replaces the "beat the free engine" goal of the [engine plan](../engine/engine_plan.md) with a narrower and harder one: **our own tensor-program layer** (an intermediate language, code generators for several back ends, a runtime), proven by running real models on it. The engine (E1 and E4) stays as the **correctness reference**. Not a clone: no CUDA API, no CUDA libraries; only public specifications are used (the PTX instruction-set document, the public driver interface, open standards). A lawyer must check the licence boundary before anything is released ([CUDA study](../../docs/cuda_study_jarvis.md)). Vision's CUDA research ([task 05](../../docs/vision_research_task_05.md)) is still pending and must be merged into this design.

## Design (three parts, small on purpose)

1. **IR:** a small language of tensor operations (matrix multiply, elementwise, reductions, softmax, layer norm, gather) with shapes and a memory layout, enough for a decoder model. Written in Rust, standard library only.
2. **Code generators:** CPU (Rust loops with blocking, threads, SIMD), **PTX text** for NVIDIA GPUs (public specification; the driver compiles it), and a second, non-NVIDIA route (Vulkan compute through SPIR-V, or OpenCL) so the claim "across hardware" is tested.
3. **Runtime:** buffers, host to device copies, kernel launch, synchronisation, for each back end; the memory manager for models larger than the GPU (the small-GPU pain) belongs here.

## Milestones and bars (fixed now)

- **K1 IR and CPU back end:** the E1 model expressed in the IR and run through the CPU generator gives logits within 1e-3 of PyTorch on the same 16 prompts, all greedy tokens equal.
- **K2 PTX matrix multiply:** a generated PTX kernel for the model's matrix shapes, run on a free cloud GPU (Colab T4) and on the founder's RTX 3050, matches numpy within 1e-3 relative error, on at least 5 shapes.
- **K3 whole model on a GPU:** the E1 model's forward pass through our stack on the T4 equals PyTorch within 1e-3, greedy tokens equal.
- **K4 speed:** generated matrix-multiply kernels reach at least **0.5x of the vendor library's speed** (as PyTorch calls it) for the model's batch-1 shapes on both GPUs; decode of the E1 model at batch 1 at least 0.5x of PyTorch with CUDA graphs on the T4 (our own earlier test: [test B](../../hw/gpu/graphs_test/PLAN.md)).
- **K5 second route:** the same IR runs on a non-NVIDIA path (Vulkan on the 3050 or a CPU through the same runtime interface) with K3's correctness; speed reported, no bar.
- **K6 memory manager:** a model larger than the 6 GB card (a 13B-class at 4-bit or INT8, per the [small GPU plan](../../hw/gpu/small_gpu/small_gpu_plan.md)) runs through the runtime at least 1.3x faster than the best free tool's offload on the same laptop.

## Stop rule and dates (my proposal; the founder may change them before the first run)

K1 by 9 Nov, K2 by 23 Nov, K3 by 7 Dec, K4 by 21 Dec. **If K2 is not met by 23 Nov, or K4 is below 0.3x on 21 Dec, the stack stops as a product project** and is kept as a learning artefact. Realistic odds are low: the closest small-team precedent (tinygrad, about 19,000 lines, a funded company of 11 to 50 people by one directory) took years; a two-person narrow stack in months should expect to reach a toy that is correct, not competitive.

## What this does not claim

No buyer exists for it yet ([research 04](../../docs/reviews/research_04_summary.md)); free projects already cover pieces of it; performance parity with tuned vendor libraries is a multi-year result.

Related: [Engine plan](../engine/engine_plan.md), [CUDA study](../../docs/cuda_study_jarvis.md), [Research task 05](../../docs/vision_research_task_05.md), [Project memory](../../docs/PROJECT_MEMORY.md), [Docs index](../../docs/INDEX.md)
