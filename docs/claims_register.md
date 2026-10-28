---
title: Claims register - what may be said about L, with its label and its evidence (28 Oct 2026)
tags: [spark, claims, evidence, honesty]
---

# Claims register (28 Oct 2026)

For use at the February event and in any conversation with a buyer, funder or reviewer. It lists what the repository supports, with the label the project rule requires, and what it does not support. It does not edit the pitch or the deck. Nothing in this repository is MEASURED on a chip or a board, and no GPU has been measured.

## Claims the evidence supports (with their label)

| claim | label | evidence |
|---|---|---|
| L Cortex recognises clothing images at 88.85% with a counting table (adds only, no multiplier) | SIMULATED, one test set, several seeds in earlier notes | [project memory](PROJECT_MEMORY.md), [foundations study](../hw/results/foundations_study.md) |
| L Cortex costs about 30 nJ per image counted from its operations | ESTIMATED (45 nm constants) | [cost frontier](../hw/results/cost_frontier.md) |
| Cortex's own layout needs about 0.18 to 0.26 uJ per decision, 20 to 28 times its operation count; the layout is not sign-off ready | ESTIMATED | [Cortex ASIC estimate](../hw/results/cortex_asic_estimate.md) |
| L Deep (routed clause layer) lifts accuracy to about 89.7% (+0.85 points) for about 49 nJ per image (1.45 times L) when 20% of images are routed to it | SIMULATED accuracy, ESTIMATED energy, two seeds | [L Deep build](../hw/results/l_deep_build.md) |
| The Deep and dispatcher RTL match an independent reference model on all 10,000 test images (accuracy 89.73% from the RTL's own predictions) and survive stress (corner inputs, mid-job resets, hostile UART bytes, 200,000 random Forge lane operations); all three stand-alone Deep cores match the reference on every routed test image; two bugs were found by these tests and fixed | SIMULATED RTL (iverilog) on a virtual FPGA; no board | [Virtual device tests](../hw/results/virtual_device_tests.md) |
| An int8 convolutional network reference gets 91.28% for about 260 nJ per image (float32 about 2,300 nJ); L plus Deep is about 1.5 points lower in accuracy and about 5 times lower in energy | reference SIMULATED, energy ESTIMATED | [cost frontier](../hw/results/cost_frontier.md), [hybrid routed CNN](../hw/results/hybrid_routed_cnn.md) (a CNN is only a labelled reference, never a component of L) |
| L continues to learn new classes while standard networks forget (about 81 to 94% against about 20% after five stages) | SIMULATED | [staged learning](../hw/results/staged_mlp.md) |
| L Forge's lane (8-bit block floating point, 16-bit accumulator) gives about 1e-2 error on matrix products and the RTL matches its golden model; a tile runs a matrix product at 99.9% lane utilisation | SIMULATED | [Forge lane and traffic](../hw/results/forge_lane_and_traffic.md), [lane numerics](../hw/results/bfp_lane_numerics.md) |
| Low-precision solvers refined in fp64 reach full accuracy at about half the data movement (Poisson); the Kalman filter needs no fp64 | SIMULATED, traffic ESTIMATED | [refinement loop](../hw/results/refinement_loop.md), [FFT and Kalman](../hw/results/fft_kalman_routing.md) |
| A memory-on-chip tile design could use about 2 to 33 times less energy than a GPU-style baseline on neighbour-exchange and sparse workloads at 2 GB, about 1 times on ray tracing | ESTIMATED, plus or minus 3 times, assumed link energies | [numeric tile study](L_numeric_tile_study.md), [Forge traffic](../hw/results/forge_lane_and_traffic.md) |
| Silicon for 1 to 2 GB on chip at 5 nm costs roughly Rs 16,000 to 73,000 per chip; the one-time cost is tens to thousands of crore | ESTIMATED with assumed inputs; NRE figures REFERENCE, unverified | [cost and power limitations](../hw/results/cost_and_power_limitations.md), [cost by node](../hw/results/cost_by_node.md) |

## Claims the evidence does not support (do not make them)

1. Any MEASURED energy, speed or accuracy on silicon or on a board. None exists.
2. That L beats a GPU in energy: the GPU side is a modelled baseline; the 36 times figure is an ESTIMATED tile-model ratio for sparse recognition only.
3. That L does everything a GPU does: L Forge has two kernels through its lane, one in RTL; ray tracing is about 1 times; no compiler exists.
4. That a 2 GB, 5 nm chip exists or is affordable now: it is a projection; the one-time cost is far beyond current funds.
5. That L Deep or L Forge runs a 1B or 4B language model: neither does (a language model would be a separate future layer).
6. That the Cortex layout is ready for fabrication: its detailed routing did not finish and design-rule and hold checks fail.
7. That the FPGA build fits a Tang Nano 20K: L Deep alone needs more block RAM than it has.
8. That the energy figures include clocking and layout overhead: those from operation counts do not; the layout showed that overhead can be 20 to 28 times.

## What would turn estimates into measurements

Board power of Cortex on the founder's board; a bigger FPGA running Cortex, Deep and a Forge tile with measured power; a GPU running the same recognition task with power read from its sensor; a layout of the Deep and Forge tiles for energy and area.

Related: [Status, 28 Oct 2026](L_status_28oct.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md), [Journal](journal.md)
