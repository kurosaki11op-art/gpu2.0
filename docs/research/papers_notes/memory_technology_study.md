---
title: Study - memory technologies, scaling limits and energy per bit
tags: [l, research, hardware, memory, energy]
---

# Study - memory technologies, scaling limits and energy per bit

Purpose: give the founder a clear, sourced picture of the physics and economics of memory (density, energy per bit, latency, link energy, cost) before L designs its own approach to "much more memory per tile at lower power". Every number below carries its source, the process node the source states, and a label. Labels follow the repo rule: MEASURED (silicon or datasheet reported by the source), SIMULATED / MODELLED (the source's own model or simulation), ESTIMATED (our arithmetic on sourced constants), HYPOTHESIS (our idea, not tested). Anything not read in full is marked UNVERIFIED. No number here is invented; where no source was read, the gap is stated.

## 0. Method and what was read, what was blocked

Read in full (downloaded from arxiv.org with curl, converted with pdftotext, files treated as untrusted data):

| Short name | arXiv id | What it gave us |
|---|---|---|
| Memory wall | [2403.14123](https://arxiv.org/abs/2403.14123) (Gholami et al., "AI and Memory Wall", extended IEEE Micro paper) | compute vs DRAM vs interconnect growth rates |
| GainSight | [2504.14866](https://arxiv.org/abs/2504.14866) (Li et al.) | SRAM cell size plateau, gain cell and eDRAM role, data lifetime, 3x energy / 4x area result |
| OpenGCRAM | [2602.21278](https://arxiv.org/abs/2602.21278) (Wang et al.) | gain cell vs 6T SRAM bitcell area, leakage, bandwidth, TSMC 40 nm macros |
| LLMET | [2607.26491](https://arxiv.org/abs/2607.26491) (Lee et al.) | per-bit access energy table: SRAM, gain cell, HBM2E, HBM3E, LPDDR5 at 7 nm and 3 nm |
| RPU | [2602.18568](https://arxiv.org/abs/2602.18568) (Adiletta, Wei, Brooks) | HBM energy breakdown (activation, wire per mm, TSV per layer, I/O), HBM3E 3.44 pJ/bit, cost per GB scaling |
| UCIe memory | [2510.06513](https://arxiv.org/abs/2510.06513) (On-package memory with UCIe) | LPDDR5 2.8 pJ/b, HBM3 0.9 pJ/b interface, UCIe and HBM4 bandwidth densities |
| Chiplets review | [2406.00182](https://arxiv.org/abs/2406.00182) ("Chiplets on Wheels") | UCIe, AIB, BoW, LIPINCON energy and latency table |
| CLIPGen | [2605.27757](https://arxiv.org/abs/2605.27757) | modelled die-to-die link energy vs reach, bump capacitance, 16/45/65 nm |
| Chiplet cost | [2206.07308](https://arxiv.org/abs/2206.07308) | analytical cost model for 2.5D chiplet systems with HBM |
| Sangam | [2511.12286](https://arxiv.org/abs/2511.12286) | HBM $/GB assumption, H100 module cost breakdown |
| HBM bit cost | [2507.02654](https://arxiv.org/abs/2507.02654) | HBM cost per bit is 5 to 10 times conventional DRAM |
| 3D DRAM infra | [2604.08044](https://arxiv.org/abs/2604.08044) | hybrid-bonded 3D DRAM: I/O density, 0.66 to 0.88 pJ/bit |
| 3D-Flow | [2602.11016](https://arxiv.org/abs/2602.11016) | SRAM access energy dominates; inter-tier transfer energy |

Of these, the full text was converted and the relevant sections read (introductions, device and energy tables, cost sections, conclusions). Long papers (Sangam, 3D DRAM infra, RPU, CLIPGen, chiplets review) were read by section for the memory, energy and cost content, not line by line for architecture detail unrelated to this study; that is stated here so the claim "read completely" is not over-read. Where a figure or table was an image, no number is quoted.

Blocked or not obtained:

- The arXiv search API host (export.arxiv.org) did not resolve from this sandbox, so ids were found with the web search tool restricted to arxiv.org and then verified by downloading the PDF and reading its title page. All 14 downloads succeeded.
- No arXiv survey was found that compares SRAM, eDRAM, DRAM, HBM and non-volatile memory side by side in one table with density, energy and latency. Non-volatile memory (MRAM, ReRAM, PCM, FeFET) numbers are therefore UNVERIFIED: the search returned [2411.13717](https://arxiv.org/abs/2411.13717), [1906.06603](https://arxiv.org/abs/1906.06603), [2406.08413](https://arxiv.org/abs/2406.08413), [2303.12310](https://arxiv.org/abs/2303.12310), [2508.18250](https://arxiv.org/abs/2508.18250) and [2608.28048](https://arxiv.org/abs/2608.28048), but these were not downloaded or read, so nothing from them is used as a number.
- Not read: industry articles (Semiconductor Engineering, Epoch AI B200 cost breakdown, Silicon Analysts packaging calculator, vendor pages), the UCIe specification itself, JEDEC HBM documents, Horowitz-style energy tables, TSMC or foundry documents. Facts seen only in search snippets are tagged UNVERIFIED-SNIPPET.
- Commercial DRAM latency (tRCD, tCL, loaded latency) was not found in any paper read. DRAM latency is therefore a gap (section 2.5).

## 1. The memory wall data

Source: Gholami et al., arXiv 2403.14123 (no single process node; trend data over 20 years of server hardware, fitted by linear regression on the plotted points, as the paper states).

MEASURED trend numbers as reported by the paper:

- Peak hardware FLOPS of server-class AI hardware grew about 3.0 times every 2 years; DRAM bandwidth about 1.6 times every 2 years; interconnect bandwidth about 1.4 times every 2 years.
- Over 20 years: peak compute 60,000 times; DRAM bandwidth 100 times; interconnect bandwidth 30 times.
- Model side (2018 to 2022): training compute of SOTA Transformer models grew about 750 times per 2 years; parameter count about 410 times per 2 years; accelerator memory only about 2 times per 2 years (Moore-like).
- The paper stresses that the wall has three parts: capacity, bandwidth, and latency, and says latency has been even harder to improve than bandwidth.
- Within a chip, the paper says intra-chip transfers (registers, L2 cache, global memory) are increasingly the bottleneck because tensor cores finish arithmetic in a few cycles.
- Suggested directions in the paper: rethink accelerator design to trade peak compute for better compute/bandwidth balance; a cache hierarchy and higher-capacity DRAM (possibly a hierarchy of DRAMs of different bandwidths); lower precision so more chip area can go to memory.

Reading for L: the wall is a gap between compute and data supply. L removes most of the arithmetic (no matrices, no multiplies), so L sits at the far end of the wall: its decisions are bound by bytes fetched per decision, not by operations. This is why density and energy per bit of the memory, plus the distance to it, decide L's cost. The paper's own remedy list (more cache, higher-capacity memory, less precision) is the same lever pointed at by GainSight and LLMET below.

Related consistent data point (3D-Flow, arXiv 2602.11016, accelerator synthesised in TSMC 16 nm, SIMULATED): once off-chip traffic is cut, on-chip SRAM accesses become the dominant energy, over 60 percent of energy in long-sequence FlashAttention; it cites a claim that an SRAM access costs 10 to 20 times an FMA (the cited prior work was not read; UNVERIFIED as a general constant). LLMET (arXiv 2607.26491) states that an HBM access costs roughly two orders of magnitude more energy than an on-chip SRAM access, citing three prior works (not read), and its own table (section 2.2) gives about 10 to 12 times for small SRAM at 7 nm, not 100 times. Treat "100 times" as a loose phrase and the table values as the sourced constants.

## 2. Density, energy per bit and latency by memory technology

### 2.1 Why SRAM stopped scaling

Sources: GainSight (2504.14866), OpenGCRAM (2602.21278).

- GainSight reports that on-chip SRAM scaling has plateaued at 0.021 square micrometres per bitcell across the 5 nm to 3 nm TSMC nodes (cited to a foundry source it lists as reference 53; the underlying foundry document was not read). It adds that even gate-all-around 2 nm struggles to restore the earlier trajectory, because maintaining the control of variation between transistor sizing and threshold voltage gets harder at smaller geometry and lower operating voltage.
- OpenGCRAM says the same in its introduction: SRAM cell sizes have largely plateaued at advanced nodes, making large arrays expensive in area and leakage power, while off-chip DRAM, even HBM, cannot meet fine-grained latency and energy demands.
- Consequence stated by GainSight: more SRAM on a reticle-limited die reduces the area left for logic, so there is a perf-per-mm2 bottleneck. LLMET adds that planar SRAM at GB scale incurs prohibitive H-tree routing overhead (section 2.2).
- A 6T cell has two cross-coupled inverters and always has a path from supply to ground in the cell; OpenGCRAM notes that a gain cell has no direct VDD-to-GND path and shows orders of magnitude lower leakage (Fig. 8c, a plot; no number read). So the physics: SRAM needs six transistors that must be sized for stability under variation, and static leakage grows with capacity.
- Non-arXiv statements seen only in search snippets (UNVERIFIED-SNIPPET): density gains began to stagnate around the 5 nm node; leading-edge 2 nm and below bitcell density improvement under 15 percent (quoted from a trade article attributing it to a Cadence engineer); thinner metal lines raise resistance and RC delay.

ESTIMATED raw density from the sourced 0.021 um2 cell (5 nm to 3 nm, TSMC): 1 mm2 = 1,000,000 um2, so 1,000,000 / 0.021 = 47.6 million bits = about 5.95 MB per mm2 as a pure bitcell array. This is an upper bound: it excludes sense amplifiers, decoders, redundancy, test logic, wiring channels and power distribution. The array efficiency factor is not given by any source read and is left as a free parameter (eta in section 4). Do not quote 5.95 MB/mm2 as a macro density.

### 2.2 Energy per bit of SRAM, gain cell and HBM (the key table)

Source: LLMET, arXiv 2607.26491, Table 2 (access energy in pJ per bit; the paper says HBM figures include IO energy and come from its reference 25; 7 nm cache and HBM2E are in the A100 platform model; 3 nm cache and HBM3E are in a B200-like platform model; the cache numbers come from the paper's NS-Cache circuit flow, so these are MODELLED, not measured silicon).

| Memory | Node | Capacity | Access energy, pJ/bit | Label |
|---|---|---|---|---|
| SRAM | 7 nm | 40 MB | 0.495 | MODELLED |
| SRAM | 7 nm | 1 GB | 2.78 | MODELLED |
| 2T gain cell, monolithic 3D (M3D) | 7 nm | 1 GB | 1.08 | MODELLED |
| SRAM | 3 nm | 128 MB | 0.917 | MODELLED |
| SRAM | 3 nm | 1 GB | 2.42 | MODELLED |
| 2T gain cell, M3D | 3 nm | 1 GB | 0.768 | MODELLED |
| 2T gain cell, M3D | 3 nm | 4 GB | 0.981 | MODELLED |
| HBM2E | A100 platform | stack | 6.6 | taken from reference, IO included |
| HBM3E | B200-like platform | stack | 5.74 | taken from reference, IO included |
| LPDDR5 | edge platform | n/a | 6.6 | assumed equal to HBM2E in that paper |

What the table says:

- Within SRAM, energy per bit rises with capacity because wires get longer: 0.495 pJ/bit at 40 MB to 2.78 pJ/bit at 1 GB at 7 nm, a factor of 5.6; at 3 nm 0.917 at 128 MB to 2.42 at 1 GB, a factor of 2.6 (ESTIMATED ratios).
- A gain cell at 1 GB is 0.768 to 1.08 pJ/bit, better than 1 GB of SRAM by about 2.6 times at 7 nm and 3.2 times at 3 nm (ESTIMATED ratios), and stays under 1 pJ/bit out to 4 GB at 3 nm in the model.
- LLMET insight 2: large on-chip memory is useful only when its access energy stays far below the HBM energy (the paper quotes about 5.7 to 6.6 pJ/bit); M3D 2T gain cell at about 0.8 to 1.1 pJ/bit preserves that margin at GB scale.
- LLMET adopts M3D 2T gain cell at 128 MB per layer as its default ultra-large cache and says such M3D memory could scale on-chip capacity to several hundred megabytes (its reference 38; not read).
- LLMET's thermal comment: stacking several SRAM dies (as AMD's 3D V-Cache, which the paper describes as 96 MB by bonding a separate SRAM die) is constrained by heat from dozens-of-micrometre-thick bonded dies, while M3D layers sit inside the few-micrometre back-end-of-line stack.

HBM and DRAM interface energy, other sources:

- RPU (arXiv 2602.18568, MODELLED, validated by the paper against a datasheet-reported figure for HBM3E): HBM3E 3.44 pJ/bit. Its analytical HBM model splits energy into row activation 0.18 pJ/bit (streaming), data movement inside the DRAM die 0.2 pJ/bit per mm (from core-die floorplan routing distances), TSV traversal 0.148 pJ/bit per stacked layer (from 0.8 pF TSV capacitance), and I/O interface 0.25 pJ/bit (from UCIe specs and HBM3E datasheets). The paper's low-capacity design (768 MB, 256 GB/s per stack) reaches 1.45 pJ/bit, 2.4 times lower than HBM3E at the same bandwidth per shoreline mm, and costs about 1.8 times more per GB. RPU is not a measured chip; the 0.2 pJ/bit/mm is an estimate by the authors.
- Note the spread in HBM3E: 5.74 pJ/bit (LLMET, IO included, from its reference) versus 3.44 pJ/bit (RPU, datasheet figure cited by RPU). The two papers do not state the same boundary (whole path with IO versus device). Both are reported; neither is ours. Use 3.44 as a lower reference and 5.74 as an upper reference for HBM3E.
- UCIe-memory paper (arXiv 2510.06513, MODELLED/from the authors' own implementation for the HBM3 value): HBM3 interface 0.9 pJ/b, assumed to hold for HBM4 (the paper itself calls this possibly optimistic given wider fan-out); LPDDR5 2.8 pJ/b, assumed the same for LPDDR6. Compare LLMET's 6.6 pJ/bit for LPDDR5, which is simply set equal to HBM2E in that paper. So LPDDR5 energy per bit has two incompatible values in the sources (2.8 interface versus 6.6 assumed total); the 2.8 is interface only.
- Hybrid-bonded 3D DRAM (arXiv 2604.08044 quoting its reference 71, a published chip result, MEASURED in the cited work, not re-verified by us): memory access energy 0.66 to 0.88 pJ/bit, a 77 to 83 percent reduction versus HBM, with I/O density of 110,000 per mm2 at 3 um pitch, an order of magnitude more bandwidth density than HBM. The same paper cites a chip with 34 Gb/s/1 Gb at 0.88 pJ/b logic-to-memory interface, and another at 0.66 pJ/bit with mini-TSV stacking (titles seen in its reference list; the primary chip papers were not read).
- 3D-Flow (arXiv 2602.11016): inter-tier vertical transfer energy set to 1.35 pJ/byte, i.e. 0.17 pJ/bit (ESTIMATED conversion), described by the authors as a conservative upper bound taken from stacked DRAM analysis; tiers connected with sub-10 um through-silicon vias.
- Reported by Sangam ([2511.12286](https://arxiv.org/abs/2511.12286)): DRAM energy was modelled with the Micron DRAM power calculator and JEDEC IDD currents (activation and read), logic synthesised at 14 nm and scaled to 7 nm; no single per-bit constant was extracted from it for this study.

### 2.3 Gain cell RAM and embedded DRAM (density and retention)

Sources: OpenGCRAM (2602.21278) and GainSight (2504.14866).

- Bitcell area relative to a 6T SRAM cell, from OpenGCRAM layouts in TSMC 40 nm (MEASURED in layout, not silicon): 2T Si-Si gain cell 69 percent of the SRAM cell area; 2T oxide-semiconductor-write, silicon-read gain cell 35 percent. OpenGCRAM also cites previous work giving the OS-Si gain cell 3 times the bitcell density of high-density SRAM at the 5 nm node. GainSight states gain cell and eDRAM provide 2 to 4 times higher density and significantly lower leakage than SRAM, citing five prior works (not read).
- ESTIMATED consequence: from 5.95 MB/mm2 raw SRAM array, a ratio of 1/0.69 gives about 8.6 MB/mm2 and 1/0.35 gives about 17 MB/mm2, if the 40 nm layout ratios transferred to 5 nm (they need not; the 3 times at 5 nm figure is the sourced one for OS-Si, about 17.9 MB/mm2 by the same arithmetic). All raw, excluding periphery.
- Macro level, OpenGCRAM: with peripherals included, dual-port Si-Si gain cell macros become smaller than single-port SRAM above 1 Kb bank size; OS-Si is the smallest across all sizes; advantage grows with bank size as periphery is amortised. A dual-port SRAM needs roughly 2 times the area of single-port (paper's reference 20, not read), and the gain cell is natively dual-port (separate read and write).
- Speed: SRAM has the highest frequency and bandwidth; gain cell frequency is lower because of its single-ended read and the storage-node drop by one threshold voltage on write (Fig. 8, plots; numbers not extracted). Retention: Si-Si gain cell is microseconds, limited by the decay of a stored 1; oxide-semiconductor gain cells reach microseconds to hours depending on design (OpenGCRAM cites ultra-low channel leakage below 1e-18 A/um). GainSight: Si gain cell micro-second scale with SRAM-comparable latency; hybrid gain cell longer retention with an inverse trade-off against write frequency; oxide eDRAM (1T1C) millisecond-scale retention with high density but higher active energy than gain cell because of charge-sharing reads.
- Key GainSight finding (SIMULATED/profiled on GPU and systolic array backends with MLPerf Inference and PolyBench): most AI data in L1 and L2 has lifetimes in the sub-microsecond to microsecond range, so refresh-free operation is possible with short-retention memories, and heterogeneous compositions reach up to 3 times lower active energy and 4 times lower area than uniform SRAM (the text also gives 3.1 times and 4.3 times in one place and 3 times energy and 2.4 times area in another case study). The device library is characterised for TSMC N5, built from published fabricated arrays and post-layout simulation, scaled to 5 nm by the authors.
- Commercial claim (vendor, via OpenGCRAM, UNVERIFIED as independent): 3T gain-cell macros with up to 50 percent area reduction and 10 times power reduction over SRAM, from 180 nm to 5 nm.

Why this matters for L: L's tile memory holds counters and lookup tables. Their lifetime is not microseconds, they are long-lived state that is updated at some rate, so the lifetime argument of GainSight does not transfer directly; refresh and write frequency are the design variables (section 5).

### 2.4 Non-volatile memory

No number is used. UNVERIFIED-SNIPPET: MRAM, ReRAM, PCM, FeFET are described in search results as enabling in-memory processing and as denser than SRAM, and a snippet reports an STT-MRAM global buffer cutting area by 75 percent at iso-accuracy with only 3 percent power saving (from a 2021 study, not read; the primary arXiv id was not verified). GainSight's Table 3 lists accelerators using MRAM (STT-AI Ultra) and RRAM (CHIMERA) as long-term RAM options, which only establishes that they exist, with no density or energy. Open gap: before L designs around NVM, read one survey with measured read energy, write energy, endurance and density per node; this study did not obtain one.

### 2.5 Latency

Sourced latency numbers are sparse and are about links, not arrays:

- UCIe die-to-die: under 2 ns for transmit plus receive, versus about 20 ns for PCIe (chiplets review, 2406.00182, taken from the UCIe consortium material it cites; not read from the specification itself). The UCIe-memory paper models the analog PHY at 0.5 ns each way at a 2 GHz logic clock, 1 ns round trip, and about 2 ns round trip with the adapter at 2 GHz (arXiv 2510.06513, MODELLED).
- CXL 100 to 200 ns (chiplets review, in its Table 2 and a separate statement; UNVERIFIED primary).
- SRAM and gain cell array latency: Fig. 8 of OpenGCRAM plots frequency; no number extracted. DRAM and HBM array latency: no number in any source read. UNVERIFIED gap. For L, latency matters less than bandwidth and energy if lookups are pipelined and independent across tiles; the exact figure must be measured on the chosen memory macro before any timing claim.

## 3. Wires, die-to-die, package and board links

### 3.1 On-chip wires

- The only sourced on-chip wire constant is 0.2 pJ/bit per mm, an estimate inside the RPU HBM model for routing inside a DRAM core die (RPU, 2602.18568; DRAM process, MODELLED, from floorplan distances in its references 35, 47, 54, not read). It is a DRAM-die value and not a logic-process wire; treat it as an order of magnitude only.
- LLMET gives a cleaner way to see the on-chip wire cost: energy per bit rises with SRAM capacity (0.495 to 2.78 pJ/bit from 40 MB to 1 GB at 7 nm) mainly because of longer H-tree routing; that is the wire cost of reaching a bit across a large array.
- 3D-Flow vertical transfer 0.17 pJ/bit (1.35 pJ/byte) for a hybrid-bonded tier crossing at TSMC 16 nm (conservative bound, the authors say).
- Search snippet only (UNVERIFIED-SNIPPET): a tutorial puts moving a bit across a chip at about 600 fJ/bit with no distance given; not used.
- Gap: no fJ/bit/mm for a logic-process metal wire at 5 nm or 7 nm was found in the papers read. For the cost model the wire energy per mm is therefore a parameter, bounded by the 0.2 pJ/bit/mm DRAM-die estimate.

### 3.2 Die-to-die and package links

| Link | Energy | Latency | Bandwidth density | Source and label |
|---|---|---|---|---|
| UCIe, standard package | 0.5 pJ/b | under 2 ns (TX+RX) | 28 to 224 GB/s per mm of shoreline | chiplets review 2406.00182, from consortium material |
| UCIe, advanced package | 0.25 pJ/b | under 2 ns | 165 to 1317 GB/s per mm | same |
| UCIe-A, 55 um bump pitch, 64 lanes | n/a | n/a | 658 GB/s/mm, 416 GB/s/mm2 | UCIe-memory 2510.06513, computed by the authors |
| UCIe-S, x32 doubly stacked at 32 GT/s, 110 um pitch | n/a | n/a | 224 GB/s/mm, 145 GB/s/mm2 | same |
| AIB | 0.85 pJ/b | 3.56 ns | 256 to 1024 GB/s/mm | chiplets review |
| BoW | 0.5 to 1 pJ/b | 5 ns | 1280 | chiplets review (unit as printed in that table) |
| LIPINCON (TSMC, InFO/CoWoS) | 0.56 pJ/bit | n/a | 1.6 Tb/s/mm2 | chiplets review |
| 4 nm NRZ single-ended D2D, 32 Gb/s/wire | 0.44 pJ/bit | n/a | 8 Tb/s/mm | published chip, as described in chiplets review (title seen: "A 4nm 32Gb/s 8Tb/s/mm Die-to-Die Chiplet ..."; primary not read) |
| Modelled 48 Gb/s UCIe-style link, organic, 30 mm reach, TSMC 16 nm | about 0.77 pJ/bit (best-power) | 50 to 120 ps channel range | n/a | CLIPGen 2605.27757, MODELLED, calibrated by the authors to a prototype |
| Same model, 1.2 to 1.4 pJ/bit at 30 mm on 45 nm SOI and 65 nm | | | | CLIPGen |
| Hybrid bonding vertical I/O | 0.66 to 0.88 pJ/bit memory access | n/a | 110,000 I/O per mm2 at 3 um pitch | 2604.08044 citing its ref 71 |

CLIPGen detail on the short-reach package question (TSMC 16 nm, 0.8 V, single 48 Gb/s lane, MODELLED): the silicon-interposer (25 um pitch) and organic (112.64 um pitch) energy curves cross near 10 mm; at 25 mm the organic link is better by more than 2 times (0.41 versus 0.83 pJ/bit at 16 nm; 0.63 versus 1.76 pJ/bit at 65 nm). The pad cost: about 63 fJ/bit for the organic bump versus about 4.5 fJ/bit for the 25 um silicon bump, a fixed roughly 60 fJ/bit penalty for organic. Silicon transmitter energy rises with reach from 0.8 fJ/bit at 2 mm to 28 fJ/bit at 9.5 mm, 234 fJ/bit at 20 mm and over 2 pJ/bit by 42.5 mm because fine-pitch wires are resistive. Lesson: energy per bit across a package is a function of reach, and below a few millimetres the pad capacitance dominates while above ten the wire resistance does.

Off-package and board-level:

- Chiplets review table: CXL 100 to 200 ns latency, QPI latency 100 ns with an energy entry of 10 to 40 pJ/b (the table text was garbled in extraction, so the column alignment is uncertain; treat as UNVERIFIED). The Japanese glossary snippet (UNVERIFIED-SNIPPET) says PCIe 5.0 is several to tens of pJ/bit versus UCIe under 0.5; and a venture-press article says moving from board-level to package-level interconnect is meant to cut energy per bit significantly.
- Best sourced off-package figure: LPDDR5 interface 2.8 pJ/b (UCIe-memory paper, MODELLED/stated) and the LLMET total access 6.6 pJ/bit for LPDDR5 (assumed equal to HBM2E).
- A published 25 Gb/s/pin ground-referenced single-ended link at 1.17 pJ/b appears only as a reference title in CLIPGen's bibliography (not read); a 0.275 pJ/b 42 Gb/s/pin PAM3 transceiver also only as a reference title. Neither is used as a number.

Summary by level (sourced pJ/bit, process as stated; all values are from different papers with different boundaries, so ratios are indicative only):

- Small on-chip SRAM, 7 nm 40 MB: 0.495 (LLMET, MODELLED).
- On-chip very large SRAM, 7 nm 1 GB: 2.78 (LLMET, MODELLED).
- Gain cell, 3 nm, 1 GB: 0.768 (LLMET, MODELLED).
- Vertical hybrid-bond crossing: 0.17 (3D-Flow, conservative) to 0.66 to 0.88 (full 3D DRAM access, cited chip results).
- Package die-to-die: 0.25 to 0.56 for advanced packages (consortium or published chips), 0.5 for standard package.
- HBM3E: 3.44 (RPU) to 5.74 (LLMET, IO included).
- LPDDR5: 2.8 (interface only) to 6.6 (assumed total).
- Board or socket links: tens of pJ/bit, UNVERIFIED.

## 4. 3D stacking options (what the sources say)

- Hybrid-bonded DRAM on logic (arXiv 2604.08044): 110,000 I/O per mm2 at 3 um pitch, order-of-magnitude more bandwidth density than HBM, 0.66 to 0.88 pJ/bit access energy; multi-layer stacking by mini-TSVs gives independent I/O datapaths per die; thermal: stacked DRAM sits on the compute heat source and retention degrades, the paper constrains chip temperature below 85 C (heat-transfer coefficient 10,000 W per m2 K assumed). This is a MODELLED design-space paper with evaluation infrastructure; it is not a silicon result.
- SRAM on logic by hybrid bonding: AMD 3D V-Cache is the commercial precedent, cited in LLMET as 96 MB by bonding a separate SRAM die on the core die. Search snippets (UNVERIFIED-SNIPPET) also quote a 64 MiB 7 nm SRAM die and a tripling of L3 bandwidth to 2 TB/s at unchanged latency. LLMET's point is that stacking multiple SRAM dies is limited by heat and die thickness.
- Monolithic 3D back-end-of-line memory (gain cell with oxide-semiconductor write transistor, or 1T1C oxide eDRAM): cells are built in the metal stack above the logic and periphery, a few micrometres thick, so capacity scales by layers (LLMET default 128 MB per layer, MODELLED). GainSight and OpenGCRAM note SRAM cannot use this trick; the write transistor or capacitor can be stacked on top of silicon, saving area.
- Vertical tier-to-tier datapaths between compute tiers (3D-Flow, 2602.11016): four-tier PE array synthesised at 16 nm, SIMULATED energy; 46 to 93 percent energy reduction and 1.4 to 7.6 times speedup versus 2D and 3D baselines on OPT and QWEN Transformer workloads, by passing data tier to tier without SRAM round trips.
- 2.5D with HBM: HBM needs a dense ring of high-speed I/O at the die edge, so bandwidth scales with the perimeter of the compute die and not its area (RPU), conflicting with reticle-limited dies. UCIe-memory paper claims up to 10 times bandwidth density and up to 3 times lower power with UCIe-attached memory versus HBM4 or LPDDR on-package (the paper's own claim, MODELLED).
- Wafer-scale: RPU says Cerebras-style and Groq-style designs avoid the shoreline limit by using SRAM as main memory, but SRAM density drives up power, cost and infrastructure; it states four WSEs are required to host a 70B model and Groq needs hundreds of processors (claims by the RPU authors, not verified against vendors).

## 5. Cost and capacity per dollar

Sources: Sangam (2511.12286), HBM bit cost (2507.02654), UCIe-memory (2510.06513), RPU (2602.18568), chiplet cost (2206.07308).

- HBM2E at $110 per GB is the assumption used by Sangam (from its reference 61, not read), treated as a conservative lower bound for HBM3. With six 16 GB stacks (94 GB total reported by the paper) the HBM is about $1,760 per stack. The paper's H100-module estimate (ESTIMATED): GPU die about $486 (814 mm2 GH100), interposer about $408, advanced-package assembly $500 at 97 percent yield, total about $12,324 per module, dominated by HBM. Its own Sangam chiplet module estimate is $61.99 with $3.85 per chiplet-on-interposer part.
- HBM costs per bit at least 5 to 10 times more than conventional DRAM, largely from on-die error correction and die-test yield losses (arXiv 2507.02654 abstract and introduction, citing its reference 1). That paper proposes moving error correction to the memory controller with large Reed-Solomon codewords so low-cost stacks without on-die ECC can be used. The UCIe-memory paper independently says HBM is 5 to 10 times more expensive per bit than LPDDR.
- RPU: cost scales with capacity because it scales with silicon area; at low capacity the fixed costs (base die logic, TSV footprint) dominate cost per GB; its 768 MB, 256 GB/s stack costs about 1.8 times more per GB than HBM3E but the module is far cheaper (about 35 times, per the authors) with 5 times better bandwidth per dollar (MODELLED; the paper's claim).
- The chiplet cost paper (2206.07308, analytical model; die cost depends on area and yield; organic interposer, bonding and package are added, 28 nm to 5 nm) is a framework for amortising cost by splitting a large monolithic die into chiplets; its core point for L is that cost rises superlinearly with die area through yield, so a reticle-size die of SRAM is expensive per bit. We did not extract per-mm2 wafer prices from it (figures are in plots); logic wafer cost per mm2 remains an unsourced parameter.
- Search snippets, UNVERIFIED-SNIPPET: Epoch AI estimates B200 HBM3E at $14 to $17 per GB centred on $15; Silicon Analysts lists $200 to $500 per HBM stack. These differ by a factor of about 7 from the $110 per GB paper assumption and cannot be reconciled without reading them; the $110 figure is HBM2E assumed for H100 era with different scope. Use the range as an uncertainty band: HBM cost per GB between roughly $15 and $110 depending on source, date and whether it is BOM or market price.
- No source read gives dollar per GB for on-chip SRAM, gain cell, or monolithic 3D memory. It can only be derived from wafer cost per mm2 (unsourced here) divided by density, so capacity per dollar for SRAM versus HBM is an open parameter and must be calibrated from a foundry quote before use.

## 6. What this means for a counter and lookup tile design

L tile facts the model needs (from the project, not from papers): a tile holds counters and lookup tables with memory inside the tile; a decision is a small number of lookups plus counter updates; no multiplies. The skeleton below uses only the sourced constants above, with unsourced items left as named parameters.

### 6.1 Parameters

Sourced constants (name = value, source, node, label):

- a_bit = 0.021 um2 per 6T bitcell (TSMC 5 nm to 3 nm, GainSight).
- r_si = 0.69, r_os = 0.35: gain cell cell-area over SRAM cell-area (TSMC 40 nm layouts, OpenGCRAM); OS-Si 3 times density at 5 nm is the cited claim.
- e_sram(C): 0.495 pJ/bit at 40 MB and 2.78 at 1 GB (7 nm); 0.917 at 128 MB and 2.42 at 1 GB (3 nm). Interpolation is an assumption (see below).
- e_gc: 0.768 pJ/bit at 1 GB and 0.981 at 4 GB (3 nm); 1.08 at 1 GB (7 nm).
- e_hbm: 3.44 to 5.74 pJ/bit (HBM3E); 6.6 (HBM2E); e_lp5: 2.8 (interface) to 6.6.
- e_wire: at most 0.2 pJ/bit/mm (DRAM-die estimate, RPU); logic wire energy unsourced.
- e_d2d: 0.25 pJ/b (UCIe advanced) to 0.5 (standard); 0.56 (LIPINCON); 0.44 (published 4 nm chip).
- e_vert: 0.17 pJ/bit (3D-Flow, 1.35 pJ/byte, conservative) to 0.66 to 0.88 (3D DRAM access).
- c_hbm: $15 to $110 per GB (range from sources above; wide).
- Reticle limit and chiplet sizing: 858 mm2 reticle figure used in the chiplets review; recommended chiplet 40 to 80 mm2 at 7 nm and 50 to 150 mm2 at 40 nm for microprocessor-type logic, from the chiplets review citing a prior study (not read).

Free parameters (not sourced; must be chosen or measured):

- C_t: tile memory capacity in bytes.
- B: bytes read plus written per decision (lookups times entry size, plus counter updates).
- h: hops (tile to tile messages) per decision; L_hop in mm the distance of one hop; m: bytes carried per hop.
- eta: array efficiency (fraction of tile memory area that is bitcells); A_logic: tile counter/control logic area.
- f_ref: fraction of memory needing refresh and its refresh energy (gain cell and eDRAM only).
- d: number of decisions per second per tile.

### 6.2 Skeleton equations

1. Tile area: A_tile = (8 * C_t * a_bit * r_cell) / eta + A_logic, where r_cell = 1 for 6T SRAM, r_si for Si-Si gain cell, r_os for oxide gain cell or the 5 nm "3 times" claim. Chip capacity per area: capacity per mm2 = 8 * ... inverse of the above. Upper bound on bits per mm2 is 1e6 / (a_bit * r_cell) = 47.6 Mbit/mm2 for SRAM at eta = 1 (ESTIMATED).
2. Memory energy per decision: E_mem = 8 * B * e_mem(C_t), with e_mem taken from the table in 2.2 at the tile's capacity (for tile capacities well under 40 MB the 40 MB value of 0.495 pJ/bit at 7 nm is an upper estimate for a smaller array only if energy rises with capacity as the sources show; smaller arrays should be cheaper, but no source gives a value below 40 MB, so any lower number must be measured).
3. Communication energy per decision: E_net = 8 * h * m * (e_wire * L_hop + e_pad), where the on-die case uses e_wire and the cross-chiplet case replaces the bracket by e_d2d.
4. Total: E_dec = E_mem + E_net + E_logic (E_logic unsourced; for a counting chip L should measure it from its own RTL synthesis).
5. Power: P_tile = d * E_dec + P_leak(C_t) + f_ref * P_refresh. Leakage is the term the sources say separates SRAM from gain cell (orders of magnitude, plot only); no per-bit leakage number was read, so P_leak is a free parameter to be fixed by a macro compiler run.
6. Capacity per chip: N_tiles = floor(A_die_usable / A_tile); chip bytes = N_tiles * C_t. Cost per GB on die = (wafer cost per mm2 / yield(A_die)) * A_die / (chip bytes); wafer cost per mm2 is unsourced here. Compare with c_hbm.
7. Break-even test (LLMET insight 2): a larger on-chip memory pays only if e_mem(C_t) is far below e_hbm; with the sourced numbers, SRAM at 1 GB (2.42 to 2.78 pJ/bit) is already between 0.42 and 0.8 of HBM3E's 5.74 and 0.7 to 0.8 of HBM3E's 3.44, whereas 1 GB of gain cell (0.77 to 1.08) is 0.13 to 0.19 of 5.74 and 0.22 to 0.31 of 3.44 (ESTIMATED ratios).

### 6.3 Worked example (ESTIMATED, B = 64 bytes is a placeholder, not a design number)

For B = 64 bytes = 512 bits per decision, memory energy only:

| Memory | pJ/bit | Energy per decision |
|---|---|---|
| 7 nm 40 MB SRAM | 0.495 | 253 pJ |
| 3 nm 128 MB SRAM | 0.917 | 470 pJ |
| 3 nm 1 GB gain cell | 0.768 | 393 pJ |
| 7 nm 1 GB SRAM | 2.78 | 1.42 nJ |
| HBM3E (RPU figure) | 3.44 | 1.76 nJ |
| HBM3E (LLMET figure) | 5.74 | 2.94 nJ |
| LPDDR5 (interface only) | 2.8 | 1.43 nJ |

One hop of 512 bits across a package at 0.25 to 0.5 pJ/b is 128 to 256 pJ; across 1 mm of die at the DRAM-die upper estimate 0.2 pJ/bit/mm is 102 pJ. So for a 64-byte decision a single die-to-die hop costs about as much as one local lookup in a mid-size SRAM, and a decision that needs several hops can be dominated by the network, not by the array. This is the central design fact: the cost of a decision is roughly (bits fetched) times (energy per bit at the level served), plus bits moved times distance.

Capacity example (ESTIMATED upper bounds): an 800 mm2 die of pure 6T bitcells at 0.021 um2 holds 800 * 5.95 = 4.76 GB of raw array, an unreachable ceiling at eta = 1 and with no logic; gain cell oxide at 35 percent of the area would hold about 13.6 GB by the same arithmetic, still ignoring periphery. Comparison point from the sources: LLMET sizes the useful range of cache for 70B-class model contexts at 256 MB to 1 GB and 2 to 4 GB for a 405B-class model on a B200-like platform (MODELLED); at the edge, the 4-bit quantised model it considers needs about 486 MB.

Interpretation: with the sourced constants, on-die capacity in the multi-gigabyte range is physically plausible only with gain cell or eDRAM and 3D layers; planar SRAM at GB scale loses on both area and energy-per-bit as capacity grows.

## 7. Opportunities for a different design (HYPOTHESES, none tested)

These are labelled HYPOTHESIS: ideas that follow from the sourced numbers and from L's counter-and-lookup character. Each lists what would need to be measured to confirm it.

1. Hierarchical tile memory with a small SRAM front and a large dense gain-cell or eDRAM back, chosen by update rate and lifetime, not by size. GainSight shows that matching device retention to data lifetime gives up to 3 times lower active energy and 4 times lower area than uniform SRAM for GPU and systolic workloads. L's data are different: lookup tables are long-lived and read-mostly, counters are short-lived hot state. HYPOTHESIS: put read-mostly tables in oxide gain cell or oxide eDRAM (long retention, 35 percent cell area, low leakage) and keep only hot counters in SRAM. To test: measure per-row write rate and lifetime distribution of L's real traces with a GainSight-style profiler and compare against retention (microsecond Si gain cell versus ms to hours oxide).
2. Event-driven, sparse access with counters that need no refresh because they are rewritten. A counter that is incremented often refreshes itself on every write; gain cell retention then matters only for rows untouched for longer than the retention time. HYPOTHESIS: a counting chip's write pattern could allow a short-retention cell with refresh-free operation, which would give the density of a gain cell without refresh power. To test: histogram of inter-write intervals per row on our data against the Si-Si (microsecond) and OS-Si (longer) retention values, noting the inverse retention-versus-write-frequency trade-off GainSight reports for hybrid gain cells.
3. Make the tile small and the hop short: keep the decision local so the dominant energy is the array and not the network. With the numbers above, one package-level hop (0.25 to 0.56 pJ/b) rivals a local lookup, and a hop over 10 mm of silicon rises towards a pJ per bit in the CLIPGen model. HYPOTHESIS: a placement in which each decision touches one tile (no multi-hop) and where data crossing tiles is a few bits rather than a bytes-wide payload gives an energy advantage independent of the memory technology. To test: count bytes per hop in L's RTL traces and compute E_net with the equations of section 6.2.
4. Use vertical (3D) distance instead of horizontal: hybrid-bonded or monolithic memory directly over the tile logic gives 0.17 to 0.88 pJ/bit and 110,000 I/O per mm2 in the sources, i.e. effectively a private wide memory port per tile, which is exactly what a memory-inside-the-tile design wants and unlike HBM's perimeter-limited bandwidth. HYPOTHESIS: a tile with a stacked memory layer can use a wide, slow, low-voltage port (many bits per access at low energy) rather than a fast narrow one. To test: floorplan one tile with a gain cell layer above it in a macro compiler that supports it, or approximate using the OpenGCRAM flow in TSMC 40 nm scaled by the ratios in section 2.3, labelling the scaling as assumed.
5. Treat the memory wall as an advantage: because L performs no multiplies, the compute-versus-bandwidth gap in Gholami et al. (3.0 times versus 1.6 times per 2 years) is a gap L does not have to pay on the compute side. HYPOTHESIS: L can use much less die area for logic and spend it on memory, the trade the paper itself recommends ("sacrifice peak compute for better compute/bandwidth"), with the breakeven set by the e_mem(C_t) < e_hbm criterion above.
6. Low-capacity, low-energy DRAM-style stacks: RPU's capacity-reduced HBM variant reaches 1.45 pJ/bit modelled at 1.8 times the cost per GB because most of the HBM energy is wire and TSV, which shrinks with fewer layers and shorter routes. HYPOTHESIS: for a bandwidth-hungry but capacity-modest L deployment, a small close memory could beat large HBM on energy per decision at acceptable cost per GB. To test: apply the cost model of RPU to L's capacity target.
7. Error-correction in the controller rather than in the cell (2507.02654): relaxed raw reliability lowers cost per bit for HBM-class memories; L's tables may tolerate or locally correct errors because counts are statistical. HYPOTHESIS: a counting chip can accept higher raw bit error rates and thereby use cheaper, denser, lower-voltage cells. To test: inject bit errors into a bit-exact simulation of L's inference and measure accuracy loss.

Ranking by expected value (HYPOTHESIS): 1, then 4, then 3.

## 8. Gaps and what to read next

- A survey with measured density, read and write energy, endurance and latency of MRAM, ReRAM, PCM and FeFET per node (the six candidate ids in section 0 were not read).
- Foundry data: macro densities in MB per mm2 for 5 nm and 3 nm including periphery; wafer cost per mm2; this sets the SRAM cost per GB, currently unsourced.
- DRAM and HBM array latency, loaded latency under random access, and refresh power: not found in any paper read.
- A logic-process wire energy per mm at 5 nm to 7 nm.
- The UCIe specification for the 0.25 and 0.5 pJ/b targets (read here only via the review and the memory paper).
- Primary chip papers behind the 0.66 and 0.88 pJ/bit hybrid-bonded DRAM results and the 0.44 pJ/bit 4 nm die-to-die link.

Related: [Paper notes index](INDEX.md), [Memory at scale synthesis](../memory_at_scale_synthesis.md)
