---
title: L Compute roadmap and bars (written before the code, 2 Nov 2026)
tags: [spark, lcompute, roadmap, bars]
---

# Roadmap and bars (fixed now)

| step | deliverable | bar |
|---|---|---|
| **0** | README, [SPEC](SPEC.md), this roadmap | written before step 1 |
| **1** | IR, interpreter, builder; kernels: vector add, tiled matrix multiply with shared memory and barriers, block reduction | each kernel matches an independent plain reference within 1e-5 relative error on at least 5 launch shapes each, including shapes not divisible by the block size; barrier divergence and out-of-range access are detected and reported (two negative tests) |
| **2** | runtime layer: device, buffers, launch queue, errors | the step 1 kernels run through the runtime API only |
| **3** | CPU native back end (IR compiled to fast code, threads and SIMD) | all step 1 and 2 tests equal the interpreter's output; at least 20x faster than the interpreter on matrix multiply 512 |
| **4** | PTX back end | the step 1 kernels, generated as PTX and run on a Colab T4 and the founder's RTX 3050, match the interpreter within 1e-5 on all shapes |
| **5** | second route (Vulkan or OpenCL) | the same suite passes on a non-NVIDIA path or a second implementation |
| **6** | libraries: matmul, softmax, layer norm, attention, built from kernels in the language | the engine's E1 model runs through them and matches PyTorch within 1e-3; matmul at least 0.5x of the vendor library on the model's shapes |
| **7** | autodiff | gradients match PyTorch within 1e-4 on a transformer block; a tiny GPT trains to the same loss within 2% |

## Note, 2 Nov 2026 (after the step 1 run)

The step 1 bar (every shape within 1e-5 relative error) was **mis-specified for long inner dimensions**: one of 17 checks measured 1.00e-5; the kernel equals a sequential fp32 sum exactly ([result](lc_step1_result.md)). The original bar is recorded as **missed**. **Step 1b** replaces it for later steps: matrix products must agree with the sequential fp32 sum exactly in the interpreter and stay within `k x 6e-8 x sum of |terms|` of a float64 reference on every back end.

## Rules

Bars are not changed after a run; a miss is reported as a miss; dates for steps 2 and later are set when step 1 is done.

Related: [README](../README.md), [SPEC](SPEC.md)
