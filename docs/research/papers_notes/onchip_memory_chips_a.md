---
title: Notes - on-chip memory designs of Cerebras, Groq and Graphcore
tags: [l, research, papers, memory, hardware]
---

# Notes - on-chip memory designs of Cerebras, Groq and Graphcore

Purpose: learn how the three companies that put the working memory INSIDE the chip designed it, so that the tile memory of L (tables of counters, clause lists, address events over a mesh) can borrow what works. Date of reading: 25 Oct 2026.

## 0. Sources actually read, and what was blocked

Label rule: every number below carries the source it came from. "Vendor claim" means a number the vendor (or an author employed by the vendor) states without independent measurement. "Measured" means the paper reports a benchmark run on real hardware. Nothing here is invented; where I could not read the primary document the item is marked UNVERIFIED.

| Source | Status | Kind |
|---|---|---|
| Jia/Maggioni/Staiger/Scarpazza (Citadel), "Dissecting the Graphcore IPU Architecture via Microbenchmarking", arXiv 1912.03413 (Dec 2019), full text, about 28,800 words | READ COMPLETELY (text extracted) | Independent microbenchmarks, hardware supplied by Graphcore. Chip: first-generation IPU (GC2, C2 board) |
| Rocki et al. (Cerebras and NETL), "Fast Stencil-Code Computation on a Wafer-Scale Processor", arXiv 2010.03660 (SC20) | READ | Written by the vendor with a national lab. WSE-1 / CS-1. Architecture section is primary |
| Jacquelin, Araya-Polo, Meng, "Massively scalable stencil algorithm", arXiv 2204.03775 | READ | Vendor plus customer. WSE-2. |
| Kundu et al. (Insaito), "A Comparison of the Cerebras Wafer-Scale Integration Technology with Nvidia GPU-based Systems", arXiv 2503.11698 | READ | Third-party analysis built on public vendor material. Mostly estimates and marketing figures, no measurements |
| "Benchmarking the Performance of Large Language Models on the Cerebras Wafer Scale Engine", arXiv 2409.00287 | READ | University benchmark on a CS-2 |
| He et al., "WaferLLM: Large Language Model Inference at Wafer Scale", arXiv 2502.04563 | READ | Academic, measured on a WSE-2. Source of the PLMR model |
| Groq authors, "Answer Fast: Accelerating BERT on the Tensor Streaming Processor", arXiv 2206.11062 (ASAP 2022) | READ | Written by Groq staff. Measured on hardware, but a Groq-run result against GPU numbers taken from NVIDIA material |
| Abts et al., "Think Fast: A Tensor Streaming Processor (TSP) for Accelerating Deep Learning Workloads", ISCA 2020 | BLOCKED (groq.com not reachable from the sandbox: proxy 403 and DNS failure). UNVERIFIED in this note. Search snippet only: 25 x 29 mm 14 nm chip at 900 MHz nominal, ResNet50 20.4K images/s at batch 1 (vendor claim, not read) | Primary paper, not read |
| Abts et al., "A Software-defined Tensor Streaming Multiprocessor for Large-scale Machine Learning", ISCA 2022 | BLOCKED, same host. UNVERIFIED. Everything about the multi-chip Groq network (dragonfly, software-scheduled routing) is therefore absent | Primary paper, not read |
| Cerebras Hot Chips 2021 and 2022 slides (hc33 / hc34.hotchips.org), Cerebras weight-streaming whitepaper (hubspot host) | BLOCKED (proxy refused the hosts). Only a search-result snippet seen: HC2022 slides state 850,000 cores, 40 GB on-chip memory, 20 PB/s memory bandwidth, 220 Pbit/s fabric bandwidth (vendor claim, snippet only) | Primary vendor material, not read |
| Graphcore architecture whitepapers and the later IPU papers (Mk2, 900 MB) | Not downloaded. Mk2 figures UNVERIFIED | - |

Consequence: the Cerebras and Groq sections rest on papers that describe the chips second hand (users and vendor staff), not on the architecture presentations themselves. The Graphcore section is the strongest: independent measurement, read in full. Treat energy-per-access as NOT STATED in every source I could read; no source gave picojoules per bit for SRAM, the fabric, or off-chip memory, so I cannot give an on-chip against off-chip energy ratio and I do not guess one.

