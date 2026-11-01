---
title: Research 04 - India - government GPU compute programme, Indian GPU clouds, and chip startups (1 Nov 2026)
tags: [spark, review, research, india, indiaai, gpu-cloud, dli]
---

# Research 04: India

Labels and read depth as in [item 7](research_04_chip_software.md). **The government's press and scheme pages (PIB, MeitY) returned access errors to my tool, so the programme's scale and subsidy rate are secondary [S]. The compute portal itself loaded and is primary [V].** Accessed 1 Nov 2026.

## The government compute portal (primary)

Pages: [compute.indiaai.gov.in](https://compute.indiaai.gov.in/) and its [price calculator](https://compute.indiaai.gov.in/indiaaipricecalculator), both "last updated 14-10-2026" [V].

| item | what the page says (short quotes) |
|---|---|
| Purpose | "Making AI Compute, Network, Storage and Platform Services on Cloud Available at Affordable Rates" |
| Process | login with a government identity; request compute "with a draft Bill based on the rate list", including a subsidy request; approval by a committee (PMEC) |
| Approval | "If the requested GPU hours is less than 5000, the compute request is auto approved." Above that, committee approval. Requests are taken between the 1st and 25th of the month; the approved list is published on the 10th of the next month; "Approvals are valid for 30 calendar days" |
| Subsidy | "Max Subsidy (Max upto 40% subject to approval from IndiaAI)"; "users must bear additional costs beyond the subsidy"; prices exclude GST |
| Who is eligible | **Startups and small firms:** recognition by the industry-promotion department, AI/ML experience, and "annual revenue 50 lakh or funding of INR 100 lakh". **Early-stage startups:** four years of AI/ML experience and a letter from a senior officer. **Researchers:** an h-index of 5 or more, or papers in AI journals with impact factor above 2.5, or 150 citations. **Students:** AI/ML projects with an aligned academic profile, or a fellowship |
| Providers | About 15, seen in logo file names (summary, not verbatim): CMS, CtrlS, Cyfuture, E2E, Ishan, JPL, Locuz, NxtGen, NTT, Neysa, Orient, Sify, Tata Communications, Vensysco, Yotta. The empanelled-GPU list is a PDF whose text my tool could not read |

**Rate list, rupees per GPU-hour, as printed (on demand / 12-month reserved):** H100 (80 GB) 153.0 / 117.0; B200 290.7 / 251.1; B300 351.0 / 319.5; A100 135.9 / 81.0; L40S 67.5 / 45.0; L4 44.86 / 24.0; **AMD MI300X 168.2 / 148.0; MI325X 169.2 / 85.5; Intel Gaudi 3 153.0 / 117.0; Google TPU v6e 114.94 / 87.6**; about 90 rows in all, including AWS accelerators.

**DERIVED:** at the full 40% subsidy an on-demand H100 hour would cost about ₹92 (153.0 x 0.6); whether any user gets the maximum is not stated. **Blog claims of "₹65 per hour" or "₹150 per hour for startups" do not match the primary rate list** and I could not trace them to an official page.

**Scale:** about 38,000 GPUs in most 2026 secondary sources, 34,000 in one; a target of 100,000 by December 2026 ([S] [Tech Pillow](https://www.techpillow.co/blog/indiaai-mission-38000-gpus-shakti-cloud-compute-2026), [S] [ValueAdd](https://valueaddvc.com/blog/indias-ai-policy-2026-gpu-procurement-data-sovereignty-and-startup-support)). The first two tender rounds drew bids for 34,333 GPUs (a 2025 report, relayed). **No official count in what I read: UNKNOWN.** Who could answer: the IndiaAI portal operators; the PIB release I could not open.

**Observations (DERIVED):**
1. Under 5,000 GPU-hours the request is auto-approved. A small team can plausibly use this; 5,000 H100 hours at ₹153 is ₹7.65 lakh before subsidy (153 x 5,000).
2. The rate card lists **non-Nvidia accelerators at about the same price as an H100** (an AMD part ₹168, a Gaudi part ₹153). Someone must write software that runs on them; whether anyone is paid to do so is UNKNOWN.
3. Eligibility needs recognition, track record or revenue/funding: **a student with no company does not obviously qualify** except through the student routes.

## Indian GPU clouds

| item | value | label |
|---|---|---|
| E2E Networks, June 2026 quarter | Revenue about ₹156.76 crore, profit about ₹43.9 crore; about 5,100 GPUs after a B200 cluster went live; the company credits higher GPU utilisation | PUBLISHED by the company, relayed, [S] [Inc42](https://inc42.com/buzz/e2e-networks-reports-₹44-cr-profit-in-q1-revenue-zooms-3-3x-yoy/); company filings were in the results but I did not open them |
| E2E, the following quarter | Revenue ₹223.8 crore, up 411% | [S] one report |
| E2E, a large order | About ₹1,000 crore of Blackwell cloud GPUs for a sovereign-AI customer | [S] |
| Yotta, Neysa and others | Named as growing providers; **no revenue, utilisation or supply figures found** | [S] |
| What Indian GPU clouds say they lack | **Not found: UNKNOWN** | The providers could answer |

(E2E's own words on its constraints, and its filings, would answer the question; I did not reach them.)

## Indian chip startups

See [item 7](research_04_chip_software.md#india): the design-support scheme, its reported scale, and one edge-AI chip startup at silicon bring-up. What software they lack: **UNKNOWN**. This is the one question where one conversation beats more research.

## Corrections to the first-pass recollection

- "Scale of an Indian programme": the 38,000-GPU figure is secondary and one source says 34,000.
- The subsidy is **up to 40%** on a published rate list, not a fixed rupee rate.

Related: [Research 04 summary](research_04_summary.md), [Item 7](research_04_chip_software.md), [Research 04 categories](research_04_categories.md), [Reviews index](README.md)
