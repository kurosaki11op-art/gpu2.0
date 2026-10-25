---
title: Paper notes - compressed and sparse inference hardware (Stanford and MIT)
tags: [l, research, papers, memory, energy]
---

# Paper notes: compressed and sparse inference hardware (Stanford and MIT)

Purpose: the founder asked how L should manage MEMORY as the system scales (more classes, words, tasks) while keeping
accuracy and low power. Four papers were read from the arXiv PDFs (text extracted with pdftotext; ids verified from the
PDF headers):

1. EIE: Efficient Inference Engine on Compressed Deep Neural Network, Han, Liu, Mao, Pu, Pedram, Horowitz, Dally
   (Stanford and NVIDIA), arXiv 1602.01528v2, ISCA 2016.
2. Deep Compression: Compressing Deep Neural Networks with Pruning, Trained Quantization and Huffman Coding, Han, Mao,
   Dally, arXiv 1510.00149v5, ICLR 2016.
3. Learning both Weights and Connections for Efficient Neural Networks, Han, Pool, Tran, Dally, arXiv 1506.02626v3,
   NeurIPS 2015.
4. Efficient Processing of Deep Neural Networks: A Tutorial and Survey, Sze, Chen, Yang, Emer (MIT, not Stanford),
   arXiv 1703.09039v2, Proc. IEEE 2017.

Labels: every number below is quoted from the paper and is therefore the paper's own MEASURED, SIMULATED or ESTIMATED
value as stated; the label is given where the paper says how it was obtained. Numbers marked "L-ESTIMATED" are
this note's own cost-model numbers and are not from any paper. Reading coverage: papers 1, 2, 3 were read completely
(text, all tables, appendix of paper 2; figures only through captions and extracted axis text). Paper 4 (about 28k
words) was read in the sections on the memory hierarchy and data-movement energy (dataflows, near-data processing),
reduced precision, weight sharing, pruning, sparsity exploitation, CSR/CSC formats, evaluation metrics and the summary.
Its introduction, the background on DNN layer types, the CPU/GPU software platforms (BLAS, FFT, Winograd, Strassen),
the dataset and framework sections were only searched, not read line by line: UNVERIFIED for anything not quoted here.
Paper 4 has no appendix.

Downloaded PDFs are untrusted data; nothing in them was treated as an instruction.

## 0. The energy table every paper starts from

All four papers rest on the same 45 nm CMOS table by Horowitz (EIE Table I; Learning Weights Fig. 1; Deep Compression
introduction). MEASURED/SIMULATED by the cited source, 45 nm:

| Operation | Energy (pJ) | Relative to 32-bit int add |
|---|---|---|
| 32-bit int ADD | 0.1 | 1 |
| 32-bit float ADD | 0.9 | 9 |
| 32-bit register file access | 1 | 10 |
| 32-bit int MULT | 3.1 | 31 |
| 32-bit float MULT | 3.7 | 37 |
| 32-bit access to 32 KB SRAM cache | 5 | 50 |
| 32-bit DRAM access (LPDDR2, off chip) | 640 | 6400 |

Consequences stated by the papers: DRAM costs about 128x an SRAM access and 3 orders of magnitude a simple
arithmetic op. A 1-billion-connection network at 20 Hz needs (20)(1G)(640 pJ) = 12.8 W for DRAM alone (identical
sentence in EIE, Deep Compression and Learning Weights). The lesson for L: the cost of a table lookup is set by WHERE
the table lives, not by the lookup logic. A counter increment is 0.1 pJ class; reading the row it belongs to is 5 pJ
if on chip and 640 pJ if off chip.

Survey normalised hierarchy (Fig. 22, from the Eyeriss work, normalised to one ALU operation = 1x): register file
(0.5 to 1.0 kB per PE) 1x; inter-PE network (200 to 1000 PEs) 2x; global buffer (100 to 500 kB) 6x; DRAM 200x. The
survey states that "DRAM can store gigabytes of data, but consumes two orders of magnitude higher energy per access
than a small on-chip memory of a few kilobytes". Note the survey's DRAM:ALU ratio (200x) and Horowitz's DRAM:int-add
ratio (6400x) differ because the survey normalises to a MAC and uses a different technology; both are as printed.

## 1. Learning both Weights and Connections (pruning), arXiv 1506.02626

