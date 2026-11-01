---
title: Weakness A (decode leaves compute idle) - our striped design does not fix it at batch 1; its edge is aggregate bandwidth (1 Nov 2026, DERIVED from simulation)
tags: [spark, gpu, weakness, decode, utilisation, result, vision-research-02]
---

# Weakness A: does our design keep the compute busy at batch 1?

**DERIVED from existing SIMULATED counters** ([striping result](stripe_result.md)); no new run. **Honesty note on the bar:** [Vision's proposed bar](../../docs/reviews/research_02_summary.md) was at least 60% matrix-unit utilisation at batch 1 on a 7B-class layer, stalls included. The numbers below were already in hand from the striping runs, so this is a **computed result against that bar, not a pre-registered prediction test**; I say so to avoid presenting it as one.

## The arithmetic

- **At batch 1 every weight byte feeds exactly one multiply-add** (INT8). So the compute floor equals the weight-read floor: no design can keep the multipliers busy longer than the weights take to arrive.
- **Tile level (M3 RTL, bit-exact, SIMULATED):** 256 multiply-adds per cycle on 256 weight bytes per cycle; a batch-1 product takes about `n x k` cycles plus 3 of pipeline fill, so the matrix unit is busy about 99% of the time **while it is fed**.
- **System level (striped scaled decoder, 288 tiles, 16 layers, d 512; SIMULATED, link 64 B per cycle, 2 cycles per hop, 1 GHz):** per token 54.4 million multiply-adds in 32,517 cycles with an empty cache: compute floor 738 cycles, so **matrix-unit utilisation = 2.3%**. With a 2,016-token cache and striped attention: 51,461 cycles, **2.3%** again. About 98% of the time is broadcast, gather, hops and the small unstriped operations, not compute and not memory.
- **Bar of 60%: missed by a factor of 26** at system level.

## Against the GPU (all labels as shown)

- Published (Vision, one H100, arXiv 2609.12923, MEASURED by that paper): decode matrix kernels busy about 9% of the time, 2% to 12% of matrix fragments used.
- **Our own T4 run (MEASURED, test B):** 1.1B-class model at batch 1 with graphs reaches 95% of the **memory** floor but only about **0.35%** of the T4's peak half-precision matrix rate (227 GFLOP/s against a spec peak of about 65 TFLOP/s, the peak from memory so ESTIMATED).
- Ours: 2.3% of our own peak (147 TFLOP/s at 288 tiles, 1 GHz, ASSUMED clock).
- **Reading:** both machines leave about 98% or more of the multipliers idle at batch 1. That is not a flaw one machine fixes: it follows from one multiply-add per weight byte. **Our design does not solve weakness A at batch 1.**

## What our design does have (and what it costs)

- **Aggregate bandwidth:** 288 tiles x 256 bytes per cycle x 1 GHz is about 74 TB/s of weight reads, against 0.24 TB/s on the T4 (about 300x). The simulated token takes 33 to 51 microseconds against 9.7 ms for the same model on the T4 with graphs (about 190x to 290x faster; the model sizes are not identical, the scaled decoder has 59 million weights against 1.1 billion, so this is **not** a like-for-like speed ratio).
- **The price is capacity and area:** the 4 MB tiles hold 59 MB of weights on 288 tiles at 20% fill; a 7B-class model needs about 1,700 tiles (7 GB over 4 MB), a 1T model about 5 wafers (earlier notes).
- So the honest claim is **bandwidth per chip from on-chip memory, bought with capacity and cost**, the same trade Cerebras, Groq and others already make. Utilisation is not a differentiator.

## What would raise utilisation (untested)

Cut the communication from about 98% of the time to a few percent: fewer, larger tiles per matrix; overlapping broadcast with compute; batching several requests (the first request pays the hops, the others share them). Each is a design experiment with a bar of its own; none is run.

## Status

- Weakness A as a **design claim: not supported** (2.3% against a bar of 60%; the same order as a GPU's idle compute).
- The shortlist now rests on **memory bandwidth and energy per bit against capacity and cost** (weakness E and the capacity gap G3), and on the measurement report. Next: decide, with Vision, whether a tiered-memory design (SRAM plus larger, slower memory) can fix capacity at a sensible cost; that is bar G3 in the step 5 model.

Related: [Striping result](stripe_result.md), [Test B plan and result](graphs_test/PLAN.md), [Research 02 summary](../../docs/reviews/research_02_summary.md), [Response to research 02](../../docs/reviews/jarvis_response_research_02.md), [Hardware index](../HARDWARE_INDEX.md)
