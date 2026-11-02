---
title: Engine milestone E2 - INT8 weights cut memory to 0.25x but miss the quality bar (+0.014 nats) and are only 1.2x faster; the memory-bound reading was wrong (2 Nov 2026, MEASURED)
tags: [spark, engine, software, result, e2, quantization]
---

# Engine E2 result (2 Nov 2026)

**MEASURED** on the cloud container's CPU. Plan and bars (written first): [engine plan](engine_plan.md); predictions P1 to P3 (written before the code): [engine study](engine_study.md). Code: INT8 path in [`engine.rs`](engine.rs) (`build_q`, `step_q`), check [`check_e2.py`](check_e2.py). Same public 6-layer checkpoint as E1.

## Result against the bars and predictions

| item | bar or prediction | measured | verdict |
|---|---|---|---|
| **Quality (bar, P1)** | loss increase at most 0.01 nats per token, 96 windows of 64 predictions, paired 95% interval | fp32 5.7314, INT8 5.7454: **+0.01407 nats per token, interval [+0.00863, +0.01951]** | **FAIL** (upper end above 0.01; the point estimate is also above) |
| **Memory (bar, P2)** | INT8 weight bytes at most 0.30 x fp32 | 81.4 MB against 324.3 MB: **0.251 x** | **PASS** |
| **Speed (P3)** | about 17 ms per token (3.5x to 4x faster), "or the engine is not memory-bound" | INT8 **50 to 60 ms** per token against **62 to 75 ms** for fp32 in the same run: **1.2x faster** | **P3 FAILED** (gain under 2x) |

- The text sample is project documents, not typical prose, so the absolute loss (5.7 nats) is high; the comparison is paired and relative. The engine's fp32 loss agrees with PyTorch within 1.1e-5 nats on 8 windows, so the loss measurement itself is sound.
- **Per the pre-set rule,** a gain under 2x means the engine **was not memory-bound** at this point; my study's reading that it already sat at the memory limit (68 ms against a 67.5 ms floor from a numpy sum) was a **coincidence of two numbers and was wrong**. Evidence: INT8 reads 81 MB in about 50 ms, i.e. 1.6 GB/s, far below the 4.8 GB/s the same machine streams, so the bytes are not the limit.

## Diagnosis (hypothesis, to be tested; not yet a result)

Both dot-product loops that compute the output logits (50,257 rows of 768, 38.6 million multiply-adds, 47% of the work) add into **one** float accumulator. Floating-point adds have about 4 cycles of latency and a compiler may not reorder them, so each add waits for the last: about 38.6 million x 4 cycles at 2.1 GHz is **about 70 ms**, the measured order. The layer matrices use a different loop form that does not have this chain. **Prediction E2c (written before the change):** splitting each dot product over 8 independent accumulators makes the fp32 decode **at least 1.4x faster** at equal outputs (within 1e-4 of the current logits). If it is not, the diagnosis is wrong.

## E2c result: the dependent-add hypothesis was mostly wrong (same day, MEASURED)

Splitting the two output-layer dot products over 8 independent accumulators changed the logits by at most 3.2e-4 (summation order; above my own 1e-4 criterion, inside the E1 bar of 1e-3) and gave: fp32 decode **51.7 ms per token against 62.2 ms** at the start of the sequence (**1.20x**) and 66.3 against 74.6 ms at positions 448 to 511 (1.13x); INT8 **41.3 against 50.3 ms** (1.22x). **Prediction E2c (at least 1.4x) failed:** the add chain explains a part (about 10 ms of 62), not the bulk. **The honest state is that I do not know where the other time goes**; two guesses (memory-bound, add chain) were each tested and each was only partly right. Next, before changing anything else: **instrument the engine with section timers** (layer matrices, attention, output layer, per token) and read the split, then decide. The 8-accumulator dot products stay in the code (a modest gain); the decode path now differs from the full pass by up to 3.2e-4, so E4's "bit-identical" statement holds only for the earlier build (the E4 bar of 1e-3 still holds).

## Quality: what to try, with its own bar

The failure is small (0.014 nats, about 0.25% of the loss) but is a miss. Candidate causes: one scale per output column is dominated by outlier weights (the large-model outlier problem from the study can already show at small scale in some columns), and the 154 MB output embedding is quantised per row. **A diagnostic ablation (quantise only the layers; only the embedding) and a per-block scale design (one scale per 32 weights) come next; the E2 bar does not change.** A design that reaches 0.01 will be reported as E2b with the same bar and the same samples.

## Limits

One model, 96 windows from one text source, weight-only INT8, scalar loops, one thread; the speed comparison is single runs within one session on a shared virtual machine; the diagnosis is a hypothesis.

Related: [Engine plan](engine_plan.md), [Engine study](engine_study.md), [E4 result](E4_result.md), [Docs index](../../docs/INDEX.md)
