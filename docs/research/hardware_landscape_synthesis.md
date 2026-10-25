---
title: Blackwell, Cerebras and the memory physics - what to learn, where a different design could win (25 Oct 2026)
tags: [l, research, synthesis, hardware, memory, energy]
---

# Blackwell, Cerebras and memory physics: what to learn, and where L could differ (25 Oct 2026)

Founder's rule: learn from them, do not copy. Sources are the three full studies: [NVIDIA up to Blackwell](papers_notes/nvidia_blackwell_study.md) (9 arXiv papers; NVIDIA's own pages blocked, so vendor specs are second-hand), [Cerebras in depth](papers_notes/cerebras_study.md) (about 22 arXiv papers; Cerebras whitepapers and Hot Chips blocked), [memory technologies](papers_notes/memory_technology_study.md) (14 arXiv papers), plus the earlier [memory-at-scale synthesis](memory_at_scale_synthesis.md). Numbers are those of the papers; "MODELLED" and "vendor" are as the source states.

## The two designs side by side
| | NVIDIA B200 (package) | Cerebras WSE-3 (wafer) |
|---|---|---|
| Fast memory | per-SM registers 256 KB (about 37 MB), tensor memory 256 KB per SM (about 38 MB), L2: about 112 MB of SRAM in total, 0.06% of the HBM | 48 KB SRAM per core (same since WSE-1), 44 GB in total (vendor) |
| Big memory | 192 GB HBM3e, 8 TB/s vendor, 4.14 TB/s measured on B200 (52%; large arrays not run); HBM latency about 270 ns | none on the wafer; weights streamed from outside, data enters at most 1.2 Tb/s (WSE-2) |
| Power | 1,000 W (vendor); power depends on the data: under 200 W on zeros, at the cap on random data (H800) | 20 to 23 kW |
| Efficiency evidence | tensor ops about 0.17 to 0.38 pJ per op on Hopper (derived), about 6 pJ per FLOP in a real training run | 96 to 179 times Frontier GPUs on molecular dynamics, 280 to 606 times on GEMV, prefill 1.6 to 2 times an A100 at up to 20 times the energy |

## Weak points the papers expose (hypotheses for a different design)
1. **Decode on GPUs is memory-bound by construction**: every token reads all the weights from HBM (about 1 to 4 operations per byte) and the ridge needs a batch of 240 to 465. Compute grew about 7 times from A100 to B200 while bandwidth grew about 4 times.
2. **Cerebras spends about half of every tile on general compute logic that sits idle on lookup and counting work.** Its table-lookup run (8.36 billion lookups per second, 130 times one A100) reaches only **1.97% of a dedicated ASIC's per-transistor efficiency**. A tile that is almost all memory and one counter operation attacks that gap directly; our synthesized tile is already 95% memory.
3. **Cerebras is limited by tiny per-core memory and a narrow door**: 48 KB per core, a 44 GB cap (models above about 13B cannot stay resident), 24 route colours, one entry port, global reductions cost about the square root of the core count in cycles, cooling is more than 90% of the chassis volume, and one wafer is one point of failure.
4. **Network energy can dominate**: one package hop costs 0.25 to 0.5 pJ per bit, about the cost of a local lookup (UCIe), while an SRAM access is about 0.5 pJ per bit at 40 MB and 2.8 at 1 GB (7 nm, MODELLED) and HBM3e 3.4 to 5.7.
5. **Memory is not equal**: HBM costs at least 5 to 10 times per bit more than DRAM; SRAM cell area stopped scaling from 5 to 3 nm (0.021 square micrometre); the memory wall is compute 3.0 times per two years against DRAM bandwidth 1.6 and interconnect 1.4.

## What L could do differently (hypotheses, none tested on our design)
- **A pure lookup-and-counter tile**: one read-increment-saturate-write macro per access, no arithmetic units, almost all area memory (against Cerebras's idle logic). Tenstorrent already puts atomic increment in tile SRAM, so the primitive is realistic.
- **Memory matched to data lifetime**: a small SRAM for hot, frequently written counters in front of a large gain-cell or eDRAM array for read-mostly tables (up to 3 times lower energy and 4 times lower area reported by GainSight, modelled).
- **Decisions kept inside one tile, few bits per hop**, so network energy does not dominate.
- **Efficiency without batching**: cost per token set by the lookups made, not by the batch needed to fill compute.
- **Tile pool with logical addresses and a defect map** instead of one giant wafer.

## Honest limits
- None of this helps if the model's quality falls: our counting language model lost to a small neural model at equal memory below about 0.5 MB, and L's clause layer costs more reads than L's table. A lookup tile is only as valuable as the accuracy of what it looks up.
- Comparing L with a GPU is only meaningful at equal task quality; we do not have that comparison yet. Our own estimates must be labelled ESTIMATED or MODELLED and normalised by process node (our synthesized tile is 130 nm).
- Cerebras and NVIDIA numbers here are vendor or survey figures where their own pages were blocked.

## Next tests that follow
1. Table compression (prune, shared 2-bit codes, skipped zeros): accuracy against bytes read (MEM-C1).
2. Clauses that must hold a positive literal, evaluated only when active.
3. Tile cost model from RTL counts with sourced constants (pJ per bit by level, hop energy 0.25 to 0.5 pJ per bit).
4. Scaling test: memory and accuracy against number of classes and tasks.

Related: [Docs index](INDEX.md), [Memory at scale synthesis](memory_at_scale_synthesis.md), [Wafer design study](L_wafer_design.md), [Paper notes index](papers_notes/INDEX.md), [Journal](journal.md)
