---
title: Research - detailed routing of SKY130 with OpenRAM SRAM macros
date: 2026-10-15
tags: [research, asic, routing, openroad]
---
# Research: why detailed routing failed, and the fixes (15 Oct 2026)

**The failure.** OpenROAD (2022 build) detailed routing of the SPARK Cortex layout (63 OpenRAM
`sky130_sram_2kbyte_1rw1r_32x512_8` macros, 8 x 8 grid) left 100k-160k design-rule violations after the first pass and
converged far too slowly. Global routing reported almost no congestion, so the cause looked like setup, not capacity.

**What the reference flows do** (OpenROAD-flow-scripts sky130hd platform, as of March 2022 and today; OpenLane):
- Signals route on met1-met5 only: li1 is excluded (`MIN_ROUTING_LAYER = met1`; the 2022 scripts pass
  `detailed_route -bottom_routing_layer met1 -top_routing_layer met5`). Our run laid 1.49 m of wire on li1.
- Global route writes a guide file and reserves capacity: layer adjustment 0.3, more congestion iterations; detailed
  route reads the guide; OpenLane runs 64 passes with `-or_seed 42`.
- Clock on met3-met5.
- Sources: [ORFS sky130hd config](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/flow/platforms/sky130hd/config.mk),
  [fastroute.tcl](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/flow/platforms/sky130hd/fastroute.tcl),
  [OpenLane droute.tcl](https://github.com/The-OpenROAD-Project/OpenLane/blob/master/scripts/openroad/droute.tcl).

**Known problems with this SRAM macro:**
- Signal pins sit on met4 along the bottom edge (and met3 on the left), with the power ring just inside on met3/met4.
- Power straps that end too close to the macro short its met4 pins
  ([OpenLane #640](https://github.com/The-OpenROAD-Project/OpenLane/issues/640),
  [#2030](https://github.com/The-OpenROAD-Project/OpenLane/issues/2030)).
- Keep every pin edge facing a channel and avoid 90-degree rotation
  ([OpenLane OpenRAM tutorial](https://github.com/The-OpenROAD-Project/OpenLane/blob/master/docs/source/tutorials/openram.md)).

**Fixes, ranked:**
1. No li1 routing; use the guide; 64 passes, `or_seed 42`.
2. Layer adjustment 0.3; macro extension 2.
3. Power-grid halo 20 um around the macros.
4. All macros R0 with pin edges facing wide channels.
5. Halos / placement keep-outs at the pin edges.
6. Only then other seeds or a newer OpenROAD.

Tried: floor3 (logic moved into one central block) failed on hold timing; floor2b (old grid + fixes 1-3) running.
See [ASIC estimate](../hw/results/cortex_asic_estimate.md).

Related: [ASIC estimate](../hw/results/cortex_asic_estimate.md), [Research: few-shot](research_fewshot_class_incremental.md), [Project memory](PROJECT_MEMORY.md)
