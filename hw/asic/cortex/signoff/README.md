---
title: Pre-fabrication checks of the L Cortex layout (22 Oct 2026)
tags: [l, asic, signoff, drc]
---

# Pre-fabrication checks of the routed L Cortex layout (SKY130, SIMULATED / ESTIMATED, not signed off)

Rebuilt from scratch on 22 Oct 2026 in a fresh container (synthesis, placement, clock tree, detailed routing with the floor2g settings).

| Step | Result | Label |
|---|---|---|
| Synthesis | 18.80 mm2, 63 SRAM macros (same as before) | SIMULATED |
| Detailed routing (`route_floor2e_rerun.log`) | **0 violations** (router's own count; 73 min; 130k, 42k, 33k, 6.0k, 1.7k, 871, ... 0) | SIMULATED |
| GDSII export (`def2gds_pip.py`, KLayout) | 193 MB, 7.5 x 6.2 mm | |
| Timing at a 20 ns clock (`final_timing_power.log`, parasitics estimated from placement) | setup -6.19 ns (about 26 ns period, ~38 MHz), **hold -0.21 ns: FAILS, needs repair** | ESTIMATED |
| Power, gated clocks, 10% activity | about 55 mW | ESTIMATED |
| Foundry-style DRC, magic `drc(full)` (`drc_tile_example.tcl`, 6 overlapping tiles) | **124,286 unique errors: FAILS.** 114,801 met1 minimum area (met1.6), 6,912 met2 min area, 2,287 met3 min area, 206 met1 spacing, 48 met1 width, 24 met2 spacing, 7 met2 width, 1 met3 width; only 5 inside the SRAM macros | SIMULATED |
| DRC control (`drc_control.tcl`: two met1 wires 0.1 um apart) | magic flags 2 errors, so the checker works | |

Two things to know:
- The first full-chip DRC run reported 0 because magic's check is lazy; it needs `drc catchup`. That "0" was wrong and is retracted.
- The minimum-area errors sit on isolated met1 pieces of 0.355 x 0.14 um (0.05 um2, min 0.083) all over the logic area, not in the macros. Whether they come from the DEF-to-GDS conversion (KLayout draws vias from the LEF) or are real is **not yet known**. Next test: stream the layout with magic's own DEF reader (it builds vias from the technology's contact cells) and re-run the DRC.

Related: [Hardware index](../../../HARDWARE_INDEX.md), [ASIC estimate](../../../results/cortex_asic_estimate.md), [Journal](../../../../docs/journal.md)
