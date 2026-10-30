---
title: New start - three candidate targets with reasons, first tests and bars (30 Oct 2026)
tags: [spark, new-start, targets, plan, decision]
---

# New start: candidate targets (30 Oct 2026)

For the founder to accept or change. Labels: MEASURED / SIMULATED / ESTIMATED; "general knowledge" marks statements from outside the project that are not verified here. Rows refer to the [GPU workload census](gpu_workload_census.md). Principle from [the lessons](lessons_L_v1.md): the target and its bar come first, the incumbent is measured first, and the cheapest decisive test comes before any build.

| rank | target | GPU weaknesses it attacks | census rows | evidence in the project | first decisive test (pass or fail stated in advance) | main risk |
|---|---|---|---|---|---|---|
| 1 | **Always-on recognition and on-device learning** (sensors, cameras, devices that learn locally) | power, heat and cooling (no fan, battery), cost, heavy training (learns on the device with few examples, no backprop), stored knowledge (adds classes without retraining) | 14, 15 (partial), 7 | SIMULATED: 89.7% clothing within about 1 to 2 points of small CNNs, bit-exact chip on 10,000 images, on-chip learning (13,569 cycles per image), confidence curve and cascade; ESTIMATED energy 16x fewer operations than a small CNN | measure the RTX 3050 baseline on the same task and the board power; bar: at least 90% accuracy at one tenth the measured energy per image of the GPU at batch 1, and a new class learned from 5 examples in under one second on the board; fail: board energy not within 10x of the GPU at batch 1, then drop the energy claim and keep only the learning claim | accuracy is capped near 90% to 91%; the energy win is a chip projection, not something a board shows |
| 2 | **Irregular and sparse workloads** (graph traversal, sparse matrices, string and sequence matching) | utilisation and memory waste: a GPU's wide units idle on irregular memory access (general knowledge, widely reported; not measured here) | 2, 9, 10 | none in version 1 except sparse table reads (ESTIMATED 36x for recognition) | model one reference kernel per row from an open suite (breadth-first search, sparse matrix-vector product, sequence alignment) on an event-driven tile in simulation against the measured GPU utilisation; bar: at least 5x better energy per useful operation in the model or the row is dropped | an unproven idea; needs a new tile design; the GPU may already be good enough with the right library |
| 3 | **Batch-1 language-model inference at the edge** (token-by-token generation, memory-bound) | memory wall (every token reads all the weights), power, cost | 14 (large models) | ESTIMATED 48x energy gain only if a 1B-parameter int8 model fits on chip (about a gigabyte, costly at 5 nm); SIMULATED counting tables within 3 to 4% of an undertrained small transformer but with a wall near 2.3 bits per character | train a small low-bit transformer and a counting-plus-lookup hybrid on one corpus and measure quality against model size and memory traffic per token; bar: within 5% of the float transformer's quality at one tenth the memory traffic or the row is dropped | the biggest market and the largest gap between a tiny test and the real thing; needs gigabytes of weights |

## Not proposed now, and why

Dense numerics, graphics, ray tracing, video codecs, cryptography and backprop training are what a GPU is built for; matching them means building a GPU, and our own study found an efficiency edge of only 1.3x to 4x on dense kernels at realistic capacities (ESTIMATED). They stay in the census as stated "not covered".

## Suggested sequence

1. Founder picks the target (or an order). 2. Measure the GPU baseline on that target (needs the founder's laptop). 3. Run the target's first decisive test. 4. Only then design; the census rows of the chosen target become the acceptance suite, and every other row is published as not covered.

Related: [GPU workload census](gpu_workload_census.md), [GPU problem analysis](gpu_problem_analysis.md), [Lessons from L version 1](lessons_L_v1.md), [Docs index](INDEX.md)
