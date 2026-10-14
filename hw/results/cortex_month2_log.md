# SPARK Cortex month 2: running log (memory shrink), SIMULATED

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

## Next

`m2i.py`: a night of sleep after each stage that dreams all known classes, new ones included, so the table cannot
learn "dream-looking = old class".

Related: [SPARK Cortex redesign](../../docs/cortex_redesign.md), [Brain code](../brain/README.md), [Results index](INDEX.md)
