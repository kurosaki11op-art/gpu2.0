---
title: Research notes - binary hashing local learning
tags: [l, research, notes]
---

# Binary/ternary/low-bit nets, hashing & sparse-coding classifiers, backprop-free learning vs CNN accuracy at tiny memory

Method note: direct fetches of arxiv.org, ar5iv, huggingface.co and alphaxiv failed (DNS) in this session. Only github.com pages were fetched in full. All other numbers below come from web-search result summaries that quote the papers; treat as "second-hand quote of the paper", not read in full. Items from my own memory are tagged UNVERIFIED. Time frame: to Oct 2026.

## Key question 1: Best Fashion-MNIST accuracy for tiny models (<100 KB) and for backprop-free methods

### Takeaway
Small supervised CNNs (<100K params, i.e. ~100 KB at 8 bit) reach ~92.5% on Fashion-MNIST (F-MNIST) in the official benchmark table; the best result of any size in that table is 96.7% (WRN40-4, 8.9M params, augmentation). For backprop-free methods, the only F-MNIST numbers I found are ~87% (Forward-Forward variant), ~84% (supervised Hebbian) and ~75% (shallow SoftHebb, fully connected); no verified conv backprop-free F-MNIST number found.

### Cited Findings
- Official F-MNIST benchmark table (submitted, not verified by maintainers): #1 WRN40-4 8.9M params, standardisation + random crops + flips = 96.7%; WRN-28-10 + Random Erasing 96.3%; WRN-28-10 95.9%; DenseNet-BC 768K params 95.4%; MobileNet (flips) 95.0%; ResNet18 94.9%; 2 Conv + 3 FC ~500K params with augmentation + BN 93.4% — [zalandoresearch/fashion-mnist](https://github.com/zalandoresearch/fashion-mnist)
- Same table, tiny models: "2 Conv, <100K params", no preprocessing = 92.5% F-MNIST / 99.2% MNIST (@hardmaru); 2 Conv ~113K params, normalisation = 92.2% / 99.3%; HOG + SVM = 92.6%; MLP 256-128-100, no preprocessing = 88.33% — [zalandoresearch/fashion-mnist](https://github.com/zalandoresearch/fashion-mnist)
- Original F-MNIST paper classical baselines roughly 85-90% (gradient boosting 88.0%, kNN 85.4%, SVC 89.7%) — [Xiao et al. 1708.07747 via search summary](https://arxiv.org/pdf/1708.07747)
- A 2024 MDPI paper claims 99.65% on F-MNIST with a small 3-conv CNN ("CNN-3-128") with augmentation and calls the prior best 99.1% — [MDPI Mathematics 12(20):3174](https://www.mdpi.com/2227-7390/12/20/3174). CAUTION: this contradicts the 96-97% ceiling in the benchmark table and the label noise noted elsewhere (hundreds of mislabeled items); I did not read the paper, so treat 99.65% as an unverified outlier claim (possible test-set tuning/leakage; not checked).
- Aggregator leaderboard lists 96.91 (no method/source given), plus 96.35, 96.3 — [wizwand F-MNIST](https://www.wizwand.com/dataset/fashion-mnist)
- A 2026 preprint: tensor-augmented CNN 1-layer 93.1%, 2-layer 93.7% (needs >=512 kernels, param count not seen) — [arXiv 2604.08072](https://arxiv.org/pdf/2604.08072). A 2026 PLOS ONE TinyCNN with linear self-attention, <0.5M params, 91.47% — [PLOS ONE record](https://econpapers.repec.org/RePEc:plo:pone00:0351671)
- Sparse-goodness Forward-Forward (Mar 2026 preprint): top-k goodness beats sum-of-squares goodness by 22.6 points on F-MNIST; best combined result 87.1% with a 4x2000 architecture — [search summary of arXiv preprint](https://arxiv.org/pdf/2501.09238) (summary came from a Forward-Forward results search; exact paper ID for the Sparse Goodness preprint not captured)
- Supervised Hebbian Learning: ~84% F-MNIST vs 63% for a simpler baseline — [arXiv 2203.01304](https://arxiv.org/pdf/2203.01304)
- Shallow SoftHebb, fully connected, 2000 hidden neurons: 96.94 ± 0.15% MNIST and 75.14 ± 0.17% F-MNIST (original SoftHebb theory paper numbers, quoted in the Journé et al. text) — [arXiv 2209.11883](https://arxiv.org/pdf/2209.11883)
- Mono-Forward (backprop-free, layer-local errors): 2x1000 ReLU MLP on MNIST/F-MNIST, 3x2000 on CIFAR; 200 epochs, no dropout/augmentation; claims to match or slightly exceed BP on MNIST and F-MNIST and be slightly worse on CIFAR-10/100 (exact per-dataset numbers not retrieved) — [arXiv 2501.09238](https://arxiv.org/pdf/2501.09238); independent evaluation agrees Mono-Forward matches tuned BP on its MLPs — [arXiv 2511.01061](https://arxiv.org/html/2511.01061v1)
- Forward Projection (closed form, single forward pass, no feedback; Nat. Commun. 2026): beats other local methods (random features, Local Supervision, Forward-Forward) on F-MNIST MLP, approaching BP; numbers not retrieved — [arXiv 2501.16476](https://arxiv.org/pdf/2501.16476)
- FINN benchmark of quantised nets on FPGA: F-MNIST accuracy reaching 88% for the studied quantised networks; weight bit-width mattered much more than activation bit-width — [arXiv 2102.01341](https://arxiv.org/pdf/2102.01341)
- 8-bit QAT small CNN on F-MNIST (informal GitHub study): size 0.92 MB to 0.233 MB, accuracy 88.37% to 87.30% — [GitHub study](https://github.com/yashmaniya0/Quantization-of-Image-Classification-Models)

### Inferences
- The tiny-model frontier on F-MNIST is ~92.5-93% at ~100K params (about 100 KB at 8 bit, ~12-25 KB at 1-2 bit if quantisation costs little, which I did not find measured on F-MNIST). The gap from 92.5% to 96.7% costs ~90x more parameters plus augmentation.
- Matrix-free/backprop-free results in the 75-87% range are 6-17 points below a 100K-param CNN; there is no verified evidence here that any backprop-free method has reached >=90% on F-MNIST.

### Gaps
- No 1-, 2- or 4-bit CNN accuracy on F-MNIST with memory in KB found in any source read.
- No verified conv-SoftHebb F-MNIST number found (Journé et al. do not report F-MNIST in the retrieved text).
- Exact Mono-Forward / Forward Projection F-MNIST percentages not retrieved.
- Papers with Code page itself not reachable.

## Key question 2: (a) Binary / ternary / low-bit networks on MNIST, CIFAR-10 (and memory)

### Takeaway
Binary/ternary nets lose little on MNIST (<1.5% error) and ~1-4 points on CIFAR-10 versus float CNNs, with 16-32x weight compression. Best tiny-MCU MNIST: ternary 99.45% in ~11.4 KB. Memory budgets in KB are best documented by BitNetMCU.

### Cited Findings
- BNN (weights and activations +-1), Theano: MNIST 0.96% error, SVHN 2.80%, CIFAR-10 11.40%; Torch7: MNIST (permutation-invariant) 1.40%, SVHN 2.53%, CIFAR-10 10.15% — [Courbariaux et al. 1602.02830 via search summary](https://arxiv.org/pdf/1602.02830)
- BinaryConnect (binary weights only): MNIST 1.29%, CIFAR-10 9.90%, SVHN 2.30% error (as tabulated in the BNN paper) — [Courbariaux et al.](https://arxiv.org/pdf/1602.02830); see also [BinaryConnect reviews](https://papers.nips.cc/paper/2015/file/3e15cc11f979ed25912dff5b0669f2cd-Reviews.html)
- Ternary Weight Networks (weights +1/0/-1): up to 16x compression vs float32; MNIST and CIFAR-10 accuracy close to full precision; no F-MNIST evaluation — [Li et al. 1605.04711](https://arxiv.org/abs/1605.04711)
- Ternary NN for FPGA: 97.76% MNIST, 5.37 microsecond latency, ~1.24 microjoule per image — [arXiv 1609.00222](https://arxiv.org/abs/1609.00222v1)
- BitNetMCU (CH32V003 RISC-V, 16 KB flash, 2 KB RAM; fully connected only, MNIST downscaled 16x16, QAT with straight-through estimator, rotation/affine augmentation "main factor"): 4-bit 25,216 weights (12.3 KB) = 99.02% (C engine; Python 99.01%); ternary 80-wide 93,568 bits (11.42 KB) = 99.45% (C engine 99.44%, Jan 2026); 64-wide 2-bit 11.0 KB = 99.53%; 4,512 2-bit params = 94.22%; at a 12 KB budget: 1-bit 100,416 weights, ternary 64,608, 2-bit 49,600, 4-bit 25,216, 8-bit 12,864; inference needs only additions; no F-MNIST/CIFAR — [BitNetMCU documentation](https://github.com/cpldcpu/BitNetMCU/blob/main/docs/documentation.md)
- RedBit: LeNet-5 MNIST 2-bit DoReFa costs about 0.07% accuracy; binarisation degrades significantly more than 2-bit — [arXiv 2301.06193](https://arxiv.org/pdf/2301.06193)
- QNN paper: 1-bit weights / 2-bit activations accuracy comparable to 32-bit (headline AlexNet/ImageNet) — [Hubara et al. 1609.07061](https://arxiv.org/pdf/1609.07061)
- XNOR-Net: not fetched. UNVERIFIED (memory): BWN ~32x weight memory saving, XNOR-Net ~58x conv speed-up, ImageNet top-1 ~44% (XNOR) / ~56.8% (BWN) AlexNet.

### Inferences
- Memory in KB: an N-weight net is N/8 KB at 1-bit, N/4 at 2-bit (ternary ~N*1.58/8). The 100K-weight 1-bit net is ~12.5 KB, so a CNN-class (~100K-weight) model fits in ~12-25 KB at 1-2 bit; BitNetMCU shows this is useful on MNIST but F-MNIST is unmeasured.
- All these results use backprop (STE) and multiply-free inference; they are matrix-vector products in structure (adds only), so they fail a "no matrix" rule even though they avoid multiplies.

### Gaps
- CIFAR-10 numbers for 1-4 bit best-in-class (e.g. ResNet-level 2-bit) not retrieved.
- No F-MNIST binary/ternary result with KB reported.

## Key question 3: (b) Hashing, sparse distributed, WTA, random-projection and ELM classifiers

### Takeaway
FlyHash and BioHash are evaluated mostly for retrieval (mAP), not classification; I found no verified F-MNIST classification accuracy for FlyHash/HTM. Random-feature/ELM readouts reach MNIST ~94% at 1,000 hidden and ~97.7% at 10,000 (informal), and sub-1% error with random receptive-field patches (McDonnell); F-MNIST numbers for ELM not found.

### Cited Findings
- FlyHash (Dasgupta et al. 2017): ~50 projection neurons expand to 2000 Kenyon cells through a sparse binary random projection, winner-take-all keeps the top ~5% — [bioRxiv 180471](https://www.biorxiv.org/content/10.1101/180471.full.pdf)
- Fly Bloom Filter / FlyNN classification (Sinha & Ram): per-class summary, competitive with nearest neighbour and single-pass classifiers on 70-71 OpenML datasets; no MNIST/F-MNIST accuracy retrieved — [arXiv 2008.08685](https://arxiv.org/pdf/2008.08685)
- A 2026 connectome-based test: fly hash beats k Gaussian projections at short hash length (3.1x AP@200 on MNIST at k=4), but Gaussian projections with equal arithmetic retrieve better on every dataset tested — [alphaxiv 2610.09114](https://alphaxiv.org/abs/2610.09114v1)
- BioHash (Ryali, Hopfield, Krotov 2020): sparse expansive code learned with a local Hebbian-like rule; best MNIST/CIFAR-10 retrieval mAP, especially at short hash lengths, beating deep hashing DH and UH-BNN; no classification accuracy or F-MNIST — [ICML 2020 / arXiv 2001.04907](https://arxiv.org/abs/2001.04907)
- ELM: random frozen input weights, least-squares output weights; McDonnell et al. report <1% MNIST error with ELM and random receptive-field patches — [arXiv 1412.8307](https://arxiv.org/pdf/1412.8307)
- Informal PyTorch forum ELM: MNIST 94.12% at 1,000 hidden, 97.66% at 10,000 (unverified forum post) — [PyTorch forum](https://discuss.pytorch.org/t/basic-extreme-learning-machine-pytorch-implementation/200562)
- Coates, Lee, Ng 2011: single-layer k-means features with whitened patches, many hidden nodes and dense extraction reach 79.6% CIFAR-10 (97.2% or 97.0% NORB depending on version) with a linear readout; width and dense stride matter more than the learning algorithm — [AISTATS 2011](https://proceedings.mlr.press/v15/coates11a.html)
- Ternary random features with SVM on F-MNIST (random-feature Gram matrices vs arc-cosine kernel); accuracy values not retrieved — [arXiv 2110.01899](https://arxiv.org/pdf/2110.01899)
- HTM: no source read. UNVERIFIED (memory): HTM spatial pooler reported ~95-98% MNIST in community tests, not competitive with CNNs.

### Inferences
- The consistent pattern (Coates & Ng; ELM; SoftHebb vs random) is that width + dense local patches + a good linear readout, not the exact unsupervised rule, determines accuracy.
- Binary hash codes are lossy for classification; the 2026 connectome study suggests random Gaussian projections often beat sparse fly projections at equal arithmetic.

### Gaps
- No verified F-MNIST accuracy for FlyHash, BioHash, HTM or ELM.
- Coates & Ng dictionary size (4000 features, UNVERIFIED memory) not seen in sources.

## Key question 4: (c) Backprop-free learning: Forward-Forward, SoftHebb, feedback alignment, local learning

### Takeaway
SoftHebb (multi-layer, conv, Hebbian soft-WTA, linear readout) is the strongest backprop-free vision result found: 99.4% MNIST, 80.3% CIFAR-10, 76.2% STL-10, 27.3% ImageNet. Plain Forward-Forward is 1.4% MNIST error but weak on CIFAR-10 (~56-61% accuracy per reproductions).

### Cited Findings
- SoftHebb (Journé, Garcia Rodriguez, Guo, Moraitis; ICLR 2023 oral): up to 5 hidden layers + linear classifier, no feedback/targets/errors: MNIST 99.4%, CIFAR-10 80.3%, STL-10 76.2%, ImageNet 27.3% — [arXiv 2209.11883v1](https://arxiv.org/abs/2209.11883v1); [ICLR page](https://www.iclr.cc/virtual/2023/oral/12759)
- Single conv layer + linear classifier on CIFAR-10: SoftHebb 71.10 ± 0.06%, hard WTA 62.69 ± 0.47%, random weights 63.93 ± 0.22% — [arXiv 2209.11883](https://arxiv.org/pdf/2209.11883)
- Hinton Forward-Forward (Dec 2022): MNIST test error 1.4% (about 1.1% reported with dropout / label smoothing in one blog) — [Analytics India summary](https://analyticsindiamag.com/hintons-forward-forward-algorithm-is-the-new-way-ahead-for-neural-networks/), [clay-atlas blog](https://clay-atlas.com/us/blog/2024/01/18/forword-forward-algorithm-hinton/); original paper arXiv 2212.13345 not fetched
- FF reproductions on CIFAR-10: MLP 39.3% test error (one-pass inference), CNN 44.3% error, improved CNN 18.8% error; FAUST 56.22% accuracy MLP vs BP 57.63% — [arXiv 2504.21662](https://arxiv.org/pdf/2504.21662)
- Nimmo & Mondragon 2025 (hard WTA + lateral inhibition + BCM in CNNs): MNIST 98%, STL-10 69.5% — [arXiv 2501.17266](https://arxiv.org/pdf/2501.17266)
- HebbFF: matches FF on MNIST/F-MNIST, faster, less VRAM, still below BP — [NeurIPS 2025 virtual page](https://neurips.cc/virtual/2025/124367)
- 21 goodness functions benchmarked on MNIST, F-MNIST, CIFAR-10, STL-10; several alternatives clearly beat the standard FF goodness — [search summary of arXiv 2511.18567](https://sotaverified.org/papers/251118567)
- Feedback alignment: no source read. UNVERIFIED (memory): FA/DFA typically a few points below BP on MNIST and far behind on CIFAR/ImageNet conv nets.

### Inferences
- Multi-layer unsupervised Hebbian conv features (SoftHebb) with a trained linear readout reach ~80% on CIFAR-10, i.e. ~10-15 points below a standard BP CNN (~93-95%, UNVERIFIED), and ImageNet drops to 27%: depth helps but the gap grows with data complexity.
- The soft (Bayesian) WTA update beat hard WTA by 8.4 points and random weights by 7.2 points at one layer on CIFAR-10, so a competition rule that stays differentiable-like is worth more than hard top-k.

### Gaps
- No SoftHebb F-MNIST number; original FF CIFAR-10 numbers not read; no feedback-alignment numbers read.

## Key question 5: (d) What limits a counting/Hebbian/perceptron readout vs a trained CNN, and techniques to close the gap

### Takeaway
Evidence points to (1) feature quality/width and local-patch structure, (2) readout capacity, (3) lack of augmentation/invariance, not the learning rule alone. Closing techniques with evidence: more width + dense patches, soft-WTA multi-layer Hebbian, closed-form/ELM readout, better goodness/objective locality, augmentation.

### Cited Findings
- Feature width and dense extraction matter more than the unsupervised algorithm; single-layer k-means + linear readout 79.6% CIFAR-10 — [Coates et al. 2011](https://proceedings.mlr.press/v15/coates11a.html)
- Random weights alone give 63.93% on one-conv CIFAR-10 vs 71.10% SoftHebb, so learned competition adds ~7 points over random features — [arXiv 2209.11883](https://arxiv.org/pdf/2209.11883)
- Depth: SoftHebb single layer 71.1% to five layers 80.3% on CIFAR-10 — [arXiv 2209.11883](https://arxiv.org/pdf/2209.11883)
- Random-feature readout needs very large width (ridge on random Fourier features reaches kernel score at D=10^5 on F-MNIST) — [arXiv 1910.09880](https://arxiv.org/pdf/1910.09880)
- Objective locality: layer-local classification errors (Mono-Forward) match BP on small MLPs, so a local supervised loss per layer closes the gap on MNIST/F-MNIST; weaker on CIFAR — [arXiv 2501.09238](https://arxiv.org/pdf/2501.09238)
- Goodness/objective choice: top-k goodness +22.6 points over sum-of-squares on F-MNIST FF — [sparse-goodness preprint summary](https://arxiv.org/pdf/2501.09238)
- Closed-form targets with randomised projections (Forward Projection) beat other local rules on F-MNIST MLP — [arXiv 2501.16476](https://arxiv.org/pdf/2501.16476)
- Augmentation was the main accuracy factor for low-bit MNIST nets (BitNetMCU), and top F-MNIST entries all use crops/flips — [BitNetMCU](https://github.com/cpldcpu/BitNetMCU/blob/main/docs/documentation.md), [F-MNIST table](https://github.com/zalandoresearch/fashion-mnist)
- HOG + SVM reaches 92.6% on F-MNIST with a hand-made, training-free feature extractor — [F-MNIST table](https://github.com/zalandoresearch/fashion-mnist)

### Inferences
- A hand-designed local-gradient feature (HOG) plus linear/SVM readout matches a ~100K-param CNN (92.6% vs 92.5%) with no backprop, which suggests a fixed, edge-oriented, spatially pooled feature bank is the cheapest route to CNN-level F-MNIST accuracy. Untested with a counting readout.
- Likely limits of a counting/perceptron readout: no spatial weight sharing/invariance, no learned discriminative features (generative or random features not tuned to class boundaries), low precision of table weights (the repo's own note: 5-bit table loses ~6 points vs float readout), and no augmentation. These are inferences from the cited work, not directly measured for counting readouts.
- Candidate gap-closers ranked by evidence: dense local patches + wide dictionary; multi-layer soft-WTA features; edge/HOG-like fixed features; layer-local supervised objectives; augmentation; boosting (no source read, UNVERIFIED).

### Gaps
- No source directly analysing counting/Hebbian-count readouts vs CNN.
- No boosting-based backprop-free F-MNIST result found.
- Papers with Code F-MNIST page and the original FF, XNOR-Net, BNN, TWN, BinaryConnect papers could not be opened directly (DNS failure for arxiv/huggingface/alphaxiv).

Related: [Notes index](INDEX.md), [Report](../matrix_free_vs_cnn_report.md)
