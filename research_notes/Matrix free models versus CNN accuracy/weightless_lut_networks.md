# Weightless / LUT neural networks as multiplier-free classifiers

SOURCE-ACCESS WARNING (read first): in this session the proxy blocked arxiv.org, ar5iv, utexas.edu (WebFetch: ENOTFOUND; curl: 403). I could NOT open any paper PDF or table directly. Only github.com pages were fetchable. All paper numbers below come from the web-search tool's summaries/snippets of those papers (secondary extraction, column labels sometimes unclear). Treat every paper number as "reported via search snippet, not verified against the table". Anything marked UNVERIFIED-MEMORY is from my background knowledge and not from a source this session. Nothing below is a first-hand read of a results table except the DWN GitHub README/example.

Citation correction: the brief lists "ULEEN arXiv 2203.01479". Search results show 2203.01479 is "Weightless Neural Networks for Efficient Edge Inference" (BTHOWeN, Susskind et al.), and ULEEN is arXiv 2304.10618. 

## Which methods reach CNN-level accuracy (about 91% Fashion-MNIST, 99% MNIST, 80%+ CIFAR-10), and with how much memory?

### Takeaway
None of the LUT/weightless methods I could find numbers for reaches CNN level on all three. MNIST tops out around 98.3% (DWN, ULEEN ASIC 98.46%) vs 99%+ CNN; Fashion-MNIST ~89% (DWN) vs ~91%; CIFAR-10 ~57-58% for DWN/PolyLUT-class models, far below 80%. Only LUTNet-style binarized-CNN variants reach the mid-80s on CIFAR-10, and those are CNN-structured with residual binarization. Memory in KB was not found for DWN or ULEEN on MNIST.