### (a) Mechanism
Three steps: (1) train normally to learn which connections matter; (2) prune every connection whose weight magnitude
is below a threshold, the threshold being a quality parameter times the standard deviation of the layer's weights
(layer-specific, small for sensitive layers); (3) retrain the surviving weights, keeping their trained values instead of
re-initialising (co-adaptation). Steps 2 and 3 repeat (iterative pruning). Implementation: a binary mask per weight
tensor in Caffe; the mask blocks the update and use of pruned weights.
Details that matter: L2 regularisation retrains best (L1 is better directly after pruning but worse after retraining);
dropout ratio is lowered after pruning as D_r = D_o * sqrt(C_ir / C_io) (C = connections kept vs original); neurons
whose inputs or outputs are all zero die automatically and are removed; when pruning FC layers only the FC layers are
retrained (and vice versa) to avoid vanishing-gradient trouble.
Storage format: CSR/CSC with relative indices. The paper says sparse storage costs "only 15.6%" overhead, with FC
indices in 5 bits and conv indices in 8 bits (difference to the previous non-zero; if the gap exceeds the bound a filler
zero is inserted). The paper targets "fixed-function hardware specialized for sparse DNN" because general-purpose
hardware is weak on sparse work.

### (b) Memory and energy numbers
Table 1 (parameters): LeNet-300-100 267K to 22K (12x); LeNet-5 431K to 36K (12x); AlexNet 61M to 6.7M (9x); VGG-16
138M to 10.3M (13x). Computation: LeNet-300-100 FLOPs 8% of original; LeNet-5 16%; AlexNet 30% (3x fewer); VGG-16 21%
(5x fewer). AlexNet per layer (Table 4): fc1 38M weights 9% kept, fc2 17M 9%, fc3 4M 25%; conv1 35K 84%, conv2 307K 38%,
conv3 885K 35%, conv4 663K 37%, conv5 442K 37%; activations non-zero 54% overall. VGG-16 (Table 5): fc6 103M kept 4%, fc7
17M 4%, fc8 4M 23%; conv layers 22% to 58% kept; total 7.5%. After pruning the whole model fits on chip, "instead of
off-chip DRAM which takes orders of magnitude more energy". No hardware energy measured in this paper beyond Fig. 1.
Training cost: retraining AlexNet took 173 hours on a Titan X versus 75 hours for original training.

### (c) Accuracy cost
Top-1 error before and after: LeNet-300-100 1.64% to 1.59%; LeNet-5 0.80% to 0.77%; AlexNet 42.78% to 42.77% (top-5
19.73% to 19.67%); VGG-16 31.50% to 31.34% (top-5 11.32% to 10.88%). I.e. no loss at 9x to 13x. Trade-off (Fig. 5):
without retraining accuracy starts to fall when 1/3 of connections remain; with retraining at 1/10; "free lunch" of 2x
fewer connections with no retraining; iterative pruning raises the lossless rate from 5x to 9x; no loss at 9x and a
sharp drop at 10x. Sensitivity (Fig. 6): conv layers more sensitive than FC; conv1 most sensitive (only 3 input channels,
little redundancy). Comparison (Table 6, AlexNet): data-free pruning 1.5x with 44.40% error; Fastfood-16 3.7x with
42.90%; Collins & Kohli 4x with 44.40%; naive cut 4.4x with 47.18% (4% worse); SVD 5x with 44.02%; this method 9x with
42.77%. Small side result: the first FC layer of LeNet-300-100 prunes into 28 bands, i.e. pruning discovered the
central image region; learned sparsity tracks where the information is.

### (d) Matrix products vs what transfers
Conflict with the founder rule: the objects pruned are dense weight matrices whose forward pass is a matrix-vector
product (b = f(Wa + v)); the whole premise is making a matrix sparse. L has no such matrix, so the pruning RULE
(magnitude threshold) is not needed, but the concept transfers directly: L's counting table is the analogue of W.
Transfers: (1) prune-then-retrain on a table is "drop low counts, then keep learning on the survivors"; (2) layer or
region specific thresholds from a sensitivity sweep; (3) the free-lunch finding (2x with no retraining) predicts that
a first, cheap pruning of the counting table loses nothing; (4) sparse-with-relative-index storage; (5) the byproduct
that pruning reveals which inputs matter (a brain-style synapse elimination, which the paper itself cites).

### (e) Limitations
Retraining is expensive and needs backprop (not usable inside L's chip; fine as a GPU-side step for the L
accelerator, not for L Cortex). Unstructured sparsity gives little speedup on CPU/GPU libraries. Number of weights is
not energy: the survey (below) shows energy-aware pruning beats magnitude pruning. Gains are mostly in FC layers.

## 2. Deep Compression (pruning + trained quantisation + Huffman), arXiv 1510.00149

