---
title: L Deep build - the routed clause layer, integer model and RTL
tags: [spark, result, simulated, l-deep, rtl]
---

# L Deep build (28 Oct 2026)

**Correction (28 Oct 2026, found by the virtual full-test-set run):** the system and block-RAM cores had a stale-read bug in the final class choice (1 image in 10,000 got the wrong class); the 300- and 200-image checks quoted below had not exposed it. Fixed; all 10,000 test images now match the reference model, and every cycle count below is one higher after the fix. See [virtual device tests](virtual_device_tests.md).

**What L Deep is:** the deeper learned layer over L Cortex's code, defined by the founder on 25 Oct 2026 ([attempts](ldeep_attempts.md), [routed clauses](own_methods_routing.md)): Tsetlin-style clauses (each an AND of literals of L's code and raw pixel bits, learned by local feedback, no error passing), read by a counting table, run only on the images L is least sure about. (Earlier today I wrongly treated it as a language model; see the correction in [project memory](../../docs/PROJECT_MEMORY.md).) **SIMULATED unless stated; the cycle counts are from RTL simulation, not a board.**

## Result 1: the integer pipeline reproduces the experiment

[ldeep_golden.py](../brain/experiments/month5/ldeep_golden.py) rebuilds the best configuration with integers only: 8,000 clauses trained on L's code plus raw pixel bits (seed 0), the 4,000 most used by a table trained on 20,000 images kept, stage-2 table over L's code plus the clause bits, images routed when the shipped table's margin is at most 3,415 (the 30th percentile). Fashion-style test set: **accuracy 89.73% against 88.85% for L alone (+0.88); on the routed 30% of images 70.8% against 67.9%.** Table entries span -104 to 105, so int8 is enough. A second seed (state `..._both_s1`, log `clause_routed2_both_s1.log`) gives 89.80% and Shirt AP 0.780 (seed 0: 0.774), so the criterion set on 25 Oct (accuracy at least 88.6 and Shirt AP at least 0.78) is met on seed 1 and just missed on seed 0 (TENTATIVE, two seeds).

## Result 2: the RTL matches bit for bit

[ldeep_core.v](../rtl/deep/ldeep_core.v), checked by [run_check_deep.py](../rtl/deep/run_check_deep.py): **300 routed images, 0 mismatches** in all 10 scores and the prediction; **mean 20,540 cycles per routed image** (min 17,203, max 22,926; about 0.4 ms at 50 MHz). Failure recorded on the way: the first testbench drove its start signal in a clock race, the core never started and the simulation ran for 20 minutes until killed; fixed by driving on the falling edge. Early exit of the clause evaluation keeps the clause phase to about 16,000 cycles; scanning all 4,608 code bits is a further 4,608.

## Memory (ESTIMATED from the exported files, int8 entries)

About **134 KB**: literals 22,232 of 14 bits (38 KB), clause headers (12 KB), clause rows 4,000 by 10 (39 KB), the stage-2 code rows 4,608 by 10 (45 KB). The stage-2 code rows duplicate Cortex's own table in a jointly trained form; sharing or retraining on the Cortex table would save 45 KB. This replaces my earlier 60 KB guess.

## Result 3: a block-RAM version and what an FPGA needs (SIMULATED RTL, synthesis counts from yosys)

