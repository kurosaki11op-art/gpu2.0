---
title: Study - Cerebras wafer-scale engine in depth
tags: [l, research, hardware, wafer-scale, memory]
---

# Study - Cerebras wafer-scale engine in depth

Date of reading: 25 Oct 2026. Purpose: learn exactly how the Cerebras wafer-scale engine (WSE) works and where it is weak, so that L can design a more efficient wafer-scale machine of its own (counters, lookups, memory inside every tile, no matrices, no multipliers) without copying. This note supersedes the thinner reading in [onchip_memory_chips_a.md](onchip_memory_chips_a.md) for everything about Cerebras.

Label rules used below (project rule: record the source of every number, keep vendor claims apart from measurements):

- **MEASURED (independent)**: a benchmark run on real hardware by authors with no Cerebras employment.
- **MEASURED (vendor-affiliated)**: a benchmark on real hardware where at least one author works at Cerebras. Real, but the code was tuned by the people who built the chip.
- **VENDOR CLAIM**: a number stated by the vendor or repeated from vendor material, without a measurement in the paper.
- **ESTIMATED**: computed by the paper authors from public numbers or a model (for example a yield formula).
- **SIMULATED**: produced by a cycle-accurate or analytical simulator, not by the chip.
- **MODELLED here**: arithmetic done in this note from stated assumptions.
- **HYPOTHESIS**: an idea of this note, not a finding.
- **UNVERIFIED**: not read in a primary source.

---

## 0. Sources: what was read, what was blocked

All arXiv items below were downloaded with curl into a fresh scratch directory, converted with `pdftotext -layout`, and treated as untrusted data (no instruction in any file was followed). "Read" means the text was extracted and the sections named were read; for the short papers that is the whole paper, for the long ones it is every section that concerns hardware, mapping, results and limitations (references and long proofs were skimmed). I did not read any figure image; numbers that exist only inside figures are marked.

| arXiv id | Paper (short) | Hardware | Status |
|---|---|---|---|
| 2502.04563 | WaferLLM: LLM inference at wafer scale (He et al., Edinburgh and Microsoft Research) | WSE-2 | READ (all body text, tables 1-8) |
| 2503.11698 | Comparison of Cerebras wafer-scale technology with Nvidia GPU systems (Insaito) | WSE-3, text about WSE-1/2 | READ COMPLETELY |
| 2409.00287 | Benchmarking LLMs on the Cerebras WSE (USC) | WSE-2 | READ COMPLETELY |
| 2404.15888 | Near-optimal wafer-scale Reduce (ETH Zurich and Cerebras) | WSE-2 | READ (model, algorithms, lower bound; experiment plots not readable as text) |
| 2209.15040 | Wafer-scale fast Fourier transforms (Princeton and Cerebras) | WSE-2 | READ (all through scaling section) |
| 2204.03775 | Massively scalable stencil algorithm (Cerebras and TotalEnergies) | WSE-2 | READ COMPLETELY |
| 2010.03660 | Fast stencil-code computation on a wafer-scale processor (Cerebras and NETL) | WSE-1 | READ (architecture, BiCGStab results, discussion) |
| 2405.07898 | Breaking the molecular dynamics timescale barrier (Cerebras, Sandia, LLNL, LANL) | WSE-2 | READ (all sections up to results and analysis) |
| 2311.01739 | Monte Carlo particle transport on AI accelerator hardware (Argonne and Cerebras) | WSE-2 | READ (architecture, kernel, decomposition, results, ASIC comparison) |
| 2404.16990 | Record acceleration of the 2D Ising model on the WSE (NETL) | WSE-2 | READ (abstract, method, mapping) |
| 2209.13768 | Field equation modeling API for the WSE (NETL and Cerebras) | WSE-2 | SKIMMED (abstract, architecture paragraph, benchmark set-up) |
| 2210.04795 | TensorFlow as a DSL for stencil computation on the WSE (Edinburgh, LLNL) | WSE-1 | READ (abstract, method, results) |
| 2601.17754 | MLIR lowering pipeline for stencils at wafer scale | WSE-2 and WSE-3 | READ (architecture, WSE-2 vs WSE-3, comparison with GPUs) |
| 2605.07954 | Stencil computations on Cerebras WSE (CStencil) | WSE-3 | READ (architecture, design, results, roofline) |
| 2604.27985 | Sparse matrix multiplication kernels on the Cerebras CS-3 | WSE-3 | READ COMPLETELY |
| 2304.03208 | Open compute-optimal language models trained on the Cerebras Wafer-Scale Cluster | 16 x WSE-2 | READ (the cluster and weight-streaming section and the scaling tables; the scaling-law and loss sections were skipped as not about hardware) |
| 2303.10464, 2303.11525, 2403.00952 | Sparse pre-training papers using the CS-2 (Cerebras authors) | WSE-2 | SKIMMED (only the statements about what the hardware sparsity kernels support) |
| 2310.09568 | Wafer-scale computing survey (Tsinghua) | Cerebras, Dojo, UCLA/UIUC | READ (architecture, packaging, power, cooling, fault tolerance sections) |
| 2407.02079 | Theseus: design-space exploration of wafer-scale chips for LLMs (Peking University) | model of wafer-scale chips | READ (method, yield model, case studies) |
| 2603.02737 | Ouroboros: wafer-scale SRAM compute-in-memory (ICT-CAS) | proposal, simulated | READ (architecture, fault tolerance, evaluation set-up) |
| 2608.28048 | AI hardware accelerators for LLMs: architectures and the memory wall | survey | READ (Cerebras section, tables) |
| 2407.10290, 2603.05266 | Switch-less dragonfly on wafers; network design for wafer-on-wafer systems | models | SKIMMED (only the lines about Dojo and wafer diameter) |

**Blocked or not obtained (all UNVERIFIED below):**

- The Cerebras weight-streaming white paper, the "100x defect tolerance" Cerebras blog and the wafer-scale cluster white paper: the proxy refused the connection (HTTP 403 on CONNECT) when retried today. Nothing from them was read. Every statement about them comes from the secondary papers above and is marked.
- The Cerebras Hot Chips slides (2021 and 2022), the IEEE Micro papers by Lauterbach and by Lie, and the Tesla Dojo Hot Chips papers: not on arXiv, not downloadable here. Facts attributed to them are second-hand through 2409.00287, 2503.11698 and 2310.09568.
- The technical report on sparse matrix multiplication on the WSE-2 (ETH Zurich, cited by 2604.27985) and the original Rocki/Cerebras long report: not read.
- The Pal et al. wafer-scale GPU case study (HPCA 2019): no arXiv copy found.
- **No paper read describes the SwarmX interconnect.** The name SwarmX does not occur in any of the extracted paper texts. All statements about it are UNVERIFIED; what the cluster paper describes is a "broadcast + reduce tree network" (section 6).

---

## 1. The numbers that matter (one table)

