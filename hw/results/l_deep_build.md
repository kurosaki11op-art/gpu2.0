---
title: L Deep build - the routed clause layer, integer model and RTL
tags: [spark, result, simulated, l-deep, rtl]
---

# L Deep build (28 Oct 2026)

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

## What is left for L Deep

1. Cost: 5.6 literals per clause on average and a full scan of the code bits; a keyed evaluation (only clauses whose positive literal is active) and the Cortex active-bit list would cut cycles several-fold; pruning clauses by use (top 4,000 of 8,000 already).
2. FPGA fit: done in RTL (block-RAM version, serial load); needs an FPGA with more than about 1.5 Mbit of block RAM, to be chosen.
3. Integration: done for the simulated pipeline (l_system.v); wiring the existing Cortex RTL core to Deep (table format and the learned-table load path) is not done.
4. Energy per routed image (cycles times layout energy per cycle), not yet estimated.
5. Continual learning: clause banks are append-only in simulation; the hardware update path is not built.

Related: [Results index](INDEX.md), [L-Deep attempts](ldeep_attempts.md), [Routed clauses](own_methods_routing.md), [L Deep RTL](../rtl/deep/README.md), [Dispatch tests](dispatch_tests.md), [Build plan](../../docs/L_build_plan_dec_jan.md)
