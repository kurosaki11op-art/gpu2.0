---
title: Research 03 Part A - is GPU cost and capacity a real pain, and for whom - counted evidence, prices, filings, workarounds, funding (1 Nov 2026)
tags: [spark, review, research, demand, pain, prices, filings, issue-trackers]
---

# Research 03, Part A: is it a real pain?

Pain is scored as **frequency x severity x lack of good workarounds x evidence of money spent**. Labels as in [Part B](research_03_routing.md); read depth **[V]** verbatim, **[S]** summary only. Accessed 1 Nov 2026. **Nothing here comes from asking a buyer.** That is the gap that matters most.

## 1. Counted evidence: what open-source users complain about

I counted issues through GitHub's public search (total counts only, 1 July to 30 Sept 2026), for the two most used open serving projects. Counts are as returned by the index at fetch time and were not checked against each repository's own page.

| query | vllm-project/vllm | share | ggml-org/llama.cpp | share |
|---|---|---|---|---|
| all issues created | 2,355 | | 1,437 | |
| label bug | 702 | 29.8% | not run | |
| label performance | 33 | 1.4% | not run | |
| label usage | 15 | 0.6% | not run | |
| label installation | 14 | 0.6% | not run | |
| "OOM" in the title (loose match) | 26 | 1.1% | 20 | 1.4% |
| "out of memory" phrase in the title | 1 | 0.04% | 3 | 0.2% |

**Reading:** out-of-memory complaints are about 1% of issue titles in both projects, and installation and performance labels are small. **This does not show cost or capacity as a visible pain in the trackers**, and it **contradicts the impression I gave in [Research 02](research_02_cuda.md) that driver and version mismatches dominate**: that came from a how-to guide, not from counts. Limits: labels are applied to a third of issues at most (702 + 33 + 15 + 14 = 764 of 2,355), titles omit causes, people with a capacity problem often buy another GPU or use an API instead of filing an issue, and an issue tracker measures software friction, not cost. UNKNOWN: counts by cause for the whole set (would need reading titles).

## 2. Money: prices, from first-party pages

Read from the vendors' own pages on 1 Nov 2026 (prices per GPU-hour, on demand; dates only where the page shows one):

| provider | H100 SXM | H100 PCIe | H200 | B200 | note |
|---|---|---|---|---|---|
| Runpod, pods (page dated 28 Oct 2026) | $3.99 | $2.89 | $5.29 | $7.99 | serverless H100 $5.39; clusters H200 $6.35 |
| Runpod, same page's embedded data | $2.69 (community) | | $3.59 | $5.98 | meta text says "from $1.99"; **the page contradicts itself** |
| Lambda instances (no date) | $3.99 to $4.29 | $3.29 | not listed | $6.69 to $6.99 | |
| Lambda clusters (no date) | $6.16 (16 GPUs), $5.85 (64), $5.54 (256) | | | $9.86, $9.36, $8.87 | |
| CoreWeave node of 8 (no date) | $49.24 per hour, i.e. **$6.16 per GPU** (my division) | | $50.44 ($6.31) | $68.80 ($8.60) | spot $19.71 (40% of on demand), H200 $20.93 (41.5%), B200 $34.11 (49.6%) |

All PUBLISHED, first-party [V]. Hyperscaler pages (AWS, Google) gave **no GPU prices to my fetch tool: UNKNOWN.**