| Item | Value | Label and source |
|---|---|---|
| Wafer / chip area | 46,225 mm2 (215 mm square on a 300 mm wafer), 7 nm (WSE-2) | MEASURED fact quoted by 2209.15040, 2204.03775 |
| Dies on the wafer | 7 x 12 = 84, each about 17 x 30 mm, about 10,156 cores per die (66 x 154) | 2204.03775 (7 x 12 array); 2310.09568 figure 8 (dimensions) |
| Cores (WSE-1 / WSE-2 / WSE-3) | about 380,000 / 850,000 / 900,000 | VENDOR CLAIM via 2010.03660, 2204.03775, 2503.11698 |
| Cores a program can actually use (WSE-2) | fabric of about 757 x 996 (about 754,000) in the collectives paper; about 920 x 920 in the molecular-dynamics paper; 755 x 994 used in the stencil paper | 2404.15888, 2405.07898, 2204.03775. The sources disagree (section 14) |
| WSE-3 user layout | 762 x 1172 PEs (about 893,000) in the sparse-kernel paper figure | 2604.27985 figure 1 |
| Memory per core | 48 KB SRAM, same on WSE-1, WSE-2 and WSE-3, 8 banks of 6 KB, single-cycle load-to-use | 2010.03660, 2409.00287, 2605.07954 |
| Total on-wafer memory | 18 GB / 40 GB / 44 GB | VENDOR CLAIM via the papers |
| Memory bandwidth per core | WSE-2: 128-bit read + 64-bit write per cycle; WSE-3 text: two 64-bit reads + one 64-bit write (192 bit) | 2404.15888 / 2605.07954 |
| Aggregate memory bandwidth | 20 PB/s (WSE-2), 21 PB/s (WSE-3) | VENDOR CLAIM (22 PB/s also appears in 2502.04563) |
| Fabric link | 32-bit wavelet per cycle per direction, 5 ports (N, S, E, W, ramp), 1 cycle per hop | 2404.15888, 2204.03775 |
| Fabric colours (routes per router) | 24 virtual channels; WaferLLM says "5-bit address, fewer than 25 routing paths" | 2209.15040, 2502.04563 |
| Aggregate fabric bandwidth | 220 Pb/s (WSE-2), 214 Pb/s (WSE-3) | VENDOR CLAIM via 2503.11698 and 2601.17754 |
| Scalar all-reduce latency | under 1.5 microseconds across about 380,000 cores (WSE-1) | MEASURED (vendor-affiliated) 2010.03660 |
| Edge-to-edge latency | about 1 microsecond (WSE-2) | MEASURED (vendor-affiliated) 2405.07898 |
| Power | 20 kW (CS-1), 23 kW (CS-2 in MD paper), 16.1 kW idle to 22.9 kW peak, 22.8 kW average under a stencil load; CS-3 23 kW | MEASURED (vendor-affiliated) 2204.03775, 2405.07898; 2503.11698 for CS-3 (press figure) |
| Data into the wafer | at most 1.2 Tb/s (WSE-2); CS-3 is attached by 100 Gb/s Ethernet links | 2209.15040; 2605.07954 |
| Defect redundancy | about 1% spare cores plus spare fabric links per row | 2310.09568 (second-hand; primary blocked) |
| Estimated die yield without redundancy | about 60% for a 510 mm2 die at 0.09 defects per cm2 | ESTIMATED, 2310.09568 |
| Best measured win over GPUs | 130x (table lookup), 179x vs an exascale GPU system (molecular dynamics), up to 606x (one GEMV) | section 10, each with its caveats |
| Worst measured behaviour | CPU parity or worse above 99% sparsity for SpMM; prefill uses 1.2x to 20x more energy than A100 GPUs | 2604.27985; 2502.04563 tables 7-8 |

---

## 2. Core, tile and wafer structure

**One tile (a "PE", processing element)** contains four things: a small in-order processor core (the "compute engine", CE), a router, 48 KB of SRAM and a hardware task scheduler. The WSE-3 sparse paper and the stencil papers all show the same picture: the PE is a tile, the tile is repeated in a grid, the grid is cut into 84 dies that are stitched together on the wafer.

- *Core.* In-order. Instructions complete in order, except instructions on vectors that stream from or to the fabric, which can run as background "microthreads" (2209.15040). The core has a fused multiply-accumulate (FMAC). In 16-bit mode it does up to 4 FMACs per cycle (SIMD-4, "up to eight 16-bit operations per cycle" counting multiply and add separately); in 32-bit mode 1 FMAC per cycle, and some 32-bit operations are not SIMD (2209.15040, 2605.07954). The WSE-1 core supports nine concurrent threads (2010.03660, 2405.07898); the WSE-3 stencil paper says eight microthreads, of which six are available to the programmer (2605.07954).
- *Tensor descriptors.* The key architectural trick is the **data structure descriptor (DSD)**: a hardware register that holds base, length and stride of a vector in memory or a stream of wavelets. One instruction walks the whole vector with no loop instructions (2204.03775, 2209.15040). Vector setup still costs "tens of cycles" per operation, so one element per core is the least efficient mapping (2404.16990).
- *Router.* Five full-duplex ports (4 neighbours and the ramp to the core), each 32 bits per cycle. The router can move ten 32-bit messages per cycle (2405.07898). The router is physically decoupled from the compute part of the tile, which is what makes defect repair possible (2310.09568).
- *Memory.* 48 KB of SRAM, the only memory a core can address. No cache, no DRAM, no shared address space (2209.15040, 2204.03775). 8 banks of 6 KB with word interleaving. Zhang et al. also describe a 256-byte, 64-bit software-configured cache (2409.00287, quoting the vendor talk); no other paper confirms it, so UNVERIFIED.
- *Area split.* Vendor statement quoted by Zhang et al.: half the core area is SRAM, half is compute logic. Insaito says about 50% of the chip is SRAM, register files and fabric. Core size: about 0.05 mm2 (Insaito, WSE-3) and 228 x 170 microns = 0.0388 mm2 (survey figure 8, WSE-2). Compare an SM of an H100: 6 mm2 (Insaito table 4).
- *Clock.* 850 MHz in all three measured WSE-2 papers (2404.15888, 2209.15040, 2204.03775 do not state more); maximum 1.1 GHz quoted from the vendor (2409.00287, 2502.04563); 875 MHz in the WSE-3 stencil paper. One paper says a single configurable oscillator clocks the whole array (2405.07898); another says every core has an independent clock (2404.15888). Unresolved.

**Peak compute per core (vendor):** about 8.8 GOPS per core and 30 mW (survey table 2, computed by dividing totals). I do not trust the per-core power: it is total divided by core count.

**Programming view of the grid:** a program names a rectangle of PEs (the "layout"), assigns code to PEs, assigns routes to colours. The host streams data in through I/O channels on the west and east edges (2604.27985 figure 1).

---

## 3. Memory