[ldeep_core_bram.v](../rtl/deep/ldeep_core_bram.v) has synchronous-read memories (so synthesis maps them to block RAM) and loads the input bits one at a time; **bit-exact on the same 300 routed images, 0 mismatches**, but 4 cycles per literal, so **mean 62,341 cycles per routed image** (min 48,771, max 72,119; 1.2 ms at 50 MHz). Synthesised for the Gowin family with yosys: about 1,650 LUT4, 514 carry cells, about 370 flip-flops and **62 block-RAM blocks (about 1.1 Mbit)**. The first version (asynchronous reads) turned every memory into logic: about 43,000 LUT4, unusable. **The Tang Nano 20K has 46 block-RAM blocks (about 0.83 Mbit), so L Deep does not fit it; the FPGA for the three-layer build needs more than about 1.5 Mbit of block RAM** (Cortex's tables and the Forge tile memories add to this).

## Result 4: two stages and the dispatcher in RTL (SIMULATED RTL)

[l_system.v](../rtl/deep/l_system.v): stage 1 reads L's table (scan of the active code bits), the dispatcher compares the margin with the routing threshold (3,415) and wakes L Deep only if the margin is at most that, whose answer replaces the first; checked by [run_check_system.py](../rtl/deep/run_check_system.py) against the integer golden pipeline on the first 200 test images in order (58 routed): **0 mismatches in the routed flag, all 10 scores and the prediction.** Mean cycles: **4,619 when not routed, 67,360 when routed, 22,814 overall** (0.46 ms per image at 50 MHz). Synthesis: about 3,000 LUT4, 575 carry cells, about 390 flip-flops and 82 block-RAM blocks (about 1.5 Mbit). Caveats: stage 1 here is a re-implementation of the table read for the experiment's integer table (the existing Cortex RTL core uses its own table format and cannot be loaded with the experiment's trained table), so this is the system of the simulated pipeline, not yet the existing Cortex core wired to Deep.

## Result 5: where the cost of stage 2 goes, and an energy estimate from the RTL's own operation counts (ESTIMATED)

Counted on the 300 routed test images (exported clause lists): **631 active code bits and 513 active raw bits per image; 11,920 literal checks per routed image with early exit; 1,021 clauses fire.** Keyed evaluation (evaluate a clause only if the rarest of its positive literals is active) cuts the literal checks only to 10,073 (15%), because **1,485 of the 4,000 kept clauses have no positive literal** (they hold only "this bit is off" literals and are evaluated on every image) and the rest key on the 33%-active raw pixel bits. So stage 2 is dominated by about 12,000 literal reads, not by the code scan (631 rows).

Energy per image from these counts with the project's 45 nm constants (SRAM read 10 pJ per 64-bit word up to 8 KB, 20 pJ at 32 KB, rising to about 21 to 23 pJ at 40 to 50 KB; adds 0.03 pJ; encoder detectors 17 nJ): stage 1 about 34 nJ; stage 2 about **120 nJ** if a 14-bit literal costs 0.22 of a word read, up to about **350 nJ** if every literal read costs a whole word. Average over a system that routes 30% of images: **about 70 to 140 nJ per image** (L alone: 29.9 nJ; the earlier note's routed-clause estimate: 68 to 99 nJ; int8 convolutional network reference: 260 nJ, all ESTIMATED), so about 1.9 to 3.7 times lower energy than the int8 reference for 1.5 points less accuracy (89.7 against 91.3, SIMULATED). The RTL as written needs 62,341 cycles per routed image, which is a latency and clocking cost (the Cortex layout showed that clocking can dominate by 20 to 28 times), not what these counts measure; a version with parallel clause engines needs fewer cycles (result 8: 16,066 with four engines).

## Result 6: the cost frontier, how many clauses are worth keeping (SIMULATED accuracy, ESTIMATED energy)

[deep_frontier.py](../brain/experiments/month5/deep_frontier.py), logs `deep_frontier_s0.log` and `deep_frontier_s1.log`: N kept clauses (of 8,000, ranked by table use), routed 30%, the two-stage integer pipeline; accuracy gain over L alone (88.85), literal checks per routed image (counted, with early exit), system energy per image from counted operations (stage 1 and encoder 34 nJ plus 30% of stage 2; 45 nm constants as above). Seed 0 / seed 1:

| kept N | accuracy gain (points) | Shirt AP | literal checks | system nJ |
|---|---|---|---|---|
| 0 (L alone) | 0 | 0.753 | 0 | 34 |
| 250 | +0.43 / +0.34 | 0.769 / 0.767 | 1,146 / 1,321 | 41 / 42 |
| 500 | +0.40 / +0.72 | 0.770 / 0.772 | 2,110 / 2,343 | 44 / 44 |
| 1,000 | +0.58 / +0.55 | 0.771 / 0.774 | 3,938 / 4,436 | 48 / 49 |
| **2,000** | **+0.86 / +0.77** | 0.774 / 0.777 | 6,962 / 7,766 | **56 / 57** |
| 3,000 | +0.78 / +0.81 | 0.777 / 0.781 | 9,673 / 10,500 | 63 / 65 |
| 4,000 | +0.88 / +0.95 | 0.774 / 0.780 | 11,930 / 12,914 | 70 / 71 |
| 6,000 | +0.91 / +0.80 | 0.784 / 0.780 | 15,702 / 16,664 | 82 / 83 |

**Most of the gain comes from the first 1,000 to 2,000 clauses: 2,000 clauses give about 90% of the 4,000-clause gain at 20% less energy (56 against 70 nJ, 1.6 times L's 34 nJ); 1,000 clauses give about 65% at 48 nJ (1.4 times L); more than 4,000 adds nothing.** This is a free cost cut for the chip: memory also falls (2,000 clauses need about half the literal, header and row storage, roughly 80 KB at int8 instead of 134 KB). The golden model and RTL use 4,000; changing to 2,000 is a re-export. Seeds agree on the shape, not on every point (differences of about 0.2 points are noise at one seed each).

## Result 7: the dispatcher over all three layers in RTL (SIMULATED RTL)

[l_chip_top.v](../rtl/top/l_chip_top.v) puts the recognition path (Cortex stage 1, Deep woken by the margin) and an L Forge matrix-product tile behind one command interface with per-layer activity flags ([README](../rtl/top/README.md)). [run_check_top.py](../rtl/top/run_check_top.py): 40 recognitions (13 routed) and one 16 x 128 x 16 matrix product, **0 mismatches** in routed flag, scores, prediction and all 256 matrix outputs. Cycles each layer was awake: Cortex stage 184,760, **Deep 799,163 (the dominant share, 13 of 40 images woke it at about 61,000 cycles each)**, Forge 2,051. The flags are the hooks for clock and bank gating; the gating, a power controller and retention are not built, and stage 1 is still the re-implementation of the experiment's table, not the existing Cortex core.

## Result 8: four parallel engines (SIMULATED RTL, synthesis counts from yosys)

[ldeep_core_p.v](../rtl/deep/ldeep_core_p.v): four engines, each with a quarter of the code rows (a contiguous range), an interleaved quarter of the clauses (clause c to engine c mod 4, which balances the load: the clauses are ranked by use and the first ones are longest), its own input-bit copy and its own partial score vector; the top adds the four vectors and takes the argmax. [partition_engines.py](../rtl/deep/partition_engines.py) splits the memories; check `python hw/rtl/deep/run_check_deep.py --parallel`. **Bit-exact on the same 300 routed images, 0 mismatches; mean 16,066 cycles per routed image (min 12,578, max 18,870), 3.9 times fewer than the single engine's 62,341.** Gowin synthesis: about 3,450 LUT4, 2,100 carry cells, 1,400 flip-flops and 60 block-RAM blocks (the same 1.07 Mbit of memory, only the small bit memory is copied four times). Eight engines would give about 8,000 cycles. Energy by operation count is unchanged (the same reads), but the layer is awake about four times less, which is what a power gate sees.

## Result 9: how many images to route (SIMULATED accuracy, ESTIMATED energy)

[deep_route_sweep.py](../brain/experiments/month5/deep_route_sweep.py), logs `deep_route_sweep_s0.log` and `_s1.log`: 2,000 kept clauses, the least-sure share r of images by the shipped table's margin go to stage 2. Seed 0 / seed 1:

| routed share r | accuracy gain (points) | system energy, nJ (multiple of L's 34) |
|---|---|---|
| 0.1 | +0.77 / +0.72 | 41 / 42 (1.2x) |
| **0.2** | **+0.88 / +0.83** | **49 / 49 (1.45x)** |
| 0.3 | +0.86 / +0.77 | 56 / 57 (1.65x) |
| 0.5 | +0.82 / +0.73 | 71 / 73 (2.1x) |
| 1.0 | +0.82 / +0.73 | 107 / 111 (3.2x) |

**The gain is reached by about 20% routing and does not grow after it; routing everything adds energy and lowers accuracy slightly (the clause layer is slightly worse than L on the easy images it replaces).** Best operating point found: **2,000 clauses, route 20%: about +0.85 points at about 49 nJ per image, 1.45 times L's energy** (ESTIMATED, two seeds), against the earlier default of 4,000 clauses at 30% (about 70 nJ). The RTL checks use the older defaults (4,000 clauses, threshold 3,415); the new point needs only a re-export with 2,000 clauses and the 20th-percentile threshold.

## Result 10: the RTL re-exported at the recommended point (2,000 clauses, route 20%), all checks pass

`KEEP=2000 RQ=0.2 python ldeep_golden.py`, then `partition_engines.py 4`: 2,000 kept clauses, 13,497 literals (6.75 per clause), threshold 2,299, integer pipeline accuracy **89.73% (the same as the 4,000-clause, 30% version, with the routed images' accuracy 64.9% against 60.5%)**, **memory 93 KB at int8** (literals 23, headers 6, clause rows 20, code rows 45). All RTL checks pass at this point with 0 mismatches on 300 routed images: single-engine core with asynchronous reads 13,514 cycles per routed image; block-RAM core 37,176; **four-engine core 9,628**; the two-stage system on 200 images (38 routed): 4,619 cycles not routed, 42,411 routed, 11,800 overall (single-engine block-RAM stage 2); the top-level dispatcher on 40 recognitions (6 routed) and a matrix product: 0 mismatches, cycles awake Cortex stage 184,760, Deep 222,970, Forge 2,051. The older results above (4,000 clauses, threshold 3,415) are kept as history.

## What is left for L Deep

1. Cost: 5.6 literals per clause on average and a full scan of the code bits; a keyed evaluation (only clauses whose positive literal is active) and the Cortex active-bit list would cut cycles several-fold; pruning clauses by use (top 4,000 of 8,000 already).
2. FPGA fit: done in RTL (block-RAM version, serial load); needs an FPGA with more than about 1.5 Mbit of block RAM, to be chosen.
3. Integration: done for the simulated pipeline (l_system.v); wiring the existing Cortex RTL core to Deep (table format and the learned-table load path) is not done.
4. Energy per routed image (cycles times layout energy per cycle), not yet estimated.
5. Continual learning: clause banks are append-only in simulation; the hardware update path is not built.

Related: [Results index](INDEX.md), [L-Deep attempts](ldeep_attempts.md), [Routed clauses](own_methods_routing.md), [L Deep RTL](../rtl/deep/README.md), [Dispatch tests](dispatch_tests.md), [Build plan](../../docs/L_build_plan_dec_jan.md)
