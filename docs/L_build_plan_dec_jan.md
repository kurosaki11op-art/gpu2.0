---
title: Build plan for L Deep and L Forge - finish by December or January for the February event
tags: [spark, plan, l-deep, l-forge, schedule]
---

# Build plan: L Deep and L Forge (started 28 Oct 2026)

Founder's target: finish L Deep and L Forge by December or January, about Rs 1 lakh available from other projects, a pitch event in February. Today is 28 Oct 2026, so about 9 to 14 weeks. **The dates below are my ESTIMATES (uncertainty about 2x), not commitments**; a failed test changes the plan, and several things wait on the founder (marked **needs founder**). Scope is the FPGA-measured pitch version; fabrication and the 2 GB chip at 5 nm stay a separate roadmap ([L Forge design](L_forge_design.md), [cost and power limitations](../hw/results/cost_and_power_limitations.md)). The standing rule that the pitch and deck are not edited by me still holds: this plan produces evidence only.

## Deliverables that make the February claim defensible

1. All three layers (Cortex, Deep, Forge) in RTL that matches their integer models bit for bit, with the dispatcher, on one FPGA build (or two boards linked), each with a stated pass or fail.
2. Measured energy per task on the FPGA against a measured GPU on the same task (the cost and energy claim becomes MEASURED for the FPGA; chip figures stay labelled ESTIMATED).
3. L Forge acceptance on four hand-mapped kernels, not a general compiler: matrix multiply, FFT, Poisson CG with refinement, Kalman filter. Numerical accuracy versus fp64 stated.
4. L Deep at about 1M parameters running a language task with its quality measured.
5. A labelled projection for the 2 GB, 5 nm chip from the measured per-tile numbers.

## Schedule (ESTIMATED)

| weeks | dates | L Forge | L Deep | shared |
|---|---|---|---|---|
| 1 to 2 | 28 Oct to 10 Nov | **gate:** refinement loop on all grids, block floating-point lane numerics, FFT and Kalman with routed precision | **gate:** choose the model (from the [accelerator design](L_accelerator_design.md)) and train or reuse the 0.94M-parameter model on a GPU; quality check (**needs founder: GPU time**) | decide the FPGA to buy with the Rs 1 lakh (**needs founder**), order measurement gear |
| 3 to 5 | 11 Nov to 1 Dec | bit-exact tile model; synthesise add-only and Forge tiles in the open flow to replace assumed areas; tile-to-tile traffic model | bit-exact ternary and int8 model; sparse row lookups; state and memory map | dispatcher model: input-type rule plus Cortex early exit (already tested) |
| 5 to 9 | 2 Dec to 5 Jan | tile RTL and checks; hand-mapped kernels on a few tiles | RTL and checks | integrate three layers and dispatcher; FPGA fit |
| 9 to 12 | 6 Jan to 30 Jan | measure kernels and energy on the FPGA | measure language task and energy | GPU baseline on the same tasks (**needs founder: GPU run**); write the measured-versus-estimated table |
| buffer | Feb | fixes, rerun failures | | event |

## Cuts that make it fit

No general compiler (four kernels hand-mapped); Deep at about 1M parameters only; Cortex layout sign-off, shuttle and the 2 GB chip are out of this schedule; a second FPGA or a larger one only if the three layers do not fit on one.

## Biggest risks

L Deep may not reach useful quality (the gate in weeks 1 to 2 decides); Forge's tile-to-tile traffic may remove its memory advantage (the traffic model decides); the FPGA may be too small for three layers; hardware and GPU measurements wait on the founder.

## Rule for every step

Test before building; record every result with its label and failures with the same prominence as wins; journal each step; commit and push.

Related: [L Forge design](L_forge_design.md), [Accelerator design](L_accelerator_design.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md)
