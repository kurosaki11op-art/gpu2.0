---
title: Research 04 - Jevons paradox in AI inference - evidence that cheaper tokens raise total use, counter-evidence, and what it means for a seller of efficiency (1 Nov 2026)
tags: [spark, review, research, jevons, prices, token-volume]
---

# Research 04: Jevons paradox

Labels and read depth as in [item 7](research_04_chip_software.md). Accessed 1 Nov 2026. **Most of the volume and price-history evidence is secondary; the primary pages I reached give a few firm points and many gaps.** I describe models by tier.

## What the primary pages show

| item | value | label |
|---|---|---|
| OpenRouter and a venture firm's study | Over **100 trillion tokens** analysed over about 13 months to Nov 2025; token volume by model author given in trillions (the largest author 14.37, ten authors listed); no total per month in the readable text | PUBLISHED [V], [State of AI 2025](https://openrouter.ai/state-of-ai) (Dec 2025). A sample of one routing service, not the market |
| OpenRouter live rankings | "Usage data through Oct 31, 2026"; weekly chart with no numbers in the text I could read | [V] [rankings](https://openrouter.ai/rankings); totals UNKNOWN |
| Google's tokens per month | **Not reached.** The search summary says 3.2 quadrillion per month (May 2026), up about 7x in a year, and that Google stopped publishing it | [S], unverified |
| Stanford AI Index 2026 | The pages read gave adoption figures (generative AI reached 53% adoption in three years; a consumer surplus estimate of $172B a year) and **no token volume and no fall-in-cost multiple** | PUBLISHED, [V] [overview](https://hai.stanford.edu/ai-index/2026-ai-index-report) and chapters; the quoted "280x fall" is [S] only |
| Current API prices, first-party, 30 Oct 2026 for one vendor | Small tier $0.25 input / $1.50 output per million tokens (a newer small tier $0.30 / $2.50); mid tier $2 / $12 (up to 200k context); flagship tier **$2.00 / $10.00 until 30 Nov, then $4.00 / $20.00 from 1 Dec 2026**; another small-tier model **$0.75 / $3.75 doubling on 1 Jan 2027** | PUBLISHED [V], [price page](https://ai.google.dev/gemini-api/docs/pricing) |
| A second vendor, undated | Small tier $0.10 input / $0.50 output (up to 100k context); mid tier $2 / $10; large tier $4 / $20; top tier $10 / $50; batch use 50% off | PUBLISHED [V], [price page](https://claude.com/pricing) |
| A third vendor | Page returned an access error: UNKNOWN | |

**DERIVED:** within one vendor the output price of the large tier is 13x (20 / 1.50) to 40x (20 / 0.50) that of the small tier, so *cheaper* tokens exist alongside *dearer* ones.

## Evidence for the paradox (secondary)

- A routing service reported that daily volume for two models rose **13.8x and 5.6x** after price promotions, and stayed above the discount-window level ([S] [OfficeChai](https://officechai.com/ai/jevons-paradox-openrouter-says-that-usage-of-tokens-jumped-after-discounts-on-gpt-5-6-terra-and-luna/), summarising the service's post; the post itself I did not read). This is a promotion on a few models, which tests substitution between models as much as total use.
- Reported growth: a platform's recurring revenue from $120M to $325M in nine months (RunPod, company statement via search, **2.7x DERIVED**); several inference platforms above $1B ([categories](research_04_categories.md)).
- A coding workload share rising from about 11% to over 50% of one service's volume ([S] secondary analyses).
- The inference share of cloud AI spend passing training in 2026 (Gartner via a trade site, [S]).

## Counter-evidence

- **Primary:** the price pages above show **scheduled price rises** for the top tiers (flagship doubling on 1 Dec 2026; one mid-size model doubling on 1 Jan 2027). Suppliers raising prices while volume grows is what shortage looks like, and it says the efficiency gains are not simply passed to buyers.
- Secondary: a gateway's blended price per token was flat in June 2026 while volume grew 29% ([S] [Tech Life](https://www.techlifeadventures.com/post/cheaper-ai-models-jevons-paradox-compute-demand)).
- No source I read separates the effect of price from that of better models and new uses (coding agents). Volume growth is not proof of a price effect.

## What it implies for a seller of efficiency (DERIVED)

1. **Efficiency enables more use by someone else.** The money in the evidence is earned by whoever sells capacity or tokens (platform revenue above) and by chip and cloud suppliers, not by tools that cut a buyer's bill.
2. **Buyers pay for access.** When suppliers raise prices and take-or-pay contracts run five years ([Research 03](research_03_pain.md)), what is scarce is capacity, which supports selling something that adds or unlocks capacity, and weakens a pure "spend less" pitch.
3. **A seller of efficiency can still win where it is also the buyer's supplier** (a token or capacity vendor), since lower unit cost widens its margin as prices fall.

**Strength of evidence: weak to moderate**, mostly secondary. The firm facts are the volumes in the study, the price pages, and the scheduled rises. UNKNOWN: a first-party series of token volume and price over 12 months. Who could answer: OpenRouter's data interface (linked on its rankings page; not fetched), the vendors' own reports.

Related: [Research 04 summary](research_04_summary.md), [Research 04 categories](research_04_categories.md), [Research 03 pain](research_03_pain.md), [Reviews index](README.md)