- **Spread for one GPU type, one week: $1.99 to $6.16 per hour, 3.1x (DERIVED)**, depending on provider, commitment and product. A 256-GPU Lambda cluster costs 10% less per GPU than a 16-GPU one (DERIVED: 5.54 / 6.16).
- **Twelve-month trend: no first-party series.** The Internet Archive was blocked for my tool. Third-party readings say one-year H100 contract prices rose 40% (from $1.70 to $2.35, Oct 2025 to Mar 2026; SemiAnalysis data relayed by [Akash](https://akash.network/the-bid/h100-rental-price-2026-cost-per-hour/)) and that first-party lists moved from $2.99 to $3.99 (Lambda) and $3.29 to $3.99 (Runpod) ([IntuitionLabs](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison)). Today's Runpod $3.99 matches the end of the second series. Earlier in 2025 prices fell (reportedly from about $8 to $3.50 and an AWS cut of about 44%): THIRD-PARTY, unverified. **So the direction over the last year is a fall in 2025 and a rise since late 2025, but I could not confirm either from a first-party series.**

## 3. Money: filings and supply data

| item | value | label and source |
|---|---|---|
| Nvidia FY2026 (year to 25 Jan 2026), concentration | One direct customer **22%** of revenue, another **14%** | PUBLISHED [V], [10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm) risk factors |
| Same, supply obligations | $95.2 billion of inventory purchase and long-term supply and capacity obligations; manufacturing lead times "extended beyond twelve months for some products" | PUBLISHED, summary-level [S] (figure from the auditor's paragraph, not read verbatim) |
| Same, revenue | $215.9 billion; Data Center grew 68% (dollar figure for Data Center not reached) | PUBLISHED [S] |
| CoreWeave FY2025 (10-K filed 2 Mar 2026) | Revenue $5.1B (2024: $1.9B); **top customer 67%**; $60.7B remaining contracts (2024: $15.1B); about 3.1 GW contracted power; contracts take-or-pay, about five years | PUBLISHED [S] (only the cover read verbatim; MD&A, financials and notes not reached) |
| 2025 supply shares | Nvidia used about 60.3% of advanced packaging (CoWoS) and 68.9% of high-bandwidth memory; the four largest designers about 90% of both | THIRD-PARTY model with stated method, [V] [Epoch AI, Mar 2026](https://epoch.ai/data-insights/ai-chip-supply-chain-constraints) |
| Cerebras 2025 | Revenue $510M; 62% and 24% from two customers (from [Research 01](research_01_pricing.md)) | PUBLISHED, filing read in part |

**Reading (DERIVED):** the money is large and concentrated. Spend is evidenced by multi-year take-or-pay contracts (CoreWeave: $60.7B, about 12x its 2025 revenue) and by a supplier whose two largest customers take 36% of revenue. **That is evidence that very large buyers pay for capacity, not that small buyers are hurt.** I did not reach the filings' discussion of capacity delays or utilisation.

## 4. Surveys

| survey | sample and method | finding | quality |
|---|---|---|---|
| Digital Realty, 2026 | 2,131 IT decision-makers, 19 countries, fieldwork Nov 2025 to Feb 2026 | 40% name a lack of **specialised infrastructure** as their main AI constraint (9% in 2024) | run by a data-centre operator; "specialised infrastructure" is not GPU cost; [S] [report](https://letsdatascience.com/news/digitate-research-flags-specialized-ai-infrastructure-gap-10688bdb) |
| DDN with a research firm, Jan 2026 | 600 US decision-makers | data layer, not accelerators, is the bottleneck; 98% cite a skills shortage | vendor-commissioned, [S] [report](https://insidehpc.com/2026/01/ddn-report-65-of-organizations-struggling-to-achieve-ai-success/) |
| Drexel and a data company | 505 leaders | infrastructure 54%, skills 51% | [S] |
| "Average enterprise GPU utilisation 5%" | cited second-hand via a Gartner spend figure and a news aggregator | idle capacity | **no method found; treat as unverified** |

I found **no survey of developers or inference operators** with a stated method that names GPU cost or memory as the top pain. The surveys that exist point to data infrastructure and skills.

## 5. Workarounds, and what they already remove

| workaround | what it fixes | evidence |
|---|---|---|
| Batching | Cost and energy per token | **Our measurement (G1): 8x to 14x less energy per token at batch 16**, laptop and cloud GPU; I did not rerun it |
| CUDA graphs and a tuned engine | "Slow at batch 1" | **Our measurement (test B, T4, one engine): graphs made it 4.7x and 2.5x faster, reaching 72% and 95% of the weights-only floor** for two small models; the default library path was 13% to 31% of the floor. Read from the plan note; I did not rerun. [V] hw/gpu/graphs_test/PLAN.md |
| Low-bit weights | Memory and bytes | Kernel quality varies 3.4x ([Research 02](research_02_fixes.md)); quality loss unverified ([Research 01](research_01_numerics.md)) |
| Rent or call an API | Having no GPU | Price spread 3.1x within one week (above) |
| More or bigger GPUs | Capacity | Works at about 7 GPUs for a 1T model (step 22), at the price of a cluster |

**Which pains the workarounds already remove:** slow decode on a small model at batch 1 (removed by an engine setting on one GPU), energy per token at high batch (removed by batching). **Which they do not:** a model larger than one GPU's memory (needs several GPUs), the price of the rental, supply and waiting time for large buyers. For those, the evidence in this note is thin for small buyers and strong only for the very large.

## 6. Funding and attempts

The funded attempts sell to the same few large buyers: Cerebras (two customers, 86% of 2025 revenue), Groq (a reported licence deal with Nvidia, [Research 02](research_02_buyers.md)), SambaNova (a $1B round at $11B in July 2026, Intel talks stalled; [S]). **That shows the pain is paid for at the top of the market, not by small teams.** I found no open project funded to cut small users' cost. UNKNOWN: any evidence of small buyers buying from these startups.

## 7. Verdict table

Strength is the strength of evidence of **pain that someone pays to remove**, not of the existence of a problem.

| group | cost per token | supply, waiting | capacity (does not fit) | speed (bandwidth) | power and cooling | software setup | what is unknown, and who could answer |
|---|---|---|---|---|---|---|---|
| Frontier labs and hyperscalers | **strong**: multi-year contracts, a $95B supply book | **strong**: 12-month lead times, 90% of packaging and memory consumed by four designers | strong (they buy racks) | strong (they pay for fast tiers) | **strong**: multi-GW contracts | weak | They are not reachable by a small team |
| Regional and neoclouds | weak-to-moderate: price lists differ 3.1x, spot is 40% of on demand | moderate: take-or-pay contracts (CoreWeave $60.7B); component shortages in risk factors [S] | weak | none | moderate: 3.1 GW contracted (CoreWeave) | weak | What small clouds pay and why; operators |
| Small AI companies and independent developers | **weak**: only list prices | **none** found | **weak**: OOM about 1% of issue titles | **weak, and mostly closed by engine settings** (test B) | none | weak (0.6% of vLLM issues are installation-labelled) | Whether they would pay more than they do; direct interviews |
| Universities and labs | **none** | none | none | none | none | none | Nobody was searched beyond general surveys; they could answer |
| Enterprises on premises | weak: surveys are vendor-run | none | none | none | none | none | Why they avoid cloud; their IT teams |
| Device makers (on-device AI) | **UNKNOWN** | | | | | | Not researched here |

**Net:** the pain is **strong and proven for very large buyers and unproven for anyone a small team could reach.** The one pain my counted evidence cannot reach is cost for small buyers; for that I found only list prices.

Related: [Research 03 summary](research_03_summary.md), [Research 03 routing](research_03_routing.md), [Research 02 buyers](research_02_buyers.md), [Research 01 pricing](research_01_pricing.md), [Test B plan](../../hw/gpu/graphs_test/PLAN.md), [Reviews index](README.md)
