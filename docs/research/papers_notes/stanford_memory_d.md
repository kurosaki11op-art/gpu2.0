---
title: Paper notes - memory-centric and in-memory accelerators (Stanford hardware groups)
tags: [l, research, papers, memory, energy]
---

# Paper notes - memory-centric and in-memory accelerators (Stanford hardware groups)

Purpose: the L chip (counting tables, clause lists, event-driven sparse row lookups, counters; no matrix products, no
multiplies) must scale to more classes, words and tasks while staying competitive with GPUs and custom AI chips on
energy and area. This note reads four papers from Stanford hardware or systems groups in full and extracts what each
says about memory organisation, with numbers, the operations each one needs (and which of those L's rules forbid), and
one concrete way L's memory could use the idea.

Labels used below: MEASURED (paper reports a silicon or real-machine measurement), SIMULATED (paper's cycle-level or
circuit simulation), SYNTHESIS (paper's post-synthesis area or power), ESTIMATED / PROJECTED (paper's own projection),
MODELLED (my own arithmetic for L, never a paper number). Every number in a "Paper numbers" block is from the PDF I
read; every number in an "L cost model" block is my own arithmetic from stated assumptions and is MODELLED/ESTIMATED.

## Access log and what could not be fetched

All PDFs came from `https://arxiv.org/pdf/<id>` through the proxy and were converted with `pdftotext`. I read the full
text of each paper (the SCNN layout text end to end; the other three from the squeezed text including captions; a few
numeric tables were only reachable as flattened text, noted where it matters).

| arXiv id | Title | Group | Fetched | Read |
|---|---|---|---|---|
| 1708.04485 | SCNN: An Accelerator for Compressed-sparse Convolutional Neural Networks | Dally (Stanford/NVIDIA/MIT), ISCA 2017 | yes | in full |
| 2104.12760 | Capstan: A Vector RDA for Sparsity | Olukotun (Stanford), MICRO 2021 | yes (v2, Sep 2021) | in full |
| 1811.09557 | Hyperdimensional Computing Nanosystem | Wong, Mitra, Rabaey, Shulaker, Rahimi | yes | in full |
| 1510.00149 | Deep Compression: Compressing Deep Neural Networks with Pruning, Trained Quantization and Huffman Coding | Han, Mao, Dally (ICLR 2016) | yes | in full (appendix timing tables only skimmed) |

Not available on arXiv, so not read (marked UNVERIFIED for any claim about them): Plasticine (ISCA 2017, Olukotun group;
the search found only the Stanford/Kozyrakis pages, no arXiv listing); the N3XT monolithic-3D papers (Wong/Mitra) as
standalone arXiv items (I did not find a verified id, so I did not guess one); the JSSC and ISSCC versions of the
CNFET/RRAM hyperdimensional chip (the arXiv chapter is the version I read). EIE is cited by SCNN and Capstan but I did
not read it here (an earlier note covers EIE if present in this folder; UNVERIFIED in this file).

Caveat on the HD paper: it is a book chapter. Its abstract states 420x energy and 25x area for monolithic-3D versus
silicon CMOS, but the body I read never derives those two numbers (a text search finds them only in the abstract), so
they are PROJECTED and UNVERIFIED as to method.

---

## 1. SCNN (arXiv 1708.04485, Dally and co-authors)

### Mechanism, exactly

SCNN is an inference accelerator for convolutional layers that never multiplies by a zero and keeps both weights and
activations compressed in the buffers, not only in DRAM. The dataflow is PlanarTiled-InputStationary-CartesianProduct-
sparse (PT-IS-CP-sparse).

1. The activation plane (W x H) is split into Wt x Ht tiles, one tile per processing element (PE) across all C input
   channels. Weights are broadcast to all PEs. Halo values at tile borders are handled by output halos: partial sums at
   the border are exchanged with neighbours at the end of each output-channel group.
2. Weights are grouped into compressed blocks of Kc x R x S (an output-channel group); input activations are compressed
   per channel in blocks of Wt x Ht. Format is run-length: a 4-bit index per element gives the number of zeros before it
   (up to 15; longer gaps use a zero placeholder). Each 16-bit value carries a 10-bit overhead for coordinates in the
   weight FIFO and activation RAMs, as the paper states.
3. Each cycle a PE fetches a vector of F=4 non-zero weights and I=4 non-zero activations and multiplies the full
   Cartesian product (16 products). Every product is useful, because only non-zeros are fetched.
4. Output coordinates come from the stored indices, not from loop counters. The 16 products are scattered through a
   16x32 arbitrated crossbar to A=32 accumulator banks (A = 2 x F x I to reduce bank contention). The accumulator
   buffer must be dense, since any output position may be hit. Banks are double-buffered; a post-processing unit (PPU)
   applies ReLU, pooling, halo exchange and re-compresses the output into the output activation RAM (OARAM).
5. Activations stay in the on-chip IARAM/OARAM between layers (the two are swapped), so they never touch DRAM unless the
   layer is too large (tiling then adds DRAM traffic).

### Memory organisation, capacity, bandwidth, energy, area

Paper numbers (SYNTHESIS, TSMC 16 nm FinFET with Catapult HLS and Design Compiler; performance from a cycle-level
simulator and the TimeLoop analytic model, so SIMULATED):

| Item | Value |
|---|---|
| PEs / multipliers | 64 PEs, 4x4 = 16 multipliers each, 1,024 total, 16-bit multiply, 24-bit accumulate |
| IARAM and OARAM | 10 KB each per PE; 1 MB of activation data plus 0.2 MB of indices in total |
| Weight FIFO | 50 entries (500 B) per PE |
| Accumulator buffers | 32 banks x 32 entries per PE, 6 KB |
| Clock / peak | slightly above 1 GHz, 2 Tera-ops (16-bit multiplies plus 24-bit adds) |
| PE area | 0.123 mm2: IARAM+OARAM 0.031, weight FIFO 0.004, multiplier array 0.008, scatter crossbar 0.026, accumulators 0.036, other 0.019 |
| Accelerator area | 7.9 mm2 (SCNN) vs 5.9 mm2 for the dense baselines DCNN and DCNN-opt (2 MB SRAM, same 1,024 multipliers) |
| Memory share of PE area | 57 percent (IARAM, OARAM, accumulators); multiplier array only 6 percent; IARAM+OARAM alone 25 percent |

The paper gives no per-access pJ table of its own; energy is reported relatively (see results). The only absolute energy
statement in the neighbouring Deep Compression paper is the 45 nm table used below.

### Application results

- Network sparsity (MEASURED on pruned Caffe models): weight density as low as 30 percent in some GoogLeNet layers;
  activation density as low as 30 percent; typical layers can cut multiplies by 4x, up to 10x. 50 to 70 percent of
  activations are zero after ReLU.
- Table I network sizes (two-byte data): AlexNet 5 conv layers, max layer weights 1.73 MB, max layer activations 0.31 MB,
  0.69 B multiplies; GoogLeNet 54 layers, 1.32 MB, 1.52 MB, 1.1 B; VGGNet 13 layers, 4.49 MB, 6.12 MB, 15.3 B.
- Network-wide speedup over the dense DCNN (SIMULATED): AlexNet 2.37x, GoogLeNet 2.19x, VGGNet 3.52x, average 2.7x.
- Energy versus DCNN (SIMULATED): DCNN-opt (zero gating plus DRAM compression) is 2.0x better; SCNN averages 2.3x; per
  layer between 0.89x and 4.7x versus DCNN and 0.76x to 1.9x versus DCNN-opt.
- Density sweep on GoogLeNet: at 100 percent density SCNN reaches about 79 percent of DCNN performance; it crosses DCNN
  at about 85 percent weight/activation density for performance, 83 percent for energy versus DCNN and about 60 percent
  versus DCNN-opt; at 10 percent weight and activation density it is 24x faster.
- Fragmentation: in the last two GoogLeNet inception blocks average multiplier utilisation falls below 20 percent;
  64 PEs beat 4 PEs by 11 percent (59 percent versus 35 percent multiplier use).
- Larger networks: only 9 of 72 layers needed DRAM tiling; their energy penalty was 5 to 62 percent, mean 18 percent.

### Operations needed versus L's rules

Conflict: 1,024 16-bit multipliers and the Cartesian-product convolution, which is a (sparse) tensor contraction; the
24-bit adder array is fine. Backprop is only used offline for pruning. No conflict: run-length-coded sparse storage,
index arithmetic, the banked scatter-accumulate network (it is a read-add-write counter update), the double-buffered
accumulator, ReLU-style thresholding, re-compression of outputs.

### Limitations

Meant for conv layers; the multiplier array is underused when layers are small or dense; an input layer with 100
percent activation density is a loss; the accumulator must stay dense; the crossbar plus accumulators make SCNN 34
percent larger than the dense design; global barriers between output-channel groups cost cycles.

### One concrete use for L

Idea: keep the table compressed all the way to the point of use, and pick the compressed format by break-even density.
SCNN shows that sparse storage with an index only pays below about 85 percent density, but pays enormously if it makes
the whole working set fit in SRAM (only 9 of 72 layers spilled).

L cost model (MODELLED; assumptions are mine): a counter table with 2^20 context rows x 16 classes x 8-bit counters is
16 MiB dense. If only 5 percent of the 16,777,216 counters are non-zero (838,861 entries), a run-length format with a
4-bit gap and an 8-bit counter costs 12 bits per entry, about 1.26 MB (13x smaller), before the extra zero placeholders
for long gaps (SCNN reports them as negligible; for L unmeasured). Using SCNN's rule that memories are about 57 percent
of area, the saving converts to area only if the SRAM macro is actually shrunk; if the 16 MiB still sits off-chip, the
saving converts to DRAM traffic instead (see section 4 for the energy ratio).

---

## 2. Capstan (arXiv 2104.12760, Olukotun group)

### Mechanism, exactly

Capstan is a reconfigurable dataflow accelerator (RDA) that extends the dense Plasticine design with hardware for sparse
iteration and sparse memory access. It is programmed in a dialect of Spatial with parallel patterns (Foreach, Reduce,
plus a Scan construct that iterates over a sparse structure).

Three mechanisms matter for memory:

1. Sparse memory units (SpMUs) with a request allocator. Sparse programs issue 16 addresses per cycle (one per SIMD
   lane) at random banks. A plain arbitrated memory serves one conflicting group per cycle. Capstan buffers d request
   vectors in an issue queue and, each cycle, a three-iteration input-first separable allocator (lanes pick a bank, then
   banks pick a lane; older requests get priority in the early rounds) chooses a conflict-free set of up to one request per
   lane and per bank. Each granted request runs in its own read-modify-write pipeline attached to one SRAM bank, with an
   arithmetic unit that supports integer and floating add and subtract, bitwise ops, test-and-set, write-if-zero, swap,
   min-report-changed, and max. Bank index is hashed (a0:3 xor a4:7 xor a8:11 xor a12:15) so any power-of-two stride
   spreads across banks. Crossbar size stays 16x16 whatever the queue depth. Ordering modes: unordered, address-ordered
   (a 128-entry Bloom filter detects same-address in-flight requests), and fully ordered. Duplicate read-only accesses are
   squashed in the queue.
2. Scanners for sparse iteration. A bit-vector scanner intersects or unions two bit-vectors, finds the first 16 set bits
   per cycle, and emits both the dense index and the indices into each compressed value array, using prefix sums. A
   256-input, 16-output scanner is the chosen design point. A two-level bit-tree encodes 262,144 positions with 512 bits
   of top level and handles very sparse data (below 1 percent density).
3. Shuffle networks (butterfly merge units, each moves entries by at most one lane, 48-bit by 64-entry inverse-permutation
   FIFO) so a vector of requests can reach the right memory tile, plus read-only compressed-DRAM bursts (base/offset
   header byte) and atomic DRAM read-modify-write in the address generators.

### Memory organisation, capacity, bandwidth, energy, area

Paper numbers (SYNTHESIS with FreePDK 15 nm at 1.6 GHz; SRAM area scaled from a 28 nm industrial compiler; performance
from a cycle-accurate simulator with Ramulator, so SIMULATED):

| Item | Value |
|---|---|
| Grid | 20x20 checkerboard: 200 compute units, 200 SpMUs (memory units), 80 DRAM address generators |
| SpMU | 16 banks x 4096 32-bit words = 256 KiB each, one read and one write port per bank; 50 MiB on chip in total |
| Lanes | 16 per compute unit, 6 vector stages, 32-bit fixed or floating point |
| Off-chip | DDR4-2133 68 GB/s, HBM2 900 GB/s, HBM2E 1,800 GB/s |
| Bank utilisation | arbitrated baseline 32 percent of banks active per cycle; depth 16 with 3 priorities reaches 79.9 percent; depth 32 with a 32x16 crossbar reaches 92.5 percent |
| Scheduler area (Table 4) | 38,052 um2 (depth 8, 16x16) to 90,433 um2 (depth 32, 32x16); chosen: depth 16, 16x16, 51,359 um2 |
| Scanner | the 256x16 choice uses 54 percent less area than a 512x16 one |
| Chip area | Plasticine 158.6 mm2, Capstan 184.5 mm2 (+16 percent); V100 for comparison 815 mm2 |
| Design power | Plasticine 155 W, Capstan 174 W (+12 percent) |
| Added units | Allocator 0.8 percent of area, scanner 4.7 percent in the compute unit, DRAM AG functional units 13.8 percent and decompressor 6.0 percent of AG area, shuffle networks 6.4 mm2 |

No pJ-per-access numbers are given; energy is argued from power and runtime ("with Capstan's speedup this would yield
much lower energy").

### Application results

- Baselines: 4-socket Xeon E7-8890 v3 with TACO and GraphIt on 128 threads; V100 with cuSparse and Gunrock.
- Abstract (v2): Capstan with DDR4 is 18x faster than the CPU, with HBM2 16x faster than the V100, and 7.6x to 365x
  faster than Plasticine on the applications that Plasticine can run, for 16 percent more area.
- Per-application ranges in the text: 4.4x to 327x over the CPU, 4.9x to 118x over the V100.
- ASIC comparison (Table 13, speedup at 1.6 GHz and at 1 GHz): EIE 0.53x and 0.40x (Capstan slower because EIE holds
  all weights in on-chip SRAM and Capstan streams them from HBM), SCNN 1.40x and 0.87x, Graphicionado BFS 2.10x and
  2.06x. Capstan peaks at 128 elements per cycle, 16x MatRaptor.
- Memory sensitivity: an arbitrated memory would make Capstan 27 percent slower on average and up to 90 percent slower on
  some kernels; the allocator gives 15 percent average and 39 percent peak speedup over a weak allocator and sits within 8
  percent of an ideal conflict-free SpMU. Ordering costs: address-ordered runs 1.11x to 1.68x slower, fully ordered 1.15x
  to 4.18x slower (COO). Dropping the one-lane shuffle shift costs up to 15 percent on convolution.
- Convolution on a ResNet-50 pruned to 30 percent density; CSC SpMV with a 30 percent dense input (as in EIE tests).
- Memory-bound note: SpMV and PageRank remain memory-bound even at 900 GB/s HBM2; BFS and SSSP still gain up to 500 GB/s.

### Operations needed versus L's rules

Conflict: the compute units are SIMD floating-point pipelines doing multiply-accumulate (CSR SpMV, convolution, SpMSpM,
BiCGStab), and the whole model is sparse tensor algebra, which is matrix-ish by definition. No conflict: the SpMU
read-modify-write unit (add, min, max, test-and-set, write-if-zero), the bank hash, the allocator, bit-vector and
bit-tree scans, intersection and union of index sets, shuffle networks, compressed-pointer DRAM bursts. For a
matrix-free chip the SpMU plus scanner subset is attractive on its own; the compute-unit pipelines would be dropped.

### Limitations

A general-purpose design: 184.5 mm2 and 174 W is far larger than a dedicated lookup engine; SRAM is only 50 MiB so large
models stream from HBM (the stated reason it loses to EIE); compression is read-only and tile-aligned; convolution maps
poorly to the positional dataflow (3.8x gain from a non-positional mode); area is scaled from a different node for SRAM;
no absolute energy per access is given.

### One concrete use for L

Idea: give L's counter table a request allocator and a hashed bank map rather than an arbitrated memory. L's workload is
exactly Capstan's random-access case: each token event touches a few rows, and updates (counter increments, if the chip
is ever allowed to learn online) are read-modify-writes.

L cost model (MODELLED): assume a 16-bank counter SRAM serving 16 event lookups per cycle. With the paper's measured
bank utilisation, an arbitrated memory delivers about 32 percent of 16 accesses per cycle (about 5 per cycle); an
allocated depth-16 queue delivers 80 percent (about 12.8 per cycle), 2.5x the throughput, for 51,359 um2 of scheduler
(synthesis at 15 nm; scale to the L node separately). That is cheaper than doubling the bank count, which doubles SRAM
macros. For the clause list: store each literal's posting list as a two-level bit-tree (512-bit top, 512-bit leaves), so
a literal with k occupied leaf blocks costs 64 B for the top plus 64 B per leaf; intersecting two literals' postings is
then a word-wise AND per level, giving a clause-satisfaction check with no comparisons and no multiplies. With 100,000
clauses (my assumption) the top level has at most 196 set bits of 512.

---

## 3. Hyperdimensional Computing Nanosystem (arXiv 1811.09557, Wong, Mitra et al.)

### Mechanism, exactly

A book-chapter-length account of a hyperdimensional (HD) computing system built from carbon-nanotube FETs (CNFETs) and
resistive RAM (RRAM), monolithically integrated in 3D, with experimental demonstrations and projections.

HD computing, as the paper defines it: information lives in D-bit random hypervectors (D = 10,000). Operations are
Multiply-Add-Permute (MAP): multiplication is component-wise XOR (binding), addition is component-wise majority
(bundling; implemented by D counters, one per component, then a threshold at k/2), permutation is a fixed rotation.
Similarity is Hamming distance. A clean-up (item) memory returns the stored hypervector most similar to a noisy one; with
10,000 bits, a third of the bits can flip and the original is still recovered.

Language-recognition case study (21 European languages): 27 letter hypervectors from an item memory; a trigram vector is
rho(rho(A)) xor rho(B) xor C; all trigram vectors of a text are bundled into a text hypervector; during training it is
stored as the language hypervector, during testing it is the query. The associative memory computes the Hamming distance
from the query to all 21 stored vectors in parallel and returns the minimum. A conventional baseline would count 27^3 =
19,683 trigram frequencies; HD stays at 10,000 bits even for 5-grams (27^5 = 14,348,907 possible).

Hardware ideas:

1. In-memory MAP kernels in 3D vertical RRAM (VRRAM, vertical 1T-4R pillars): XOR is a one-time-programmed look-up table
   read through the pillar address (no rewrite); addition uses analogue current summing along a shared pillar; permutation
   moves bits along pillars with VDD/GND pulses. Measured: 4-layer devices; up to 10^12 XOR evaluation cycles and 10^11
   addition cycles without disturb errors.
2. Randomness for free: RRAM stochastic set (50 percent probability) and CNFET variations (CNT count, threshold voltage)
   generate the seed hypervectors; the item memory is a set of time-encoded delay cells with coincidence detectors.
3. Approximate incrementer using RRAM gradual reset: 8 transistors and one RRAM cell, versus about 240 transistors for a
   digital 7-bit incrementer (so 30x fewer), replacing the D=10,000 accumulators.
4. Associative memory as ternary content-addressable memory built from 2 CNFETs and 2 RRAMs per cell; matchline current
   summed; training writes the query into the RRAM at 3 V, inference reads at about 0.5 V; the line with most current wins.

### Memory organisation, capacity, bandwidth, energy, area

Paper numbers (labels as the paper states them):

| Item | Value | Label |
|---|---|---|
| Hypervector | 10,000 bits; 21 stored class vectors = 210,000 bits in the associative memory (my arithmetic from the paper's sizes) | design |
| Item memory | 27 letter vectors, constant look-up table | design |
| RRAM device | at most 2 V set/reset, about 10 ns pulses, HRS/LRS ratio 10 to 100; measured LRS about 10 kOhm, HRS 400 kOhm to 1 MOhm; 10-year retention | cited |
| RRAM endurance | 10^12 cycles per cell, 10^5 to 10^7 at array level | cited |
| RRAM array scale | up to 16 Gbit 1T-1R arrays have been demonstrated (cited) | cited |
| Monolithic 3D | inter-layer vias at metal pitch (100 nm at 28 nm node) versus 10 um for TSVs; tiers fabricated at 200 C maximum for the CNFET/RRAM demonstrations | MEASURED |
| Circuit energy | 3x lower dynamic energy (variation-based circuits vs silicon at same node); 19x lower energy for 2T2R TCAM versus SRAM TCAM (reduced leakage) | ESTIMATED / SIMULATED |
| System | up to 35x energy-execution-time product benefit versus silicon CMOS; at 28 nm 7.6x lower energy and 4.6x faster | ESTIMATED / SIMULATED |
| Headline | up to 420x energy efficiency and 25x less area versus silicon CMOS | PROJECTED, method not shown in the chapter |
| Endurance simulation | Figure 5 shows recognition accuracy versus endurance limit for 2 kb to 10 kb vectors; robustness holds but "more realistic endurance modelling is future work" | SIMULATED |

### Application results

- Table 1 (HD versus baseline accuracy): language recognition 21 classes 96.7 percent vs 97.9; text categorisation 8
  classes 94.2 vs 86.4; speech 26 classes 95.3 vs 93.6; EMG gesture 5 classes 97.8 vs 89.7; flexible EMG 96.6 vs 88.9; EEG
  74.5 vs 69.5; ECoG seizure 95.4 vs 94.3.
- Chip (MEASURED): pairwise classification of 21 languages with mean accuracy up to 98 percent on more than 20,000
  sentences (6.4 million characters), one training text (about 100,000 characters) per language, 98 percent accuracy
  preserved with 78 percent of hardware outputs stuck at 0 or 1.
- Random indexing comparison: an SVD-based LSA needs memory proportional to vocabulary times documents; random indexing
  needs memory proportional to vocabulary, using 8,000-dimensional vectors for 54,000 words from 37,000 documents.

### Operations needed versus L's rules

Conflict: none strictly (XOR, majority, rotation, Hamming distance, counters). Permutation is said in the paper to be
"multiplication by a matrix" in general, but the fixed rotation used is a wiring permutation, not a matrix product. Item
memory and class memory are table lookups; the encoder is counters plus a threshold. One caution: the associative
search is a full-width comparison against every class vector (class count x D bit-reads per query), which is the
opposite of event-driven sparse access; it is cheap only because it is done inside the memory array.

### Limitations

Nanotechnology (CNFET, RRAM, monolithic 3D) is lab-scale and not a standard CMOS process; the 420x/25x claims are
projections without derivation in the chapter; RRAM endurance is limited, so heavy online counting is risky; the digital
design compares one component per clock (O(D) cycles per Hamming distance), while the nanosystem relies on analogue
current summing, whose precision and variation limit the number of classes per matchline; the experimental task is
small (21 classes).

### One concrete use for L

Idea: place the class-score accumulation inside the memory array, using the TCAM or matchline-sum trick: read L's
per-class counters by driving the activated rows and summing along a column or matchline, rather than moving counters to
an adder. And use non-volatile cells for read-mostly tables (the counters are trained on a GPU and only read on chip),
so endurance is no problem.

L cost model (MODELLED): a table with 16 classes and 2^20 context rows needs 16 bit-columns per row at 1-bit presence
(2^20 x 16 bits = 2 MiB), or 8 columns of 3-bit quantised counters if multibit cells are used. The only paper-grounded
energy ratio is 19x for a 2T2R TCAM cell versus an SRAM TCAM cell (SIMULATED, leakage-driven). If an on-chip SRAM
lookup array costs E per query, a non-volatile array at the paper's ratio would cost E/19 at best for the leakage part;
dynamic read energy is not given and I will not invent it. The 30x transistor saving of the approximate incrementer
(8 versus 240 transistors) matters only if L's counters are updated on chip.

---

## 4. Deep Compression (arXiv 1510.00149, Han, Mao, Dally)

### Mechanism, exactly

A three-stage pipeline to reduce the storage of a trained network so that it fits on-chip SRAM:

1. Pruning: train normally, remove connections below a magnitude threshold, retrain the survivors. Result 9x (AlexNet)
   and 13x (VGG-16) fewer parameters.
2. Trained quantization and weight sharing: per layer, 1-D k-means clustering of the surviving weights into k centroids
   (linear initialisation across [min, max] is best, because it keeps the few large weights; Forgy and density-based
   initialisations lose them). Each connection stores a log2(k)-bit index into the layer's shared-weight table. The
   centroids are fine-tuned during retraining by summing the gradients of all weights that share an index. AlexNet:
   256 centroids (8 bits) in conv layers, 32 centroids (5 bits) in fully connected layers.
3. Huffman coding of the weight indices and of the sparse index gaps, saving a further 20 to 30 percent (22 percent on
   AlexNet) since both distributions are biased.

The sparse structure is stored as CSC/CSR with relative (difference) indices of 8 bits for conv layers and 5 bits for
fully connected layers (4 bits in the AlexNet table), padding with a filler zero when a gap exceeds the field, so that
the meta-data overhead is smaller than the standard 2a+n+1 numbers.

### Memory organisation, capacity, bandwidth, energy, area

Paper numbers:

| Item | Value | Label |
|---|---|---|
| 45 nm energy per 32-bit operation | float add 0.9 pJ; SRAM access 5 pJ; DRAM access 640 pJ (about 3 orders over an add) | cited from prior work |
| DRAM power for a 1 billion-connection net at 20 fps | 20 Hz x 1 G x 640 pJ = 12.8 W | arithmetic in paper |
| Storage after compression | LeNet-300-100 1070 KB to 27 KB (40x); LeNet-5 1720 KB to 44 KB (39x); AlexNet 240 MB to 6.9 MB (35x); VGG-16 552 MB to 11.3 MB (49x) | MEASURED |
| Storage composition | weights and sparse indices each about 5 bits on average, so about half and half; codebook overhead negligible | MEASURED |
| AlexNet pipeline | pruning to 11 percent (9x), then 3.7 percent (27x) with quantization, then 2.88 percent (35x) with Huffman | MEASURED |
| VGG-16 pipeline | 7.5 percent (13x), 3.2 percent (31x), 2.05 percent (49x) | MEASURED |
| LeNet-300-100 / LeNet-5 | 3.1 percent (32x) to 2.49 percent (40x) / 3.05 percent (33x) to 2.55 percent (39x) | MEASURED |

The paper compares weight storage only; it gives no chip area figures. It states that the quantized sparse form could not
be benchmarked on CPU and GPU because the vendor sparse libraries do not support an indirect weight-table lookup or
relative indexing, and recommends a custom ASIC, which became EIE.

### Application results

- Accuracy (Table 1, MEASURED): LeNet-300-100 error 1.64 percent reference, 1.58 percent compressed; LeNet-5 0.80
  versus 0.74; AlexNet top-1 42.78 versus 42.78 and top-5 19.73 versus 19.70; VGG-16 top-1 31.50 versus 31.17 and top-5
  11.32 versus 10.91. No loss.
- Bit-width sweep (Table 6, AlexNet conv bits / fc bits): 8/5 bits gives top-1 42.78 and top-5 19.70 (no loss); 8/4 bits
  gives 42.79 and 19.73 (0.01 percent loss); 4/2 bits gives 44.77 and 22.33 (1.99 and 2.60 percent loss).
- Pruning and quantization combined: a network can be compressed to 3 percent of its size without loss, but pruning alone
  or quantization alone begins to lose accuracy below about 8 percent of the original size.
- Speed and energy on dense versus pruned fully connected layers, batch 1 (MEASURED): pruned layers run 3x on CPU, 3.5x on
  GPU, 4.2x on mobile GPU on average; energy 7x lower on CPU, 3.3x on GPU, 4.2x on mobile GPU (Figures 9 and 10). With
  batching the benefit disappears (appendix timing tables, only skimmed).
- Comparison (Table 7): other methods compress AlexNet by at most about 4x to 24x with loss; this work 35x without.

### Operations needed versus L's rules

Conflict: the network being compressed is a dense or sparse matrix-vector product with multiplies, and the k-means and
fine-tuning use backprop. Those are on the training (GPU) side, which L's rule allows. For the chip: the stored form
(relative index, small codebook index, Huffman code) needs only table lookups, an add for the running index, and a
prefix decode; the multiply by the weight is the part L does not have, because L's table entries are counts, not
weights.

### Limitations

Network-specific retraining is needed (fine-tuning on the GPU); Huffman decode is variable-length and awkward for
parallel hardware (the ASIC follow-up avoids it); conv layers need more bits than fully connected ones (accuracy drops
below 4 bits); benefits for batch-sized work are small because matrix-matrix multiplies already reuse data;
sparse-library support is missing in off-the-shelf software.

### One concrete use for L

Idea: compress L's counter table with the same three steps: prune to the non-zero counters, replace counters with a 4 to
5-bit index into a small per-table codebook (a shared-value table, in the paper's sense), and store relative gaps of 4
bits.

L cost model (MODELLED, reusing the 2^20 x 16 x 8-bit, 5 percent non-zero table from section 1): 838,861 entries; with a
4-bit gap and a 4-bit codebook index (16 shared counter levels, an assumption; Deep Compression used 16 levels only
under 8/4-bit AlexNet, where loss was 0.01 percent, and L's tolerance for counter quantisation is UNMEASURED) each entry
costs 8 bits, so 0.84 MB, 20x smaller than the 16 MiB dense table. Using the 45 nm numbers (SRAM 5 pJ and DRAM 640 pJ per
32-bit access): a row lookup that returns about one 32-bit word costs 5 pJ if the 0.84 MB table fits on chip and 640 pJ if
the 16 MiB table lives in DRAM, a 128x difference. For one lookup per token and a million tokens per second, that is 5 uW
versus 640 uW for the table access alone (arithmetic, not a measurement). The point carries over to any scale-up: the
first-order energy rule is whether the table fits on chip.

---

## Cross-paper comparison

| Aspect | SCNN | Capstan | HD nanosystem | Deep Compression |
|---|---|---|---|---|
| What it stores | compressed activations and weights | sparse tensors in banked SRAM plus HBM | hypervectors, class memory | quantized sparse weights |
| Compression | run-length, 4-bit gap | CSR/CSC/COO, bit-vector, bit-tree, delta-coded DRAM bursts | none (dense random bits) | prune + codebook + Huffman |
| On-chip capacity | 1 MB activations plus 0.2 MB indices; 7.9 mm2 | 50 MiB; 184.5 mm2 | 210 kb class memory for the 21-class task | n/a (software); targets SRAM |
| Key memory trick | scatter-accumulate banks | request allocator, 32 to 80 percent bank use | compute inside the array | codebook indirection |
| Needs multiplies | yes (16-bit) | yes (FPU lanes) | no | yes (inference weights) |
| Evidence level | synthesis plus simulation | synthesis plus simulation | silicon (accuracy), projections (energy, area) | measured accuracy and size |

## What matters for L (summary, my judgement)

1. Fit the table on chip. The 128x ratio between a DRAM and an SRAM access at 45 nm, together with the 35x to 49x
   measured compression of Deep Compression and SCNN's observation that 57 percent of its area is memory, says the first
   design variable is bits per table entry and entries kept. Prune to non-zero counters, use a small shared-value
   codebook, and a 4-bit relative index.
2. Do not use an arbitrated memory for random lookups. Capstan's allocator raised bank use from 32 to 80 percent for
   51,359 um2 at a 16x16 crossbar and 0.8 percent of chip area. Hash the bank index so strided keys spread.
3. Use bit-vector or bit-tree index sets for the clause list. A 256-bit scan per cycle and a 512-bit top level covering
   262,144 positions turn clause intersection into word-wise AND, with no multiplies.
4. Put the class-sum inside the array and keep read-mostly tables in non-volatile cells (HD nanosystem). The only
   verified ratio is 19x (simulated) for TCAM cell energy; 420x and 25x are unverified projections and should not go in
   L planning documents without the underlying paper.
5. Counters that the chip never rewrites (inference on the chip, training on a GPU) sidestep the RRAM endurance limit
   (10^5 to 10^7 array-level writes) that the HD paper flags.

## Open questions

- How many bits per counter does L need? The 8/5 and 8/4 AlexNet results do not transfer; measure L's accuracy versus
  codebook size.
- What is the real density of L's counter table at the target number of classes and words?
- Is a Hamming-style full associative search ever cheaper than an event-driven sparse row lookup for L? The HD paper
  does the full search; L's design is the opposite.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md).
