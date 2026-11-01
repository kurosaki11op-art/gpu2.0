---
title: Research 03 summary - the pain is proven only for very large buyers, and no published expert cache reaches the 82 percent the step 22 speed bar needs (1 Nov 2026)
tags: [spark, review, research, pain, moe, expert-cache, verdict]
---

# Research 03 summary (1 Nov 2026)

Assignment: [research task 03](../vision_research_task_03.md). Notes: [Part A, pain](research_03_pain.md), [Part B, expert routing](research_03_routing.md). I worked independently and read Jarvis's [leads](../watch_radar.md) only after finishing; corrections are at the end. Labels and read depth are defined in the notes.

## The answer in brief

1. **Part B: on the published evidence, a 17 GB cache cannot reach 82%.** The cache is 1.06 times the weights one token reads. The lowest published ratio is 2.0 to 2.1, where an ordinary LRU cache gets 60% to 66%, and an **offline-optimal** cache gets 79.1% in the one layer measured. A cache's hit rate cannot fall as it grows, so at 1.06 times the optimum is at most about 79% for that model (one layer, one domain). 82% needs prediction or a changed model.
2. **Predictors reach 85% to 92%, but under a different definition,** where prefetched experts count as hits. They still move the bytes over the tier interface, and the one test on a bandwidth-bound device found prefetch gave no speedup. Step 22's tier is bandwidth-bound at batch 1.
3. **No hit rate exists for 3% to 6% of experts, at batch 8 to 64, or for a 1T-class model.** Traces exist for small models (FLAME: 64 experts, top-6, 1.3B to 10.3B total, Apache-2.0), not for anything near 1T.
4. **Part A: the pain is strong for very large buyers and unproven for small ones.** Multi-year take-or-pay contracts (CoreWeave $60.7B), a supplier whose two biggest customers are 36% of revenue, and lead times over 12 months are real. For small teams I found only list prices (a 3.1x spread for one GPU in one week) and trackers where out-of-memory is about 1% of issue titles.
5. **Our own measurements say the cheapest workaround already removes the most visible small-user pain:** a good engine took a T4 to 72% and 95% of its memory floor at batch 1 (test B).
6. **Nobody has said they would pay.** That cannot be settled by search; the only evidence that would is interviews or a pilot.

## Hit-rate table (Part B)

Cache size is shown as a share of all experts and as a multiple of the experts one token uses ("x active", DERIVED). Step 22 needs **1.06 x active (3.4% of experts) and 82%**.

| source | model | cache | x active | policy | hit rate | scope | read |
|---|---|---|---|---|---|---|---|
| 2608.18261 | 128 experts, top-8 | 13.4% | 2.1 | LRU, LFU, static | 65.9%, 60.1%, 59.2% | one layer, code, 8,000 tokens | [V] |
| same | same | 13.4% | 2.1 | **offline optimal** | **79.1%** | same | [V] |
| 2412.00099 | 8 experts, top-2 | 50% | 2.0 | LRU | 60% | all layers | [V] |
| same | 16 experts, top-2 | 50% | 4.0 | LRU | 78% | same | [V] |
| same | 64 + 2 shared, top-6 | 50% | 5.3 | LRU | 72% | same | [V] |
| same | 60 + 4 shared, top-4 | 50% | 7.5 | LRU | 65% | same | [V] |
| 2511.05814 | 8 experts, top-2 | 50% | 2.0 | LRU, LFU | recall 58.2%, 59.8% | one prompt | [V] |
| 2609.12978 | 128 to 256 experts, top-4 to 8 | 15% | 2.4 to 6.4 | LRU | 60.02% | average | [S] |
| same | same | 15% | same | trained predictor | 84.56% | average; prefetched counts as a hit | [S] |
| same | same | 25% | 4 to 10.7 | predictor | 91.72% | same | [V] |
| 2609.04238 | 128 experts, top-8 | n/a | n/a | previous-token reuse | 46.7% | not a cache test | [V] |
| same | same | n/a | n/a | trained probe, top-8 recall | 91.2% (layers 0.84 to 0.97) | prediction only | [V] |
| **step 22 condition** | 1T-class | **3.4%** | **1.06** | | **>= 82%** | batch 1 | |

## Proposed pass line (details in Part B)

