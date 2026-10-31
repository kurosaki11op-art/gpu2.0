---
title: Research 01 - pricing, margins and buying behaviour (31 Oct 2026)
tags: [spark, review, research, pricing, buyers, competitors]
---

# Research 01: pricing, margins and buying behaviour

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026.

## Margins and revenue

| company | figure | label and source |
|---|---|---|
| Nvidia, FY2026 | Revenue $215.9B; gross margin 71.1% GAAP, down from 75.0% | PUBLISHED, [S] [10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm), [S] [release](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026) |
| Cerebras, 2025 | Revenue $510.0M; hardware $358.4M, cloud $151.6M; gross margin about 39.0% (hardware 42.9%, cloud 29.9%, DERIVED); operating loss $145.9M | PUBLISHED, [P] [S-1](https://www.sec.gov/Archives/edgar/data/2021728/000162828026025762/cerebras-sx1april2026.htm) |
| Cerebras concentration | One customer 62% and another 24% of 2025 revenue | PUBLISHED; 62% seen in a summary of the filing, [S] [breakdown](https://www.mostlymetrics.com/p/cerebras-ipo-s1-breakdown) also reports it |
| Cerebras and OpenAI | 750 MW, over $20B, with a warrant, a $1B loan and exclusivity limits | PUBLISHED, S-1; loan terms seen in a summary only |
| Inference spending | $23.3B against $19B training on AI cloud infrastructure in 2026 (55%) | THIRD-PARTY, Gartner relayed, [S] [TechTimes](https://www.techtimes.com/articles/323879/20260811/gartner-marks-first-year-inference-spending-beats-ai-training-55-cents-every-cloud-dollar.htm) |

**Reading:** Nvidia's 71% margin is real, but it is not a free gift to entrants: Cerebras, the most advanced challenger in this niche, earns 39%. Nvidia's cut room was tested only in a model ([step 14](../../new_start/step14_price_cut_result.md)).

## Prices

| item | value | label |
|---|---|---|
| Rubin rack | about $7.8M to $9.1M; one report $3 to 4M | THIRD-PARTY; see [packaging](research_01_packaging.md) |
| Ironwood on-demand | $12.00 per hour; a large buyer reportedly about $1.60 per hour | PUBLISHED list and THIRD-PARTY estimate, [S] [Shattered](https://shattered.io/google-ironwood-tpu-pricing-vs-nvidia-2026/). **List to deal gap of 7.5x (DERIVED)** |
| GPU API, one 670B-class test | $1.35 input, $5.40 output per million tokens at 36 tokens/s; another provider $2 and $6 at 167 tokens/s | PUBLISHED via [P] [InferenceX v2](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs) |
| Provider margin estimate on that | up to 83% input, 45% output | THIRD-PARTY, same |
| Cerebras API | from about $0.10 per million tokens | Secondary, [S] [page](https://www.morphllm.com/cerebras-pricing) |
| Tenstorrent | p150 $1,399; p100a $999; workstation $11,999; 32-chip rack from $110,000 | PUBLISHED, [S] [summary](https://www.spheron.network/blog/tenstorrent-vs-nvidia-open-source-ai-hardware/), [P] [Register](https://www.theregister.com/on-prem/2025/11/27/blackhole-quietbox-tenstorrents-ai-workstation-reviewed/2113269) |

## Who buys, why, how they decide

| buyer | what is seen | source and limit |
|---|---|---|
| Frontier labs | Multi-gigawatt, multi-supplier deals with equity or finance attached; one lab about 1M TPUs and 3.5 GW; another 750 MW from Cerebras | [S] [TPU deal summary](https://www.inferencechips.com/companies/google-tpu/); S-1 |
| Sovereign-linked buyers | Most of Cerebras's revenue to date | S-1 |
| Neoclouds | Own Nvidia or AMD; compete on price per token | InferenceX |
| Enterprises | Mostly buy tokens or rent | Weak: I found no primary survey of decision criteria |
| Hobbyists and developers | Low-priced cards and workstations | Register review |

Decision criteria from surveys: **UNKNOWN.** I found none I would rely on. Only procurement staff can answer, and that requires interviews.

**DERIVED conclusion:** the large deals are bundled with finance and capacity commitments that no solo founder can offer. The market open to a newcomer without capital is small buyers, and there the price point is already set by parts such as a $1,399 card.

## Check on this project's numbers

- **GPU baseline:** the $3,320 and $25,000 H100 pair is old. UBS's manufacturing estimate of $38,902 is for a superchip with one CPU and two GPUs, and memory is $24,297 of it, so the current cost basis is several times higher, mostly memory. Comparison at the current generation (V-17) needs throughput too, so **no direction of change can be claimed** before running it.
- **Rack-level price per GPU:** about $108,000 to $126,000 (DERIVED from $7.8M to $9.1M over 72, whole rack), far from the $25,000 assumed. The project's "buyer's price" argument must be redone on this, with new throughput.

## What they cannot do

Nvidia cannot lower prices without affecting a very large margin line, but its 3.9-point margin drop shows some sensitivity, not a constraint. Its prices are set by demand; how it would respond to a small entrant is UNKNOWN. Cerebras is exposed to customer concentration, and exclusivity limits whom it may sell to.

Related: [Research summary](research_01_summary.md), [Supply and funding](research_01_supply.md), [Step 14 price cut](../../new_start/step14_price_cut_result.md), [Reviews index](README.md)
