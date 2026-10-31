---
title: Research 01 summary - where a newcomer can and cannot beat Nvidia and Cerebras; gap table, wedges and honest negatives (31 Oct 2026)
tags: [spark, review, research, competitors, wedges, gaps]
---

# Research 01 summary (31 Oct 2026)

Assignment: [research task 01](../vision_research_task_01.md). Topic notes: [compute](research_01_compute.md), [memory](research_01_memory.md), [numeric formats](research_01_numerics.md), [interconnect](research_01_interconnect.md), [packaging, power and cooling](research_01_packaging.md), [software and lock-in](research_01_software.md), [pricing and buyers](research_01_pricing.md), [supply and funding](research_01_supply.md).

## The answer in brief

1. **The project's core idea is no longer open ground.** SRAM-resident decode ships at Cerebras, and Nvidia has absorbed Groq's version into its own platform in a deal reported at about $20B. A solo founder cannot win here on scale, money or software.
2. **The real weakness in SRAM machines is capacity,** and it is the same weakness in this project. Google authors call SRAM-only designs insufficient. Adding SRAM chips raises hops, cost and network needs.
3. **GPU cost per token is a moving target:** up to 2x in months from software and about 21x from one feature in one test. A fixed 2x to 7x hardware claim against today's GPU is not a durable basis.
4. **Measured system energy reduces the headline.** With Google's split, a 3.5x to 7.3x accelerator gain means about 1.7x to 2.0x per prompt (DERIVED).
5. **What is open to this founder is narrow:** independent measurement, small low-power parts, and measured old-node silicon. All have weak demand evidence. **No wedge below is proven.**

## Gap table

Sizes carry their labels; sources are in the topic notes. "Our design" means what exists today, not a plan. Bars are proposed, to be fixed by the founder and Jarvis before each test.

| # | gap | who has it | evidence | size | can our design address it? | test | proposed pre-registered bar |
|---|---|---|---|---|---|---|---|
| G1 | No public measured energy per token at a stated per-user speed across machines | All; InferenceX uses TDP | InferenceX states it; ML.ENERGY covers H100 and B200 only | Coverage gap, not a number | Not a chip question; our counters and RTX 3050 runs help | Predict J per token on the RTX 3050, then measure, on 3 models and 3 batch sizes | Prediction within 20% on at least 7 of 9 points; otherwise withdraw the tool idea |
| G2 | High per-user speed is expensive on GPUs | GPUs | About $0.56 at 50 and $4 at 125 tokens/s per user, one workload (MEASURED by SemiAnalysis, summary-level) | About 7x across that range | Only with striping, unsimulated; already occupied by Cerebras and LP30 | Simulate a striped 1B model with full traffic | Under 100 microseconds per token with mesh contention, and 2x better cost than LP30-class on sourced inputs. Low chance |
| G3 | Capacity on SRAM machines | Cerebras, LP30, **us** | 44 GB flat; 128 GB per LP30 rack; about 20 to 40 systems for 1.6T (THIRD-PARTY) | 162x less memory per rack than Rubin (DERIVED) | **No.** SRAM-only has this flaw | Scan SRAM plus Flash or DRAM tiers in step 5 for 70B and 1T | 1T model within 2x of HBM machine's chips, with 4x or better speed, on sourced figures |
| G4 | Racks do not fit ordinary rooms | Rubin, CS-4 | About 166 to 230 kW and 125 to 135 kW per rack (THIRD-PARTY) | About 12x to 23x an ordinary rack budget of about 10 kW (that budget is my assumption) | Possibly, for small models; 11 W chip is unsupported | Design a card for an 8B to 30B model; compare with a $1,399 p150 | At least 2x tokens per second per dollar and per watt, on the same model at FP8, with RTL-derived numbers |
| G5 | Low realised performance against peak | Everyone | 41% to 50% on Tenstorrent (MEASURED); utilisation under 60% in one 2023 cluster | 2x | Unclear: statically scheduled mapping may help; nothing shown | Measured utilisation of the tile at M3 on a real layer | At least 80% MAC busy over a full 1B-class layer, with memory stalls included |
| G6 | Poor public data on quality by format | All | One write-up: 1.5 to 2.4 points at 4 bits | 1 to 3 points | Yes, as measurement; M4-f | Per-format quality table on 3 model sizes on the RTX 3050 | Paired 95% intervals; INT4 within 1 point or the 4-bit figures are withdrawn |
| G7 | Software for one narrow family is achievable; general is not | Newcomers | AMD and Tenstorrent cases | UNKNOWN in money | Yes for one family (M4) | M4 on a real pretrained model | Existing M4 bars |
| G8 | A cheap, repeatable way to get measured silicon data | Students and small teams | India schemes; open shuttles | About ₹30 lakh (secondary) | Yes: tile through 180 nm | Apply; tape out one tile | Measured MAC and SRAM energy within 2x of scaled model, per charter M5 |

