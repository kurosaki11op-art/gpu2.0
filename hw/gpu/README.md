---
title: hw/gpu - our own GPU (programmable accelerator): instruction set, simulator, exporter (31 Oct 2026)
tags: [spark, gpu, index]
---

# hw/gpu: our own GPU

Charter and milestones: [own GPU charter](../../docs/own_gpu_charter.md).

- [ISA_M1.md](ISA_M1.md): instruction set and programming model, version 0.
- [M3_plan.md](M3_plan.md) and [M3_result.md](M3_result.md): milestone M3 plan, bars and result (RTL of one tile, INT8 matrix engine: bit-exact, 98% decode utilisation, synthesised; the RTL rate recalibrates M2).
- [M4_plan.md](M4_plan.md): milestone M4 plan and bars (compiler front end, real pretrained model).
- [stripe_plan.md](stripe_plan.md): striping plan and bars (split every matrix over many tiles; latency claim gated on it).
- [M2_plan.md](M2_plan.md) and [M2_result.md](M2_result.md): milestone M2 plan, bars and result (cycle and energy model: counts, cycles, decode and energy pass; latency against the earlier model fails).
- [M1_result.md](M1_result.md): milestone M1 result (SIMULATED); [M1_fix_plan.md](M1_fix_plan.md) and [M1_fix_result.md](M1_fix_result.md): the W8A8 transformer fix (bars met with mixed precision; the loss shows quantisation was already harmless).
- `sim/gpu_sim.rs`: functional simulator (Rust, `rustc -O gpu_sim.rs`; usage in the file header).
- `m1/export_models.py`: trains the two test models and writes tensors, programs, references; `m1/m1_check.py`: the checks; `m1/results/`: counters and check output.

Related: [Hardware index](../HARDWARE_INDEX.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Home](../../README.md)