Hit rate h counts every byte moved over the tier interface, prefetched or not, against the tier. At 1.06 x active, no change to the model or router, a model with at least 128 routed experts and top-6 or more, three workloads, windows of at least 512 decode tokens at batch 1: **overall h >= 0.82 and 10th-percentile layer >= 0.60.** First step: replay the offline optimum on the FLAME traces; **if it is under 0.82, stop the demand-cache route.** Cost: a few hours, no GPU.

## Verdict table (Part A, compressed)

| group | evidence of pain someone pays to remove |
|---|---|
| Frontier labs, hyperscalers | **Strong** (contracts, supply, power); not reachable |
| Regional and neoclouds | **Weak to moderate** (take-or-pay contracts; price spread; unread MD&A) |
| Small AI companies, developers | **Weak** (list prices only; OOM about 1% of titles; speed mostly closed by engine settings) |
| Universities, labs | **None found** |
| On-premises enterprises | **None to weak** (vendor-run surveys) |
| Device makers | **UNKNOWN**; not researched |

By pain: cost (weak for small buyers), supply (strong for large), capacity (weak), speed (mostly closed), power (strong at hyperscale), software setup (small share).

## Corrections

**To Jarvis's first pass and step 22:**

| statement | finding |
|---|---|
| Step 22: "h is unknown between a few percent and about 90%" | Narrower: for a **demand cache** the best published numbers at 2 x active are 60% to 66%, and the offline optimum is 79.1% in one layer. 90% appears only with predictors and a different hit definition |
| Step 22 caveat: "72% to 92% with predicted routing (ExpertFlow, MoE-Beyond)" | I could not read either paper (summary only). The predictors I could read count prefetched experts as hits, which does not reduce tier traffic |
| "A cache of about twice the active experts is a good balance" (ICLR 2026 study, cited second-hand) | "Good balance" is not a high hit rate: at 2.0 to 2.1 x active, published LRU is 60% to 66%. I could not read the study |
| Single-author blog, 87.6% to 93.0% on one model | Not read; conditions (cache size, prediction) unknown |
| "Hit rate is a function of cache share of weights" (implicit in the 3.4% figure) | Not comparable across models: the cache must be compared with the **active** experts, and finer-grained models are less cacheable at the same ratio |

**To my own earlier work:**
- [Research 02](research_02_cuda.md) said driver and version mismatches are the most common visible complaint. Counted: installation-labelled issues are 0.6% of vLLM's, out-of-memory about 1% of titles. The earlier statement came from a guide; I withdraw it as a ranking.
- [Research 01](research_01_pricing.md) called the Nvidia margin evidence for "price room". Part A adds that its demand is highly concentrated (22% and 14% for two direct customers).

## How far to trust this

- **Read verbatim:** the three cache papers' key tables (2608.18261 Table 3 and Table 5, 2412.00099 Fig. 9, 2511.05814), the traces' dataset card, Epoch AI, the vendors' price pages, and Nvidia's customer-concentration sentence.
- **Summaries only:** SeqMoE's 15% numbers and predictor recall, the Nvidia obligations figure, almost all of CoreWeave's figures, the surveys, third-party price histories.
- **Not reached:** the original offloading paper (arXiv 2312.17238, unreadable PDF), hit rates at batch 8 to 64, any 1T-class trace, Internet Archive price history, hyperscaler GPU price pages, MD&A and notes of both filings, AI-company utilisation figures.
- **Counts:** from GitHub's public search index at fetch time, not re-verified.
- **Nothing was run by me except arithmetic.**

## UNKNOWN, and who could answer

| question | who |
|---|---|
| Hit rate at 1.06 x active, batch 1, for a 128-expert-or-more model | One script over the traces, then a rented GPU run (Jarvis or the founder) |
| Hit rates at batch 8 to 64 | Same; needs multi-request traces |
| A 1T-class routing trace | Teams that serve one |
| Whether small buyers would pay more or switch | Interviews with real buyers (the founder) |
| First-party 12-month price history | A browser session with archive access |
| Hyperscaler GPU prices | Their own pricing pages in a browser |

Related: [Research task 03](../vision_research_task_03.md), [Part A](research_03_pain.md), [Part B](research_03_routing.md), [Step 22 result](../../new_start/step22_tier_result.md), [Research 02 summary](research_02_summary.md), [Reviews index](README.md)
