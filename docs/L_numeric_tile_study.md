---
title: L numeric tile study - benchmark list and an energy model (what a GPU does beyond L)
tags: [spark, research, benchmark, estimate, accelerator]
---

# L numeric tile study (28 Oct 2026)

Founder's question: we are fighting to replace GPUs, so what must a replacement do (rocket-style physics, 3D rendering, big models), and does placing memory on the chip solve it? This note lists the benchmarks, then runs an order-of-magnitude energy model. **Everything here is ESTIMATED, about plus or minus 3x, energy only.** No hardware, no GPU measured, no real chip simulated. Script and logs: [numeric_tile_model.py](../hw/brain/experiments/month5/numeric_tile_model.py), `numeric_tile_model_{64,256,1024}.log` in the same folder.

## 1. Benchmark list (workload sizes are round, typical numbers we chose, not measurements)

| workload | why it matters | bound by | arithmetic |
|---|---|---|---|
| Dense matrix multiply 4096^3 | core of training and of every layer | compute | fp32 multiply-add |
| 3D FFT 512^3 | signal processing, physics, imaging | memory | complex fp32 |
| 3D Poisson solve 256^3, CG 200 iterations | engineering simulation (heat, flow, fields) | memory | fp64, mixed precision possible |
| CFD stencil 512^3 x 100 steps | fluid and rocket-style flow solvers | memory | fp64 |
| Kalman filter, 12 states, 1e6 steps | navigation and control | latency, tiny | fp64 |
| Small network inference, int8, 1e6 images | perception | on-chip traffic | int8, about half zeros |
| LLM token generation, 1B parameters, int8 | language models | weight streaming | int8 |
| Ray tracing 1080p, 500 MB scene | 3D rendering | pointer chasing | fp32 |
| Sparse recognition (L-like), 1e6 images | our niche | table reads | int8 adds, 87% inputs off |

## 2. Model

Two architectures. **GPU style:** dense units, operands from a 1 MB-class cache, working set in external HBM; both the naive precision and a mixed-precision variant (so the comparison is fair). **Tile hypothesis (not a build):** memory in many small banks next to compute, the whole working set on chip when it fits the capacity (ONCHIP_MB), otherwise spilled to HBM; zero skipping where data is sparse; bulk work in low precision with a routed fraction in high precision. Constants: Horowitz 45 nm figures (MEASURED by their authors, quoted as references), fp64 assumed (4x fp32 multiply, an assumption), and a "modern" set (compute x0.2 assumed; HBM3E 5.74 pJ/bit and large SRAM 0.495 to 2.78 pJ/bit from the memory-technology study, MODELLED/ESTIMATED).

## 3. Results (modern constants, gain in energy over the GPU mixed-precision baseline, ESTIMATED)

| workload | 64 MB on chip | 256 MB | 1024 MB | where the tile's energy goes at 256 MB (compute / on-chip / external) |
|---|---|---|---|---|
| Dense matrix multiply | 1.8x | 4.0x | 4.0x | 59 / 32 / 9 % |
| 3D FFT | 1.8x | 2.1x | 4.7x | 3 / 23 / 74 % |
| Poisson CG | 1.3x | 2.0x | 32.8x | 1 / 5 / 94 % |
| CFD stencil | 1.5x | 1.6x | 2.5x | 4 / 13 / 83 % |
| Kalman | 2.5x | 2.5x | 2.5x | 63 / 37 / 0 % |
| Small network int8 | 20.6x | 20.6x | 20.6x | 2 / 98 / 0 % |
| LLM 1B int8 | 1.1x | 1.4x | 48.2x | 0 / 1 / 98 % |
| Ray tracing | 1.6x | 2.1x | 3.4x | 4 / 17 / 79 % |
| Sparse recognition (L-like) | 35.8x | 35.8x | 35.8x | 8 / 91 / 0 % |

## 4. What this says (ESTIMATED, read with the caveats)

1. **Capacity is the cliff.** The big gains for Poisson and the LLM appear only when the whole working set fits on chip (1 GB class); below that the tile is roughly a GPU. Moving memory onto the chip helps only as far as it fits, and SRAM area and cost are not modelled here, so the 1024 MB column may be unaffordable.
2. **The arithmetic primitive matters only for compute-bound kernels.** Compute is about 59% (dense multiply) and 63% (Kalman) of tile energy, and 1 to 12% for every memory-bound kernel. A cheaper multiplier, or no multiplier, cannot move memory-bound workloads; locality, capacity and skipping can.
3. **Our niche is real but narrow:** sparse event-driven recognition, 35.8x in this model, because 87% of inputs are off and the table lives in small banks.
4. **Where we lose or are unknown:** dense fp64 physics and large scenes or models need capacity or external memory; we would be a GPU-class competitor there at best, 1.3x to 4x at realistic capacities.
5. The fp64 constants are assumed, the workload sizes are chosen, and no accuracy or numerical-stability check was made (mixed precision can fail to converge). Treat every ratio as a direction.

## 5. Open question from the founder: one primitive for everything

Candidates to test before building: logarithmic number system (multiply as add), table-lookup multiplier, stochastic computing, block floating point or posits, analog in-memory compute. Test each for numerical error (matmul, FFT, CG convergence, Kalman) and estimated energy against the multiplier. Expectation (REASONING, not a result): the share-of-energy numbers above cap the gain at about 2x on compute-bound kernels and near 1x elsewhere, so the shoot-out should come after the capacity question.

Related: [Concept study: convolution](concept_study_convolution.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md), [Journal](journal.md)
