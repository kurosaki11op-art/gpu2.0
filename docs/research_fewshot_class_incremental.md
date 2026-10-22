---
title: Research - learning a new class from a few examples after shipping
date: 2026-10-15
tags: [research, few-shot, continual-learning]
---
# Research: learning a new class from a few examples after shipping (15 Oct 2026)

**The failure it answers.** After the chip has learned classes 0-4 from thousands of examples, one example of a new
class reaches only ~6.5% on that class (SIMULATED): old rows of the table sit near +-15 after thousands of +1 steps,
a new row gets a handful, so its score cannot compete. The literature calls this old/new bias; every few-shot
class-incremental method fixes it either by writing the new class at full scale in one shot or by normalising scores
across classes.

Numbers below are as reported in abstracts and summaries (the full papers could not be fetched from here); check the
papers before quoting them elsewhere.

| Idea | Source | Mechanism | Integer form on the chip |
|---|---|---|---|
| One-shot write of a class | C-FSCIL, Hersche et al., CVPR 2022 ([arXiv 2203.16588](https://arxiv.org/abs/2203.16588)); weight imprinting, Qi et al., CVPR 2018 ([arXiv 1712.07136](https://arxiv.org/abs/1712.07136)) | a new class's prototype = sum of its shots' codes, written straight in, no training | add a large step on the class's active bits on the first example |
| Novelty-gated learning rate | Allred & Roy 2020; Daram et al. 2020 ([doi](https://doi.org/10.3389/fnins.2020.00928)) | dopamine-like signal: learn fast when a class is new | step = W0 >> log2(n) (shifts) |
| Weight aligning | Zhao et al., CVPR 2020 ([arXiv 1911.07053](https://arxiv.org/abs/1911.07053)) | scale new-class weights to the old classes' norm | per-class sum of abs weights, power-of-two shift of the score |
| Bias correction | Wu et al. (BiC), CVPR 2019 ([arXiv 1905.13260](https://arxiv.org/abs/1905.13260)); CALA ([arXiv 2412.12654](https://arxiv.org/abs/2412.12654)) | scale + offset on new-class scores, class-specific | a shift and an integer bias, tunable at night |
| Hippocampus + cortex | FearNet, Kemker & Kanan, ICLR 2018 ([arXiv 1711.10563](https://arxiv.org/abs/1711.10563)) | fast episodic store answers recent classes, sleep moves them into the slow store, a gate picks | stored examples score by overlap; compare-based gate; night rehearsal |
| Synaptic scaling | Hofmann & Maeder, IEEE TNNLS 2022 | homeostatic down-scaling frees headroom | night pass shifts old rows down |
| Bleaching (weightless nets) | WiSARD bleaching ([arXiv 2005.00887](https://arxiv.org/abs/2005.00887)); ULEEN ([arXiv 2304.10618](https://arxiv.org/abs/2304.10618)) | counters thresholded at b to break saturation ties | our per-bit counters as thresholded prototypes |

Ranking for L: (1) one-shot imprint with a 1/n step, (2) per-class norm alignment, (3) hippocampus gating,
(4) night down-scaling + bias calibration, (5) counter prototypes. Caution from the literature: imprinting at full
scale can swing the bias toward new classes, so measure old and new accuracy separately. Tested in
`hw/brain/experiments/month4/fewshot_fixes.py`.

Related: [Prior art for L Cortex](prior_art_cortex.md), [Project memory](PROJECT_MEMORY.md), [Few-shot note](../hw/brain/experiments/month4/fewshot_saccades.md)