### Cited Findings
- DWN (arXiv 2410.11112) Table 2, MNIST FPGA: DWN variants 97.1% to 98.3% accuracy with about 692 to 4,082 LUTs; the smallest row "DWN (n=6; sm) 97.1%, 692 LUTs". PolyLUT and NeuraLUT listed at 96% with 70,673 and 54,798 LUTs — [search summary of arXiv 2410.11112](https://arxiv.org/pdf/2410.11112)
- DWN Fashion-MNIST: DiffLogicNet 87.44%, DWN (n=6) 89.01%, DWN (n=2) 89.12% (search snippet, column labels not visible, assumed accuracy) — [arXiv HTML 2410.11112](https://arxiv.org/html/2410.11112)
- DWN CIFAR-10: DiffLogicNet 57.29%, DWN (n=6) 57.42%, DWN (n=2) 57.51%; authors claim better efficiency "excluding CIFAR-10" — [arXiv HTML 2410.11112](https://arxiv.org/html/2410.11112)
- A third-party 2026 comparison lists DWN CIFAR-10 57.4%, ~20,837 LUTs, 276 MHz, 14.5 ns; FPGN 58.1%, 15,336 LUTs, 5.7 ns — [FPGN arXiv 2607.08427](https://arxiv.org/pdf/2607.08427)
- BitLogic benchmark: DWN 57.42-57.51% on CIFAR-10; PolyLUT 53.02% +/- 0.16% at largest width; BitLogic best 58.06% — [BitLogic arXiv 2602.07400](https://arxiv.org/pdf/2602.07400)
- ULEEN (FPGA, Zynq Z-7045): 96.2% MNIST at 14.3 M inferences/s vs FINN 95.83%; ULEEN 45 nm ASIC 98.46% vs 99.35% for a quantized Bit Fusion model — [search summary, ULEEN arXiv 2304.10618](https://ar5iv.labs.arxiv.org/html/2304.10618)
- BTHOWeN: medium MNIST model ~94.3% (about 0.3% below an MLP), ~16% of MLP energy; one third-party write-up says exceeding 95% — [BTHOWeN arXiv 2203.01479](https://arxiv.org/pdf/2203.01479) (via search summary)
- NeuraLUT (2403.00849) Table III: NeuraLUT HDR-5L MNIST 96%, 54,798 LUTs, 431 MHz, 12 ns; PolyLUT 96%, 70,673 LUTs, 16 ns — [NeuraLUT](https://arxiv.org/pdf/2403.00849)
- PolyLUT-Add (2406.04910) HDR MNIST: 96.5% and 96.6% (fan-in 6x2, 6x3), 6 cycles at 378 MHz; 2.0-13.9x fewer LUTs and 1.2-1.6x lower latency than PolyLUT at similar accuracy — [PolyLUT-Add](https://arxiv.org/pdf/2406.04910)
- NeuraLUT-Assemble (2504.00592) Table IV: itself 97.9% MNIST, 5,070 LUTs, 2.1 ns; PolyLUT-Add 96%, 14,810 LUTs, 10 ns; PolyLUT 97.5%, 75,131 LUTs, 17 ns. Note PolyLUT baseline conflicts (96% vs 97.5%) between papers — [NeuraLUT-Assemble](https://arxiv.org/pdf/2504.00592)
- LogicNets CIFAR-10: one paper reports 72.3% with under 0.3M logic gates; another 64.74% for a co-designed variant (configs differ, source papers not identified) — [FPGN comparison search result](https://arxiv.org/pdf/2607.08427)
- LUTNet targeted a binarized ReBNet-style CNV net on CIFAR-10; FPGN reports its own 4-bit residual-binarized variant at 84.42%, and says LUTNet's slightly higher accuracy relies on residual binarization — [FPGN](https://arxiv.org/html/2607.08427), [LUTNet](https://arxiv.org/pdf/1904.00938)
- TreeLUT (2501.01511): evaluated on MNIST, JSC, NID; LUT-only, no BRAM/DSP. FQTree paper lists TreeLUT JSC 75.6% at 2,234 LUTs / 3 cycles and 74.6% at 796 LUTs / 2 cycles. TreeLUT MNIST numbers not retrieved — [TreeLUT](https://arxiv.org/pdf/2501.01511), [FQTree](https://arxiv.org/pdf/2608.12140)

### Inferences
- The best matrix-free LUT numbers (about 98.3% MNIST, 89% FMNIST, 57.5% CIFAR-10) leave gaps of roughly 0.7, 2 and 22+ points to CNN targets. CIFAR-10 is the decisive weakness.
- For this repo's FMNIST target (about 91%) DWN is about 2 points short on the numbers seen.

### Gaps
- Model memory in KB for DWN, ULEEN, BTHOWeN on MNIST/FMNIST: not found (papers unreadable). 
- Exact ULEEN/BTHOWeN FMNIST and CIFAR-10 numbers: not found. TreeLUT MNIST row: not found. LogicNets/PolyLUT MNIST-FMNIST-CIFAR tables: not found.
- Energy (nJ/inference) for any method: not found, except BTHOWeN relative figures below.

## How is each trained, and is inference purely lookups/adds?

### Takeaway
Modern LUT networks (DWN, LogicNets, PolyLUT, NeuraLUT, LUTNet, TreeLUT-as-boosting) are trained with gradients (or boosting) on a GPU/CPU and then compiled to fixed tables; inference is table lookups plus thresholds/adders. BTHOWeN/ULEEN-style WNNs use Bloom-filter tables with a hash; classic WiSARD trains by counting/setting bits, but ULEEN trains with backprop.

### Cited Findings
- DWN is trained with an Extended Finite Difference (EFD) technique for approximate gradients over binary LUT values; model is interconnected lookup tables — [DWN search summary](https://arxiv.org/pdf/2410.11112)
- DWN reference code: PyTorch, requires CUDA, Adam lr 1e-2, StepLR gamma 0.1 step 14, batch 32, 30 epochs; MNIST example: inputs binarized with DistributiveThermometer(3), two LUT layers (2000 then 1000 LUTs, n=6 inputs each, first layer learnable mapping), GroupSum(10, tau=1/0.3) output — [GitHub README](https://github.com/alanbacellar/DWN), [examples/mnist.py](https://github.com/alanbacellar/DWN/blob/main/examples/mnist.py)
- BTHOWeN: counting Bloom filters, cheap hash function, Gaussian-based nonlinear thermometer encoding; ~80% less energy and ~85% lower latency than MLPs, across nine datasets average >40% error reduction and >50% size reduction vs prior WNNs — [BTHOWeN](https://arxiv.org/pdf/2203.01479)
- LogicNets repo examples: jet substructure and network intrusion detection; paper arXiv 2004.03021 — [GitHub](https://github.com/Xilinx/logicnets)
- PolyLUT extends LogicNets with polynomial functions per neuron, enumerated into LUTs — [BitLogic summary](https://arxiv.org/pdf/2602.07400)
- TreeLUT: gradient boosted decision trees compiled to LUT logic — [TreeLUT](https://arxiv.org/pdf/2501.01511)

### Inferences
- All of these fit "train on GPU, infer on chip". Inference is lookups, comparators and small adders (class score sums); no multiplies, with the caveat that PolyLUT/NeuraLUT hide multiplies inside enumerated tables (table size is exponential in fan-in x bits, so they target FPGA LUT fabric).
- Whether WiSARD-style counting alone (no gradients) is competitive: BTHOWeN's ~94-95% MNIST suggests it lags gradient-trained DWN (~98%); ULEEN's gain over BTHOWeN is attributed to backprop (UNVERIFIED-MEMORY: ULEEN uses multi-shot training with STE and pruning).

### Gaps
- Exact ULEEN training recipe and WiSARD original numbers: not read.
- Whether DWN inference includes any adders beyond popcount/GroupSum: README only says GroupSum.

## Known weaknesses

### Takeaway
Input encoding (thermometer) and wide inputs are the main costs, and CIFAR-10 accuracy plateaus near 57%.

### Cited Findings
- DWN on CIFAR-10 with a 10-bit thermometer input exceeded the training GPU memory budget in the dense-connectome variant beyond width about 4,000; "oom" entries in BitLogic's table — [BitLogic](https://arxiv.org/pdf/2602.07400)
- Reaching practical accuracy (e.g. over 90%) on complex tasks like CIFAR-10 with LUT-based DNNs is described as an open challenge — [search summary of arXiv 2601.09773](https://arxiv.org/pdf/2601.09773)
- PolyLUT-Add exists specifically to address wide inputs (added accuracy +2.7% on MNIST at A=2 but 2-3x LUT size) — [PolyLUT-Add](https://arxiv.org/pdf/2406.04910)
- An FPL 2025 H-WNN paper claims 87.72% CIFAR-10 for its own model; I could not read it, so the architecture (likely convolutional/hybrid) and memory are unknown — [FPL 2025 WNN](https://utw10244.utweb.utexas.edu/pubs/FPL_2025_WNN.pdf) (snippet only)

### Inferences
- Reaching 80%+ CIFAR-10 appears to require convolution-like structure or residual binarization, not flat LUT layers; this conflicts with a pure flat-table design.

### Gaps
- Thermometer bit cost per pixel in KB for CIFAR-10: not found. No first-hand check of the H-WNN 87.72% claim.

## Suggested follow-up
Re-run with arxiv access (or HuggingFace papers) to read Table 1/2 of 2410.11112, ULEEN 2304.10618 tables, and the H-WNN FPL 2025 paper, which is the most relevant lead for CNN-level CIFAR accuracy.
