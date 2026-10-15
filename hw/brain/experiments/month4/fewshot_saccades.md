---
title: Few-shot - saccades and top-m voting
tags: [spark, cortex, few-shot, experiment]
---

# Few-shot: saccades (shifted copies) and top-m voting (15 Oct 2026, 07:50 IST)

Episodic recall on spread codes (month 3), 3 seeds; `fewshot_saccades.py`, log `fewshot_saccades.log`.
Saccades = every stored example also stored shifted by one pooled cell up/down/left/right. Top-m = a class scores the
sum of its m best overlaps.

| Examples per class | best-1 (month 3) | top-2 | saccades, top-2 | network (month 2) |
|---|---|---|---|---|
| digits 1 | 40.5 | 40.5 | 37.9 | 39.1 |
| digits 5 | 61.3 | **62.8** | 56.0 | 67.4 |
| digits 20 | 74.2 | 76.3 | 70.5 | 81.2 (table: 86.6) |
| clothing 1 | 42.8 | 42.8 | 41.0 | 43.7 |
| clothing 5 | 53.3 | **56.6** | 53.1 | 62.9 |
| clothing 20 | 62.3 | 64.5 | 62.1 | 73.7 (table: 70.2) |

SIMULATED. Saccades hurt on every setting (the spread code already gives the position tolerance; shifted copies add
false matches): rejected. Top-2 voting gains 1.5-3.3 points at 5 examples and costs nothing in hardware (two running
maxima per class instead of one), but the gap to the network at 5 examples remains (digits -4.6, clothing -6.3).
The few-shot limit on the claims sheet stands.

## Replay of dreams from the few examples (same day)

`fewshot_replay.py` (log `fewshot_replay.log`): the table also practises 50 or 200 dreams per class drawn from the
k examples' on-rates. At 5 examples: digits 55.7 -> 50.2 / 50.8 (plain codes), 43.7 -> 48.6 / 48.2 (spread codes);
clothing 49.5 -> 49.3 / 45.9, 46.9 -> 45.6 / 43.9. It mostly hurts (dreams from 5 examples add noise, not variety)
and stays below episodic recall (digits 62.8, clothing 56.6). Rejected. SIMULATED, 3 seeds.

## Rarity-weighted recall (15 Oct, evening)

`fewshot_rarity.py` (log `fewshot_rarity.log`): each bit weighted 1-4 (or 0-3, 1-8) by how rare it is on unlabeled
images, so rare shared bits count more. At 5 examples, top-2: digits 62.8 -> 53.8, clothing 56.6 -> 53.7; worse at
every size. Rare bits here are mostly noise, not evidence. Rejected. SIMULATED, 3 seeds.

Related: [Few-shot fusion](../month3/fewshot_fusion.md), [Month 3 results](../../../results/cortex_month3.md), [Month 4 experiments](INDEX.md)
