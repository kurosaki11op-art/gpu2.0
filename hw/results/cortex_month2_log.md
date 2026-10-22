# L Cortex month 2: running log (memory shrink), SIMULATED

Scripts and raw logs: `hw/brain/experiments/month2/` (month-1 exploration: `experiments/month1/`).
Datasets and cached codes are not in git; scripts rebuild them.
Goal: memory from 11-28 MB to about 100 KB (Tang Nano 20K block RAM is about 103 KB), keeping month-1 accuracy;
one decision rule for every task; re-test few-shot.

## Findings so far

| # | Test | Result | Verdict |
|---|---|---|---|
| a | Fast table counters 8 -> 5 -> 4 bit (clothing, 18,432-bit code) | 85.8 -> 83.3 -> 82.4 | 5-bit is usable |
| a | Concept cells pruned to their most active S synapses | clothing 66-73, sound 20-28 | fails: the most active inputs fire for every class |
| b | Same, weighted against each input's overall firing rate (homeostasis), with/without inhibitory synapses | first run 10% = **bug** (unseen bits got huge weights from the smoothing constant); fixed: clothing 56-70, sound 24-36 | fails |
| c, d | Fold the code into fewer bits by fixed random wiring (OR) | clothing concept cells 83.1 at 2,048 bits (from 18,432); sound table 76 -> 49 (2,048) / 63 (4,096) | works for sparse image codes, not for dense sound codes |
| j, e | One joint detector set over all channels; top-k winners | clothing 9,216 bits, 94 active: table 83.9, concept 83.2; sound 62-67 | sparse, but sound loses too much |
| e | Concept cells storing only synapses seen at least twice | clothing 83 -> 74, still ~900 synapses per cell | fails |
| f | Small per-channel detector sets (32 per channel), synapse precision | 4,608-bit image code: table (5-bit, 28 KB) digits 97.0, clothing 84.7; concept 8 cells x 3-bit (135 KB) digits 95.8, clothing 79.0. Sound (23,040 bits): table 72.5 (5-bit, 141 KB) | best size/accuracy so far |
| g | Stop forgetting without dreams: local competition + homeostatic scaling | after 5 stages: clothing 23 -> 66, digits 28 -> 80, sound 18 -> 45 (month 1 with dreams: 86 / 96 / 72) | helps, not enough: dreams are needed |

| h | Dream source for sleep, fast table (5-bit) as the only decision maker, 5 stages. Code: 4,608 bits (images), 23,040 (sound) | see table below | count dreams best for digits and sound; concept 8x3-bit best for clothing; 2-bit cells fail |

Test h, accuracy after 5 stages (dream memory + 28 KB table for images, + 141 KB table for sound):

| Dream source | memory (images / sound) | Digits | Clothing | Sound |
|---|---|---|---|---|
| Per-class counts, 8-bit | 45 KB / 225 KB | 92.9 | 77.6 | **71.1** |
| Concept cells 4 x 3-bit | 68 / 338 KB | 90.9 | 81.2 | 62.6 |
| Concept cells 8 x 3-bit | 135 / 675 KB | 92.9 | **82.3** | 64.3 |
| Concept cells 8 x 2-bit | 90 / 450 KB | 83.9 | 65.8 | 45.7 |
| Concept cells 16 x 2-bit | 180 KB / n.a. | 87.0 | 72.6 | (killed) |
| Month 1 (11.5 / 28 MB) | | 97.2 | 86.3 | 71.8 |

