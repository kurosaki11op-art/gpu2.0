---
title: Research 04 summary - chip makers buy software teams, not freelance work; the paid categories need capital; India offers cheap compute and design support (1 Nov 2026)
tags: [spark, review, research, verdict, software-for-hardware-makers, jevons, india]
---

# Research 04 summary (1 Nov 2026)

Assignment: [research task 04](../vision_research_task_04.md). Notes: [Jevons](research_04_jevons.md), [categories paid for](research_04_categories.md), [India](research_04_india.md), [item 7: software for hardware makers](research_04_chip_software.md). Independent pass; Jarvis's [first sketch](../restart_2_weakness_study.md) read only afterwards. Labels and read depth are defined in the notes: **[V]** primary text read, **[S]** summary only.

## The answer in brief

1. **Software for hardware makers: strong evidence that chip makers value the layer, none that they buy it from small outside teams.** Four large deals in 13 months bought compiler or runtime teams outright (Qualcomm and Modular, completed 29 Jul 2026; AMD and Untether's engineers; Nvidia and Groq; Intel and Codeplay earlier). I found no contract, price list, services page or funded company selling this work to chip startups. The one firm that did (Codeplay) was acquired.
2. **The open software above the chip is already portable by plug-in** (vLLM, SGLang, the ggml engine; Triton lists only two vendors' GPUs). What new chips lack is the vendor-specific part: operator mapping, tuned kernels, testing on silicon. An outsider needs the vendor's documents and hardware.
3. **How much of the CUDA moat sits in the low-level layer: UNKNOWN.** No measured study. Blogs say the vendor libraries and multi-GPU communication are the hardest to port.
4. **The categories with proven money need capital.** Serving platforms (several above $1B reported) and GPU brokerage (RunPod $325M recurring, company statement via a news relay) sell capacity. The buildable categories (cost visibility, measurement) have the weakest payment evidence and free alternatives; orchestration and sharing are owned by a free vendor tool.
5. **Jevons: weak to moderate.** Volume has grown a lot and suppliers are *raising* prices (a flagship tier doubles on 1 Dec 2026, from first-party price pages [V]). Efficiency mostly enables use by whoever sells capacity.
6. **India: the compute portal is primary and usable** (requests under 5,000 GPU-hours auto-approved; subsidy up to 40%; H100 at ₹153 per hour before subsidy), but it needs a recognised startup or an academic profile. The government's own scheme pages were blocked to my tool, and what Indian chip startups lack in software is **UNKNOWN**.

## Verdict table

Evidence of payment is strong / weak / none; "accessible" is my assessment for two people with free compute.

| category | evidence of payment | accessible to a small team | competition | cheapest experiment that could kill it |
|---|---|---|---|---|
| Software for chip makers: acquisitions of teams | **Strong** (four deals) | not as a product | in-house, Modular (now Qualcomm), Intel's Codeplay | not testable by a small team |
| Software for chip makers: **outside projects** | **None found** | **Partly** (open-engine plug-ins; needs vendor access) | vendors' own teams | Ten conversations with software leads at chip companies, including Indian startups under the design scheme. **Bar (proposed): at least 2 of 10 offer a scoped paid pilot or give written access to documents and hardware or a simulator within six weeks. Kill if none** |
| Orchestration and sharing | Strong for the acquirer, none for a newcomer | **No** (free vendor tool) | vendor's open scheduler | none worth running |
| Utilisation and cost visibility | **Weak** (vendor surveys, an acquisition at unknown price) | **Moderate** | several tools; free OpenCost | A one-page report on ten teams' real GPU data; kill if none share data |
| Serving and inference platforms | **Strong** | **No** as a business | funded platforms | none for a small team |
| GPU brokerage and marketplaces | **Strong** (one company) / weak (another) | **No** | RunPod, Lambda | none |
| Reliability and failure recovery | **None** for an independent product | **No** | clouds in-house; open tools | none |
| On-premises deployment and support | **None found** | UNKNOWN | UNKNOWN | five interviews |
| Data-centre power software | **Weak to moderate** (one funded company; thin proof) | **No** | early | none |

## Corrections to Jarvis's first sketch

| statement | finding |
|---|---|
| Founder's categories: scheduling and sharing | A vendor's free open-source scheduler covers queues, fairness and GPU sharing; the newcomer's route is closed ([categories](research_04_categories.md)) |
| Utilisation and cost visibility | The "5% utilisation" figure is from a vendor's report on its own customers' clusters, not an independent measurement |
| Failure recovery | Large clouds ship it in-house; I found no independent funded product |
| Serving setup for small clouds | No evidence of payment found; the funded platforms are large |
| "Others have inference software too; Nvidia has the low-level layer" | Supported for the top layer (open engines run on several chips); **the share of the moat in the low-level layer is unmeasured** |
| "A well-funded portability-software startup raised hundreds of millions" | Consistent with Modular (about $380M raised, third-party; bought by Qualcomm). The $3.9B price is press-only; neither company's release states a price |
| "Chip startups, including Indian ones, often have small software teams" | **No headcount or software-gap evidence found** (job boards list openings only) |
| "Nvidia subsidised its software; CUDA was free" | Not checked here |
| The size of one acquisition and the scale of an Indian programme (flagged unverified in the brief) | No price found for the orchestration deal; the programme figure is 34,000 to 38,000 GPUs in secondary sources, with no official count read; the subsidy is up to 40% on a published rate list, not a fixed ₹65 or ₹150 |

## What the evidence says about the founder's idea

It is **the one category where a chip maker has been shown to pay real money for what the idea would produce**, and also the one where all the money went to whole teams that had already built a product. Both are true. A two-person service business could be built on the open-engine plug-in route, but the only evidence of demand is indirect, and the first test is an interview, not a build.

## How far to trust this

- **Read on primary pages:** Modular's two releases (price not stated), the India compute portal (rules, rate list), the open projects' hardware lists, two first-party API price pages, OpenRouter's study.
- **Summaries only:** every funding and revenue figure for platforms, most acquisition details (AMD and Untether, Nvidia and Groq, Codeplay), the E2E figures, all government scheme figures.
- **Not reached:** PIB and MeitY pages, AMD's newsroom, Nvidia's announcements of Run:ai and Groq, OpenAI's price page, Google's token statement, OpenRouter's totals, the Stanford chapters' cost multiple, the empanelled-GPU list PDF.
- **Nothing was run or built.** Arithmetic only, marked DERIVED.

## UNKNOWN, and who could answer

| question | who |
|---|---|
| Do chip makers buy compiler, runtime or kernel work from small outside teams, and for how much | Software leads at chip companies; the founder's contacts |
| What software Indian chip startups lack | The startups |
| The low-level share of the CUDA moat | A measured study; engine maintainers |
| Price of the Run:ai, Groq and Codeplay deals | Companies' filings and releases |
| Official count and subsidy of India's GPU programme | The IndiaAI portal operators and PIB (blocked to me) |
| Token volume and price over 12 months, first-party | OpenRouter's data interface; vendors |
| What Indian GPU clouds lack | E2E, Yotta, Neysa |

Related: [Research task 04](../vision_research_task_04.md), [Item 7](research_04_chip_software.md), [Categories](research_04_categories.md), [India](research_04_india.md), [Jevons](research_04_jevons.md), [Research 03 summary](research_03_summary.md), [Reviews index](README.md)
