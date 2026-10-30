---
title: Lessons from project L version 1 - wins, failures and what the new start must do differently (30 Oct 2026)
tags: [spark, lessons, retrospective, decision]
---

# Lessons from project L, version 1 (30 Oct 2026)

Founder's decision, 30 Oct 2026: stop building on the three-layer L design, learn from its wins and failures, and start a new project. Nothing is deleted: version 1 stays in this repository as it was at commit `9d9f4ca` on branch `claude/sharp-davinci-wrwazg`. **Labels as everywhere: MEASURED / SIMULATED / ESTIMATED.**

## What worked (keep)

1. **Verification culture.** Every block was checked bit for bit against an independent model, and the whole recognition chip ran all 10,000 clothing test images with 0 mismatches (SIMULATED RTL). It caught real bugs (a stale-read argmax, a start-signal race, memories silently turned into logic, an accumulator erasure).
2. **On-chip learning without backprop.** The Cortex core trains its own table: 13,569 cycles per image (pipelined), bit-exact with the model; its rule beat an offline-trained softmax table on the same code (88.85% against 86.0 to 86.7%).
3. **A usable confidence signal.** Flagging the least-sure 20% raised accuracy on the answered images from 89.7% to 95.8%; a chip-first cascade reached 91.4% at about 6x less energy than the strong reference CNN (ESTIMATED).
4. **The method transfers at small scale.** Counting tables came within 3 to 4% of an undertrained small transformer on next-character prediction, learning in one pass (SIMULATED).
5. **Process.** Labelled numbers, failures recorded as prominently as wins, a virtual device to test everything before any purchase, a regression that stayed green.

## What failed (do not repeat)

1. **The three-layer design was not justified.** L Deep added 0.9 point for about 1.45x the energy; three attempts to improve it (hard-only training, residual stage, specialist clauses) gained at most 0.14 point; better detectors, an offline table and better routing signals gained nothing. L Forge never touched recognition.
2. **Accuracy capped near 90%** (a linear readout on a fixed binary code holds about 91% at best); a small reference CNN measured here got 90.7%, a stronger one 91.75%; shirt-like classes hold 61% of the errors.
3. **I stated numbers from memory before measuring** (a CNN gap of 3 to 5 points); the measured small CNN was within 1 point. I also misread L Deep as a language model and built plans on it for days.
4. **Every energy claim stayed ESTIMATED.** The Cortex layout energy was 20 to 28 times its operation count; an FPGA prototype carries about a watt of static power so it cannot show a chip-level energy win; the GPU baseline was never measured validly (shared GPU, Windows energy saver, clock at 210 MHz).
5. **Scope grew faster than evidence** (recognition, numerics, memory tiles, a 2 GB 5 nm projection) with no agreed bar for any of them.

## What the new start must do differently

1. **Target and bar first.** Write the workload, the accuracy bar, the energy and cost bar, and the measurement plan in numbers before any design.
2. **Measure the incumbent first**, on the same task, on an idle full-speed GPU.
3. **One problem GPUs are bad at**, chosen from the founder's list (power, heat, cooling, memory, cost, training, stored knowledge), with a cheapest-decisive-experiment before building.
4. **Keep the verification culture and the virtual device**; keep a claims register and never mix evidence levels.
5. **Be honest about what a prototype can show:** a board shows function and accuracy; chip-level energy remains a projection.

## Assets worth reusing

The bit-exact flow (iverilog checks, independent reference models, `hw/run_all_checks.sh`), the virtual device and 3D viewer (`hw/virtual`), the Cortex encoder and core with on-chip learning, the dispatcher and early-exit confidence, the mesh and router RTL, the cost and energy models, the GPU measurement scripts, the risk-coverage and cascade tests.

Related: [GPU problem analysis](gpu_problem_analysis.md), [Gap diagnosis](../hw/results/gap_diagnosis.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md)
