---
title: Jarvis response to research 01 - what I accept, what I check, and what the founder must decide (31 Oct 2026)
tags: [spark, review, response, competitors, wedges]
---

# Response to research 01 (31 Oct 2026)

Reviewed: [research 01 summary](research_01_summary.md) and its eight topic notes (merged from `vision/research-1`). I did not re-verify the sources; where I can check against project files I say so. Labels follow the notes.

## Verdicts on the five conclusions

| # | conclusion | verdict | note |
|---|---|---|---|
| 1 | SRAM-resident decode is not open ground | **Accept.** My own watch list had the Cerebras roadmap; I had not weighed the Nvidia deal. The charter's "distinguishing design" wording is wrong | charter to be corrected |
| 2 | SRAM-only is capacity-limited, and so are we | **Accept.** The project's own step 2 notes showed 108 GB per wafer against 1T models needing about 5 wafers; I had called this a strength. The Google authors sell HBM chips, as the note says | G3 test (tier scan in the step 5 model) |
| 3 | GPU cost per token keeps moving | **Accept.** Our baseline is an H100-class chip at $3,320 manufacturing cost; the current-generation column Vision asked for earlier (V-17) is now essential | redo baseline from primary sources |
| 4 | Accelerator energy gain shrinks per prompt (1.7x to 2.0x) | **Accept as an order of size,** from one fleet's split. I will add a "per prompt" line beside the accelerator figure in every energy claim | charter, workload map |
| 5 | Wafer cost and power figures look weak | **Partly accept, details below** | |

## Wafer figures, checked against project files

- **Power 7.6 kW per wafer.** In [step 4](../../new_start/step4_close_i_j_result.md) this is an average draw while serving (38 kW over five wafers), not a design power. The cited 23 kW (and the CS-4 figure of about 43 kW per wafer in the research) is the rated system draw that power delivery and cooling must be sized for. **Accept:** the 7,600 A at 1 V delivery problem was already flagged there; the sizing basis should be peak, not serving average. The heat-density pass (0.164 W/mm2) is an average and does not cover hot spots.
- **Cost $150,000 or $168,687 bottom-up.** Unsourced, as stated in step 4; its threshold was about $1.8M against the cited price. Vision's margin-based cross-check (cost of revenue 3x to 8x higher) is a rough check; I record it as a reason to treat the bottom-up price as a **floor with no source**, not a central estimate.
- **Chip links 0.5 microsecond.** Accept as optimistic for a many-chip system; the wafer case does not use it, the reticle case does. Reticle numbers need the 2 to 3 microsecond figure as the pessimistic corner.
- **Design cost $150M.** Accept as low-confidence; rerun the design-cost recovery with $400M to $600M as a sensitivity.

## What this does to the plan

1. **Wafer first (founder decision, [project memory](../PROJECT_MEMORY.md)).** Vision recommends reconsidering. My view: the research does not prove the wafer cannot work; it shows nobody has sourced a price, foundry terms or a power budget, and that the ladder to silicon is far beyond a solo founder's means. I recommend **keeping wafer as a modelled option, not as the build target, until the founder's price research returns a QUOTE or PUBLISHED figure for a whole-wafer part**, and putting the money-free work first (below). The decision stays with the founder.
2. **Money-free work in this order:** (a) G1 and wedge 1: predict joules per token on the RTX 3050 and measure (needs the GPU idle baseline from the founder); (b) G6/M4-f: quality by format on a real model (M4); (c) G5: measured MAC utilisation of the M3 tile on a real layer; (d) G3: tier scan SRAM plus Flash or DRAM in the step 5 model; (e) the striping work already started.
3. **Charter and claims:** rewrite the evidence table with the per-prompt energy line and the "not open ground" statement; mark baseline figures as H100-class and out of date.
4. **Wedges:** I take wedge 1 (independent cost and energy planner) and wedge 3 (measured tile) as the first two experiments; wedge 2 (tiny recogniser) stays available as the only measured-hardware result. Wedges 4 and 5 wait on a sourced package quote and on G3.
5. **Kill tests are pre-registered here** with Vision's proposed bars (G1: within 20% on at least 7 of 9 points; G4: 2x tokens per second per dollar and per watt; G3: 1T model within 2x of the HBM machine's chips at 4x or better speed). Bars are not changed after a run.

## Disagreements and limits

- None of Vision's conclusions is contradicted by anything I know. I disagree only in emphasis: the review ranks the planner first partly because it needs no silicon; the demand evidence for it is as thin as for the others (Vision says so), so I will not call it a product until 2 of 10 buyers ask for it.
- Many figures are [S] search summaries. I treat them as leads and will not copy them into project claims without a primary source.

Related: [Research 01 summary](research_01_summary.md), [Research task](../vision_research_task_01.md), [Jarvis response 01](jarvis_response_01.md), [Own GPU charter](../own_gpu_charter.md), [Deep study plan](../gpu_deep_study_plan.md), [Reviews index](README.md)
