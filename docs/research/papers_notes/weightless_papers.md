---
title: Paper notes - weightless networks
tags: [l, research, papers]
---

# Weightless networks: DWN, ULEEN, BTHOWeN and later LUT/logic-gate work

Read in full from the arXiv PDF text on 24 Oct 2026 (pdftotext). DWN code read from the PyPI sdist torch_dwn 1.1.1 (the GitHub raw tree was reachable only for README and examples/mnist.py). Every number is quoted from the paper text; "UNVERIFIED" marks anything not found in the paper text. Hardware numbers are the papers' own FPGA/ASIC results (MEASURED by the authors with vendor tools, not by us). Lines tagged DERIVED are our arithmetic from quoted configs, not paper claims.

Sources: [DWN arXiv 2410.11112v5](https://arxiv.org/abs/2410.11112) (ICML 2024), [ULEEN arXiv 2304.10618](https://arxiv.org/abs/2304.10618), [BTHOWeN arXiv 2203.01479](https://arxiv.org/abs/2203.01479), [DWN README](https://raw.githubusercontent.com/alanbacellar/DWN/main/README.md), [DWN examples/mnist.py](https://raw.githubusercontent.com/alanbacellar/DWN/main/examples/mnist.py), [torch_dwn 1.1.1 sdist](https://pypi.org/project/torch-dwn/).

## 0. Short answer for the reader (one-layer LUT net 88.9 % at 78 KB; conv LUT net 75 %)

- DWN's Fashion-MNIST row is 89.12 % (n=2, 7.8 KiB, 2 layers x 8000 LUT-2) and 89.01 % (n=6, 31.3 KiB, 2 layers x 2000 LUT-6), both with 7 thermometer bits per pixel. So the reader's 88.9 % one-layer net is already at DWN level on accuracy; DWN's edge is size (4x to 10x smaller), not accuracy. ULEEN is 87.86 % at 262 KiB (that ULEEN row is quoted in the DWN paper, not in the ULEEN paper).
- No weightless-network paper I found reports Fashion-MNIST above 89.12 % (DWN Table 1). Nothing in the DWN/ULEEN/BTHOWeN text gets past ~89 % on this dataset; "what is needed to go higher" is therefore NOT answered by these papers for Fashion-MNIST. The only route shown to move CIFAR-10 far is convolution with learned logic (LogicTreeNet, section 5), which is not a weightless net in the strict sense.
- The three levers DWN's own ablation (Table 10) attributes accuracy to, on Fashion-MNIST: finite difference only 85.74 %; + EFD 86.88 %; + learnable mapping 87.94 %; + both 89.01 %. Learnable mapping is worth about 2.2 points, EFD about 1.1 to 1.3. Spectral regularisation is worth +1.06 (87.10 -> 88.16, different run set, Table 12).
- DWN on CIFAR-10 is weak without convolution: 57.42 % (n=6, 8000 LUTs, 10 thermometer bits, 62.5 KiB) and ULEEN 54.21 %. A conv LUT net that reaches 75 % is already far above any DWN number; what the reader's conv net lacked is probably the LogicTreeNet recipe (section 5), not the DWN recipe.

## 1. DWN: Differentiable Weightless Neural Networks (Bacellar, Susskind et al.)

### 1.1 Model
- Multi-layer network of LUT-n nodes (n inputs, 2^n binary entries). Output of last LUT layer is split into C groups and summed (popcount, `GroupSum`), divided by a temperature, softmax cross-entropy. No arithmetic between LUT layers. Inference = address formation + table read, then popcount + argmax.
- Real-valued LUT entries during training; forward uses sign (entry > 0 -> 1). Code: `luts = rand(out, 2^n)*2-1` (uniform in [-1,1]); with `clamp_luts=True` entries are clamped to [-1,1] before every training forward; layer output is binarised with a straight-through function `(x>0).float()` whose backward is identity. (torch_dwn lut_layer.py, utils.py.)
- Hidden-layer LUT size n: they use n=2 and n=6 (n=6 matches FPGA LUT-6). Paper argues VC-dimension of a LUT-n is 2^n versus n+1 for a DNN neuron, so few large LUTs beat many small ones.

### 1.2 Input encoding
- Distributive Thermometer (Bacellar et al. 2022): thresholds are data quantiles per feature (feature-wise by default), so each bit is on for an equal share of training samples. Definition (App. B): T(q) = (1[q>t1], ..., 1[q>tz]) with ordered thresholds. Code: sort each feature's training values, threshold i = value at index floor(N * i/(z+1)), i=1..z. Not uniform, not Gaussian (ULEEN/BTHOWeN use Gaussian; DWN's code also ships `Thermometer` = uniform between min and max, and `GaussianThermometer`).
- Bits per feature z used (Table 14): MNIST z=3 (lg) / 1 (sm); Fashion-MNIST z=7 (both n=2 and n=6); KWS 8; ToyADMOS 2 to 3; CIFAR-10 z=10; JSC z=200; tabular z=200. Fashion-MNIST input is therefore 784 x 7 = 5488 bits (DERIVED).
- For Table 3 (microcontroller) Fashion-MNIST uses z=3 (bit-packed, 1000+500 LUTs) or z=32 (unpacked, 220+110 LUTs) (Table 15).

