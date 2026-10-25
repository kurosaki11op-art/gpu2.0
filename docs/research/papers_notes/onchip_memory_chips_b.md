---
title: Notes - on-chip and in-memory compute designs (Dojo, Tenstorrent, d-Matrix and macros)
tags: [l, research, papers, memory, hardware]
---

# Notes: on-chip and in-memory compute designs (Dojo, Tenstorrent, d-Matrix and macros)

Date of reading: 25 Oct 2026. Purpose: the founder wants to learn how companies that put memory inside or next to the compute designed it, so that the L tile (a table-of-counters / clause-list memory plus a small event engine, no multiplies, no dense matrix products) can borrow what is real and avoid what is marketing.

Labels used: **MEASURED** (silicon or running hardware, with a source I read), **VENDOR** (a vendor statement, not independently checked), **MODELLED** (post-layout extrapolation, analytical or simulated model), **DERIVED** (my arithmetic from numbers in a source I read, shown), **UNVERIFIED** (I could not read the primary text; the number comes from a search snippet or a secondary paper).

## 0. What I could and could not read

The sandbox proxy allows arXiv and raw GitHub only. Every vendor site was refused (HTTP 403 on CONNECT), so the following **primary sources were blocked and are UNVERIFIED here**:

| Source | Status |
|---|---|
| Tesla Hot Chips 34 (2022) Dojo microarchitecture slides (hc34.hotchips.org) | blocked; numbers below come from a search-engine summary of the slides and from a secondary arXiv survey that cites Talpes et al. |
| Tesla Dojo whitepaper(s), AI Day 2021/2022 | not found as a downloadable whitepaper; not read |
| SemiAnalysis and Next Platform Dojo articles | blocked (also only secondary) |
| d-Matrix technical whitepaper (d-matrix.ai PDF) | blocked; only a search summary of it was available |
| d-Matrix Corsair press release and trade press | seen as search snippets only; marketing |
| Tenstorrent docs.tenstorrent.com pages | blocked |
| Horowitz ISSCC 2014 "Computing's energy problem" | not downloadable; numbers come from a 2026 arXiv paper that quotes it |

What I **did read completely or in the relevant parts** (downloaded, converted with pdftotext or raw markdown, stored in the session scratchpad):

1. Tenstorrent `METALIUM_GUIDE.md` (tt-metal repo, about 6,200 words, read fully).
2. Tenstorrent `tt-isa-documentation`, Wormhole B0: `TensixTile/L1.md` (full), `NoC/README.md` (full). These are hardware reference documents written by the vendor, the closest thing to an architecture manual that is public.
3. Tenstorrent `tt-metal` tech reports: GEMM_FLOPS (header and summary read, tables skimmed) and TT-Fabric (architecture overview read, parts skimmed).
4. Brown, Davies, Le Clair, "Exploring Fast Fourier Transforms on the Tenstorrent Wormhole", arXiv 2506.15437 (third-party measurement on real hardware; read fully).
5. Houshmand, Sun, Verhelst, "Benchmarking and modeling of analog and digital SRAM in-memory computing architectures", arXiv 2305.18335 (KU Leuven; survey plus validated energy model; read the body).
6. Karfakis et al., "MXFormer: a microscaling floating-point charge-trap transistor compute-in-memory transformer accelerator", arXiv 2602.12480 (22 nm CTT non-volatile CIM, with area/power tables; read the relevant sections).
7. Rojkov et al., "Investigating energy bounds of analog compute-in-memory with local normalization", arXiv 2602.08081 (read the energy-bound passages only).
8. Sze et al., "Efficient processing of deep neural networks: a tutorial and survey", arXiv 1703.09039 (read the memory-hierarchy energy figure).
9. Lee and Bruck, "Data gravity and the energy limits of computation", arXiv 2603.26053 (read the energy-table passage; it quotes Horowitz, Google TPUv4i and UPMEM).
10. Secondary: wafer-scale computing survey arXiv 2310.09568 (its Table II lists Dojo and Cerebras figures), and the LLM-accelerator survey arXiv 2510.16805 (one paragraph each on Dojo and Corsair).

I looked for a dedicated d-Matrix arXiv paper and for a Dojo arXiv paper and found none. I did not find a Mythic paper with an energy table that I could read, so the non-volatile example is MXFormer's charge-trap macro, and the analog-flash discussion is limited to what these surveys say.

## 1. Tesla Dojo (D1 chip and training tile)

