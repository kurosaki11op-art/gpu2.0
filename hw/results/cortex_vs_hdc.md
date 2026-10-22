---
title: L Cortex vs hyperdimensional computing
tags: [spark, cortex, results, prior-art]
---

# L Cortex vs hyperdimensional computing (HDC), the closest prior art (SIMULATED)

HDC continual-learning accelerators (see [prior art](../../docs/prior_art_cortex.md)) keep one long class vector per class,
the sum of its examples' hypervectors, so they also never forget and merge by adding. Script `hw/brain/hdc_baseline.py`,
numbers `hdc_baseline_<task>.json`. D = 10,000 bipolar dimensions; decision by cosine similarity.

| Accuracy after 5 learning stages (old data never shown again) | Digits | Clothing | Sound |
|---|---|---|---|
| HDC on raw pixels (random projection), bundling only | 82.8 | 68.3 | 28.9 |
| HDC on our sensory code (record encoding), bundling only | 91.4 | 75.8 | 42.9 |
| HDC on our sensory code, retrained in stages (perceptron-style, 3 passes)* | 92.4 | 78.2 | 63.5 |
| **L Cortex, integer chip model, one rule (mean of 3 seeds)** | **94.6** | **78.3** | **69.4** |
| for reference: HDC on our code retrained with all classes at once (20k examples) | 92.9 | 80.2 | 69.8 |

\* to keep run time down, staged retraining used the first 4,000 examples of each stage; bundling used all of them.

| Cost | HDC (on our code) | L Cortex |
|---|---|---|
| Class memory | 195 KB (10 x 10,000 x 16-bit) | 28 KB table + 56 KB dream counts = 84 KB |
| Item memory | 4,608 x 10,000 bits = 5.6 MB (or regenerate on the fly) | none |
| Adds per example to encode | ~246 active bits x 10,000 = ~2.5 million | ~246 x 10 = ~2,500 |
| Multipliers | none (bipolar) | none |

Reading: with the same senses, the chip is ahead of the strongest HDC variant on digits (+2.2) and sound (+5.9) and level
on clothing (+0.1), with about 2.3x less class memory and about 1,000x fewer additions per example. HDC's pure
bundling (the variant that truly never forgets) is 3-27 points behind. One seed for HDC; our numbers are a 3-seed mean
(spread under 1 point).

## Update 15 Oct: sound with the chip's own cochlea and its noise floor

Both methods on the same new sound codes (integer cochlea + noise floor; `CODES=sep_speech_floor_F64_p2.npz`,
`hw/results/hdc_baseline_speech_floor.json`, log `hw/brain/experiments/month4/hdc_speech_floor.log`): HDC retrained
in 5 stages 65.5 (63.5 before), all at once 71.2; L Cortex in 5 stages 71.2 (5 seeds), all at once 71.9 (3 seeds).
The chip stays ahead in stages by **+5.7** and is level all at once. SIMULATED.

Related: [Prior art](../../docs/prior_art_cortex.md), [Month 2 results](cortex_month2.md), [Results index](INDEX.md)
