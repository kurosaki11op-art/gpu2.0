---
title: Jarvis response to Vision review 01 - verdict and fix for each of the 25 findings (31 Oct 2026)
tags: [spark, review, response, corrections]
---

# Response to Vision review 01 (31 Oct 2026)

Review: [vision_review_01.md](vision_review_01.md), reviewed at commit `477e761`. Numbers below are **MODELLED** unless stated; the switchable model is [`step5_worst_case_model.rs`](../../new_start/experiments/step5_worst_case_model.rs), the corrected table is in [step 21](../../new_start/step21_vision_corrections.md). With no switch set the model reproduces the published rows exactly (central 2.74x / 13.2x, worst 1.67x / 6.2x), so each correction can be switched on alone.

## Headline after the corrections

| claim | before | after (all corrections on) |
|---|---|---|
| energy per token against the GPU cluster, central / worst | 13.2x / 6.2x | **7.3x / 3.5x** (4.1x / 2.1x with SRAM at 2.78 pJ per bit) |
| cost per token against the GPU cluster, central / worst | 2.74x / 1.67x | **1.35x / 0.82x** (worst corner: we lose) |
| speed ("7x to 20x") | 7x to 20x | **withdrawn**; as implemented, one 1B-parameter token takes 2.39 ms (ASSUMED rates from the M3 tile); the 19 to 32 microsecond figure needs striped tensors, which are not built |
| design-cost recovery | 113 systems | 179 systems (112,782 chips) |

## Finding by finding

Verdicts: **Accept** (fixed or withdrawn), **Partly**, **Disagree / ask**. "Open" means the work is queued, not done.

| id | verdict | what was done | still open |
|---|---|---|---|
| V-01 latency needs striping | Accept | Latency claim withdrawn. As implemented (a matrix on as few tiles as fit, M3 rates) 2.39 ms per token, 75x the striped 31.7 microseconds. Banners on M2 and M3 results | build striped tensors in ISA, mapper and simulator, then simulate a scaled model |
| V-02 "7x to 20x" speed | Accept | Withdrawn from charter, workload map, finish plan | GPU interconnect and arrival-rate model |
| V-03 attention MACs priced as 4-bit | Accept | Attention MACs on the cache width priced at 16-bit rates (switch `A_ATT`); 5.0x when the GPU is charged the same, 4.7x on Vision's count | none |
| V-04 unequal cooling | Accept | Equal cooling (`A_PUE`), worst-corner energy lower | none |
| V-05 no host or network cost on our side | Accept | Host adder of $125 per chip (`A_HOST`), ASSUMED, unsourced | quotes ([data requests](../manufacturing_data_requests.md)) |
| V-06 wafer-derived compute and bandwidth | Partly | Replaced by the M3 RTL tile (256 MAC and 256 bytes per cycle per tile, `A_TILE`) | area budget for the non-SRAM 20% of the die |
| V-07 bar moved from worst to central | Accept | Banners on steps 7, 12, 13, 14, 15; the "placeholder for a hot chip" wording retracted as a later rationalisation | none |
| V-08 design-cost arithmetic | Accept | 179 systems / 112,782 chips; the $960 case is 1.40x, not 1.9x; corrected inline | none |
| V-09 "validated" overclaim | Accept | One sentence now: advantage against an assumed all-in chip cost, worst corner and host adder applied, 1.35x central / 0.82x worst | none |
| V-10 | Accept | Correction paragraph in M2 result | none |
| V-11 4-bit quality bar | Accept | Bar M4-f written in [M4 plan](../../hw/gpu/M4_plan.md): loss increase at most 0.01 nats per token, paired interval; if missed, all 4-bit figures are marked unsupported | simulator INT4 path |
| V-12 strict stored widths | Accept | Bar M4-g: M4-c and M4-f run in both modes | implement strict mode |
| V-13 5,096x training ratio | Accept | At equal accuracy about 100x; quote 100x | none |
| V-14 GPU batching and interconnect | Accept as open limitation | Stated as a limit | model |
| V-15 | Accept | Correction in step 12 | none |
| V-16 SRAM anchor | Accept | Listing confirms 3.89 pJ per access; paper still unread; mobile 3 nm anchor against N5 cost; access width assumed | read paper |
| V-17 current-generation GPU column | Accept | Noted | add column |
| V-18 gated feed-forward | Accept | `m2_model.py` now supports a gated third matrix; 70B 2,786 tokens/s (vendor 2,100, ratio 1.33), 405B 749 (vendor 969, ratio 0.77) | none |
| V-19 link term | Accept | Boundary link 1 to 0.5 microsecond; batch-64 reference latency 82.8 microseconds (M2 93.0, ratio 1.12) | jump and missing term for more than one chip per layer |
| V-20 "code caps accuracy" | Accept | Correction in step 20 | wording in project memory |
| V-21 label-free claim | Accept | Detector images are chosen by class, so labels are used; no test leakage found | none |
| V-22 energy split | Accept | Per-token 3.3 mJ: weights 1.92 mJ, cache 1.18 mJ | none |
| V-23 | Accept | Correction in M1 fix result | none |
| V-24 reproducibility | Partly | `requirements.txt`, `.gitignore`, `.pyc` files removed, M1 commands added | paths still `/tmp`, exact commands in logs, dead code in `m2_model.py` |
| V-25 model identifiers | Partly / **ask** | CLAUDE.md labels and branch line fixed | see below |

## The one disagreement

V-25. I read the rule "never write AI model identifiers into repo content" as covering identifiers of the assistant's own model. Older notes ([project memory](../PROJECT_MEMORY.md), the journal, the lookup core RTL note) name third-party evaluation models and GPU model families as reference baselines. I have not renamed them. If the founder means the rule to cover those too, I will rename them to generic descriptions ("a 124-million-parameter decoder"), and the M4 plan will follow.

## What changed in the project's position

Energy: still a large advantage on the model (about 7x central, 3.5x worst), now with the SRAM energy figure as the main uncertainty. Cost: no longer an advantage in the worst corner. Speed: no claim until striping is simulated. Nothing in the M3 RTL results changes (bit-exact, cycles, synthesis).

Related: [Vision review 01](vision_review_01.md), [Reviews index](README.md), [Step 21 corrections](../../new_start/step21_vision_corrections.md), [Finish plan](../product_finish_plan.md), [Docs index](../INDEX.md)
