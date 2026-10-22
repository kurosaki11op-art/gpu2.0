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

## Night of 22-23 Oct: root cause of the well / latch-up errors, and what is still open

- **Root cause found (SIMULATED):** the flow never inserted filler cells, so every gap in a cell row left slivers of N-well (nwell.1, nwell.2a, hvi.5) and diffusion more than 15 um from a tap (LU.2/LU.3). After `filler_placement` (`fill.tcl`, 3.17 million fill cells) the magic DRC of tile 0_1 dropped from about 12,500 errors to 1,036, **all within 3 um of an SRAM macro** (thin LEF pin stand-in shapes for the macro, met3/met4 width and spacing; not the logic or routing). Outside the macros: **0 errors** on that tile. The other five tiles are being re-run on the final layout.
- **Control for the checker:** a row of real standard cells with a tap at each end is flagged exactly beyond 15 um from the taps, so the latch-up check is right.
- **Hold:** repair adds buffers (67 on the old layout: hold -0.21 -> +0.10 ns; before routing on the rebuilt layout: -0.31 -> +0.35 ns). The final flow does it before routing (`route6c.tcl`).
- **Tap spacing** changed from 14 to 13 um (`flow3_tapd.tcl`, `TAPD=13`) as the usual recipe for this process.
- **Antenna (OPEN, ESTIMATED):** OpenROAD `check_antennas` on the routed layout: 2,279 net violations and 2,611 pin violations out of 115,506 nets (2%). `repair_antennas` crashes in this OpenROAD build (segmentation fault in `GlobalRouter::addLocalConnections`, with and without `-iterations`), so antenna diodes are not inserted yet.
- **LVS (OPEN):** not run.
- **Environment note:** the container's disk allowance ran out once (about 30 GB); jobs writing at that moment crashed or wrote empty files. Large intermediate files are now deleted as soon as they are used.
- **Logical equivalence (SIMULATED, formal):** post-layout netlist (with hold and clock-tree buffers) vs the synthesised netlist, yosys `equiv_make`/`equiv_simple`/`equiv_induct` (`equiv_postpnr.ys`, `equiv_result.txt`): 77,330 equivalence points proven, 0 unproven. SRAM macros replaced by the same stand-in on both sides, tap/decap cells removed, clock-gate cell modelled by behaviour. Netlist-to-netlist, not a physical LVS.

Related: [Hardware index](../../../HARDWARE_INDEX.md), [ASIC estimate](../../../results/cortex_asic_estimate.md), [Journal](../../../../docs/journal.md)