### 1.3 Gradient estimator: Extended Finite Difference (EFD)
- Problem: the LUT addressing function A(U,a) is discrete. Gradient wrt table entry U_i is exactly 1 if i = address else 0 (so each sample updates exactly one entry per LUT per step). Gradient wrt an address bit a_j needs a surrogate.
- Plain finite difference: dA/da_j = A(U, a with bit j=1) - A(U, a with bit j=0). Only looks at Hamming distance 1 (7 of 64 entries for a LUT-6).
- EFD (Eq. in Sec 3.1): dA/da_j = sum over all k in {0,1}^n of  (-1)^(1-k_j) * A(U,k) / (H(k,a,j)+1)  where H is the Hamming distance between k and a excluding bit j. All 2^n table entries contribute, damped by distance. Cost O(2^n) per LUT versus O(2^(2^n)) parameters for DiffLogicNet's relaxation (18,446,744,073,709,551,616 vs 64 for LUT-6).
- Released code uses exponential decay instead of 1/(H+1): weight = alpha * beta^dist, defaults alpha = 0.5 * 0.75^(n-1), beta = 0.25/0.75 = 1/3, sign by the value of bit j (README: "improves upon the paper's version ... exponential decay instead of linear decay"). Per-entry table gradient is atomicAdd of the output gradient at the addressed entry.
- Ablation (Table 10; FD = minimal DWN): MNIST 96.15 / +EFD 96.59 / +LM 98.30 / +EFD+LM 98.31; Fashion-MNIST 85.74 / 86.88 / 87.94 / 89.01; KWS 52.33* / 52.33* / 70.24 / 71.52; ToyADMOS/car 87.73 / 88.02 / 88.52 / 89.03; CIFAR-10 48.37* / 48.37* / 55.36 / 57.42 (* one layer, so input derivative not needed and FD = EFD).

### 1.4 Learnable mapping (which input bits feed which LUT)
- Baseline (WNN, DiffLogicNet): fixed pseudo-random wiring. DWN: a matrix W of shape P x Q (P = previous layer width in bits, Q = n x number of LUTs in the layer). Forward picks for each LUT input slot the argmax over P of its column (a hard selection, exactly one bit). Backward: dW = (2x-1)^T G (x binary mapped to -1/+1, G = backpropagated gradient), dx = G softmax(W / tau_lm, dim=0)^T. Code default tau_lm = 0.001, W initialised uniform [0,1).
- At inference W is discarded: connections are fixed, zero overhead. During training W is a dense P x Q matrix (for Fashion-MNIST first layer 5488 x 12000 floats, DERIVED) - a GPU-side training cost only.
- README advice: learnable mapping in the first layer only (faster convergence, negligible accuracy difference), using it in all layers needs softmax-temperature tuning and slows training; with learnable mapping DWNs can be shallower (2 layers typical), with random mapping you need depth to mix features.
- Value: LM alone gives +2.15 (MNIST), +2.20 (Fashion-MNIST), +17.91 (KWS), +6.99 (CIFAR-10) points over FD (Table 11).

