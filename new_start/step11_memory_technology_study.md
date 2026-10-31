---
title: Memory technology study - which memory could close the SRAM cost failure (31 Oct 2026, MODEL plus sourced facts)
tags: [spark, new-start, memory, mram, edram, pim, cost, study, failure]
---

# Memory technology study (31 Oct 2026)

**MODELLED scan plus qualitative sourced facts.** Scan: [`step5_worst_case_model.rs`](experiments/step5_worst_case_model.rs) with four new switches (`MM2GB`, `SRAM_PJ`, `BW_SCALE`, `LEAK`), [full scan](experiments/step11_memory_scan.log), [PIM what-if](experiments/step11_pim_what_if.log). The bar was written in the source before the run: a memory scenario is **viable** if, with the reticle-chip option at $1,330 per chip, 16-bit cache, 4-bit weights, the GPU priced at manufacturing cost ($3,320), the **worst corner shows cost advantage at least 2x and energy advantage at least 5x.** Follows [step 10](step10_capacity_levers_result.md), which derived the requirement.

## What the scan says the memory must deliver (180 scenarios)

Density (bits per mm2 relative to SRAM at the same chip price) is what decides cost; read energy, bandwidth and standby power decide energy and speed.

| density vs SRAM | best worst-corner cost advantage (over all other settings) | viable scenarios |
|---|---|---|
| 1x (SRAM) | 0.62x | 0 |
| 2x | 1.12x | 0 |
| 3x | 1.58x | 0 |
| **5x** | **2.2x** | **11 of 36** |

Interpolating, the cost bar needs **about 4.2x or more** the bits per area of SRAM at no extra price per chip. In the viable cases read energy is 1.0 pJ/bit or lower (0.3 to 1.0 tested), bandwidth per GB is at least 0.3x the SRAM wafer's, and standby or refresh power is at most 1.6 W/GB (3.0 W/GB breaks the energy bar in several cases). A bandwidth of 0.1x loses the cost bar.

## The candidates, with what the sources say (vendor and trade-press statements; none read in full; no foundry macro data found)

| technology | density | read energy and speed | other facts | fit to the requirement |
|---|---|---|---|---|
| **Embedded MRAM** | one-transistor cell, 8-14 F2 against 40-60 F2 for SRAM in a vendor table (nodes not matched), about 3x to 7x smaller cell; a foundry executive estimates 2x or better density; macros up to 1 Gb against about 2 Mb for SRAM ([Synopsys](https://www.synopsys.com/articles/emram-low-power-advanced-nodes.html)) | **not found**; write energy listed at 5 pJ/bit | relative cost 0.1x to 1x of SRAM (vendor ratio); available at 22 nm (eMRAM) and a 14/12 nm variant aimed at replacing SRAM working memory ([TSMC roadmap](https://www.eenewseurope.com/en/mram-set-to-replace-sram-says-tsmc-roadmap/), [scratchpad](https://www.eenewseurope.com/en/tsmc-moves-to-mram-for-scratchpad-memory/)) | **the only candidate whose sourced density comes near the 4.2x need** (cell ratio yes, whole-macro density about 2x by one estimate); read energy, speed and added wafer cost unknown; write energy is costly for a cache written every step |
| **Gain-cell and other embedded DRAM** | denser than SRAM, not quantified ([survey](https://upcommons.upc.edu/entities/publication/e09ea2ba-ae1d-4cd7-8cd3-7f9f12398bd2/full), [stackable gain cell](https://arxiv.org/pdf/2503.06304)) | not found | retention tens of microseconds (1T1C, about 170 microseconds projected at 7 nm) to seconds for oxide-semiconductor cells at 85 C, so refresh power; no confirmed production at 5 or 7 nm; one company is commercialising it | **unproven**: density plausible, refresh and availability unresolved |
| **DRAM with compute inside (HBM-PIM, AiM)** | DRAM economics: HBM3E sells for $12-17 per GB (third-party estimates) | internal bandwidth about 2 TB/s per HBM-PIM cube against about 307 GB/s external ([HPIM paper](https://arxiv.org/pdf/2509.12993)); energy per bit not found | compute is limited (AiM: about 1 TFLOPS per chip; a PIM unit at 400 MHz because of stack heat); vendor claims up to 10x speedup on a large model at lower cost and energy ([SK hynix talk](https://cse.snu.ac.kr/en/community/seminar/1007)) | fixes cost, **but compute-starved at large batch** (below) |
| **3D stacking of SRAM** | does not cut silicon cost per bit: each layer still costs wafer area | | | does not meet the density need on cost |

## What-if: DRAM economics with SRAM-like compute (not a real product)

If a chip held 77 GB at $1,330 ($17 per GB, HBM pricing), with 0.2x the SRAM wafer's bandwidth per GB and 1.5 pJ/bit read energy (**assumed, no source**), the model gives cost advantage **7.2x**, energy advantage **4.0x** (fails 5x; 2.3x at 3 pJ/bit), 182 tokens per second per user, 12 chips. **That result assumes logic-class compute on those chips** (I let compute scale with area as for the SRAM chips). Real DRAM-process compute is about 100 times less (AiM: about 1 TFLOPS per chip against about 170 TMAC/s per chip assumed here): at batch 1,024 the 12 chips would need about 3e13 multiply-adds per step, seconds on 12 TFLOPS. **A DRAM-PIM machine is therefore a low-batch, low-latency machine, not a high-throughput one**, and at low batch its cost per token is poor. Adding real compute dies brings back a GPU-like design.

## Verdict

- **No memory technology with sourced numbers closes the cost failure today.** The scan sets a clear requirement (at least about 4.2x SRAM density at SRAM-like price, read energy 1.0 pJ/bit or lower, bandwidth at least 0.3x SRAM, standby at most 1.6 W/GB). Embedded MRAM is the closest candidate by cell size, but read energy, speed and wafer cost are missing, and the macro-level density estimate (about 2x) is below the need.
- **Decision needed from data, not modelling:** the missing numbers are foundry macro data (area, read energy, access time, cost adder) for eMRAM at 22 nm and 14/12 nm, normally in ISSCC or IEDM papers or under foundry NDA. I could not find them with web search; they are the next evidence to obtain.
- **If they do not arrive,** the large-model SRAM system keeps its status: a speed-and-energy claim at best cost parity (central) or 1.6x worse (worst corner); the cost bar is not moved.

Related: [Step 10 capacity levers](step10_capacity_levers_result.md), [Step 7 cost result](step7_cost_basis_result.md), [Step 6 SRAM energy](step6_sram_energy_result.md), [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Docs index](../docs/INDEX.md)
