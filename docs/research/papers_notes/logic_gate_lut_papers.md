---
title: Paper notes - logic gate and LUT networks
tags: [l, research, papers]
---

# Paper notes - logic gate and LUT networks

Source: full text of each arXiv PDF, read 24 Oct 2026 (pdftotext). All numbers below are numbers REPORTED BY THE PAPERS (none re-run by us). Where the PDF text extraction garbled a table and I could not map a value to its row with certainty, it is marked UNVERIFIED. Where a paper does not report a dataset it is marked "not reported".

Papers: [1] Deep Differentiable Logic Gate Networks, arXiv 2210.08277 (NeurIPS 2022). [2] Convolutional Differentiable Logic Gate Networks, arXiv 2411.04732 (NeurIPS 2024). [3a] LogicNets 2004.03021. [3b] PolyLUT 2309.02334. [3c] PolyLUT-Add 2406.04910. [3d] NeuraLUT 2403.00849. [3e] NeuraLUT-Assemble 2504.00592 (FCCM 2025). [3f] TreeLUT 2501.01511 (FPGA 2025). [4] AdderNet 1912.13200 (CVPR 2020). Note: the id 2504.01797 is NOT NeuraLUT-Assemble (it is an unrelated paper); the correct id is 2504.00592.

## 0. Bottom line for the reader (read this first)

1. The only recipe in this set that trains a hidden stack of tiny gates/tables to CNN-like image accuracy is [2] LogicTreeNet. Reported (discretised, i.e. hard-gate inference accuracy): MNIST 99.23 % (M, 566 K gates), 99.35 % (L, 1.27 M gates); CIFAR-10 86.29 % (G, 61.0 M gates), 84.99 % (L, 28.9 M), 80.17 % (B, 16.0 M). Fashion-MNIST: not reported in any of the papers read.
2. What makes it work, in order of measured effect in the [2] ablation (CIFAR-10, model L, Table 5, baseline 84.99 %): residual initialisation (Gaussian init instead: 76.18 %, minus 8.8 points; training does not converge, Fig. 7), logic-gate TREES as conv kernels (depth d=1,1,1,1 only: 80.98 %; d=2,2,2,2: 83.32 %), OR pooling (without: 81.45 %), only 2 input channels per tree (8 channels: 83.53 %), weight decay (without: 83.94 %).
3. The gradient trick is NOT a straight-through estimator. It is a closed-form probabilistic relaxation: every neuron holds 16 logits, output = softmax-weighted sum of the 16 real-valued gate formulas, inputs are probabilities in [0,1]. At export, argmax picks one gate per neuron. Gap soft vs hard is below 0.1 % on MNIST [1] and "very small during late training" on CIFAR-10 [2].
4. The LUT family ([3a]-[3e]) trains ordinary quantised neurons (weights, batch-norm, 2-3 bit activations with straight-through estimator via Brevitas) and enumerates every input combination into a truth table afterwards. Training is standard SGD/AdamW backprop, export is an exact table lookup. Accuracy on MNIST tops out at 98.6 % (NeuraLUT-Assemble with augmentation) with 6-input LUTs. CIFAR-10: none of [3a]-[3f] report it.
5. Easiest to reimplement in PyTorch on CPU in a few hours: [1] (about 40 lines; the whole layer is a gather, 16 formulas, a softmax mix). Add the residual initialisation (one line, z[A]=5) and you have the key ingredient of [2]. The LogicTreeNet convolution (shared-parameter gate trees, OR pooling) is another 1-2 hours in plain PyTorch (slow but fine for MNIST sizes; the authors needed fused CUDA kernels for CIFAR scale). Section 9 gives a concrete recipe.
6. Matrix-free check against the project rule (no dense matrix-vector products): [1] and [2] are fully matrix-free at inference (2-input gates, gathers, popcount for the class score). [3a]-[3e] are table lookups at inference; the only multiplies exist inside training. [3f] TreeLUT is comparisons + table + small adder tree. [4] AdderNet is NOT a lookup design: it is a dense L1-distance convolution (about 2x the additions of a CNN, plus batch-norm multiplications, plus full-precision first and last layers in its CIFAR setup), so it breaks the "no dense matrix" rule. Notes on it are for training tricks only.

## 1. Deep Differentiable Logic Gate Networks (Petersen, Borgelt, Kuehne, Deussen; arXiv 2210.08277)

### Architecture
- Layered network of 2-input logic gates. Each neuron has exactly 2 inputs chosen pseudo-randomly at init and FIXED for the whole training. No weights, no activation function. Same neurons per layer ("straight network"), 4 to 8 layers in all experiments; architecture picked by grid search over layers in {2..10} and width in factors of 2.
- 16 possible 2-input Boolean functions; a neuron's whole state is 4 bits after training.
- Output: n output neurons grouped into k classes (n/k per class); class score = number of 1s in the group (popcount). In training the sum of probabilities is used. Score divided by a temperature tau then softmax cross-entropy.
- Aggregation formula in the paper: sum over group divided by tau plus optional beta (beta irrelevant for classification).

