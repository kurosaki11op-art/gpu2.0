---
title: Striping plan - split every weight matrix across many tiles so one token is fast (31 Oct 2026, plan and bars written before any work)
tags: [spark, gpu, striping, latency, plan, vision-v01]
---

# Striping plan (31 Oct 2026)

Why: [Vision review 01, V-01](../../docs/reviews/vision_review_01.md). The 19 to 32 microsecond token latency assumes every matrix is split over all tiles. The simulator today puts a whole matrix on one tile (`W name tile`, `MM ... tile`); as implemented a 1B-parameter token takes 2.39 ms (MODELLED, [response](../../docs/reviews/jarvis_response_01.md)). No latency figure is called a result until the bars below are met.

## Design (what will be built)

- **ISA:** `W` accepts a stripe: `W name tile0..tileN` splits the output columns of the matrix evenly over the listed tiles; `MM` on a striped weight broadcasts the activation to every stripe tile and concatenates the outputs (a gather).
- **Simulator:** each stripe tile runs its own columns; counters are per tile; time per `MM` = broadcast time + the slowest stripe + gather time, on the mesh with the existing hop and link-bandwidth constants (ASSUMED, M3 tile rate 256 MAC per cycle). Row-split (reduction over k) is a second variant with a partial-sum add.
- **Mapper:** assigns stripes so that each tile holds an equal share of every matrix and the cache, and checks SRAM overflow.

## Bars (written before the work)

- **S-a (correctness):** striped outputs equal unstriped outputs bit for bit in INT8 mode (all M1 checks re-run) at stripe widths 1, 4, 16.
- **S-b (counts):** total MACs and SRAM bytes unchanged by striping (within 0.1%); mesh bytes reported separately and larger than unstriped.
- **S-c (latency):** simulate a scaled decoder (the 1B-class shape if memory permits, else a 1/16 scale with the stripe width scaled the same) and report cycles per token including broadcast and gather. Pre-set pass: within 3x of the 31.7 microsecond striped estimate. A miss is reported as a miss and the estimate is replaced by the simulated figure.
- **S-d (independence):** a second count of MACs and bytes from PyTorch hooks on the exported model agrees with the simulator within 1%.

## Not covered

Hardware timing of the mesh, congestion, and arrival rates (batching) are ASSUMED/unmodelled; the result will say so.

## Added 31 Oct 2026, before the run: sweep of the assumed network constants (S-e)

The striping result depends on two ASSUMED constants: link bandwidth between tiles (64 bytes per cycle) and cycles per hop (2). Question: how much of the 36 to 51 microsecond result survives worse values, including a chip-to-chip crossing (Vision research: 2 to 3 microseconds per crossing on a shipping system, 2,000 to 3,000 cycles at 1 GHz).

- Grid: link bandwidth 16, 32, 64, 128, 256 bytes per cycle; hop cost 2, 16, 200, 2,000 cycles. Scaled decoder of the S-c test, stripe width 16, striped attention on, M3 tile rates, 1 GHz.
- Measured quantity: marginal cost per token near 480 tokens of context (difference of the 448-step and 512-step totals, divided by 64). Cost at 2,048 tokens was measured only for the reference cell (the earlier run); the sweep uses 480 tokens to keep it feasible.
- **S-e bar:** per-token cost at most **95 microseconds** (3x the 31.7 microsecond estimate) for link bandwidth of at least 32 bytes per cycle with hop cost up to 16 cycles (on-wafer style). Reported without a bar: the chip-crossing corner (200 to 2,000 cycles); if it exceeds 95 microseconds by more than 10x there, striping every matrix across chips is not viable and the reticle design needs a different mapping.
- Results are reported for all 20 cells, whichever way they go.

Related: [Response to Vision review 01](../../docs/reviews/jarvis_response_01.md), [M3 result](M3_result.md), [M2 result](M2_result.md), [Finish plan](../../docs/product_finish_plan.md), [Docs index](../../docs/INDEX.md)
