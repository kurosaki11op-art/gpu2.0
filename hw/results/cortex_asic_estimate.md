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
`python hw/rtl/cortex/run_check_cortex.py DATA_DIR --asic` -> RESULT_ASIC_CHECK

## Area (synthesis, typical corner, before place and route)

| Part | Count | Area |
|---|---|---|
| OpenRAM 2 KB SRAM macros (32 x 512) for table, dream counts, list buffer | 63 | ~17.9 mm^2 (0.285 mm^2 each) |
| Standard cells (logic + 20,351 flip-flops, mostly the encoder's small memories) | 69,870 | ~0.84 mm^2 |
| **Total** | | **~18.8 mm^2** |

Reading: the brain logic itself is under 1 mm^2. Memory is ~95% of the area, and these open-source macros are large
for what they store (2 KB in 0.285 mm^2); commercial 130 nm SRAM is several times denser, and a newer process far more.
The 84 KB of real memory would be a few mm^2 at most with a dense SRAM compiler.

## Timing and power: not yet meaningful

OpenSTA on the synthesized netlist reports the worst path missing a 20 ns clock by 218 ns, because unbuffered
flip-flops drive thousands of inputs (a 44 ns clock-to-output on one register). Buffer trees are inserted during
place and route, which has not been run for this design. For the same reason the power figure from this netlist
(230 mW at 50 MHz, 10% activity, SRAM macros not counted) is not a result. Use the operation-count estimate in
[energy estimate](cortex_energy_estimate.md) until place and route is done.

## Next steps for a real chip (months 7-8)

1. Put the encoder's small memories (image, receptor map, code map) into small SRAM macros instead of flip-flops.
2. Place and route with OpenROAD (Phase A's `hw/asic/pnr/flow.tcl` as the template), with high-fanout repair, then
   timing and power with parasitics.
3. Pad ring and multi-corner checks only if fabrication is ever planned (not in scope now).

Related: [Month 3 results](cortex_month3.md), [Energy estimate](cortex_energy_estimate.md), [Results index](INDEX.md)
