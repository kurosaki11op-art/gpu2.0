---
title: Research 02 - power, heat and water - system-level energy per prompt and what limits data-centre growth (1 Nov 2026)
tags: [spark, review, research, power, water, grid, energy-per-token]
---

# Research 02: power, heat, water

Labels and read depth as in [hardware](research_02_hardware.md). Accessed 1 Nov 2026. **The IEA, Gartner and LBNL pages returned access errors (403) to my fetch tool, so every national and global figure below comes from search summaries or the agencies' own news items surfaced by search [S]. Verify before use.**

## System-level energy per prompt (the best primary data)

| item | value | label |
|---|---|---|
| Google, median text prompt, May 2025 | **0.24 Wh**: accelerators 58% (0.14 Wh), host CPU and memory 25%, idle provisioned machines 10%, overhead 8% | MEASURED by the operator, arXiv [2508.15734](https://arxiv.org/html/2508.15734) [V] |
| Same, a narrower method (efficient machines only) | 0.10 Wh | same [V] |
| Energy per median prompt over one year | 33x lower, with 44x lower emissions | same [V]; includes software, hardware and model changes |
| GPU-only energy per token, B200, 32B dense model | 0.15 to 0.21 J (batch 512 to 128) | MEASURED, arXiv [2601.22076](https://arxiv.org/html/2601.22076v1) [V], from [Research 01 compute](research_01_compute.md) |
| Batch effect | 3x to 5x less energy per token, then a plateau | same |
| 405B-parameter training run, 16,000 H100s | 1% to 2% throughput swing by time of day from heat; load swings of tens of megawatts | PUBLISHED [V], see [hardware](research_02_hardware.md) |

**DERIVED:** 43% of the energy per prompt (25% host + 10% idle + 8% overhead, as printed; the shares sum to 101% from rounding) is outside the accelerator. A new accelerator that cuts accelerator energy by 7x cuts the prompt's energy by 2.0x (accelerator 0.14 Wh to 0.02 Wh; total 0.24 Wh to 0.12 Wh). This is the same arithmetic as in [Research 01 compute](research_01_compute.md).

## What limits growth

| item | value | label |
|---|---|---|
| Global data-centre electricity | About 415 TWh in 2024, rising to about 945 TWh by 2030 in the IEA base case; AI-optimised centres more than four times; about 12% per year growth since 2017; 2024 shares US 45%, China 25%, Europe 15%. The 415 figure and the "accelerated servers about half the increase" figure came from a third-party summary, not the agency's own page | THIRD-PARTY and PUBLISHED, [S] [IEA news item](https://www.iea.org/news/ai-is-set-to-drive-surging-electricity-demand-from-data-centres-while-offering-the-potential-to-transform-how-the-energy-sector-works) |
| US data-centre electricity | 58 TWh in 2014, 176 TWh in 2023; projected 325 to 580 TWh by 2028 | PUBLISHED, [S] [Berkeley Lab summary](https://newscenter.lbl.gov/2025/01/15/berkeley-lab-report-evaluates-increase-in-electricity-demand-from-data-centers/) |
| Gartner's 565 TWh for 2026 | Quoted in Jarvis's note via a trade site; **I could not open Gartner** | UNKNOWN |
| Grid queues | A Texas queue of about 474 GW of data-centre requests, "more than five times" the state's record peak; the grid operator delayed its review after the governor asked for an audit | THIRD-PARTY news, [S] [Utility Dive](https://www.utilitydive.com/news/texas-hits-pause-data-center-interconnections/827046/) |
| Construction and equipment | Of 16 GW targeted for 2026 only 5 GW had begun construction; power transformer lead times about 128 weeks | One source, [S] [mgrid](https://mgrid.org/2026/01/15/data-center-grid-delays-50-percent-2026-ai-capacity-risk/), unverified |
| Water | 211 billion gallons attributed to data-centre electricity use in 2023; cooling design sets the direct share; indirect water from power generation is separate | One foundation report, [S] [Water Foundation](https://waterfdn.org/wp-content/uploads/2026/07/Water-Data-Centers-2026.pdf). **The "17 billion gallons direct" figure I tried to confirm was not found** |

## Reading

- **The limit is delivery of power, not only its cost:** grid connection, transformers and permits. That is a constraint on racks of 100 kW and more, and little evidence says it constrains small, air-cooled deployments. This supports the [Research 01](research_01_packaging.md) observation that rack-scale power excludes some buyers; **demand from those buyers is UNKNOWN.**
- **Water** is the weakest-sourced item. No per-token water figure from a primary source was found: Google's paper reports one (0.26 mL per median prompt, [V] read as quoted in the abstract in Research 01's note), which is a single operator.
- **What a chip can change:** accelerator energy (58%), and the idle and host shares only if the chip or its software changes how many machines must be provisioned. Nobody in these sources showed that.

Related: [Research 02 summary](research_02_summary.md), [Hardware weaknesses](research_02_hardware.md), [Research 01 packaging](research_01_packaging.md), [Reviews index](README.md)
