---
title: L hypothesis, falsification tests and fabrication plan
date: 2026-10-22
tags: [L, hypothesis, fabrication]
---
# The L hypothesis, how it can fail, and the silicon plan

**Hypothesis (not a result).** A brain-style model with constant-size state, sparse event-driven activity and low-bit weights, on a chip built for it, needs far less memory traffic and energy per token than a transformer on a GPU at the same quality, and so less scarce HBM, heat and water. The model comes first: the savings come from its state size, sparsity and low-bit weights; a chip can only exploit them. L Cortex proves the principles at small scale only.

**Falsified if (my proposed thresholds, not data):** (1) L loses its quality edge at larger sizes or when made matrix-free; (2) a fused GPU implementation gets within about 3x of the simulated chip; (3) a transformer chip with the same memory budget matches its energy per token; (4) the exact-recall unit adds nothing outside copy tests.

**Gates, in order:** measure the model (firing rates, ablations, seeds: [prompt](../prompts/L_facts_for_accelerator_prompt.md)); fused GPU baseline; matrix-free version keeps its quality; bit-exact simulator with energy model; FPGA; then silicon. Design notes: [L accelerator design](L_accelerator_design.md).

**Silicon, node and size (all costs ESTIMATED from public reports recalled from memory; verify before quoting):**

| Node | Access | Cost |
|---|---|---|
| 130 nm | open PDK (SKY130): prototype only, not comparable to a GPU | free flow; shuttle about $10k-50k |
| 28-65 nm | mature; via a university or a Europractice-style programme | shuttle about $50k-300k |
| 5 nm class | today's data-centre GPUs (TSMC 4N, die up to about 814 mm2) | wafer about $17k (CSET 2020 table); design tens of millions of dollars |

**Material:** silicon CMOS is the only practical choice for dense logic (mature, high yield, full tools). Limits: cost and mask NRE at advanced nodes, power density and heat, SRAM that no longer shrinks as fast as logic, supply concentrated in a few fabs, fab energy and water. GaN and SiC suit power electronics, compound semiconductors suit RF and optics, 2D materials and memristors are research stage: none is ready for dense logic. Non-volatile memories (MRAM, ReRAM) are a later option for weight storage.

**Plan:** write the RTL node-agnostic; compare energy against GPUs at a GPU-class node using published scaling (ESTIMATED, uncertain: our op energies are 45 nm values); prove on an FPGA; tape out at an accessible mature node when funded. A 5 nm-class chip needs tens of millions of dollars and foundry access we do not have, so it is not claimed.

Related: [Docs index](INDEX.md), [L accelerator design](L_accelerator_design.md), [Project memory](PROJECT_MEMORY.md)
