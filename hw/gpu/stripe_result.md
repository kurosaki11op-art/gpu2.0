---
title: Striping result - one token of a scaled decoder in 36.5 microseconds when every matrix is split over 16 tiles (31 Oct 2026, SIMULATED with ASSUMED link constants)
tags: [spark, gpu, striping, latency, result, vision-v01]
---

# Striping result (31 Oct 2026)

**SIMULATED** (functional simulator with a cycle model; no hardware). Plan and bars were written before the code: [stripe plan](stripe_plan.md). Code: striping option `GPU_STRIPE=S` in [`gpu_sim.rs`](sim/gpu_sim.rs) (each weight used by `MM` is split by output columns over S tiles; stripe i of logical tile h sits on tile h + i x logical tiles; the activation is broadcast to the stripe tiles and the outputs are gathered on the home tile), decoder generator [`gen_decoder.py`](stripe/gen_decoder.py), independent counter [`torch_count.py`](stripe/torch_count.py), driver [`run_stripe_checks.sh`](stripe/run_stripe_checks.sh), log [`stripe_checks.log`](stripe/results/stripe_checks.log). Striping is a mapping option in the simulator; the instruction text (ISA) is unchanged, and convolution weights are not striped.

## Bars and results

| bar | result |
|---|---|
| **S-a** striped outputs equal unstriped bit for bit at widths 1, 4, 16 | **PASS.** Output files are byte-identical for the transformer (prefill and decode) and the CNN, in fp32, INT8-weights and W8A8 modes, at all three widths (9 model-mode pairs, one checksum each) |
| **S-b** MACs and SRAM bytes unchanged (within 0.1%); mesh bytes larger | **PASS.** MACs 104,890,368, SRAM read 3,211,520 and write 2,981,888 bytes at every width. Mesh byte-hops grow from 458,752 (width 1) to 5,332,992 (width 4, 11.6x) and 58,810,368 (width 16, 128x) |
| **S-c** scaled decoder within 3x of the 31.7 microsecond estimate (limit 95 microseconds) | **PASS on the scaled model, with caveats below.** 16 layers, d 512, ff 2,048, 4 heads, vocabulary 8,000 (58.7 million weights, per-tile work comparable with the 1B shape at width 16); M3 tile rates (256 MAC and 256 bytes per cycle), 1 GHz. Per token, averaged over 64 decode steps: width 1 **222.5 us**, width 8 **47.5 us**, width 16 **36.5 us** (first token, empty cache: 218.5, 43.5, 32.5 us) |
| **S-d** independent MAC count within 1% | **PASS, exact.** PyTorch hooks: 54,444,032 MACs at the first token and 55,476,224 at token 64; the simulator's per-token average over 64 steps, 54,960,128, equals the hook average to the unit. Note: this checks operation counts, not bytes or cycles |

## What the result means, and what it does not

- **The 31.7 microsecond estimate was not wrong by orders of magnitude.** With striping the simulated cost is 32 to 37 microseconds per token on a model with comparable work per tile, against 222 microseconds with no striping (6x) on the same model.
- **Compute is about 1% of the time.** The 54 million MACs spread over 288 tiles are only about 740 cycles; the rest of the 36,500 cycles is broadcast and gather over the mesh (link bandwidth 64 bytes per cycle, 2 cycles per hop, **ASSUMED**), hops, the unstriped small operations (layer norm, residual adds, attention on one tile) and the embedding path. **The latency is a function of the assumed network constants**, not of the tile; a different link width moves it directly. This is the number to test next on real mesh hardware data.
- **Attention is not striped.** The cache lives on one tile and attention reads it there. At 64 tokens of context that costs little. At the reference context of 2,048 tokens the scaled model needs 2 x 512 x 2,048 = 2.1 million MACs per layer on one tile (8,192 cycles, 131 microseconds over 16 layers, MODELLED arithmetic not simulated), and a 2,048-token 16-bit cache of this width is 4 MB per layer for the keys and values together, the whole tile. So **the 3x bar is not met at the reference context until attention and the cache are also split by head across tiles**; that is not built.
- **Scale:** the full 1B shape (4x wider) was not simulated (the weight file does not fit the free disk); equal per-tile work was assumed to carry over, but the mesh terms (distances, activation size) change with width, so the scaled result is a stand-in, not the 1B figure.
- **Wafer versus chips:** the mesh constants here are the on-wafer kind (cheap hops). Chip crossings would cost more; the reticle case needs its own run.
- **Batch 1 only, one request, no queueing, no host.**

