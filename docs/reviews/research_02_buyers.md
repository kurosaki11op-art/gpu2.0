---
title: Research 02 - what buyers say they cannot get, and why inference-chip startups won or struggled (1 Nov 2026)
tags: [spark, review, research, buyers, startups, groq, cerebras, sambanova, graphcore]
---

# Research 02: buyer needs and startup outcomes

Labels and read depth as in [hardware](research_02_hardware.md). **Almost all of this is [S]: secondary articles and search summaries.** Accessed 1 Nov 2026. Where a source is a vendor selling something, it is marked.

## 1. What buyers cannot get

| claim | evidence | label and caveat |
|---|---|---|
| Rented H100 time is expensive and wildly priced | Median on demand about $4.20 per GPU-hour across 16 providers (7 Oct 2026); other trackers $2.81 to $3.46; **$1.38 to $12.29 range, 8.9x (DERIVED)**; hyperscaler on-demand at the top | THIRD-PARTY trackers that disagree, [S] [Uvik](https://uvik.net/blog/gpu-price-index/), [S] [Thunder Compute](https://www.thundercompute.com/blog/ai-gpu-rental-market-trends) |
| Prices for committed capacity rose | One tracker: one-year H100 contracts up 40% to about $2.35 per hour (Oct to Mar), attributed to booked packaging capacity, a memory shortage, and power limits; another headline says on-demand prices fell. **Both can hold: different contract types** | THIRD-PARTY, [S] [Data Storage](https://datastorage.com/articles/gpu-rental-prices-mid-2026-what-h100-h200-and-b200-capacity-actually-costs-right-now/) |
| Memory lead times of 36 to 52 weeks | One source | THIRD-PARTY, [S] |
| **Idle GPUs are common** | One vendor article: audits put average enterprise GPU utilisation at about 5%; a survey says 79% of respondents have GPU capacity idle at least half the time | **Weak:** second-hand (a Gartner spend figure and a survey relayed by a news aggregator and a trade site), not verified, definitions unknown, [S] [finanzen](https://www.finanzen.net/nachricht/aktien/5-gpu-utilization-the-401-billion-ai-infrastructure-problem-enterprises-can-t-keep-ignoring-15671084) |
| Buyers seek alternatives | A 2024 survey of 1,000 companies, run by a chip vendor and two partners, found more than half "actively looking for alternatives to GPUs for inference" | **VENDOR-sponsored**, 2024, [S] [Furiosa](https://furiosa.ai/blog/a-new-global-survey-of-businesses-ai-infrastructure-plans-conducted-by-furiosaai-clearml-and-aiia) |
| Intent to outsource inference | 13.2% to 23.1% in one quarter | One report, [S] |
| Privacy and on-premises | Regulated buyers want control; on-premises gives up on-demand availability | Vendor blog, [S] [BentoML](https://www.bentoml.com/blog/how-to-beat-the-gpu-cap-theorem-in-ai-inference) |
| Neocloud complaints about allocation | **Not found** | UNKNOWN; neoclouds could answer |

**What this adds up to:** price and access complaints are real, but the idle-capacity numbers cut the other way: if buyers truly leave GPUs idle, a cheaper chip does not fix their problem. The evidence on either side is weak. **I found no survey with a method I would rely on. Direct interviews are the only way to resolve this.**

## 2. Startup outcomes

| company | what happened | evidence quality |
|---|---|---|
| Groq | Cut its 2025 revenue projection by more than $1B (reported July 2025) to about $500M (one source), against about $90M in 2024; raised $750M at $6.9B (Sept 2025); then a reported **$17B to $20B licence and asset deal with Nvidia** (late Dec 2025; sources disagree on size and whether it was a purchase) | Secondary; the revenue figures conflict (CB Insights lists $50M for 2025), [S] [SCMP](https://www.scmp.com/tech/big-tech/article/3320085/ai-chip-start-groq-nears-us600-million-funding-deal), [S] [Sacra](https://www.sacra.com/c/groq) |
| Cerebras | Revenue $510M in 2025, 62% and 24% from two customers, 39% gross margin; large contract with one AI lab; IPO | PUBLISHED, from my [Research 01 pricing note](research_01_pricing.md) (filing read in part) |
| SambaNova | Intel talks at about $1.6B reported Dec 2025, **stalled Jan 2026**; partnership Feb 2026; $1B round at $11B in July 2026 | Secondary, [S] [Bloomberg via DCD](https://www.datacenterdynamics.com/en/news/sambanova-seeking-500m-in-funding-after-acquisition-talks-with-intel-stall-report/), [S] [TechCrunch](https://techcrunch.com/2026/07/08/sambanova-draws-1b-at-11b-valuation-in-series-f-first-close/) |
| Graphcore | $4M revenue in 2023; sold to SoftBank in 2024 for about $600M, below the $700M raised | [S] [Sifted](https://sifted.eu/articles/graphcore-company-accounts-2023-news) |
| Untether AI | Receivers appointed Feb 2026 | [S] [tracker](https://killedbyai.net/funding/) |

**Primary reasons:** I found no source that tested a cause. Observable patterns, **DERIVED from the table, not proven:** (1) two of the three that sold or were absorbed (Groq, Graphcore) were far below their own revenue plans; (2) the one public filing shows revenue concentrated in two buyers, each tied to a financing relationship; (3) the survivors were bought or financed by an incumbent or a sovereign-linked investor. Graphcore's founder blamed lack of investment ([S] [EE Times](https://www.eetimes.com/ai-chip-startup-graphcore-acquired-by-softbank/)). **Whether software maturity was the cause is UNKNOWN** from what I read; claims that it was come from blogs.

**Implication for a small team:** two of the routes that worked were an acquisition by or licence to an incumbent, and a financing-linked anchor customer. The brief's "small startup working with big companies" is consistent with the Groq outcome, but that is one case, and the reported price shows the incumbent wanted a team and an architecture, not a product revenue line.

Related: [Research 02 summary](research_02_summary.md), [Research 01 pricing](research_01_pricing.md), [Research 01 supply](research_01_supply.md), [Reviews index](README.md)
