---
title: Research notes - tsetlin and logic networks
tags: [l, research, notes]
---

# Tsetlin machines and logic-gate networks as multiplier-free image classifiers

Access note: in this session only github.com and web-search snippets were reachable. arxiv.org, neurips.cc, openreview, semanticscholar and huggingface.co all failed (DNS/proxy 403). So NO paper PDF was read in full. "Cited" numbers below come from (a) GitHub READMEs fetched in full, or (b) search-result summaries of the papers (secondary, marked SNIPPET). Everything marked UNVERIFIED is from memory or not confirmed. Re-check SNIPPET numbers against the papers before publishing.

## Reported Fashion-MNIST, MNIST and CIFAR-10 accuracy

### Takeaway
Convolutional TMs reach about 99.1-99.4% MNIST and 90-92.5% Fashion-MNIST; CIFAR-10 is the weak spot (75.1% Drop-Clause CTM, 82.8% TM Composites, both SNIPPET). Convolutional DLGN reports 86.29% CIFAR-10 with 61M gates (SNIPPET, consistent across several listings); the 2022 DLGN only about 62%.

### Cited Findings
- Original Convolutional TM paper peaks: MNIST 99.4%, KMNIST 96.31%, Fashion-MNIST 91.5%, 2D noisy XOR 100% (SNIPPET) — [search summary of arXiv 1905.09688](https://arxiv.org/pdf/1905.09688)
- pyTsetlinMachine README (single runs, binarised inputs): MNIST flat 98.07% (250 epochs); MNIST flat weighted 98.19%; MNIST 2D conv weighted 99.16% (peak 99.21%); Fashion-MNIST 2D conv weighted 90.06% (peak 90.39%) with 10x10 patches; IMDb 89.76% — [cair/pyTsetlinMachine](https://github.com/cair/pyTsetlinMachine)
- PyTsetlinMachineCUDA README: MNIST weighted 98.16%; MNIST 2D conv 99.10% (peak 99.14%); Fashion-MNIST 2D conv 90.94% at epoch 30 — [cair/PyTsetlinMachineCUDA](https://github.com/cair/PyTsetlinMachineCUDA)
- Original TsetlinMachine repo: binarised MNIST, average of 50 runs, test accuracy 98.2% after 400 epochs; training accuracy near 99.9% — [cair/TsetlinMachine](https://github.com/cair/TsetlinMachine)
- Drop Clause CTM: CIFAR-10 75.1% (±0.4), CIFAR-100 45.2% (±0.2), Fashion-MNIST 92.5% (±0.25), averaged over 100 runs (SNIPPET) — [arXiv 2105.14506](https://arxiv.org/pdf/2105.14506)
- TM Composites: reported CIFAR-10 82.8%; abstract says +2 points Fashion-MNIST, +12 points CIFAR-10, +9 points CIFAR-100 over prior TMs (SNIPPET) — [arXiv 2309.04801](https://arxiv.org/pdf/2309.04801)
- Fashion-MNIST with Composite TM 93.00% at 8,000 clauses; Fuzzy-Pattern TM 92.18% (2 clauses), 93.19% (20), 94.68% (8,000) (SNIPPET, 2025 paper) — [arXiv 2508.08350](https://arxiv.org/html/2508.08350v1)
- Coalesced TM (Glimsdal and Granmo 2021): Fashion-MNIST 71.99% (standard TM) -> 89.66% (CoTM) at 50 clauses/class, about 22 Kb memory; similar above 1K clauses/class; no CIFAR-10 accuracy found (SNIPPET) — [arXiv 2108.07594](https://arxiv.org/abs/2108.07594)
- Deep DLGN (Petersen et al., NeurIPS 2022): CIFAR-10 up to 62.14% (secondary review); MNIST model of 384,000 parameters said to match an NN needing over 22M parameters (secondary review, not paper) — [Liner review](https://liner.com/review/deep-differentiable-logic-gate-networks); paper [arXiv 2210.08277](https://arxiv.org/pdf/2210.08277) (not read)
- Convolutional DLGN (NeurIPS 2024 oral): CIFAR-10 86.29% with 61M gates, "29x smaller" than prior SOTA (SNIPPET, confirmed across arXiv/NeurIPS listings) — [arXiv 2411.04732](https://arxiv.org/pdf/2411.04732)
- Conv DLGN Table 1 baselines (SNIPPET, truncated): TTNet large 70.75% / 189M gates; FINN CNV 80.10% / 901M gates; LUTNet 84.95% / 1,290M gates; model M = 3.08M gates; model B = 16M gates (matches FINN accuracy with about 56x fewer gates); model L = 28.9M gates, 84.99% — [arXiv HTML](https://arxiv.org/html/2411.04732v1)
- A SlidesLive talk page lists 86.38% / 111M gates, conflicting with the paper's 86.29% / 61M — [SlidesLive](https://slideslive.com/39028046/convolutional-differentiable-logic-gate-networks); prefer paper figures.
- tmu repo has example scripts MNISTConvolutionDemo.py, MNISTDemoCoalesced.py, CIFAR2Demo3x3LiteralBudget.py (note "CIFAR2", a 2-class subset presumably; no accuracy given in the README) — [cair/tmu examples](https://github.com/cair/tmu/tree/main/examples/classification)

### Inferences
- Within TMs, CIFAR-10 accuracy is about 75-83%, well below CNNs but now in range of the best logic-gate CNN (86.29%). Both are far from float CNNs (above 95%, UNVERIFIED here).
- TM Fashion-MNIST results span about 90% (plain conv) to 94.7% (newest variant), so "about 91%" is a safe floor for classic CTM.

### Gaps
- Focused Negative Sampling: tmu README lists it as a feature but no accuracy numbers found; the search found no source.
- No paper tables read directly; per-model gate counts for DLGN MNIST/CIFAR and the DLGN 2022 table not obtained.
- Weighted TM paper numbers not found.

## Training method (backprop or not) and what inference needs

### Takeaway
TMs are trained without backprop or gradients: online, one example at a time, with Tsetlin Automata Type I/II feedback. DLGNs ARE trained with backprop/Adam through a continuous relaxation, then discretised into pure gate circuits.

### Cited Findings
- TM: classification is a majority vote over conjunctive clauses, half positive polarity and half negative; learning online, one example at a time, using Type I and Type II feedback, with a resource-allocation rule that stops reinforcing clauses once votes exceed a target threshold — [cair/TsetlinMachine](https://github.com/cair/TsetlinMachine)
- tmu feature list: Tsetlin Machine, Coalesced, Convolutional, Regression, Weighted, Autoencoder; extras: drop clause, literal budget, focused negative sampling, Type III feedback, sparse computation with absorbing actions; C and CUDA wrappers — [cair/tmu](https://github.com/cair/tmu)
- Inputs must be Boolean: examples binarise MNIST by threshold (75), Fashion-MNIST by OpenCV adaptive Gaussian thresholding, IMDb to unigram/bigram bits with chi-squared selection to 5,000 features, California housing up to 25 bits per feature — [PyTsetlinMachineCUDA](https://github.com/cair/PyTsetlinMachineCUDA)
- DLGN: differentiable relaxation combining real-valued logics with a continuously parameterised network, learning which of 16 two-input gates each neuron takes; trained with CrossEntropyLoss and Adam, lr 0.01; outputs via GroupSum(k=10, tau=30); for more than 6 layers raise grad_factor; needs far wider layers than MLPs because very sparse (e.g. MNIST example 5 layers x 16,000 neurons; configs up to 64,000 neurons/layer for MNIST and 1,024,000 for CIFAR-10) — [Felix-Petersen/difflogic](https://github.com/Felix-Petersen/difflogic)
- DLGN inference: eval mode discretises the net; CompiledLogicNet compiles to C for static CPU execution; PackBitsTensor for bit-packed GPU; over 1 million MNIST images per second on a single CPU core; CUDA about 50-100x faster than the Python implementation — [Felix-Petersen/difflogic](https://github.com/Felix-Petersen/difflogic)
- Conv DLGN adds deep logic-gate tree convolutions, logical OR pooling, and residual initialisations; earlier random connections capped CIFAR-10 at about 62% (SNIPPET) — [arXiv 2411.04732](https://arxiv.org/pdf/2411.04732)
- TM inference per the descriptions above is clause evaluation (AND of included literals) plus per-class vote sums; clause weights (Weighted/Coalesced) add integer weights to votes. Exact op counts were not stated in any source I read.

### Inferences
- TM inference needs bitwise AND, popcount/count and integer add (weights make it integer add, not multiply); DLGN inference needs only 2-input gates, no adds except a final popcount (GroupSum). Both are multiplier-free at inference (inference from design; the DLGN GroupSum popcount is from the README).
- DLGN trains on a GPU with backprop and heavy compute, which fits "inference on chip, training on GPU"; TM training is gradient-free but also sequential and needs many epochs.

### Gaps
- Exact per-inference operation counts (adds, bit ops) for CTM/CoTM not found in a source read.
- Whether Conv DLGN training cost is far above conventional CNNs: not confirmed (UNVERIFIED).

## Reported energy versus neural nets

### Takeaway
Energy claims exist but are vendor- or group-reported with unclear baselines; no independent replication found. Treat 52x as a microcontroller benchmark, not an ASIC/FPGA result.

### Cited Findings
- Literal Labs: 54x faster inference and 52x lower energy than neural networks, MLPerf Tiny on a roughly $30 NUCLEO-H7A3ZI-Q board with no accelerator; accuracy within ±2% of comparable NNs; models trained on its platform with open datasets on CPUs/microcontrollers (company/press claims) — [TechRadar](https://www.techradar.com/pro/50x-faster-50x-thriftier-uk-ai-startup-backed-by-arm-delivers-stunning-gains-in-performance-and-power-consumption-using-a-cheap-usd30-system-board), [Literal Labs technology page](https://www.literal-labs.ai/technology)
- Unite.ai says up to 10,000x more energy efficient; not found on company pages, so likely overstated — [Unite.ai](https://www.unite.ai/a-game-changer-for-ai-the-tsetlin-machines-role-in-reducing-energy-consumption/)
- ETHEREAL (compressed TM, STM32F746G-DISCO board, not FPGA/ASIC): over an order of magnitude lower inference time and energy than Binarized NNs, much smaller memory, model size reduced by up to 87.54% versus standard TMs with minor accuracy loss (SNIPPET) — [arXiv 2502.05640](https://arxiv.org/pdf/2502.05640)
- Dynamic TM FPGA training accelerator: 2.54x GOP/s per Watt and 6x less power than next-best comparable design (compared with other designs, not NNs) (SNIPPET) — [arXiv 2504.19797](https://arxiv.org/abs/2504.19797)
- Conv DLGN uses gate count as a proxy for chip area, and the TTNet/FINN/LUTNet gate comparison above; no energy-per-inference number found, FPGA 4 ns latency claim UNVERIFIED (not found in any result) — [arXiv 2411.04732](https://arxiv.org/pdf/2411.04732)
- Newcastle early-TM ASIC / asynchronous design papers exist but no energy-per-inference numbers were visible (SNIPPET) — [Newcastle TM paper PDF](https://www.staff.ncl.ac.uk/rishad.shafik/files/2020/06/TM_Paper2020_Converted.pdf)

### Inferences
- Energy figures cannot be put on one scale: microcontroller (Literal Labs, ETHEREAL), FPGA training (Dynamic TM), and gate-count proxy (DLGN) measure different things.

### Gaps
- No pJ/inference or uJ/inference figure for image classification on FPGA/ASIC read from a source; Newcastle TM ASIC numbers not obtained. Decision-tree/boosting-tree hardware (e.g. FPGA GBDT, Tree-based inference) was not researched: access limits and call budget.

## Weaknesses

### Takeaway
CIFAR-10 accuracy, Boolean encoding, and clause/gate count are the main limits.

### Cited Findings
- TM CIFAR-10: best found 82.8% (TM Composites), 75.1% (Drop Clause CTM) (SNIPPET, sources above).
- Booleanisation needed: images thresholded (fixed or adaptive) before TM; continuous features need many bits (up to 25 per feature in regression demo) — [PyTsetlinMachineCUDA](https://github.com/cair/PyTsetlinMachineCUDA)
- Convolutional TM training is slow in the old CPU code: conv epochs about 400-760 s versus about 8 s for flat MNIST; "Optimize convolution code" listed as open — [cair/pyTsetlinMachine](https://github.com/cair/pyTsetlinMachine)
- Standard TM drops sharply with few clauses (Fashion-MNIST 71.99% at 50 clauses/class) — [arXiv 2108.07594](https://arxiv.org/abs/2108.07594)
- DLGN: needs CUDA and a matching Toolkit; compile time can become long for large models; Python implementation slow; the library says "Patent pending"; the 2022 version stuck at about 62% on CIFAR-10 — [Felix-Petersen/difflogic](https://github.com/Felix-Petersen/difflogic)
- Conv DLGN gate count is large in absolute terms (3.08M to 61M gates) even if 29x smaller than prior logic-network SOTA (SNIPPET) — [arXiv 2411.04732](https://arxiv.org/pdf/2411.04732)

### Inferences
- For a matrix-free chip: TM (clause AND + vote) maps naturally to bit-parallel logic, but CIFAR-10 needs the composite/convolutional form; DLGN is the more accurate on CIFAR-10 but needs tens of millions of gates, which is large for a chip block.

### Gaps
- Memory in bytes for CTM CIFAR-10 models not found; booleanisation loss quantified nowhere in sources read.
- Matched-size CNN baseline accuracy (e.g. float ResNet) not read in these sources; any figure above 95% is UNVERIFIED.

Related: [Notes index](INDEX.md), [Report](../matrix_free_vs_cnn_report.md)
