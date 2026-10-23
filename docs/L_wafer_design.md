---
title: L wafer-scale design study (paper design, 23 Oct 2026)
date: 2026-10-23
tags: [L, accelerator, wafer, multichip, design]
---

# L wafer: a Cerebras-class design for sparse lookup models (PAPER DESIGN, ESTIMATED; nothing built)

**Decision (founder, 23 Oct 2026):** keep all model memory on chip (no DRAM or HBM) and scale by tiling, as Groq and Cerebras do. This note is the architecture for a wafer-scale L machine, to be refined by simulation. **It is a design study. Nobody here can fabricate a wafer; the near-term deliverables are the architecture, a simulator and an FPGA or chiplet prototype.** Related: [L accelerator design](L_accelerator_design.md), [L hypothesis](L_hypothesis.md), [multi-chip test](../hw/results/multichip_lm.md), [counting language model](../hw/results/counting_lm.md).

## 1. What we are building a competitor to (public figures, recalled from memory, verify)

| | Groq | Cerebras WSE-3 | Graphcore IPU |
|---|---|---|---|
| On-chip memory | about 230 MB per chip | about 44 GB per wafer | about 900 MB per chip |
| Scale-out | hundreds of chips, compiler-scheduled direct links | one wafer; weights streamed from external units for training | many chips |
| Core idea | no caches, everything planned at compile time | memory next to every core, defect-tolerant wafer | memory spread over many small cores |

All three keep model memory in SRAM next to compute. None of them is built for sparse lookup models; they do dense matrix work.

## 2. The L wafer idea

**Tile.** One tile = one lookup core (reads a table row, adds scores; the L Cortex core, scaled) + several SRAM banks (0.5 MB each) + a mesh router. The whole wafer is a 2-D mesh of tiles.

**Memory first.** Area split (assumed): about 62% SRAM, 10% lookup cores, 20% mesh, power delivery and test, 8% spare tiles to route around defects (Cerebras-style yield trick).

**Model mapping.** A big table (the counting language model, later an L language model) is split by hashed slot over all banks; a lookup is a short message to the owning tile and back. Frequent rows are copied to many tiles (measured need: 2.1 times load imbalance at 64 chips).

**Learning.** Counting updates and dreams run inside the owning tile (no read-modify-write over the mesh): the counter lives where the increment happens.

## 3. Sizing (script `hw/brain/experiments/month5/wafer_sizing.py`, assumptions inside, ESTIMATED)

| Node | Table memory on a 46,000 mm2 wafer | 0.5 MB banks | Peak lookups per second | Per-token latency across the wafer |
|---|---|---|---|---|
| 130 nm (our open macros, 0.007 MB/mm2 measured) | about 0.2 GB | 401 | 2e10 | 0.6 us |
| 28 nm | about 17 GB | 34,000 | 2e13 | 6 us |
| 7 nm | about 98 GB | 200,000 | 2e14 | 14 us |
| 5 nm | about 112 GB | 230,000 | 2e14 | 15 us |

Reading: at 7 nm the model memory is about twice WSE-3's 44 GB because more of the area is memory and the lookup cores are tiny; at our open 130 nm it is 0.2 GB, so the open process cannot compete on capacity and is only a prototype vehicle. Peak lookups assume every bank busy every cycle; real throughput is lower (load imbalance, sequential token steps). Latency is dominated by the eight sequential steps crossing the mesh.

## 4. What a competitor needs that we do not have

| Need | Why it is hard | Our route |
|---|---|---|
| Foundry wafer-scale integration (stitching across reticles) | needs a leading-edge foundry partner and years | architecture and simulator now; partner later |
| Power delivery and cooling for kilowatts | tens of thousands of amps at about 1 V | out of reach; model only |
| Defect tolerance | a wafer always has defects | spare tiles and routing around them: design in RTL, test in simulation |
| Funding | wafer-scale companies raised hundreds of millions of dollars (verify) | none today |
| A model worth running | the memory is useless without a model of useful quality | the open test: quality of an L-style language model against memory |

## 5. Honest status and staged path

1. **Now (cloud):** tile and mesh simulator (cycle-level), hot-row copying, defect-tolerant routing, wafer sizing with real counting-model traffic.
2. **Months:** a small tiled prototype on FPGAs (several boards over serial links), measured lookups per second and power.
3. **With funding:** a multi-project tiled chip at a mature node, then a leading-edge node through a programme partner.
4. **Not claimed:** that L beats Cerebras or a GPU on useful AI today. The unproven part is quality: the counting language model has roughly n-gram quality at 8 MB; the wafer only matters if an L-style model reaches high quality at large size.

Related: [L accelerator design](L_accelerator_design.md), [L hypothesis](L_hypothesis.md), [Index](INDEX.md)
