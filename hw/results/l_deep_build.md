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

## What is left for L Deep

1. Cost: 5.6 literals per clause on average and a full scan of the code bits; a keyed evaluation (only clauses whose positive literal is active) and the Cortex active-bit list would cut cycles several-fold; pruning clauses by use (top 4,000 of 8,000 already).
2. FPGA fit: the bit memory as block RAM with a serial load; the wide input port is simulation only.
3. Integration: shared code memory with Cortex and the dispatcher (margin at most the threshold wakes Deep).
4. Energy per routed image (cycles times layout energy per cycle), not yet estimated.
5. Continual learning: clause banks are append-only in simulation; the hardware update path is not built.

Related: [Results index](INDEX.md), [L-Deep attempts](ldeep_attempts.md), [Routed clauses](own_methods_routing.md), [L Deep RTL](../rtl/deep/README.md), [Dispatch tests](dispatch_tests.md), [Build plan](../../docs/L_build_plan_dec_jan.md)