- **Per core: 48 KB, fixed since 2019.** WSE-1 (14 nm) had 18 GB over 380,000 cores; WSE-2 (7 nm) 40 GB over 850,000; WSE-3 (5 nm) 44 GB over 900,000. Going from 7 nm to 5 nm bought only 10% more memory, because the vendor spent the density on compute and kept 48 KB (VENDOR CLAIM numbers; inference mine, HYPOTHESIS).
- **Everything is single-cycle and deterministic.** Memory access time is deterministic, no cache; run-to-run variation under 4% (2404.15888), under 1% (2209.15040), 0.8% load imbalance (2204.03775).
- **Memory bandwidth equals datapath bandwidth.** Two operand reads and one write per cycle, so a binary vector operation never waits (2405.07898). That is why stencils turned from memory-bound to compute-bound: arithmetic intensity 0.11 flop per byte against memory and 0.75 against the fabric, still compute-bound on the wafer, memory-bound on an A100 (2204.03775, MEASURED vendor-affiliated).
- **The cap is capacity, not bandwidth.** A 3D FFT of 1024 cubed (16 GiB out-of-place) is the largest power of two that fits (2209.15040). Fluid solves are limited to meshes that fit 18 GB (2010.03660). Models above about 13 billion parameters at 16 bits do not fit on one WSE-2: WaferLLM could only run a subset of layers of a 34B and a 72B model (2502.04563 section 7.1). The cap is also local: each core holds 48 KB, so tensors must be cut into tiny chunks and "pipeline parallelism is forced" because tensor parallelism would need 5 to 6 times more local memory (2502.04563 section 8, VENDOR-INDEPENDENT authors' estimate).
- **Capacity vs the L tile.** 44 GB for 900,000 cores is 48 KB each. A table-and-counter design wants memory to dominate: if the tile area is 80 to 90% SRAM instead of 50%, capacity per wafer could be 1.6 to 1.8 times higher at the same density (MODELLED here, assuming SRAM density is the same and the router costs the same; HYPOTHESIS).

---

## 4. Fabric: topology, bandwidth, per-hop latency, routing limits

**Topology.** Plain 2D mesh, nearest neighbour only, no express links, no torus wrap (2404.15888 had to emulate a ring by mapping, see their figure 7). Dies are joined by wires drawn across the scribe lines, so a hop between dies costs the same as a hop inside a die: "uniform topology, uniform bandwidth, guaranteed latency" (2405.07898, 2503.11698). The survey (2310.09568) gives the reasons for the mesh: easy physical implementation, and alternate paths exist when a router fails; tree topologies have fewer hops but are harder to repair.

**Bandwidth.** 32 bits per link per direction per cycle. Aggregate 220 Pb/s (WSE-2) and 214 Pb/s (WSE-3), VENDOR CLAIM. A core's injection bandwidth is one 32-bit word per cycle, one quarter of the peak 16-bit compute rate (2010.03660): the fabric is *not* faster than the compute. The collectives paper adds a hidden limit: there is one port between core and router, so a core cannot send on the x axis and the y axis in the same cycle, and 2D patterns gain less than expected (2404.15888 section 7).

**Latency.**

- One cycle per hop for a wavelet (about 1.2 ns at 850 MHz; MODELLED here).
- Ramp (core to router, router to core) about 2 cycles on the cycle-accurate simulator under ideal conditions, "around 7" on real hardware according to a reference cited in 2404.15888; so sending and receiving a wavelet costs 2 x T_R + 1 cycles of depth per dependent step.
- Scalar all-reduce across 380,000 cores under 1.5 microseconds (WSE-1, MEASURED vendor-affiliated).
- Edge to edge about 1 microsecond (WSE-2, MEASURED vendor-affiliated).
- The distance between two cores is up to N_w + N_h hops, "up to several thousand" in a million-core mesh, a 1,000x gap between local memory (1 cycle) and the far end (2502.04563, ESTIMATED by the authors).
- Router-local software relaying: if a route does not exist, a message must be relayed by software in an intermediate core, costing a per-routing latency beta that is larger than the per-hop latency alpha (2502.04563). This is where a hardware limit on routes turns into a 10x to 100x slowdown.

**Routing limits (the part that shapes every program).**

- A wavelet carries a 32-bit payload plus a *colour*. The colour selects a route. There are **24 colours** per router (2209.15040, 2404.15888, 2405.07898). Each router stores up to **four routing configurations per colour** and switches among them when a control wavelet arrives (2404.15888). Two wavelets arriving on the same colour in the same cycle give undefined behaviour, so programs must avoid it by construction.
- Routing is configured offline at compile time (2010.03660), though control wavelets can advance the table at run time (2204.03775, 2605.07954). That mechanism is what lets 24 colours serve a 25-point stencil: broadcast patterns that shift their root along the row, each using two colours (2204.03775).
- Hardware multicast: a router can copy a wavelet to several outputs at no extra cost (2404.15888). Router filters can select wavelets by count, so a core on a row can capture every k-th wavelet of a stream and let the rest flow on (2209.15040). That is how all-to-all transposes were built.
- A WSE-2 router had a quirk: each core had to send to itself as well as to its neighbours; WSE-3 removed that requirement and the same compiler output ran up to 38.1% faster (2601.17754). The WSE-3 NoC is otherwise described as unchanged (2502.04563).
- The route budget is the limiting resource. WaferLLM's design rules (the PLMR model: Parallelism, Latency, Memory, Routing) put routing on equal footing with memory (2502.04563 section 3).

**Reduce and all-reduce, from the collectives paper (SIMULATED model validated by MEASURED vendor-affiliated runs, less than 4% error).** The model has five terms: energy E (total hops), distance L, depth D (dependent steps), contention C, and number of links N, giving T = max(C, E/N) + L + (2 T_R + 1) D. The authors prove a lower bound for 1D Reduce and show their generated "Auto-Gen" tree is within 1.4x of it, the two-phase reduce within 2.4x, while the older vendor patterns can be 5.9x off at some sizes. On 512 x 512 PEs their two-phase variant is up to 3.32x faster (reduce) and 2.56x (all-reduce) than the vendor library. Takeaway: even on the best hardware network, a global reduction costs a number of cycles proportional to the square root of the core count unless routes are designed by hand.

---

## 5. How data and tasks are mapped (dataflow, tasks, routing)

**Execution model.** Dataflow with tasks. A task is a short non-preemptive code block activated by (a) an explicit activate, (b) the arrival of a wavelet of a given colour (a "data task"), or (c) completion of an asynchronous vector operation (2605.07954). Tasks run to completion; the hardware picks the next runnable one each cycle. The survey calls this a "dataflow trigger mechanism" (2310.09568). An actor-model reading is given in 2601.17754.

**Mapping rule that all applications follow:** map two of the problem dimensions to the two axes of the mesh and put the third dimension in the local 48 KB. Stencils (2204.03775, 2010.03660), FFT pencils (2209.15040), atoms (one atom per core, 2405.07898), batches of Ising lattices (2404.16990) all do it.

**What the papers show about mapping practice:**

- *Stencil (25-point, 3D).* Each core owns a column of nz cells. Neighbour data arrive by shifting broadcast patterns; vector FMACs apply coefficients to arriving data "on the fly". 51 floating-point instructions per cell; 69.6% of cycles busy, 11.6% idle on memory (MEASURED vendor-affiliated).
- *FFT.* A 3D FFT of n cubed uses n x n cores, one pencil per core, three compute phases and two transposes. The cycle count per 1D FFT is 3 n log2 n + 34 n + 34 log2 n in 16-bit and 6.5 n log2 n + 35 n + 36 log2 n in 32-bit (2209.15040). The transposes use broadcast-and-filter; each router reconfiguration costs about 30 cycles, so small messages pay a fixed tax.
- *Molecular dynamics.* One atom per core; a "marching multicast" sends position data to a square neighbourhood in two stages, with an occasional greedy re-assignment of atoms to cores (2405.07898).
- *LLM inference (WaferLLM).* Prefill: partition both dimensions of activations and weights over the mesh and use a new GEMM (MeshGEMM) built from cyclic shifts and an *interleave* that keeps every transfer to two hops; decode: replicate along one axis, use a K-tree all-reduce with K=2 for GEMV, and a "shift" KV cache that moves old rows upward so memory fills evenly (2502.04563).
- *Sparse matrix times dense matrix.* Rows of the sparse matrix are streamed in as column-index and value pairs; router PEs in a column forward each pair to the row of worker PEs holding the matching rows of the dense matrix; workers multiply-accumulate; partial sums flow south to accumulator PEs and then back to the host (2604.27985). This is the closest published mapping to an event-driven sparse row lookup.
- *Cross-section table lookup (Monte Carlo).* The big table is cut into 48 KB pieces spread over the grid; each row of cores holds all nuclides of a slice; a particle visits every core in its row, accumulating partial results; load is balanced by transferring particles and table segments between rows (2311.01739).

**Constraints that show up in every mapping:**

1. 48 KB per core forces decomposition into tiny blocks; a hot spot of one core (a row end, the KV-cache last row) becomes the failure point.
2. 24 colours force pattern reuse and run-time reconfiguration; collective libraries "reconfigure routers and give artificially slow results", so authors write their own (2404.15888).
3. Corner and diagonal communication has to be relayed in two stages (2605.07954); there is no diagonal link.
4. Nothing may rely on arrival order across colours; receive completion needs counters or sentinel control wavelets and the non-preemptive tasks need explicit barriers (2605.07954).
5. Mesh corners and edges are under-used: 4 corner cores had zero busy cycles in the stencil run; "edge cores are underutilised" in the GEMV profile (2204.03775, 2502.04563).

---

## 6. Models larger than the wafer: weight streaming, MemoryX, SwarmX

What is READ (2304.03208, MEASURED vendor-affiliated):

- The cluster they trained on, named Andromeda, is **16 CS-2 systems**, each with a WSE-2 of 40 GB SRAM and 7.5 PFLOP/s half-precision peak, 120 PFLOP/s together.
- **Weight servers and command servers** drive the CS-2s: they *broadcast the weights and control instructions through a broadcast + reduce tree network*, and the same network collects and reduces the gradients from all CS-2s. When the weight servers receive the reduced gradients they **run the optimiser step** and update the weights, and they save and restore checkpoints.
- **Activation / data workers** read an independent shard of the dataset from disk and send sub-batches to a CS-2. When a model needs activation checkpointing, the CS-2 can evict activations to its activation worker and refill them later.
- The execution mode is "weight streaming": weight servers stream weights to the wafer and collect gradients each training step. It "permits training models of size only limited by the memory capacity of weight servers", and they say they ran models beyond the full 175-billion-parameter size without changes other than the configuration. The weights never live on the wafer; only the current layer's weights, the activations and the gradients do.
- Scaling (MEASURED, weak scaling, speed relative to 1 CS-2): 15.50x, 15.87x, 15.62x, 15.45x, 15.32x, 14.52x, 15.45x on 16 CS-2 for seven model configurations; linear "within 9%". Strong scaling for batch sizes used in training: 7.1x to 7.9x on 8 CS-2s. FLOP utilisation relative to the smallest run stays within 8% (0.92 to 1.05).

What is only second-hand:

- **MemoryX** is the external memory: "DRAM and flash" holding weights, and it sends each layer's weights to the wafer and gets gradients back (2409.00287, quoting the vendor). Capacity 1.2 TB to 1,200 TB per CS-3 and models up to 24 trillion parameters, from the vendor press release (2503.11698, 2608.28048: "up to 1.2 PB"). In the scaling-law paper the servers are generic "weight servers"; the name MemoryX is not used there. The mapping of MemoryX to the weight servers is therefore an inference. UNVERIFIED.
- **SwarmX**: no paper read describes it. UNVERIFIED. The tree network of the scaling-law paper (broadcast of weights down, reduction of gradients up) is the only trace.
- **Bandwidth of the link to the external memory**: the papers state only the host links of the CS-3 ("100 Gb/s Ethernet", 2605.07954) and, for the WSE-2, a maximum transfer rate to the wafer of 1.2 Tb/s (2209.15040). The number of links is not stated; 12 x 100 Gb/s would give 1.2 Tb/s (inference only, UNVERIFIED).
- Consequence, **MODELLED here** (assumptions: all 1.2 Tb/s = 150 GB/s usable for weights, 16-bit weights): streaming the weights of a 175-billion-parameter model (350 GB) takes at least 2.3 seconds per pass; streaming the weights of the 13-billion-parameter model (26 GB) takes at least 0.17 seconds. Weight streaming is therefore a *large-batch* mode: the batch must be big enough that the compute per pass lasts longer than the stream, which is exactly what the papers say ("solid performance at small per-system batch sizes" means 33 to 264 sequences of 2048 tokens per CS-2 in their tables). For batch-one decoding it would give 2.3 seconds per token for the large model. That is the reason WaferLLM keeps the whole model resident instead. HYPOTHESIS (the real link may be faster than my assumption).
- Insaito's statement that training needs "8 to 16 GB per billion parameters" and table 3 (one WSE-3 is enough for any model size because MemoryX grows) is a vendor-derived argument, not a measurement.

---

## 7. Sparsity support

- **Hardware claim:** the cores "eliminate multiply-by-zero operations", scheduling is fine-grained dataflow so work is only done on non-zero data, which saves dynamic power and gives efficient *unstructured* sparsity (vendor statement quoted in 2409.00287, citing Lie 2023 and a Cerebras sparse-model paper). Not independently measured in the papers I read. The 125 PFLOPS WSE-3 peak in 2608.28048 "refers to sparse FP16, Cerebras having disclosed no dense equivalent": VENDOR CLAIM and the dense number is UNVERIFIED.
- **What exists in software:** the Cerebras PyTorch interface supports weight sparsity but **stores the matrix dense with a mask** (2604.27985), so it cannot hold a matrix larger than the wafer when dense. The sparse pre-training papers (2303.10464, 2403.00952) state that "the specialised kernels of the CS-2 were designed to facilitate training with **static** unstructured sparsity": dynamic sparsity (masks that change during training) is not supported by those kernels. Their measured-versus-theoretical speed-up figure for a 12k x 12k matrix multiplication, up to 90% sparsity, was regenerated from a vendor talk (Lie 2021) and the plot values were not readable as text: UNVERIFIED numerically. The papers present the gain as a FLOP reduction (2 to 2.5x at 75% sparsity in 2403.00952), not as a measured wall-clock gain.
- **What a third party measured (2604.27985, MEASURED independent, WSE-3, random synthetic matrices, N from 2,048 to 65,536, dense width 256, compared with a 32-core server CPU (AMD EPYC 9354P) running PyTorch sparse kernels):** SpMM up to 100x faster than the CPU at 90% sparsity; SDDMM up to 20x at 90%; both fall toward the CPU's speed as sparsity rises, and **above 99% sparsity the wafer is no better than, or worse than, the CPU**. Reasons stated: not enough work per core; the cost of streaming matrix and result between host and wafer dominates; only limited pipeline parallelism with few non-zeros. The SELLPACK-like format that feeds many I/O channels is 20x to 80x bigger than compressed-row format at 99.99% sparsity (about 1.1 GB or 4.1 GB versus 53 MB for N = 262,144), and even compressed-row streaming is limited by I/O. For N = 262,144 the dense matrix would be 256 GB.
- **Sparse conclusion:** the wafer is good at *medium* sparsity when the whole problem is resident and when the dense side is large. It is not a machine for event-driven, hyper-sparse work fed from outside.

---

## 8. Power, cooling, area, packaging

All of this is about the CS-2/CS-3 system, not the chip alone.

- **Power.** CS-1 20 kW (2010.03660); CS-2 16.1 kW baseline, 22.9 kW peak, 22.8 kW average during a stencil run (MEASURED, 2204.03775); 23 kW in the MD paper; survey estimate 26 kW; CS-3 23 kW (2503.11698 citing press). A stencil run reached 22 GFLOP/W (503 TFLOP/s at 22.8 kW, 32-bit).
- **Power delivery.** The wafer needs more than 20,000 A at low voltage (Insaito, vendor-derived; the primary white paper is blocked). Edge delivery would drop voltage in the middle, so the system delivers power vertically through the board, with "over 300" voltage-regulation modules under the wafer, multiple per reticle for redundancy and per-reticle regulation (2503.11698, second-hand). The survey adds that edge schemes make a single fault in the chain affect many dies, while vertical schemes inherently fail locally (2310.09568).
- **Packaging.** No package: wafer, flexible connector, main board and cold plate are clamped together; a custom connector absorbs the different thermal expansion of silicon and board (2503.11698, second-hand). Stack: board, membrane/connector, wafer, copper heat exchanger.
- **Cooling.** Closed loop: water/propylene glycol at low pressure and high flow through micro-fins on a copper cold plate; heat leaves through a fan-cooled heat exchanger. Coolant temperature rose from 23.6 to 25.6 degrees C during a 22.8 kW run (MEASURED, 2204.03775). The survey says the cooling takes more than 90% of the chassis volume and caps density of wafer-scale systems (2310.09568, ESTIMATED by the survey authors). The power density per area is "comparable to the most advanced GPUs" (about 0.5 W per mm2: 23,000 W over 46,225 mm2, MODELLED here), so cooling is a plumbing and mechanical problem, not an exotic heat-flux one.
- **Thermal throttling exists.** PEs insert no-ops "to regulate thermal stress" and "prevent wafer cracking"; this was the only noted difference between the cycle-accurate simulator and the real chip (2404.15888). Timing is therefore not perfectly deterministic.
- **Size, rack and price.** CS-2 takes about one third of a rack (2209.15040). 15U per CS-3 (Insaito). Price estimate 2 to 3 million dollars per system (Insaito, press-based; ESTIMATED). Insaito's table 2 (ESTIMATED from vendor peaks, not measured): rack-level 250 PFLOPS at 46 kW for two CS-3s versus 216 PFLOPS FP8 at 42.9 kW for a B200 rack; per-watt-per-dollar the B200 rack is 1.5 to 3 times better. Peak FP16 per rack for the wafer is quoted as 250, which depends on the sparse-peak ambiguity above, so UNVERIFIED.
- **Area.** 46,225 mm2, about 56 times a reticle-limited GPU die (826 mm2: 2311.01739 table 4: "48x transistors, 56x area, 57x power, 65x FP32 peak" for WSE-2 versus A100).

---

## 9. Yield and defect handling

- **Design principle:** make the defect unit tiny. A defect can kill at most one 0.04 mm2 tile rather than a 6 mm2 SM. Insaito's illustrative calculation (ESTIMATED, 0.001 defects per mm2 for both chips, 5 nm): the worst-case area lost to defects is about 2.2 mm2 for the wafer against 361 mm2 for 72 H100-sized dies, "about 164x more fault tolerant" (their wording). The 164x is a ratio of fault-tolerant core sizes and should be read as an illustration, not a yield measurement.
- **Mechanism (second-hand, primary blocked):** about 1% of cores are spares; spare fabric links per row let the fabric bypass a dead core and restore a logical rectangular mesh; the router is decoupled from the core so a dead core does not kill the network; the on-chip SoC remaps at run time and exposes only healthy cores to software as a regular grid (2310.09568; 2502.04563: "no explicit handling at the software level"; 2405.07898: "hardware mechanisms transparently correct fabrication defects so that the design maintains uniform topology, uniform bandwidth and guaranteed latency").
- **Why it is needed (ESTIMATED):** with 0.09 defects per cm2 (survey, from a public estimate) a 510 mm2 die has about 60% die yield; so roughly 40% of the 84 dies would have at least one defect without repair (2310.09568, Murphy model). 93% functional wafer area against 70 to 80% for commercial GPUs is quoted from the vendor blog by 2502.04563 (VENDOR CLAIM).
- **Operational evidence:** the WaferLLM authors report "high reliability over two years of WSE-2 deployment" (anecdote, not a statistic; 2502.04563).
- **What the user sees:** the usable grid is not exactly the nominal one. Different papers report fabrics of about 757 x 996, 755 x 994 and about 920 x 920 for the same chip generation; "the performance will depend on the specific chip; if there are defects, a proprietary process will route around them" (2404.15888). Fabrication defects therefore leak into placement and sometimes timing.
- **Other chips (second-hand):** the competitor wafer-scale designs avoid yield loss differently: Tesla's tile assembles 25 pre-tested D1 dies (645 mm2 each, 354 nodes each, 8,850 nodes per tile) on a fan-out wafer with 2 TB/s per die edge, 11 GB SRAM per tile, 1.25 MB per node, 9.1 POPS, 15 kW (all from the survey's table 2 and WaferLLM, VENDOR numbers from Dojo talks, UNVERIFIED primary); the UCLA/UIUC prototype design assembles 2,048 pre-tested chiplets on a silicon-interconnect wafer (15,100 mm2, 1,024 tiles of 14 ARM cores) with two independent routing networks (x-y and y-x order) for link faults (2310.09568). The survey's conclusion: known-good-die assembly has a yield advantage and costs inter-die bandwidth; stitching costs yield and gives uniform bandwidth. Theseus (SIMULATED, 0.1 defects per cm2, yield target 0.9) finds that a design with pre-tested dies on fan-out beats a stitched wafer in energy-delay for LLMs because yield overhead is smaller (2407.02079, takeaway 2). That is a model result with matrix-heavy workloads, HYPOTHESIS for L.

