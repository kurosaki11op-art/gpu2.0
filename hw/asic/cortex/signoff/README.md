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
| Foundry-style DRC, magic `drc(full)`, 6 overlapping tiles, macro insides replaced by their LEF pins and obstructions (`drc_tile_example.tcl`) | **FAILS, cause not yet known.** The first tiling dropped the vias and produced 124,286 false minimum-area errors (retracted). With a correct tiling the minimum-area errors are gone, but about 153,000 errors remain on 5 of 6 tiles, almost all well and latch-up rules: 88,016 LU.3 (P-diffusion more than 15 um from an N-tap), 23,848 nwell.4, 22,421 hvi.5, 15,205 nwell.2a, 1,208 nwell.1; plus about 2,900 met3/met4 width and spacing near the macro corners (partly my stand-in shapes). Spread over the whole chip (96 of the 500 um bins) | SIMULATED |
| DRC control (`drc_control.tcl`: two met1 wires 0.1 um apart) | magic flags 2 errors, so the checker works | |

Two things to know:
- The first full-chip DRC run reported 0 because magic's check is lazy; it needs `drc catchup`. That "0" was wrong and is retracted.
- The first tiling used a clip that dropped the via layer, so every routed stub looked too small (met1.6 minimum area, 114,801 errors). That was my mistake, not the layout. The OpenRAM macros hold about 416 million shapes each (63 of them), which is why the full check could not finish; they are replaced by their LEF pins and obstructions, so the macro insides are NOT checked.
- The well and latch-up errors are not explained yet. The layout has 366k tap cells (`tapcell -distance 14`) and the checker flags them anyway; candidates are my DEF-to-GDS conversion, the tap halo around the macros, or the checker setup. Next test: stream with magic's own DEF reader on a small block, and check one flagged spot by hand.

Related: [Hardware index](../../../HARDWARE_INDEX.md), [ASIC estimate](../../../results/cortex_asic_estimate.md), [Journal](../../../../docs/journal.md)
