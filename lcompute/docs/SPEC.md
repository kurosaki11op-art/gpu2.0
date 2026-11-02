---
title: L Compute programming model specification, version 0.1 (2 Nov 2026)
tags: [spark, lcompute, spec, programming-model]
---

# Programming model, version 0.1

This is the contract kernels are written against. The interpreter implements it exactly; back ends must match it.

## Execution

- A **kernel** is a function with typed parameters, run once by every **thread**.
- Threads form **blocks**; blocks form a **grid**. Dimensions have three axes (x, y, z). Each thread can read its thread index, block index, block size and grid size (axis 0, 1, 2).
- **Blocks are independent:** no ordering between blocks, no communication between blocks inside one launch (global memory writes by different blocks must go to different locations).
- **Threads of one block** run concurrently in principle and can cooperate through **shared memory** and **barriers**.

## Memory spaces

- **Global:** buffers passed as parameters (32-bit floats in version 0.1), readable and writable by all threads; accesses are bounds-checked in the interpreter (an out-of-range access is an error, like a memory checker).
- **Shared:** per block, declared by the kernel with a fixed size, visible to the threads of that block only; undefined contents at start.
- **Registers:** per thread values of type i32, f32 or predicate (true or false); registers can be reassigned.

## Barrier

`barrier` makes every thread of the block wait until all threads of the block have reached it; writes to shared memory before the barrier are visible to all threads after it. **Every thread of a block must reach the same barriers in the same order, or the kernel is invalid** (the interpreter reports barrier divergence, including a thread that returns while others wait).

## Instructions (version 0.1)

Constants; special registers (thread, block, block size, grid size by axis); scalar parameters; integer and float arithmetic (add, subtract, multiply, divide, remainder, min, max, and, or, shifts); comparisons producing predicates; float unary operations (negate, absolute value, square root, exponential, hyperbolic tangent); conversions between i32 and f32; select; global and shared loads and stores; labels, unconditional and conditional branches, return.

## Not in 0.1 (planned)

Atomics, warp-level operations, f16 and integer-8 types, 64-bit integers, texture-like access, dynamic shared memory, streams and events (runtime layer), multiple kernels per launch graph.

Related: [README](../README.md), [ROADMAP](ROADMAP.md)
