---
title: Project status, 31 Oct 2026 - what is measured, simulated, estimated, and what waits on whom
tags: [spark, status, summary]
---

# Status, 31 Oct 2026 (replaces the 28 Oct status for the current direction)

## Direction

Version 1 (the three-layer L Cortex, L Deep, L Forge design) was dropped on 30 Oct 2026 ([lessons](lessons_L_v1.md)); it stays in the repository untouched. Both fresh targets tested failed their pre-set first-step bars: irregular and sparse workloads (GPU memory waste 1.9x to 2.9x, bar 5x; [step 1](../new_start/step1_result.md)) and batch-1 language-model decode (3.6x energy per token at the pessimistic SRAM value, bar 5x; [step 1, target 3](../new_start/step1_lm_result.md)). Defensible scope, written in [project memory](PROJECT_MEMORY.md): **small, sparse, on-device recognition with a confidence flag**; the uncovered GPU workloads are listed in the [census](gpu_workload_census.md) and are stated as not covered.

## What is MEASURED (real hardware)

| item | result | source |
|---|---|---|
| L algorithm on an ESP32 (software, not the chip) | bit-exact with the model on 1,000 of 1,000 images; **8.69 ms per image** (115 images per second) after two optimisations; first run 25.05 ms | [first ESP32 run](../hw/results/esp32_first_run.md) |
| small int8 CNN on the same ESP32, same build flags | **255.2 ms per image**; checksum equals the PC run; **29x slower than the L algorithm** (a time ratio) | same |
| founder's laptop RTX 3050 6 GB | idle about 6 W; a first throughput run was invalid (a second job shared the GPU and Windows energy saver pinned the clock at 210 MHz); the baseline has to be rerun on an idle GPU at full clock | [measurement protocol](measurement_protocol.md) |

## What is SIMULATED (bit-exact RTL and models, no board)

The whole recognition chip ([L Cortex encoder and core with on-chip learning, L Deep, dispatcher, reject flag](../hw/results/l_deep_build.md)) matches the reference model on all 10,000 Fashion-MNIST test images with 0 mismatches; 89.7% accuracy (a measured small CNN 90.7%, a stronger one 91.75%); the reject flag gives 95.8% accuracy on the answered images at 20% flagged; the chip-first [cascade demo](../hw/results/cascade_demo.md) reaches 91.2% at 15 to 16% flagged. Learning on the chip: 13,569 cycles per image (pipelined), 60,000 images projected at about 16 s at 50 MHz. Findings recorded as failures: [accuracy gap tests](../hw/results/accuracy_gap_tests.md), [gap diagnosis](../hw/results/gap_diagnosis.md), [new-class learning](../hw/results/target1_new_class_learning.md), [language boundary test](../hw/results/text_boundary_test.md).

## What is ESTIMATED (assumed constants, nothing measured)

Chip energy per image about 0.049 uJ by operation count (the Cortex layout estimate is 20 to 28 times its operation count); the cascade at about 5.7x less than the strong CNN alone (2.3x if the chip's first stage costs 1 uJ); all GPU energy figures except the idle power above.

## Waiting on the founder

1. **USB power meter** (an amiciSense 6-in-1 tester, ordered): energy per image of the L algorithm and the CNN on the ESP32; flash `esp32_mode2` (idle), `esp32_mode0` (L) and `esp32_mode1` (CNN) and record Wh and time over 10-minute windows ([procedure](../hw/mcu/README.md)).
2. **GPU baseline** on the RTX 3050 with `gpu_energy_baseline.py --net small` and `--net strong` (patched script; Windows energy saver off, plugged in, no other job on the GPU).
3. **Board and money:** the FPGA board purchase ([decision](fpga_board_decision.md)) waits for the Rs 1 lakh and the three pre-purchase checks; a board measures function and accuracy, not chip-level energy.

## What can proceed without the founder

Further tuning of the MCU build (the detectors are 76% of the ESP32 time), regression and documentation, and any new-start experiment whose pre-set bar is written first.

Related: [Project memory](PROJECT_MEMORY.md), [Lessons from L version 1](lessons_L_v1.md), [GPU problem analysis](gpu_problem_analysis.md), [New start charter](../new_start/README.md), [Docs index](INDEX.md)