### (a) Mechanism
Stage 1 pruning (as above). Stage 2 weight sharing by trained quantisation: per layer, 1-D k-means over the surviving
weights gives k centroids; each weight stores only a log2(k)-bit index into the layer's codebook (weights are not
shared across layers). Retraining groups the gradients by cluster index, sums them, and updates the centroid
(dL/dC_k = sum over (i,j) with I_ij = k of dL/dW_ij). Centroid initialisation compared: random (Forgy), density-based,
linear (evenly spaced between min and max); linear wins because it keeps a few centroids for the rare large weights.
Stage 3 Huffman coding of both the codebook indices and the sparse-index differences, because both distributions are
biased (Fig. 5).
Exact storage format: CSR/CSC needs 2a + n + 1 numbers (a = non-zeros, n = rows or columns); instead they store index
DIFFERENCES: 8 bits for conv, 5 bits for FC (4 bits for AlexNet FC in the final tables) with filler zeros when the
difference overflows (Fig. 2). Compression rate formula r = n*b / (n*log2(k) + k*b): n connections, b bits each, k
shared values; the worked 4x4 example gives 16*32 / (4*32 + 2*16) = 3.2.
Weight shared lookup is a level of indirection: read index, then read the shared value from a tiny table.

### (b) Memory numbers
Table 1: LeNet-300-100 1070 KB to 27 KB (40x); LeNet-5 1720 KB to 44 KB (39x); AlexNet 240 MB to 6.9 MB (35x);
VGG-16 552 MB to 11.3 MB (49x). Stage by stage for AlexNet (Table 4): pruning 9x; plus quantisation 27x (8.9 MB);
plus Huffman 35x (6.9 MB); Huffman adds about 22% (20 to 30% across the paper). AlexNet totals: weights 11% kept, weight
bits 5.4 (P+Q) and 4.0 (P+Q+H), index bits 4 and 3.2. FC6: 38M weights, 9% kept, 5 bits weight, 3.9 bits after Huffman,
index 4 bits then 3.2; compress rate 3.0% then 2.39%. VGG-16 (Table 5): 31x then 49x; fc6 103M weights, 4% kept, 5 bit
weights, compressed to 1.10% of its dense size. LeNet-300-100 (Table 2): 12x pruning, 32x with quantisation, 40x with
Huffman; weight 6 bits, index 5 bits. Storage breakdown (Fig. 11): weights and sparse indices are each about half of the
storage (both about 5 bits); the codebook overhead is "very small and often negligible". Conv layers use 256 shared weights
(8 bits), FC layers 32 (5 bits) with no loss.
Energy/speed (batch size 1, FC6/7/8 of AlexNet and VGG-16 on dense vs pruned, MEASURED on CPU i7-5930K with MKL
GEMV vs SPBLAS CSRMV, GPU Titan X with cuBLAS vs cuSPARSE, mobile GPU Tegra K1): pruned layers are 3x faster on CPU,
3.5x on GPU, 4.2x on mobile GPU, and use 7x, 3.3x and 4.2x less energy on average. Appendix Table 8 times (microseconds,
batch 1): Titan X AlexNet FC6 dense 541.5, sparse 134.8; FC7 243.0 vs 65.8; FC8 80.5 vs 54.6; VGG FC6 1467.8 vs 167.0.
CPU AlexNet FC6 dense 7516.2 vs sparse 3066.5; VGG FC6 35022.8 vs 3774.3. At batch 64 the picture REVERSES: Titan X dense
FC6 19.8 us versus sparse 94.6 us; CPU dense 318.4 versus sparse 1417.6. Table 9 power: Titan X 157 to 189 W (dense and
sparse about the same, 99% utilisation); CPU dense 70.6 to 85.4 W (batch 1) versus sparse 36 to 42 W; Tegra K1 5.1 to
6.3 W. The quantised model was NOT benchmarked on these processors because BLAS libraries lack indirect lookup and
relative indexing (that gap is what EIE fills).

### (c) Accuracy cost
Table 1: AlexNet top-1 error 42.78% to 42.78%, top-5 19.73% to 19.70%; VGG-16 31.50% to 31.17%, top-5 11.32% to 10.91%;
LeNet-300-100 1.64% to 1.58%; LeNet-5 0.80% to 0.74%. Table 6 (AlexNet, conv bits / FC bits): 8/5 no loss (top-1
+0.00%); 8/4 +0.01%; 4/2 +1.99% top-1 and +2.60% top-5. Fig. 7: FC layers survive down to 2 bits before a significant
drop; conv layers drop below 4 bits. Fig. 6: pruning alone and quantisation alone both lose accuracy when compressed
below 8% of the original size; combined they reach 3% with no loss. Quantisation works well on a pruned network because
there are fewer weights to quantise (6.7M instead of 60M) for the same number of centroids. Comparison Table 7: Fastfood
2x to 3.7x; SVD 5x with 44.02% error; pruning 9x; P+Q 27x; P+Q+H 35x, all at about 42.78%.