---

## 10. Measured performance against GPUs (with source, hardware, comparator, caveat)

Reading rule: a ratio against a GPU is only as good as the GPU code. Every row lists the comparator.

| # | Workload | Wafer result | Comparator | Ratio | Label and caveat |
|---|---|---|---|---|---|
| 1 | Table lookup: macroscopic cross-section kernel, 250 nuclides per lookup (2311.01739) | 8.36 x 10^9 lookups/s (WSE-2, 744,000 particles at once, 280 microseconds, 21% communication overhead, 10% load imbalance left) | 6.43 x 10^7 lookups/s on one A100 (heavily tuned CUDA with sorting) | 130x | MEASURED (vendor-affiliated). Transistor-normalised, WSE-2 reaches only 1.97% of a published ASIC design for the same kernel, the A100 0.73% |
| 2 | Molecular dynamics, 800,000 atoms, EAM (2405.07898) | 274,016 steps/s (Ta), 106,313 (Cu), 96,140 (W) | Frontier GPU system at its strong-scaling limit: 1,530 / 973 / 998 steps/s; CPU cluster 4,938 / 3,120 / 3,633 | 179x / 109x / 96x (GPU); 55x / 34x / 26x (CPU) | MEASURED (vendor-affiliated). WSE used FP32, the GPU code FP64. Peak utilisation 20 to 23% vs 0.2 to 0.4% GPU. Timesteps per joule 1 to 2 orders of magnitude better |
| 3 | 25-point 3D stencil, 755 x 994 x 1000 (2204.03775) | 9.86 x 10^12 cell updates/s, 0.0761 s per 1,000 steps, 503 TFLOP/s, 22 GFLOP/W | tuned code on 1 GPU of a 4 x A100 node: 17.4 s | 228x | MEASURED (vendor-affiliated). The authors expect the gap to narrow with many GPUs |
| 4 | Same family via compiler (2601.17754) | WSE-3 around 14x faster time-to-solution than 128 A100 and 20x than 128 CPU nodes for a 3D acoustic benchmark | numbers from a different paper, different grid sizes, OpenACC GPU code | 14x | MEASURED (independent), explicitly "not a strictly direct comparison" |
| 5 | 2D stencil, up to 44,800 x 44,800 (2605.07954) | up to 342x over a GPU tensor-core convolution stencil | A100, FP64 code ported to TF32, 50% multiplications by zero | 342x | WSE-3 numbers for more than 512 x 512 cores come from the cycle-accurate simulator validated to a 5% interval; GPU baseline is a port, not native. SIMULATED/MEASURED hybrid |
| 6 | 3D FFT 512 cubed, 32-bit (2209.15040) | 959 microseconds on 512 x 512 cores (815,371 cycles) | 18% faster than the best published GPU result of the same size; "order of magnitude" faster than CPU clusters | 1.18x vs best GPU | MEASURED (vendor-affiliated). Excludes loading data: moving 512 cubed through the 1.2 Tb/s link would take at least 14 ms |
| 7 | Ising model, up to 200 million spins (2404.16990) | 61.8 x 10^12 flip attempts/s aggregate over 754 lattices | single V100 and H100 prior results | up to 148x vs V100, 88x vs H100 | MEASURED (independent lab). Aggregate over many small independent lattices; productivity metric chosen by authors |
| 8 | One 16K x 16K GEMV (2502.04563) | 1.2 microseconds | cuBLAS-based tensor-parallel GEMV: 0.336 ms on 1 A100, 0.253 ms on 8, 0.340 ms on 2 x 8 | 280x to 606x | MEASURED (independent). Energy ratio 7.5x to 121x. Not the theoretical 7,000x |
| 9 | End-to-end decode of an 8B dense model (2502.04563) | 2,699.9 tokens/s per request at 420 x 420 cores (2,243 at 660 x 660) | SGLang on 1 A100: 78.9; on 8: 260.4; on 2 x 8: 164.6 | 10x to 34x | MEASURED (independent). Wafer throughput *falls* as more cores are used |
| 10 | End-to-end 2048/2048 tokens, 8B | 2,370 tokens/s | 36.5 (1 A100), 128.4 (8), 79.3 (2 x 8) | 18x vs best | MEASURED (independent) |
| 11 | Prefill, 4K context, 8B (2502.04563) | 27,686 tokens/s per request | 13,988 (1 A100), 17,362 (8) | 1.6x to 2x | MEASURED (independent). **Energy: the A100 uses less**: A100/WSE energy ratio 0.05 (1 GPU), 0.34 (8), 0.84 (2 x 8) |
| 12 | Decode energy, 8B | as above | A100/WSE-2 energy ratio 0.92 (1 GPU), 2.22 (8), 7.02 (2 x 8) | parity to 7x | MEASURED (independent) |
| 13 | KV cache capacity (2502.04563) | 137,548 tokens (8B) with shifted placement | 382 tokens with concatenated placement on the same mesh | 360x | MEASURED (software design, not hardware) |
| 14 | BERT/GPT training throughput (2409.00287) | e.g. 7,594 hours projected for one epoch of a 20B-parameter GPT-style model over 211 million samples, compute-bound on a roofline | none (no GPU baseline) | none | MEASURED (independent); projections, no comparison |
| 15 | Weak scaling across 16 CS-2 (2304.03208) | 14.5x to 15.9x of 16x | 1 CS-2 | linear within 9% | MEASURED (vendor-affiliated) |
| 16 | Early 2D Jacobi stencil via TensorFlow on CS-1 (2210.04795) | 2.5x four V100 GPUs, 114x two 18-core Xeons | delivered-performance metric | | MEASURED (independent), early software |
| 17 | Sparse-dense matmul on WSE-3 (2604.27985) | up to 100x at 90% sparsity | CPU only | CPU parity or worse above 99% sparsity | MEASURED (independent), no GPU comparator |
| 18 | BiCGStab on WSE-1 (2010.03660) | 28.1 microseconds per iteration, 0.86 PFLOPS mixed precision, about 200x faster than a 16,384-core partition of a lab cluster on a multiphase fluid code | CPU cluster | | MEASURED (vendor-affiliated) |

