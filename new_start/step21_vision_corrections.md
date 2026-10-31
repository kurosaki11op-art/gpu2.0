---
title: Corrections after Vision review 01 - energy, cost and speed claims restated (31 Oct 2026, MODELLED)
tags: [spark, new-start, correction, review, energy, cost, speed, model]
---

# Corrections after Vision review 01 (31 Oct 2026)

**MODELLED.** The independent review ([Vision review 01](../docs/reviews/vision_review_01.md), 25 findings) found errors and over-claims in the energy, speed and cost results. I reproduced the five largest by patching the model ([`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs), switches `V2`, `A_ATT`, `A_PUE`, `A_HOST`, `A_TILE`; with none set the model reproduces every earlier published row), [log](experiments/step21_vision_corrections.log). Point-by-point answers: [response](../docs/reviews/jarvis_response_01.md). **This note supersedes the headline numbers of steps 5 to 15 where it differs.**

## What was wrong (all accepted, all reproduced)

1. **Attention multiply-adds were priced as 4-bit operations** (0.12 pJ) although they run on the 16-bit cache (1.5 pJ in the model's own table) (V-03). Now priced at 1.5 pJ on both machines.
2. **Unequal cooling factor** (1.4 for the GPU hall, 1.15 for ours although our chip is air-cooled by the note's own argument) (V-04). Now one factor (1.3) for both.
3. **No host, network or rack cost on our side**, while the GPU is charged 1.5 times its price for them (V-05). Now +$125 per chip (one $2,000 host per 16 chips, **ASSUMED**).
4. **Compute and SRAM bandwidth per chip came from a wafer with a different area split** (V-06, V-16). Now taken from the M3 RTL tile (256 multiply-adds and 256 bytes per cycle per 4 MiB tile at 1 GHz); this also removes the inconsistency between the bank design and the assumed 2,000 bytes per cycle.
5. **"350 W" for the GPU is not total board power:** the model adds HBM and multiply-add energy on top, so the modelled board draws **538 W (central) and 287 W (the "100 W" corner)**; the label is corrected, not the number (V-04).

## Corrected results (1T mixture-of-experts, 4-bit, SRAM 0.55 pJ/bit, 420 mm2 per GB, chip at $480 before the host adder, GPU at its manufacturing cost $3,320; cost advantage = GPU cost per token / ours)

| corrections applied | central: cost, energy | worst corner: cost, energy |
|---|---|---|
| none (as published) | 2.74x, 13.2x | 1.67x, 6.2x |
| attention at 1.5 pJ only | 2.71x, 10.0x | 1.66x, **5.0x** |
| one cooling factor only | 2.68x, 10.8x | 1.64x, 5.1x |
| host and network adder only | 2.19x, 13.2x | 1.33x, 6.2x |
| M3 tile rates only | 1.72x, 11.3x | 1.04x, 5.1x |
| **all four** | **1.35x, 7.3x** | **0.82x, 3.5x** |
| all four, host adder $400 | 0.94x, 7.3x | 0.57x, 3.5x |

**Corrected statements:**
- **Energy:** per token about **7x below a GPU cluster centrally and 3.5x in the worst corner** (was 13x and 6x); the pre-set 5x floor in the worst corner **does not hold**. Row J is no longer "closed, passes".
- **Cost, like for like:** about **1.35x cheaper centrally and 0.82x (more expensive) in the worst corner** (was 2.74x and 1.67x); the 2x bar fails in both corners. The central 2.74x "bar met" of step 15 should not be quoted: it rested on the optimistic inputs above, on a bar moved from the worst corner to the central one, and on an unsourced $150. **The worst-corner bar W1 has failed since step 5 and still fails.**
- **Cost, buyer's price view (GPU at its selling price, all four corrections, host adder included):** at our price of $2,660 per chip (2x markup, the step 13 case) the buyer's advantage is **1.87x centrally and 0.75x in the worst corner** (was 3.16x and, with the GPU at $15,000, 1.26x); at $3,990 it is 1.27x and 0.51x. The "sell 33% below Nvidia at a 76% margin" arithmetic of step 14 needs the same correction and should not be quoted. The design-cost recovery figure was wrong (179 systems, not 113); the $960 case of step 15 gives 1.4x, not 1.9x.
- **Speed:** the **"7x to 20x per-user speed" is withdrawn** (V-02): the 20x end is the abandoned wafer option; the reticle-chip option gives 6.5x to 9.8x only because the GPU cluster was sized to a 30 tokens per second floor, and GPU-to-GPU communication, the real limit, is not modelled. **Speed advantage: unquantified.**
- **Latency of a 1B model (V-01):** the 19 to 32 microseconds per token figure assumes every matrix is striped over all tiles of the chip, which the instruction set and simulator cannot express (a weight tensor lives on one tile; the simulator asserts it). With each matrix on as few tiles as it needs (a 2.1 MB matrix on one tile, an 8.4 MB feed-forward matrix on two) and the M3 tile rate of 256 multiply-adds per cycle, the same model gives **2.39 milliseconds per token (about 420 tokens per second), 75 times slower** (arithmetic reproduced; the review's 1.18 ms used the older 368 rate). **Quote "about 2.4 ms as implemented; 19 to 32 microseconds only with an unbuilt striped mapping".** Striping (split tensors in the instruction set and mapper, broadcast and reduction simulated) is the next piece of work on this point.

## What survives

A functional simulator with an exact INT8 tile in RTL; an energy advantage that is real in direction (about 3.5x to 7x modelled, with the corrections) but not a 5x-to-13x claim; a cost position near parity at best, with the unsourced packaging and host figures deciding it; and the list of numbers that only hardware, supplier quotes or a data-centre GPU measurement can settle.

Related: [Vision review 01](../docs/reviews/vision_review_01.md), [Response to review 01](../docs/reviews/jarvis_response_01.md), [Step 15 packaged cost](step15_packaged_cost_result.md), [Step 12 final disposition](step12_close_i_j_final.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
