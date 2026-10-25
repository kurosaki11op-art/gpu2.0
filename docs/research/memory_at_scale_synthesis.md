---
title: Managing memory as L scales - what the chip and memory papers say (25 Oct 2026)
tags: [l, research, synthesis, memory, energy, hardware]
---

# Managing memory as L scales: synthesis of the memory and on-chip reading (25 Oct 2026)

Sources (full-text reads by parallel readers; numbers are the papers' or vendors' own, not reproduced by us; several vendor sources were blocked by the sandbox proxy and are marked UNVERIFIED in the notes): [compressed and sparse inference hardware](papers_notes/stanford_memory_a.md) (EIE, Deep Compression, pruning, survey); [IO-aware design and memory tiers](papers_notes/stanford_memory_b.md) (FlashAttention 1 and 2, Monarch, SN40L); [state size and recall](papers_notes/stanford_memory_c.md) (H3, Zoology, Based, Mamba); [Stanford memory-centric hardware](papers_notes/stanford_memory_d.md) (SCNN, Capstan, hyperdimensional nanosystem, Deep Compression); [Cerebras, Groq, Graphcore](papers_notes/onchip_memory_chips_a.md); [Dojo, Tenstorrent, d-Matrix, in-memory macros, xAI](papers_notes/onchip_memory_chips_b.md).

## What the evidence says
1. **Data movement, not arithmetic, is the cost.** 45 nm (Horowitz, second-hand): int32 add about 0.1 pJ, small SRAM access 10 to 100 pJ per 64 bits, off-chip DRAM 1,300 to 2,600 pJ per 64 bits; a 32-bit read is 5 pJ from SRAM and 640 pJ from DRAM (128 times). In EIE's processing element only 12.7% of power is arithmetic and 74% moves index and weight data: once the multiplier is gone, **memory layout decides efficiency**.
2. **Every step outward loses 1 to 2 orders of magnitude of bandwidth** (Graphcore IPU, MEASURED): local 31 TB/s at 6 cycles, on-chip exchange 7.7 TB/s, chip to chip 108 GB/s. Cerebras and Groq make the same choice (memory in the compute tile; vendor figures: 48 KB per core and 40 GB total, 220 MiB SRAM respectively); a third party measured 10 to 20 times faster decode than an A100 cluster on Cerebras (WaferLLM).
3. **Compression keeps accuracy and makes the table fit on chip**: prune plus shared codes plus coding gives 35 to 49 times (Deep Compression, MEASURED by the authors) with no accuracy loss down to about 3% of the size; skipping zero inputs saves about 3 times energy; allocated hashed banks lift bank use from 32% to 80% for 0.8% of area (Capstan, 15 nm synthesis).
4. **Memory must grow with what is remembered**: any causal recurrent model needs at least about N bits of state to recall N independent key-value pairs (Based Theorem 3.1, Zoology Corollary H.24). The goal is slow growth and sparse touching, not constant size. Additive writes with sparse or binary features are counter increments (no multiplies); recall rises with the number of hashed features; a 64 to 128 token exact window recovers 90.8% of attention's recall at about 1e-5 of the latency of a 4,096 window.
5. **Tiers and conditional use of memory**: SN40L keeps 520 MiB SRAM, 64 GiB HBM, up to 1.5 TiB DDR; only 1 of 150 experts is hot at a time (authors' own model against DGX). Fusion of steps gave 2 to 13 times.
6. **In-memory compute macros are far better on paper than as chips**: 13 to 17 fJ per operation for a modelled charge-trap macro, 75.7 TOPS/W for the macro against 14.4 for the whole chip; in that chip the digital part drew 85 W against 68 W for the memory macros. Claim only MODELLED numbers; do not go analog.
7. **Tenstorrent's tile SRAM has atomic increment and compare-and-increment as hardware primitives** (5 bank cycles each): the same operation as L's counter update; a 4-byte payload rides on a 32-byte flit, so events must be packed.
8. **Wafer faults**: logical tile addresses with a boot-time defect map and spare tiles; barriers instead of caches and arbiters for bounded latency.
9. **xAI has no public chip**: it buys Nvidia GPUs (Colossus) and its custom work is cooling; Dojo is Tesla's.

## Design rules for L's tiles that follow (decisions, in order of cost)
1. Spend nearly all tile area on SRAM (our synthesized 8 KB tile on SKY130 is 95% memory).
2. Counters update in one access: read, increment, saturate, write (already the behaviour of the bank in `l_tile.v`).
3. Compress the tables: prune, shared 2-bit codes, column layout with skipped zeros; test MEM-C1 (accuracy and bytes read; expected 15 to 30 times, ESTIMATED).
4. Files clauses under an active positive literal so only active entries are read (keyed evaluation, see [L-Deep attempts](../../hw/results/ldeep_attempts.md)).
5. Hash recall of the top few candidates so bytes per decision stay roughly flat with class count (MODELLED: about 41, 34 and 41 KB at 10, 100 and 1,000 classes, against 41 KB, 410 KB and 4.1 MB for a flat scan).
6. Pack events; logical addresses with a defect map for wafer scale.
7. Normalise every claim by process node and label it ESTIMATED or MODELLED; our 130 nm tile cannot be compared with 5 nm SRAM densities directly.

## What this does not say
Memory on chip is already what Cerebras, Groq, Graphcore and Dojo do, with large budgets and multiply-accumulate hardware. L's possible edge is the algorithm: counters, lookups and sparse events, with local learning. That is unproven at scale.

Related: [Docs index](../INDEX.md), [Wafer design study](../L_wafer_design.md), [Paper notes index](papers_notes/INDEX.md), [Journal](../journal.md)
