---
title: Our own methods from the failures - retrieve-then-rerank and routed clauses
tags: [l, memory, routing, clauses, energy, scaling]
---

# Two methods sketched from the failures (25 Oct 2026)

Lessons that shaped them: every active bit reads a row with an entry for every class, so cost grows with the number of classes, and cutting entries out of rows loses accuracy ([MEM-C1](table_compression_mem_c1.md), [option B](sparse_table_option_b.md)); the clause layer helps the confusable classes but costs about 2.7 times L's reads on every image ([L-Deep v3](ldeep_attempts.md)). Both methods spend memory reads only where they pay. SIMULATED, one seed; energy ESTIMATED.

## Method 1: retrieve, then rerank
Each class keeps a signature of its S most distinguishing bits as an inverted index (bit to classes). Stage 1: every active bit reads its short list and votes; the top C classes are candidates. Stage 2: only the candidates are scored exactly. Scripts: [retrieve_rerank.py](../brain/experiments/month5/retrieve_rerank.py), [omni_c1.py](../brain/experiments/month5/omni_c1.py); logs: [EMNIST sweep](../brain/experiments/month5/retrieve_rerank_sweep.log), [Omniglot](../brain/experiments/month5/omni_c1_step2.log).

- **Entry counts overstate the saving.** Memory is read in 64-bit words: a 47-class row of 6-bit entries is 5 words, so at 47 classes stage 2's one word per candidate entry is as costly as the full row. In words, 47 classes: full table about 3.2 thousand words per decision, retrieve-rerank (S 400, C 8) about 6.6 thousand: **worse**, although accuracy is kept (82.9 against 82.9). It is not a method for tens of classes.
- **At 1,623 classes (Omniglot, 12 drawings per class, 482 active bits) it pays**, counted in words: full table 71,122 words per decision (5.6 MB at 6 bits) and 27.75% accuracy (top-16 recall of the full table is 64.6%). Retrieve-rerank: S 200, C 32 keeps 27.75% at 2.3 times fewer words; S 50, C 32 gives 27.0% (-0.7) at 3.6 times fewer; S 50, C 8 gives 24.3% (-3.4) at 8.5 times fewer. The stage-1 lists grow with the number of classes, so the saving is a few times, not orders of magnitude. The weak absolute accuracy (27.8%) limits any retrieval: the code was not designed for 1,623-way few-shot recognition.

## Method 2: routed clauses
L's own table decides first (cheap); only images that need it (top class in T-shirt, Pullover, Coat, Shirt, or a small margin) evaluate the 8,000-clause layer and are re-scored by the table that reads L's code plus clause bits. Script [clause_routed.py](../brain/experiments/month5/clause_routed.py), log [clause_routed.log](../brain/experiments/month5/clause_routed.log).

| Route | Accuracy | Cluster | Shirt AP | Images that evaluate clauses |
|---|---|---|---|---|
| L alone | 88.85 | 80.6 | 0.753 | 0% |
| L + clauses on every image | 89.55 | 82.0 | 0.779 | 100% |
| top class in the cluster | 89.39 | 81.7 | 0.778 | 40% |
| margin below the 30th percentile | **89.59** | **82.0** | 0.775 | **30%** |
| margin below the 50th percentile | 89.55 | 82.0 | **0.780** | 50% |

- **The whole gain survives with 30% of the clause cost**: accuracy +0.7, cluster +1.4, Shirt AP +0.022 (0.775).
- **Energy (ESTIMATED, 45 nm constants of the project's model, keyed clause reads, second stage reusing L's partial sums)**: L alone 29 nJ; clauses on every image 146 nJ keyed or 250 nJ scan; routed at 30% about 68 nJ keyed (2.3 times L) or 99 nJ scan (3.4 times L). Still above L's own energy, so a win in accuracy and a loss in energy, but far smaller than the 5.0 to 8.5 times of the always-on layer.
- Not yet combined: pruned clause sets (top 4,000 by use gave AP 0.773), clauses required to hold a positive literal (keyed evaluation of all of them), a second seed.

## Best-accuracy version so far (25 Oct 2026, SIMULATED, one seed)
Per the founder's direction (build the strongest version first, tune cost later). Scripts [clause_routed2.py](../brain/experiments/month5/clause_routed2.py), [tm_faithful.py](../brain/experiments/month5/tm_faithful.py); logs [1,600 clauses](../brain/experiments/month5/clause_routed2_c1600.log), [clauses over both codes](../brain/experiments/month5/clause_routed2_both_c800.log), [training](../brain/experiments/month5/tm_both_c800.log). Clauses are ranked by how much a table trained on 20,000 images uses them; the best N are kept; L's table then reads L's code plus the N clause bits (trained on all 60,000 images).

| Clause layer (per class) | Clauses kept | Every image: accuracy / cluster / Shirt recall / Shirt AP | Routed (30% of images): accuracy / cluster / Shirt AP |
|---|---|---|---|
| L alone (reference) | 0 | 88.85 / 80.6 / 0.638 / 0.753 | n/a |
| 800, read L's code, 5.5 epochs | 8,000 | 89.55 / 82.0 / 0.666 / 0.779 | 89.59 / 82.0 / 0.775 |
| 1,600, read L's code, 4 epochs | best 8,000 of 16,000 | 89.60 / 82.0 / 0.668 / 0.783 | 89.61 / 82.0 / 0.773 |
| 1,600, read L's code, 4 epochs | all 16,000 | 89.65 / 82.1 / 0.656 / 0.779 | 89.67 / 82.1 / 0.773 |
| **800, read L's code and the raw pixel bits, 4 epochs** | best 4,000 of 8,000 | **89.73** / 82.1 / 0.649 / **0.780** | 89.73 / 82.1 / 0.774 |
| **800, read L's code and the raw pixel bits, 4 epochs** | all 8,000 | 89.68 / 82.2 / 0.658 / **0.789** | 89.71 / 82.2 / 0.781 |

- **The strongest version reaches the Shirt AP criterion (0.78) with half the clauses**: L's code plus the best 4,000 clauses over detector and raw-pixel literals gives 89.73% accuracy (+0.88) and Shirt AP 0.780 (+0.027); all 8,000 give AP 0.789 (+0.036).
- **Doubling the clauses on the same input saturates** (800 to 1,600 per class: AP 0.779 to 0.783, accuracy +0.05); a **richer input** (adding the raw pixel bits as literals) helped more at equal clause count (AP 0.779 to 0.789), in line with the papers (input code matters most).
- **A positive-literal rule (every clause holds at least one positive literal, for keyed evaluation) cost accuracy while learning** (75.9% and Shirt AP 0.36 after 0.9 epochs against about 84% and 0.55 for unconstrained clauses at the same point) and was dropped; the energy of the clause layer therefore keeps the scan or keyed estimates of [L-Deep attempts](ldeep_attempts.md) for now.
- Not yet: a second seed, the energy of the routed 4,000-clause version, richer input codes (edge maps, team of codes), a second clause layer.

## Second seed (26 Oct, SIMULATED)

Seed 1 of the clause layer (same recipe): L + 4,000 clauses 89.76 / cluster 82.4 / Shirt recall 0.667 / AP 0.786; 8,000: 89.80; routed 30%: 89.80 to 89.84. Seed 0 gave 89.73 / 89.68; the +0.9 gain over L (88.85) holds on both seeds. Logs: tm_both_c800_seed1.log, clause_routed2_both_s1.log.

Related: [Results index](INDEX.md), [L-Deep attempts](ldeep_attempts.md), [Sparse table option B](sparse_table_option_b.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
