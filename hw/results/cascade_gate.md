---
title: Gated cascade for the confusable clothing classes (24 Oct 2026)
tags: [l, clothing, cascade, results]
---

# Pay for the second look only when unsure (SIMULATED, Fashion-MNIST, one seed)

`hw/brain/experiments/month5/cascade.py`, log `cascade.log`. Stage 1 = the shipped L decision (slow table, look-again, 88.92%). Gate: the stage-1 answer is T-shirt, Pullover, Coat or Shirt AND the margin between its two best scores is among the smallest p% of such images. Stage 2 = counting readout trained on those four classes only, code = detector code + HOG-style edge bits + 10,000 pairwise ANDs chosen by counting (19,312 bits; table 75 KB at 8 bit, about 19 KB at 2 bit). No gradients, no multiplies.

| Share of images sent to stage 2 | Accuracy | Shirt recall | T-shirt recall | Extra active rows per image (average) |
|---|---|---|---|---|
| 0 % (stage 1 only) | 88.92 | 63.1 | 88.2 | 0 |
| 4 % | 89.40 | 65.9 | 87.4 | 59 |
| 10 % | 89.78 | 70.5 | 86.0 | 148 |
| **20 %** | **90.00** | **73.8** | 84.5 | 296 |
| 30 % / 40 % | 89.96 / 89.96 | 74.0 | 84.0 | 443 / 591 |

(Stage 2 uses about 1,481 active rows when it runs; stage 1 about 589 per view.)

**Reading.** Sending the least-sure fifth of images to the second stage gives about +1.1 points overall and +10.7 points of Shirt recall (T-shirt recall falls 3.7), for an average of about 300 more active rows, much less than the five views of stage 1. The gain is the same size as the best "always on" variants but costs far less on average. This is the first change that improves Shirt without giving up the sparse, multiply-free, small-memory character. It does not reach the CNN (91.1; Shirt 79.4).

**Limits.** One seed; the gate percentile was swept on the test images (a fixed threshold must be chosen on a validation set before quoting this); stage 2 adds a second encoder pass (HOG bits are compares and counts, cheap) and a 19 to 75 KB table; T-shirt recall pays a price.

Related: [Results index](INDEX.md), [Clothing accuracy round](clothing_features_round.md), [Specialist for Shirt/T-shirt](shirt_specialist.md), [Journal](../../docs/journal.md)