| i | A night of sleep after each stage dreaming ALL known classes (new included), table only | concept 8x3-bit + 2x night: digits 95.3, clothing 84.2 (was 92.9 / 82.3); counts + 2x night: 94.3 / 79.7; sound: night hurts (count 69.6-67.2 vs 71.1 day-only) | night helps images, not sound |
| j | Chip-honest dream memory: 8/6/4-bit firing rates, fixed shift k (EMA), stochastic rounding | digits 86.7 / 78.1 / 57.2, clothing 75.2 / 67.7 / 55.2 | fixed step too noisy (tracks last ~64 examples) |
| k | Metaplasticity: shift grows with experience (k = bit length of count, cap 9-12), 8-bit rates, 45 KB | digits 93.1-93.3, clothing 77.9-78.3 (exact counts: 94.3 / 79.7); sound with night 61.2 | within ~1 pt of exact counting on images |
| l | On-chip concept cells (P cells x B-bit metaplastic rates, best-match cell learns) | best P2 x 8-bit (90 KB): digits 92.5, clothing 79.0; P4 x 4-bit, P8 x 3-bit fail (58-86) | no better than one rate vector per class |

| m | Soft imprint for new on-chip concept cells; sound with day-only rate memory | clothing 72.5-78.5, digits 92.1-92.6; sound 61.1 | no gain; 8-bit rates lose ~10 pts on sound |
| n | Single-pass concept cells with exact 16-bit counters (streaming, as a chip must) | 8 cells: digits 94.4, clothing 80.1 (720 KB); sound day-only 71.1 (3.6 MB) | = exact per-class counts; multi-pass sorting (84.2) not reachable in one pass |
| o | Per-class counters with synaptic scaling (halve all counts when a class's count is full), B-bit | images: 12-bit 68 KB: digits 94.1, clothing 78.8; **10-bit 56 KB: 94.1 / 78.9**; 8-bit 45 KB: 90.9 / 78.6 | **chosen for images**: 28 KB table + 56 KB counts = 84 KB, fits the Tang Nano's block RAM |

| p | Consolidation (old-class rows 1/4 as plastic) and sharper dreams | consolidation +0.3-0.6 (noise level); sharp dreams -10 to -12 | rejected |
| q | Few-shot with imagined variants (rate dreams, jittered copies) | changes within +-2 points, no consistent gain | few-shot stays an open weakness |
| v3 | Month-2 suite on images, small design (5-bit table 28 KB + 10-bit scaled counts 56 KB = 84 KB), night 1 | see table below | memory 11.5 MB -> 84 KB (137x) |

v3 suite, images (`cortex_v3_mnist_scaled10_n1.json`, `cortex_v3_fashion_scaled10_n1.json`):

| | Digits | Clothing |
|---|---|---|
| All data at once: brain table / network | 97.0 / 97.8 | 84.7 / 87.3 |
| 5 stages: brain / network / network + replay 20 | 94.1 / 19.5 / 49.6 | 78.9 / 20.0 / 37.8 |
| Merge (chip A 0-4 + chip B 5-9, add tables and counts, one night) | **95.8** | **82.7** |
| Few-shot 1 / 5 / 20: brain table | 37.5 / 55.7 / **82.5** | 39.0 / 49.5 / 68.6 |
| Few-shot 1 / 5 / 20: network | 39.1 / 67.4 / 81.2 | 43.7 / 62.9 / 73.7 |

## Integer reference model (month 3 started) - `hw/brain/cortex_int.py`, `run_int.py`

Integers only, one pass per real example (a streaming chip cannot re-read the day), xorshift random lanes,
rejection-sampled dreams (no divider). After 5 stages:

| Setting | Digits | Clothing | Sound |
|---|---|---|---|
| night 2 passes | **95.0** | 79.2 | 62.1 |
| night 0 | n.a. | n.a. | 66.0 |
| night 0 + daydream (dream of the new class after each real example) | 90.7 | 76.4 | **68.0** |
| night 2 + daydream | 94.6 | 79.5 | n.a. |
| night 1 + daydream | n.a. | 79.3 | 63.4 |
| sound: 12-bit counts / replay buffer 64 / both fixes | | | 67.2 / 66.4 / 68.4 |

The night helps images (+3 to +4) and hurts sound (-4 to -6). Next: a self-regulated night that stops when dreams
keep surprising the table.

Related: [L Cortex redesign](../../docs/cortex_redesign.md), [Brain code](../brain/README.md), [Results index](INDEX.md)
