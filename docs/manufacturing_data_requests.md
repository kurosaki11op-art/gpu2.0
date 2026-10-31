---
title: Data and quotes to obtain before manufacturing - the figures the models still assume (31 Oct 2026)
tags: [spark, manufacturing, quotes, data-request, row-i, checklist]
---

# Figures to obtain before manufacturing (31 Oct 2026)

Founder: row I (cost) is left for manufacturing time. This is the checklist of what the cost, energy and capacity models still **assume**, each with the exact thing to ask for, who can answer, and which model result it decides. Nothing here is a result.

| # | what to obtain | who can answer | why it matters (model result it decides) |
|---|---|---|---|
| 1 | **Package cost** for a flip-chip package of an 800 mm2 die (organic substrate, about 11 W, no HBM, no interposer), at 10,000, 100,000 and 1,000,000 units; assembly yield | OSAT or substrate vendors (quote request) | The model assumes about $60 of a $150 per-chip figure; central cost advantage 2.7x at $480 per chip, 2x only up to about $650 ([step 15](../new_start/step15_packaged_cost_result.md)) |
| 2 | **Board cost per chip** (a board of 8 to 16 such chips, connectors, mechanical share) and **power regulation** for 11 W per chip (about 1 V, about 11 A) | board manufacturers; regulator vendors | about $40 and $20 assumed; same decision |
| 3 | **Cooling** for an 11 W chip: heat spreader and air path versus a cold plate; rack-level cost per kW | chassis and cooling vendors | about $30 assumed |
| 4 | **Wafer price and defect density** for the chosen node (5 nm today at $16,000 to $21,300 as third-party estimates), and **SRAM repair** (row and column redundancy) yield | foundry or a multi-project wafer broker; foundry design rules | decides $336 against $635 per 800 mm2 die (85% against 45% yield) |
| 5 | **SRAM macro data** at the chosen node: area per bit, read energy per bit, access time, standby power, for banks of 16 KB to 1 MB | foundry memory compiler datasheets (under agreement) | replaces the single cited 3 nm datapoint behind 0.55 pJ/bit; the energy bar holds up to about 1.0 pJ/bit ([step 6](../new_start/step6_sram_energy_result.md)) |
| 6 | **Embedded MRAM macro data** (22 nm and the 14/12 nm variant): area per bit, **read** energy, access time, cost adder per wafer, endurance | foundry eMRAM offering; ISSCC or IEDM papers | the only memory candidate near the 4.2x density need; read energy and cost adder are missing ([memory study](../new_start/step11_memory_technology_study.md)) |
| 7 | **Design cost**: mask set, tape-out, IP licences (SRAM compiler, I/O), design team for a leading-node chip | foundry quotes; design-service companies | assumed $150M in the margin and volume arithmetic ([step 14](../new_start/step14_price_cut_result.md)) |
| 8 | **Nvidia-class price**: actual quotes for an H100-class or newer GPU and the host and network around it | cloud list prices; server resellers | the buyer-price advantage scales with this ([step 13](../new_start/step13_buyer_price_result.md)) |
| 9 | **GPU decode power** under load, measured on a datacentre GPU (idle and decode) | cloud instance, or published measurements | the laptop RTX 3050 measurement (43 W decoding, 13 W idle) is one device only |
| 10 | **A DRAM-PIM reference** (HBM-PIM or AiM): energy per bit, compute per chip, availability to a small company | memory vendors | the DRAM route fixes cost but is compute-starved; real numbers decide whether it is a path ([memory study](../new_start/step11_memory_technology_study.md)) |

**Order of effort:** items 1 to 3 together (one quote round gives the packaged cost), then item 5 (needed for any tape-out anyway), then 6. Items 7 and 8 need business inputs, not engineering. Measured energy on a small board (the USB meter, from 1 Nov 2026) covers a different question: the ESP32 energy per image of the L algorithm against the CNN ([procedure](../hw/mcu/README.md)).

Related: [Workload map](gpu_workload_map.md), [Row I price-cut test](../new_start/step14_price_cut_result.md), [Row I packaged cost](../new_start/step15_packaged_cost_result.md), [Status, 31 Oct 2026](status_31oct.md), [Docs index](INDEX.md)
