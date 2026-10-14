---
title: SPARK Cortex ASIC estimate (SKY130)
tags: [spark, cortex, results, asic]
---

# SPARK Cortex as a real chip: SkyWater 130 nm estimate (ESTIMATED, no fabrication)

What the whole design (sensory encoder + learning core + UART) would take in the open SkyWater 130 nm process, using
the open-source flow from Phase A. Files: `hw/asic/cortex/` (`synth.ys`, `synth_stat.txt`, `sta.tcl`, `sta_report.txt`).
The core's big memories become OpenRAM SRAM macros through a build option (`CORTEX_ASIC` in `cortex_core.v`).

## Verification with the SRAM macros

The core built with the OpenRAM macro simulation models instead of FPGA RAMs:
`python hw/rtl/cortex/run_check_cortex.py DATA_DIR --asic --small` -> **0 mismatches** over 4,752 + 4,810 compared
lines (predictions, update flags, dream lengths, full memories), two configurations, halving exercised (18 minutes of
simulation; the full-length scenario passes on the FPGA build).

## Area (synthesis, typical corner, before place and route)

| Part | Count | Area |
|---|---|---|
| OpenRAM 2 KB SRAM macros (32 x 512) for table, dream counts, list buffer | 63 | ~17.9 mm^2 (0.285 mm^2 each) |
| Standard cells (logic + 20,351 flip-flops, mostly the encoder's small memories) | 69,870 | ~0.84 mm^2 |
| **Total** | | **~18.8 mm^2** |

Reading: the brain logic itself is under 1 mm^2. Memory is ~95% of the area, and these open-source macros are large
for what they store (2 KB in 0.285 mm^2); commercial 130 nm SRAM is several times denser, and a newer process far more.
The 84 KB of real memory would be a few mm^2 at most with a dense SRAM compiler.

## Timing and power before layout: not meaningful

OpenSTA on the bare synthesized netlist reported the worst path missing a 20 ns clock by 218 ns (unbuffered flip-flops
drive thousands of inputs) and 230 mW. Both numbers were artefacts of the missing buffer trees and are superseded below.

## Placement, clock tree and global routing (OpenROAD, 15 Oct 2026; ESTIMATED, not sign-off)

Flow: `hw/asic/cortex/flow.tcl` (floorplan 6.45 x 4.80 mm, the 63 macros in an 8 x 8 grid with routing channels,
power grid, placement at 45% density, fanout repair, clock tree, setup/hold repair), then `resume.tcl` (global routing,
timing repair and reports with global-route parasitics). Logs of this (ungated) run: `ungated/flow.log`, `ungated/resume.log`.
No detailed routing, one corner (typical, 1.8 V, 25 C), `cortex.sdc` = 20 ns clock.

| Quantity | Value | Note |
|---|---|---|
| Die | 6.45 x 4.80 mm = 31.0 mm^2 | macros spread out with channels; not area-optimised |
| Cell + macro area | 19.4 mm^2 (63% utilisation) | 14,487 buffers added by fanout repair |
| Setup, worst slack | -2.96 ns at 20 ns | **~43 MHz** achievable as is (period ~23 ns) |
| Hold, worst slack | +0.13 ns | met |
| Clock skew | 3.4 ns (latency 8.6-12.0 ns) | large die, one clock tree to 63 macros; the main cause of the setup miss |
| Power | 355 mW at 50 MHz | 10% switching on every net (a default, not a measured activity); includes the SRAM macros (see the correction below) |

Reading, honestly:
- **Speed is fine for the job**: at ~43 MHz a decision (~1,600 cycles) takes ~37 us and a learned example a few ms;
  the FPGA runs the same design at 27 MHz.
- **The power figure contradicts the operation-count energy estimate and must not be hidden.** 355 mW x 37 us is
  ~13 uJ per decision, against 9.4 nJ counted from the operations a decision needs
  ([energy estimate](cortex_energy_estimate.md)). The gap is overhead the operation count leaves out: the clock tree and
  ~20,000 flip-flops (the encoder's small memories) toggling every cycle, every net assumed to switch 10% of the time,
  and no clock gating or idle power-down. (First reading; the breakdown below shows
  most of it is the SRAM macros clocked every cycle.)
- So the ~74x energy claim is about the work a decision needs, not about this unoptimised layout. Closing the gap
  needs: the encoder's flip-flop memories moved into SRAM (step 1 below), clock gating so idle blocks do not toggle,
  and a real switching activity from simulation (a VCD of a decision) instead of the 10% default. Until then, quote
  the layout power as an upper bound for an unoptimised design.

### Where the 355 mW goes (diagnosis, same night)

`power_probe.tcl` re-ran the power report on the clock-tree database with activity given only at the inputs and
propagated by OpenSTA through the logic, instead of 10% on every net:

| Activity | Total | Sequential | Combinational |
|---|---|---|---|
| 10% on every net (as above) | 352 mW | 45 mW | 308 mW |
| 10% at the inputs, propagated | 364 mW | 45 mW | 319 mW |
| 1% at the inputs, propagated | 338 mW | 41 mW | 297 mW |

Power hardly depends on what the data does: **~6 nJ is spent every clock cycle just clocking the chip**. Cell mix
(`cell_mix.tcl`, `cell_mix.txt`): 20,380 flip-flops (~17,200 of them the encoder's small memories: image 6,272, receptor
map 3,136, code map 4,608, detector signs 3,200), 25,579 clock-type buffers (clock tree plus buffers inserted by
fanout repair on a 6.45 mm die), 49,102 logic cells (much of it read multiplexers for those flip-flop memories).
So the fix is architectural, not a matter of a better activity number:
1. clock gating: the encoder idles while the core decides or dreams, and the whole chip idles between commands;
2. the encoder's flip-flop memories into SRAM (removes ~17,000 flip-flops and their read multiplexers);
3. a compact die (the macros are spread over 31 mm^2, so the clock tree is long).

**Correction (later the same night):** the 63 SRAM macros are not missing from the figure, as first written; OpenSTA
puts them in the combinational group. Their library charges 13.8 pJ per clock edge per port **whether or not the macro
is selected**, so the estimate pays for all 63 macros every cycle, although a decision touches a few at a time.

### First fix: clock gating, step by step

1. Encoder memories on gated clocks (`cortex_cg`, 4 sky130 clock-gating cells; bit-exact). Layout re-run
   (`gated_enc/flow.log`): ~43 MHz (setup -3.02 ns at 20 ns), hold -0.44 ns before routing. OpenSTA assumes a gated
   clock still runs every cycle and ignores pin activities on clock nets, so the gated clocks were declared as
   generated clocks running 1 cycle in 1,000 (`power_gated.tcl`, the encoder idles while the core decides):
   366 -> **242 mW**. Breakdown (`gated_enc/power_by_cell.txt`): SRAM macros 175 mW (72%), clock buffers ~45 mW,
   flip-flops ~10 mW, everything else < 15 mW.
2. Every SRAM port clock gated by its own select (`sram_array` in `hw/asic/spark_mem_sky130.v`; 126 more gates, 130
   in all): only the bank a cycle reads or writes gets a clock edge. Core with the SRAM macro models still bit-exact
   (`check_core_asic_gated.log`). Layout re-run (`gated_all/flow.log`): ~42 MHz (setup -3.71 ns at 20 ns), hold
   -0.68 ns before routing (needs hold repair after routing). Power (`gated_all/`), SRAM read ports modelled at 1
   cycle in 9 (each array's reads go to one of its 9 banks), other gated clocks 1 in 1,000:

| Build | 10% activity | 1% activity |
|---|---|---|
| no gating | 366 mW | 350 mW |
| encoder gated | 242 mW | - |
| encoder + every SRAM port gated | **77 mW** | **62 mW** |

   Breakdown at 10% (`gated_all/power_by_cell.txt`): clock-tree and large buffers ~45 mW, SRAM 10.9 mW (from 175),
   flip-flops ~8 mW, logic < 15 mW.

**What a decision costs in this layout (ESTIMATED):** 62-77 mW at 50 MHz is 1.2-1.5 nJ per clock cycle; a decision
takes ~1,600 cycles, so **~2.0-2.5 uJ per decision**, down from ~11 uJ without gating. That is still ~200x above the
9.4 nJ counted from operations. What remains is mostly the clock tree of a 31 mm^2 die whose 63 macros are spread
out with routing channels, plus ~3,000 flip-flops that are clocked every cycle. Clock-tree synthesis inserted 13,838 clock buffers
(10,776 of them the largest size) for 4,325 sinks on the main clock and 17,216 behind the encoder's gates; tuning it
(smaller buffers, wider sink clusters) is the first lever. Next levers, not yet tried: a compact
die (macros abutted; the clock tree shrinks with it), gating the core's own registers while it waits, and fewer
cycles per decision. There is no layout of the comparison network on the same process, so the 74x ratio between
the two designs remains an operation-count comparison only.

## Next steps for a real chip (months 7-8)

1. Put the encoder's small memories (image, receptor map, code map) into small SRAM macros instead of flip-flops.
2. Clock gating and a power estimate from a simulated switching activity (VCD) instead of the 10% default.
3. Detailed routing and a smaller die once 1-2 are done (placement and global routing: done, above).
4. Pad ring and multi-corner checks only if fabrication is ever planned (not in scope now).

Related: [Month 3 results](cortex_month3.md), [Energy estimate](cortex_energy_estimate.md), [Results index](INDEX.md)
