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

## Step 2 bars (written before the code, 2 Nov 2026)

Deliverable: a runtime API (`alloc`, `free`, `create_stream`, `copy_to_device`, `copy_to_host`, `launch`, `synchronize`) with in-order streams and checked errors, running the reference interpreter behind it. Bars:
- **R1:** the step 1 kernels (vector add n = 100,003; matrix multiply 33x129x17; block reduction n = 12,345) run **through the runtime API only** and meet the step 1 bars.
- **R2 order:** two dependent launches on one stream with no synchronisation between them give the exact result (the second sees the first's output).
- **R3 concurrency:** 4 independent launches on 4 streams are each correct; 100 chained launches on one stream (`x = x + 1`) end at exactly 100.
- **R4 errors detected and reported with a message** (7 cases): wrong-size copy; use of a freed buffer; double free; unknown buffer handle; launch with the wrong number of arguments; launch with an argument of the wrong kind; an out-of-range access inside a kernel reported by `synchronize`.
- **R5 resources:** after all buffers are freed the runtime reports zero live buffers; dropping the runtime joins its stream threads without hanging.

## Step 3 bars (written before the code, 2 Nov 2026)

Deliverable: a **lockstep block executor**: the threads of a block run together, every instruction applied to all active threads at once as a tight loop (registers stored per instruction, not per thread), divergent branches handled by running the lowest-numbered instruction among the active threads first so that threads re-join (barriers become waiting points). Same meaning as the interpreter; selectable behind the runtime.
- **C1 equality:** every launch of the step 1 suite (all shapes of all three kernels) gives **bit-identical output buffers** from the fast back end and the interpreter.
- **C2 errors:** both negative tests (barrier divergence, out-of-range access) are still detected, with the same kind of message.
- **C3 runtime:** the step 2 suite R1 to R5 passes with the fast back end behind the runtime.
- **C4 speed:** the 512 x 512 x 512 tiled matrix multiply runs **at least 20x faster** than the interpreter on the same machine (wall-clock; interpreter measured once, fast back end best of 3); GFLOP/s reported.
- **C5 reported, no bar:** vector add and block reduction at 1,000,000 elements, both back ends.

## Note, 2 Nov 2026 (after the step 1 run)

The step 1 bar (every shape within 1e-5 relative error) was **mis-specified for long inner dimensions**: one of 17 checks measured 1.00e-5; the kernel equals a sequential fp32 sum exactly ([result](lc_step1_result.md)). The original bar is recorded as **missed** on the first run, and **passed on a second run after a kernel fix** (two-level tile summation; worst error 2.9e-6). **Step 1b** replaces it for later steps: matrix products must agree with the sequential fp32 sum exactly in the interpreter and stay within `k x 6e-8 x sum of |terms|` of a float64 reference on every back end.

## Rules

Bars are not changed after a run; a miss is reported as a miss; dates for steps 2 and later are set when step 1 is done.

Related: [README](../README.md), [SPEC](SPEC.md)
