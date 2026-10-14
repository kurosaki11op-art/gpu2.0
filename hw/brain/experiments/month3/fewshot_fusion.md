---
title: Few-shot fusion test (episodic + table)
tags: [spark, cortex, experiment, few-shot]
---

# Few-shot fusion: episodic recall and the table vote together (15 Oct 2026, 03:00 IST)

Question: at 5 examples per class the chip is behind a small network (digits 61.3 vs 67.4, clothing 53.3 vs 62.9).
Two memory systems (episodic recall like the hippocampus, the table like the cortex) might do better together.

Test: `fewshot_fusion.py` (float sim, spread codes r=1, 3 seeds). Score = table score + (best overlap per class << s),
integer only. Logs: `fewshot_fusion.log` (shift down, table dominates), `fewshot_fusion_shiftup.log`.

| Examples per class | table | episodic | best fused | network (earlier) |
|---|---|---|---|---|
| digits 1 | 28.7 | **40.5** | 39.4 (<<6) | 39.1 |
| digits 5 | 43.7 | **61.3** | 59.8 (<<6) | 67.4 |
| digits 20 | 86.6 | 74.2 | **88.1** (<<3) | 81.2 |
| clothing 1 | 25.4 | 42.8 | 42.2 (<<6) | 43.7 |
| clothing 5 | 46.9 | 53.3 | **56.4** (<<5) | 62.9 |
| clothing 20 | 70.2 | 62.3 | **71.2** (<<3) | 73.7 |

SIMULATED. Result: fusion adds +1 to +3 points at 20 examples and on clothing at 5, but no single shift wins at every
size, and the gap to the network at 5 examples remains (digits -6, clothing -6.5). Not adopted; the few-shot claim
stays as in the claims sheet. A shift that falls as a class's count n grows (the chip
already stores n) amounts to the best-fused column: digits 39.4 / 59.8 / 88.1, clothing 42.2 / 56.4 / 71.2, i.e. a
small gain at 20 examples and on clothing at 5, a small loss on digits at 1 and 5.

Related: [Month 3 results](../../../results/cortex_month3.md), [Month 3 experiments](INDEX.md)
