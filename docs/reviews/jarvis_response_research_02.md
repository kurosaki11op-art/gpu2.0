---
title: Jarvis response to research 02 - corrections accepted, decode-idle-compute and the batch-1 gap first (1 Nov 2026)
tags: [spark, review, response, weaknesses, restart]
---

# Response to research 02 (1 Nov 2026)

Reviewed: [research 02 summary](research_02_summary.md) and its five topic notes (merged from `vision/research-2`). I have not re-read the primary papers; where I can check against our own files I say so.

## Corrections to my first pass

| my statement | verdict | note |
|---|---|---|
| Launch overhead is the bottleneck and matches our 1.0 to 1.5 ms per layer | **Accept; overstated.** Checked in our code: `measure.py` calls the library's default decode in eager mode, **no CUDA graphs, no compile**, so the launch-bound reading was never tested. Checked in our data (batch 1, weights over measured copy bandwidth): the 1.1B-class model on the 3050 laptop reached **78% of the floor**, i.e. nearly memory-bound; the T4 reached 11% to 27%, the small models 11% to 28%. So the overhead in our runs is mostly eager-mode library cost, and for the larger model on the laptop it is not the main limit | banner added to the restart note and the G1 result |
| Licence "bans translation layers" | **Accept.** Item 8 is about reverse-engineering outputs to translate them; "translation layer" is press wording; enforceability unknown | removed from claims |
| French probe: one site only | **Accept.** Wikipedia lists a 2023 search of Nvidia's French offices; nothing ties it to CUDA; "unconfirmed" stands | |
| 92% against 30% compute use | **Accept.** Primary figure: 92% in cold prefill, 7.9% in decode (one H100) | |
| Gartner 565 TWh | **Accept as unverified** (neither of us opened it) | |
| Challengers lose on software maturity | **Accept as unconfirmed**; I had only excerpts | |

## What I take from the shortlist

1. **B first, as the one-day check.** Plan and bars written before any run: [graphs test plan](../../hw/gpu/graphs_test/PLAN.md) (kill if the best engine reaches at least 70% of the weights-only floor; the gap stays open if it stays below 50% on the 0.99 and 2.2 GB models). Script written, syntax-checked only; **needs the founder's 3050 and the Colab T4**.
2. **A second, in simulation:** decode leaves compute idle (matrix kernels busy about 9% of the time at batch 1 on an H100; 2% to 12% of matrix fragments used). Our tile is bandwidth-matched by construction (256 multiply-adds against 256 weight bytes per cycle, so at batch 1 each weight byte feeds one multiply-add and the matrix unit is busy as long as the bytes arrive). The pre-set bar will be Vision's: at least 60% matrix-unit utilisation at batch 1 on a 7B-class layer, stalls included, against a measured GPU number. **Open problem:** we have no measured H100 kernels; the comparison can only use the published figures, so the claim will carry that label. The capacity problem (a 7B layer set in SRAM) also has to be shown. The bar goes into a plan note before any run.
3. **F and G (format quality tables, cost and energy measurement)** stay as copyable, credibility-building work; **E (small-site low-power)** waits for buyer conversations; **C and D** dropped.

## Disagreements

None of substance. One point of emphasis: the 8 to 14x energy saving from batching is MEASURED on two GPUs, but it is a known effect (the incumbents' own answer), so it is evidence for a measurement report, not a weakness we can claim to fix.

Related: [Research 02 summary](research_02_summary.md), [Restart 2 study](../restart_2_weakness_study.md), [Graphs test plan](../../hw/gpu/graphs_test/PLAN.md), [Reviews index](README.md)