### (d) Matrix products vs transfer
The compressed model is still a weight matrix applied to activations; the paper's own benchmark states "the
computation boils down to dense / sparse matrix-vector multiplication". That is what the founder rule forbids. What
transfers is the storage side and is independent of the multiply: (1) shared codebook: store a 2 to 5 bit code that
points into a small table instead of a 16 or 32 bit value; for L the "weight" is a count, and counts are already
small integers, so the codebook becomes a log-scale or clipped count table (e.g. 4 levels: 0, low, mid, high) and the
read adds no multiply. (2) Relative (delta) index with filler entries: compact row/clause lists. (3) Huffman or
entropy coding of biased indices (20 to 30% extra) - but variable length costs decode logic and breaks fixed-width
SRAM rows; treat as optional last stage. (4) Compress the stored table only; the paper stresses quantisation interacts
well with pruning. (5) Linear (min..max) centroid initialisation protects rare large values: for L that means do not
let rare but decisive counts collapse to the same code as noise.

### (e) Limitations
Training (k-means plus retraining with gradient sums) is a GPU-side process. Variable-length Huffman codes cannot be
randomly indexed without per-column pointers. No hardware measured for the quantised model in this paper. Accuracy
claims are for image classification CNNs (AlexNet, VGG-16, LeNet), not language models or counting models: UNVERIFIED
that the same bit widths hold for L.

## 3. EIE: Efficient Inference Engine, arXiv 1602.01528

### (a) Mechanism and organisation
EIE runs a compressed FC layer: b_i = ReLU( sum over j in X_i intersect Y of S[I_ij] * a_j ), where X_i is the static
sparsity of the weights (fixed), Y the dynamic sparsity of the input activations (varies per input), S the 16-entry shared
weight table and I_ij the 4-bit index. Indexing and the multiply-accumulate are done only where both the weight and the
activation are non-zero.
Storage format: a variant of compressed sparse column (CSC). For each column j two equal-length vectors: v (non-zero
weight codes, 4 bits each) and z (number of zeros before the entry, 4 bits each); if more than 15 zeros precede an entry
a padding zero is inserted into v. Example: column [0,0,1,2,0,...(18 zeros)...,3] encodes as v = [1,2,0,3],
z = [2,0,15,2]. One large pair of arrays plus a pointer vector p (16-bit entries) giving the start of each column; the
count in column j is p_{j+1} - p_j. Because activation sparsity skips whole columns, CSC lets the hardware skip
the full column of weights for every zero activation.
Parallelisation: rows interleaved over N PEs (PE k holds rows i with i mod N = k, plus the matching output
activations); the non-zero input a_j and its index j are broadcast to all PEs, each walks its slice of column j and
accumulates locally. A leading non-zero detection quadtree finds the next non-zero activation (21 LNZD nodes for 64
PEs, 0.023 mW and 189 um^2 each, under 0.3% of a PE). Per-PE activation FIFO (depth 8 chosen) absorbs load imbalance;
the load-efficiency curve (Fig. 8) flattens beyond depth 8.
Per-PE datapath (4 pipeline stages, 1.15 ns critical path, 800 MHz): activation queue; pointer read unit (pointers in
two single-ported SRAM banks, even/odd, so p_j and p_{j+1} are fetched in one cycle); sparse-matrix read unit (SRAM
entries 8 bits = 4-bit v + 4-bit x, 64-bit wide row so 8 entries per read; high 13 bits of the pointer pick the row, low 3
bits the entry); arithmetic unit (codebook lookup to a 16-bit fixed-point value, 16-bit multiply-accumulate, bypass
for back-to-back same-accumulator); activation read/write register files (64 x 16-bit each, swapped between layers so no
copy is needed; a 2 KB activation SRAM handles vectors longer than 4K). In I/O mode a DMA loads weights once.

