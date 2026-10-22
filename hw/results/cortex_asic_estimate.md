---
title: L Cortex ASIC estimate (SKY130)
tags: [spark, cortex, results, asic]
---

# L Cortex as a real chip: SkyWater 130 nm estimate (ESTIMATED, no fabrication)

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
| encoder + every SRAM port gated | 77 mW | 62 mW |
| same, lighter clock tree (see 3.) | 47 mW | 33 mW |
| pipelined core, lighter clock tree (see 4.) | **49 mW** | **35 mW** |

   Breakdown at 10% (`gated_all/power_by_cell.txt`): clock-tree and large buffers ~45 mW, SRAM 10.9 mW (from 175),
   flip-flops ~8 mW, logic < 15 mW.

3. Lighter clock tree (`cts_light/`): root buffer clkbuf_8, tree buffers clkbuf_2 / clkbuf_4, 30 sinks per cluster
   (`CTS_ROOT`, `CTS_BUFS`, `CTS_CLUSTER` in `flow.tcl`): 47 mW at 10% activity, 33 mW at 1%. Setup unchanged
   (-3.71 ns at 20 ns, ~42 MHz); hold -1.34 ns before detailed routing (worse than the default tree's -0.68 ns; needs
   hold repair after routing, which adds delay cells and a little power).

4. Fewer cycles (`CORTEX_PIPE`, on in the ASIC build; bit-exact, also with the SRAM macro models): the score loop
   takes one code bit per cycle and dreams prefetch their counters. Cycles per decision 1,243 -> 264, per dream
   21,894 -> 7,109. Layout of this core with the lighter clock tree (`pipe_light/`): 49 mW at 10% activity, 35 mW
   at 1%; setup -5.10 ns at 20 ns (~40 MHz), hold -0.83 ns before routing.

**What a decision costs in this layout (ESTIMATED):** 33-47 mW at 50 MHz is 0.7-0.9 nJ per clock cycle; a decision
takes ~1,600 cycles (unpipelined), so ~1.1-1.5 uJ per decision (2.0-2.5 uJ with the default clock tree), down from ~11 uJ
without gating. **With the pipelined core: 0.70-0.98 nJ per cycle x 264 cycles = ~0.18-0.26 uJ per decision**
(ESTIMATED from its own layout), ~20-28x above the 9.4 nJ operation count. Per learned example (5-stage run, ~95% of it dreams):
~45-62 uJ on digits, ~27-38 uJ on clothing ([note](../brain/experiments/month4/energy_per_example_layout.md)). That is still ~100-150x above the 9.4 nJ counted from operations. What remains is mostly the clock tree of a 31 mm^2 die whose 63 macros are spread
out with routing channels, plus ~3,000 flip-flops that are clocked every cycle. Clock-tree synthesis inserted 13,838 clock buffers
(10,776 of them the largest size) for 4,325 sinks on the main clock and 17,216 behind the encoder's gates; tuning it
(smaller buffers, wider sink clusters) is the first lever. Next levers, not yet tried: a compact
die (macros abutted; the clock tree shrinks with it), gating the core's own registers while it waits, and fewer
cycles per decision. There is no layout of the comparison network on the same process, so the 74x ratio between
the two designs remains an operation-count comparison only.

### Detailed routing attempt (15 Oct, `route.tcl`, log `route_run1_lost.log`)

Detailed routing of the pipelined, clock-gated layout (OpenROAD TritonRoute) after hold repair (1,818 endpoints):
design-rule violations 160k after the first pass, 96k after the second, 72,435 after the third; the run was lost in a
container restart during the fourth. It was not converging toward zero at a useful rate, so it was not restarted:
the floorplan (63 macros in a grid with narrow channels, standard cells squeezed between them) needs rework - wider
channels or a block of standard cells beside the macro array - before detailed routing is worth running. The timing
and power figures above therefore remain global-route estimates.

Second attempt (`floor2/`: channels 250 / 300 um, 7.5 x 6.2 mm die, 42% utilisation; setup -4.41 ns, hold -0.36 ns
before routing): 103,658 violations after the first pass, ~65k at 60% of the second (first attempt: 160k, then 96k) -
better, still far from converging; lost in a second container restart. Detailed routing stays open: it needs a
floorplan with a dedicated standard-cell block and more routing layers reserved, and a run of many hours in a stable
environment.

### Detailed routing, solved to 25 violations (15-16 Oct, `flow3.tcl`, `route3.tcl`, `route4.tcl`, `floor2*/`, `diag/`)

What the five attempts showed (all ESTIMATED, OpenROAD 2022 build, SKY130, one corner):

