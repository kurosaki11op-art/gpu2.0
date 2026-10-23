---
title: Multi-chip test of the counting language model (23 Oct 2026)
tags: [l, multichip, memory, results]
---

# Splitting the table over many chips (SIMULATED; costs modelled with stated assumptions)

Decision (user, 23 Oct): keep all memory on chips (no DRAM or HBM) and scale by using several chips, as Groq and Cerebras do. `hw/brain/experiments/month5/multichip_lm.py` (log `multichip_lm.log`): the 8 MB counting language model ([note](counting_lm.md)) is split over N chips by table slot (hash-spread). One token needs 48 table lookups (6 context orders times 8 sequential yes/no steps). Measured on the real text: share of lookups that leave the home chip and the load per chip. Modelled with assumptions: round trip 200 ns per remote lookup, 5 ns local, 14 pJ per access (library), 5 pJ per bit between chips, 6 bytes per lookup.

| Chips | Remote lookups | Busiest chip / average | Messages per token | Bytes per token | Latency per token | Energy per token (lookups + links) |
|---|---|---|---|---|---|---|
| 1 | 0% | 1.00 | 0 | 0 | 0.04 us | 0.67 nJ |
| 4 | 73% | 1.08 | 35 | 211 B | 1.64 us | 9.1 nJ |
| 16 | 93% | 1.24 | 45 | 269 B | 1.64 us | 11.4 nJ |
| 64 | 98% | **2.12** | 47 | 281 B | 1.64 us | 11.9 nJ |

**Reading.**
- Splitting by hash sends almost every lookup off the home chip (98% at 64 chips), but the traffic stays small (about 280 bytes per token) and the energy stays in nanojoules per token, because only 48 rows are touched.
- **Measured: the load is not even.** At 64 chips the busiest chip serves 2.1 times the average (frequent contexts are hot); the fix is to copy hot rows to every chip (not yet tested).
- The 8 steps are sequential, so latency is 8 times the chip-to-chip round trip (1.6 us per token at the assumed 200 ns); it does not shrink with more chips, so a faster link or fetching several steps at once is the lever.

**Dense 7-billion-parameter model on the same idea (analytic, cost only, 4-bit weights = 3.5 GB, pipeline split):**

| SRAM per chip | Chips needed | Cross-chip bytes per token | Compute energy per token (int8 MACs, 0.2 pJ, 45 nm) |
|---|---|---|---|
| 3 MB (130 nm open macros, 400 mm2) | 1,167 | 4.8 MB | 2.8 mJ |
| 300 MB (28 nm, Groq-class) | 12 | 45 KB | 2.8 mJ |
| 1.2 GB (7 nm) | 3 | 8 KB | 2.8 mJ |

**Do not read this as "L beats a transformer".** The 8 MB counting model has roughly n-gram quality (1.8 bits per character on a small text); the 7-billion-parameter model has far higher quality. This table compares cost only. Whether an L-style model can reach the same quality at this memory is the open hypothesis. Limits: first-order model (no contention or link queues), link figures are typical ranges, one corpus.

Related: [Results index](INDEX.md), [Counting language model](counting_lm.md), [Bits against accuracy](bits_vs_accuracy.md), [Journal](../../docs/journal.md)