### 1.5 Learnable reduction (tiny models only) and spectral regularisation
- Learnable reduction: replaces final popcount by a decreasing pyramid of LUT layers (e.g. 64,32,16,8,4,2,1) to save circuit area for ultra-low-cost chips; Table 13 shows 1.53x to 5.14x smaller NAND2 count. Not needed for the accuracy goal.
- Spectral regularisation (Sec 3.4) - the paper's answer to instability / overfitting of free LUT tables: because only the sign of a table entry matters for the address lookup, L1/L2 pulling entries toward 0 "results in instability" (entries near 0 flip sign under tiny updates). Instead penalise the L2 norm of the Fourier (Walsh) coefficients of each LUT's pseudo-Boolean function f: spec = (1/2^n) sum_x f(x) prod_i (2x_i-1) over subsets S; computed as ||L C||_2 with a precomputed 2^n x 2^n matrix C, L the u x 2^n table matrix in [-1,1]. Effect: robustness to single-input perturbations, e.g. an unaccessed entry whose Hamming-1 neighbours all agree should take their value. Ablation Table 12 (DWN vs +SN): MNIST 97.82 -> 97.88; Fashion-MNIST 87.10 -> 88.16 (+1.06); KWS 67.17 -> 69.60; ToyADMOS 88.04 -> 88.68; phoneme 89.55 -> 89.50; skin-seg 99.65 -> 99.83; higgs 68.51 -> 72.42 (+3.91). The mnist.py README example does not use it (UNVERIFIED whether the released package implements spectral regularisation; not found in torch_dwn 1.1.1 source).
- Other stabilisers actually present (code/paper): LUT entry init U(-1,1) and clamp to [-1,1] (keeps entries near the sign boundary so they can still flip, bounded STE), temperature on the GroupSum (paper Table 14 values 1/0.03 to 1/0.7; README: "crucial for achieving high accuracy"), step-decayed learning rate down to 1e-5.

### 1.6 Training recipe (Table 14, 15)
- Optimiser: Adam (README/example: `Adam(lr=1e-2)` + StepLR gamma 0.1). Paper configs: 100 epochs, learning rate schedule 1e-2 (30 ep), 1e-3 (30), 1e-4 (30), 1e-5 (10); batch size 128 for MNIST/Fashion-MNIST, 100 for KWS/ToyADMOS/CIFAR-10, 32 to 256 for tabular. README quick example: 30 epochs, batch 32, StepLR step 14, two layers 2000 and 1000 LUT-6, learnable mapping in layer 1, `GroupSum(10, tau=1/0.3)`.
- No data augmentation except "+aug" MNIST row (ULEEN-style shifts; 98.77 %). No ensembles, no pruning in DWN.
- Fashion-MNIST configs (Table 14): DWN n=2: z=7, 2 x 8000 LUT-2, tau 1/0.061, batch 128. DWN n=6: z=7, 2 x 2000 LUT-6, tau 1/0.122, batch 128, same LR schedule. CIFAR-10: n=2, z=10, 2 x 24000, tau 1/0.03, batch 100; n=6, z=10, 1 x 8000, tau 1/0.03.
- Is the "2 x 2000" = layer 1 LUT-6 then layer 2 LUT-6 each of 2000? Yes (layers listed per Table 14); popcount then runs over the 2000 last-layer outputs split into 10 groups of 200 (DERIVED).

### 1.7 Inference operations and model memory
- Fashion-MNIST DWN n=6 (DERIVED): 2000 + 2000 = 4000 LUT-6 reads (24,000 address-bit fetches), 2000-bit popcount in 10 groups of 200, one 10-way argmax. No multiplies, no hashing. LUT content 4000 x 64 bits = 32,000 B = 31.25 KiB, matching Table 1's 31.3 KiB. Wiring (not counted in the quoted size): 24,000 index values (13 bits each for layer 1 = 12000 x 13, layer 2 12000 x 11 bits), about 36 KB, DERIVED; the MCU implementation stores six 10-bit indices per LUT in 7.5 bytes (App. E).
- n=2 version: 16,000 LUT-2 reads, 16000 x 4 bit = 8000 B = 7.8 KiB (DERIVED, matches).

### 1.8 Exact accuracy table (Table 1, Z-7045 FPGA, 200 MHz, 112 bit/cycle input)
Columns: accuracy % / parameter KiB / latency ns / throughput samples/s / energy nJ per sample / FPGA LUTs (1000s). * = could not be synthesised, hardware values approximate.