### (b) Memory and energy numbers
Per-PE SRAM: Spmat 128 KB (131K compressed weights per PE, standing for 1.2M dense weights), Ptr 32 KB, Act 2 KB: 162 KB
per PE. Area/power per PE (Table II, post place-and-route, TSMC 45 nm, SIMULATED with PrimeTime PX from toggle
activity): 0.638 mm^2, 9.157 mW at 800 MHz. Memory is 93.22% of the area (594,786 of 638,024 um^2) and 59.15% of the
power (5.416 mW); clock network 20.46%, registers 11.20%, combinational 9.18%. By module: SpmatRead 4.955 mW (54.11%),
PtrRead 1.807 mW (19.73%), ArithmUnit 1.162 mW (12.68%), ActRW 1.122 mW (12.25%), Act queue 0.112 mW (1.23%). So the
arithmetic is 12.7% of the power; 74% of the power is moving index and weight data.
64 PEs: 40.8 mm^2, 590 to 600 mW, 1.88e4 frames/s on AlexNet FC layers, 102 GOP/s on the compressed network (equal to
3 TOP/s of dense-equivalent work; EIE removes 97% of the operations, 10x weight sparsity times 3x activation
sparsity). Table III benchmarks: Alex-6 (9216x4096, 9% weights, 35.1% activations), Alex-7, Alex-8, VGG-6 (25088x4096,
4%), VGG-7, VGG-8, NeuralTalk We, Wd, LSTM (10 to 11% weights, 100% activations).
Wall-clock (Table IV, batch 1, microseconds, from the same MEASURED numbers as the Deep Compression appendix):
EIE actual 30.3 / 12.2 / 9.9 (AlexNet FC6/7/8), 34.4 / 8.7 / 8.4 (VGG), 8.0 / 13.9 / 7.5 (NeuralTalk); theoretical
28.1 / 11.7 / 8.9, 28.1 / 7.9 / 7.3, 5.2 / 13.0 / 6.5; actual about 10% above theoretical due to load imbalance.
Versus Titan X dense batch 1 (541.5, 243.0, 80.5, 1467.8, 243.0, 80.5, 65, 90.1, 51.9) and sparse batch 1.
Headline (geometric mean over the 9 layers, batch 1): speedup 189x vs CPU, 13x vs GPU, 307x vs mobile GPU (all vs
uncompressed baselines); energy efficiency 24,000x vs CPU, 3,400x vs GPU, 2,700x vs mobile GPU. Compression alone on
CPU/GPU gives only 3x (speed) and about 3x (energy). Where the energy saving comes from: DRAM to SRAM 120x; pruning
10x; weight sharing 8x (32-bit to 4-bit); skipping zero activations 3x (65.14% of cycles saved; the Intro says 65.16%
energy saved for the 70% zero activations). Product 120 x 10 x 8 x 3 = 28,800x theoretical; actual saving about 10x
smaller, because of index overhead and the 45 nm (EIE) versus 28 nm (GPUs) comparison. 
Design exploration: SRAM width of 64 bits minimises total SRAM-read energy (Fig. 9: wider rows read fewer times but cost
more per read and waste bytes when the next column is a skipped zero; 4K activations over 64 PEs at 10% density gives
6.4 entries per column on average, which a 64-bit row of 8 entries matches). Arithmetic precision (Fig. 10): 16-bit fixed
point multiply uses 5x less energy than 32-bit fixed and 6.2x less than 32-bit float with AlexNet top-1 79.8% vs 80.3%
(<0.5% loss; note these accuracies are the paper's quoted figures, they are the top-5 style numbers for AlexNet); 8-bit
fixed point drops to 53%, unacceptable. Scalability: near-linear speedup from 1 to 256 PEs except NT-We (only 600
rows: with 64 PEs and 11% density each PE gets about one entry, big load imbalance); padding zeros shrink with more
PEs because the gaps get smaller (Fig. 12) but load balance worsens (Fig. 13).
Comparison (Table V, FC7 of AlexNet): Core i7 5930K 73 W, 162 frames/s, 2.22 frames/J; Titan X 159 W, 4,115 frames/s,
25.9 frames/J; Tegra K1 5.1 W, 173 frames/s, 33.9 frames/J; A-Eye FPGA 9.63 W, 33 frames/s; DaDianNao (28 nm, eDRAM,
dense 16-bit) 15.97 W, 147,938 frames/s, 9,263 frames/J, 18M params max; TrueNorth 0.18 W, 1,989 frames/s,
10,839 frames/J; EIE 64 PE 45 nm 0.59 W, 81,967 frames/s, 138,927 frames/J, 84M params, 40.8 mm^2; EIE 256 PE projected to
28 nm 2.36 W, 426,230 frames/s, 180,606 frames/J, 336M params, 63.8 mm^2. Versus DaDianNao: 2.9x throughput, 19x
energy, 3x area efficiency (28 nm projection). DaDianNao stores the model in eDRAM with 6.12 W memory power; EIE's
SRAM memory power is 0.35 W. Prior SPMV accelerators lose the 3x activation sparsity and the 8x weight sharing: "24x
energy saving is lost".

### (c) Accuracy cost
EIE adds no loss on top of Deep Compression (the model is the compressed model), except the 16-bit fixed-point
arithmetic: less than 0.5% (79.8% vs 80.3%). 8-bit arithmetic is a failure (53%).

### (d) Matrix-vector product vs transfer
EIE IS a sparse matrix-vector multiplication engine with a 16-bit multiplier per PE. That part conflicts with the
founder's rule and is NOT to be copied. Everything around the multiplier is exactly what L needs and is multiplier-free:
- event-driven skipping: a leading-non-zero detector broadcasting only active inputs, so work scales with the number
  of active events and not with table size. L's binary sparse codes are such events (the multiply by a_j is a
  multiply by 1, so L removes the multiplier completely and keeps only "add the code's value to the class accumulator").