**What these rows say together:** the wafer wins by 100x or more exactly where (a) the problem fits in 40 GB, (b) the work is local or has a tiny reduction, (c) the GPU comparator is communication-limited because it must be spread over many devices, or (d) the kernel is latency-bound. It wins by 1.2x to 2x on prefill-like dense compute, and it loses on energy there. Its win on LLM decode is real but is a single-request latency win; no paper compares throughput per dollar or per watt at the same total cost.

Third-party hardware-cost comparison (ESTIMATED, Insaito): at ISO space and power the CS-3 peak numbers are 3.9x (FP8) and 7.8x (FP16) over a DGX H100 rack, 1.16x and 2.3x over a B200 rack; per watt per dollar, B200 wins by 3x and the H100 rack ties. These are vendor peaks, not measurements.

---

## 11. Programming model and its constraints

- **Two programming levels.** (1) High-level PyTorch/TensorFlow: the compiler maps the layers to the wafer as a pipeline of kernels with a library of kernels; limited to what the library covers; sparse support dense-with-mask only (2604.27985, 2310.09568 section V). (2) CSL, the Cerebras Software Language, a Zig-like language exposing tasks, wavelets, colours, DSDs, layout files (2204.03775, 2604.27985). Everything non-standard — every paper in sections 4 and 5 — is written in CSL or in another vendor language (the molecular-dynamics paper used a language called Tungsten plus hand-tuned assembly).
- **The developer must think about:** which colour each route uses; router configuration switching (control wavelets); which task is blocked; when a microthread blocks on an empty fabric queue; send-completion barriers because tasks are non-preemptive; memory budget per core (all buffers in 48 KB); the host-device boundary (host-to-device transfers can serialise, 2604.27985).
- **Effort:** WaferLLM was about 7,000 lines of CSL plus 2,000 lines of Python (2502.04563). The Monte Carlo kernel needed a custom decomposition and load balancing scheme (2311.01739). The compiler paper calls CSL "complex and susceptible to errors" and shows a loop of a few lines turning into a callback graph (2601.17754). A compiler-generated stencil beat the hand-written one by up to 7.9% on WSE-2 (hand-written reached 28.2% of peak, 2601.17754), so tooling can help for regular codes.
- **Portability across generations:** hand-written WSE-2 stencil code is "not supported on WSE-3 due to hardware generations that require kernel rewriting" (2601.17754).
- **Constraints that bite:** 24 colours; four configurations per colour; one core-to-router port; 48 KB; no diagonal links; non-preemptive tasks; only 32-bit packets (payload plus colour, with 16 bits data and 16 bits control according to 2409.00287); fp32 not natively SIMD on WSE-3 (2605.07954); static sparsity only; dynamic shapes hard.
- **What is easy:** weight streaming for training: change the number of systems and the stack chooses the data-parallel layout (2304.03208). That is the real software achievement and it is hidden from the user.