## Ranked wedges

None is validated. Ranking weighs founder's means first, then evidence. **All have demand "unknown" until someone pays.**

### 1. Independent inference cost and energy planner

- **Buyer:** neoclouds and enterprises sizing a purchase. **Pay now:** analyst subscriptions, consultants, or nothing.
- **Claim:** given a model, a per-user speed and a hardware list, predicts joules and cost per token to within 20%, with measured validation.
- **For:** a real, stated gap in the leading benchmark; uses what exists; needs no silicon or capital.
- **Against:** free academic data and SemiAnalysis's established position; our model has already needed heavy correction; may be a small market.
- **Kill test (about 2 to 3 weeks, no cost):** bar G1, then 10 buyer conversations. Kill if prediction fails, or fewer than 2 of 10 offer a paid pilot or a written request.

### 2. Tiny on-device recognition with a confidence flag (existing L Cortex)

- **Buyer:** embedded product makers. **Pay now:** small NPUs, microcontroller inference libraries.
- **Claim:** on a cheap microcontroller, about 30x faster than a small CNN with a confidence flag at similar accuracy (8.69 ms against 255.2 ms, project MEASURED on ESP32; accuracy 1 to 2 points lower).
- **For:** the only result here measured on real hardware. Works now as a library.
- **Against:** the founder has moved away from it; accuracy gap; small tasks only; I did not rerun it; market reports are not useful evidence; commercial demand UNKNOWN.
- **Kill test (about 2 weeks, one ESP32):** compare with a quantised microcontroller CNN from a standard toolchain, then offer it to 5 embedded makers. Kill if it is not 5x faster at equal accuracy (with flag), or none will pilot.

### 3. Measured tile and open simulator as a credential and research asset

- **Buyer:** grant bodies, academic and Indian design programmes, possibly later an employer or partner. **Pay now:** grants and salaries, not product prices.
- **Claim:** an open, bit-exact tile with measured energy that shows how to map one model family.
- **For:** a cheap ladder exists; finishes checklist items 3 and 4 of the [finish plan](../product_finish_plan.md); suits one person.
- **Against:** 180 nm says little about N5 energy; not a business by itself.
- **Kill test:** one application or enquiry to the DLI or ChipIN route. Kill if a student or new firm is not eligible and no open shuttle slot is available within 12 months.

### 4. Low-power PCIe card for small models in ordinary rooms

- **Buyer:** regulated or offline sites running 8B to 30B models. **Pay now:** one or two workstation GPUs, Tenstorrent cards, rented API.
- **Claim:** at least 2x tokens per second per dollar and watt in an air-cooled card.
- **For:** avoids CoWoS, HBM, a network and rack power. An 8B model at 4 bits, 4 GB plus cache, fits on about 3 to 4 of the project's chips (DERIVED).
- **Against:** at the project's unsourced $480 per chip that is about $1,500 to $1,900 before margin, against a $1,399 card already on sale. Needs at least $10M to reach N5. Crowded. Models keep growing. Buyer data is weak.
- **Kill test (a week, no cost):** bar G4 on paper using M3 RTL rates and a sourced package quote; 5 buyer conversations. Kill if under 2x on paper.

### 5. Weight tier using Flash or DRAM (research direction, not a product)

- **Buyer:** none yet; research only. **Claim:** tiered memory reduces chip count for large models.
- **For:** the strongest public expert view of where capacity will come from.
- **Against:** needs memory-vendor partnership; incumbents and Cerebras's reported roadmap head the same way; endurance and latency limits.
- **Kill test:** bar G3 in the existing model. Kill if it misses on sourced figures.

### Rejected, on this evidence

- **Wafer-scale system** (current [order of work](../gpu_deep_study_plan.md)): foundry access UNKNOWN; system cost likely several times the assumed $150,000; own power figure unsupported; capital far beyond the ladder. **I recommend the founder reconsider "wafer first".** It is the founder's decision.
- **Cheaper than Nvidia at data-centre scale:** cost is 1.35x central and 0.82x worst after corrections, on an old GPU baseline, and large buyers bundle finance.
- **Training, general CUDA-class compatibility:** evidence above.

