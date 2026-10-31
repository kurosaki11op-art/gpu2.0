---
title: Research 01 - memory capacity, bandwidth, energy and cost at Nvidia, Cerebras and rivals (31 Oct 2026)
tags: [spark, review, research, memory, competitors]
---

# Research 01: memory

Labels: PUBLISHED, VENDOR CLAIM, THIRD-PARTY ESTIMATE, MEASURED, DERIVED (my arithmetic on the labelled inputs), UNKNOWN. Read depth: **[P]** primary source read in part, **[S]** only a search summary or secondary page. Accessed 31 Oct 2026. Evidence grading is in the [summary](research_01_summary.md).

## What they do

| machine | fast memory | bandwidth | bandwidth per GB (DERIVED) | label and source |
|---|---|---|---|---|
| Nvidia Rubin GPU | 288 GB HBM4 | 22 TB/s | about 76 per second | VENDOR CLAIM via press; [S] [summary of specifications](https://hashrateindex.com/blog/nvidia-vera-rubin-nvl72-specs-breakdown/). Rack bandwidth figures conflict: 1.4 or 1.6 PB/s, [S] [report](https://www.tweaktown.com/rss/click/news/114304/?c=news-mf) |
| Nvidia rack (72 GPUs) | 20.7 TB HBM4 plus 54 TB LPDDR5X | as above | | VENDOR CLAIM, [S] same |
| Nvidia and Groq LP30 | about 0.5 GB SRAM, no HBM; 128 GB in a 256-chip rack | 150 TB/s per chip (one analysis) | about 300,000 per second | Rack total PUBLISHED by vendor via [P] [ServeTheHome, Mar 2026](https://www.servethehome.com/decoding-the-future-of-inference-at-nvidia-groq-lpus-join-vera-rubin-platform-for-low-latency-inference/2/); bandwidth THIRD-PARTY, [S] [analysis](https://morethanmoore.substack.com/p/nvidia-introduces-groq-lp30-and-lpx) |
| Cerebras WSE-3 | 44 GB SRAM | 21 PB/s | about 477,000 per second | VENDOR CLAIM in a filing, [P] [S-1, Apr 2026](https://www.sec.gov/Archives/edgar/data/2021728/000162828026025762/cerebras-sx1april2026.htm) |
| Cerebras CS-4 | still 44 GB per wafer; 3 wafers per rack | about 43 PB/s per wafer | about 980,000 per second | VENDOR CLAIM via [P] [SemiAnalysis, Aug 2026](https://newsletter.semianalysis.com/p/cerebrass-next-generation-cs-4-fast) and [P] [Next Platform](https://www.nextplatform.com/compute/2026/08/19/cerebras-overclocks-wse-3-waferscale-engine-to-boost-inference-oomph-in-nexus-cs-4/5289400) |
| Google Ironwood | 192 GB HBM | UNKNOWN here | | VENDOR CLAIM, [S] [summary](https://thenextweb.com/news/google-ironwood-tpu-inference-cloud-next) |
| Tenstorrent p150 | 32 GB-class GDDR6, 512 GB/s; 180 MB SRAM | 512 GB/s | about 16 per second | VENDOR, [S] [store summary](https://www.spheron.network/blog/tenstorrent-vs-nvidia-open-source-ai-hardware/) |

## Why

Decode is memory bound, and HBM bandwidth has grown more slowly than compute. In a Google paper accepted by IEEE Computer, Nvidia 64-bit FLOPS grew 80x from 2012 to 2022 while bandwidth grew 17x (PUBLISHED, [P] [Ma and Patterson, 2026](https://arxiv.org/abs/2601.05047)). Nvidia chose HBM because it serves training as well as inference. Cerebras and Groq chose SRAM for its bandwidth per bit.

## What the buyer really gets

- **Speed from SRAM is real at the user level.** Artificial Analysis figures, relayed by others, are about 1,700 tokens/s sustained for Cerebras on a 120B model, and 478 to 493 for Groq. A vendor's own documentation claims about 3,000 ([S] [secondary comparison](https://www.spheron.network/blog/groq-lpu-vs-cerebras-wse-cheapest-inference-2026/); I did not reach Artificial Analysis's own page). Sustained speed is well below the vendor claim, which itself is a lesson.
- **Capacity is what SRAM lacks.** SemiAnalysis's author estimates that a roughly 1.6T-parameter model needs about 20 to 40 "systems", over $20M of capital and 1 MW (THIRD-PARTY ESTIMATE; the text mixes "systems" and wafers, so the unit is unclear; [P] same article).

## Efficient, effective, cheap?

| item | value | label |
|---|---|---|
| HBM3E cost per GB, Q4 2023 to Q4 2025 | about $15 to $20.5 (read from a chart); 1.35x rise | PUBLISHED, [P] Ma and Patterson |
| HBM3E cost per GB/s | about $0.29 to $0.39 (read from a chart); 1.35x rise | same |
| DDR4 cost, 2022 to 2025 | capacity 0.54x, bandwidth 0.45x | same |
| HBM4 price per GB | about $15 to $36 contract or forecast; $72.58 spot for scarce lots, Sep 2026 | THIRD-PARTY ESTIMATES that disagree, [S] [Silicon Analysts](https://siliconanalysts.com/data/hbm-pricing), [memoryindex](https://memoryindex.io/hbm4-price) |
| HBM3E energy | about 3.44 pJ/bit (model validated against a reported value) | PUBLISHED, [S] [RPU paper](https://arxiv.org/pdf/2602.18568) |
| HBM share of system cost | memory is about 26% of a $7.8M rack in one estimate; 62% of a $38,902 superchip bill in another | THIRD-PARTY ESTIMATES on different bases, [S] [Morgan Stanley relayed](https://www.digitalcitizen.life/nvidias-vera-rubin-ai-rack-may-cost-7-8-million-as-memory-prices-surge/), [UBS relayed](https://technews.tw/2026/09/07/ubs-disassembles-the-vera-rubin-platform-cost/) |
| SRAM cost per GB | no public source found | UNKNOWN; the project's $175 per GB of die is its own derivation |

**DERIVED consequences for this project:**

1. The project's 5.74 pJ/bit HBM figure is 1.67x the 3.44 pJ/bit above. At 3.9 pJ/bit my earlier test moved central energy from 13.2x to 12.0x, so the effect is modest because GPU board power dominates.
2. The SRAM to HBM price gap is 2.4x to 11x on the figures above ($175 against $72.58 to $16), not a fixed 10x. It moved in the project's favour during 2026, and the source warns that part of the surge is short-term demand.
3. A 1T model at 4 bits needs 500 GB for weights alone: about 4 LP30 racks or 12 Cerebras wafers (11.4 rounded up), before any cache. The same 500 GB fits in under 2 Rubin GPUs.

## The flaw, and what stops copying

SRAM-only memory has a capacity flaw, and the strongest public statement is direct: the Google authors call SRAM-only solutions insufficient, and say Cerebras and Groq both later retrofitted external DRAM ([P] Ma and Patterson, page 3). Note that the authors work at a company that sells HBM-based TPUs, so they are not neutral. The roadmap of Cerebras adding stacked DRAM is reported ([S] [RCR](https://rcrtech.com/semiconductor-news/cerebras-cs-4-nexus-rack-cs-6/); not confirmed in its own materials).

**Cheapest fixes a newcomer could study** (from the same paper, none tested by us): High Bandwidth Flash for weights, claimed 10x capacity per node, limited by write endurance and microsecond page reads; near-memory compute; 3D stacking. All need vendor partnerships. Incumbents can adopt each of them, so none is a moat.

## What they cannot do, or do badly

- **Nvidia:** HBM supply and price exposure; bandwidth per GB is about 4,000x lower than LP30's. It has bought the answer by adding LPX for decode.
- **Cerebras:** capacity per wafer has been flat at 44 GB since WSE-3, and concurrency is costly, because each request's cache also sits in scarce SRAM.
- **Groq LP30:** one vendor-reported view says it is not low cost for the largest models ([P] ServeTheHome). LP30 lacks FP4; LP35 adds it in 2027 (vendor roadmap, same source).

Related: [Research summary](research_01_summary.md), [Compute](research_01_compute.md), [Numeric formats](research_01_numerics.md), [Reviews index](README.md)