---

## 12. Failure modes (observed or implied)

1. **Capacity wall.** Anything that does not fit in about 40 GB must be streamed or cut; WaferLLM could not run 34B and 72B models completely on one WSE-2.
2. **Communication wall at high parallelism.** WaferLLM decode throughput drops from 2,699.9 to 2,243 tokens/s per request as cores increase from 420 x 420 to 660 x 660; MeshGEMM scaling reaches 70% efficiency near the limit while SUMMA and Cannon drop under 50% at 720 x 720; the vendor GEMV spends up to 90% of its time communicating (2502.04563).
3. **Hot cores.** Concatenated KV cache fills one row; the last core in a reduce chain receives everything; contention C in the model of 2404.15888.
4. **Under-use of the grid.** Small problems use only a rectangle; corners are idle; edge cores under-used; in the stencil case 11.6% idle on memory.
5. **Host I/O.** Streaming a problem into or out of the wafer takes longer than computing it for small kernels (FFT: 14 ms in, 1 ms compute; SpMM: only one I/O channel unless the data format is redesigned; hyper-sparse parity with a CPU).
6. **Thermal regulation inserting no-ops** and run-to-run variability under 4%.
7. **Software fragmentation.** Wafer generation changes require kernel rewrites; routing library calls reconfigure routers and slow things down.
8. **Cost and single point of failure.** One wafer is one chip: if the board, connector or cold plate fails the whole 2 to 3 million dollar unit is down (ESTIMATED price; survey says long-term reliability of the packaging "needs to be looked into", 2503.11698).
9. **Energy at the low-parallelism end.** In prefill the wafer uses 1.2x to 20x more energy than 1 to 16 A100 GPUs (2502.04563 table 7).