| Dataset | Model | Acc % | KiB | Lat ns | Samples/s | nJ | kLUT |
|---|---|---|---|---|---|---|---|
| MNIST | FINN | 98.40 | 355.3 | 2440 | 1.56M | 5445 | 83.0 |
| MNIST | ULEEN (aug) | 98.46 | 262.0 | 940 | 4.05M | 823 | 123.1 |
| MNIST | DiffLogicNet (xs) | 96.87 | 11.7 | 90 | 33.3M | 17.2 | 9.6 |
| MNIST | DiffLogicNet (sm)* | 97.62 | 23.4 | 95 | 33.3M | - | 19.1 |
| MNIST | DWN n=2 lg | 98.27 | 5.9 | 135 | 25.0M | 42.3 | 10.3 |
| MNIST | DWN n=6 sm | 97.80 | 11.7 | 60 | 50.0M | 2.5 | 2.1 |
| MNIST | DWN n=6 lg | 98.31 | 23.4 | 125 | 25.0M | 19.0 | 4.6 |
| MNIST | DWN n=6 lg +aug | 98.77 | 23.4 | 135 | 22.2M | 21.6 | 4.6 |
| Fashion-MNIST | FINN | 84.36 | 355.3 | 2440 | 1.56M | 5445 | 83.0 |
| Fashion-MNIST | ULEEN | 87.86 | 262.0 | 940 | 4.05M | 823 | 123.1 |
| Fashion-MNIST | DiffLogicNet | 87.44 | 11.7 | 270 | 9.52M | 119.8 | 11.4 |
| Fashion-MNIST | DWN n=2 | 89.12 | 7.8 | 255 | 10.0M | 145.4 | 13.6 |
| Fashion-MNIST | DWN n=6 | 89.01 | 31.3 | 250 | 10.0M | 90.9 | 7.6 |
| CIFAR-10 | FINN (conv BNN) | 80.10 | 183.1 | 283000 | 21.9K | 150685 | 46.3 |
| CIFAR-10 | ULEEN | 54.21 | 1379 | - | - | - | - |
| CIFAR-10 | DiffLogicNet* | 57.29 | 250.0 | 11510 | 87.5K | - | 283.3 |
| CIFAR-10 | DWN n=2* | 57.51 | 23.4 | 2200 | 468K | - | 45.7 |
| CIFAR-10 | DWN n=6 | 57.42 | 62.5 | 2190 | 468K | 3972 | 16.7 |