### Training: relaxation, init, optimiser
- Activations relaxed to probabilities a in [0,1]; gates replaced by their expectation under independent Bernoulli inputs. Table 1 of the paper (id, op, real-valued form): 0 False 0; 1 A and B = A*B; 2 not(A implies B) = A - AB; 3 A = A; 4 not(A implied by B) = B - AB; 5 B = B; 6 xor = A + B - 2AB; 7 or = A + B - AB; 8 nor = 1 - (A + B - AB); 9 xnor = 1 - (A + B - 2AB); 10 not B = 1 - B; 11 A implied by B = 1 - B + AB; 12 not A = 1 - A; 13 A implies B = 1 - A + AB; 14 nand = 1 - AB; 15 True 1.
- Gate choice: each neuron has w in R^16, p = softmax(w), neuron output = sum_i p_i * f_i(a1, a2). Fully differentiable, no sampling, no Gumbel, no straight-through.
- Init: w drawn i.i.d. from a standard normal ("washed out" distributions; [2] later shows this is the weak point beyond about 6 layers).
- Optimiser: Adam, constant learning rate 0.01 for logic nets (0.001 for the NN baselines), batch size 100, up to 200 epochs. Authors state Adam is much better than SGD or SGD+momentum here because its per-step gradient normalisation helps deeper gate nets.
- Temperature tau searched over {1, 1/0.3, 1/0.1, 1/0.03, 1/0.01}; optimum depends mainly on outputs per class (more outputs => larger tau). Heuristic in text: when n grows 10x, tau should shrink by a factor of roughly sqrt(2) to 10 as printed in the paper text (the extracted text is garbled here; treat the exact factor as UNVERIFIED). Chosen values in Table 6: MNIST small 1/0.1, MNIST normal 1/0.03, CIFAR small 1/0.03, CIFAR medium/large/large x2/large x4 1/0.01.
- Discretisation: take the mode (argmax) of each neuron's distribution. All reported results are after discretisation. MNIST gap below 0.1 %. Most neurons converge to one gate. Float16 training did not hurt (not used for reported numbers). Reduced gate sets (fewer than 16) were always worse.
- Training cost: MNIST small 1.8 h, MNIST normal 5.3 h; CIFAR small 1.3 h, medium 7.4 h, large 24.2 h, large x2 45.6 h, large x4 90.3 h (their Table 8/9, original unoptimised code, A6000-class GPU).

### Input encoding
- MNIST: binarised pixels (threshold not stated in the text I read; UNVERIFIED).
- CIFAR-10: thermometer code. Colour-channel resolution 4 => 3 binary values per channel at thresholds 0.25, 0.5, 0.75 (small, medium, large models use this per Table 5 caption: "first 3 lines"); resolution 32 => 31 binary values with thresholds i/32 for i in 1..31 (large x2? the caption says "the large models"; the exact rows using 32 are UNVERIFIED; the text says last three rows of the top block: large, large x2, large x4). No data augmentation, no dropout.

### Size, inference
- Parameters = number of gates. Table 6: MNIST small 6 layers x 8 000 = 48 000; MNIST normal 6 x 64 000 = 384 000; CIFAR small 4 x 12 000 = 48 000, medium 4 x 128 000 = 512 000, large 5 x 256 000 = 1 280 000, large x2 5 x 512 000 = 2 560 000, large x4 5 x 1 024 000 = 5 120 000.
- Inference: bitwise ops on int64 words, 64 images batched bit-sliced (bit j of word i = value i of image j). Authors estimate about 250 binary gates per core per Hz-cycle. Connections need not be stored (regenerate from a seed); only 4 bits per gate. Class popcounts done with adder logic. Compiled to C, gcc compile time quadratic in lines, the reason the biggest models' numbers are extrapolated (in parentheses).

### Accuracy rows (all MEASURED by the authors, averaged over 10 runs for their own models)
Table 4 (MNIST, binarised input; columns Acc, params, space, CPU time, GPU time, OPs):
- Linear Regression 91.6 %, 4 010 params.
- Neural Network (small) 97.92 %, 118 282 params, 462 KB.
- Neural Network 98.40 %, 22 609 930 params, 86 MB, 2.2 ms CPU.
- Diff Logic Net (small) 97.69 % (+-0.11), 48 000 gates, 23 KB, 625 ns CPU, 6.3 ns GPU, 48 K ops.
- Diff Logic Net 98.47 % (+-0.05), 384 000 gates, 188 KB, 7 us CPU, (50 ns) GPU, 384 K ops.
- Baselines in same table: FINN 98.40 % (641 ns, 5.28 M ops); ReBNet 98.29 %; LowBitNN 99.2 %; SET-MLP 98.74 % with 89 797 params; L0 regularisation 98.6 %.
- Claim: more than 1 million MNIST images per second on one CPU core at > 97.5 %; > 12x faster than the best BNN at 98.4 %.

Table 5 (CIFAR-10):
- Neural Network (colour res 4) 50.79 %, 12.6 M params.
- Diff Logic Net small 51.27 % (48 K gates); medium 57.39 % (512 K); large 60.78 % (1.28 M); large x2 61.41 % (2.56 M); large x4 62.14 % (5.12 M, 2.44 MB).
- Comparison rows: Regularized SReLU NN 68.70 % (20.3 M params); Student-Teacher NN 65.8 % (1 M) and 74.3 % (31.6 M); SET-MLP 74.84 %.
- Fashion-MNIST: not reported. Also tested: MONK-1/2/3, Adult census, Breast cancer (tabular; not copied here).

### Observations useful for design
- Gate histogram (4-layer CIFAR model, 12 000 neurons/layer): constants 0/1 rarely used; first layer and/nand/or/nor; middle layers many pass-through A, B, not A, not B (the net builds its own residual paths); last layer mostly xor/xnor; implications rare.
- Limits stated by the authors: training cost high; "convolutions and residual connections" listed as future work; performs well only up to about 6 layers (stated again in [2]).

