---
title: Finish plan - what "the product is done" means, the failure register, and the order of work before customers (31 Oct 2026)
tags: [spark, gpu, product, plan, failures, milestones]
---

# Finish plan before customers (31 Oct 2026)

**Founder's decision, 31 Oct 2026:** finish the product and fix the failures first; only then go to customers. This note defines "done" for the product (the programmable accelerator for existing AI models, [charter](own_gpu_charter.md)), lists every open failure with its status, and fixes the order of work. Every milestone keeps its rule: bars written before the work, failures reported as misses.

## What "the product is done" means (a checklist a customer or investor can verify)

1. **It runs real, existing models** end to end with no hand mapping (a pretrained transformer decoder and a convolutional network), with accuracy equal to the original within a stated tolerance. *Status: two small trained models work on the simulator (M1); a pretrained real model is the next step (M4).*
2. **It reports cost, energy and latency per token** from counted operations with constants that are sourced or labelled. *Status: M2 done for energy; latency has a 21 to 36 microsecond range per token for a 1B model, overhead factor unresolved.*
3. **A tile exists as RTL** with cycle counts and area from synthesis, bit-exact with the simulator. *Status: not started (M3).*
4. **At least one number is measured on real hardware** (energy or cycles of a tile), replacing a model constant. *Status: not started (M5; needs a shuttle or board and money, gated).*
5. **A comparison against a real GPU on the same model** with measured joules per token (the RTX 3050 baseline exists for one model). *Status: partial.*

## Failure register (everything that failed or is open, with the plan to fix or retire it)

| # | failure or open item | what it blocks | plan |
|---|---|---|---|
| 1 | **No compiler**: the mapper is a script for two models | "no hand mapping" | **M4**: an importer for GPT-2-family decoders and sequential convolutional networks; real pretrained model; bars below |
| 2 | **Latency overhead factor** unresolved (21 to 36 microseconds per token) | latency claim | resolved only by RTL cycle counts (M3) and a measurement (M5); until then reported as a range |
| 3 | **No RTL of the tile** | silicon-level numbers | **M3** after M4 |
| 4 | **No hardware measurement** | every energy and latency constant | gated on money: first a board or an open shuttle only if M3 passes and a partner or funding exists |
| 5 | **Cost: about 1.35x centrally and 0.82x in the worst corner like for like after the review corrections (the 2x bar fails)**; packaging and host cost unsourced | the cost claim | supplier quotes ([data requests](manufacturing_data_requests.md)); not fixable by modelling |
| 6 | **Quantisation metric**: top-1 agreement is noisy | quality claims | resolved in M1 fix; later milestones use the loss increase (at most 0.01 nats per token) |
| 7 | **L's accuracy ceiling** (about 90% clothing) | none for this product | retired (the founder chose the accelerator on 31 Oct) |
| 8 | **Language cascade** failed its bars | none for this product | retired by the pre-set stop rule |
| 9 | **Training, graphics, FP64** not covered | "everything a GPU does" | out of scope by the staged charter; stated as gaps |

## Order of work

*Changed 31 Oct 2026: M3 first (the founder left the order to me after asking why M4 came first).* The largest uncertainty is the silicon-level numbers (MAC rate per tile, SRAM bandwidth, latency overhead), not software, and every claim rests on them; RTL is the first thing that can confirm or break them, so it comes before the compiler.

1. **M3 (RTL of one tile)** first, as a small slice: an INT8 matrix engine, bit-exact with the simulator, synthesised on the open 130 nm flow, with cycle counts, area and timing. Bars in [M3 plan](../hw/gpu/M3_plan.md). The numbers then recalibrate the M2 constants.
2. **M4 (compiler front end, real model)** next: a pretrained GPT-2 small through the simulator, bars in [M4 plan](../hw/gpu/M4_plan.md); it is the part a customer sees.
3. **Gate to hardware (items 4 and 5 of the failure register):** decided together with the founder once M3 results exist.
4. **Customers** after items 1 to 3 pass and the gap list is honest.

Related: [Own GPU charter](own_gpu_charter.md), [Failure and lessons notes](lessons_L_v1.md), [Manufacturing data requests](manufacturing_data_requests.md), [M2 result](../hw/gpu/M2_result.md), [Docs index](INDEX.md)