Source: DWN Table 1. The paper's footnote: ULEEN used augmented data for MNIST; Fashion-MNIST/CIFAR-10 ULEEN/FINN rows reuse the MNIST topologies' hardware numbers (FINN 84.36 % and ULEEN 87.86 % come from the DWN authors' retraining; the ULEEN paper itself has no Fashion-MNIST or CIFAR-10 result).
- Other DWN tables: Table 2 (xcvu9p out-of-context, MNIST) DWN n=6 sm 97.1 % 692 LUTs 2.4 ns; md 97.8 % 2055 LUTs 4.6 ns; md 97.9 % 1413 LUTs 3.6 ns; lg 98.3 % 4082 LUTs 6.0 ns; versus PolyLUT 96 % 70673 LUTs, NeuraLUT 96 % 54798 LUTs. Table 3 (Elegoo Nano ATmega328P, 2 KB SRAM, 30 KB flash, 20 MHz): Fashion-MNIST DWN accuracy-optimised 88.2 % at 16.4/s, throughput-optimised 84.1 % at 95/s, XGBoost 83.2 % at 81/s; MNIST 97.9 / 94.5 / 90.2 %. Appendix D: out-of-context at 250 MHz, 4 ns/image, 250 M images/s, fully pipelined.
- Energy/latency headline: geometric-mean energy-delay-product 2522x better than FINN and 63x better than ULEEN (abstract/intro); per-sample energy and latency in the table above (FPGA, vendor tools, authors' MEASURED/synthesis numbers).

## 2. ULEEN (Susskind, Arora et al., 2023)

### 2.1 Model
- WiSARD-style: per class a discriminator = a set of RAM nodes, each replaced by a Bloom filter (k=2 H3 hashes per filter in all selected models) over an n-bit slice of the thermometer-coded, pseudo-randomly reordered input. Class score = number of filters that fire; argmax. Single layer (no gradients through indexing/hash needed).
- Ensemble of 3 to 7 submodels with different bits-per-input, inputs-per-filter and entries-per-filter; score vectors summed across submodels. "Ensembles of small models give better accuracy than monolithic large models"; submodel accuracies can be as low as 80 %.
- Counting Bloom filters for one-shot training (smallest of the k counters incremented), bleaching threshold b picked by binary search on validation set, afterwards binarised (entries < b -> 0, else 1).
- Multi-shot training uses "continuous Bloom filters": float entries in [-1,1], forward uses unit step (x>=0 -> 1), backward treats step as identity (STE); a filter fires if the minimum of its k entries >= 0.

### 2.2 Encoding
- Gaussian non-linear thermometer: per input feature assume normal, fit mean and std on training data, for a t-bit code split the Gaussian into t+1 equal-probability regions; thresholds are the boundaries. More resolution near the centre. Table I bits per input: 2 (ULN-S), 3 (ULN-M), 7 (ULN-L) on MNIST. BTHOWeN reports 12.9 % reduction in mean error versus linear thermometer on MNIST.
- Input-to-filter mapping: fixed random permutation (reordering), shared across discriminators. No learned mapping.

### 2.3 Training (multi-shot)
- Adam, base learning rate 1e-3, weights U(-1,1), dropout p=0.5 on filter outputs, softmax cross-entropy on summed ensemble outputs, PyTorch on a Tesla M40. Epoch count and batch size: UNVERIFIED (not found in the paper text). MNIST augmentation: 9 shifted copies of each training image, +/-1 pixel horizontal and vertical.
- Pruning: after training compute correlation between each filter's output and correct class output, remove a fixed fraction (30 % used for all models) of lowest-correlation filters per discriminator, learn integer per-class biases to compensate, fine-tune with multi-shot training. Sensitivity: almost no loss to 30 %; 80 % pruning gives 97.65 % at 75.31 KiB for ULN-L.
- Why it is stable: step function with identity STE on filters whose floats are bounded in [-1,1]; since single layer there is no gradient through addresses/hashes; dropout + pruning + ensembles regularise. (The paper does not discuss instability of free LUT tables explicitly; DWN is where instability and L1/L2 failure is stated.)

### 2.4 Inference operations and memory
- Per image per submodel: thermometer encode, reorder, H3 hash (AND/OR/XOR only, no arithmetic; hash params shared by all Bloom filters in a submodel so hash computed once and broadcast to all discriminators), k=2 table lookups per filter per class, AND-reduce, popcount, add across submodels, add bias, argmax. DERIVED example for ULN-L SM0 (7 bits, 12 inputs/filter): 784x7/12 = 458 filters per class x 10 classes x 2 lookups; total across 6 submodels grows linearly.
- Table I model sizes (KiB, accuracy): ULN-S ensemble of 2: 16.9 KiB, 96.20 %; ULN-M ensemble of 3 (listed 5 submodels in the table; ensemble row reads "3"): 101 KiB, 97.79 %; ULN-L: 262 KiB, 98.46 % (submodels 25.0, 37.7, 30.2, 50.3, 43.1, 75.6 KiB; individual accuracies 88.78, 93.24, 92.44, 93.92, 90.47, 90.44 %). Note: the ULN-M and ULN-L "Ensemble" row counts in the extracted text (3, 7) do not match the number of listed submodels (5, 6); UNVERIFIED which is correct - the text says "between 3 and 6 submodels".
- Table II (Z-7045 FPGA): ULN-S 0.21 us, 14,286 kIPS, 1.1 W, 0.234 uJ (b=1) / 0.077 uJ (b=inf), 17,319 LUT, 0 BRAM, 96.20 %; ULN-M 0.29 us, 14,286 kIPS, 3.1 W, 0.887 / 0.214 uJ, 49,445 LUT, 97.79 %; ULN-L 0.94 us, 4,070 kIPS, 3.4 W, 3.148 / 0.826 uJ, 123,117 LUT, 98.46 %. FINN SFC/MFC/LFC: 95.83 / 97.69 / 98.40 %, LFC 2.44 us, 1,561 kIPS, 8.8 W, 21.5 / 5.637 uJ.
- Table III (45 nm ASIC, 500 MHz, batch 16): ULN-S 55,556 kIPS, 0.84 W, 17.5 nJ/inf, 0.61 mm^2, 96.20 %; ULN-M 55,556 kIPS, 2.58 W, 57.1 nJ, 2.09 mm^2, 97.79 %; ULN-L 38,462 kIPS, 6.23 W, 195.5 nJ, 5.22 mm^2, 98.46 %; Bit Fusion BF32 19.1 kIPS, 1.79 W, 93,589 nJ, 1.65 mm^2, 99.35 %. Single-inference ASIC latency 0.032 us (ULN-S) to 0.056 us (ULN-L).
- Table IV (software, ULN-L vs Bloom WiSARD accuracy % / KiB): MNIST 91.5 -> 98.5, 819 -> 262; Ecoli 79.9 -> 87.5; Iris 97.6 -> 98.0; Letter 84.8 -> 90.0; Satimage 85.1 -> 88.0; Shuttle 86.8 -> 99.9; Vehicle 66.2 -> 76.2; Vowel 87.6 -> 90.0; Wine 92.6 -> 98.3.
- Fig. 10 progression on MNIST (values read from text only): ULN-L reduces error 82 % and model size 68 % versus Bloom WiSARD; one-shot models cannot reach 96 % under 2 MB.
- ULEEN reports no Fashion-MNIST or CIFAR-10 row. Its Fashion-MNIST 87.86 % (262 KiB) and CIFAR-10 54.21 % (1379 KiB) appear only in DWN Table 1.

## 3. BTHOWeN (Susskind, Arora et al., 2022)

- Name: Bleached Thermometer-encoded Hashed-input Optimised Weightless Neural Network. One-shot, no gradients: counting Bloom filters (H3 hash, k hashes), bleaching threshold b chosen by binary search on a 10 % validation split (90/10 train/validation), then binarise. Bleaching values above 400 were found for some models (so counters would need ~9 bits).
- Encoding: Gaussian non-linear thermometer (same as ULEEN: t+1 equal-probability regions per feature from mean/std). Mapping: random, fixed.
- Training = one pass presenting each sample to its class discriminator; Numba JIT Python. Hyperparameter sweep (MNIST: 1008 configurations): bits per input 1 to 8; input bits per filter 28, 49, 56; entries per filter 128 to 8192 (powers of two); hash functions 1 to 6.
- Table III selected models (bits/input, bits/filter, entries/filter, hashes, KiB, test acc): MNIST-Small 2, 28, 1024, 2, 70.0, 0.934; MNIST-Medium 3, 28, 2048, 2, 210, 0.943; MNIST-Large 6, 49, 8192, 4, 960, 0.952; Ecoli 10,10,128,2, 0.875 KiB, 0.875; Iris 3,2,128,1, 0.281, 0.980; Letter 15,20,2048,4, 78.0, 0.900; Satimage 8,12,512,4, 9.00, 0.880; Shuttle 9,27,1024,2, 2.63, 0.999; Vehicle 16,16,256,3, 2.25, 0.762; Vowel 15,15,256,4, 3.44, 0.900; Wine 9,13,128,3, 0.422, 0.983.
- Table IV (Zybo xc7z020, 100 MHz, 64-bit bus; dynamic power W (total W), dynamic energy nJ/inf (total)): MNIST-Small 25 cycles, 0.195 (0.303) W, 48.75 (75.8) nJ, 15,756 LUT, 0.934; Medium 37 cycles, 0.386 (0.497) W, 142.8 (183.9) nJ, 38,912 LUT, 0.943; Large (bigger FPGA) 74 cycles, 3.007 (3.509) W, 2225 (2597) nJ, 0.952; Large* with 256-bit bus 19 cycles, 600.0 (695.6) nJ. Iso-accuracy comparators: MLP 784-16-10 846 cycles, 245 (1133) nJ, 0.946; LeNet-1 CNN 1 33,615 cycles, 19,497 (54,792) nJ, 0.947; Hashed WNN prior work 0.907.
- Claims: Medium model uses 16 % of the MLP energy, ~96 % lower latency; vs Bloom WiSARD on average 41 % less error and 51 % smaller models; no Fashion-MNIST or CIFAR-10 result in the paper (grep of the PDF text finds none).
- BTHOWeN trains nothing but counters: the "no gradient" baseline. It reaches 95.2 % on MNIST at 960 KiB; ULEEN's gradient training reaches 98.46 % at 262 KiB. That 3-point MNIST gap at a quarter of the memory is the value of multi-shot STE training plus ensembles plus pruning.

## 4. Why training free LUT tables with straight-through gradients is unstable, and what each paper does

- Only the sign of an entry matters: weight decay / L1 / L2 toward 0 cause sign flips with tiny updates -> DWN says "results in instability"; replaced with spectral (Walsh-Fourier) regularisation. DWN code additionally clamps entries to [-1,1] and initialises U(-1,1).
- Each sample updates exactly one table entry per LUT (gradient is a one-hot at the addressed entry), so rarely addressed entries get no signal and memorise: "Even very small DWNs may sometimes perfectly memorize their training data" (Sec 3.4). Spectral norm ties unaccessed entries to their Hamming-1 neighbours; EFD spreads the input-side gradient over all 2^n entries.
- Input-side gradient is only a surrogate: FD sees 7 of 64 entries; EFD all 64 with distance weights; ablation shows FD -> EFD is worth +1.1 points on Fashion-MNIST.
- Fixed random wiring wastes depth/width: learnable mapping (+2.2 points Fashion-MNIST).
- Logit scale: popcount of thousands of bits needs a temperature (tau) tuned per model or softmax saturates (DWN Table 14 uses 1/0.03 to 1/0.7; README says crucial; LogicTreeNet gives tau proportional to the square root of the number of output gates).
- ULEEN: single-layer so no gradients through lookups; clip [-1,1], dropout 0.5, pruning plus fine-tune.
- Later literature on the same STE problem for gate networks: [Fitting Multilinear Polynomials for Logic Gate Networks, 2605.08657](https://arxiv.org/abs/2605.08657) proves interaction-coefficient starvation under STE and shows Soft-Mix collapses at depth (-37.3 pp on CIFAR-10 at 12 layers) while a covariance-Jacobian method holds (-0.5 pp). [Light Differentiable Logic Gate Networks, 2510.03250](https://arxiv.org/abs/2510.03250) says vanishing gradients and discretisation error come from the parametrisation. Not directly about LUT-n, but the same failure family.

## 5. Other 2022-2026 papers with CIFAR-10 / Fashion-MNIST (search results; weightless-specific ones are scarce)

arXiv API searches (title/abstract: weightless, WiSARD, Bloom, LUT, logic gate; CIFAR; Fashion) found no other WiSARD/weightless paper with a Fashion-MNIST or CIFAR-10 table. Candidates and what they report:
- [Convolutional Differentiable Logic Gate Networks (LogicTreeNet), 2411.04732](https://arxiv.org/abs/2411.04732) (NeurIPS 2024): CIFAR-10 Table 1: LogicTreeNet-S 60.38 % (0.40 M gates), -M 71.01 % (3.08 M), -B 80.17 % (16.0 M), -L 84.99 % (28.9 M), -G 86.29 % (61.0 M). Comparators: DiffLogic Net medium 57.39 % (0.51 M), largest 62.14 % (5.12 M), FINN CNV 80.10 % (901 M), LUTNet 84.95 % (1290 M), XNOR-Net 86.28 %, BinaryNet 88.60 %. FPGA (VU13P): -B 24 ns/image, 41.6 M FPS vs FINN 45.6 us. Recipe: trees of logic gates as conv kernels, logical OR pooling, residual (identity-biased) gate initialisation, thermometer-coded inputs (S, M: 2-bit via 3 thresholds; B, L, G: 5-bit plus fixed edge/curvature detector kernels), AdamW, lr 0.02, batch 128, weight decay 0.002 / 0.001 (CIFAR), a neural-network teacher on class scores for B, L, G, softmax temperature tau 20 (S), 40 (M), 280 (B), 340 (L), 450 (G), 45k/5k train/validation split. No Fashion-MNIST row (the 2 text hits are the word "fashion").
- [Deep Differentiable Logic Gate Networks, 2210.08277](https://arxiv.org/abs/2210.08277): CIFAR-10 62.14 % at 5.12 M gates (quoted via the LogicTreeNet table, not read directly).
- [A Method for Optimizing Connections in Differentiable Logic Gate Networks, 2507.06173](https://arxiv.org/abs/2507.06173): Fashion-MNIST: trainable-connection network 87.16 % vs 87.17 % for 6 layers x 8000 gates with fixed connections, with 6x fewer gates (figure 4 text). A closely related idea to DWN's learnable mapping.
- [WARP-LUTs, 2510.15655](https://arxiv.org/abs/2510.15655): CIFAR-10 only; matches DLGN accuracy with a quarter of the parameters (5,120,000 vs 20,480,000 for the "large" MLP-style model, 50,000 steps, each step about one third of the wall-clock time); Gumbel noise in training reduces train/discrete mismatch; final accuracy numbers not extracted (figure-only) - UNVERIFIED.
- [Quasi-Weightless Transformers, 2411.01818](https://arxiv.org/abs/2411.01818), [Differentiable Weightless Controllers, 2512.01467](https://arxiv.org/abs/2512.01467): found; neither gives a Fashion-MNIST or CIFAR-10 image-classification result I extracted (the controllers paper has 0 hits for both; quasi-weightless transformer mentions CIFAR 8 times, not read in detail - UNVERIFIED).
- Depth/scaling of logic gate nets: [2607.21633](https://arxiv.org/abs/2607.21633) (IALGN, depth to 150 layers on MNIST, CIFAR-10, CIFAR-100), [2610.01069](https://arxiv.org/abs/2610.01069) (dynamic logic kernels, width scaling). Numbers not extracted - UNVERIFIED.

## 6. What the DWN/ULEEN recipe does that the reader's nets likely did not (inference, labelled)

All of this is INFERENCE from the papers, not tested here.
1. Two stacked LUT layers (LUT-6, e.g. 2000 + 2000) with the first layer's wiring learned by a softmax-argmax mapping, instead of one layer with random wiring. DWN's own ablation attributes +2.2 points on Fashion-MNIST to the mapping.
2. EFD input gradient across all 2^n entries (alpha*beta^Hamming), not plain FD or no input gradient: +1.1 points (Fashion-MNIST).
3. Quantile (distributive) thermometer with 7 bits per pixel (5488 inputs), per pixel.
4. Entries real in [-1,1], clamped each step, STE identity on the binarised output; Adam lr 1e-2 stepped x0.1 every 30 epochs to 1e-5, 100 epochs, batch 128; tuned softmax temperature on the grouped popcount (1/0.122 for Fashion-MNIST n=6).
5. Spectral regularisation (+1.06 on Fashion-MNIST in their ablation, unclear if in public code).
6. For a conv LUT net (75 % trained badly): the DWN paper has no conv model. The relevant recipe is LogicTreeNet: identity/residual initialisation, OR pooling, a teacher on class scores, temperature scaled with the square root of the number of output gates, weight decay, AdamW at lr 0.02, high-bit thermometer plus fixed edge detectors for the large models. DWN CIFAR-10 stays at 57.42 % without convolution.
7. Ceiling: DWN 89.12 % and 89.01 % are the best weightless Fashion-MNIST numbers I found; ULEEN-type ensembles (87.86 % at 262 KiB) are worse. Beyond ~89 % there is no weightless recipe in these papers; the evidence points to convolution (shared small trees/LUTs, OR pooling) plus input features such as fixed edge detectors, as in LogicTreeNet on CIFAR-10. No Fashion-MNIST number for that family was found.

## 7. Gaps / UNVERIFIED list
- UNVERIFIED: ULEEN training epochs and batch size; ULEEN ensemble sizes in Table I (extracted text inconsistent).
- UNVERIFIED: whether the public torch_dwn implements spectral regularisation (not in v1.1.1 source); DWN Fashion-MNIST/CIFAR-10 example scripts not reachable (only examples/mnist.py read).
- UNVERIFIED: WARP-LUTs final CIFAR-10 accuracies; accuracies in 2607.21633 and 2610.01069; Quasi-Weightless Transformer image results.
- Not found: any weightless-network (WiSARD/Bloom/DWN family) paper from 2022 to 2026, other than DWN, with Fashion-MNIST or CIFAR-10 rows; ULEEN and BTHOWeN papers themselves have none.
- Energy figures are the papers' FPGA/ASIC synthesis numbers (authors' tools); none MEASURED by us.

Related: [Notes index](INDEX.md)
