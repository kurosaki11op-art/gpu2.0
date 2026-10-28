---
title: One chip, three layers - memory map, die area, energy management and a cheap way to fabricate
tags: [spark, result, estimate, accelerator, cost, architecture]
---

# One chip, three layers (28 Oct 2026)

Founder's plan: for the pitch, fabricate one layered chip with all three layers (L Cortex, L Deep, a shared memory block), and while building them find a cost-efficient way to fabricate and a way to manage memory and energy. This note works that out from numbers already in the repo. **ESTIMATED / MODELLED; nothing here is measured on silicon.** Script and log: [one_chip_three_layers.py](../brain/experiments/month5/one_chip_three_layers.py), `one_chip_three_layers.log`. Real inputs: our SKY130 layout ([Cortex ASIC estimate](cortex_asic_estimate.md): 84 KB of memory in 63 OpenRAM macros, 0.285 mm2 per 2 KB macro, logic 0.84 mm2). L Deep sizes are MODELLED in the [accelerator design](../../docs/L_accelerator_design.md) (ternary weights 227 KB, state 35 KB at d=128). The 256 KB shared block, the Deep logic area and the density of other processes are my assumptions.

## 1. Memory map (KB)

| block | KB | source |
|---|---|---|
| Cortex: table, dream counts, list buffer | 84 | layout |
| Deep: ternary weights, d=128 | 227 | MODELLED (510 at d=192) |
| Deep: delta-rule state, scan, conv | 35 | MODELLED |
| Shared block: embeddings, buffers, replay store | 256 | ASSUMED |
| **Total** | **602** (922 at d=192) | |

The whole three-layer chip needs about 0.6 to 0.9 MB. That is small: the earlier 1 GB sizing was for GPU-class physics and models, not for the pitch chip.

## 2. Die area by process (ESTIMATED)

| process | memory | logic | die |
|---|---|---|---|
| SKY130, open macros (what our layout used, 7 KB per mm2) | 86 mm2 | 2.8 | **89 mm2** |
| SKY130, denser memory compiler (assumed 4x) | 21.5 | 2.8 | 24 mm2 |
| 28 nm (assumed 7 Mb per mm2) | 0.7 | 0.26 | **1.0 mm2** |
| 16 nm (assumed 14 Mb per mm2) | 0.3 | 0.09 | 0.4 mm2 |

**This is the biggest practical finding.** With the open macros the chip is too large to be a cheap test chip (even Cortex alone was 18.8 mm2 and a 31 mm2 die in layout), while on a mature commercial node the same chip is about 1 mm2, where die cost is cents to dollars and the price is set by the shuttle and mask, not by silicon. The memory, not the logic, decides the cost, so the first cost lever is the memory type (denser compiler or a commercial mature node), not the design.

## 3. Energy and memory management (ESTIMATED, 45 nm constants)

**L Deep, one token, every ternary weight read once (dense case):**

| memory organisation | nJ per token |
|---|---|
| one 227 KB array | 1,065 |
| 32 KB banks | 608 |
| 8 KB banks, wake one at a time | 318 |
| 8 KB banks plus skipping silent FFN neurons (5% fire, saves 31%) | 219 |

Reads are about 91% of Deep's energy, so **how the memory is split and gated is worth 3 to 5x, more than any arithmetic choice** (consistent with the [primitive test](arithmetic_primitive_test.md)). The same lesson is in our layout: gating every SRAM port cut Cortex power from 366 to 77 mW and the lighter clock tree to 47 mW.

**L Cortex:** the operation count says 9.4 nJ per decision, our own layout says 0.18 to 0.26 uJ, **20 to 28 times higher**. The pitch must quote the layout figure until the gap is closed (compact die, fewer flip-flops, finer gating), as the layout note already says.

**Power domains:** Cortex always on (it is the router and decides easy cases), Deep woken only on the share r of tasks it is needed for, shared memory banked and gated per bank. Average energy per task (Cortex 0.22 uJ plus r times Deep 0.32 uJ): r=5% 0.24 uJ, r=20% 0.28 uJ, r=100% 0.54 uJ. The share r is measured for images (about 20% routed, [routed second pass](routed_second_pass.md)) and unknown for language.

## 4. Cost-efficient fabrication path (REASONING plus the numbers above; prices need quotes)

1. **Fix the memory problem first** (free, in simulation): move the encoder's 17,000 flip-flop memories into SRAM, compact the floorplan, finish gating. This shrinks area and power whatever the process.
2. **Pick the process by area:** if the chip must stay under about 10 mm2 on a shared open shuttle, it needs a dense memory compiler; if a mature commercial node is reachable, the same chip is about 1 mm2. Get a quote for both (shuttle prices were not found; do not plan on a number).
3. **Build in stages that each give a measurement:** FPGA (done for Cortex), then one test die with all three layers at small sizes (Deep at d=128, shared block small), because the 0.6 MB map is already small.
4. **Keep layers as power domains on one die for this first chip** (no chiplet links, no packaging cost); the chiplet kit stays a later roadmap item ([layered product line](layered_product_line.md)).

## 5. What is not known (so the pitch must not claim it)

L Deep has no layout and no measured energy; its numbers are modelled from the design doc and a 45 nm constant table. The 256 KB shared block is a guess. Cortex's layout is not sign-off (detailed routing did not finish). Silicon power, speed and the cost of any shuttle are unknown.

Related: [Results index](INDEX.md), [Cortex ASIC estimate](cortex_asic_estimate.md), [Layered product line](layered_product_line.md), [Cost by node](cost_by_node.md), [Accelerator design](../../docs/L_accelerator_design.md)
