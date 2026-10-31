---
title: Charter - building our own GPU (programmable accelerator): scope, evidence, milestones with pre-set bars (31 Oct 2026)
tags: [spark, gpu, accelerator, charter, plan, milestones]
---

# Charter: our own GPU (31 Oct 2026)

**Founder's decision, 31 Oct 2026:** the project goal is to build our own GPU: a programmable parallel processor that runs existing models and compute workloads more efficiently than today's GPUs. The L Cortex recognizer stays as a small, separate result (about 90% on clothing with a hidden-layer head, about 88.9% with the counting recipe); it is not the product's accuracy claim. This note fixes the scope, what the evidence supports, and the milestones. Nothing here is a result.

## What the evidence supports (all MODELLED unless stated; see the linked notes)

| claim | status | note |
|---|---|---|
| energy per token 5x to 13x below a GPU cluster on large-model decode (SRAM-resident weights, 0.55 pJ/bit reads) | modelled, one cited datapoint behind the read energy | [step 6](../new_start/step6_sram_energy_result.md), [step 12](../new_start/step12_close_i_j_final.md) |
| per-user speed 7x to 20x higher | modelled with a latency model calibrated on two vendor figures | [step 4](../new_start/step4_close_i_j_result.md) |
| cost: parity at manufacturing cost (central), conditional win on price against Nvidia's margin | modelled; rests on an unsourced $150 package/board/power/cooling figure | [step 13](../new_start/step13_buyer_price_result.md), [step 15](../new_start/step15_packaged_cost_result.md) |
| heat: about 11 W per chip, no cold plate | modelled | [step 15](../new_start/step15_packaged_cost_result.md) |
| **not supported or not covered:** training, graphics, FP64, graph and sparse irregular work (1.9x to 2.9x against a 5x bar), long-context attention | gaps | [workload map](gpu_workload_map.md) |

## Scope (staged, because "everything a GPU does" is too large for one step)

1. **Stage 1, inference of existing models** (dense and mixture-of-experts transformers, convolutional networks): matrix multiply, attention, normalisation, activations; INT8, INT4 and FP16 weights; weights-stationary dataflow on SRAM tiles.
2. **Stage 2, a programming model and compiler** so a model from PyTorch or ONNX runs without hand mapping (the CUDA equivalent; the founder has said we will develop it).
3. **Stage 3, training** (gradients, higher precision, optimiser state): not before stage 1 and 2 work; today's rule "train on a GPU" holds.
4. **Not planned:** graphics, ray tracing, video codecs, FP64 science codes, unless a customer need appears.

## Architecture hypotheses to test (each gets its own pre-set bar before any build)

- **Tile:** an SRAM bank group plus a small multiply-add array (INT8/INT4/FP16 lanes) with local control; weights stay in the tile's banks; activations move.
- **Fabric:** a mesh with communication overlapped with compute (the earlier mesh work measured 10% to 15% fewer cycles with double buffering, bit-exact RTL).
- **Numerics:** per-layer precision, block floating point (an earlier bit-exact lane model exists in the version 1 archive).
- **Memory:** reticle-size dies of about 1.9 GB of SRAM each, many per board; tiering with denser memory only if foundry data arrives ([memory study](../new_start/step11_memory_technology_study.md)).

## Milestones and bars (written before the work)

| id | milestone | bar |
|---|---|---|
| **M1** | **Instruction set, programming model and a functional simulator** of one tile and a mesh of tiles, with a mapper for a transformer decoder block (d = 256, 4 heads) and a small convolutional layer stack | outputs match PyTorch fp32 within a relative error of 1e-2; with INT8 weights, top-1 agreement at least 99% on 1,000 inputs; the simulator's counted multiply-adds and SRAM bytes per layer match the analytic model within 5% |
| **M2** | **Cycle and energy model validated against the simulator** for batch-1 and batch-64 decode of a 1B-parameter model (4-bit) | modelled energy per token within 20% of the step 6 model's value at the same constants; speed within 20% of the latency model |
| **M3** | **RTL of one tile**, synthesised for the open 130 nm flow | bit-exact with the simulator on a layer; area, cells and cycle count reported; counted energy per multiply-add within 2x of the model's assumption |
| **M4** | **Compiler front end**: import a small ONNX model and map it automatically | a 2-layer decoder and a small convolutional network run end to end with no hand mapping, same tolerance as M1 |
| **M5** | **A test chip** on a multi-project open shuttle or an FPGA board (both need money: the board purchase was skipped on 30 Oct) | one tile's measured energy per multiply-add and per SRAM bit read, replacing the model constants |

Existing assets reused: the mesh tile RTL and its overlap result, the block floating-point lane model, the sky130 synthesis flow, the decode and cost models, the ESP32 power measurement procedure, the lessons notes. **Reference points to beat**, all with their own labels: the measured laptop GPU (RTX 3050: 43 W while decoding, 1.4 J per token for a 1.5B model in half precision, 31 tokens/s with an unoptimised loop) and the modelled GPU cluster of the cost notes.

## Honest risks

A programmable chip with a compiler is a very large effort for a small team; the largest modelled advantages (energy and speed) rest on assumed SRAM energy and latency figures that M3 and M5 must confirm; the cost advantage is conditional on an unsourced packaging cost and on Nvidia not cutting its price; design cost (assumed $150M for a leading-node chip) is out of reach without funding, so open-PDK and FPGA stages come first; software compatibility is the moat Nvidia has built over many years.

## Next action

Start **M1**: write the instruction set and programming model note, then the simulator. Bars above stand; no work starts on M2 to M5 until M1 passes.

Related: [Workload map](gpu_workload_map.md), [GPU problem analysis](gpu_problem_analysis.md), [New start charter](../new_start/README.md), [Manufacturing data requests](manufacturing_data_requests.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md)
