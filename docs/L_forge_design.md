---
title: L Forge - design of the third layer (what a GPU does, done our way)
tags: [spark, design, accelerator, l-forge, hypothesis]
---

# L Forge: design of the third layer (28 Oct 2026)

Name locked by the founder, 28 Oct 2026. L Forge is the general numeric layer of the three-layer chip (L Cortex, L Deep, L Forge): it does the work a GPU does that the first two cannot (dense linear algebra, FFT, physics solvers, filters, rendering), **by our own methods, not by imitating a GPU**. Target (locked 28 Oct): 5 nm, 2 GB of built-in memory. **Everything below is a design hypothesis built from our own estimates; nothing is built or measured.** Labels as elsewhere: ESTIMATED, SIMULATED, ASSUMED.

## 1. What a GPU does, and where it wastes (concept study, [GPU and memory](concept_study_gpu_and_memory.md))

Thousands of lock-step lanes, a four-step memory ladder (registers, shared memory, L2, HBM), the same precision for everything, every element computed whether it is zero or not. Our estimates say most of its energy is data movement (external memory 74 to 98% of energy in memory-bound kernels) and that the multiplier is only 1 to 12% of those kernels ([tile study](L_numeric_tile_study.md)).

## 2. The differences L Forge is built on (each with its evidence and its test)

| # | difference | GPU does | L Forge does | evidence | status |
|---|---|---|---|---|---|
| D1 | **Memory in the tile, the whole working set on chip** | streams from HBM through a ladder | 48 KB banked SRAM per tile, data stays put, work moves | tile model: 2 to 48x at 2 GB (table 5) | ESTIMATED; fabric traffic not modelled |
| D2 | **Precision routing** | one precision per kernel | bulk in 8-bit block floating point or int8, a small routed share in fp32 or double (iterative refinement) | primitive test: only fp16, bfloat16, int8, 8-bit block floating point pass four kernels; low precision stalls CG at 1e-2, refinement needed | SIMULATED error; refinement loop built and converges on Poisson with 8-bit inner solves, about half the traffic; with a stencil multigrid preconditioner the solve itself needs far fewer passes ([refinement loop](../hw/results/refinement_loop.md)) |
| D3 | **Event-driven skipping** | computes zeros | tiles do work only where data is non-zero or changed | 35.8x on sparse recognition; 4.7x when run dense | ESTIMATED; helps only sparse work |
| D4 | **Banked, gated reads** | wide reads from large arrays | wake one 6 KB bank, gate the others | 3 to 5x on L Deep reads (model); layout power 366 to 47 mW with gating (ESTIMATED) | needs Forge tile layout |
| D5 | **Dispatch by input** | the host launches kernels | an always-on dispatcher wakes only the layer needed; Cortex first, early exit | early exit works (0.967 vs 0.968), predictive wake not supported ([dispatch tests](../hw/results/dispatch_tests.md)) | SIMULATED for recognition only; the rule for numeric jobs is the free input-type tag |
| D6 | **Deterministic dataflow, no cache** | caches and thread scheduling | a compiled static schedule, single-cycle bank access | Cerebras precedent (variation under 4%, vendor-affiliated) | HYPOTHESIS for us; needs a compiler |
| D7 | **Cost-aware by design** | one large die | add-only path first, multiply only where it pays; tile logic kept small; layers share one interface | cost and power limits note | ASSUMED tile area |
| D8 | **Measured acceptance tests, not promises** | n/a | a capability ships only if its benchmark beats the GPU baseline | rule from the founder: each layer earns its place by test | process |

## 3. Tile (hypothesis, to be sized by synthesis)

Per tile: 8 banks of 6 KB (48 KB), a router with five ports, a small scheduler with an event queue, an **add path** (ternary and int8 adds, no multiplier, the L way), **block floating-point multiply-accumulate lanes** (labelled hybrid component, used only where a test shows it pays), and a small high-precision unit for the routed refinement share. 2 GB at 48 KB per tile is 43,690 tiles.

## 4. Size and cost at 5 nm, 2 GB (ESTIMATED, assumed tile logic)

Memory is about 683 mm2; the rest depends on tile logic, which is an assumption: add-only tile 0.005 mm2 (901 mm2 total, 2 dies, Rs 32k bare, Rs 81k finished); **Forge tile with multiply-accumulate lanes 0.015 mm2 (1,338 mm2, 3 dies, Rs 48k bare, Rs 120k finished)**; Cerebras-size tile 0.025 mm2 (1,775 mm2, 3 dies, Rs 73k bare, Rs 182k finished). So the locked target's cost depends on how small the Forge tile can be made, and the earlier 2-die figure assumed the add-only tile.

## 5. Acceptance tests (target gains at 2 GB, modern constants, ESTIMATED upper-bound-style model gains over a mixed-precision GPU baseline)

| benchmark | gain | what could break it |
|---|---|---|
| Dense matrix multiply | 4.0x | compute-bound; multiplier energy equals a GPU's, gain is memory only |
| 3D FFT | 5.1x | all-to-all traffic across tiles, not modelled |
| Poisson CG, fp64 | 33x | convergence under mixed precision; neighbour traffic |
| CFD stencil, fp64 | 8.2x | neighbour traffic; fp64 share |
| Kalman filter | 2.5x | tiny, latency-bound |
| Small network, int8 | 20.6x | sparsity assumption (half zeros) |
| 1B-parameter language model, int8 | 48x | weights must be stationary beside compute |
| Ray tracing | 3.4x | irregular memory access |

## 6. Where L Forge is not better (honest)

Dense matrix multiply gains only memory energy; a multiplier costs the same. Fabric traffic between tiles (FFT, stencils, all-reduce) is **not in the model** and could remove much of D1's gain. fp64 at scale needs the refinement loop to converge. GPUs have a software moat (CUDA, libraries) that a new chip has no answer to without a compiler. No GPU or tile has been measured.

## 7. Build order (each step a test before the next)

1. Numerical: build the block floating-point multiply-accumulate with refinement in simulation and show CG and Kalman converge to fp64 accuracy (builds on the primitive test).
2. Area: synthesise the add-only tile and the Forge tile in the open flow; replace the assumed 0.005 and 0.015 mm2 with measured areas.
3. Traffic: add a tile-to-tile traffic and energy model for FFT and stencil; re-run the acceptance table.
4. Software: define how a kernel is mapped to tiles and compiled; run the benchmark list on an emulator.
5. FPGA: a few tiles on the FPGA for the pitch, measured energy against a GPU on the same small kernel.

Related: [L numeric tile study](L_numeric_tile_study.md), [GPU and memory concept study](concept_study_gpu_and_memory.md), [Arithmetic primitive shoot-out](../hw/results/arithmetic_primitive_test.md), [Cost and power limitations](../hw/results/cost_and_power_limitations.md), [Dispatch tests](../hw/results/dispatch_tests.md), [One chip, three layers](../hw/results/one_chip_three_layers.md), [Docs index](INDEX.md)