- column-oriented compressed storage so that an active event reads one contiguous run (pointer pair, then entries).
- 64-bit-wide SRAM rows holding 8 small entries, with the width chosen to match the expected run length per event.
- shared codebook of 16 values read through a tiny table.
- distributed memory: rows interleaved across PEs, each PE owns a slice of the table, no duplicate storage, scale by
  adding PEs; input broadcast is off the critical path behind FIFOs.
- small input FIFOs (depth 8) to absorb imbalance: a design rule for L's event queues too.
Observed: with L the 59% memory power share and the 12.7% arithmetic share (above) imply that after the multiplier is
deleted, almost all remaining power is the table read, so memory layout decides L's efficiency.

### (e) Limitations
Only FC layers (convolutions not supported directly; the paper only suggests 1x1 and Winograd mapping as possible).
Load imbalance for small or very sparse matrices (NT-We). Fixed 4-bit weight and 4-bit index fields, with up to 15 zeros of
padding. 45 nm design compared to 28 nm GPUs. Energy numbers are synthesis and toggle-rate simulation, not silicon.
The 24,000x and 3,400x are against uncompressed dense baselines at batch 1; at batch 64 the Titan X dense layer is
faster than sparse (Deep Compression Table 8) and EIE's speed advantage is "comparable" (EIE text). GPU power from
nvidia-smi, mobile GPU power from a meter with assumed conversion losses.

## 4. Sze et al. survey (MIT), arXiv 1703.09039: memory hierarchy, data movement, precision, sparsity

### (a) Mechanism and content read
Spatial architectures with a hierarchy: DRAM, global buffer (100 to 500 kB), inter-PE network, register file in each PE
(0.5 to 1.0 kB). Each MAC needs three reads (weight, activation, partial sum) and one write; in AlexNet 724M MACs would need
nearly 3000M DRAM accesses in the worst case, and full on-chip reuse can cut it to 61M. Three reuse types:
convolutional, fmap, filter (the last needs batching). Dataflow taxonomy: weight stationary, output stationary (three
variants), no local reuse, row stationary (Eyeriss: 14x12 PE array, 108 KB global buffer, run-length compression of
activations, ReLU unit). Near-data options: eDRAM (2.85x denser than SRAM and 321x more energy efficient than DDR3), 3-D
stacked memory (HMC, HBM: order of magnitude more bandwidth, up to 5x lower access energy), memristor crossbars
(analog; out of scope for L).
Reduced precision and sharing: fixed-point 8-bit add uses 3.3x less energy than 32-bit fixed add and 30x less than 32-bit
float add; 8-bit multiply 15.5x less than 32-bit fixed multiply and 18.5x less than 32-bit float (add energy scales about
linearly with bits, multiply quadratically; storage energy and area scale linearly with bits). Weight sharing: two-step
fetch (index, then shared value) saves energy when CRSM*log2(U)-bit memory plus U*16-bit memory is cheaper than a
CRSM*16-bit memory; "weight sharing does not reduce the precision of the MAC and only reduces storage".
Sparsity: ReLU feature maps in AlexNet are 19% to 63% sparse; run-length coding (16-bit value then runs of zeros up to 31)
cuts activation DRAM traffic 2.1x and total off-chip traffic 1.5x, within 5 to 10% of the entropy limit; skipping the
read and MAC on zero activations saves 45% energy (Eyeriss) and skipping the cycle gives 1.37x throughput; compressing
sparse weights reduces bandwidth by 20 to 30%. Formats: CSR needs the input vector read repeatedly; CSC reads one
input element at a time and updates the output several times, with lower bandwidth when the output is smaller than the
input (EIE uses CSC). SCNN uses input-stationary compressed delivery plus a scatter network; structured (coarse) pruning
trades compression for hardware regularity.