## Honest negatives

**Do not try to beat:**

- **Nvidia:** rack-scale systems, supply, software depth, the speed of its software improvements, and finance-backed sales. It also now owns a decode path.
- **Cerebras:** ultra-fast decode that already ships. Its speed lead over GPUs is vendor-stated or estimated, but the sustained speed of about 1,700 tokens/s has third-party support. It has years of wafer-scale engineering and over $24B in reported backlog ([S] [secondary](https://www.mostlymetrics.com/p/cerebras-ipo-s1-breakdown)).

**Project claims and plans this research contradicts or weakens:**

| project statement | contradiction | source |
|---|---|---|
| SRAM-resident serving as the distinguishing design ([charter](../own_gpu_charter.md)) | Shipping at Cerebras and in Nvidia's platform; an expert view that SRAM-only is insufficient | [memory](research_01_memory.md) |
| Wafer system hardware $150,000, $168,687 bottom-up | S-1 margin plus a THIRD-PARTY price suggests cost of revenue 3x to 8x higher, with caveats | [packaging](research_01_packaging.md) |
| 7.6 kW per wafer | Shipping wafers 23 kW and about 43 kW | [packaging](research_01_packaging.md) |
| Energy 7x central, 3.5x worst | Accelerator only; 1.7x to 2.0x per prompt on Google's split | [compute](research_01_compute.md) |
| 0.5 microsecond chip links in a 630-chip system | 2 to 3 microseconds on a shipping wafer system | [interconnect](research_01_interconnect.md) |
| 4-bit as a project lever | GPUs already have FP4; quality loss reported | [numerics](research_01_numerics.md) |
| H100, $3,320 and $25,000 baseline | Rubin-generation costs and prices are several times higher, and throughput much higher; must be redone | [pricing](research_01_pricing.md) |
| "$150M assumed design cost" | Low-confidence $400M to $600M+ at 3 nm; rivals raising $230M to $700M rounds | [supply](research_01_supply.md) |
| A CUDA-class layer in the deep study plan | AMD's progress at far larger scale | [software](research_01_software.md) |

**In the project's favour:** memory and interconnect are indeed the primary challenges by expert view, not compute. HBM cost per GB rose while DDR's fell. SRAM avoids the CoWoS queue. The 10 pJ/bit link and 1.6 W/GB leakage assumptions look conservative.

## How far to trust this research

- **Read in part from primary sources:** the S-1 (first 118,000 characters: foundry, memory and software risk factors **not reached**), Ma and Patterson (first 6 pages), InferenceX pages (paywalled, chart values not visible), Chung et al. and Elsworth et al. (to about 60%), ServeTheHome, Next Platform, SemiAnalysis's CS-4 article (paywalled after the opening), The Register (about 70%).
- **Search summaries of secondary pages only:** marked [S] in the notes. This includes the Nvidia 10-K figures, most HBM and tape-out prices, and all India scheme figures. Several sites sell services or seem machine-written. Treat them as leads, not facts.
- **Not reached:** Artificial Analysis's own pages, MLCommons's results, Google's TPU papers, and AMD's filings. Intel Gaudi evidence was not found. Vendor manuals were not read, so how CUDA's execution model works is not reviewed here; it belongs in Jarvis's concept notes.
- **Not independently measured:** nothing in these notes was tested by me apart from arithmetic.
- **Dating:** the sources are fast-moving, and many date from 2026 reports I could not cross-check.

## Remaining UNKNOWNs, and who could answer

| question | who |
|---|---|
| Cerebras system price and bill of materials | Cerebras, its customers |
| Whole-wafer foundry terms for a startup | TSMC or another foundry |
| A buyer's cost to migrate from CUDA | Teams who have ported |
| Current fleet utilisation | Hyperscalers, large neoclouds |
| Packaging quote for an 800 mm2 die | OSATs ([data requests](../manufacturing_data_requests.md)) |
| Eligibility and real cost of India's MPW support | ChipIN Centre, the DLI scheme office |
| How smaller buyers decide | Direct interviews by the founder |

Related: [Research task](../vision_research_task_01.md), [Vision review 01](vision_review_01.md), [Jarvis response 01](jarvis_response_01.md), [Own GPU charter](../own_gpu_charter.md), [Deep study plan](../gpu_deep_study_plan.md), [Reviews index](README.md)
