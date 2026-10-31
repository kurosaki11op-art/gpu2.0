---
title: The integrated chip in silicon terms - logic area, memories and a free memory saving (31 Oct 2026)
tags: [spark, chip, asic, area, estimate]
---

# Integrated chip, silicon-level estimate (31 Oct 2026)

First synthesis of the INTEGRATED chip (`l_cortex_deep`: cortex encoder with the fast detector option, cortex core inference build, dispatcher, four-engine L Deep, reject flag) for SkyWater 130 nm (`sky130_fd_sc_hd`, typical corner) with Yosys, memories left as separate memory blocks so they do not swamp the logic figures. Earlier ASIC work in [hw/asic](../asic/README.md) covered only the older Cortex core. **ESTIMATED: synthesis only, no placement or routing, no timing closure, no power run, not sign-off.** Scripts in the scratch folder only (`synth.ys`, `mem.ys` shown in the journal entry); the figures below are what they printed.

## Logic (synthesis, typical corner)

| item | value |
|---|---|
| logic area (all standard cells, memories excluded) | **185,602 um2 = 0.186 mm2** |
| cells | 19,735 |
| flip-flops | 2,765 (302 plain, 2,463 with enable; the enable flops are 74,000 um2, about 40% of the logic area) |
| XNOR and XOR cells | 2,331 + 774 (the detector matching: two templates per cycle, 4 channels) |

The logic is small: under 0.2 mm2 at 130 nm, no multiplier anywhere. Its biggest parts are the register state and the detector comparison.

## Memories (33 arrays found in the synthesised design; widths and depths as declared)

| memory | bits | kind |
|---|---|---|
| L Deep, 4 engines: code rows (80 x 1,152 each) | 368,640 | constants (a ROM or a loaded RAM) |
| L Deep, 4 engines: clause rows (80 x 500 each) | 160,000 | constants |
| L Deep, 4 engines: clause headers (about 19 x 500 each) | 37,500 | constants |
| L Deep, 4 engines: literals, **as built before the fix** (14 x 8,192 each) | 458,752 | constants; the engines use only 3,192 to 3,480 literals each |
| L Deep, 4 engines: input-bit copies (6,176 each) | 24,704 | RAM |
| Cortex core: slow table (80 x 4,608) | 368,640 | RAM, loaded by SLOAD |
| Cortex core: list buffer (13 x 4,608), lanes, counts | 61,088 | RAM |
| encoder (templates, maps, pixels) + top pixel copy | 23,488 | RAM |
| **total as built before the fix** | **1,502,972 bits (188 KB)** | |

**Free saving found and applied:** the literal memories were declared 8,192 deep per engine; the engines hold at most 3,480 literals, so they are now 4,096 deep (`NLITS_E`, `ldeep_core_p.v`), 4 x 57,344 bits instead of 4 x 114,688: **229,376 bits fewer, 1,273,596 bits (159 KB) in total, 15% less memory**, with the same function (the regression below confirms it).

## What this means in area (ESTIMATED, assumptions stated)

- **SkyWater 130 nm with the open OpenRAM macros (2 KB in 0.285 mm2, about 57 kbit per mm2):** the 1.27 Mbit would need about 22 mm2 of memory against 0.19 mm2 of logic: memory is 99% of the die, as the earlier Cortex estimate found ([Cortex ASIC estimate](cortex_asic_estimate.md): 95%). The constants would be loaded into RAM at start-up, because no ROM macro exists in the open flow.
- **A dense modern node (the project's [SRAM cost model](sram_area_cost_model.md), N5 macro density about 31.8 Mbit per mm2 before overhead):** the 1.27 Mbit is about 0.04 mm2 plus overhead; the logic at 5 nm is a small fraction of a mm2 (a 130 nm to 5 nm logic shrink of 100 to 300 times is an assumption). The whole recognition chip is then a few hundredths of a square millimetre, and cost per die is not the issue: the fixed cost of making any chip is.

## What is still missing for a real chip estimate

Placement and routing with timing closure, a power run with real switching activity (the energy figures in the [cascade demo](cascade_demo.md) are still operation counts), ROM or loadable-memory choice for the constants, memory-macro energy per read, and clock gating. The next chip step is a placed and routed run of this synthesis.

Related: [Cortex ASIC estimate](cortex_asic_estimate.md), [L Deep build](l_deep_build.md), [SRAM area and cost model](sram_area_cost_model.md), [Cascade demo](cascade_demo.md), [Results index](INDEX.md)