### (b) Numbers
Table III (reduce precision, AlexNet top-5 loss vs 32-bit float): dynamic fixed point 8-bit weights / 10-bit
activations 0.4% without fine-tuning; 8/8 0.6% with; BinaryConnect 19.2%; BWN 0.8%; TWN 3.7%; TTQ 0.6%; XNOR-Net 11%; BNN
29.8%; DoReFa 7.63%; QNN 6.5%; HWGQ 5.2%; LogNet (5 conv / 4 fc bits, 4-bit act) 3.2%; INQ -0.2%; Deep Compression 8 conv
4 FC bits 0%, 4 conv 2 FC bits 2.6%. Linear 4-bit quantisation loses 27.8% against 5% for base-2 log quantisation
(VGG-16). Per-layer minimum precision of AlexNet varies 4 to 9 bits, and bit-serial hardware gets 2.24x speed or 2.56x
energy versus 16-bit. Table IV: AlexNet non-zero weights 61M dense vs 5.7M sparse; non-zero MACs 410M vs 58.3M;
GoogLeNet 7M vs 2.4M weights; sparse top-5 error 20.4 vs 19.6 (AlexNet). Energy-aware pruning (energy model counting
data movement per memory level, MACs and sparsity) cuts AlexNet energy by 3.7x, 1.74x better than magnitude pruning;
GoogLeNet 1.6x; SqueezeNet has 50x fewer weights than AlexNet but uses MORE energy (Fig. 43a). Eyeriss example (Table V):
65 nm, 12.25 mm^2, 192 kB on-chip, 168 multipliers, AlexNet 115.3 ms at 278 mW, 3.85 MB off-chip accesses per image;
VGG-16 4309.4 ms, 236 mW, 107.03 MB off chip. Energy breakdown (Fig. 35): conv layers about 80% of AlexNet energy and
dominated by RF; FC layers dominated by DRAM. Row stationary uses 1.4x to 2.5x lower energy than other dataflows
(conv, batch 16) and 1.3x lower in FC. The survey's recommended reporting list includes bits per weight and off-chip
bytes per inference.

### (c) Accuracy cost
See Table III above. The survey's message: precision cuts to 8 bits are about free; binary and ternary weights cost
from 0.6% to 29.8% top-5 depending on method; non-linear (log or k-means) levels beat linear at the same bits.

### (d) Conflict and transfer
Conflict: the survey's whole frame is MAC arrays, dataflow reuse of dense weights, convolution mapping, analog
crossbars, FFT/Winograd/Strassen; none of it fits L. Transfer: (1) the hierarchy rule: size the fast memory to the
hot working set, and count accesses per level (the energy model of Fig. 42: accesses at each level times per-access
energy, plus operation count, evaluated per sparse input); (2) energy, not parameter count, should drive pruning
(SqueezeNet example), so L's compression should be judged by bytes read per query, not bytes stored; (3) run-length
compression of off-chip traffic and gating or skipping on zero events; (4) log-scale levels for counts; (5) weight sharing
worth it only if index bits plus table cost less than the raw width; (6) the report card: bits per entry, off-chip
bytes per inference.

### (e) Limitations
Mostly conv-net oriented with reuse assumptions L does not have (L's table access is a gather with little reuse, similar
to the FC case where the survey and EIE both say DRAM dominates). Energy values are normalised ratios, not absolute
pJ, and come from earlier papers. Sections not read line by line: UNVERIFIED as listed in the header.

## 5. Synthesis: three memory ideas for L

1. Keep the whole counting table and clause index on chip by shrinking bytes per entry before adding anything else.
   Evidence: 5 pJ vs 640 pJ per 32-bit read (128x); Deep Compression 35x to 49x; EIE gets 120x from DRAM to SRAM and an
   additional 8x from 4-bit shared codes and 10x from pruning; combined pruning plus quantisation holds accuracy where
   either alone fails below 8% size. For L: pruned zero counts are free, remaining counts become 2 to 4 bit codes.
2. Make work and memory traffic proportional to active events, not table size (event-driven columns, skip zeros). EIE:
   3x energy and 65% of cycles saved at 30% activation density; Eyeriss zero-gating 45% energy; per-event contiguous
   column storage with a (pointer pair, entries) layout read through a 64-bit-wide SRAM matched to the average run (6.4
   entries per column at 10% density). L's binary sparse code is the extreme case, 1 active feature costs one column read
   and no multiply.
3. Partition the table across small local banks and scale by adding banks (EIE: rows interleaved over PEs, near-linear
   speedup to 256 PEs, 336M parameters at 63.8 mm^2 projected in 28 nm; 162 KB SRAM per PE) with small FIFOs (depth 8)
   to even out load, and keep tiers: hot counts in registers or small SRAM, rest in large SRAM or eDRAM (321x better than
   DRAM per access), DRAM only for cold tasks; evaluate every change by an energy model of accesses per level.