## 2. Convolutional Differentiable Logic Gate Networks (Petersen, Kuehne, Borgelt, Welzel, Ermon; arXiv 2411.04732)

### Architecture (LogicTreeNet)
- Convolution with logic-gate trees: each output channel k has a complete binary tree of depth d (d=3 in the main models, 2^d - 1 = 7 learnable gates, 8 leaf inputs). The 8 leaves are picked at random (fixed) from the receptive field (3x3 x C_in; MNIST first layer 5x5). The tree's gate choices are SHARED across all spatial positions (this is the weight sharing / equivariance). Different output channels have independent gates.
- Restriction: each tree reads only 2 input channels (not up to 8). Ablation: 83.53 % (8 channels) vs 84.99 % (2 channels). Also chosen so that hardware routing stays local (model split into k/8 groups with no cross connections, no accuracy cost).
- OR pooling: 2x2 stride 2, logical OR relaxed with the max t-conorm max(a,b) (not a probabilistic OR). Without OR pooling: 81.45 %. Training pulls the post-pool activation level back to the no-pooling level (post-pool 66.5 % at init, converges), no regulariser needed.
- Net layout CIFAR-10 (k = width; k in S 32, M 256, B 512, L 1024, G 2048 per text; Table 6 lists G as k = 2 560, discrepancy inside the paper, UNVERIFIED which is right): conv(k kernels, 3x3, d=3) -> ORpool -> conv(4k) -> ORpool -> conv(16k) -> ORpool -> conv(32k) -> ORpool (2x2 left) -> flatten 128k -> random logic layers 128k->1280k->640k->320k -> GroupSum (10 classes). Zero padding 1. Logical depth 23 layers, 15 trainable (4 conv blocks with 2 learnable tree levels... see paper Fig. 6; the text says "tree depths of d=3,4"), 3 random layers. B and L use 2x gates in last layers.
- MNIST layout: 3 conv blocks: k kernels 5x5 d=3 no padding -> ORpool (12x12) -> 3k 3x3 -> ORpool (6x6) -> 9k 3x3 -> ORpool (3x3) -> flatten 81k -> 1280k -> 640k -> 320k -> GroupSum. Output gate factor 2 for S and M.

### Training
- Relaxation identical to [1] (16 logits, softmax-mixture of probabilistic gate formulas), plus max t-conorm for pooling.
- Residual initialisation (the key new trick): initialise each gate's logits so that gate "A" (pass first input) has probability about 90 % and the other 15 gates 0.67 % each. Equivalent to z[A] = 5 and all other z = 0 (softmax(5,0,...,0) = e^5/(e^5+15) = 0.908). Reasoning: Gaussian init washes activations towards 0.5 and the gradient norm shrinks by a factor of 0.1 to 0.2 per gate, so deep nets cannot train. Residual init makes every gate a wire at first; training replaces it where useful. Bonus: trained net contains many A gates, which cost nothing in hardware after logic synthesis. Appendix Fig. 11 ablates z[A] on an MNIST model: works for z >= 2, z=1.5 gives only 13 %, "generally recommend z = 5"; on CIFAR-10 z=2 was too small to train.
- Optimiser AdamW, learning rate 0.02 (CIFAR) and 0.01 (MNIST), weight decay 0.002 (CIFAR S,M,B,L; 0.001 for G), 0 for MNIST. Batch 128 for CIFAR; MNIST 512 (S), 256 (M), 128 (L). Per-epoch time 30 s for the L model on one RTX 4090. Curves in Fig. 7 run to 700 epochs; Fig. 10 x-axis to 1000 (units not stated, UNVERIFIED). Hold-out validation sets used for model selection (CIFAR 45 000/5 000, evaluated every 2 000 steps; MNIST 50 000/10 000, every 5 000 steps).
- Temperature tau (Table 6): CIFAR S 20, M 40, B 280, L 340, G 450; MNIST S 6.5, M 28, L 35. Rule of thumb: tau proportional to sqrt(outputs per class); larger tau for harder tasks; for the teacher setting multiply tau by about sqrt(2). Outputs per class: CIFAR 1K / 8K / 32K / 64K / 80K; MNIST 1K / 4K / 8K.
- Teacher: CIFAR B, L, G models are supervised by a neural-network teacher on the class-score level (so those rows are not pure hard-label training). S and M are not.
- Fused CUDA kernels: tree + pooling in one kernel (keep intermediates in registers, store only output and pool index, recompute in backward). 68 % fewer memory accesses, about 90 % less training memory, up to 200x faster per gate than [1]'s implementation. d=4 trees not worth it (register pressure, over 10x slower, no gain per gate).
- Discretisation: argmax per gate. Gap small late in training (Fig. 10), no noticeable overfitting. Logic synthesis afterwards removes trivial gates: MNIST L had 3 216 128 training gates, 697 758 after synthesis.

