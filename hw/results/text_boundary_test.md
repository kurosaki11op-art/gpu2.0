---
title: Language boundary test - counting tables against a small transformer on Tiny Shakespeare (30 Oct 2026)
tags: [spark, language, boundary, negative-result, estimate]
---

# Language boundary test (30 Oct 2026)

Question: do L's methods (counting tables, hashed lookups, adds, one-pass learning) carry over from images to language, where GPUs are used most? Character-level next-character prediction on Tiny Shakespeare (1,115,394 characters, last 10% held out), scored in bits per character (BPC, lower is better; 6.02 is random over 65 symbols). Script [text_boundary_test.py](../brain/experiments/month5/text_boundary_test.py), log [text_boundary_test.log](../brain/experiments/month5/text_boundary_test.log). **SIMULATED quality, one seed, one small corpus; energy ESTIMATED from operation counts.**

## Results

| model | held-out BPC | size | learning |
|---|---|---|---|
| counting tables, order 3 | 2.90 | about 25 KB | one pass over the text, 16 s |
| counting tables, order 4 | 2.49 | about 120 KB | same |
| **counting tables, order 5 (best)** | **2.33** | about 380 KB | same |
| counting tables, orders 6 / 7 / 8 | 2.36 / 2.45 / 2.55 (worse) | 0.9 / 1.7 / 2.8 MB | same |
| reference transformer, 2 layers, d = 128, context 128 (430,000 parameters) | 2.25 to 2.28 (flat for the last 5 minutes) | 0.43 M parameters | gradient descent, 11,354 steps, 900 s on this CPU, undertrained |

1. **At this tiny scale the counting tables come within about 0.07 to 0.1 BPC (3 to 4%) of the transformer**, learning in one pass in seconds against 15 minutes of gradient descent, with no matrices. So the method does carry over to language at small scale.
2. **But the counting tables hit a wall at about 2.3 BPC.** Adding context (orders 6 to 8) makes them worse and the tables grow from 380 KB to 2.8 MB, because contexts become too sparse to count; this is the known limit of n-gram counting. A neural model keeps improving with more parameters and training (literature figures for this corpus are far lower, about 1.5 BPC for well-trained networks, not measured here), while our transformer reference was small and stopped early. So the comparison is at the weak end of the transformer, not its limit.
3. **Energy (ESTIMATED, operation counts only):** the transformer needs about 0.48 million multiply-adds per character, about 0.10 microjoule for the multiplies alone; the order-5 counting model needs 5 table reads per character, about 50 pJ at the project's 10 pJ per read (mixing arithmetic and hashing not counted), roughly 1,000 times fewer operations at about 3 to 4% worse quality. Caveats: the tables hold about 190,000 counts that grow with the corpus; a larger corpus would need more memory and DRAM-cost accesses.

## What it means

The "small things only" worry is partly right: language is a boundary where the counting method stops scaling at about 2.3 BPC while neural models continue to improve with scale. For a small always-on language task (keyword, command or next-character prediction on a device) the method is competitive and far cheaper in operations; for a large language model it is not evidence of anything. No test here says our method can replace a GPU for language models.

Related: [GPU problem analysis](../../docs/gpu_problem_analysis.md), [Gap diagnosis](gap_diagnosis.md), [Results index](INDEX.md), [Journal](../../docs/journal.md)