**Source quality.** Primary slides blocked. Everything in this section is UNVERIFIED against the slides, but the same figures appear in two independent secondary places (a search summary quoting the slides, and Table II of the wafer-scale survey arXiv 2310.09568, which cites Talpes, Williams and Sarma, Hot Chips 2022).

**Memory capacity and organisation (UNVERIFIED, consistent across secondaries).**
- Each Dojo node (a core) has 1.25 MB of SRAM, used as plain main memory, not as a cache.
- A D1 die has 354 usable nodes in an 18 x 20 grid (the grid is larger than the number used, probably for yield), about 440 MB of SRAM per die.
- A training tile joins 25 D1 dies (5 x 5) plus I/O dies (40 I/O dies in the survey's description). The survey's table gives 11 GB SRAM per tile, 8,850 nodes, 9.1 POPS (peak, vendor), about 15 kW per tile, 9 TB/s network bandwidth per tile (the secondary sources disagree with each other on tile-edge bandwidth: 4.5 TB/s per edge in the slide summary, 36 TB/s total off-tile in another article, "2 TB/s per D1 die edge" in the survey; I do not know which unit each uses, so none of these is used below).
- DRAM (HBM) sits on the side of the tile and is far from the nodes; the survey notes Dojo developers said locality has to be enforced because the cost of moving data between HBM and central dies is high.

**Bandwidth.** Per node: 400 GB/s load and 270 GB/s store from the local SRAM (UNVERIFIED, same source; the survey gives "270-400 GBps").

**How compute and memory are interleaved.** A node is a small full computer: a scalar general-purpose part (branches, flexibility, the survey says including "sparse computing" support) and a wide vector/matrix part, with the node's SRAM next to it, and a mesh router. Nodes are tiled into a 2D mesh with no shared memory; data moves by explicit messages. Per-node compute is about 1.02 TOPS (DERIVED by the survey as total divided by node count, not a measurement). A node uses under 1.7 W by the same division (DERIVED).

**Operations and precision.** Dense MACs in BF16 and Tesla's configurable 8-bit float (CFloat8) (per the LLM-accelerator survey, UNVERIFIED). It is a multiply-accumulate machine. The scalar side exists because dense matrix hardware is awkward for irregular work.

**Scaling and its cost.** The whole point is a 2D mesh of identical nodes that continues across die and tile boundaries, with pipeline parallelism across chips instead of large per-chip memory. The cost is packaging: the tile is a wafer-scale object (over 16,000 mm2 as 25 dies), 15 kW, with custom power and cooling. The interconnect energy cost: the wafer-scale survey gives off-chip inter-die links at roughly 10 pJ/bit and on-chip at roughly 0.1 pJ/bit (survey table, generic, not Dojo-specific).

**Limits and failure modes.** 1.25 MB per node is small; the model must be partitioned so each node's slice fits, and a miss means a trip over the mesh or to HBM. Yield is handled by testing dies before assembly (known-good dies) and by having fewer usable nodes than the grid. The LLM survey (arXiv 2608.28048, seen in a search summary only) says Tesla wound the Dojo programme down in 2025; I could not verify this from a primary source.

**Measured results.** None in sources I could read. All performance numbers for Dojo are vendor peak claims.

## 2. Tenstorrent (Grayskull, Wormhole, Blackhole)

**Source quality.** The best-documented of the three. The ISA documentation and the Metalium guide are vendor documents, and the FFT paper is a third-party measurement, partly co-authored by a Tenstorrent employee.

**Memory capacity and organisation.**
- Each Tensix tile has **1464 KiB (Wormhole) or 1536 KiB (Blackhole) of plain scratchpad RAM**, called L1 but explicitly not a cache (ISA doc). No cache hierarchy anywhere on the chip; "any component can read from or write to SRAM located in other Tensix cores" over the NoC (Metalium guide).
- In Wormhole, L1 is 16 banks of 91.5 KiB; each bank does one 128-bit read or one 128-bit write per cycle; 16 ports; bank conflicts serialise (ISA doc). DERIVED peak at the 1 GHz clock stated in the GEMM report: 16 banks x 16 B = 256 B per cycle = 256 GB/s per tile, theoretical, shared among all clients.
- Wormhole n300 card: two chips, 120 Tensix cores (60 per chip), 24 GB GDDR6 in 24 banks of 1 GB (FFT paper). The ISA doc says each DRAM tile holds 2 GiB GDDR6 reachable through six NoC interface units. The compute grid used by the matmul benchmark is 8 x 8 on Wormhole and 13 x 10 on Blackhole (GEMM report). DERIVED SRAM per Wormhole compute grid: 64 x 1464 KiB, about 91.5 MiB, so the whole on-chip SRAM is two orders of magnitude below a model of any size; DRAM is the real store and L1 is a staging area ("hybrid" approach in the guide).

**Interconnect (ISA doc, NoC README).** Two physically separate NoCs, each a 2D torus, flowing in opposite directions. Flit = 256 bits. Throughput one flit per cycle per axis per hop, router-to-router latency 9 cycles, NIU-to-router about 5 cycles. DERIVED at 1 GHz: 32 GB/s per link per direction. Packet = one header flit plus up to 256 data flits (8192 B); very short packets carry 4 bytes of data behind a single header flit. The NoC supports: reads, writes, **atomics**, **broadcast writes to a rectangle of tiles**, and partial writes where "any arbitrary subset of the 16 (or 32) bytes" is written, plus a 32-bit immediate broadcast four times. Between chips: Ethernet (4 links per direction on Wormhole, 2 on Blackhole in TT-Fabric); a software/firmware fabric with routing tables, link-failure re-routing, and TT-link mode with sequence numbers. The vendor claims standard Ethernet up to 800G per chip (VENDOR).

**How compute and memory are interleaved.** Five tiny RISC-V "baby" cores per tile (RV32IM, no task switching): one moves data in, one moves data out, three drive the compute engine (unpack, math, pack). They do not touch the data themselves; they issue instructions to the NoC, the unpacker, the matrix unit (FPU), the vector unit (SFPU) and the packer, which access L1 directly. Software model: reader kernel, compute kernel, writer kernel, linked by **circular buffers in L1** with hardware metadata for synchronisation. The guide stresses explicit data movement, no coherence protocol, deterministic latency. The compute engine works on 32 x 32 tiles of values.

**Operations and precision.** FPU: matrix multiply, add, subtract, multiply, transpose, reduction; the paper states 2048 multiplies and 2048 adds per cycle per matrix engine. SFPU: vector unit, eight registers of 32 lanes, with squares, roots, trig, conditionals. GEMM report: about 4 TFLOPS per matrix engine at 1 GHz in the lowest fidelity mode (Wormhole), about 1 TFLOPS in the highest; peak measured whole-card matmul "around 190 TFLOPs" on Wormhole and 580 on Blackhole (vendor-run benchmark, so VENDOR/MEASURED by the vendor, not independent). Formats from FP32 down to block formats BFLOAT8_B and BFLOAT4_B. So the chip is a dense-tile MAC machine; Tenstorrent's contribution is the memory and movement design, not avoiding multiplies.

**What the L1 does that is not a MAC (important for L).** From the ISA doc, L1 access ports support **atomic read-modify-write on 32-bit integers: atomic increment, compare-and-increment (used for FIFO metadata), compare-and-set**, and a **near-memory accumulate of 4 x FP32 or INT32 (saturating) or 8 x FP16/BF16** exposed to the packers. Each atomic blocks the port and the bank for five cycles (two for a non-atomic accumulate variant). A narrow write (under 128 bits) is also a five-cycle read-modify-write. The NoC can issue atomics to a remote tile's L1 and get a 32-bit result back, and can broadcast atomics to a rectangle of tiles. So, in the ISA, a remote counter increment is a first-class NoC transaction, at a cost of five bank-cycles.

**Sparse and conditional execution.** I found no sparse-execution or event-driven hardware in the documents I read. Conditionals exist in the SFPU (predicated vector lanes) and software decides what to move; there is no hardware skipping of zeros. The "conditional" part of the founder's question is, in these documents, only the compare-and-increment atomics and software control flow on the baby cores. Not found: a Tenstorrent document on sparsity. UNVERIFIED whether one exists on blocked pages.

**Scaling and its cost.** Cards scale by Ethernet in a mesh (QuietBox: 8 Wormhole or 4 Blackhole chips). The chips can also act as network switches. Cost per the guide: the developer owns data placement, sharding and movement; kernels written for Grayskull (64-wide vectors, 19-bit float) do not run on Wormhole or Blackhole (32-wide, 32-bit), so every generation costs a software rewrite.

**Limits and measured results (FFT paper, MEASURED, third party).** Wormhole n300 running a 2D FFT in FP32 on 64 Tensix cores is **slower than a 24-core Xeon**, but draws about 8 times less power and used about 2.8 times less energy. On a single Tensix core, 16,384-point FFT took 14.39 ms initially versus 1.85 ms on one Xeon core. Removing data reordering halved the runtime; removing both read and write reordering gave about one sixteenth. The best optimised version reached 5.31 ms, still 2.9 times slower than one Xeon core. Lesson: the baby cores are poor at irregular data movement ("the cores are fairly limited and designed more for driving components"); for narrow stores the L1 costs five times the bandwidth of a 128-bit write; irregular gather/scatter is the bottleneck. A prior Grayskull stencil study (cited in the paper) got CPU-level performance at five times less energy after the code became about 160 times faster than the naive version. Takeaway: the architecture is efficient when data movement is regular and bulk, and weak at fine-grained reorders.

## 3. d-Matrix (Corsair, digital in-memory compute)

**Source quality.** The technical whitepaper was blocked. There is **no arXiv paper from d-Matrix** that I could find. Everything is UNVERIFIED and partly marketing; independent validation is missing (a TechInsights note, seen as a snippet, says the company had not published industry benchmarks such as MLPerf).

**What the sources say (UNVERIFIED).**
- Hierarchy (whitepaper, by a search summary): a chiplet has four Quads, each with four Slices, a RISC-V control core and a dispatch engine; each slice has DIMC cores, SIMD cores and a data reshape engine.
- Card: eight chiplets, 512 MB SRAM in total (LLM-accelerator survey arXiv 2510.16805, which cites the whitepaper). Launch release (snippet): PCIe Gen5 card, 2 GB "performance memory" integrated, up to 256 GB off-chip capacity memory, 2400 TFLOPs peak 8-bit. Trade press quotes 9,600 TOPS at 12-bit block floating point and 600 W TDP. The two sets of figures conflict, so I do not use them.
- Number format: a block floating-point format (BFP12, groups of values share an exponent) and INT8; higher-precision accumulation.
- Claim (VENDOR): 60,000 tokens per second at 1 ms per token for a Llama3 8B model in one server (preliminary, per the vendor's own note).
- Chiplets are used to beat reticle limits and improve yield; cards pair through bridge cards.

**What this tells us even without the whitepaper.** The key idea is digital in-memory compute (DIMC): the multiplier-cell sits in the SRAM array and a digital adder tree accumulates, so there is no analog noise and no ADC. A more reliable description of the DIMC family is in section 4 (Houshmand et al.). The workload is a dense matrix-vector product with weights held in SRAM, so d-Matrix is a MAC design even though the MAC is inside the array. Memory is split between small fast SRAM (512 MB per card) and large slow capacity memory, and the claim is that decode (memory-bound) inference benefits from SRAM bandwidth. The cost: weights must be loaded into the array, and a model larger than the SRAM spills to the capacity memory, where the benefit disappears (inference, but I could not find what ratio they accept).

**Measured results.** None that I could read.

## 4. In-memory computing macros with energy tables

### 4.1 Houshmand, Sun, Verhelst (KU Leuven), arXiv 2305.18335

A literature benchmark plus an analytical energy model validated against published silicon (MEASURED chips from other papers, MODELLED by the authors; mismatch to reported values is within about 15% for most analog designs and about 10% for digital).

- **Analog versus digital IMC.** In DIMC the stored weight row is read and combined with the input in a binary multiplier cell tightly integrated with the SRAM cells, then accumulated by a digital adder tree. In AIMC all rows are activated at once and A/D conversion is needed. AIMC is more energy efficient only if the converter cost is amortised over a very large array and utilisation is high; DIMC trades efficiency for noise-free results and flexible array shape.
- **Peak numbers in their survey figure (MEASURED by the original authors, peak, at stated precision).** Best analog peak about 1800 TOP/s/W [their ref 26], in a very large array with optimised converters; best density from a 7 nm design with flash ADCs. DIMC points (22 nm, 28 nm) sit lower in TOP/s/W. Only designs reporting 50% sparsity were kept for fairness. Peak figures vary with precision and voltage, and the authors warn they are poor predictors of workload energy.
- **Model constants (MODELLED).** ADC energy k1 = 100 fJ, k2 = 1 aJ (formula E_ADC = (k1 x res + k2 x 4^res) x V^2 ...); DAC about 44 fJ per conversion step. Bit-line and word-line energy proportional to C x V^2; adder tree modelled as 5 gates per full adder.
- **Case study (MODELLED).** On tinyMLPerf networks with equal total SRAM cells: big-array analog macros win on layers with high accumulation and weight reuse (convolutions, ResNet8); they lose on fully connected layers with no weight reuse, because weights must be rewritten each time (DeepAutoEncoder) and on depthwise/pointwise layers. Small arrays with many macros stay well utilised but need more traffic to outer memory for inputs and partial sums. Energy for weight writes and outer-memory traffic is a large share.
- **Leakage** is not in the model and dominates at low voltage and frequency (a 0.6 V DIMC point diverges).

### 4.2 MXFormer, UCLA, arXiv 2602.12480 (non-volatile, charge-trap transistor)

A 22 nm FDSOI charge-trap-transistor (CTT) analog current-summing macro. **Energy numbers are MODELLED**: analog blocks extrapolated from a post-layout macro and characterised CTT cells; digital blocks synthesised to the 22 nm library; SRAM from vendor datasheets. The authors say they did not build the full system.
- Macro (Table 3): 768 x 768 array, 1.78 mm2, 20.02 TOPS, 58.83 TOPS/W, 11.26 TOPS/mm2; 1024 x 1024 array, 2.97 mm2, 35.72 TOPS, 75.72 TOPS/W, 12.02 TOPS/mm2; 5-bit weights and inputs, 10-bit outputs, analog clock 169 MHz, multiplexing degree 10 (only one bit-line logically active, which lowers throughput by the multiplexing degree). DERIVED energy per operation: 1 / 75.72 TOPS/W is about 13.2 fJ per op for the 1024 array, about 17 fJ for the 768 array (the paper does not define whether an op is a MAC or two ops here; I assume it follows the usual 2 ops per MAC but this is UNVERIFIED).
- System (Tables 4, 5): the Large system is 561.5 mm2, 182.6 W, 2631.6 TOPS, 4.69 TOPS/mm2, 14.41 TOPS/W. In that system the CTT macros take 427.7 mm2 of area but only 67.8 W; the digital systolic arrays take 58 mm2 but **85 W**; SRAM takes 46 mm2 and only 0.2 W. So the digital remainder (systolic array for attention, vector units, softmax) costs more power than the memory macros. At peak, the analog macro is not the energy problem; everything around it is.
- Storage density: about 1756 kb/mm2 for the 1024 CTT arrays, against about 34 kb/mm2 for a TSMC gain-cell microscaling macro they cite (ISSCC 2025, not read). The point of non-volatile storage here is to hold the **whole model on the die** ("fully weight-stationary"), so only activations stream (about 16 GB/s PCIe is enough; at 19 pJ per bit for LPDDR4 the I/O power is below 1%).
- Failure modes and limits stated: calibration of current mirrors (write-verify-write), limited dynamic range handled by exponent alignment and a two-pass scheme that halves throughput, 10-bit ADC cost, sequence-length balance (analog work grows with N, the digital attention with N squared), and accuracy loss on small models (for example BERT-Base SQuAD F1 73.1 for the MXFP4 reference versus 72.2 on their model of the hardware).
- The comparison with a 5 nm B200-class GPU (14.4 versus 9 or 4.5 TOPS/W, 4.7 versus 1.13 TOPS/mm2) is against the GPU's published peak, using the authors' modelled numbers. Treat as MODELLED vs VENDOR.

### 4.3 Energy-bound paper, arXiv 2602.08081

An upper limit of 100 fJ/op (10 TOPS/W) and a design point near 29 to 30 fJ/op are discussed for analog CIM with local normalisation (MODELLED). Not read beyond these passages.

### 4.4 Digital SRAM macro titles seen but not read

From reference lists and search snippets only (UNVERIFIED, I did not read the papers): a 28 nm 29.2 TFLOPS/W BF16 and 36.5 TOPS/W INT8 digital CIM; a 5 nm 254 TOPS/W 221 TOPS/mm2 fully digital CIM (title in the Houshmand reference list); a 6T-SRAM digital macro "D6CIM" at 60.4 TOPS/W, 1.46 TOPS/mm2, 1005 kb/mm2 (title only). I list them because they show the order of magnitude of digital CIM at the macro level: tens to low hundreds of TOPS/W, at 1 to 8 bit precision, macro level and peak.

## 5. Energy per access: memory against compute-in-memory against off-chip

All of these are 45 nm or mixed-node figures, so only the ratios are meaningful.

| Quantity | Value | Label and source |
|---|---|---|
| Int32 add (45 nm) | 0.1 pJ | UNVERIFIED primary; quoted in arXiv 2603.26053 (Horowitz) |
| FP operations (45 nm) | 0.4 to 3.7 pJ | same |
| On-chip cache/SRAM access, 64-bit (45 nm) | 10 to 100 pJ depending on size | same |
| Off-chip DRAM, 64-bit (45 nm) | 1300 to 2600 pJ (about 20 to 40 pJ per bit) | same |
| 7 nm: Int32 0.03 pJ, FP32 1.31 pJ; DDR 1300 pJ per 64-bit, GDDR6 350 to 480, HBM 250 to 450 | | quoted from Google TPUv4i analysis in the same arXiv paper, UNVERIFIED primary |
| Normalised access cost: register file 1x, neighbouring PE over NoC 2x, 100-500 kB buffer 6x, DRAM 200x | | arXiv 1703.09039 (Eyeriss line of work), figure read |
| LPDDR4 | 19 pJ per bit | assumed in arXiv 2602.12480 |
| On-chip link roughly 0.1 pJ/bit, off-chip die-to-die about 10 pJ/bit, ultra-short-reach below 1 pJ/bit | | arXiv 2310.09568 table, generic |
| CIM macro, per operation | about 13 to 17 fJ (CTT, MODELLED), 30 to 100 fJ (analog bounds, MODELLED); digital CIM tens to low hundreds of TOPS/W so roughly 5 to 30 fJ per 1-8 bit op at peak (UNVERIFIED) | sections 4.1 to 4.4 |
| UPMEM DRAM PIM | 170 pJ against 3010 pJ per 64-bit operand operation (vendor claim of 20 times); an independent evaluation found savings of 11 to 20% on some database operations and a 58% increase on others | arXiv 2603.26053 |

The honest ordering: a multiply-free integer add is about 0.1 pJ; a small SRAM read is 10 pJ or more per 64 bits (a factor of 100 above the add); off-chip DRAM is another 100 times above that. A CIM macro avoids reading the stored operand out of the array, so its per-operation energy can fall below the energy of reading one word, but only when the operand is reused across many cycles; the Leuven study shows that weight rewrites, inputs, partial sums and ADCs eat much of the gain on real workloads.

## 6. What transfers to L

**A counter or lookup macro, not a MAC.** None of the three companies built one, but the pieces are public.
1. Tenstorrent's L1 already exposes the operations an L tile needs as hardware primitives: atomic increment, compare-and-increment, compare-and-set, saturating integer accumulate near the SRAM bank, partial-byte writes, and remote atomics over the NoC with a returned result. It pays five bank-cycles for each read-modify-write. A counter macro for L should fold this into the array: a row-wise read-increment-saturate-write done at the sense-amplifier/write-driver level in one access, rather than a bank-wide five-cycle lock. That is a design the literature suggests but I found no paper that measures one; the cost is a small saturating incrementer per column group and a write-back path (ESTIMATED, no source).
2. The CIM energy gain comes from not moving the stored operand; for a lookup/counter macro the same holds: the "compute" is an increment or a compare of a few bits, much cheaper than the 5-gate full adders the Leuven model uses for MAC adder trees. A tile where the lookup row and its counter are updated in place avoids every DRAM-like trip. The Leuven point about weight rewrites applies in reverse: L's counters are written on every training event on the Cortex side (or in place), so write energy and endurance matter, which argues for SRAM, not charge-trap or flash cells.
3. Do not copy the analog route: ADCs, calibration, and noise are all exactly what a matrix-free counting chip avoids, and the macro energy numbers above are dominated by ADC and the digital remainder once the array is efficient (MXFormer: 85 W in digital arrays against 68 W in the CTT macros).

**Tile memory sizing.** Reference points: 1.25 MB per Dojo node (UNVERIFIED), 1.43 to 1.5 MB per Tenstorrent tile. Both are chosen to hold a tile's working set plus buffers; both rely on a larger store (HBM or GDDR6) behind. For L the table is the model, so the sizing question is how many counters per tile. A 1 MB tile at 8-bit counters holds about 1 million counters (DERIVED); Tenstorrent's 16-bank, 128-bit-per-cycle organisation shows how to give a tile enough ports (one bank access per cycle per client) so that an event engine, a NoC interface and a writeback path do not stall each other. Bank conflicts are the failure mode to design against: random hash lookups into a few banks will conflict, so L should hash to bank first and queue per bank.

**Event routing.** The Tenstorrent NoC is the closest public match: 256-bit flits, header plus data, tiny packets of 4 bytes behind one header flit, atomics, rectangle broadcast, two opposite-direction tori, ordering weak by default and optionally strengthened. Observations for L: a packet of one header flit is at least 32 bytes on the wire for a 4-byte payload (87.5% waste), so L's tiny address events should be packed several to a flit, or the NoC flit narrowed to 32 to 64 bits, and the router should use the event's address bits for routing. Dojo's mesh with node-local SRAM and explicit messages and Tenstorrent's no-coherence rule agree: no cache coherence, explicit placement. Both show that fine-grained gather/scatter is the weak spot (the FFT paper: reordering cost dominated). L's event traffic is exactly fine-grained scatter, so it must be a hardware path (router and tile-side queue), not software on tiny cores. Multi-chip: Ethernet-class links with re-routing exist on Tenstorrent; Dojo's tile packaging is out of reach for a small team.

**Honest account of what a small team can and cannot build or claim.**
- Can: an RTL tile (counter array, hash/lookup, event queue, router) and its bit-exact regression, which L Cortex already has; synthesis and place-and-route to an open or academic PDK; SRAM macro energy from a memory compiler or published datasheets; an FPGA or emulation for system-level behaviour; honest analytical energy models in the style of the Leuven paper, validated against published silicon, each labelled MODELLED.
- Cannot, without a foundry shuttle and years: silicon measurements of a custom compute-in-SRAM or charge-trap macro; wafer-scale or chiplet packaging; a production software stack. Every vendor above needed all three.
- Cannot claim: any TOPS/W or fJ per op for L as MEASURED. The numbers in section 5 are peak macro figures at 1 to 8 bit, at stated voltages, and the literature shows system efficiency sits well below them (MXFormer: macro 75.72 TOPS/W, whole system 14.41). L should compare against a GPU only as MODELLED, with the counting workload spelled out, and not borrow the "9.1 POPS" or "60,000 tokens per second" style of peak claims.
- Tenstorrent's example shows the credible shape of a result: a third party measured energy on real hardware and reported it was slower than a CPU but used less energy, with reasons. That is the form L's claims should take.

## 7. xAI: does it design its own AI chip?

**Finding: no public technical source exists.** Search results (late 2024 onward reporting on the Colossus cluster in Memphis, 100,000 Nvidia H100 GPUs first, planned growth with H200 and later Blackwell, Spectrum-X Ethernet) describe xAI as a buyer of Nvidia GPUs. The custom elements reported were infrastructure (liquid cooling), not silicon. A 2026 search turned up no reporting on an xAI chip programme, tape-out, or paper; results show only that xAI is now referred to as SpaceXAI after a reported February 2026 acquisition (secondary sources, may be out of date). There is no xAI Hot Chips talk, whitepaper or arXiv paper that I could find. The chip design in the Musk group's orbit is Tesla's (the Dojo D1 above, and the in-car chips), and xAI sources I found do not claim to reuse it. Everything here is UNVERIFIED reporting; for L nothing can be learned about xAI hardware from public documents.

## 8. Summary

- Dojo and Tenstorrent both chose many small nodes, each with 1.25 to 1.5 MB of plain SRAM, a mesh network and explicit data movement, and no caches. This is the same shape as L's tile-plus-mesh idea, but their tiles are built around dense multiply-accumulate engines that L must avoid.
- Tenstorrent's public ISA already treats an atomic increment and compare-and-increment on the tile SRAM as first-class, a useful existence proof for an L counter macro, with a five-cycle cost that an L-specific macro should remove.
- d-Matrix has no public technical text I could read; treat Corsair as UNVERIFIED and partly marketing.
- Macro-level compute-in-memory reaches roughly 10 to 100 fJ per operation at peak and low precision (MODELLED or reported peak), against about 0.1 pJ for an integer add, 10 pJ or more for a small SRAM read, and about 1300 pJ per 64-bit off-chip DRAM access at 45 nm (UNVERIFIED primary), and system-level efficiency is several times worse than macro peak.
- No source reports sparse, event-driven hardware execution; L's event path would be its own design, not a borrowed one.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
