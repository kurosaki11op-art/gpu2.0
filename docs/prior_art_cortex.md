---
title: Prior art for L Cortex
tags: [spark, cortex, prior-art]
---

# Prior art for L Cortex (checked 15 Oct 2026, web search)

Purpose: know exactly what is new before anyone says "first". Short answer: **"a chip that keeps learning without
forgetting" is not new**. Our combination is, as far as this search found.

## Closest prior art

| Work | What it does | Same as ours | Different from ours |
|---|---|---|---|
| Hyperdimensional computing (HDC) continual learning: [Clo-HDnn](https://arxiv.org/html/2507.17953v1) (ASIC accelerator), [ImageHD](https://arxiv.org/pdf/2604.21280) (FPGA), [C-FSCIL](https://arxiv.org/pdf/2203.16588) (few-shot class-incremental, IBM/ETH) | class memories are sums of example vectors (hypervectors) | additive class memory: no forgetting, merge by adding, no backprop | they build long random vectors (projections); no dreams or sleep; C-FSCIL uses a backprop-trained feature extractor |
| [Intel Loihi 2 continual learning](https://arxiv.org/html/2511.01553v1) | prototype-based online learning on a neuromorphic chip | on-chip continual learning, local rules | spiking prototypes, no generative replay |
| Sleep / replay methods: [SESLR](https://awesomepapers.io/generative-models/papers/2507.02901), [replay without an offline phase](https://arxiv.org/html/2609.31630v2), [sleep-inspired replay on memristive hardware](https://doi.org/10.1145/3822454.3822474) | replay or sleep phases against forgetting | sleep and replay | software algorithms, or memristor hardware aimed at temporal context |
| [Gradient-free model merging by averaging prototypes](https://arxiv.org/pdf/2109.00150v1.pdf) | federated class-incremental learning without gradients | merging knowledge between devices without gradients | averages prototypes; no chip |
| [ETH online few-shot class-incremental learning at the edge](https://arxiv.org/pdf/2403.07851v1) | ~12 mJ per new class on a microcontroller | backprop-free learning on the edge | uses a pretrained network's features |
| Weightless / RAM-based networks: WiSARD (1981), BTHOWeN (2022), ULEEN (2023); [FPGA pyramidal WNN learning](https://pubmed.ncbi.nlm.nih.gov/12964210/) | lookup-table neurons, often on FPGAs | lookup and count, no multiplies | not aimed at continual learning; no sleep |
| Tsetlin machines, Numenta HTM | logic / sparse sequence memory | local learning | different mechanisms |

## What L Cortex adds (claims to defend, all SIMULATED so far)

1. **A surprise-gated fast table on top of additive memory**, so decisions are sharper than a sum-of-examples memory
   while old classes are still protected.
2. **Generative dreams from tiny counters** (10-bit, synaptic scaling) with **sleep that ends itself** when dreams stop
   agreeing with the day's learning; no stored examples.
3. **Everything without a multiplier or divider** (dream sampling by rejection, scores by adding table words), and
   **bit-exact RTL that places and routes on a $25 FPGA** (Tang Nano 20K) with timing met.

## What we must not claim

- Not "the first chip that learns continuously" (HDC accelerators and Loihi 2 exist).
- Not "the only design that never forgets" or "the first that merges knowledge by addition" (HDC class memories do both).
- Few-shot learning is weaker than a small neural network with 1-5 examples.
- Not "never forgets" without qualification: it holds for new classes; for a new condition of known classes (domain
  shift) the month-2 design forgets too, unless it keeps a frozen copy of its dream memory ([details](../hw/results/cortex_new_condition.md)).

## Measured against HDC (SIMULATED)

[L Cortex vs HDC](../hw/results/cortex_vs_hdc.md): after 5 stages, the chip is ahead of the best HDC variant on digits
(94.6 vs 92.4) and sound (69.4 vs 63.5) and level on clothing (78.3 vs 78.2), with ~2.3x less class memory and ~1,000x
fewer additions per example.

Related: [L Cortex redesign](cortex_redesign.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md)
