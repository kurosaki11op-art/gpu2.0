---
title: GPU workload census - every computation pattern a GPU is used for, and what version 1 tested (30 Oct 2026)
tags: [spark, gpu, workloads, census, coverage, test-plan]
---

# GPU workload census (30 Oct 2026)

Founder's rule (30 Oct 2026): before designing, know every process a GPU is used for and test that the design can do each one. **"Every application" is not a closed list, but computation patterns are close to one.** Standard practice is to classify by pattern, not by application: the Berkeley "dwarfs" (the 2006 Berkeley view of parallel computing; Rodinia, a GPU suite, was built around them), plus the GPU domains the dwarfs do not cover (fixed-function graphics, video codecs, machine learning, cryptography). This census is written from the project's knowledge plus two web checks on 30 Oct 2026; the dwarf list itself is from memory and **must be checked against the original report (Asanovic et al., EECS-2006-183)** before it is relied on (the search results confirmed the idea, the original seven, and that later slides count 14, but did not return the full list). Benchmark suites confirmed by search: Rodinia, SHOC, Parboil, SPEC ACCEL (19 OpenCL and 15 OpenACC and OpenMP applications); MLPerf was **not** confirmed by the search. Sources: [Berkeley CS267 syllabus](https://people.eecs.berkeley.edu/~demmel/cs267_Spr16/Syllabus.html), [ALTIS GPGPU benchmarking paper](https://arxiv.org/pdf/1906.10347), [SPEC ACCEL 1.2](https://www.spec.org/accel/press/accelv12release.html).

## Census and version 1 status

Status columns use only what was actually run in version 1 (SIMULATED RTL or model); "none" means never attempted.

| # | pattern | typical GPU uses | what the hardware needs | version 1 status |
|---|---|---|---|---|
| 1 | dense linear algebra | matrix multiply, solvers, deep-net layers | multiply-add at high rate, regular memory | SIMULATED RTL: block floating-point lane and mesh matrix multiply, bit-exact |
| 2 | sparse linear algebra | conjugate gradient, graph analytics | gather/scatter, irregular memory | partial: Poisson CG with refinement through the lane model; sparse table reads in recognition; no sparse-matrix engine |
| 3 | spectral methods | FFT, signal processing, imaging | butterflies, all-to-all transposes | partial: DFT through the lane model, all-to-all mesh verified; no butterfly path |
| 4 | N-body methods | molecular dynamics, astrophysics | pairwise force, reciprocal square root | none |
| 5 | structured grids | stencils, CFD, weather | regular neighbour access, halo exchange | partial: stencil as a preconditioner in the lane model; no halo-exchange test |
| 6 | unstructured grids | finite elements, meshes | indirect indexing | none |
| 7 | map-reduce and Monte Carlo | random sampling, finance, histograms | random numbers, reductions | none (one random generator exists in the Cortex dreaming) |
| 8 | combinational logic | hashing, crypto, bit operations | bit-level logic | none |
| 9 | graph traversal | search, shortest paths, social graphs | pointer chasing, irregular parallelism | none |
| 10 | dynamic programming | sequence alignment, string matching | wavefront dependencies | none |
| 11 | backtrack and branch-and-bound | solvers, planning | irregular tree search | none |
| 12 | graphical models | probabilistic inference | message passing | none |
| 13 | finite state machines | parsing, compression, protocols | serial state updates | none |
| 14 | machine-learning inference | image, speech, language models | low-precision multiply, large weights | partial: small recognition (89.7% clothing) and a counting-table language model (2.33 bits per character); no large model |
| 15 | machine-learning training | backpropagation, optimisers | gradients, high precision, memory for activations | partial: on-chip counting-rule learning only; no backprop |
| 16 | fixed-function graphics | rasterisation, texturing, depth, blending | dedicated pipeline hardware | none |
| 17 | ray tracing | rendering, simulation | BVH traversal, intersection tests | none (dropped after the traffic model) |
| 18 | video encode and decode | streaming, conferencing | dedicated codec blocks | none |
| 19 | cryptography and zero-knowledge | mining, ZK proofs (large integer and modular arithmetic, number-theoretic transforms) | wide integer arithmetic | none |

## How "can do every process" would be tested

For each row: a reference workload (from Rodinia, SHOC, Parboil, SPEC ACCEL or, for machine learning, MLPerf once its categories are checked), a golden answer (fp64 or the reference implementation), a pass criterion (correct answer within a stated error), and a cost measurement (cycles, energy, memory). A row may be claimed as covered only with a passing result in the coverage matrix; any row without one is stated as not covered. Test order by cost of the test: the rows with a standard open reference (1, 2, 3, 5, 14) first in simulation, then the irregular rows (6, 9, 10) which show whether the design handles non-regular memory at all.

## The tension to decide on

Covering all 19 rows is what a GPU is: wide arithmetic, high-bandwidth memory, thread scheduling, plus dedicated graphics, ray-tracing and video blocks. Our own energy study found gains of only 1.3x to 4x on dense and bandwidth-bound kernels at realistic on-chip capacities, and large gains only for sparse recognition (about 36x, ESTIMATED) and for models that fit on chip. So "does everything a GPU does" and "far more efficient than a GPU" pull in opposite directions; the census and the coverage matrix make that trade-off measurable instead of arguable. A design can be honest in either form: a general machine with a modest efficiency edge, or a specialised machine with a large edge on a stated subset.

Related: [GPU problem analysis](gpu_problem_analysis.md), [Lessons from L version 1](lessons_L_v1.md), [Numeric tile study](L_numeric_tile_study.md), [Docs index](INDEX.md)
