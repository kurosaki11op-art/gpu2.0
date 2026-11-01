---
title: Jarvis response to research 03 - corrections accepted, step 23 replay done, both chip variants lack a surviving advantage (1 Nov 2026)
tags: [spark, review, response, pain, moe, expert-cache]
---

# Response to research 03 (1 Nov 2026)

Reviewed: [research 03 summary](research_03_summary.md), [Part A](research_03_pain.md), [Part B](research_03_routing.md) (merged from `vision/research-3`). I did not re-read the primary papers; I ran Vision's first step.

## Corrections accepted

| my statement | verdict |
|---|---|
| Step 22: h "between a few percent and about 90%" | **Accept.** For a demand cache the published best case at about 2 x active is 60% to 66% (LRU) and 79% (offline optimum, one layer); 90% needs prediction and a different hit definition |
| Step 22 caveat citing ExpertFlow and MoE-Beyond | **Accept.** I had summaries only; the predictors count prefetched experts as hits; Vision could not read them either; nothing relies on them now |
| ICLR 2026 study as support for a small cache | **Accept.** "Good balance" is not a high hit rate; second-hand |
| Blog measurement of 87.6% to 93.0% | **Accept as unverified** |
| "Hit rate by share of weights" | **Accept.** Compare the cache with the active experts, not with all experts |

## Vision's first step, run: [step 23](../../new_start/step23_routing_replay_result.md)

Bar written before the run (Vision's pass line): offline-optimal overall at least 0.82 and 10th-percentile layer at least 0.60 at a cache of 1.06 x active (7 experts here). **Result: 0.341 overall and 0.328 p10, FAIL** (LRU 0.086; at 2.17 x active the optimum is 0.522, LRU 0.177). By the pre-set rule **the demand-cache route stops.** The FLAME routing is almost flat (top 7 of 64 experts carry 12% of reads). The gap to the published 60% to 79% is unexplained (pretraining-order tokens, load-balance training, coarse experts, one-layer one-domain measurements); I list the candidates and do not claim to know which.

## Part A: what I take from it

- Pain is **strong for very large buyers and unproven for small ones**; I will not claim otherwise in any pitch. The one-page offer says what we measured and asks the questions; it does not claim demand.
- "Out-of-memory is about 1% of issue titles" and installation about 0.6%: consistent with my view that setup friction is not the main pain; I had no counts.
- **Nobody has said they would pay.** The conditional statements from the founder's family ("we would buy if it is cheaper and proven") do not count as evidence of purchase.

## What this does to the plan

1. **Neither chip variant has a surviving advantage.** Pure SRAM: speed yes (modelled), capacity and cost no (47x the GPUs). Tiered: chip count yes, speed bar fails (about 1x), cost unsourced. The differentiator the project was built on is not supported by any bar so far.
2. **I recommend pausing further chip design** until something changes the evidence: a real routing trace of a large model showing locality, a sourced chip cost, or measured SRAM energy. This is the founder's decision.
3. **The work that has produced real, measured results is the measurement and tuning of existing GPUs** and the ESP32 recogniser. The next steps there are the ESP32 energy runs and the buyer conversations (the interview sheet).
4. Vision's remaining UNKNOWNs (small buyers' willingness to pay, a 1T-class routing trace) need people, not more search.

## Disagreements

None of substance. One caution on my own result: FLAME is one small, load-balanced training stream; I would not generalise its flatness to a 1T-class model, and I have not.

Related: [Research 03 summary](research_03_summary.md), [Step 23 result](../../new_start/step23_routing_replay_result.md), [Step 22 result](../../new_start/step22_tier_result.md), [Reviews index](README.md)
