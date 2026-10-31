---
title: hw/gpu - our own GPU (programmable accelerator): instruction set, simulator, exporter (31 Oct 2026)
tags: [spark, gpu, index]
---

# hw/gpu: our own GPU

Charter and milestones: [own GPU charter](../../docs/own_gpu_charter.md).

- [ISA_M1.md](ISA_M1.md): instruction set and programming model, version 0.
- [M1_result.md](M1_result.md): milestone M1 result (SIMULATED).
- `sim/gpu_sim.rs`: functional simulator (Rust, `rustc -O gpu_sim.rs`; usage in the file header).
- `m1/export_models.py`: trains the two test models and writes tensors, programs, references; `m1/m1_check.py`: the checks; `m1/results/`: counters and check output.

Related: [Hardware index](../HARDWARE_INDEX.md), [Own GPU charter](../../docs/own_gpu_charter.md), [Home](../../README.md)
