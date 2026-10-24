---
title: Paper notes - Tsetlin machines
tags: [l, research, papers]
---

# Paper notes - Tsetlin machines

Read in full from the arXiv PDF text (24 Oct 2026), plus the public reference code of the Fuzzy-Pattern TM
(raw files from github.com/BooBSD/FuzzyPatternTM, branch main). Numbers are quoted as printed in the papers; they are
**reported by the authors, not reproduced by us** (label: REPORTED). "DERIVED" = computed by us from the paper or code.
"UNVERIFIED" = not found in the paper text. Page numbers are arXiv PDF pages.

Papers covered (arXiv ids): (1) Fuzzy-Pattern TM, 2508.08350 (FPTM); (2) Convolutional TM, 1905.09688 (CTM);
(3a) TM Composites, 2309.04801; (3b) Composites toolbox, 2406.00704; (3c) Drop Clause, 2105.14506;
(3d) Coalesced TM, 2108.07594 (CoTM). Focused negative sampling (Glimsdal et al., ISTM 2022, pp. 73-80) has **no arXiv
version that I could find** (IEEE only, not reachable): only its abstract is known second-hand (see section 7).

## 0. Bottom line for L Cortex (read this first)

1. **Fashion-MNIST 91.5 -> 94.7 is mostly an input-encoding story, with a learner change on top, and the paper offers no ablation that separates them.**
   - Same CTM learner, 1 bit/pixel adaptive-Gaussian threshold (window 11, offset 2), 10x10 window, 8000 clauses/class:
     91.18 mean / 91.50 peak (CTM Table 4, p.11). CoTM with the same encoding: 91.18 mean (weighted), 91.83 mean / 92.0 peak (coalesced) (CoTM Tables 3 and 5).
   - Drop clause (a learner regulariser, same encoding): 92.5 (Drop Clause Table 5/6).
   - Composite of 4 TMs that differ **only in how the image is booleanised** (threshold, 2 colour-thermometer sizes, HoG): single members 90.5-91.1, team 93.0 (Composites Table 2, p.6) = +1.9 points from encoding diversity alone.
   - FPTM with a **59,584-bit multi-scale, multi-orientation, quantile-thermometer code** (DERIVED from the repo code, section 1.3): 92.18 with **2 clauses/class**, 93.19 with 20, 94.68 with 8000 + 6x augmentation (FPTM Table 4, p.7). Two clauses per class on the rich code beat 8000 clauses/class on the 1-bit code, so clause count and the classic convolution are not the lever.
   - Caveat: FPTM also changes the learner (fuzzy/saturating-popcount clause, deterministic Type Ia, size cap L). The paper never runs a standard TM on its own encoding, so the split is **UNVERIFIED**. The best-supported reading: encoding gives most of the 91.5 -> 93 step; fuzzy popcount matching is what lets 2-20 clauses exploit it; augmentation + 8000 clauses give the last ~1.5 points.
2. **Reported accuracies are peak-on-test** (selected by test accuracy over epochs): CTM "Peak" row, FPTM repo comments "Best accuracy: 93.59% after 857 epochs" next to the paper's 93.19%. Treat 94.68 and 91.50 as optimistic by an unknown amount (UNVERIFIED size).
3. **None of the six papers gives per-class accuracy or a confusion matrix for Fashion-MNIST** (grep for shirt/confusion/per-class finds only the dataset description). Shirt vs T-shirt is therefore not documented in any of them. CoTM gives per-class F1 only for an artificially imbalanced CIFAR-10 (Table 7, p.15).
4. **Copyable into a multiplier-free counting classifier** (details in section 8): thermometer code on raw pixels with image- or dataset-quantile thresholds; fixed integer edge kernels at 3/5/7 px in two orientations (shift-add only); sign-split thermometers (positive and negative responses thresholded separately); concatenating everything into one flat, position-specific bit vector; saturating-popcount ("fuzzy") clause scoring; 6x augmentation (zoom 0.9/1.1, rotate +-6 deg, flip). Not needed: the convolutional learner, the TA state machine.

## 1. Fuzzy-Pattern Tsetlin Machine (arXiv 2508.08350, A. Hnilov, 11 Aug 2025, single author, independent researcher, preprint v1)

