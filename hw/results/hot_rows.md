---
title: Hot-row copies fix the uneven load (23 Oct 2026)
tags: [l, multichip, load-balance, results]
---

# Copying the most used table rows to every chip (SIMULATED)

The [multi-chip test](multichip_lm.md) found that frequent contexts make some chips much busier than others (busiest chip 2.1 times the average at 64 chips). `hw/brain/experiments/month5/hot_rows.py` (log `hot_rows.log`) picks the K most used table slots on the first half of the text, copies them to every chip, and measures on the second half (13.5 million lookups, 818,000 distinct slots used).

| Chips | Copied slots K | Memory cost (of 4.2 M slots) | Remote lookups | Busiest chip / average |
|---|---|---|---|---|
| 16 | 0 | 0 | 93.8% | 1.25 |
| 16 | 1,024 | 0.02% | 53.4% | 1.02 |
| 16 | 16,384 | 0.39% | 32.3% | 1.01 |
| 64 | 0 | 0 | 98.4% | **2.12** |
| 64 | 64 | 0.00% | 78.4% | 1.18 |
| 64 | 1,024 | 0.02% | 56.0% | **1.06** |
| 64 | 16,384 | 0.39% | 33.9% | 1.02 |

**Reading.** Copying only 1,024 slots (0.02% of the memory) removes the imbalance (2.12 to 1.06 at 64 chips) and cuts remote lookups from 98% to 56%; 16,384 slots (0.4%) cuts them to about a third. Access is strongly skewed, so a small cache of hot rows captures much of the traffic.

**Limits.** Learning updates to a hot row must reach every copy (write-through or periodic merge); that cost is not modelled, and inference is the common case. The hot set was chosen on the same kind of text; a changing workload needs the set refreshed. One corpus.

Related: [Results index](INDEX.md), [Multi-chip test](multichip_lm.md), [Journal](../../docs/journal.md)
