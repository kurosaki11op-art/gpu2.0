---
title: Problems of today's GPUs - what we address, what the evidence says, what is not solved (30 Oct 2026)
tags: [spark, gpu, analysis, scope, claims]
---

# Problems of today's GPUs and where L stands (30 Oct 2026)

Founder's goal (30 Oct 2026): analyse every problem of today's GPUs (power, heat and cooling, memory, cost, heavy training, stored knowledge, intelligence and efficiency) and solve them, with the chip neither beaten on accuracy nor lacking any process a GPU is used for. This note maps each problem to what the project has actually shown. **Labels: MEASURED (a real run), SIMULATED (RTL or model), ESTIMATED (assumed constants), NOT SHOWN.** Nothing about L is MEASURED on a board yet; the only measured GPU number so far is idle power of the founder's laptop RTX 3050 (about 6 W), and its throughput run was invalid (shared GPU, energy saver on, clock 210 MHz; to be redone).

## 1. Problem by problem

| GPU problem | What L does about it | Evidence | Honest gap |
|---|---|---|---|
| **Power and heat** | adds and table reads instead of multiply-accumulate, events instead of dense passes, an early-exit dispatcher that wakes the deeper layer for 20% of images | ESTIMATED: L + Deep about 49 nJ per image against about 0.8 to 3.8 uJ of multiplies for a small and a strong reference CNN (about 16x by operation count, 5 to 6x for the cascade); Cortex layout estimate 0.18 to 0.26 uJ | nothing measured on a board; an FPGA prototype will carry about a watt of static power, so a measured energy win on the prototype is unlikely; the win is a chip projection |
| **Cooling** | follows from power: at 30 to 50 nJ per image the heat is milliwatts at thousands of images per second | ESTIMATED | same as above |
| **Memory wall** | tables and weights stay next to the compute in small SRAM banks; L's table is 46 KB, Deep 93 KB at int8 | SIMULATED: 74 block RAMs on the integrated FPGA fit; ESTIMATED: the 2 GB, 5 nm tile model gains 1.3 to 4x on dense kernels, large only when the whole working set fits | big models need the capacity that costs money (SRAM at 5 nm); no RTL for the 2 GB design |
| **Cost** | tiny die for the recognition core | ESTIMATED: cost models; NRE Rs 12.8 crore at the low end up to thousands of crore | the NRE is the problem, not the die; a shuttle or a mature node is the only affordable route |
| **Heavy training** | L Cortex learns on the chip with no backprop: LEARN, DREAM, FOLLOW; staged and few-label learning | SIMULATED RTL: 60,000 images trained in the chip simulation, 13,569 cycles per image (pipelined), about 16 s at 50 MHz projected (ESTIMATED); few labels: digits 93.1 / 91.3 / 90.7% at 10 / 5 / 2% labels against 94.1% (SIMULATED, earlier tests) | the on-chip rule is weaker than offline training only in some tests (it beat an offline softmax table, 88.85 against 86.0 to 86.7%); the L Deep clause layer is trained on a host; no deep-net-scale training |
| **Stored knowledge** | learns from few examples and keeps old classes by dreaming | SIMULATED: staged clothing 83.3 with replay against 87.1 with all earlier data, so some loss remains | no language-scale knowledge; a language model is a future item (L Language), not built |
| **"Less intelligent"** | not a hardware property: a GPU runs whatever model it is given | none | cannot be claimed or tested as a chip property |
| **Efficiency per accuracy** | cascade: the chip answers the confident 80 to 90%, the rest goes to a stronger fallback | SIMULATED accuracy 91.4% at 15% flagged with ESTIMATED energy 6x below the strong CNN alone | the fallback must exist; the chip alone is 89.7% |

## 2. Accuracy: measured position (SIMULATED, Fashion-MNIST, one seed each)

L + L Deep 89.73%; small reference CNN 90.7%; stronger reference CNN with augmentation 91.75%; deep tuned CNNs 93 to 95% (literature, not measured here). Errors concentrate on shirt-like classes (61% of errors in four pairs); 5.9% of all images are wrong for both L and the strong CNN. Tested and failed to close the gap: detector refit (88.87 against 88.85), offline table (86.0 to 86.7), hard-only table, residual Deep, specialist clauses (best +0.14), better routing signals (at most 0.1). **"Never beaten on accuracy" is not met today, and none of the cheap levers move it.**

## 3. "Lacking no process a GPU is used for" - coverage today

| GPU workload | Status |
|---|---|
| matrix multiply | SIMULATED RTL, bit-exact (block floating-point lane, about 1e-2 error against fp64), meshes up to 8x8 |
| FFT | SIMULATED through the lane model; all-to-all mesh verified; no dedicated butterfly path |
| iterative solvers, Kalman, stencils | SIMULATED through the lane model; precision routing helps solvers, not FFT or Kalman |
| small-network inference | covered by L Cortex and L Deep (recognition) |
| on-device learning | covered by L Cortex (clothing and digits; few-label and staged) |
| deep-network training with backprop | **not covered, by design** |
| small-scale language (next-character, commands) | SIMULATED: counting tables 2.33 bits per character against 2.25 to 2.28 for an undertrained small transformer, about 1,000x fewer operations (ESTIMATED); hit a wall at that quality ([text boundary test](../hw/results/text_boundary_test.md)) |
| large language models | **not covered**: needs about a gigabyte of weights (ESTIMATED gain 48x only if it all fits on chip) and no RTL exists |
| graphics, rasterisation, ray tracing | **not covered** (ray tracing dropped from the acceptance list: about 1x in the traffic model) |
| general programmability (CUDA ecosystem), video codecs | **not covered** |

So the chip would be a complementary accelerator for recognition, on-device learning and a set of numeric kernels, not a replacement for a GPU. Covering everything a GPU does is what makes a GPU large, hot and expensive; the problems on the founder's list are largely the price of that generality.

## 4. What would be needed to move each "NOT SHOWN" to evidence

1. Measured GPU baseline (the RTX 3050 run, on an idle full-speed GPU with the patched script) and a board power measurement: the two numbers every energy claim waits on.
2. A target workload list agreed in advance, with the accuracy and energy bar for each (a cascade bar and an on-device-learning bar are defined by the tests above).
3. Rule: any workload outside the covered set is stated as not covered in the pitch.

Related: [Concept study: GPU and memory](concept_study_gpu_and_memory.md), [L status](L_status_28oct.md), [Claims register](claims_register.md), [Gap diagnosis](../hw/results/gap_diagnosis.md), [Measurement protocol](measurement_protocol.md), [Docs index](INDEX.md)