### 1.1 Clause and inference
- Clause = conjunction of included literals (input bits and their negations), as in a TM. **Fuzzy evaluation**: vote starts at `c = min(LF, n_literals)` (if n_literals is 0 or > LF it starts at LF), is decremented by 1 per failed literal, clipped at 0. Vote in [0, LF]. Example in paper (p.2): LF=50, 100 literals, 15 fail -> 50-15 = 35; 80 fail -> 0; clause with 20 literals, 10 fail -> 10. LF=1 gives (nearly) the classic all-or-nothing clause.
- Code (src/FuzzyPatternTM.jl, `check_clause`): loop over included literal indices, `c -= !x[i]` for plain literals and `c -= x[i]` for negated ones, **early exit when c <= 0**. This is exactly a saturating XNOR/popcount against an include-mask. Class score = sum(positive-clause votes) - sum(negative-clause votes); prediction = argmax over classes (one-vs-rest; each class owns its clause teams).
- Inference cost per image: for every class and clause, at most min(n_literals, ...) bit tests, with early exit. Bound = classes x clauses x L. For the Fashion-MNIST "small" model: 10 x 20 x <=200 = **<=40,000 bit tests (DERIVED)**; "tiny": 10 x 2 x <=1200 = <=24,000 (DERIVED); "big": 10 x 8000 x <=30 = <=2.4M (DERIVED). No multiplications in the classifier. The booleanisation front-end does need small-integer multiply-accumulates (section 1.3). Throughput given only for IMDb: 34.5 million predictions/s, 51.4 GB/s, batch mode, all cores of a Ryzen 9 7950X3D (p.5). Fashion-MNIST inference speed: UNVERIFIED (not stated).

### 1.2 Learning (pp.2-3, code `feedback!`)
- Per training sample (x, y): feedback to class y's teams as "positive" and to every other class as "negative" (code `train!`: loops over all classes != y). Update probability per team = `(T - v)/(2T)` for positive and `(T + v)/(2T)` for negative, with `v` = clipped class vote (standard TM resource-allocation rule).
- Type Ia made **deterministic** (no random draw): for a matching clause, literals with value 1 get state +1 only if clause size < L (size cap L); literals that are 0 are decremented, deterministically, but only while state < include_limit (code comments "No random"). Type Ib: when a clause fails, `S` random literal indices get state -1 (probability of decrement = 1/S per paper, p.3). Type II as in a TM but on the negative side.
- Automata: 1 byte per TA, `states_num=256`, `include_limit` 230 (Fashion-MNIST) / 240 (CIFAR) / 200 (MNIST) in the example scripts; a TA includes its literal when its state >= include_limit.
- Hyperparameters (p.3): optimum `T ~ sqrt(CLAUSES/2) x LF` (multiclass), `T ~ sqrt(CLAUSES) x LF` (binary), "may vary by a factor of two"; `S_FPTM ~ (S_TM)^2` (empirical, "further investigation required"); `LF <= L`; fewer clauses -> larger LF. L = max literals per clause. No backprop, no multiplies in learning (random draws and counters).
- Fashion-MNIST settings (Table 4, p.7): tiny 2 clauses/class, T 80, S 1000, L 1200, LF 1200; small 20 clauses/class, T 100, S 700, L 200, LF 200; big 8000 clauses/class, T 700, S 700, L 30, LF 30. Epochs: 1,000 for all three (the "Test accuracy" statistic - peak, median, or mean - is **not defined** for Fashion-MNIST; for IMDb it is "median peak test accuracy").
- Hardware: Julia 1.11.6, AMD Ryzen 9 7950X3D, 64 GB DDR5, no GPU (p.4).

### 1.3 Booleanisation / input encoding for Fashion-MNIST
The paper says only (p.7): "convolutional preprocessing is applied during the booleanization stage and is not an inherent component of the FPTM... Several fixed convolutional kernels (3x3, 5x5, and 7x7) were used for edge detection. The resulting feature maps were thresholded based on the pixel value histogram and concatenated into a single boolean bit vector." No bit counts are given. The exact recipe below comes from the **reference code** (examples/FashionMNIST/fmnist_conv.jl and prepare_augmented_dataset.jl), so it is DERIVED from code, not from the paper text:
- Input: 28x28 Float32 image (MLDatasets scale, assumed [0,1]).
- 8 fixed convolution maps, each trimmed back to 28x28 by cropping the padding (Kp = 1, 2, 3, 1):
  - 3x3 Sobel x: `[-1 0 1; -2 0 2; -1 0 1]`, and its `rotl90` (y).
  - 5x5 x-kernel and its rotation. In the 2/20-clause script the 5x5 kernel is a **diagonal** one `[0 1 2 3 4; -1 0 2 3 3; -2 -2 0 2 2; -3 -3 -2 0 1; -4 -3 -2 -1 0]`; in the augmented-data script it is a symmetric horizontal one `[-2 -1 0 1 2; -3 -2 0 2 3; -4 -3 0 3 4; -3 -2 0 2 3; -2 -1 0 1 2]` (the two scripts differ; the paper does not say).
  - 7x7 x-kernel `[-3 -2 -1 0 1 2 3; -4 -3 -2 0 2 3 4; -5 -4 -3 0 3 4 5; -6 -5 -4 0 4 5 6; ...]` and its rotation.
  - a fourth 3x3 line detector (named "9" in the code) `[-1 -1 -1; 2 2 2; -1 -1 -1]` and its rotation. The paper mentions only three sizes; the code has these four kernel pairs.