| Run | Layout | Pass 1 | Pass 2 | Final |
|---|---|---|---|---|
| floor2 (14 Oct) | 8 x 8 grid, density 0.45, li1 allowed | 103,658 | ~96k | lost in a restart |
| floor3 | all logic in one central block between two macro arrays | - | - | global routing never finished (heavy settings) |
| floor2b | floor2 grid + no li1 + guide + 20 um power halo | - | - | global routing never finished (same heavy settings) |
| floor2c | same, light global route (no layer adjustment) | 174,309 | 60,575 | 54k after pass 3, slow |
| floor2d | same grid, global placement density 0.15 | 145,484 | 45,632 | 25 after 64 passes |
| **floor2e** | **floor2d + met5 power stripes at pitch 84 / offset 76.2 um** | **145,480** | **45,506** | **1 after 40 passes** |

Causes found, in order: (1) the 2022 reference settings (100 global-route iterations, layer adjustment 0.3, macro extension)
stalled global routing for hours, the light settings finished in minutes; (2) 88% of floor2c's remaining violations were
met1 shorts inside a ~4 mm2 central blob where the standard cells were packed (target density 0.45), not at the macros;
spreading the cells (density 0.15) removed the blob and routing converged (violations by pass: 145k, 46k, 38k, 9.2k, 4.0k,
2.7k, 2.2k, 1.9k, 1.8k, 1.6k, 945, 438, 364, ... 137, ... 28, 25). Forbidding li1 for routing (as the reference flows do)
made pass 1 worse (174k vs 104k) but the guide + spread cells more than paid for it.

**floor2d's last 25 violations** (`floor2d/drc_summary.txt`): 18 shorts on met4 and 7 metal-spacing on met5, all within
10 um of an SRAM macro top edge (8 macros of the dream-counter memory), 7 involving the VDD stripe: a signal via at the macro
edge landed next to a met5 power stripe. **Fix (floor2e):** met5 stripes at pitch 84 um, offset 76.2 um, so no stripe lies
within 12.9 um of any macro top or bottom edge (the old 56 um pitch cannot get beyond 4.3 um). Same flow otherwise: detailed
routing ends at **1 violation** (`floor2e/drc_final.txt`: one VDD-vs-signal short on met5 at x 3246, y 1430 um) after 40
passes, 14,205,859 um of wire, 914,506 vias. Per pass: 145,480 / 45,506 / 37,849 / 8,876 / 4,050 / 2,924 / ... / 453 / ... /
30 / ... / 7 / 4 / 1. One more stripe tweak (or a single-net ECO) would reach zero. Timing, power and area figures of this
document remain those of the global-route estimates above (not re-extracted from the routed design).

## Next steps for a real chip (months 7-8)

1. Put the encoder's small memories (image, receptor map, code map) into small SRAM macros instead of flip-flops.
2. Clock gating and a power estimate from a simulated switching activity (VCD) instead of the 10% default.
3. Detailed routing and a smaller die once 1-2 are done (placement and global routing: done, above).
4. Pad ring and multi-corner checks only if fabrication is ever planned (not in scope now).


**floor2f (ESTIMATED):** floor2e routing database, router seed 43: ends at 6 violations (all at macro edges), worse than floor2e (1). Seeds only shuffle the last few; floor2e remains the best run.

**floor2g (SIMULATED routing result, OpenROAD TritonRoute):** floor2e global route and CTS database, signal and clock routing limited to met1-met4 (met5 left to the power stripes), 40 passes, `hw/asic/cortex/route5.tcl` + `floor2g/run.sh`. Detail routing ends at **0 violations** (`floor2g/route_full.log`, DRT-0199 "Number of violations = 0", empty `route_drc.rpt`; 1 h 49 min elapsed). This clears floor2e's last short (VDD vs signal on met5). Still a routed-database result from the open flow, not a signed-off DRC/LVS run and nothing taped out.



## Slow table and finer-grid encoder options (19 Oct 2026, ESTIMATED by arithmetic, not re-run through the layout flow)

- `CORTEX_SLOW` adds a third memory: 8 bits x 10 classes x 4,608 words = 46 KB (1.6x the fast table, 0.8x the dream memory). The core's memories today are about 94 KB (list 7.5, table 28.8, dream counts 57.6), so the
  slow table adds about +49% to the SRAM macros (about 23 more 2 KB macros); scaling the 18.8 mm2 image-chip estimate (95% macros) gives about +9 mm2. One FOLLOW sweep is 3 cycles per code bit (~14k cycles), once per 500 ticks. Not placed or routed.
- `ENC_S1` (finer winner grid) changes no memory (same 4,608-bit code); the encoder takes 2.3x the cycles per image (48,162 vs 21,378 cycles per image, simulation; the receptor stage is shared). Not placed or routed.
- Functional checks: `run_check_cortex_slow.py` (plain, pipelined, SRAM macro models) and `run_check_encoder.py --s1 --asic`: 0 mismatches.

Related: [Month 3 results](cortex_month3.md), [Energy estimate](cortex_energy_estimate.md), [Results index](INDEX.md)
