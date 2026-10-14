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
timing repair and reports with global-route parasitics). Logs: `flow.log`, `resume.log`.
No detailed routing, one corner (typical, 1.8 V, 25 C), `cortex.sdc` = 20 ns clock.

| Quantity | Value | Note |
|---|---|---|
| Die | 6.45 x 4.80 mm = 31.0 mm^2 | macros spread out with channels; not area-optimised |
| Cell + macro area | 19.4 mm^2 (63% utilisation) | 14,487 buffers added by fanout repair |
| Setup, worst slack | -2.96 ns at 20 ns | **~43 MHz** achievable as is (period ~23 ns) |
| Hold, worst slack | +0.13 ns | met |
| Clock skew | 3.4 ns (latency 8.6-12.0 ns) | large die, one clock tree to 63 macros; the main cause of the setup miss |
| Power, logic only | 355 mW at 50 MHz | 10% switching on every net (a default, not a measured activity); SRAM macros report 0 (their library has no power data) |

Reading, honestly:
- **Speed is fine for the job**: at ~43 MHz a decision (~1,600 cycles) takes ~37 us and a learned example a few ms;
  the FPGA runs the same design at 27 MHz.
- **The power figure contradicts the operation-count energy estimate and must not be hidden.** 355 mW x 37 us is
  ~13 uJ per decision, against 9.4 nJ counted from the operations a decision needs
  ([energy estimate](cortex_energy_estimate.md)). The gap is overhead the operation count leaves out: the clock tree and
  ~20,000 flip-flops (the encoder's small memories) toggling every cycle, every net assumed to switch 10% of the time,
  and no clock gating or idle power-down. 87% of it is in combinational cells, most of them the inserted buffers.
- So the ~74x energy claim is about the work a decision needs, not about this unoptimised layout. Closing the gap
  needs: the encoder's flip-flop memories moved into SRAM (step 1 below), clock gating so idle blocks do not toggle,
  and a real switching activity from simulation (a VCD of a decision) instead of the 10% default. Until then, quote
  the layout power as an upper bound for an unoptimised design.

## Next steps for a real chip (months 7-8)

1. Put the encoder's small memories (image, receptor map, code map) into small SRAM macros instead of flip-flops.
2. Clock gating and a power estimate from a simulated switching activity (VCD) instead of the 10% default.
3. Detailed routing and a smaller die once 1-2 are done (placement and global routing: done, above).
4. Pad ring and multi-corner checks only if fabrication is ever planned (not in scope now).

Related: [Month 3 results](cortex_month3.md), [Energy estimate](cortex_energy_estimate.md), [Results index](INDEX.md)
