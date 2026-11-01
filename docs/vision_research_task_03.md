---
title: Research task 03 for Vision - is GPU cost and capacity a real pain, and does expert routing allow a small SRAM cache (1 Nov 2026)
tags: [spark, review, research, prompt, demand, pain, moe, vision]
---

# Research task 03 for Vision (1 Nov 2026)

Founder's request: find out whether the problem is a **real pain** for real people, from articles, papers, repositories, communities and platforms. Jarvis did a first web pass ([leads in the watch list](watch_radar.md)); it is secondhand and mostly blogs. Work independently from primary pages; read the leads only after your own pass, as before.

Repository: <https://github.com/kurosaki11op-art/gpu2.0>. Read branch `claude/sharp-davinci-wrwazg`; work on a new branch `vision/research-3`; write only in `docs/reviews/` (`research_03_<topic>.md` and `research_03_summary.md`). Standing rules: label every number (MEASURED / SIMULATED / MODELLED / ESTIMATED / PROJECTED; quoted figures PUBLISHED / VENDOR CLAIM / THIRD-PARTY ESTIMATE / UNKNOWN), source link and date for each, UNKNOWN instead of guessing, no AI model identifiers in repository content (describe models by size and type).

## Part A: is it a real pain? (evidence, not opinion)

Define pain as **frequency x severity x lack of good workarounds x evidence of money spent**. For each of the groups below find primary evidence for each factor and say what you could not find.
1. **Who** is hurt: small AI companies, independent developers, labs and universities, regional clouds, enterprises running models on premises, makers of on-device products. Rank by evidence, not by size.
2. **What hurts:** cost per token, GPU price or rental, supply and waiting time, memory capacity (models that do not fit), memory bandwidth (speed), power and cooling, software setup. Use counted evidence: public issue trackers (counts and dates of threads by cause), forum and community posts that quote numbers, conference talks, surveys with a stated method and sample.
3. **Money:** public price lists of GPU rental and hosted inference (several providers, dates), price trends over 12 months, reported utilisation of rented or owned GPUs, earnings or filing statements about supply and cost (primary pages only).
4. **Workarounds and their limits:** what people already do (quantisation, batching, engine settings, cheaper GPUs, rented capacity, API providers) and where those fail; use our own measurements as one data point: batching saved 8x to 14x energy per token and graphs made one engine 2.5x to 4.7x faster ([test B](../hw/gpu/graphs_test/PLAN.md)). Say which pains those workarounds already remove.
5. **Funding and attempts:** startups and open projects that attack the pain and how they fared (funding, customers), as evidence the pain is paid for.
6. **Verdict table:** for each group and each pain: evidence strength (strong / weak / none), what is still UNKNOWN, and who could answer.

## Part B: expert routing and a small on-chip cache (decides the step 22 speed bar)

[Step 22](../new_start/step22_tier_result.md) found that a 1T mixture-of-experts model at batch 1 reads about 16 GB per token from a 500 GB model, that 11 chips hold about 17 GB of SRAM (3.4% of the weights), and that the speed bar needs 82% to 95% of each token's reads to come from that SRAM. The literature disagrees on how skewed expert popularity is. From the **primary papers** (not blog summaries), answer:
1. Measured expert hit rates for a cache holding about 3% to 6% of the experts, **per layer and over the whole model**, with and without a routing predictor, and for which models and workloads (chat, code, long context). Report the number of models, the window length over which hits are counted, and the batch size.
2. Whether hit rates hold at batch 1 for models with hundreds of small experts, and how they change at batch 8 to 64.
3. Any published routing trace we could download and replay (name the source), and the smallest model whose routing statistics are representative of a 1T-class model.
4. A **pass line proposal:** the hit rate a 17 GB cache must reach for the step 22 speed bar (82%) and whether any published result reaches it under the same conditions.

## Deliverables

One note per topic, a summary with the verdict table (Part A) and the hit-rate table (Part B), and a short list of corrections to Jarvis's first pass. Public sources only; do not contact anyone.

Related: [Research task 02](vision_research_task_02.md), [Watch list with the first-pass leads](watch_radar.md), [Step 22 result](../new_start/step22_tier_result.md), [Reviews index](reviews/README.md), [Docs index](INDEX.md)
