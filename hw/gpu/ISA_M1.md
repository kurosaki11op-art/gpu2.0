---
title: Our GPU, milestone M1 - instruction set, programming model and functional simulator (31 Oct 2026)
tags: [spark, gpu, isa, simulator, m1, programming-model]
---

# M1: instruction set, programming model, functional simulator (31 Oct 2026)

Charter: [own GPU charter](../../docs/own_gpu_charter.md), milestone M1. **Version 0 of the instruction set**: coarse, tensor-level, written to be executed by a functional simulator first and lowered to tile hardware later. Nothing here is a hardware result.

## Machine model

- **Tiles in a 2D mesh.** Each tile has a **local SRAM** (4 MB in the INT8 configuration), a **multiply-add array** (INT8 x INT8 into INT32, plus an FP32 path for the reference configuration) and a **vector unit** (add, multiply, normalisation, softmax, activation functions, maximum pooling).
- **Weights stay put.** A weight tensor is placed in one tile's SRAM once (`W`) and never moves; activations move between tiles over the mesh. This is the weights-stationary dataflow of the energy and cost models.
- **Every tensor has a home tile**: the tile that produced it (activations) or holds it (weights). An operation executes on a tile; inputs homed elsewhere are fetched over the mesh, and the simulator charges **bytes x hops** (Manhattan distance on a square mesh).
- **Two configurations:** `fp32` (reference: 4-byte weights and activations) and `int8` (weights 1 byte, quantised per output channel at load; activations 2 bytes in storage, quantised per row to INT8 inside each matrix operation, accumulated in INT32, dequantised to FP32; vector operations in FP32).

## Instructions (one per line; an optional `#tag` last token groups counters by layer)

| instruction | meaning |
|---|---|
| `W name tile` | place weight `name` in `tile`'s SRAM; capacity checked in the `int8` configuration |
| `MM out a w bias tile` | `out = a @ w + bias` on `tile` (`w` must be homed there; `bias` may be `-`); `a` is `[m,k]` (leading dimensions flattened) |
| `CONV out x w bias cin kh kw tile` | valid convolution, stride 1, input `[1,cin,H,W]`, `w` stored as `[cin*kh*kw, cout]`; lowered inside the tile to a patch gather plus the same matrix operation |
| `GATHER out table ids tile` | rows of `table` selected by the integer tensor `ids` |
| `ADD out a b`, `MUL out a b` | element-wise |
| `RELU out a`, `GELU out a` | activations (GELU is the tanh form) |
| `LN out a gamma beta` | layer normalisation over the last dimension (epsilon 1e-5) |
| `ATTN out q k v heads tile` | causal multi-head attention over `[T,d]`; softmax in FP32; key and value tensors are read from the tile's SRAM |
| `MAXPOOL2 out x` | 2 x 2 maximum pooling on `[1,C,H,W]` |
| `FLATTEN out x` | reshape to `[1,N]` |

## Counters (reported per tag and in total)

`macs` (multiply-adds actually executed, causal attention counts only the lower triangle), `sram_read_bytes`, `sram_write_bytes`, `mesh_byte_hops`, `vector_ops`. Byte sizes: `int8` weights 1, activations 2; `fp32` both 4.

## Programming model

A model is exported as (1) a tensor store (`tensors.bin`, `manifest.txt`), (2) a program (`program.txt`) produced by a **mapper** (Python, `hw/gpu/m1/export_models.py`), which places each weight on a tile (first fit) and emits the instruction list. The simulator (`hw/gpu/sim/gpu_sim.rs`, Rust, standard library only) executes the program for each input and writes the output tensor and the counters.

Related: [Own GPU charter](../../docs/own_gpu_charter.md), [Hardware index](../HARDWARE_INDEX.md), [Workload map](../../docs/gpu_workload_map.md)
