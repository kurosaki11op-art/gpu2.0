---
title: Research 04 - categories of GPU software and services that companies pay for, who buys, and what a small team could build (1 Nov 2026)
tags: [spark, review, research, categories, orchestration, serving, finops, power, buyers]
---

# Research 04: what is paid for

Labels and read depth as in [item 7](research_04_chip_software.md). **Almost everything here is [S]:** search summaries of company claims and trade press, because first-party pages for funding and revenue mostly did not load or do not exist. Revenue figures are marked as company statements or third-party estimates. Accessed 1 Nov 2026.

## Category table

"Accessible" means what a two-person team with a laptop GPU and free cloud GPUs could build and test in weeks. It is my assessment, not evidence.

| category | evidence of payment | typical customer and model | free alternatives | dominant players | accessible to two people? |
|---|---|---|---|---|---|
| Orchestration and scheduling | Nvidia bought Run:ai (**no price found** in anything I read; any size quoted from memory is unverified) and then open-sourced its scheduler under Apache-2.0 ([S] [The New Stack](https://thenewstack.io/nvidia-open-sources-kai-scheduler-to-help-ai-teams-optimize-gpu-utilization/)); ScaleOps raised $130M (Series C, Mar 2026, [S] [TechCrunch](https://techcrunch.com/2026/03/30/scaleops-130m-series-c-kubernetes-efficiency-ai-demand-funding/)) | Enterprises running GPU clusters; subscription | **Yes, far:** the open scheduler covers queues, fairness, bin-packing and GPU sharing | the incumbent GPU vendor (owner of the free tool) | **No:** the free tool is the vendor's own |
| GPU sharing, multi-tenancy | Bundled: time-slicing in the vendor's operator; sharing is a feature of the open scheduler | | vendor-supplied | same | No |
| Utilisation and cost visibility | A vendor survey of 23,000 Kubernetes clusters reports **5% average GPU use** (CAST AI, [S] [IT Brief](https://itbrief.news/story/cast-ai-report-finds-5-gpu-use-in-kubernetes-clusters)); a 2026 FinOps survey reports GPU spend as the top concern ([S] [ecorpit](https://ecorpit.com/gpu-spend-finops-top-concern-2026/)); Kubecost sits inside IBM (**price UNKNOWN**) | FinOps and platform teams; subscription | OpenCost (open source) | several cost tools; no clear leader | **Moderate:** a measurement and report tool is buildable; the evidence of payment is vendor-sourced |
| Serving and inference platforms | Modal: $750M Series D at $15.75B reported, run rate above $1B in one report and $300M in a tear sheet (**conflict**); Fireworks: $1.505B round at $17.5B, "$1B+ ARR" company statement; Baseten: reported talks at $26B; Together: $800M round, details garbled ([S] [AI Weekly](https://aiweekly.co/alerts/modal-closes-750m-series-d-led-by-accel-at-1575b-valuation-crosses-1b-arr), [S] [ValueAdd](https://valueaddvc.com/blog/fireworks-ai-valuation-2026-17-5b-series-d-and-the-1b-arr-inference-business), [S] [Runtime Wire](https://runtimewire.com/article/modal-baseten-funding-talks-inference-valuations)) | Developers and companies; **per-token and per-second usage pricing** | the open serving engines | the funded platforms above | **No as a business** (it sells capacity and needs GPUs and capital); thin tooling on top is possible |
| Reliability and failure recovery | Cloud providers build it into their clusters (automatic repair, health checks, replacement in under five minutes by one vendor's claim; [S] [Together](https://together.ai/blog/auto-repair-for-together-gpu-clusters), [S] [Crusoe](https://www.crusoe.ai/resources/blog/autoclusters-minimizing-hardware-failures-in-large-gpu-clusters)). **No funded independent product found** | Operators of large clusters | open tools from Microsoft and Oracle, and a vendor tool ([S] [Rafay](https://rafay.co/ai-and-cloud-native-blog/automated-gpu-health-monitoring-with-nvidia-nvsentinel-on-the-rafay-platform)) | the clouds themselves | No |
| GPU brokerage and marketplaces | RunPod says its recurring revenue passed **$325M** (13 Oct 2026), from $120M in January, with 1.2 million developers ([S] [CityBiz, relaying the company release](https://www.citybiz.co/?p=917605); **DERIVED: 2.7x in nine months**); Lambda estimated at $520M or $760M (**conflict**, THIRD-PARTY); a marketplace's revenue estimated at $2.2M (weak) | Developers; hourly price | none | RunPod, Lambda | **No** (needs supply and capital) |
| On-premises deployment and support | **None found** beyond vendor blogs | Regulated enterprises | | | UNKNOWN |
| Data-centre power software | Emerald AI: $150M Series A at $1.05B (Aug 2026), $25M earlier; it slows or moves jobs when the grid asks; deployed at a pilot; **the main proof so far is one three-hour test on 256 chips** (analysts, [S] [Mercom](https://mercomindia.com/emerald-ai-raises-150-million-series-a-funding-at-1-05-billion-valuation), [S] [Fortune](https://www.fortune.com/2026/03/31/emerald-ai-nvidia-fast-pass-data-center-grid-connects)) | Data-centre operators and utilities | none | early | No |
| Software for hardware makers | See [item 7](research_04_chip_software.md): strong for whole-team acquisitions; **none** for small outside teams | Chip makers | open engines | vendors in-house | Partly |
| Developer workflow tools | A workflow-tool company acquired by a GPU cloud for about $1.7B, as stated in the cloud's own news list (the full release was not opened; [P] [CoreWeave news](https://www.coreweave.com/news)) | Teams training models | | | No |

**Reading (DERIVED):** the categories with real money (serving platforms, brokerage) sell **capacity** and need capital; the categories a small team could build (cost visibility, measurement) have the weakest evidence of payment and free alternatives; orchestration is owned by a free vendor tool. The strongest evidence of any kind is serving and brokerage revenue, and those are exactly where a laptop team cannot compete.

## Who decides and how they buy

| category | who pays | how | evidence |
|---|---|---|---|
| Serving and brokerage | developers, startups, companies | self-serve card, per-use | RunPod's developer count and price pages ([Research 03](research_03_pain.md)) |
| Orchestration, cost visibility | platform and finance teams | enterprise sales | vendor reports only |
| Power software | operators with utilities | pilots, no standard contract (as of late June 2026 no standardised binding utility–data-centre agreement existed, [S]) | one source |
| India's GPU access | startups and researchers by application | committee approval; see [India](research_04_india.md) | primary |

## Cheapest experiments (proposals, none run)

- **Cost visibility:** build a one-page report from a GPU owner's own metrics and see whether any of ten teams would pay or at least send real data. Kill if none send data.
- **Software for hardware makers:** see item 7.

Related: [Research 04 summary](research_04_summary.md), [Item 7](research_04_chip_software.md), [India](research_04_india.md), [Research 02 buyers](research_02_buyers.md), [Reviews index](README.md)
