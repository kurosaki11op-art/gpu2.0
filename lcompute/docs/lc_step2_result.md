---
title: L Compute step 2 result - the runtime layer: buffers, in-order streams, checked errors; all bars R1 to R5 pass (2 Nov 2026, MEASURED)
tags: [spark, lcompute, result, step2, runtime]
---

# Step 2 result (2 Nov 2026)

**MEASURED** on the cloud container's CPU. Bars (written first): [ROADMAP](ROADMAP.md) step 2. Code: [`runtime.rs`](../src/runtime.rs) (about 60 lines of runtime), tests [`step2.rs`](../src/step2.rs).

## What was built

A runtime API with the shape of a GPU runtime, running the reference interpreter behind it: `alloc`, `free` (waits for all streams, like cudaFree), `create_stream` (a worker thread with an in-order command queue), `copy_to_device`, `copy_to_host`, `launch` (asynchronous: it returns once the command is queued), `synchronize`. Mistakes are checked where they are made (copy sizes, handles, argument count and kinds at enqueue time) and errors inside kernels are held per stream and returned by `synchronize`, once.

## Results (all bars met)

- **R1:** the step 1 kernels run through the runtime only: vector add (n = 100,003) exact; matrix multiply 33x129x17 within 1.0e-6; block reduction (n = 12,345) within 3.6e-7.
- **R2:** two dependent launches on one stream with no wait between them: exact.
- **R3:** four independent streams: each exact; **100 chained launches on one stream end at exactly 100 in every element.**
- **R4:** all seven kinds of mistake are reported with a message naming the problem (wrong-size copy, use after free, double free, unknown handle, wrong argument count, wrong argument kind, out-of-range access inside a kernel); an extra check shows the error is reported once and the stream is usable afterwards.
- **R5:** zero live buffers after freeing everything; dropping the runtime joins its threads.
- **Bar R1 to R5: PASS.**

## A bug found on the way (recorded)

The first run **hung**: `free` held the stream-list lock for the whole `for` loop (a lock guard written inside the loop header lives until the loop ends) while `synchronize` tried to take it. The test timeout exposed it; fixed by taking the count first. Found by running the tests, not by reading the code, which is the point of having them.

## Limits

Float32 buffers only; the back end behind the runtime is the slow reference interpreter; no events, no copies between streams, no pinned memory, no multi-device, no memory pool; concurrency was tested on four streams and 100 chained launches, not stress-tested; the runtime has no GPU yet (that is step 4).

## Next (step 3)

The CPU native back end: the same IR compiled into fast code (threads and SIMD) behind the same runtime, with a bar written first: outputs equal to the interpreter's on the whole suite and at least 20x faster on matrix multiply 512.

Related: [README](../README.md), [ROADMAP](ROADMAP.md), [Step 1 result](lc_step1_result.md), [Docs index](../../docs/INDEX.md)
