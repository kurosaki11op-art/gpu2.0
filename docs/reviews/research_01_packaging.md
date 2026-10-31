---
title: Research 01 - packaging, power and cooling (31 Oct 2026)
tags: [spark, review, research, packaging, power, cooling, competitors]
---

# Research 01: packaging, power and cooling

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026.

## What and why

| machine | package | power | cooling | label and source |
|---|---|---|---|---|
| Rubin GPU and rack | Two dies on TSMC 3 nm, 8 HBM4 stacks, CoWoS-class | about 1.8 kW per GPU; rack about 166 to 230 kW (sources conflict) | Direct liquid | VENDOR and THIRD-PARTY, [S] [guide](https://www.spheron.network/blog/nvidia-vera-rubin-nvl72-guide/), [S] [breakdown](https://hashrateindex.com/blog/nvidia-vera-rubin-nvl72-specs-breakdown/) |
| Next Rubin rack | | about 600 kW expected in 2027; GPU count conflicts | Liquid | THIRD-PARTY, [S] same |
| Cerebras CS-3 | Whole wafer | about 23 kW per system | Water to the processor | [P] [S-1](https://www.sec.gov/Archives/edgar/data/2021728/000162828026025762/cerebras-sx1april2026.htm) for cooling; power cited by [P] [SemiAnalysis](https://newsletter.semianalysis.com/p/cerebrass-next-generation-cs-4-fast) |
| Cerebras CS-4 | Same 5 nm wafer, higher clock | 125 to 135 kW per 3-wafer rack: about 42 to 45 kW per wafer (DERIVED) | Liquid | THIRD-PARTY, same. SemiAnalysis's author finds at best a slight gain in performance per watt, against a vendor claim of up to 10x throughput per watt |
| Tenstorrent QuietBox | 4 cards | 300 W per chip; 1,650 W supply | Liquid in a workstation | MEASURED and vendor, [P] [Register](https://www.theregister.com/on-prem/2025/11/27/blackhole-quietbox-tenstorrents-ai-workstation-reviewed/2113269) |

**Why:** they run hot because customers pay for speed and because memory and compute must be close. Silicon power density is a choice, driven by clock.

## Cost, and is it the cheap way?

- **Rubin rack:** about $7.8M (Morgan Stanley) or $9.1M (Bernstein); one much lower report at $3 to 4M. THIRD-PARTY, [S] [relay](https://www.digitalcitizen.life/nvidias-vera-rubin-ai-rack-may-cost-7-8-million-as-memory-prices-surge/). UBS's manufacturing estimate is $38,902 for a superchip, $24,297 of it memory ([S] [TechNews](https://technews.tw/2026/09/07/ubs-disassembles-the-vera-rubin-platform-cost/)).
- **Cerebras system price:** UNKNOWN; not stated in the S-1 text read. DERIVED hint: SemiAnalysis's "over $20M" for about 20 "systems" implies about $1M each, with the unit unclear.
- **DERIVED: test of the $150,000 wafer system.** Cerebras's 2025 hardware gross margin is about 42.9% (hardware revenue $358.4M, cost $204.7M, PUBLISHED, S-1). If a system sells for $1M to $2.5M, its cost of revenue would be about **$570,000 to $1.43M, about 3x to 8x the project's $168,687 bottom-up figure.** Cost of revenue contains more than the bill of materials, and Cerebras buys at low volume, so this does not give a true bottom-up number. But the project's wafer-system figure now has evidence against it and none for it.

## Checks on this project's numbers

| project figure | public comparison | reading |
|---|---|---|
| 7.6 kW per wafer | CS-3 23 kW; CS-4 about 43 kW | 3x to 6x lower than shipping wafers with less SRAM and more compute. Possible only with far less compute activity; it should be justified from an area and activity budget. **Treat as unsupported** |
| 11 W per 800 mm2 chip, no cold plate | A low-activity estimate; no comparable part found | Peak, not average, sets the cooling and regulator design |
| Air-cooled room | Rubin needs liquid and about 200 kW per rack | A real gap for smaller buyers: an air-cooled, low-power box |

## Flaw, and what stops copying

**The flaw is that power-hungry rack systems exclude many buildings and buyers.** A newcomer's cheapest fix is low clock, low voltage and modest scale on an ordinary PCIe card. Incumbents could ship one, and Tenstorrent, Qualcomm and others already sell or announce products near it, so this is a market position, not a technical moat.

## What they cannot do

Top-end racks cannot go into ordinary rooms. Facility readiness and lead time for power are UNKNOWN from the sources read; data-centre operators could answer. Wafer-scale packaging and power delivery details are not public: UNKNOWN; only Cerebras and its suppliers can answer.

Related: [Research summary](research_01_summary.md), [Interconnect](research_01_interconnect.md), [Wafer price research prompt](../wafer_price_research_prompt.md), [Reviews index](README.md)
