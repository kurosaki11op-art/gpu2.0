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

## Status

The Vision V-01 gate is **met on the scaled model in simulation**: striped weights and striped attention give 32.5 microseconds per token with an empty cache and 51.5 microseconds at 2,048 tokens of context. The latency claim stays withdrawn from charter-level statements until it is run on the full 1B shape and with network contention, and its dependence on the assumed link constants is tested (a width or hop-cost sweep is the next run). Next: the link-constant sweep, then the wafer and reticle system models under the Vision corrections.

Related: [Stripe plan](stripe_plan.md), [Response to Vision review 01](../../docs/reviews/jarvis_response_01.md), [M3 result](M3_result.md), [M2 result](M2_result.md), [Hardware index](../HARDWARE_INDEX.md), [Docs index](../../docs/INDEX.md)