## 1. Graphcore IPU (first generation) - the clearest data

### 1.1 Memory capacity and organisation (MEASURED architecture description, arXiv 1912.03413)

- 1,216 tiles per chip. A tile is one core plus 256 KiB of local SRAM, total 304 MiB per chip (608 MiB per two-chip board). Except for the register file there is no other memory on the device: no cache, no shared memory (section 1.2 and 1.4 of the paper).
- Each tile owns an independent, contiguous 21-bit address space shared by its 6 hardware execution contexts; code and data of that tile must both fit inside the 256 KiB.
- The memories are scratchpads, not caches. Control-flow divergence and address divergence cost nothing; each core reads local memory at fixed cost independent of access pattern. The authors present this as why the IPU suits irregular and sparse access, "provided that working sets fit in IPU memory".
- Clock 1.6 GHz (Table 1.1).

### 1.2 Bandwidth and latency (MEASURED unless marked)

- Local read latency: 6 clock cycles = 3.75 ns, fixed, independent of access pattern (the paper tests invariance). Compared in the same table with an NVIDIA T4: shared memory 11.94 ns (19 cycles), L1 20.13 ns (32 cycles); Intel L2 2.79-4.62 ns.
- Theoretical aggregate read bandwidth 31.1 TB/s (16 bytes per tile per cycle x 1.6 GHz x 1,216 tiles). Nominal quoted figure 45 TB/s aggregate. The measured bandwidth reached close to the theoretical figure only with vectorised, well-unrolled code; naive loops got a fraction (the paper gives per-approach fractions in Table 3.1; I did not copy them). Write bandwidth theoretical limit 15.5 TB/s.
- Per-chip capacity comparison (Table 1.1): 304 MiB against 1.25-2.5 MiB for a T4's equal-latency levels, so one to two orders of magnitude more fast memory than GPU or CPU levels of equal speed.
- Energy per access: NOT STATED in the paper.

### 1.3 Interconnect (MEASURED)

- On-chip "exchange": all tiles sending to random destinations simultaneously reached 7.7 TB/s aggregate; each tile can use 6.3 GB/s to an arbitrary destination; tile-to-tile latency 165 ns or lower, and it does not degrade under load (section 1.5). Point-to-point small-message latency on chip 0.133 microseconds (Table 4.1).
- Off-chip IPU-Links: ten link interfaces per chip. The two chips on a board are joined by three links of 64 GB/s nominal bidirectional each, two of which are used for intra-board transfers; measured 108 GB/s between the two chips (84% of nominal). Off-board direct link about half that per direction (28 GB/s). Small-message latency: off-chip on-board 0.633 microseconds, off-board direct link 0.524, indirect 0.779 (Table 4.1). Point-to-point peak bandwidth per pair: 6.34 GB/s on chip, 5.46 on board, 4.99 off board direct, 4.91 indirect (Table 4.4).
- Host: two PCIe Gen3 x16, each IPU gets 8 lanes, about 6 GB/s per IPU (section 4.7.2).
- Ratio worth noting for L: on-chip aggregate exchange (7.7 TB/s) is about 4 times lower than local memory (31.1 TB/s theoretical), and chip-to-chip (108 GB/s between two chips) is about 70 times lower than the on-chip exchange. Each step outward loses roughly one to two orders of magnitude of bandwidth, which is the whole argument for keeping data local.

### 1.4 Compute and memory ratio, power, area

- Peak compute 31.1 TFlops/s single precision and 124.5 TFlops/s mixed precision per chip (vendor-supplied peak, reported in the paper). So memory 304 MiB feeds 124.5 TFlops: about 2.4 MiB per TFlop/s of mixed-precision peak.
- Power and die area: not given in the paper text that I read (my search of the text found no TDP figure). UNVERIFIED here.

### 1.5 Overflow: what happens when the model does not fit

