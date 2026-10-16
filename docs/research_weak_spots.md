---
title: Research - fixing the weak spots (dreams, few-shot words, clothing)
date: 2026-10-16
tags: [research, dreams, few-shot, keyword-spotting, weightless]
---
# Research: fixing the weak spots (16 Oct 2026, morning)

Three literature searches (snippet-level only: full papers could not be fetched, so every number is "as reported in
a search summary" and several are marked unverified by the searchers). Nothing here is a drop-in recipe; the mapping to
the chip's integer hardware is ours. The ranked ideas are being tested in the chip model
(`hw/brain/experiments/month4/`).

## 1. Staged learning loses ~6 points on clothing (dreams treat bits as independent)

- **k prototypes per class** (competitive learning, winner takes the update; a dream picks a prototype, then draws bits
  from that prototype's rates): independence only has to hold inside a cluster. Cost k x counters. Multi-prototype HD
  classifiers beat single-prototype ones (Rahimi et al. 2018, [arXiv 1812.05705](https://arxiv.org/pdf/1812.05705)); no
  replay result found.
- **Tiny exemplar buffer** (5-20 typical codes per class, [TEAL](https://arxiv.org/abs/2407.00673); survey:
  [Masana et al.](https://arxiv.org/pdf/2010.15277), herding vs random depends on the method). ~2.3 kbit per class as sparse index lists.
- **Cue-and-complete dreaming** (start from a stored code, drop ~10-20% of its bits, re-draw them from the class rates).
- **Willshaw pair tables** ([Simas et al. 2022](https://arxiv.org/pdf/2207.04827v1)): strongest correlation model that
  stays add-and-compare, but 1 bit per bit pair; likely too dense at 5% active bits.
- Brain: sleep-like replay with local Hebbian rules recovers forgotten tasks
  ([Tadros et al., Nat. Commun. 2022](https://www.nature.com/articles/s41467-022-34938-7)); replaying at a higher feature
  level keeps correlations ([van de Ven et al. 2020](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7426273/)).

## 2. New spoken words from 1-5 recordings (12-22%)

- Every successful few-shot keyword-spotting system uses an embedding learned on many other words
  ([Parnami & Lee 2020](https://arxiv.org/pdf/2007.14463), [Rusci & Tuytelaars 2023](https://www.isca-archive.org/interspeech_2023/rusci23_interspeech.html),
  [Chameleon 2025](https://arxiv.org/pdf/2505.24852)); raw features with a prototype give no such guarantee.
- Virtual examples from one recording by **joint** speed and spectral warp (0.9 / 1.1 + matching row shift) beat
  independent blurs ([Povey et al. 2015](https://www.danielpovey.com/files/2015_interspeech_augmentation.pdf)).
- **Match-time search** instead of blurring: max over row offsets -2..+2 (vocal-tract length ~ a shift on a log axis) and
  over a few frames of time slack, keeping the stored pattern sharp
  ([VTL-warped features 2025](https://arxiv.org/pdf/2501.03523), banded DTW [Wilkinghoff 2024](https://arxiv.org/html/2404.14903v2)).
- Reuse the old words as a fixed embedding (describe a new word by its match to known words / shared sub-word detectors).

## 3. Clothing 84.8 vs network 87.3

- Reported weightless / Tsetlin results are 91-94% but with far bigger models
  ([Convolutional TM 91.5%](https://arxiv.org/pdf/1905.09688), [TM composites](https://arxiv.org/pdf/2309.04801),
  [ULEEN](https://arxiv.org/pdf/2304.10618), [DWN](https://arxiv.org/pdf/2410.11112)): the gap is mostly capacity and encoding richness.
- Cheap ideas: thresholds at pixel-histogram quantiles (distributive thermometer), a coarse-scale centre-surround
  channel (larger window), a second small table on a different encoder with scores summed (+1-2 for 2x memory),
  averaged-perceptron table.

Related: [Research: few-shot class-incremental](research_fewshot_class_incremental.md), [Project memory](PROJECT_MEMORY.md), [Docs index](INDEX.md)