## Update: attention and cache striped (31 Oct 2026, SIMULATED)

Option `GPU_STRIPE_ATTN=1`: the key and value cache is split by head and by context chunk over the stripe tiles; each tile reads its share and does 1/S of the multiply-adds; the query is broadcast and one partial (head dimension plus the softmax maximum and sum) per tile is merged on the home tile. Outputs are unchanged (the arithmetic is the same; only the cycle model changes). Measured directly on the scaled decoder at width 16, as the marginal cost of the 64 decode steps ending at 2,048 tokens ([log](stripe/results/attention_2048.log)):

| attention | per-token cost near 2,016 tokens of context |
|---|---|
| on one tile (unstriped) | **290.5 us** (bar of 95 us missed by 3x) |
| striped over 16 tiles | **51.5 us** (**S-c passes at the reference context**, bar 95 us) |

The first prediction above (131 microseconds extra for one-tile attention, MODELLED arithmetic) was too low: the simulation gives about 258 microseconds extra, because the cache bytes read per token also bind. Limits: tile size was set to 16 MB (the embedding and position tables on tile 0 need it); the cache is assumed to be spread evenly with no imbalance; the merge and broadcast use the same ASSUMED link constants; no contention; no queueing; scaled model, not the full 1B shape.

## Sweep of the assumed network constants (bar S-e, 31 Oct 2026, SIMULATED; plan and bar committed before the run)

Per-token cost near 480 tokens of context, microseconds, scaled decoder, width 16, striped attention ([log](stripe/results/sweep_network.log), script [`sweep_network.sh`](stripe/sweep_network.sh)):

| link bytes per cycle \ cycles per hop | 2 | 16 | 200 | 2,000 |
|---|---|---|---|---|
| 16 | 62.1 | 139.0 | 1,150 | 11,045 |
| 32 | 46.6 | 123.6 | 1,135 | 11,030 |
| 64 (assumed so far) | 38.9 | 115.8 | 1,127 | 11,022 |
| 128 | 35.0 | 112.0 | 1,123 | 11,018 |
| 256 | 33.1 | 110.0 | 1,122 | 11,016 |

- **S-e FAILS as pre-registered.** The bar was at most 95 microseconds for link bandwidth of at least 32 bytes per cycle with hop cost up to 16 cycles. At 2 cycles per hop it holds for every link width (33 to 62 microseconds, 62 at the narrowest 16); at 16 cycles per hop it fails at every link width (110 to 139 microseconds).
- **The hop cost is what matters, not the link width.** Going from 16 to 256 bytes per cycle changes the result by less than 2x; going from 2 to 16 cycles per hop triples it, and the chip-crossing corner (200 and 2,000 cycles, i.e. 0.2 to 2 microseconds per hop at 1 GHz) gives about 1.1 and 11 **milliseconds** per token.
- **Why:** every striped matrix and every attention pays one broadcast and one gather, each costing a hop cost times the farthest stripe tile's distance. In this mapping the 16 stripe tiles of a layer sit on tile numbers home + i x 18 on a 17 x 17 mesh, so the farthest is up to about 30 hops away; with 16 layers and about 8 striped operations per layer, that is thousands of serial hops per token. The fixed per-token chain of dependent hops, not the compute, sets the latency.
- **What it means:** the 33 to 51 microsecond results hold only if a hop costs about 2 cycles (2 nanoseconds at 1 GHz) with this placement. On-wafer wires might do that; chip-to-chip links cannot (Vision research: 2 to 3 microseconds per crossing), so **striping every matrix across chips is not viable** in this form: at 200 cycles per hop it is already more than 10x over the bar's limit, which was the pre-set trigger for rethinking the reticle mapping.
- **Not yet tried (next experiment, new bar needed):** compact placement (the 16 stripe tiles of a layer in a 4 x 4 block, farthest tile about 6 hops), tree broadcast, and overlapping the broadcast with compute. Compact placement alone should cut the serial hop count by about 5x; that is a prediction, not a result.