---

## 13. Weak points a different design could exploit (HYPOTHESES, each with its evidence)

Each item is a hypothesis of this note. The evidence column is MEASURED or VENDOR as labelled in the sections above.

**W1. The compute core is the wrong thing for a counting machine, so half the area is idle for it.** Evidence: half the tile is compute logic (vendor); MD reaches 20 to 23% of peak (best case, FMAC-heavy); the lookup kernel reaches 1.97% of the transistor efficiency of a dedicated ASIC design (2311.01739); an FFT pencil reaches 0.89 flop/cycle against a SIMD-4 peak. For L, a tile of a few counters, a comparator and a small table engine could put 80% or more of the area into memory (section 3). Test: MODEL the lookup rate of such a tile against 8.36 x 10^9 lookups/s on WSE-2.

**W2. A single binary search costs 250 cycles on a general core; a dedicated lookup engine costs far fewer.** Evidence: after all optimisations 250 cycles per nuclide per particle with most time in binary search (2311.01739); the ASIC reference needs 46 cycles (ESTIMATED by another group, 14 nm). A hardware search or hash path in the tile could be around 5x faster (MODELLED from those two cycle counts only, assuming the memory is the same).

**W3. Memory per core is fixed at 48 KB and per-wafer capacity is only 44 GB.** Evidence: section 3; WaferLLM needs 5 to 6x more local memory to avoid pipeline parallelism. Exploit: put the L model in tables whose size is chosen by area, and use compressed sparse formats in the tile so that 44 GB of raw capacity is worth more (counts/rows of a sparse table vs dense floating point tensors). Counter tables need few bits per entry; the wafer stores 16 bits or 32 bits per number regardless.

**W4. The network is a plain mesh with a 24-colour routing budget, so any non-local access needs hand-built routes or software relaying.** Evidence: section 4; WaferLLM's PLMR model; alpha versus beta. Exploit: route by *address or hash in the packet* (an event carries its destination), not by colour, so there is no route budget; accept that the router needs a small table lookup per hop.

**W5. Global reduction is O(sqrt N) cycles and needs hand-designed trees.** Evidence: 2404.15888 (two-phase 2.4x from lower bound; the vendor pattern up to 5.9x). Exploit: counters are *commutative and associative*; a design where routers merge counters on the way (in-network add) or where counts are summed hierarchically by region removes the all-reduce critical path. The wafer already has hardware multicast but no in-network reduction (HYPOTHESIS: no paper mentions in-router add; 2404.15888 shows reduces done in cores).

**W6. Data enters the wafer through a narrow door (1.2 Tb/s, about 150 GB/s).** Evidence: FFT, SpMM, Insaito/WaferLLM. The wafer is excellent when everything is resident and poor when it must stream. Exploit: for L, inference should be resident (the project rule: inference on chip, training on a GPU) so the narrow door only carries tokens and results.

**W7. Weight streaming is a training design; as an inference design it is bandwidth-bound.** Evidence: section 6 arithmetic (MODELLED): 2.3 s to stream a 350 GB model through 150 GB/s. L avoids it by not streaming weights at all: tables are resident, each token touches a few rows (event-driven sparse row lookups).

**W8. Cooling and power dominate the system volume and cost.** Evidence: more than 90% of the chassis volume is cooling (survey), 20,000 A power delivery, custom connector, ESTIMATED 2 to 3 M dollars. A memory-heavy, counter-based wafer should have much lower power density, because SRAM reads are cheaper than FMACs (HYPOTHESIS; the energy ratio is not given in any paper read). If power density is lower the mechanical stack can be simpler. Needs an energy-per-access number I do not have: UNVERIFIED.

**W9. Stitching forces identical reticles, so the machine is homogeneous.** Evidence: survey (the mask cannot change during a full-wafer exposure); Theseus (SIMULATED) finds that assembling pre-tested dies yields better energy-delay for LLMs. Exploit: L could use two kinds of reticle, a memory-dense one and an event-routing one, if the design is a die array; a hypothesis only.

**W10. Yield repair depends on a rectangular logical mesh with spare rows.** Evidence: section 9. Exploit: with tiles being tiny and memory-dominated, the tile *is* the repair unit; a counter tile with built-in self-test can be mapped out by the address space (no regular grid needed if routing is by address). HYPOTHESIS.

**W11. Dense arithmetic engines idle during irregular, event-driven work, and vector setup is expensive.** Evidence: "tens of cycles to set up an arithmetic operation" (2404.16990); SpMM falls to CPU parity when each core has few non-zeros; the Monte Carlo kernel has 10% residual imbalance. A counter tile that processes one event per cycle without setup overhead addresses this directly.

