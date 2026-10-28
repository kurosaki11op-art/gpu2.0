---
title: Virtual device tests - the whole design on a simulated FPGA, with stress
tags: [spark, result, simulated, rtl, tests, virtual]
---

# Virtual device tests (28 Oct 2026)

Founder's request: before any FPGA is built or bought, test that everything runs virtually, on a virtual device made for us, with serious tests. Built in [hw/virtual](../virtual/README.md): a virtual FPGA (VFPGA-L1: 50 MHz virtual clock, 20,000 logic cells, 120 block RAMs of 18 Kbit, 48 multipliers, UART), a full regression, three stress tests and a rotatable 3D view. **SIMULATED (iverilog) and yosys synthesis estimates; no board, no place and route, no timing closure, no power.** The device is a simulation target sized for this design, not a real part.

## Result: everything passes, after two real bugs were found and fixed

`python hw/virtual/run_all.py` runs 14 steps in sequence, **all passed** (log `hw/virtual/results/run_all.log`, summary `test_summary.json`):

| step | what | result |
|---|---|---|
| RTL checks of the blocks | three L Deep cores (300 routed images each), two-stage system (200 images), layered top (40 recognitions plus a matrix product), UART board top, Forge tile | 0 mismatches each |
| **Test 1** | **the whole 10,000-image test set through the system RTL, compared image by image (routed flag, all 10 scores, prediction) with an independent reference model written from the RTL memory files** | **0 mismatches; accuracy from the RTL's own predictions 89.73%; 20.0% routed; mean 12,103 cycles per image (not routed 4,620, routed 42,014, maximum 50,810); at 50 MHz 0.24 ms per image, 4,131 images per second** |
| **Test 2** | stress mix on the layered top, three seeds: 47 recognitions each (random routed and not routed, corner inputs: all zeros, all ones, alternating, single set bits, sparse and dense random), 4 matrix products interleaved, 2 reset injections in the middle of routed runs, repeated identical images | 0 mismatches in all three |
| **Test 3** | Forge: 200,006 random lane operations (extreme mantissas, exponent gaps beyond the alignment limit); the matrix-product tile on seven data distributions (normal, heavy-tailed, 90% zeros, wide dynamic range, all zeros, all maximum, alternating extremes) | 0 mismatches; error against fp64 1.0e-2 (normal), 1.5e-2 (heavy-tailed), 6.6e-3 (90% zeros), 1.0e-2 (wide range) |
| **Test 4** | UART board top under a hostile host: junk bytes, an invalid op, a double sync, unknown ops between valid jobs; then routed and not routed recognitions, all-zero and all-one inputs, a matrix product | every valid job answered exactly; 1,320 reply bytes as expected, none extra |
| resource fit | yosys, Gowin family: the whole board top needs 4,861 LUT4, 1,134 carry cells, 779 flip-flops, 74 block RAMs (62% of the device), 16 multipliers (33%); 5,995 of 20,000 logic cells (30%) | fits with room |

Block counts (LUT4 / carry / flip-flops / block RAM / multipliers): UART 106 / 39 / 70 / 0 / 0; L system (stage 1, dispatcher, L Deep with one engine) 2,746 / 574 / 384 / 64 / 0; Forge tile 2,803 / 479 / 208 / 10 / 16; four-engine Deep core 3,408 / 2,097 / 1,418 / 76 / 0.

## What the virtual tests found (failures recorded as prominently as wins)

1. **A real RTL bug, found only by the full test set.** The final class choice read class 0 before the last table add had landed. 1 image of 10,000 got the wrong class (RTL 89.72% against the reference's 89.73%); image 4203 scored 5,075 for class 0 and 5,092 for class 2 and the RTL answered class 0. All earlier checks (300 and 200 images) had passed by luck. Fixed in the system and block-RAM cores (the argmax now starts from the lowest value and visits all classes); every cycle count in earlier notes is now one higher (for example 4,620 for a not-routed image).
2. **The Forge accumulator could be erased by a zero block.** A block whose products sum to zero but whose exponent is much larger than the accumulator's wiped the running sum: matrix products on 90%-zero data had 21% error instead of 0.7%, and all-zero inputs mismatched. Fixed in the lane RTL, the golden model and the vectorised tile model (a zero block sum leaves the accumulator unchanged), and the exponent of all-zero blocks is clamped. The 3,288-operation lane check had not covered this case; the stress test did.
3. **The UART protocol has no flow control.** A host that sends the next command before the reply has arrived loses bytes silently (the first version of the hostile-host test did that and failed). The host script already waits for each reply; the protocol note now says a host must.

## Limits

Simulation only: the virtual device checks function and resource counts, not timing, clock domains, block-RAM initialisation on a real part, or power. The yosys counts are estimates. Stage 1 is a re-implementation of the table read for the experiment's trained table, not the existing Cortex core. The reference model is independent of the golden exporter but shares the memory files, so it checks the RTL logic, not the trained contents. Four-engine L Deep and the Forge tile were exercised in the regression but not inside the 10,000-image run (which uses the one-engine core).

## The 3D virtual board

[vfpga_3d.html](../virtual/vfpga_3d.html): a rotatable 3D floorplan of VFPGA-L1 in plain canvas code (no external 3D library): logic tiles coloured by layer (L Cortex stage 1, L Deep, L Forge tile, dispatcher and UART), block-RAM and multiplier columns, resource bars, the block table, the test results and findings, and a replay of 29 real simulated jobs in which each layer's region lights while it is awake (awake share per layer shown live). The split of the shared system module between Cortex stage 1 and L Deep is an estimate; the memory split is exact by size.

Related: [Results index](INDEX.md), [Virtual device README](../virtual/README.md), [L Deep build](l_deep_build.md), [Forge lane and traffic](forge_lane_and_traffic.md), [Status, 28 Oct 2026](../../docs/L_status_28oct.md)