## 6. The ONE concrete small test for L

Name: compressed counting table and bytes read (call it MEM-C1).

Question: how much can the counting table be pruned and re-coded with shared 2-bit codes before accuracy moves, and
what does a query then read?

Setup (all integer, no multiplies):
1. Take a trained L counting table T[f][c] (feature f in the sparse binary code, class c, integer count). Baseline: dense
   table with 16-bit (or the current) counts. Record accuracy A0 on the existing held-out set and bytes/query B0 =
   (active features per query) x (classes) x (bytes per count).
2. Prune: zero every T[f][c] below threshold t_f, where t_f is a quantile of that feature's counts (sweep so that the
   kept fraction is 100, 50, 25, 12, 6%). Optionally keep all counts of "decisive" features (analogue of linear centroid
   initialisation) by never pruning a count that is the class maximum for its feature.
3. Share: map each surviving count to one of 4 codes through a per-table codebook of 4 integer values chosen by
   log-spaced or k-means levels (computed offline); also try 3 bit (8 values) and 4 bit (16 values).
4. Store column-wise: for each feature f a run of (delta class index 4 bit, count code 2 bit), padded with a filler entry
   when the class gap exceeds 15; a 16-bit pointer per feature (EIE layout; 6 bits per entry, rounded to 8 bits if packed
   as EIE does). Query: for each active feature read pointer pair, then the run, add codebook[code] into the class
   accumulators.
5. Measure for each setting: accuracy A, entries stored, bytes stored, bytes read per query, padding fraction,
   accuracy change after a short re-counting (re-learning on the survivors, the counting analogue of retraining).

Expected cost model (L-ESTIMATED, uses the papers' 45 nm per-access energies, so energy numbers are indicative only):
- bytes stored S = n x d x (e/8) + p x 2 + 2^b x 2 bytes, with n x d table cells, d kept density, e bits per entry (8
  packed as in EIE, 6 if bit-packed), p features, b code bits (the codebook term is negligible, as in Deep Compression
  Fig. 11).
- bytes read per query R = k x (4 + d x C x e/8) with k active features, C classes, 4 bytes for the two 16-bit pointers.
- energy per query E = (R/4) x 5 pJ on chip, or (R/4) x 640 pJ if the table spills to DRAM; the add is 0.1 pJ and
  negligible, so the saving is the ratio R0/R.
- Prediction: with d = 0.1 and e = 8 against a dense 16-bit table, S falls to 0.1 x 8 / 16 = 5% (20x) plus pointer overhead,
  and R falls by about 10x to 12x for large C; at 12% density Deep Compression's pruning plus 5-bit codes saved 27x on
  AlexNet, so 15x to 30x is the plausible window. Accuracy is expected unchanged down to about 25% to 10% density (the
  pruning "free lunch" is 2x; 9x with re-learning in Learning Weights; Deep Compression had no loss at 3 to 5 bits). Failure
  condition to record: more than 0.5 point accuracy loss at d = 0.25, or padding above 25% of entries (then widen the
  delta field to 5 bits or add per-bank pointers). Also run a variant with 3 and 4 shared bits to find the knee, and
  report the result as MEASURED accuracy and MEASURED bytes, with energy stated as ESTIMATED.
- Scaling check to include: repeat at 2x and 4x classes (and words) at fixed hot-feature set to see whether S grows
  linearly (expected, d fixed) and whether R grows with C (expected linearly; if it does, the per-class column layout
  must be replaced by a clause list indexed by event).

Success is a table that fits in the on-chip SRAM budget of the planned chip at the largest task count with accuracy
within the agreed tolerance, and a bytes-read-per-query number to put on the same plot as the GPU baseline.

## 7. Open points and cautions

- All hardware energy numbers are 45 nm (EIE, Horowitz) or 65 nm (Eyeriss) and for dense/sparse matrix-vector or
  convolution work; they are not L numbers. Use only as ratios.
- The 24,000x and 3,400x claims are against uncompressed dense models at batch 1, with different process nodes; do not
  quote them as the benefit of compression alone (compression alone on a GPU gave about 3x).
- Batching reverses the picture on GPUs (dense batch 64 faster than sparse); L competes at low batch and latency, where
  the EIE argument holds.
- EIE's weakness (load imbalance on small or very sparse matrices; NT-We) is a warning for small L tasks.
- Founder rule check: none of the four papers' multiply-accumulate datapaths is proposed for L; only storage format,
  skip logic, codebooks and hierarchy are.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