**W12. Unstructured sparsity is static and masks are dense on the host.** Evidence: section 7. L's native representation is sparse, so a machine that stores only the non-zero rows removes the dense-with-mask storage.

**W13. Software complexity is the moat and the cost.** Evidence: section 11; 7,000 lines of CSL per model. L's tile has no tensor shapes: the program is the table, so compilation is table placement. HYPOTHESIS.

**W14. Energy at low occupancy.** Evidence: prefill energy ratio 0.05 to 0.84 against A100 (the wafer burns 20 kW whether or not it is used). Exploit: tiles that gate off when idle; event-driven logic costs power only on events (HYPOTHESIS; needs a circuit-level number).

---

## 14. Conflicts and inconsistencies between the sources

- Cores: 850,000 (all vendor numbers); about 754,000 (757 x 996); about 846,000 (about 920 x 920); 755 x 994 used. The survey gives 853,104 from 12 x 7 dies of 66 x 154 cores, which is a different number again.
- Memory bandwidth of WSE-2: 20 PB/s (most) versus 22 PB/s (WaferLLM).
- Fabric bandwidth WSE-3: 214 Pb/s (2601.17754) versus "215 PB/s" in 2605.07954 (almost certainly a unit slip; 1 PB/s = 8 Pb/s).
- Clock: 850 MHz measured; 1.1 GHz maximum; one oscillator versus independent clocks.
- Power: 20 kW (CS-2 in 2209.15040), 22.8 kW average (2204.03775), 23 kW (2405.07898), 26 kW estimate (survey).
- Ramp latency T_R: 2 cycles in the simulator; about 7 on hardware (cited, not measured by the authors).
- Peak performance WSE-3: 125 PFLOPS (sparse FP16 per 2608.28048); 250 PFLOPS FP16 for two CS-3 per rack in Insaito's table; the dense figure is undisclosed.
- Yield: 60% (estimated, no repair), about 100x defect tolerance (vendor blog, blocked), 93% functional area (vendor, quoted).
- The tile memory layout appears as 128-bit read + 64-bit write (WSE-2 papers) and as two 64-bit reads + one 64-bit write (WSE-3 paper); not a contradiction but a different description.

---

## 15. What to learn without copying (for a counter and lookup based tile design)

The founder's constraint: no copying, no matrices, no multipliers. What carries over is *principles* confirmed by measurement, not circuits.

1. **Memory inside the tile, single-cycle, no cache, no shared address space.** Every measured win in section 10 comes from this one choice. Keep it. Change the ratio: more memory, less compute logic (W1).
2. **Event-triggered work.** A wavelet arriving starts a task on the data; no polling, no barrier except what the data imply. This matches L's address events. What to copy as an idea: "arrival of a message selects the code" at hardware level, without OS or message library (2405.07898). What not to copy: 24 colours and offline route tables.
3. **Hardware multicast and count-based filtering in the router.** The FFT transposes and stencil broadcasts are built from "send the stream down the row; each router keeps the k-th element". For L this is a primitive for fan-out of an event to the tiles that hold the rows. A router with a counter and a compare is already within the L philosophy.
4. **Determinism.** Variation under 4% (1% in one study), a cycle-accurate simulator that matches (2404.15888, 2605.07954 within 5%). Plan for a cycle-accurate simulator from the start, as the Cerebras collectives and stencil work did; it made 3x speed-ups discoverable by model rather than by trial.
5. **A four-term cost model.** Energy (hops), distance, depth, contention (2404.15888); and the PLMR checklist of parallelism, latency, memory and routing (2502.04563). Both can be written for a counter mesh and used as design rules before any RTL.
6. **Bit-packed state.** The Ising work packs 16 spins in an int16 and gets 61.8 x 10^12 flips/s aggregate on 754 independent lattices with only local communication (2404.16990). That is the same shape as bit-plane counters and clause bits. It also warns: put several independent problems in the memory of a tile so that setup overhead is amortised.
7. **Table lookup is a first-class workload.** 8.36 x 10^9 lookups/s on a general core mesh, a published dedicated ASIC reference 5x cheaper in cycles per lookup, load imbalance and table-replication as the problems still left (2311.01739). The solutions they found (circulate the queries through the row that holds the table; transfer table segments between rows; stochastic interpolation to cut the memory reads) are directly reusable ideas for a hash-table tile.
8. **Defect handling by small unit plus spare links.** About 1% spares and spare links per row, router separate from compute, transparent to software (2310.09568). For a tile that is only memory plus a few counters the repair granule is smaller still. Copy the *separation of router from compute*, not the row-spare scheme.
9. **Locality in the programming model.** The wafer rewards "do it where the data is" and punishes remote access by a factor up to 1000. Make the L language express ownership of a table row by a tile, not a global tensor.
10. **A narrow external door is acceptable if the model is resident.** The point of weight streaming is that the wafer is a *compute appliance with an external parameter store*; L inverts it: the parameter store *is* the wafer, and only tokens cross the door. The measured cost of the opposite choice is in section 7 (host streaming dominates) and in the arithmetic of section 6.
11. **Do not copy:** FMAC datapaths, 32-bit float wavelets, 16-bit SIMD, DSD tensor descriptors for dense vectors, reticle stitching if known-good-die assembly gives a better yield-bandwidth balance for a memory-dominated design (Theseus, SIMULATED), liquid cooling stack sized for 23 kW (unless L's power density is as high; W8).

**Open questions for L (to answer by modelling, not by reading):**

- Energy per SRAM read, per counter increment and per router hop for a memory-dominated tile at the same node: no paper read gives a measured per-access energy for the WSE; ask in the L energy model.
- How many cycles an address event spends per hop if the router looks up the destination in a small table rather than using a colour.
- What the all-reduce-free formulation of an L training aggregate looks like if counts add in the network.
- Whether a pre-tested-die array (Dojo-like) or a stitched wafer suits a memory-dominated tile better; Theseus suggests dies, the yield argument for stitching depends on tile size and defect density (0.09 to 0.1 per cm2 in the sources).

---

## 16. Items still UNVERIFIED (not read in a primary source)

- Weight-streaming execution details of the commercial stack, MemoryX capacity and bandwidth, SwarmX design and bandwidth.
- Real bandwidth of the external link and of the CS-3 I/O (only "100 Gb/s Ethernet" and "1.2 Tb/s" were found, from two different generations).
- The "100x defect tolerance" claim, exact spare-core percentage, spare-link scheme and run-time remapping procedure.
- Per-core and per-access energy; the dense FP16 peak of WSE-3; the 256-byte per-core cache; the power-delivery current and the VRM count (only quoted second-hand).
- Tesla Dojo and UCLA/UIUC details (only through the survey, WaferLLM and two network papers that were skimmed).
- Values in sparse speed-up plots; all experiment plots of the collectives paper; Ouroboros results against Cerebras (its own simulator, calibrated to 6 to 9% latency against its Cerebras model).
- Any figure that exists only inside an image.

Related: [Paper notes index](INDEX.md), [Memory at scale synthesis](../memory_at_scale_synthesis.md)
