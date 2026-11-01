---
title: Research 03 Part B - expert routing and a small on-chip cache - published hit rates, traces to replay, and a pass line for the step 22 speed bar (1 Nov 2026)
tags: [spark, review, research, moe, expert-cache, routing, hit-rate]
---

# Research 03, Part B: expert routing and a small cache

Labels: MEASURED, SIMULATED (a cache replayed over recorded routing), PUBLISHED, VENDOR CLAIM, DERIVED (my arithmetic), UNKNOWN. Read depth: **[V]** verbatim text read; **[S]** only a summary (search result or the fetch tool's own summary of a truncated page). Papers are named by arXiv number and described by size. Accessed 1 Nov 2026. Reference: [step 22](../../new_start/step22_tier_result.md).

## The step 22 condition, in the papers' units

Step 22 needs about 82% of the bytes read per token to come from a 17 GB SRAM cache (1.6 TB/s tier; 91% at 0.8 TB/s). One token reads about 16 GB of a 500 GB model. **So the cache is 17/16 = 1.06 times the weights one token reads, i.e. about one token's worth of active experts per layer, and 3.4% of all experts.** Papers report cache size as a share of all experts, which hides how the models differ in how many experts a token uses. I therefore convert every result to **cache size divided by active experts** ("x active"), which is the number comparable with step 22's 1.06. (DERIVED; the conversion assumes equal-size experts.)

## Published hit rates

| source and model | cache | x active | policy | hit rate | scope | how measured | read |
|---|---|---|---|---|---|---|---|
| 2608.18261: 30B-total/3B-active, 48 layers, 128 experts, top-8 | 13.4% | 2.1 | LRU / LFU / static pin / **offline optimal (Belady)** | **65.9% / 60.1% / 59.2% / 79.1%** | **one layer (24), code text, 8,000 tokens** | SIMULATED replay of router traces; batch size UNKNOWN | [V] Table 3 |
| 2412.00099: 8 experts, top-2 (13B active) | 50% (4 of 8) | 2.0 | LRU | 60% | all layers, validation text | measured miss rates, hit = 1 - miss; batch 1 generation | [V] Fig. 9 |
| same: 16 experts, top-2 (6.6B active) | 50% | 4.0 | LRU | 78% | same | same | [V] |
| same: 64 routed + 2 shared, top-6 (2.8B active) | 50% | 5.3 | LRU | 72% | same | same | [V] |
| same: 60 routed + 4 shared, top-4 (2.7B active) | 50% | 7.5 | LRU | 65% | same | same | [V] |
| 2511.05814: 8 experts, top-2 | 50% | 2.0 | LRU / LFU | recall 58.2% / 59.8% | one 50-word prompt; batch 1 | measured; no percent-of-experts sweep | [V] |
| same, speculative loading | n/a | n/a | predictor | precision and recall 84.6% | **one prompt** | its speed was not measured | [V] |
| 2609.12978 (four models, 128 to 256 experts, top-4 to top-8) | 15% | 2.4 to 6.4 | LRU / trained predictor (SeqMoE) | 60.02% / **84.56%** (average) | averages over models; per-layer not reported | measured on consumer GPUs; mostly batch 1 | [S] |
| same | 25% | 4 to 10.7 | strongest baseline / SeqMoE | 74.24% / **91.72%** | same | same | [V] abstract |
| same | 45% | 7 to 19 | baseline / SeqMoE | 88.50% / 96.97% | same | same | [V] abstract |
| 2609.04238: 30B-total/3B-active, 128 experts, top-8 | no cache sweep | n/a | previous-token reuse / trained probe | **46.7%** top-8 overlap / **91.2%** top-8 recall (per layer 0.84 to 0.97) | per layer given as a range | measured probes; a different question: prediction, not cache | [V] |

**What no source gives:** a hit rate at **1.06 x active** (3% to 6% of experts) for any model. The lowest ratio in anything I read is 2.0 to 2.1.

The 2609.12978 hit counts a needed expert as a hit if it was **resident before on-demand loading**, which includes experts the predictor fetched in advance. Those prefetched bytes still cross the tier interface (see the pass line below). The two readings give very different answers to the question step 22 asks.

Results I could not read and that Jarvis's first pass cites: ExpertFlow (91.96% with a predictor, arXiv 2410.17954), MoE-Beyond (17% to 72% with 10% of experts, 2508.17137), an ICLR 2026 poster on routing consistency across 20 models, a single-author blog (87.6% to 93.0%). I saw them only as search summaries: **UNKNOWN**.

## What the numbers say (DERIVED)

1. **Demand caching of fine-grained models lands at 60% to 72% for a cache of 2 to 7.5 times the active experts**, and **it is not monotone in that ratio across models**: 78% at 4x for an 8-or-16-expert model, 65% at 7.5x for a 60-expert model. Finer-grained experts are less cacheable at the same ratio.
2. **The offline optimal policy reaches only 79.1% at 2.1 x active** in the one layer measured. An optimal demand cache's hit rate cannot fall as the cache grows, so **at 1.06 x active it is at most about 79% for that model, layer and domain** (assuming the one-layer, one-domain result generalises, which is unproven). The cache-conditional paper makes the same point: lossless caches "cannot surpass the theoretical cache hit rate bound set by the model's own routing". **So 82% cannot be met by a plain cache on this evidence.** It needs prediction or a change to the model.
3. **Changing the model changes the numbers, and also the model.** Training routers for locality raised LRU hits at 25% of experts from 0.49 to 0.79, at a 2.1% to 3.1% perplexity cost, which failed the author's own pre-registered quality gate (2608.18261, 137M-parameter models; [V] Table 5). The cache-conditional routing (2412.00099) reached 79% to 93% for a 0.1% to 3% perplexity change. Either way the chip would no longer run the original model's answers, which the charter requires.
4. **Prediction helps, but hides latency, not bandwidth.** The one paper that tested prefetch on a bandwidth-bound device found it did not speed things up (0.19 to 0.12 tokens/s for previous-token prefetch; 0.12 to 0.13 for an oracle): prefetch "changes when bytes are read, not how many" (2609.04238 section 5.10 [V]). Step 22's tier is exactly bandwidth-bound at batch 1.
5. **Always-active parts count as hits.** Attention and shared experts, if held in SRAM, are guaranteed hits. If they are a fraction s of the bytes read, the cache needs only (0.82 - s) / (1 - s) over the routed experts. With **an illustrative s of 12% (ASSUMED; the share for a 1T-class model is UNKNOWN)** that is 79%, so it helps by about three points. Check whether step 22's 3.4% already counts them.

## Batch size

No source I read reports **hit rates** at batch 8 to 64. What exists:
- One measured serving test (2608.18261, 235B-total model paged from SSD): throughput tracked a model at batch 1 and 8, then collapsed to 0.087 tokens/s at batch 32 against 0.35 predicted, from cache thrash [V Table 2, per its summary].
- Jarvis's formula: the share of experts touched in a step is 1 - (1 - f)^b with f = 3.2%. That gives about 23% at b = 8 and about 88% at b = 64 (DERIVED, assuming independent routing, so an upper bound; correlated routing lowers it). Hit rates at those batches are **UNKNOWN**.

## Routing traces you can replay

| source | content | licence | limits |
|---|---|---|---|
| [CMU-FLAME/FLAME-MoE-Traces](https://huggingface.co/datasets/CMU-FLAME/FLAME-MoE-Traces) (dataset card read [V]) | Three models: 1.3B, 3.8B, 10.3B total; **64 routed experts, top-6, 2 shared**; 8, 11 and 17 MoE layers; 11 checkpoints each; 52,428,800 tokens per capture; Parquet with token id and per-layer expert indices and scores | Apache-2.0 | **Recorded during pretraining,** so token order and batching may not look like single-request decode (UNKNOWN); the corpus is not named; no whole-dataset download command; fewer experts than a 1T-class model |
| OLMoE (arXiv 2409.02060) | 6.9B total/1.3B active, 64 experts, top-8: **weights and code are open; routing traces are not released** | open | You would generate traces yourself; its own analysis gives no per-layer share for the top experts, but says routing saturates early and some experts specialise by domain (for one scientific-paper domain, the first expert in layer 0 is almost 100% specialised) [V] |

**Smallest representative model:** none found. A 1T-class model has 256 or more routed experts per layer with top-8 and a 61-layer stack. The closest open models are 128-expert, top-8 models around 30B total, which at 4 bits need about 17 GB of memory and a rented 24 GB card. **Whether a 30B-class model's routing is representative of a 1T-class one is UNKNOWN.** Nobody who runs a 1T model has published a trace that I could find.

## Pass-line proposal

Step 22 asks for h >= 0.82 (at 1.6 TB/s tier) and 0.91 (at 0.8 TB/s). I propose pre-registering these conditions:

1. **Unit:** h = bytes read from SRAM / total bytes read per token, where **any byte moved over the tier interface counts against the tier**, including prefetched bytes that turn out unused. (This is the only definition under which "82%" corresponds to the tier-bandwidth saving step 22 assumes.)
2. **Cache size** in the same unit as step 22: 1.06 x active experts per layer, plus attention and shared experts resident.
3. **Model and workload:** at least one open model with at least 128 routed experts per layer and top-k of 6 or more, **no change to the model or router**, three workloads (chat, code, long context of 4,096 tokens or more), windows of at least 512 consecutive decode tokens at batch 1, at least 3,000 tokens in total per workload.
4. **Report** the overall value and the **10th-percentile layer** (a slow layer stalls the token). Proposed bars: overall >= 0.82 and 10th percentile >= 0.60.
5. **Step 0, an upper bound:** replay the offline optimal policy at 1.06 x active first. **If the optimum is below 0.82, no demand cache can pass,** and the question becomes whether a predictor can win without more tier traffic. I would expect this to fail on the published numbers above.
6. **Cost of this test:** a script over [FLAME-MoE-Traces](https://huggingface.co/datasets/CMU-FLAME/FLAME-MoE-Traces) (a few hours, no GPU), then one run of a 30B-class model on a rented GPU to generate decode traces. FLAME's 64 experts at top-6 put 1.06 x active at about 10% of experts, so the result is a ceiling check, not proof.

**Published results under the same conditions: none.** The nearest, 84.6% at 2.4 to 6.4 x active with a trained predictor, uses a different definition of a hit (point 1) and a larger cache.

Related: [Research 03 summary](research_03_summary.md), [Research 03 pain](research_03_pain.md), [Step 22 result](../../new_start/step22_tier_result.md), [Research 02 summary](research_02_summary.md), [Reviews index](README.md)
