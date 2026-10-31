---
title: Wafer-scale price research prompt - what we plan to build and which prices to find (31 Oct 2026)
tags: [spark, gpu, wafer, cost, research, prompt]
---

# Wafer-scale price research (31 Oct 2026)

Give this whole page to whoever researches (you, or another assistant). Every number found must be labelled with its source and kind: QUOTE (a supplier wrote it to us), PUBLISHED (a public price list or paper), THIRD-PARTY ESTIMATE, or UNKNOWN. Do not fill a gap with a guess; write UNKNOWN.

## What we plan to build (MODELLED design, nothing built)

- A **wafer-scale inference accelerator**: one whole 300 mm wafer (about 46,000 mm2 usable, like the Cerebras WSE class) of mostly on-chip SRAM, no external memory.
- **Process node:** N5-class (5 nm) assumed. Alternatives worth pricing: N7, N6, 12/16 nm (cheaper wafer, less SRAM per mm2).
- **Layout:** about 80% of the area SRAM (about 108 GB per wafer at 4-bit-weight use), 20% compute and routing; the wafer is a mesh of small tiles (about 4 MB SRAM and a 256 MAC-per-cycle INT8 engine per tile), with spare tiles routed around defects. The RTL tile exists and is synthesised on an open 130 nm library only.
- **Target workload:** existing large language models (70B dense up to 1T mixture-of-experts) at 4-bit and 8-bit, decode at small batch, many wafers per model (1T model: about 5 wafers).
- **Power:** about 7.6 kW per wafer system (modelled; Cerebras CS-3 is cited at 23 kW), liquid cooled.

## What our model uses today, and how weak each number is

| item | value in model | status |
|---|---|---|
| N5 300 mm wafer | about $18,500 | third-party estimates |
| Cerebras CS-3 system | $2-3 million | third-party estimate, no published price |
| our wafer system hardware (power delivery, cold plate, packaging, test) | $150,000 | **ASSUMED, no source; the largest unknown** |
| break-even price for our cost bar | about $214,000 per wafer system (central), lower in the worst corner | derived |

## What to find (priority order)

1. **Whole-system price of a wafer-scale machine** that is not Cerebras's list price: any quote, filing, teardown or analyst breakdown (bill of materials) of power delivery, cold plate, packaging, test, chassis. Ask: is $150,000 plausible, and what is the real range?
2. **Foundry access for a wafer-scale part:** does any foundry (TSMC and others) allow a whole-wafer die, who has done it, with what stitching or interconnect method, and what the NRE, mask-set and minimum-order cost is. Ask whether a startup can get access at all, and through which route (shuttle, a design-services company, a partner).
3. **Mask-set and NRE costs** at N5, N7, 12/16 nm, and the price of a wafer at each, for a small-volume customer (not a hyperscaler).
4. **Yield and redundancy:** published defect density, the spare-tile fraction wafer-scale vendors use, and how defective tiles are routed around; clustered defects and edge loss.
5. **Wafer-scale packaging and cooling suppliers:** power delivery to a 46,000 mm2 die (voltage, current, plane design), cold-plate makers, test sockets, and what each costs per unit at 10, 100 and 1,000 units.
6. **Embedded SRAM macros:** is a licensed SRAM compiler for N5 or N7 available to a startup, at what licence price, and the published energy per bit and area per Mbit (our model uses 0.55 pJ/bit and 420 mm2 per GB).
7. **Alternatives that avoid a whole wafer:** several large chiplets on one interposer or panel; compare price against the whole wafer.
8. **Who buys and at what price per token:** public prices for hosted inference on wafer-scale systems versus GPU clouds, to fix the selling-price target.

## Output wanted

A table: item, value or range, label (QUOTE / PUBLISHED / THIRD-PARTY ESTIMATE / UNKNOWN), source link, date of the source, and a one-line note on how sure you are. Send the table back; the cost model will be re-run with these values and the result recorded with the same labels. Contact requests to suppliers are listed in [manufacturing data requests](manufacturing_data_requests.md).

Related: [Manufacturing data requests](manufacturing_data_requests.md), [Own GPU charter](own_gpu_charter.md), [Step 5 result](../new_start/step5_worst_case_result.md), [Step 3 result](../new_start/step3_cost_power_result.md), [Docs index](INDEX.md)