## Compact placement (bar S-f, 31 Oct 2026, SIMULATED; plan and bar committed before the run)

The 16 stripe tiles of a layer now sit in a 4 x 4 block with the home tile at its corner (`GPU_COMPACT=1`). Same decoder, striped attention, width 16, per-token cost in microseconds near 480 tokens of context ([log](stripe/results/sweep_network_compact.log)); the spread placement of S-e in brackets:

| link bytes per cycle \ cycles per hop | 2 | 16 | 200 | 2,000 |
|---|---|---|---|---|
| 16 | 56.3 (62.1) | 93.0 (139.0) | 576 (1,150) | 5,299 (11,045) |
| 32 | 40.9 (46.6) | 77.6 (123.6) | 560 (1,135) | 5,284 (11,030) |
| 64 | 33.1 (38.9) | **69.9** (115.8) | 553 (1,127) | 5,276 (11,022) |
| 128 | 29.3 (35.0) | 66.0 (112.0) | 549 (1,123) | 5,272 (11,018) |
| 256 | 27.3 (33.1) | 64.1 (110.0) | 547 (1,122) | 5,270 (11,016) |

- **S-f PASSES:** at 16 cycles per hop and 64 bytes per cycle the cost is 69.9 microseconds (bar 95); it passes at every link width from 16 bytes per cycle up (64 to 93 microseconds). Outputs are byte-identical to the unstriped run at widths 1, 4 and 16 for the prefill and decode models ([log](stripe/results/compact_md5.log)).
- **The prediction was about right:** about 5x fewer serial hops was predicted; the hop-dependent part of the cost fell about 2x at 16 cycles per hop (from 116 to 70 microseconds, against the 33 microsecond floor), less than hoped, because the farthest stripe tile is still 6 hops away and each operation still pays a broadcast and a gather.
- **Chip-to-chip crossings are still not viable:** at 200 cycles per hop (0.2 microsecond) the cost is about 550 microseconds, 5x over the bar, and about 5.3 milliseconds at 2,000 cycles (the 2 to 3 microsecond crossing reported for shipping systems). Reducing the number of serial hops further (tree broadcast, overlapping with compute, a different split such as pipeline stages across chips) is untried; the plain striping mapping does not work across chips, which matters for the reticle design.
- **Summary of the speed claim, all SIMULATED, scaled decoder, 480 tokens of context:** 33 to 70 microseconds per token if a hop costs 2 to 16 cycles at 1 GHz with compact placement; about 550 microseconds at 0.2 microsecond per hop. It rests on assumed hop cost and has not been checked against a real mesh.

## Status

The Vision V-01 gate is **met on the scaled model in simulation**: striped weights and striped attention give 32.5 microseconds per token with an empty cache and 51.5 microseconds at 2,048 tokens of context. The latency claim stays withdrawn from charter-level statements until it is run on the full 1B shape and with network contention, and its dependence on the assumed link constants is tested (a width or hop-cost sweep is the next run). Next: the link-constant sweep, then the wafer and reticle system models under the Vision corrections.

Related: [Stripe plan](stripe_plan.md), [Response to Vision review 01](../../docs/reviews/jarvis_response_01.md), [M3 result](M3_result.md), [M2 result](M2_result.md), [Hardware index](../HARDWARE_INDEX.md), [Docs index](../../docs/INDEX.md)
