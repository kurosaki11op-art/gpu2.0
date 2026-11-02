---
title: L Compute step 1 result - IR, interpreter and builder: 16 of 17 checks pass, one misses the written bar by a hair, kernels are exact (2 Nov 2026, MEASURED)
tags: [spark, lcompute, result, step1, interpreter]
---

# Step 1 result (2 Nov 2026)

**MEASURED** on the cloud container's CPU. Bar (written first): [ROADMAP](ROADMAP.md) step 1. Code: [`ir.rs`](../src/ir.rs), [`builder.rs`](../src/builder.rs), [`interp.rs`](../src/interp.rs), kernels and tests in [`main.rs`](../src/main.rs).

## What was built

- **IR:** a flat register-based instruction list with labels and branches (typed i32, f32, predicate), global and shared memory, barrier.
- **Interpreter:** the reference semantics of the [SPEC](SPEC.md): blocks in parallel on CPU threads, threads of a block run to each barrier in turn, **bounds-checked memory**, **barrier divergence detected** (a thread returning while others wait).
- **Builder:** a Rust API in which kernels are written as ordinary code (loops, conditions, shared arrays, barriers).
- **Three kernels:** vector add; **tiled matrix multiply** (16 x 16 tiles staged through shared memory with barriers); **block reduction** (shared-memory tree).

## Results

- Vector add: 5 sizes (1 to 100,003): exact.
- Block reduction: 5 sizes (1 to 65,537, including sizes not divisible by 256): max relative error 1.2e-6.
- Tiled matrix multiply, 6 shapes (including 1x768x2304, 17x33x45, 33x129x17: not divisible by the tile): relative errors 5.8e-7 to 2.8e-6 on five shapes and **1.00e-5 on 1x768x2304**.
- **Negative tests:** barrier divergence **detected**; out-of-range global load **detected**, each with a message naming the kernel, block and thread.
- **Bar (every kernel within 1e-5 relative error on at least 5 shapes, both negative tests detected): FAIL as written**, by one check of 17: the 1x768x2304 matrix multiply measured 1.00e-5 against a double-precision reference.

## Why, and what it does not mean

The diagnostic run compares the kernel with a **sequential fp32 sum in the same order: the difference is exactly 0 on all six shapes.** So the kernel computes exactly what the specification says; the 1.00e-5 is the rounding error of adding 768 float32 products, measured against a float64 reference. **The bar was mis-specified for long inner dimensions**; I am **not** calling step 1 passed on the original bar and I do not change it after the run. **Step 1b (new, written now, applied to later steps):** matrix products are checked against a bound that scales with the rounding the sum can incur, error at most `k x 6e-8 x sum of |terms|` (the standard fp32 bound) **and** exact agreement with the sequential fp32 sum for the interpreter's own kernels. Under step 1b the results above pass (stated as a re-specification, not as a pass of the first bar).

## Limits

Float32 buffers and scalar parameters only; no atomics, no warp operations, no f16 or int8; the interpreter is slow (it defines meaning, it is not a back end); the matrix multiply is one tile size; tests run on the CPU only.

## Next (step 2)

The runtime layer (device, buffers, launch queue, errors) so the same kernels run through an API instead of raw interpreter calls; then step 3, the CPU native back end, with the bar written before it.

Related: [README](../README.md), [SPEC](SPEC.md), [ROADMAP](ROADMAP.md), [Docs index](../../docs/INDEX.md)
