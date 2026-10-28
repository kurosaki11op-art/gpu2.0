---
title: Status of the three-layer chip (L Cortex, L Deep, L Forge) on 28 October 2026
tags: [spark, status, l-deep, l-forge, plan]
---

# Status, 28 Oct 2026 (end of the first autonomous build session)

Target set by the founder: a layered chip, all three layers, built-in memory, 5 nm and 2 GB as the long-term target; a pitch-ready FPGA and simulation version by December to January. Labels follow the project rule (SIMULATED, ESTIMATED, MODELLED; nothing here is MEASURED on silicon or a board, and no GPU has been measured). Dates are not promised.

## The three layers

| layer | what it is | what exists | evidence | missing |
|---|---|---|---|---|
| **L Cortex** | counting front end and table, matrix-free | simulation, bit-exact RTL, layout (not sign-off), board build | 88.85% on the clothing test set, 29.9 nJ by operation count (SIMULATED, ESTIMATED); layout energy 0.18 to 0.26 uJ per decision (ESTIMATED), 20 to 28x above the operation count | board measurement (needs the founder's board), clean sign-off, closing the energy gap |
| **L Deep** | the routed clause layer over L's code | integer golden model, RTL core (two versions), two-stage system with dispatcher in RTL | 89.73% with the recommended point (2,000 clauses, route 20%; two seeds +0.85 points at about 49 nJ per image, 1.45 times L); RTL bit-exact on 300 routed images, a 200-image system test and the top-level dispatcher; four-engine core 9,628 cycles per routed image; 93 KB memory; needs about 1.1 to 1.5 Mbit of FPGA block RAM ([L Deep build](../hw/results/l_deep_build.md)) | energy per image from RTL (the sequential design is far above the operation count), faster microarchitecture, wiring to the existing Cortex RTL core, learning on chip |
| **L Forge** | general numeric layer, hybrid (add path plus block floating-point lane) | design note, lane in RTL (bit-exact, 3,288 ops), a tile running a matrix product in RTL, bit-exact tile model, traffic model, five numeric studies | error 1e-2 for 8-bit blocks; refinement reaches fp64 accuracy on Poisson at about half the traffic; Kalman filter through the lane matches the truth; matrix product tile 99.9% lane utilisation; fabric traffic modest for stencils, FFT and matrix multiply (ESTIMATED) ([lane and traffic](../hw/results/forge_lane_and_traffic.md), [refinement](../hw/results/refinement_loop.md), [FFT and Kalman](../hw/results/fft_kalman_routing.md), [lane numerics](../hw/results/bfp_lane_numerics.md)) | the Kalman, Poisson and FFT kernels in RTL (they run through the bit-exact lane model, only the matrix product is RTL), a dedicated butterfly path for the FFT, router and control, a compiler, ray tracing dropped, layout-based area, measured energy |

## Virtual device tests (28 Oct 2026, after the first version of this note)

The whole design ran on a simulated FPGA (VFPGA-L1): all 10,000 test images through the RTL match the reference (89.73%, 4,131 images per second at 50 MHz virtual clock), three stress tests pass, and the design uses 30% of the device's logic and 62% of its block RAM. The tests found and fixed two real bugs (a stale read in the final class choice, and a zero block erasing the Forge accumulator). See [virtual device tests](../hw/results/virtual_device_tests.md) and the 3D board in `hw/virtual/vfpga_3d.html`. Cycle counts quoted above are one lower than after the fix.

## The honest comparison with a GPU (nothing measured)

Sparse recognition: about 36x lower energy than a GPU-style baseline by the tile model (ESTIMATED) and about 5 times lower than an int8 convolutional network by operation count (49 nJ for L plus Deep at the recommended point against 260 nJ, both ESTIMATED, not counting clocking and layout overhead) for 1.5 points less accuracy (89.7 against 91.3, SIMULATED). Dense physics and language models: about 4x to 32x in the tile model at 2 GB (ESTIMATED), shrinking with fabric traffic and die crossing; ray tracing about 1x. All GPU-side numbers are modelled references.

## Corrections made in this session (recorded in the notes)

L Deep is the clause layer, not a language model (found while starting its build); the 1 GB memory cost assumed shared logic (with per-bank logic it is larger); fp16's refinement failure was underflow; precision routing helps iterative solvers by about 2x in traffic, not more; the first Deep RTL ran with a testbench race; the first Deep synthesis turned memories into logic.

## What I need from the founder

1. The FPGA purchase from the Rs 1 lakh: decision recorded in the [FPGA board decision](fpga_board_decision.md) (Tang Mega 138K primary, Arty A7-100T fallback); the founder must run the three pre-purchase checks (toolchain licence, package and pins, price and stock) and buy.
2. A GPU baseline run on the same task (clothing recognition) with power read from the GPU sensor, and the board power measurement of Cortex.
3. A quote from a shuttle or design-service programme (no price found), and whether a registered company exists for the Design Linked Incentive.

## Next steps in order

1. Layout-based energy for Deep and a Forge tile (clocking and overhead are not in the operation counts); an active-list scan for the code phase.
2. FFT and Poisson refinement through the lane; tile router and control; area from synthesis of a full tile.
3. Wire the existing Cortex RTL core to Deep and the dispatcher; replicate Deep on a second dataset.
4. Board and GPU measurements once the hardware is available.

Related: [Build plan](L_build_plan_dec_jan.md), [L Forge design](L_forge_design.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md), [Journal](journal.md)