- A model that fits in 304 MiB lives entirely on chip. Larger models are "sharded across IPU processors and IPU boards": the Multi-IPU abstraction presents several chips as one virtual device with the same programming interface; tile-to-tile communication crosses IPU-Links transparently. Transient data that is used once should be streamed in from the host over PCIe.
- Failure mode (author's statement, MEASURED architecture limit): working set and code must fit tile by tile; the programmer or compiler must partition data across tiles, and tiles exchange data when they need non-local operands. The Multi-IPU supports power-of-two sizes only (2, 4, 8, 16 IPUs).

### 1.6 Scheduling model

- Bulk synchronous parallel (BSP). Programs are compiled as compute phase (local memory only), then exchange phase (no compute), then a barrier. The compiler lays out computation as vertices, data as tensors and data exchanges as static edges. The exchange has hardware support for all-to-all personalized exchange. So the schedule is static at the superstep level, with a hardware barrier, not cycle-exact like Groq.

### 1.7 Sparsity

- No special sparsity hardware is claimed. The claim is that fine-grained distributed SRAM makes irregular and sparse access cost the same as dense access, per tile, provided the data is local.

### 1.8 Yield and fault tolerance

- Not discussed in the paper. UNVERIFIED.

## 2. Cerebras WSE (WSE-1 in CS-1, WSE-2 in CS-2, WSE-3 in CS-3)

### 2.1 Memory capacity and organisation

- WSE-1 (CS-1), vendor-authored architecture section of arXiv 2010.03660: about 380,000 cores, each with 48 KB of dedicated SRAM, 18 GB total; MIMD, distributed memory, no shared memory; load-to-use latency one cycle; per core 16 bytes of read and 8 bytes of write bandwidth to memory per cycle; up to eight 16-bit floating point operations per cycle; 2D mesh fabric with 16 bytes of injection bandwidth per core per cycle (the stencil paper's intro words it as injection bandwidth one fourth of peak floating-point compute bandwidth); total system power 20 kW (vendor-authored statement). The wafer has a 7 x 12 array of 84 identical dies, and the dies are joined by extending the interconnect across the scribe lines. Authors say memory bandwidth matches the peak compute rate and communication bandwidth is only slightly lower.
- WSE-2 (CS-2), arXiv 2204.03775, 2409.00287, 2502.04563: 850,000 cores, each with 48 KB SRAM; 40 GB total. Clock up to 1.1 GHz, TSMC 7 nm, die area about 46,000 mm2, 2.6 trillion transistors. Memory bandwidth quoted 20 PB/s (arXiv 2409.00287 table) and 22 PB/s (WaferLLM text); these are vendor figures reproduced by academics, and the two papers disagree by 10%, so treat the number as "about 20 PB/s, vendor claim". Per core per cycle: fetch two 32-bit operands from SRAM, do a multiply-accumulate and write back (WaferLLM).
- Per-core detail (arXiv 2409.00287, citing a Cerebras source): memory organised in eight 6 KB banks, each 32 bits wide, plus a 256-byte 64-bit-wide software-configured cache. About 50% of core silicon is SRAM and 50% logic (same source). This is a much higher memory share than a GPU core; the third-party comparison (2503.11698) says about 50% of the WSE-3 area is SRAM, register files and fabric. Core area 0.05 mm2 on WSE-3 against about 6 mm2 for an H100 SM (third-party, from public data).
- WSE-3 (CS-3), third-party figures only (arXiv 2503.11698, vendor-sourced marketing numbers, not measured): 4 trillion transistors, 900,000 cores, 44 GB on-chip SRAM, 5 nm, 23 kW system power.
- Energy per access: NOT STATED. Authors of arXiv 2010.03660 state only that the wafer has "lower energy cost for memory access" than conventional systems; no number.

### 2.2 Interconnect between cores (vendor-authored, WSE-1, arXiv 2010.03660; WSE-2, arXiv 2204.03775)

- Each core has a router with five full-duplex links: East, West, North, South and the core itself; every router moves data on all five links in parallel each cycle. Packets are 32 bit: 16 bits data plus 16 bits control (WSE-2 paper 2409.00287 description); the message carries a "color" (virtual channel) that selects the route.
- Routing is configured offline at compile time. Data travels along virtual channels; a router can forward an input word to any subset of its outputs (so multicast is a routing property). Each router has 24 static routes (colors), per arXiv 2409.00287; WaferLLM states that a WSE-2 core recognises only message headers with a 5-bit address code, so each core supports at most 2^5 = 32 distinct routing paths (they write 25), and the software must plan paths carefully; if more paths are needed, messages are relayed through intermediate cores at extra per-routing cost. This routing-table limit is a real failure mode of the mesh at million-core scale.
- Hardware tasks are triggered by arriving data: the channel of an arriving word selects which code runs (event-driven). Nine concurrent threads per core (WSE-1 paper); eight micro-threads holding tensor instructions (arXiv 2409.00287).
- Latency: nanosecond per hop (WSE-1 paper, vendor-authored). A scalar AllReduce across about 380,000 cores took under 1.5 microseconds (MEASURED on WSE-1, same paper).
- Fabric bandwidth: 220 Pbit/s aggregate (HC2022 slide figure, snippet only, UNVERIFIED).

### 2.3 Measured results (with source)

- WSE-1 BiCGStab solver, 7-point stencil, mixed precision: 0.86 PFLOPS, MEASURED, vendor plus NETL (arXiv 2010.03660). The paper claims it is beyond what CPU and GPU clusters achieve on this problem, because of memory and interconnect bandwidth per flop. Each core holds ~31 KB of its 48 KB for matrix and vector data in the example with Z=1536.
- WaferLLM (arXiv 2502.04563), WSE-2, MEASURED by an academic group (the A100 baseline was run with SGLang): LLaMA3-8B decode (4K context) about 2,700 tokens/s per request against 78 (1 GPU), 260 (8 GPUs), 164 (2x8 GPUs); LLaMA2-13B decode 2,039 against 48 (1 GPU), 175 (8 GPUs). Prefill throughput 27,686 against 13,988 (1 GPU) for LLaMA3-8B. Headline claim: 10-20 times faster than an A100 cluster for full inference. Energy: a WSE-2 has 47 times the area and 37 times the power and cost of an A100 (their statement), and WaferLLM obtains 2-2.5 times better energy efficiency at SGLang's optimal multi-GPU decode result, but is worse on energy than a single A100 for prefill (A100/WSE-2 energy ratio 0.05 to 0.84 means the A100 uses less energy per token there). Decode on WaferLLM is hurt by the small 48 KB local memory, which forces pipeline parallelism and causes up to 5 times underutilisation (their statement).
- Performance of the whole machine on tensor-parallel GPU scaling is poor in the same paper (8 GPUs give only 1.2-1.6 times prefill and 3.3-3.6 times decode speedup over 1 GPU), which is the GPU weakness the wafer exploits.

### 2.4 Capacity overflow: weight streaming

- From arXiv 2409.00287 (secondary description): model weights are stored in an external DRAM and flash device called MemoryX; MemoryX sends the weights of each layer to the wafer at compute time; the wafer computes outputs using the streamed weights and the activations resident in cores; for training, gradients go back to MemoryX, where the weight update is performed. Compute and memory are decoupled; MemoryX scales from 1.2 TB to 1,200 TB (arXiv 2503.11698, vendor-sourced, third-party). Detailed streaming bandwidths, the SwarmX fan-out network and the Cerebras whitepaper itself were blocked: UNVERIFIED.
- The stencil paper states the single-wafer limit plainly: the memory capacity (18 GB on WSE-1) limits the problem size, which is the price of keeping everything in SRAM.
- WaferLLM keeps the whole model and KV cache on the wafer (decode of LLaMA3-8B fits; they note "single WSE-2 chip" constraint on model size in the benchmark set-up, e.g. removing the 4K context length for one of the models).

### 2.5 Sparsity

- Vendor-sourced description repeated in arXiv 2409.00287: fine-grained dataflow scheduling lets a core perform computation only on non-zero data, saving dynamic power; together with the high memory bandwidth this supports unstructured sparsity in weights and activations. The core is called a Sparse Linear Algebra Compute (SLAC) core in the Cerebras literature. I found no measured sparsity speedup in the papers I could read: UNVERIFIED as a performance result, a vendor claim.

### 2.6 Yield and fault tolerance

- The only text I could read is the third-party analysis (arXiv 2503.11698, no measurement): small cores mean small area lost per defect (0.05 mm2 on WSE-3 against 6 mm2 for an H100 SM; the paper computes that WSE-3 is about 164 times more fault tolerant for cores); redundancy-based defect tolerance in cores, fabric and memory; the fabric is "dynamically configurable" so that connections between cores can be re-routed around defects, which "helps recover almost full yield". The detailed Cerebras description (spare cores, re-linking routes at the die boundary, a defect map loaded at boot) is in the blocked vendor presentations: UNVERIFIED. The numeric claims here are estimates from public information, not vendor yield data.
- Other physical limits listed in that paper: about 20 kW to extract from the wafer, custom packaging and thermal-expansion matching, vertical power delivery to all cores, high system cost.

## 3. Groq TSP (Tensor Streaming Processor, "LPU")

Reminder: the two Groq ISCA papers were BLOCKED. What follows comes from the Groq-authored BERT paper (arXiv 2206.11062), which restates the architecture, plus search-result snippets for the ISCA 2020 abstract.

### 3.1 Memory capacity and organisation

- On-chip SRAM 220 MiB, "highly banked": the paper says each memory slice has a bank of SRAM with up to 176-way memory concurrency, and the memory (MEM) is made of 88 independent blocks distributed evenly between the two hemispheres of the chip. Pseudo-dual-port SRAM cells allow simultaneous read and write on opposite banks, each access moving one 320-byte vector per cycle. On-chip SRAM bandwidth 55 TiB/s; operand bandwidth into matrix and vector units 20 TB/s; 40 TiB/s at the boundary between vector unit and MEM (vendor-authored statements).
- Layout: functional units are arranged spatially by function. Matrix execution modules (MXM) at the east and west edges, switching modules (SXM) inside them, a vector module (VXM) in the middle, and MEM between compute units. Data move through 45 streaming register files; 64 streams (32 eastward, 32 westward), each a 320-byte vector per cycle, 20 TiB/s.
- SRAM is explicit scratchpad: no caches, no arbiters (ISCA 2020 abstract snippet: determinism by "eliminating all reactive elements in the hardware, for example arbiters and caches"). It is 4-10 times a modern GPU's last-level cache (authors' statement).
- Compute: four MXM planes, each a 320 x 320 int8 multiply-accumulate array, so the chip is built around dense matrix multiplication; this is the opposite of L's rule and matters only as a design contrast. VXM has 16 ALUs.
- Chip facts (Table I of the BERT paper, vendor table): die 725 mm2, 14 nm, 26.8 billion transistors, TDP 275 W. For comparison the same table lists A100 826 mm2, 7 nm, 54.2 billion, 400 W; T4 545 mm2, 12 nm, 13.6 billion, 70 W. Memory-to-compute area ratio: not stated.
- Energy per access: NOT STATED.

### 3.2 Measured results

- BERT-base, int8, sequence length 128, batch 1, measured on a TSP at 900 MHz (Groq-run, MEASURED): average 128.9 microseconds, standard deviation 3.8 microseconds, 1st percentile 128.5, 99th percentile 129.5; A100 (TensorRT, figures taken from NVIDIA material) 630 microseconds average and 790 at the 99th percentile; T4 1330 / 1570. Claimed 4.8 times (average) and 6.1 times (99th percentile) speedup over the A100. Caveats: the A100 numbers exclude host copy while the TSP numbers include it; the TSP is the older 14 nm chip; the numbers are a vendor comparison, not independent. The only latency variation came from the PCIe link replay on transmission errors (PCIe gen4 x16 to the host).
- Their latency estimate before running was only 1% shorter than measured, which shows what static scheduling buys: exact prediction.
- ResNet50 batch 1: 20.4K images/s (ISCA 2020 abstract snippet, UNVERIFIED, vendor claim).

### 3.3 Scheduling model

- The compiler schedules every instruction statically; there is no hardware arbitration, cache miss or non-uniform delay, so latency is known to the cycle and tail latency collapses to the average (99th percentile 0.4% above the mean in the BERT experiment). The programmer (GroqAPI) controls the instruction schedule, VXM ALU and MXM plane allocation, and memory allocation. Deep pipelining chains ALUs so that intermediate results never touch SRAM: in BERT only about 5.5% of addressable memory was used as scratchpad, 58% (int8 embedding) or 71% (int16 embedding) as constants (weights), and under 1% for instructions (Fig. 11, MEASURED allocation).
- Limit stated in the same paper: SRAM is more capacity-constrained than DRAM systems, so the work focused on models that fit on a single chip. A model larger than 220 MiB needs several chips; the multi-chip design (global software-scheduled network) is in the blocked 2022 paper: UNVERIFIED.

### 3.4 Sparsity, interconnect, yield

- Sparsity: not discussed in the sources I read. UNVERIFIED.
- Interconnect between chips: not readable (blocked). UNVERIFIED.
- Yield and fault tolerance: not discussed. UNVERIFIED.

## 4. Side by side (numbers as sourced above)

| Item | Graphcore IPU gen 1 | Cerebras WSE-2 | Groq TSP |
|---|---|---|---|
| On-chip memory | 304 MiB in 1,216 x 256 KiB (MEASURED description) | 40 GB in 850,000 x 48 KB (vendor, repeated by papers) | 220 MiB in 88 blocks (vendor-authored) |
| Local access | 6 cycles, 3.75 ns (MEASURED) | 1 cycle load-to-use (vendor-authored, WSE-1) | static, cycle-known (vendor-authored) |
| Aggregate memory bandwidth | 31.1 TB/s theoretical, 45 TB/s nominal | about 20 PB/s (vendor) | 55 TiB/s (vendor-authored) |
| Core-to-core | exchange, 7.7 TB/s MEASURED, 165 ns | 2D mesh, 32-bit packets, nanoseconds per hop, 220 Pbit/s (vendor snippet) | streams between functional units, 20 TiB/s |
| Overflow | shard across chips, stream from host | weight streaming from MemoryX | single chip; multi-chip UNVERIFIED |
| Schedule | BSP: compute, exchange, barrier | compile-time routes, data-triggered tasks | fully static instruction schedule |
| Power | not read | 20 kW for WSE-1 system, 23 kW CS-3 (third-party) | 275 W TDP |

Energy per bit: no source I could read states energy per bit for SRAM against fabric against off-chip. The best proxy for the relative cost of distance is bandwidth and latency, which are measured only for Graphcore: local 31.1 TB/s, on-chip exchange 7.7 TB/s, chip-to-chip 108 GB/s (board), host 6 GB/s per chip; latency 3.75 ns local, 133-165 ns across the chip, 0.5-0.8 microseconds between chips. Energy numbers must come from other papers (not in this note).

## 5. What transfers to L

L's frame: tiles hold tables of counters and clause lists; tiles exchange tiny address events over a mesh; no matrices, no multiplies; a wafer machine is the long-term idea. The three chips are built for dense or semi-dense tensor work, so I transfer the memory and communication design, not their arithmetic. Everything below is an inference from the sources and is an ESTIMATE until L's own tile model is measured.

1. **Tile memory sizing.** The two designs that use many small tiles settled on tens to hundreds of KB per tile: 256 KiB (IPU) and 48 KB (Cerebras), with 6 cycle and 1 cycle access. Cerebras spends about half of its core area on SRAM (cited from a secondary paper). Cerebras' own users report that 48 KB is too small for dense LLM decode (WaferLLM: forces pipeline parallelism, up to 5 times underutilisation) while the IPU's 256 KiB must hold both code and data. L's tables of counters and clause lists are small-record, random-access objects that need no multiplier, so L can spend nearly all tile area on SRAM and a tiny control unit; the lesson is to size a tile so that its share of the model (one hash bucket range or one clause group) fits locally with room for the event queue, and to make that share a design parameter rather than a constant. The alternative of a Groq-style large central block (220 MiB, one 320-byte vector per cycle per bank) suits streaming vectors, not L's sparse single-word lookups.

2. **Event routing instead of data movement.** Cerebras is the closest match: a word arriving on a channel triggers a task at the destination (data-triggered, event-driven), routes are fixed at compile time as colors, a router forwards a word to any subset of neighbours (multicast), and hop latency is nanoseconds. Their measured scalar AllReduce over about 380,000 cores took under 1.5 microseconds, which is the kind of number L needs for a global "vote" or a clause-count reduction. The IPU adds the counterpoint: the exchange loses a factor of about 4 against local bandwidth and chip-to-chip loses about 70 more, so an L event should carry only an address plus a small payload and almost every access should stay in the tile. Warning from WaferLLM: a 5-bit header means at most 32 routes per core, so a large mesh needs either a few reused route classes or hierarchical addressing with relay by intermediate tiles at an extra routing cost. L's address events need an addressing scheme that works with a small per-router table.

3. **Capacity overflow.** Three answers exist: shard over more chips with a transparent global address space (IPU Multi-IPU, power-of-two sizes only), stream the weights through the wafer from an external store (Cerebras MemoryX, compute and memory decoupled, GB/s per chip limited), or stay single chip (Groq BERT). For L the clean choice is: model state stays in tiles; when it does not fit, shard by address range across wafers or chips and send the same address events across the link, since an event is tiny and a link loses 1-2 orders of magnitude in bandwidth anyway; use an external store only for cold tables that can be read as sequential streams. Because L inference is event-driven and sparse, link bandwidth costs less than it does for a dense layer stream. Training stays on a GPU, so there is no need to stream gradients back.

4. **Fault tolerance by redundancy and routing around defects.** The only source for this is the third-party Cerebras analysis, so treat it as UNVERIFIED in detail: small cores lose little area per defect, and a configurable fabric re-routes around dead cores. For a wafer machine L has a natural advantage because tiles are small and identical and addressing is by event, not by physical position: give every tile a logical address, keep a boot-time defect map that remaps logical to physical tiles, add spare tiles per region, and let the mesh route around dead tiles. Because routes in the Cerebras design are compile-time configuration, a defect map implies a re-compile or a table reload per wafer; L should plan for that. Also record that counters held in a dead tile are lost: replication or periodic scrub from a GPU-side master copy is needed for state, which the three vendors' sources do not discuss (UNVERIFIED).

5. **Static scheduling.** Groq's result is the strongest evidence for it: latency standard deviation 3.8 microseconds on 128.9 microseconds, 99th percentile 0.4% above the mean, prediction within 1% of measurement (vendor-run BERT result). The IPU's BSP model is a cheaper middle road, a barrier between compute and exchange phases, with static edges. Event-driven L has variable work per input (sparse events), so a fully cycle-static schedule is not natural; the transferable parts are (a) no caches and no arbiters in the tile (fixed local access time), (b) a statically fixed route table, and (c) bounded per-tile work per time step, with a barrier between steps like BSP so that tail latency stays bounded. This is a design option to test in the L simulator, not a result.

6. **What does not transfer.** The 320 x 320 MXM arrays (Groq), the 4-way FMAC datapath with fp16 (Cerebras) and the mixed-precision AMP units (IPU) are matrix and multiply hardware; they are outside the founder's rule. The performance numbers above compare these chips on dense LLM work, so none of them predicts L's speed. No source gives energy per bit; L must obtain its own MODELLED numbers for SRAM access, a hop, and a link.

## 6. Limits and failure modes summary

- Fixed capacity: all three fail or slow sharply when the working set exceeds on-chip memory (IPU: tile-by-tile fit; Groq: single chip models; Cerebras: 18/40 GB wafer, remedy MemoryX).
- Small per-core memory harms dense workloads (Cerebras decode underutilisation).
- Routing resources are finite (5-bit header, at most 32 routes per core on WSE-2; relay costs more latency).
- Cost and cooling: 20-23 kW per wafer system, custom packaging; a GPU cluster may still win on energy for batch prefill (WaferLLM energy ratio 0.05-0.84 in prefill).
- Vendor claims of 20 PB/s, 220 Pbit/s and 55 TiB/s are peak figures; the only independently measured memory bandwidth in this set is the IPU (close to 31.1 TB/s for well-vectorised code, a fraction for naive code).
- Missing: primary Groq ISCA papers, Cerebras Hot Chips and weight-streaming whitepaper, Graphcore Mk2 documents. Re-fetch these from a host that is allowed, or ask for the PDFs to be placed in the repo, before relying on this note for the Groq network and the Cerebras defect-tolerance mechanism.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
