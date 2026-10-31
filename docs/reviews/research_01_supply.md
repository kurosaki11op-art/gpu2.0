---
title: Research 01 - supply chain and manufacturing access for a startup, foundry, packaging and funding (31 Oct 2026)
tags: [spark, review, research, supply, foundry, funding, india]
---

# Research 01: supply chain and access for a startup

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026. **Most cost figures are from sites that sell planning services, and they disagree. Only a foundry or a broker's written quote settles them.**

## Costs of a chip

| item | value | label and source |
|---|---|---|
| N5 mask set; total NRE | about $6.5M; about $10M | THIRD-PARTY, [S] [Silicon Analysts](https://siliconanalysts.com/analysis/fabless-startup-tapeout-cost-guide) |
| N3 mask set | $10M to $50M across sources | THIRD-PARTY, [S] [guide](https://siliconanalysts.com/guide/tsmc-3nm-cost) |
| Total design of a 3 nm AI accelerator | $400M to $600M+ | Low-confidence estimate, [S] [report](https://www.useluminix.com/reports/competitive-intelligence/cost-estimates-for-openai-s-chip-jalapeno/source/1) |
| MPW seat, 22 nm and below | $50,000 to $400,000 | Broker's page, [S] [ToMPW](https://www.tompwservice.com/pricing) |
| N5 wafer | about $18,500 | THIRD-PARTY, [S] [Silicon Analysts](https://siliconanalysts.com/data/wafer-pricing) |

The project's assumed $150M design cost sits below the low-confidence range and above masks alone. It cannot be called conservative.

## Packaging and supply

- **CoWoS:** Nvidia about 60% of TSMC's 2026 capacity, Broadcom about 15%, AMD about 11% (THIRD-PARTY, Morgan Stanley relayed, [S] [TipRanks](https://www.tipranks.com/news/tsmc-expands-ai-chip-packaging-as-supply-limits-shift)). Other suppliers are expanding ([S] [DIGITIMES](https://www.digitimes.com/news/a20251210PD218.html)). Startup allocation: UNKNOWN.
- **A design without HBM or CoWoS avoids this bottleneck,** as LP30 does on Samsung SF4X ([P] [ServeTheHome](https://www.servethehome.com/decoding-the-future-of-inference-at-nvidia-groq-lpus-join-vera-rubin-platform-for-low-latency-inference/2/)). This is the one supply benefit of the project's SRAM design, and it holds for a simple package.
- **Wafer-scale:** Cerebras buys "substantially all" services on purchase orders with no capacity commitment, and has sole-source suppliers (PUBLISHED, [P] [S-1](https://www.sec.gov/Archives/edgar/data/2021728/000162828026025762/cerebras-sx1april2026.htm)). **Whether a foundry would give a startup whole-wafer access, on what terms: UNKNOWN.** I found no second company doing this. Only the foundries can answer.

## Funding levels of rivals

| company | figure | label and source |
|---|---|---|
| Cerebras | IPO May 2026 at $185 per share, later well below its first-day high | Secondary, [S] [INDmoney](https://www.indmoney.com/blog/us-stocks/cerebras-stock-cbrs-earnings-valuation-analysis) |
| Groq and Nvidia | about $20B deal, Dec 2025; asset purchase plus licence and hires; not confirmed officially in what I read | THIRD-PARTY, [S] [summary](https://intuitionlabs.ai/articles/nvidia-groq-ai-inference-deal) |
| Etched | $700M, Aug 2026, valued at $10.3B | Secondary, [S] [tracker](https://newmarketpitch.com/blogs/news/ai-inference-chips-top-startups-fundraising) |
| MatX | $500M Series B, Feb 2026 | same |
| Positron | $230M, Feb 2026 | same |
| Small rounds | Rounds under $100M total only $466M, falling from $570M two years ago | same; a blog's count |

**Reading:** the entry price for a leading-node accelerator is now hundreds of millions of dollars.

## What is open to a student founder in India

| route | detail | label and source |
|---|---|---|
| DLI scheme, design support | Up to 50% of eligible cost, capped at ₹15 crore per application, plus sales-linked incentive | Secondary and conflicting; check the [PIB note](https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=156811&ModuleId=3&reg=3&lang=1) and guidelines. [S] [Fidus](https://fidus.one/india-semiconductor-mission) |
| MPW and validation support | Up to ₹30 lakh per application (about $34,000) | Secondary, [S] [India Briefing](https://www.india-briefing.com/news/india-design-linked-incentive-scheme-semiconductor-sector-supply-chain-40767.html/), [S] [NirmanKit](https://www.nirmankit.in/learn/semiconductor-dli-how-to) |
| ChipIN Centre | Remote EDA tools and IP for startups and MSMEs | Secondary, [S] [Startupwire](https://www.startupwire.in/post/indias-semiconductor-ecosystem-moves-toward-scale-eda-tools-chip-design) |
| SCL Mohali | 180 nm MPW for academics and early startups; 56 chips made there | Secondary, [S] [EE Times India](https://www.eetindia.co.in/india-eyes-50-fabless-chip-firms-as-dli-scheme-gains-traction/). Whether it is free: UNKNOWN |

**Possible explanation of the open "30 lakh" item in the [deep study plan](../gpu_deep_study_plan.md):** ₹30 lakh matches this MPW support cap. I cannot tell whether that is what the founder saw. If so, it is **about a shuttle seat, not a wafer system,** and is far below any N5 route. Eligibility rules for a student, and whether a company must exist first: UNKNOWN; ask the scheme office.

## What a realistic ladder looks like (DERIVED; no quotes)

1. Free: simulator, open PDK synthesis, measurements on owned hardware.
2. About ₹0 to ₹30 lakh: one tile on 180 nm through SCL or an open shuttle. This gives measured energy for MACs and SRAM on an old node.
3. $50,000 to $400,000: a small test chip at an advanced node, needing grants or a partner.
4. $10M+: an N5 product. Requires venture funding, which requires steps 1 to 3 and a buyer.

A wafer-scale part is off this ladder.

## What they cannot do

Incumbents do not need these routes, so they do not compete for them. That gives little advantage, apart from a low-cost way to get measured silicon data.

Related: [Research summary](research_01_summary.md), [Pricing](research_01_pricing.md), [Manufacturing data requests](../manufacturing_data_requests.md), [Reviews index](README.md)
