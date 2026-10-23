---
title: Counting language model, first test (23 Oct 2026)
tags: [l, language-model, counting, results]
---

# Counting language model: does quality grow with table memory? (SIMULATED, algorithm test)

**Question.** Can a language model built only from hashed count tables (no matrix, no backpropagation, learning online, each character seen once) reach useful quality, and does quality grow with memory? This is the first test of the "design our own model" route in the L hypothesis ([hypothesis](../../docs/L_hypothesis.md)).

**Setup** (`hw/brain/experiments/month5/counting_lm.py`, log `counting_lm.log`). Text: the Python standard library's own documentation, 561,285 characters of English technical text. Prequential protocol: predict each character, then learn it, so every number is a one-pass online result. The next byte is predicted as 8 yes/no decisions. Each decision reads one pair of 8-bit counters (n0, n1; halved at 255) per context order (last 0 to n characters, hashed) from one shared table of M slots with no collision check. The score is the sum of the log-odds ln((n1+a)/(n0+a)) over the orders; p = 1/(1+exp(-k s)) with one global scale k = 0.25 (a shift by 2) and a = 0.2, picked once on this text.

| Context orders | Table slots | Memory | Bits per character (whole run) | Second half |
|---|---|---|---|---|
| 0..5 | 2^12 | 8 KB | 4.83 | 4.67 |
| 0..5 | 2^14 | 32 KB | 3.95 | 3.83 |
| 0..5 | 2^16 | 128 KB | 3.04 | 2.97 |
| 0..5 | 2^18 | 512 KB | 2.31 | 2.24 |
| 0..5 | 2^20 | 2 MB | 1.93 | 1.81 |
| 0..5 | 2^22 | 8 MB | 1.80 | 1.67 |
| 0..5 | 2^24 | 32 MB | 1.77 | 1.63 |
| 0..6 | 2^24 | 32 MB | 1.70 | 1.56 |

Reference points: unigram entropy 4.70 bits per character; offline compressors on the same text (not online, not comparable in kind): zlib 2.26, bz2 1.60, xz 1.54.

**Reading (SIMULATED).**
- **Quality grows with memory, as the L plan assumed**: 4.8 bits per character at 8 KB, 1.8 at 8 MB; the curve flattens above about 8 MB.
- **It learns online in one pass** and ends near the offline compressors, with counts only; the table path has no multiplier (the global scale is a shift).
- **Context order matters** more than the last megabytes: 0..2 gives 3.05, 0..3 2.31, 0..4 1.93, 0..5 1.77, 0..6 1.70.

**Not shown, and limits (said plainly).**
- The prototype uses floating-point logarithms and a sigmoid; mapping them to table lookups on the chip is not done, and the counter lookups are random memory accesses (the real cost on a chip is memory traffic, not measured).
- **No comparison with a neural language model of the same memory yet**; xz and bz2 are only reference points. A counting model is expected to be weaker than a transformer at equal size; this test does not decide that.
- One corpus, one language, bytes not words; 561 KB is tiny next to real language-model data.
- The log-odds sum is a naive-Bayes style mix (orders are correlated), calibrated by one global scale; a better mix is an open improvement.

**Next tests.** (1) A small neural character model trained on the same text (and a ternary version) at matched memory; (2) a word-level version with a larger vocabulary; (3) the forgetting test: learn text A, then text B, then measure A again; (4) map the log-odds and sigmoid to lookup tables and count memory reads per token.

## Multiplier-free hash (23 Oct, SIMULATED)

The first test used a multiplying hash. `hw/brain/experiments/month5/counting_lm_mf.py` (log `counting_lm_mf.log`) replaces it with a hash built only from shifts, rotates and XOR (a xorshift mix), so the table index needs no multiplier in hardware:

| Table slots | Multiplier-free hash (all / second half) | Multiplying hash (all / second half) |
|---|---|---|
| 2^16 | 3.042 / 2.962 | 3.041 / 2.965 |
| 2^20 | 1.923 / 1.810 | 1.926 / 1.812 |
| 2^22 | 1.802 / 1.670 | 1.802 / 1.670 |
| 2^24 | 1.771 / 1.634 | 1.770 / 1.632 |

The quality is the same to the third decimal, so the hardware token sequencer can compute the slot index with shifts and XOR only (the log-odds and sigmoid still need lookup tables; not yet mapped).

Related: [Results index](INDEX.md), [L hypothesis](../../docs/L_hypothesis.md), [L accelerator design](../../docs/L_accelerator_design.md), [Journal](../../docs/journal.md)
