---
title: Deep study of GPUs - what they lack, and our wafer design built from the lessons (plan, 31 Oct 2026)
tags: [spark, gpu, wafer, study, plan, software]
---

# Deep study plan (31 Oct 2026)

Founder order: build a wafer-scale processor with its own software stack (a CUDA-class layer), after a deep study of GPUs, fixing their problems and what holds AI back. Method (founder rule, 28 Oct): for each concept, write why it exists, how it is built, where it is used, its flaws and limits; then design our own fix; then test it against a bar written before the test. Existing models must still run (compatibility layer). Every number carries MEASURED / SIMULATED / MODELLED / ESTIMATED / PROJECTED.

## Concepts to study (one note each, in this order)

1. Execution model: SIMT, warps, thread blocks, scheduling and divergence.
2. Memory hierarchy: registers, shared memory, L1/L2, HBM; bandwidth wall, capacity, data movement energy.
3. Matrix units (tensor cores) and number formats: fp32/16/8/4, block scaling, accuracy limits.
4. Interconnect and scale-out: NVLink/PCIe/network, collective operations, synchronisation cost.
5. Software stack: CUDA programming model, kernels, compilers, libraries, graph capture, portability; lock-in and what a compatibility layer needs.
6. Sparsity and conditional compute: what GPUs cannot exploit (irregular access, MoE routing).
7. Batching and latency: why GPUs need batches, tail latency, KV cache memory.
8. Reliability and power: failure rates, power capping, cooling.
9. Training versus inference needs on one design.
10. Wafer-scale specifics: on-wafer mesh, defect routing, power delivery, packaging, programmability limits seen in existing wafer-scale systems.

Each note ends with a table: flaw, evidence (source or measurement), our fix, test and pre-set bar, status.

## What may hold AI back (hypotheses, not facts, each to be tested or marked untestable here)

- Memory capacity and bandwidth per unit of compute (the wall decode hits). Testable in the model.
- Energy per operation and per bit moved. Testable in the model and, partly, by counted operations.
- Latency per token for long reasoning chains. Testable by simulation (striping).
- Programming difficulty and lock-in. Partly testable (how many lines to port a model).
- Continual learning, memory over long time, learning from few examples. These are algorithm questions; hardware may help but the project has retired its own accuracy work (see the charter). Marked as outside what this chip can prove.
- AGI itself: not testable by a hardware project. No claim will be made.

## Software layer plan

- Our own programming model on the tile instruction set (ISA v0 exists, simulator exists).
- A compiler front end that imports existing models (M4 plan: importer, GPT-2-class decoder).
- A compatibility path for the common model formats; CUDA source compatibility is a separate, large decision and is not promised.

## Order of work

1. Striping and wafer system model under the Vision corrections ([plan](../hw/gpu/stripe_plan.md)).
2. Concept notes 1 to 10, starting with 2 (memory), 4 (interconnect), 5 (software).
3. Hardware cost: the founder's price research ([prompt](wafer_price_research_prompt.md)); the 30 lakh figure is unconfirmed as to what it covers.

Related: [Own GPU charter](own_gpu_charter.md), [Finish plan](product_finish_plan.md), [Wafer price research prompt](wafer_price_research_prompt.md), [Workload map](gpu_workload_map.md), [Docs index](INDEX.md)
