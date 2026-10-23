---
title: Neural baseline for the counting language model (23 Oct 2026)
tags: [l, language-model, results]
---

# A small neural character model against the counting model at the same memory (SIMULATED, torch on CPU)

`hw/brain/experiments/month5/neural_lm_baseline.py` (log `neural_lm_baseline.log`): embedding of the last 6 characters, one ReLU hidden layer, 256-way softmax; Adam, 4 epochs on the first half of the same 561,285-character text, bits per character (bpc) on the second half; memory counted at 8 bits per weight.

| Model | Memory | bpc on second half |
|---|---|---|
| Neural 8-32 | 12 KB | 3.084 |
| Neural 16-128 | 48 KB | 2.429 |
| Neural 16-512 | 181 KB | 2.220 |
| Neural 32-1024 | 457 KB | 2.088 |
| Counting (orders 0..5, online) | 32 KB | 3.828 |
| Counting | 128 KB | 2.965 |
| Counting | 512 KB | 2.236 |
| Counting | 2 MB | 1.812 |
| Counting | 8 MB | 1.670 |

**Reading (failure recorded).** At equal memory up to about 0.5 MB the small neural model is better (48 KB: 2.43 against 3.83 for the counting model at 32 KB, 457 KB: 2.09 against 2.24 at 512 KB). The counting model only wins by using far more memory (2 MB and above reach 1.81 and lower, which these small networks did not reach here, though they were not tuned or enlarged further). So "the counting language model is more memory-efficient" is NOT shown; what the counting model offers is learning on the fly with no training run, no backprop and a lookup-only chip path.

## Second text: Shakespeare (1,115,394 characters, a different kind of English; fetched from the char-rnn data set on GitHub; Project Gutenberg is blocked from this container)

Files: `shakespeare_input.txt`, `counting_lm_shakespeare.log`, `neural_lm_baseline_shakespeare.log`.

| Model | Memory | bpc second half |
|---|---|---|
| Neural 8-32 / 16-128 / 16-512 / 32-1024 | 12 / 48 / 181 / 457 KB | 3.204 / 2.860 / 2.708 / 2.643 |
| Counting orders 0..5, online | 32 KB / 128 KB / 512 KB | 4.355 / 3.516 / 2.837 |
| Counting | 2 MB / 8 MB / 32 MB | 2.397 / 2.229 / 2.184 |

Same shape as on the Python text: the neural model wins at equal memory below about 0.5 MB; the counting model overtakes it from about 2 MB (2.40 against 2.64 at 457 KB for the largest net tried) and improves slowly to 2.18. The longer text moves the picture a little (bigger text, more to count), but one more text is still not a benchmark; no real large corpus (billions of characters) was reachable, and the neural nets were not enlarged beyond 457 KB, so the comparison above 0.5 MB is partly unequal in memory.

**Limits.** Not a like-for-like protocol: the counting model is online (it learns while reading, so the second-half figure includes what it learned from the first half and from the second half so far), the neural model is frozen after 4 epochs on the first half. One seed, one text (Python documentation), networks not tuned, bigger networks not tried.

Related: [Results index](INDEX.md), [Counting language model](counting_lm.md), [Shrinking a standard network](compress_mlp.md), [Journal](../../docs/journal.md)