- Bits per pixel: **raw image: 4 bits** (`x>0`, `x>q25`, `x>q50`, `x>q75`, where q are quantiles of the positive pixel values). **Each of the 8 conv maps: 9 bits** = positive side `x>0`, `x>q25`, `x>q34`, `x>q50`, `x>q75` (quantiles of the positive responses) + negative side `x<q25`, `x<q34`, `x<q50`, `x<q75` (mirrored quantiles of the negative responses, `1-p`). Total 4 + 8x9 = **76 maps x 784 = 59,584 bits per image (DERIVED; I counted 76 output lists in both scripts)**. The classifier then also uses negated literals, so 119,168 literals.
- Threshold scope: in `fmnist_conv.jl` (the 2- and 20-clause models) the quantiles are computed **per image** (inside `bools`, over that image's own positive / negative values) = adaptive, contrast-normalised thresholds. In `prepare_augmented_dataset.jl` (the 8000-clause 94.68 model) they are computed **once over the whole augmented training set** (fixed global thresholds).
- Augmentation (big model only, paper p.7 "horizontal flips, small rotations and zoom"): training set x6 = original + Zoom(0.9) + Zoom(1.1) + Rotate(-6) + Rotate(+6) (crop 28x28) + flip (code `FlipY()`, "Y because of dataset orientation") = 360,000 images (DERIVED).
- MNIST example (examples/MNIST/mnist.jl): plain 4-bit thermometer `booleanize(x, 0, 0.25, 0.5, 0.75)` (4 x 784 = 3,136 bits), 20 clauses, T 20, S 200, L 150, LF 75; the repo README shows a 98.56% curve for this 20-clause MNIST model (an image in the README; the number is in the image alt-text, not in the paper: UNVERIFIED in paper).
- Not present: no multi-scale pyramid, no coordinates, no colour handling in Fashion-MNIST; the "multi-scale" is the 3/5/7 kernel sizes, the "adaptive" part is the per-image or global quantile thresholds.

### 1.4 Model size
- Paper: IMDb binary model, 12,800 input bits x 2 (negated) x 2 (pos/neg) x 1 byte = **50 KB** (p.5). Fashion-MNIST model size: **not given in the paper (UNVERIFIED)**.
- DERIVED from code (1 byte per TA; four UInt8 matrices of `clause_size x clauses/2` per class = 2 x 59,584 x clauses bytes per class): training state = 2.4 MB per class for 20 clauses (23.8 MB for 10 classes); 0.24 MB per class for 2 clauses. **Deployed model** only needs the included-literal index lists (UInt16), at most L per clause: tiny <= 10 x 2 x 1200 x 2 B = 48 KB; small <= 10 x 20 x 200 x 2 B = 80 KB; big <= 10 x 8000 x 30 x 2 B = 4.8 MB (upper bounds, assuming every clause hits its L cap).

### 1.5 Results (exact rows)
- Fashion-MNIST, Table 4 (p.7), 1,000 epochs: FPTM tiny (2 clauses/class) **92.18%**; small (20) **93.19%**; big (8,000, augmented) **94.68%**. Text (p.7): previous Composite TM 93.00% with 8,000 clauses/class -> ~400x fewer clauses at 93.19%; 20-clause model trains 1,000 epochs "in just 10 minutes on desktop CPU"; "new state-of-the-art among all TM variants"; claims to beat Inception-v3 with specialised conv filters [13] (that number is not given in this paper: UNVERIFIED).
- Code comments (examples, not the paper): 2 clauses "Best accuracy: 92.53% after 713 epochs"; 20 clauses "Best accuracy: 93.59% after 857 epochs"; 8000 clauses "Best accuracy: 94.74% after 11 epochs, Normal 94.68% test acc after 50 epochs" (so the big model converges in tens of epochs, not 1,000; training time for the big model not reported).
- MNIST: not in the paper. CIFAR-10: not in the paper; the repo script `cifar10_conv.jl` comments `CLAUSES = 20  # (69%+ acc)`, T 1600, S 1000, L 4000, LF 4000 (code comment only, UNVERIFIED).
- IMDb (for the learner story): 90.15% median peak test accuracy with 1 clause/class vs Weighted CoTM 90.18% (~50 clauses/class), 1,000 epochs; training 399 s (1 thread) / 45.5 s (32 threads) vs 14,362 s Weighted CoTM (Table 2, p.4). Noisy Amazon Sales 85.22% at 20% noise vs GraphTM 78.17%, GCN 66.23% (Table 6, p.8).
- Per-class / Shirt vs T-shirt: none.

## 2. The Convolutional Tsetlin Machine (arXiv 1905.09688v5, Granmo, Glimsdal, Jiao, Goodwin, Omlin, Berge, 27 Dec 2019)

### 2.1 Encoding
- Pre-processing (p.9): "We binarize these datasets using an adaptive Gaussian thresholding procedure with window size 11 and threshold value 2. Accordingly, the CTM operates on images with merely **1 bit per pixel**." (MNIST, K-MNIST, F-MNIST.) The text says the CTM supports multi-bit pixels but "in the present paper, we only investigate single bit representations" (p.10). Z = 1 layer for all (Table 1).
- Patch/convolution: image X x Y x Z; clause = W x W x Z filter; step d; number of patches B = B_X x B_Y with B_X = (X-W)/d + 1. **Position bits appended to every patch**: B_X + B_Y extra variables, thresholded (thermometer) coordinates, e.g. x-coordinates 1, 4, 6 -> "111", "011", "001" (p.8-9). Window W = 10 for MNIST, K-MNIST, F-MNIST; W = 2 for 2D noisy XOR (Table 1, p.9). With W=10, d=1 on 28x28: B = 19 x 19 = 361 patches; per-patch input = 100 + 19 + 19 = 138 bits -> 276 literals (DERIVED; d=1 is assumed, the step used for MNIST is not stated: UNVERIFIED).
- No multi-scale, no per-channel; no CIFAR (stated as future work, p.12).

### 2.2 Clause and learning
- Clause = AND of included literals (x_k or not x_k) of one patch; empty clause = 1 in learning, 0 in inference. Clause output over the image = **OR over all patches** (Eq. 18). Class sum = sum of positive clauses - sum of negative clauses, argmax over classes (multiclass by one TM per class). Integer clause weights optionally learnt (+1 on Type I when clause fires, -1 on Type II, min 1; Eq. 9-17), used for MNIST, K-MNIST, F-MNIST; not for noisy XOR.
- Learning: Tsetlin automata, 2N states per literal; N = 100 states per action is NOT stated here (state count UNVERIFIED). Feedback probability `(T - clamp(v,-T,T))/(2T)` (Type I, y=1) or `(T + clamp)/(2T)` (Type II, y=0). Type Ia: reinforce Include for literals = 1 in a matching clause; Type Ib: with probability 1/s push literals towards Exclude (clause=0 or literal=0); Type II: for a clause that fires wrongly, include a literal that is 0. For the CTM, the patch used for the update is **one patch drawn uniformly at random from the patches on which the clause fired**; if none fired only Type Ib applies. Negative-polarity clauses swap Type I/II.
- Hyperparameters (Table 1, p.9): clauses/class 8,000, T 10,000, s 10.0, W 10, Z 1, weighting yes (F-MNIST). MNIST: 8,000 / 10,000 / s 5.0; K-MNIST: s 10.0; noisy XOR: 40 clauses, T 60, s 3.9, W 2, no weighting. Light manual binary search. Epochs: 250, results are "single-run averages obtained from the last 100 epochs of 250" (p.9). Hardware: NVIDIA DGX-2.

### 2.3 Inference cost and size
- Cost grows linearly with clauses m and patches B (p.8). Per image F-MNIST (DERIVED): 8,000 x 10 = 80,000 clauses x 361 patches = 28.9M clause-patch tests, each an AND-compare over <=276 bits (with early exit). Time per epoch (train+test, 60k train / 10k test images): 52.2 s for 8,000 clauses on F-MNIST, 16.9 s for 250 (Table 3, p.10).
- Model size, Table 5 (p.11), "assuming 32-bit real-valued weights": TM with 4,000 class clauses 7,657 kB; **CTM 250 clauses 127 kB; CTM 8,000 clauses 2,109 kB** (same for MNIST and F-MNIST). How these were computed is not explained (UNVERIFIED). For reference Logistic Circuit (binary) 1,072 kB MNIST / 2,456 kB F-MNIST; CNN 3 conv. 8,784 kB; ResNet 19,352 kB.

### 2.4 Results (exact rows)
- Table 4 (p.11), test accuracy %: **F-MNIST: TM 90.09; CTM (Mean) 91.18 +- 0.01; CTM (95%ile) 91.39; CTM (Peak) 91.50.** MNIST: TM 98.57; CTM Mean 99.33 +- 0.0; 95%ile 99.38; Peak 99.40. K-MNIST: TM 92.03; CTM 96.08 / 96.25 / 96.31. 2D N-XOR: TM 99.12; CTM 99.99 / 100.0 / 100.0. Baselines on F-MNIST in the same table: 4-NN 85.40, SVM 89.7, Random Forest 81.6, Gradient Boosting 88.0, Simple CNN 90.7, Logistic Circuit (binary) 87.6, Logistic Circuit (real-valued) 91.3, PreActResNet-18 92.00. Human accuracy on F-MNIST quoted as 83.50% (p.9).
- Table 3 (p.10), mean test accuracy vs clauses per class (250 / 500 / 1000 / 2000 / 4000 / 8000): MNIST 98.82 / 98.98 / 99.14 / 99.22 / 99.28 / 99.33; K-MNIST 92.75 / 93.86 / 94.89 / 95.40 / 95.85 / 96.08; **F-MNIST 88.25 / 88.79 / 89.42 / 89.89 / 90.65 / 91.18**; epoch times F-MNIST 16.9 / 17.2 / 17.8 / 25.0 / 27.8 / 52.2 s.
- Text (p.11): F-MNIST passes 90.0% at epoch 9 and peaks at 91.5% at epoch 170; MNIST peaks 99.4% at epoch 234. Figure 5 is accuracy per epoch.
- CIFAR-10: none (future work). Per-class / confusion: none. Learned patterns for MNIST shown as 10x10 bit patches with `*` don't-cares and valid position ranges (Table 2, p.10).

## 3. TM Composites: plug-and-play collaboration (arXiv 2309.04801v2, Granmo, 12 Sep 2023)

- Idea: several independently trained TMs, each fed a **different booleanisation** (a "specialist"), add their class sums after normalising each by `alpha_t = max_{d,i}(c) - min_{d,i}(c)` over the data set; prediction = argmax of the sum of normalised class sums (Eq. 7-8, p.3). No retraining, no fine-tuning. Confidence = max class sum; Fig. 2 shows accuracy rising monotonically with confidence (CIFAR-100).
- Encodings (pp.4-5): "10x10 Thresholding" = OpenCV adaptive Gaussian thresholding **per colour channel**, 10x10 convolution window; "Color Thermometers" = **8-level thermometer encoding per colour channel** (ref. Buckman et al.), 3x3 and 4x4 windows; "Histogram of Gradients" = HoG features thresholded, setup reused from github.com/hudara/cifar-10 (threshold value not given in this paper). Fashion-MNIST uses the same specialist families (grey).
- Hyperparameters (Table 1, p.5), all with a literal budget of 32 [Abeyrathna 2023]: Thresholding: CIFAR-10 2K weighted clauses T 500 s 10.0; CIFAR-100 16K T 4000; **Fashion-MNIST 8K weighted clauses, T 2000, s 10.0**. Colour thermometers: 2K / 16K / **8K**, T 1500 / 12000 / **6000**, s 2.5. HoG: 2K / 16K / **8K clauses (unweighted), T 200, s 10.0**. Accuracy after **100 epochs**.
- **Table 2 (p.6), accuracy %, CIFAR-10 / CIFAR-100 / Fashion-MNIST:** 10x10 Thresholding 57.0 / 35.1 / 91.1; 3x3 Color Thermometers 62.1 / 42.7 / 90.5; 4x4 Color Thermometers 62.7 / 43.4 / 90.6; Histogram of Gradients 63.5 / 25.4 / 91.1; 10x10T + HoG 68.0 / 38.9 / 92.4; 10x10T + 3x3C 68.6 / 49.6 / 92.3; 10x10T + 4x4C 68.7 / 49.2 / 92.2; 10x10T + 3x3C + 4x4C 71.7 / 50.3 / 92.4; **10x10T + 3x3C + 4x4C + HoG 75.1 / 52.2 / 93.0**.
- The abstract's "+2 points Fashion-MNIST, +12 CIFAR-10, +9 CIFAR-100" matches the best-single vs team gaps only approximately (93.0 - 91.1 = 1.9; 75.1 - 63.5 = 11.6; 52.2 - 43.4 = 8.8); the +12/+9 are rounded versions. (A third-party summary quoted an 18-point CIFAR-10 gain from 57.0; it measures against the weakest member, not the best.)
- Inference cost: each member runs a full CTM inference; the team costs the sum (4 TMs in the best row). Model size: not given (UNVERIFIED). Per-class results: none. Hardware: not stated in text I read.

## 4. Composites toolbox (arXiv 2406.00704v2, Gronningsaeter, Smorvik, Granmo, 5 Feb 2025) - CIFAR-10 encodings

- 22 specialists, 7 booleanisation techniques (Canny edge per RGB channel, HoG with threshold >= 0.1 per element, adaptive Gaussian thresholding, adaptive mean thresholding, Otsu per channel, colour thermometers with t evenly spaced thresholds over 0-255 per channel (8-level example in Table I), **adaptive colour thermometers** = multi-level statistical thresholding (thresholds from mean +- k*sigma recursion) feeding the thermometer code), with and without horizontal-flip augmentation (50k -> 100k images). Hyperparameter search with Optuna, 50 trials x 5 epochs, 2,000 clauses (Table II/III: window 1-32, T 1-3000, s 1-10, weighted yes/no); 250 epochs, accuracy = mean of last 25 epochs; NVIDIA DGX H100.
- **Table IV (CIFAR-10, accuracy at 2,000 ... 64,000 clauses):** best single specialist 5x5 Color Thermometers 64.5 -> **75.4 +- 0.09** at 64,000 clauses; 4x4 Color Thermometers 75.1; 3x3 74.3; 5x5 Adaptive Gaussian Thresholding 57.9 -> 70.2; 10x10 Canny 48.7 -> 60.6; HoG 64.2 -> 67.5 (flat after 32k). **TM Composite (all 22 added): 79.5 / 80.6 / 81.5 / 82.2 / 82.7 / 82.8 +- 0.01** at 2k / 4k / 8k / 16k / 32k / 64k clauses per specialist. Previous best 75.1 (Drop Clause / Composites). Model size and per-image cost not given; scale = 22 specialists x clauses (UNVERIFIED as a number). No MNIST or Fashion-MNIST rows.
- Lesson: colour thermometers (more bits per channel) dominate on CIFAR-10 (62-64% with only 2,000 clauses vs ~58% for 1-bit thresholds), i.e. again bits per pixel, not the learner.

## 5. Drop Clause (arXiv 2105.14506v2, Sharma, Yadav, Granmo, Jiao; AAAI 2023 version "Drop Clause: Enhancing Performance, Robustness and Pattern Recognition Capabilities of the Tsetlin Machine")

- Learner-only change: in each epoch every clause is switched off for the whole epoch with probability p (`pi_j in {0,1}`, zero with probability p); p=0 is the vanilla TM. Dropped clauses are not evaluated or updated, so training time falls (CIFAR p=0.5: 61.83 s -> 32.58 s per epoch). Implemented in PyCUDA, 16 NVIDIA V100 GPUs for images.
- Encoding: CTM with adaptive Gaussian thresholding, "merely **1 bit per pixel per channel**" (Sect. 3.2); the discussion states the loss of colour information (3 x 8 bits -> 3 Boolean values) as the likely cause of the accuracy gap to deep networks. Window sizes: not stated in the text I read (UNVERIFIED; interpretability figure uses 8x8 patches).
- Hyperparameters: MNIST and Fashion-MNIST 8,000 clauses, T 6,400, s 5.0; CIFAR-10/100 60,000 clauses, T 48,000, s 10.0; epochs: UNVERIFIED (results "averaged over 100 runs", peak).
- **Table 5 (CTM accuracy vs drop probability p = 0 / .1 / .25 / .5 / .75):** MNIST 99.3 / 99.3 / 99.45 / 99.35 / 98.2; **F-MNIST 91.5 / 91.75 / 92.5 / 92.25 / 91.25**; CIFAR-10 69.3 / 70.5 / 73.2 / 75.1 / 72.6; CIFAR-100 35.5 / 39.5 / 42.6 / 45.2 / 40.8. Text: peak MNIST 99.45% (+-0.25), F-MNIST 92.5% (+-0.25), CIFAR-10 75.1% (+-0.4), CIFAR-100 45.2% (+-0.2); K-MNIST 97.6% (+-0.2) (footnote 3).
- Table 6: CTM (p=0) / CTM(DC) / SVM / RF / K-NN / XGB: MNIST 99.3 / 99.45 / 93.4 / 93.8 / 95.3 / 96.2; F-MNIST 91.5 / 92.5 / 84.6 / 87.5 / 85.4 / 88.4; CIFAR-10 69.3 / 75.1 / 37.5 / 48.7 / 33.9 / 47.8. Table 7 (comparison with EEV-BNN, Hybrid-ViN, AlexNet-DFA, Maxout): the PDF text extraction mis-aligns the columns, so I only trust: CTM(DC) F-MNIST 92.5, CIFAR-10 75.1, CIFAR-100 45.2; Maxout CIFAR-10 about 86.8 and CIFAR-100 about 59.52 (column assignment UNVERIFIED). Inference: **1.5 ms per image for the CIFAR-10 model on one V100** (MEASURED by authors). Robustness: MNIST-C drop 11.18 points standard CTM vs 7.7 with drop clause (Table 9). Per-class: none.

## 6. Coalesced TM (arXiv 2108.07594v1, Glimsdal, Granmo, Aug 2021)

- Learner/size change: **one shared clause pool** for all classes; a weight matrix W (clauses x outputs, integer, learnt by stochastic searching on the line: Type Ia moves weights one step away from 0, Type II one step towards 0, Type Ib leaves them) relates each clause to each class. Class score = weighted sum of clause outputs. Convolutional (CTM-style) variant used for images. "CoTM operates at a similar level as TM with half the number of clauses."
- Encoding identical to the CTM: adaptive Gaussian threshold, window 11, value 2, 1 bit/pixel (p.11). 10 repeats, mean of last 25 epochs; Tesla V100.
- **Fashion-MNIST, Table 3 (p.12), clauses/class 50 / 100 / 250 / 500 / 1K / 2K / 4K / 8K:** Weighted CTM 82.33 / 83.73 / 88.25 / 88.79 / 89.42 / 89.89 / 90.65 / 91.18; **Coalesced 86.79 / 87.4 / 88.0 / 89.20 / 89.83 / 90.00 / 90.71 / 91.18**; voting margin 625 ... 10K, s = 15.0; training time per epoch 25.1 s (50) ... 81.9 s (8K); testing 1.6 ... 6.4 s per 10k images; model size 22 / 44 / 110 / 220 / 439 / 879 / 1758 / 3516 kB.
- MNIST Table 2: Coalesced 98.33 (50 clauses, 22 kB) ... 99.29 (8K); weighted 97.86 ... 99.33. Kuzushiji Table 4: Coalesced 89.66 (50) ... 96.33 (8K); weighted 71.99 ... 96.08. **The abstract says "71.99% to 89.66% on Fashion-MNIST ... 50 clauses (22 Kb)" but those numbers are the Kuzushiji-MNIST row of Table 4; the Fashion-MNIST 50-clause pair is 82.33 -> 86.79.**
- Table 5 (p.14), CoTM with 64,000 clauses (as stated in the text): F-MNIST mean 91.83 +- 0.01, 95%ile 91.93, peak 92.0; MNIST 99.31 / 99.34 / 99.36; K-MNIST 96.65 / 96.70 / 96.71 (column alignment recovered from the text extraction; trust moderately).
- Learning speed: MNIST passes 99.3% at epoch 19 vs epoch 57 for weighted TM. CIFAR-10 appears only in the class-imbalance study (Table 7: per-class F1, e.g. airplane 0.47 CoTM vs 0.39 TM at 5,000 examples; absolute accuracy not reported). No Fashion-MNIST per-class results.

## 7. Focused negative sampling (Glimsdal et al., ISTM 2022, pp.73-80)
- No arXiv version found; IEEE Xplore only (not reachable). Second-hand abstract (search snippets, not the paper): aims to discriminate classes that are hard to tell apart; tested on NLP, image processing and reinforcement-learning tasks; "accuracy close to a vanilla TM while needing roughly 42% fewer epochs on average". Everything else (sampling rule, hyperparameters, Fashion-MNIST/CIFAR rows, per-class results): **UNVERIFIED / not read**. Relevance: it targets exactly confusable class pairs such as Shirt/T-shirt, but I could not check it.

## 8. Which encoding steps can be copied into L Cortex (counting, multiplier-free)

L Cortex constraints: sparse binary code, XNOR/popcount detectors, 8-bit counting table, no backprop, no heavy matrix. Mapping:

| Step (source) | What it is | Multiplier-free? | Evidence it matters |
|---|---|---|---|
| A. Raw-pixel thermometer, 4 levels (FPTM code: x>0, >q25, >q50, >q75 of the image's non-zero pixels) | 4 compares per pixel against 3 thresholds | yes (compare only; quantiles from a 256-bin histogram counter) | 1 -> 4 bits per pixel; Composites show 8-level thermometers beat 1-bit thresholds by 5-7 points on CIFAR-10 (Table 2 p.6; Table IV) |
| B. Image-adaptive thresholds (per-image quantiles) vs global (train-set quantiles) | contrast normalisation | yes (histogram + running count); global variant needs no per-image work | FPTM small/tiny (per-image) 92.2-93.2 with 2-20 clauses; big (global) 94.68 |
| C. Fixed oriented edge kernels: 3x3 Sobel, 5x5, 7x7, 3x3 line detector, each in x and y (rotl90) | 8 maps/image | coefficients 0, +-1..+-6: shift-add (6 = 4+2), ~144k add/shift-add per image DERIVED; no true multiply | multi-scale edges are the only big addition to the 1-bit/pixel code; the CTM learns W=10 patches instead |
| D. Sign-split thermometer on each map (>0, >q25, >q34, >q50, >q75 for positive responses; mirrored for negative) | 9 bits/pixel/map | yes | splits "dark-to-light" from "light-to-dark" edges, which separates e.g. collar/sleeve contours |
| E. Flat concatenation: 76 maps x 784 = 59,584 bits, each bit tied to a location (no weight sharing in the learner) | position-specific code | yes | the learner is NOT convolutional in FPTM; "convolution" is only in the front-end |
| F. Saturating-popcount scoring: vote = max(0, min(LF, n_lit) - mismatches), early exit at 0, include-mask size cap L | XNOR + popcount + clip | yes | enables 2-20 clauses/class; not ablated vs strict clauses on the same code |
| G. 6x augmentation (zoom 0.9/1.1, rotate +-6 deg, flip) | training only (GPU side) | n/a | 93.19 -> 94.68 is confounded with 8000 clauses, so its own share is UNVERIFIED |
| H. Position bits appended to patches (CTM) | thermometer x/y coordinates | yes | only in CTM; FPTM instead keeps one bit per location |
| I. Team of specialists, normalised score sum (Composites) | several encodings, class sums divided by (max-min) | the division by alpha_t is a one-off constant per specialist, can be a shift | +1.9 on F-MNIST, +11.6 on CIFAR-10 |

Not copyable as-is: TA state machines/random feedback (training stays on the GPU anyway), the CTM OR-over-patches (361 patches x all clauses is far costlier than one flat match), exact Optuna search.

Suggested next measurements (not done here; no experiment was run): (i) run L Cortex's counting classifier on the 59,584-bit code from section 1.3 and on the 4-bit raw thermometer alone to split encoding from learner; (ii) report bit density of the code (not stated in any paper: UNVERIFIED); (iii) report Shirt/T-shirt/Pullover/Coat confusion, since none of the six papers does.

## 9. Caveats on the sources
- FPTM is a single-author preprint (v1); all its Fashion-MNIST numbers are the author's own, peak-on-test style, and the statistic (median/mean/best) is unspecified. The paper text and the example code disagree in small ways (kernel sets, 2-clause 92.18 vs 92.53 best, epochs 1,000 vs 50 for the big model).
- CTM / CoTM / Drop-clause numbers are "mean of the last N epochs" plus a separately listed peak; the Fashion-MNIST CTM peak (91.50) is not the headline mean (91.18).
- The Composites "Fashion-MNIST 93.00" quoted by FPTM comes from 8,000 clauses per class **per specialist** and four specialists, so the "400x fewer clauses" claim compares a single FPTM against a team of four; the real ratio is ~100x on a per-specialist basis (DERIVED: 4 x 8000 / 20).

Related: [Notes index](INDEX.md)
