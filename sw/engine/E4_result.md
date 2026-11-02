---
title: Engine milestone E4 - key-value cache decoding gives bit-identical logits and nearly flat per-token cost (2 Nov 2026, MEASURED)
tags: [spark, engine, software, result, e4, kv-cache]
---

# Engine E4 result (2 Nov 2026)

**MEASURED** on the cloud container's CPU, same model and prompts as [E1](E1_result.md). Plan and bars (written first): [engine plan](engine_plan.md). Code: `step` and the `decode` mode in [`engine.rs`](engine.rs).

## Result

- **Same outputs:** decoding one token at a time with the key-value cache, over the 16 E1 prompts (173 positions), gives logits that differ from the full-recompute pass by a **maximum of 0.0** (bit-identical: the arithmetic is done in the same order). Bar: within the E1 bar (1e-3, full greedy agreement). **PASS.**
- **Per-token cost against position** (one 512-token sequence, mean time per token over each 64-position window, single run): 68.2, 67.7, 72.3, 79.6, 78.5, 75.2, 81.0, 78.3 ms for positions 0 to 511. The slowest window is **19.6% above the fastest** (81.0 against 67.7 ms). Bar: within 20%. **PASS, with a thin margin** (single run, no repeat; timer noise on a shared container is of that order).

## Reading and limits

- Per-token cost is nearly flat because at this size (6 layers, 768 wide) the per-token matrix work and the 50,257-way output layer dominate; attention over the cache adds little up to 512 positions. For longer contexts or wider models the cache cost will grow, as expected.
- **Speed is poor and is not a claim:** about 68 ms per token (about 15 tokens per second) for an 82-million-parameter model on one thread in fp32. A mature engine will be many times faster on the same CPU; E3 (bar 0.8x of llama.cpp) will **fail unless the code gets threads, blocked matrix multiplies and INT8**. The plan's stop rule (below 0.5x on 30 Nov) stays in force.
- One model; one run of the timing; no repeat; the check of equality was against our own full pass, which E1 matched to PyTorch within 3.8e-4.

## Next

E2 (INT8 weights, bar 0.01 nats per token and 0.3x memory), then threads and blocking for E3.

Related: [Engine plan](engine_plan.md), [E1 result](E1_result.md), [Docs index](../../docs/INDEX.md)