### Input encoding
- CIFAR S, M: 2-bit per channel via 3 thresholds as in [1]. B, L, G: 5-bit input plus fixed (non-learned) edge and curvature detector kernels with thresholds, turned into binary codes; their gate cost is included in the gate counts.
- MNIST: 1 input bit (# input bits = 1 in Table 6), binarised.

### Accuracy rows (MEASURED, discretised models; authors' tables)
Table 1 (CIFAR-10, accuracy, gate count):
- LogicTreeNet-S 60.38 %, 0.40 M; M 71.01 %, 3.08 M; B 80.17 %, 16.0 M; L 84.99 %, 28.9 M; G 86.29 %, 61.0 M.
- Reference rows: DiffLogic medium 57.39 % 0.51 M; DiffLogic largest 62.14 % 5.12 M; Conv. TTNet small 50.10 % 0.57 M, large 70.75 % 189 M; FINN CNV 80.10 % 901 M; LUTNet 84.95 % 1 290 M; XNOR-Net (NIN) 86.28 % 1 780 M; ReBNet 80.59 % / 85.94 %; BinaryNet 88.60 % 4 090 M; FBNA CNV 88.61 % 5 540 M; Hirtzlin et al. 91 % 87 400 M. The 29x claim is G (61 M gates) versus XNOR-Net 1 780 M.

Table 2 (CIFAR-10 FPGA time per image, Xilinx VU13P, input-transfer limited): LogicTreeNet-S 60.38 % 9 ns; M 71.01 % 9 ns; B 80.17 % 24 ns (41.6 M FPS) vs FINN CNV 80.10 % 45.6 us. No energy figures reported in this paper.

Table 3 (MNIST, accuracy, gates, FPGA time; Xilinx XC7Z045):
- LogicTreeNet-S 98.46 %, 147 K gates, 4 ns; M 99.23 %, 566 K, 5 ns; L 99.35 %, 1.27 M, time not reported.
- Reference: DiffLogic small 97.69 % 48 K; DiffLogic 98.47 % 384 K; DWN 98.77 % 45 ns; TTNet 98.02 % 360 K; LUTNet 98.01 % 5 ns; FINN CNV 98.40 % 5.28 M 641 ns; FINN FCN 98.86 % 258 M; LowBitNN 99.2 % 152 us.
- Seed variance of individual models (Table 4): S 98.21 % +-0.31, M 99.13 % +-0.11, L 99.29 % +-0.06; small models were trained several at once and selected on the validation set.

Table 5 (CIFAR-10 ablation around L = 84.99 %): conv depths d=1,1,1,1 80.98 %; 1,1,2,2 82.68 %; 2,2,2,2 83.32 %; 2,2,3,3 84.13 %; no OR pool 81.45 %; Gaussian init 76.18 %; no weight decay 83.94 %; 8 input channels per tree 83.53 %.

Fashion-MNIST: not reported. Energy: not reported (gate count used as chip-area proxy; BMAC about 8 gates quoted in appendix).

## 3. LUT-network family (all Imperial/Sydney/Xilinx FPGA work; training is standard backprop, inference is table lookup)

Common recipe of [3a]-[3e]: a "neuron" or "sub-network" with small fan-in F and beta-bit quantised inputs/outputs is a function of X = F*beta bits. After training, evaluate it on all 2^(F*beta) input combinations and store the result as a ROM (an "L-LUT", later mapped to 6-input FPGA LUTs by synthesis). Cost grows exponentially in F*beta, so everything is very sparse and low bit.

### 3a. LogicNets (Umuroglu, Akhauri, Fraser, Blott; arXiv 2004.03021)
- Architecture: sparse MLP. Each neuron has a fixed random fan-in gamma (random sparsity chosen a priori, mask fixed), weights, batch-norm, and a beta-bit quantised activation. Neuron = X:Y truth table with X = gamma*beta input bits, Y = beta output bits. Example in paper: 6 inputs x 2 bits = 12 input bits, 2 output bits, cost formula LUTCost(X,Y) = (Y/3) * (2^(X-4) - (-1)^X) 6-input LUTs, which gives 170 for X=12, Y=2. They cap X = beta*gamma <= 15 in the exploration.
- Training: PyTorch + quantisation-aware training (straight-through estimator with learned scale factors), Adam, mini-batch 1024, 1000 epochs, step-decay learning rate starting at 0.1. Standard backprop. Convert by enumeration (lossless) to Verilog ROMs.
- Datasets: jet substructure (JSC) and UNSW-NB15 network intrusion (NID). MNIST, Fashion-MNIST, CIFAR-10: not reported in this paper.
- Rows (Table I; accuracy, synthesised LUTs, Fmax): JSC-S 67.8 %, 214 LUTs; JSC-M 70.6 %, 14 428; JSC-L 71.8 %, 37 931 (I could not tie every number in the garbled row to its column; the 214 and 37 931 figures are stated in the prose, the rest UNVERIFIED); NID-S 83.88 %, NID-M 91.30 %, NID-L 88.68 %. Latency "less than 15 ns", hundreds of millions of inferences per second.
- Finding on activation bitwidth: beta=2 or 3 beats binary at similar LUT cost (JSC: 88.7 % versus 85.3 % best binary in the NID plot, per the prose of Section V-B).

### 3b. PolyLUT (Andronic, Constantinides; arXiv 2309.02334)
- Idea: inside each neuron replace the linear function by a multivariate polynomial of degree D over its F inputs (all monomials up to degree D, count = (F+D)!/(F! D!)). Because the whole thing is tabulated anyway, the multiplications cost nothing at inference and the table size is unchanged. Parameters scale polynomially (Table II: LogicNets F+1; PolyLUT (F+D choose D); LUTNet 2^(beta F)).
- Training: PyTorch, AdamW (decoupled weight decay) with SGD warm restarts, Brevitas quantised activations with learned scales, batch-norm at input and output of each layer. 1000 epochs for JSC and UNSW-NB15 (batch 1024), 500 epochs for MNIST (batch 256). Fixed random sparsity.
- MNIST model HDR (Table III): neurons per layer 256, 100, 100, 100, 100, 10 (input 784), beta=2, F=6, polynomial degree D=4; exception beta0/F0 for input layer (the table lists "beta0 = 1" in this column; I cannot tell from the extracted text which model it belongs to, UNVERIFIED; the follow-up paper lists the input layer for NID as beta_i=1, F_i=7). The input code for the 784 pixels is not described in the text I read (UNVERIFIED).
- Table IV rows: MNIST PolyLUT (HDR) 96 %, 70 673 LUTs, 4 681 FF, 0 DSP, 0 BRAM, 378 MHz, 16 ns. FINN 96 %, 91 131 LUTs, 5 BRAM, 200 MHz, 310 ns. hls4ml 95 %, 260 092 LUTs, 190 ns. Claimed 19.38x lower latency than FINN, 11.88x lower than hls4ml, 1.28x fewer LUTs than FINN.
- Other: NID Lite 92 %, 3 336 LUTs, 9 ns (LogicNets 91 %, 15 949 LUTs, 13 ns); JSC-M Lite 72 %, 12 436 LUTs, 5 ns; JSC-XL 75 %, 236 541 LUTs, 21 ns. Case study: higher degree lets you drop layers; latency reduction 1.76x to 2.29x at equal error.
- CIFAR-10, Fashion-MNIST: not reported.

### 3c. PolyLUT-Add (Lou, Rademacher, Boland, Leong; arXiv 2406.04910)
- Idea: widen effective fan-in by summing A independent PolyLUT sub-neurons (each fan-in F, separate random sparse connections) in a second small "Adder-layer" table (itself a table with A*(beta+1) input bits). Total fan-in F*A with table sizes about A*2^(beta F) + 2^(A(beta+1)) instead of 2^(beta F A).
- Training: PolyLUT toolflow, AdamW, 1000 epochs (JSC-M Lite, NID Lite), 500 epochs (JSC-XL, HDR), batch 1024 (JSC, NID) and 128 (MNIST). Note: NID training sensitive to random seed.
- MNIST HDR model: layers 256, 100, 100, 100, 100, 10, beta=2, F=6, A in {2,3}, D in {1,2} for the main sweep; D=3 in the "optimise for accuracy" Section.
- Table II (HDR; accuracy, table entries): PolyLUT D=1 F=6: 93.8 %; PolyLUT-Add D=1 F=6x2: 96.5 % (A=3: 96.6 %); PolyLUT D=2: 95.4 %; PolyLUT-Add D=2 6x2: 97.1 %, 6x3: 97.6 %. (A column of 96.1 % and 97.3 % belongs to high-fan-in PolyLUT F=10 with 2^12 x 256 entries; mapping inferred, partly UNVERIFIED.) Claimed gain over PolyLUT: 2.7 points MNIST (A=2).
- Table III MNIST row: PolyLUT-Add (HDR-Add2, D=3) 96 %, Fmax 625 MHz, latency 10 ns, FF 2 609; PolyLUT (HDR, D=4) 96 %, 70 673 LUTs, 378 MHz, 16 ns. LUT count of the PolyLUT-Add MNIST row could not be recovered from the garbled table (UNVERIFIED). Abstract: LUT reduction 2.0x to 13.9x and latency 1.2x to 1.6x at similar accuracy.
- CIFAR-10, Fashion-MNIST: not reported.

### 3d. NeuraLUT (Andronic, Constantinides; arXiv 2403.00849)
- Idea: map an entire small dense sub-network (L layers, width N, ReLU, full-precision, with skip connections of step S) onto one L-LUT. Only the sub-network's F quantised inputs and 1 quantised output are visible, so table size stays 2^(beta F) regardless of the hidden depth/width. Skip connections inside the sub-network fight vanishing gradients (the whole circuit is much deeper than a LogicNets net). Parameter count per L-LUT O(L N^2 + (F+L) N).
- Training: PyTorch, AdamW + SGD warm restarts, Brevitas, batch-norm on sub-network inputs/outputs; 1000 epochs for JSC and 500 for MNIST. Conversion: enumerate all 2^(beta F) inputs through the sub-network (lossless), emit Verilog ROMs with registers.
- MNIST model HDR-5L: L-LUTs per layer 256, 100, 100, 100, 10; beta=2; F=6; L=4; N=16; S=2; exception beta0=7, F0=2 (as printed in Table II; the pairing of the exception with HDR-5L vs the JSC rows is slightly ambiguous in the extracted text).
- Table III MNIST: NeuraLUT HDR-5L 96 %, 54 798 LUTs, 3 757 FF, 0 DSP, 0 BRAM, 431 MHz, 12 ns, area x delay 6.6e5. PolyLUT 96 %, 70 673 LUTs, 16 ns, 11.3e5. FINN 96 %, 91 131 LUTs, 310 ns, 282.5e5. hls4ml 95 %, 260 092 LUTs, 190 ns, 494.2e5. Claimed up to 26x latency reduction on MNIST (vs FINN) and 4.3x lower latency than prior LUT work at equal accuracy (abstract).
- JSC rows: JSC-2L 72 %, 4 684 LUTs, 3 ns; JSC-5L 75 %, 92 357 LUTs, 14 ns.
- CIFAR-10, Fashion-MNIST: not reported.
- Note for our rules: the sub-network inside each L-LUT is dense and float during training only; the exported object is a pure table.

### 3e. NeuraLUT-Assemble (Andronic, Constantinides; arXiv 2504.00592)
- Idea: build one wide-fan-in neuron as a TREE of small L-LUTs (e.g. a 16-input tree from fixed 4-input or 6-input L-LUTs plus a combining LUT) so that no single table exceeds 6 input bits at beta=1. Tree parameters per layer: assemble flag (fixed sparsity within tree, learned grouping at the leaves), fan-ins, bit widths, L, N, S.
- Grouping of the leaf connections is NOT random: first a dense training stage with a hardware-aware group regulariser, then structured pruning to the allowed fan-in, then retraining (method of the extended PolyLUT paper). This removes seed sensitivity. Mixed precision: input and output layers get more bits than the inner tree layers.
- Skip connection across the whole tree: all activations inside a tree removed except the last, so a linear skip path from tree input to tree output is hidden inside the final table (no extra hardware).
- Training: PyTorch QAT, AdamW + SGD warm restarts, Brevitas, 1000 epochs JSC, 500 epochs MNIST and NID. Learning rate value not stated in the text I read (UNVERIFIED).
- MNIST configuration (Table II): layer sizes [2160, 360, 2160, 360, 60, 10], assemble flags [0,1,0,1,1,1], fan-ins [6,6,6,6,6,6], bit widths [1,1,1,1,1,6], L=2, N=64, S=2. So hidden activations are 1 bit and fan-in 6, i.e. 6-input LUTs; only the output layer has 6 bits.
- Accuracy rows (Table II/IV): floating-point FC reference 98.7 %; NeuraLUT-Assemble 97.9 % without augmentation, 98.6 % with augmentation (a dense FC reference of same size 98.4 % per Table II). Hardware (Table IV, out-of-context P&R, xcvu9p): +aug 5 037 LUTs, 713 FF, 849 MHz, 2.2 ns, area x delay 1.11e4; no-aug 5 070 LUTs, 725 FF, 863 MHz, 2.1 ns, 1.06e4. Comparisons in the same table (accuracy/LUTs): TreeLUT 96.6 %, 4 478 LUTs, 2.5 ns; DWN 97.8 %, 2 092 LUTs, 9.2 ns; NeuraLUT 96 %, 54 798 LUTs, 12 ns; PolyLUT-Add 14 810 LUTs and AmigoLUT 16 081 LUTs (their accuracy column mapping is garbled in extraction, UNVERIFIED); hls4ml 95 %, 260 092 LUTs, 190 ns. Claims 62x area-delay reduction and +2 points versus NeuraLUT on MNIST; 8.42x on JSC CERNBox.
- Pipelining: register per layer or per 3 layers; MNIST latency 6.5 ns/5.040 LUT at 916 MHz (every layer) vs 2.2 ns at 849 MHz (every 3 layers) per Table III.
- CIFAR-10, Fashion-MNIST: not reported.

### 3f. TreeLUT (Khataei, Bazargan; arXiv 2501.01511)
- Not a neural net: gradient-boosted decision trees (XGBoost) turned into hardware. Inputs quantised to w_feature bits (comparison thresholds quantised accordingly), each tree = comparators + a LUT-mapped decision structure, leaf values quantised to w_tree bits, then adder trees sum tree outputs per class and an argmax picks the class. No multiplications, no BRAM, no DSP. Quantisation: per tree shift leaves by min leaf, scale all by one positive factor (2^w_tree - 1)/max leaf, round; shift bias; argmax unchanged.
- Training: XGBoost with n_estimators (trees per class), max_depth, eta, scale_pos_weight, plus grid search on w_feature, w_tree. RTL generation takes seconds (versus hours for PolyLUT family).
- MNIST (784 features, 10 classes) hyper-parameters (Table 2): TreeLUT (I): 30 trees per class, depth 5, eta 0.8, w_feature 4, w_tree 3, pipeline [0,1,1], accuracy 96.6 % (96.9 % before quantisation). TreeLUT (II): 30 trees, depth 4, eta 0.8, w_feature 4, w_tree 3, 95.6 % (96.5 % before quantisation).
- Table 5 hardware: TreeLUT (I) MNIST 97 % (rounded), 4 478 LUTs, 597 FF, 791 MHz, 2.5 ns, area x delay 1.12e4; TreeLUT (II) 96 % (rounded), 3 499 LUTs, 759 FF, 874 MHz, 2.3 ns, 8.05e3. POLYBiNN (I) 97 %, 109 653 LUTs, 90 ns. PolyLUT-Add 96 %, 14 810 LUTs. Claims 4x to 101x lower area-delay than recent LUT-NNs.
- Other: JSC (I) 75.6 %, NID (I) 92.7 %. CIFAR-10, Fashion-MNIST: not reported. Ceiling: about 97 % on MNIST.

### 3g. Cross-paper comparison on MNIST (reported numbers)
| Method | Hidden units | MNIST acc | Cost (reported) |
|---|---|---|---|
| Diff. Logic Net [1] | 384 000 random 2-input gates | 98.47 % | 384 K gates, 7 us/img one CPU thread |
| LogicTreeNet M [2] | conv gate trees | 99.23 % | 566 K gates, 5 ns FPGA |
| LogicTreeNet L [2] | conv gate trees | 99.35 % | 1.27 M gates |
| PolyLUT HDR [3b] | 6-input 2-bit polynomial LUTs | 96 % | 70 673 LUTs, 16 ns |
| PolyLUT-Add [3c] | adder of poly-LUTs | 96 % at 10 ns | 625 MHz (LUT count UNVERIFIED) |
| NeuraLUT [3d] | 6-input 2-bit sub-net LUTs | 96 % | 54 798 LUTs, 12 ns |
| NeuraLUT-Assemble [3e] | LUT trees, 1-bit | 97.9 % / 98.6 % (+aug) | about 5 000 LUTs, 2.1-2.2 ns |
| TreeLUT [3f] | GBDT | 96.6 % / 95.6 % | 4 478 / 3 499 LUTs, 2.5 / 2.3 ns |
No paper in the set reports Fashion-MNIST. CIFAR-10 is reported only by [1] (best 62.14 %) and [2] (best 86.29 %).

## 4. AdderNet: Do We Really Need Multiplications in Deep Learning? (Chen, Wang, Xu, Shi, Xu, Tian, Xu; arXiv 1912.13200) - method and training tricks only

- Method: replace the convolution (cross-correlation) by the negative L1 distance between filter and input patch: Y(m,n,t) = - sum |X(m+i,n+j,k) - F(i,j,k,t)|. Output is always <= 0, so batch norm follows every adder layer and then normal activations are usable. Subtraction by complement addition. Cost: about 2x the additions of the equivalent CNN, zero multiplications in the adder layers, but batch norm still multiplies (authors say negligible, ratio about 4068 for c_in = 512, d = 3).
- Not a lookup design and not matrix-free: it is a dense template-matching convolution. It fails the project's "no dense matrix" rule. Use only the training tricks below.
- Tricks that matter:
  1. Gradient w.r.t. filters: use the full-precision "L2-style" gradient X - F (Eq. 5), not the true L1 gradient sgn(X - F) (which makes it signSGD and fails in deep nets).
  2. Gradient w.r.t. input X: HardTanh-clipped (F - X) clipped to [-1, 1] (Eq. 6/7), to stop gradient magnitudes exploding through the chain rule.
  3. Adaptive per-layer learning-rate scaling: dF_l = gamma * alpha_l * grad_l, alpha_l = eta * sqrt(k) / ||grad_l||_2, k = number of elements in the filter, eta = 0.1 (picked from {1, 1/2, 1/5, 1/10, 1/20}, the list is garbled in extraction, UNVERIFIED exact set). Reason: filter-gradient norms of AdderNet are 100x smaller than CNN and differ per layer (LeNet-5-BN layer 1: 0.0009 vs 0.2261; layer 2: 0.0012 vs 0.2990; layer 3: 0.0146 vs 0.4646).
  4. Variance analysis: Var[Y_adder] = sqrt(pi/2) * d^2 * c_in * (Var[X] + Var[F]) is far larger than the CNN's, hence mandatory batch norm after each adder layer.
- Training setup: MNIST LeNet-5-BN, 32x32 input, Nesterov momentum 0.9, weight decay 5e-4, cosine LR from 0.1, 50 epochs, batch 256; fully-connected layers also converted. CIFAR: 400 epochs, batch 256, first and last layers kept full-precision convolutions (like BNN practice), eta 0.1. ImageNet: ResNet-18, 150 epochs, weight decay 1e-4, batch 256.
- Accuracy rows: MNIST LeNet-5-BN: CNN 99.4 % (about 435 K multiplications + 435 K additions), AdderNet 99.4 % (about 870 K additions, almost no multiplications). Table 2 CIFAR-10 (BNN / AdderNet / CNN): VGG-small 89.80 / 93.72 / 93.80; ResNet-20 84.87 / 91.84 / 92.25; ResNet-32 86.74 / 93.01 / 93.29. CIFAR-100: VGG-small 65.41 / 72.64 / 72.73; ResNet-20 54.14 / 67.60 / 68.14; ResNet-32 56.21 / 69.02 / 69.74. ImageNet (Table 3) ResNet-18 top-1: BNN 51.2 %, AdderNet 67.0 %, CNN 69.8 % (prose says 66.8 %, a discrepancy inside the paper); ResNet-50 74.9 % vs 76.2 %. Fashion-MNIST: not reported. Latency: LeNet-5 about 1.7 M cycles vs 2.6 M on a VIA Nano 2000 (float multiply 4, add 2). No energy figure for the adder layers beyond op counts.

## 5. Why the gate/LUT training works: what is reliable and what is fragile (synthesis across the papers)

1. Relaxation, not estimator: [1], [2] use an exact expectation over independent Bernoulli inputs and a softmax over gate types; no STE. The LUT papers use ordinary quantised nets with STE only for the activation quantiser; the "gate" is then learned as a float function and enumerated exactly. Both avoid hard stochastic sampling.
2. Initialisation decides depth: [2] shows Gaussian logits cap depth at about 6 layers (8.8 points lost, Fig. 7 unstable) and z[A] = 5 residual init removes the cap. Sweep result: z[A] >= 2 works on MNIST, z = 5 recommended for deep CIFAR nets. The LUT family handles depth with skip connections inside the sub-network (NeuraLUT, S=2) or hidden across the whole tree (Assemble).
3. Temperature: output popcount divided by tau; tau scales with sqrt(outputs per class); too small tau saturates softmax, too large flattens. Values 6.5 to 450 in [2], 1/0.01 to 1 in [1] (they use the inverse convention).
4. Optimiser: Adam/AdamW with a large learning rate (0.01-0.02) for logit parameters; SGD is poor [1]. Weight decay on logits helps (+1 point on CIFAR) [2].
5. Convolution: sharing the tree's gate choices across positions and taking 8-leaf trees (3 learnable levels) makes receptive fields larger than 2 inputs while keeping 2-input hardware gates. Random connectivity [1] caps CIFAR-10 at about 62 %.
6. OR pooling (max t-conorm) is worth 3.5 points and is cheap (an OR gate / a max).
7. Teacher: [2]'s larger CIFAR models use a CNN teacher on class scores; the smaller ones do not.
8. Seed and connection sensitivity: random fixed wiring makes small models vary (MNIST S: +-0.31) [2]; NeuraLUT-Assemble replaces random wiring by learned grouping (dense train, prune, retrain) [3e]; PolyLUT-Add NID is seed-sensitive [3c].

## 6. Mapping to an inference chip with table lookups only (no multiplies)

- [1]/[2] gate nets export as 4 bits per gate (a 2-input gate is a 4-entry truth table; 4 bits identify it among the 16 functions) and a wiring list. A gate-tree kernel of depth 3 (8 inputs, 7 gates) can also be collapsed into one 256-entry x 1-bit table (UNVERIFIED as a statement from the papers; it follows from the definition and the papers state that trees reduce memory accesses). Class score = popcount of the output group.
- [3b]-[3e] export as 2^(beta F)-entry tables; with beta=1, F=6 that is 64 entries x 1 bit per unit (Assemble MNIST). Per-sample inference = gather inputs, index, read.
- Conv weight sharing in a LUT setting means one table per output channel reused at every position (the same sharing [2] uses for gates). None of [3a]-[3f] does convolution on images.
- Energy: no paper in this set reports energy in joules. Only gate/LUT counts, latency (ns) and FPGA resources; those are the numbers to quote (labelled as reported, not energy).

## 7. Easiest to reimplement in PyTorch on CPU, in a few hours

Rank by effort:
1. [1] difflogic-style dense layer (about 1 hour): fixed random index tensors a_idx, b_idx of shape [n_out]; logits parameter [n_out, 16]; forward: a = x[:, a_idx], b = x[:, b_idx], compute the 16 formulas from Table 1 stacked into [batch, n_out, 16], weight by softmax(logits), sum. GroupSum head + temperature + cross-entropy. Adam lr 0.01, batch 100. MNIST small (6 layers x 8 000) is feasible on CPU; expect hours for the 200 epochs the authors used, but 20-30 epochs already gives the ballpark (my estimate, not from the paper, ESTIMATED).
2. Add residual init (one line: logits[:, 3] = 5, others 0, with the paper's id 3 = "A"). Enables 8+ layers.
3. [2]-style conv tree layer (2-3 hours): for each output channel pick (channel, dy, dx) triples for 2^d leaves from the receptive field (2 channels only), gather by unfold, apply the shared tree of relaxed gates along the gather dimension, OR-pool with max. Plain PyTorch will be 10-100x slower than the authors' fused kernels (ESTIMATED), so do MNIST first (M-size model with 1 input bit), not CIFAR.
4. [3a]-[3d] need Brevitas-like quantisers with learned scales and straight-through rounding plus an enumerate-and-tabulate export. About half a day including a correct exporter. The export is trivial and exact once the quantised network is done, and the result is a truth table directly.
5. [3f] TreeLUT: xgboost + a few dozen lines to quantise leaves. Fastest to get to about 96-97 % MNIST but it tops out there (MEASURED by the paper, 96.6 %) and trees are not CNN-like.
6. [4] AdderNet: simple (a cdist-like L1 conv) but not table-lookup, see Section 4.

Recommended path for the project goal (CNN-like accuracy, table lookups, GPU-trained): implement 1 + 2 first and measure the soft-vs-hard gap on MNIST; then 3 (gate-tree convolution with OR pooling) as the CNN-like component. Fall back to [3e]-style trees of 6-input 1-bit tables if 4-bit gate truth tables are too fine-grained for the chip.

## 8. Gaps and caveats

- No Fashion-MNIST number in any of the nine papers; CIFAR-10 only in [1], [2], [4]. If Fashion-MNIST is needed it must be run locally.
- [2]: epochs/steps for the final models are not stated in the text I read (UNVERIFIED); Table 6 and the text disagree on the size parameter k of model G (2 048 vs 2 560).
- [1]: MNIST binarisation threshold not stated in the text read (UNVERIFIED).
- PolyLUT-Add LUT count for the MNIST Table III row and several Table II/IV accuracy-to-row mappings are UNVERIFIED because of PDF table extraction.
- Energy figures: none in [1], [2], [3a]-[3f]; do not quote any.
- LogicTreeNet code is in the difflogic library (github Felix-Petersen/difflogic) per the paper; I did not check the repo.
- Not read: DWN (Differentiable Weightless Neural Networks, Bacellar et al. 2024), which appears in the tables above as MNIST 98.77 % (45 ns) [2] / 97.8 % (2 092 LUTs, 9.2 ns) [3e]; the two papers quote different DWN configurations. It is the closest direct "learn the table contents with a gradient estimator" competitor and is worth a follow-up read.

Related: [Notes index](INDEX.md)
