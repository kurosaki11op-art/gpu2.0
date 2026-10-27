---
title: Multi-threshold input for L's front end, and what teaching the eyes does
tags: [spark, results, foundations, front-end]
---

# Multi-threshold input for L's front end (27 Oct 2026)

SIMULATED, Fashion-MNIST, one seed. Follow-up to the [foundations study](foundations_study.md). Scripts in `hw/brain/experiments/month5/`: `front_end_test.py` (stand-in front end, logs `front_end_*.log`), `multi_threshold_L.py` (L itself, log `multi_threshold_L.log`).

## Test 1: does sending the task's error back to the eyes help? (stand-in front end)

A small stand-in for L's front end (5 by 5 patches over thresholded pixel channels, shared pattern finders, pooled to a 4,608-feature code of about 13% active bits), the eyes trained with an auxiliary readout, then the pooled responses binarised and read by OUR counting table:

| how the eyes were trained (pooling 4, 2 channels, 4 epochs) | our table on the code |
|---|---|
| not trained (random filters) | 87.30 |
| exact backprop | 87.74 |
| random fixed feedback wires (feedback alignment) | 87.33 |
| sparse random +-1 feedback wires (adds and subtracts) | 87.31 |

Finer geometry (pooling 2, 32 filters, 8 epochs): random 86.28, exact backprop 86.93, feedback alignment 86.67. With real-valued pixel input instead of two black/white channels: random 87.80, backprop 88.15 (the network's own float readout 89.83 and 90.36).

**The error signal to the eyes helps very little (+0.4 to +0.7 at best), by any route, and every variant stays below L's own Hebbian code (88.85).** The earlier hypothesis in the foundations note, that L is limited because its detectors are not taught by the task error, is not supported by this test.

## Test 2: finer input (more threshold channels), stand-in with exact-backprop eyes

Our table on the binary code (1-level / 2-level output code): 2 thresholds 86.93 / 87.83; 5 thresholds 87.96 / 88.43; 8 thresholds 88.73 / 89.05. Untrained eyes: 2 thresholds 86.28 / 86.53; 5 thresholds 86.24 / 87.00 (no gain without trained eyes). A two-level output code (a second bit when the response is above a higher quantile) adds about +0.5 to +0.9.

## Test 3: more threshold banks on L itself

L's front end is one bank of 32 Hebbian detectors per binary input channel (1,152 bits each); shipped channels: pixel > 50, pixel > 150, centre-surround 'on' 8, 'off' 8. Added threshold banks fitted exactly as L fits its own (same recipe, same table):

| channels | bits | active bits | accuracy | cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|---|---|
| shipped: 50, 150, on8, off8 | 4,608 | 589 | **88.85** | 80.6 | 0.638 | 0.753 |
| two thresholds: 50, 150 | 2,304 | 211 | 86.50 | 76.5 | 0.566 | 0.677 |
| four thresholds: 32, 96, 160, 224 | 4,608 | 375 | 87.74 | 78.9 | 0.575 | 0.711 |
| five thresholds | 5,760 | 478 | 88.04 | 79.1 | 0.601 | 0.719 |
| eight thresholds | 9,216 | 748 | 88.50 | 79.7 | 0.588 | 0.732 |
| shipped + two thresholds (6 channels) | 6,912 | 787 | 88.91 | 81.4 | 0.644 | 0.751 |
| five thresholds + on8 + off8 (7 channels) | 8,064 | 855 | 89.48 | 82.1 | 0.641 | 0.763 |
| eight thresholds + on8 + off8 (10 channels) | 11,520 | 1,125 | **89.82** | 82.3 | 0.641 | 0.762 |

- **More threshold banks do help L: +0.6 (7 channels) and +1.0 (10 channels) in accuracy, +1.4 to +1.6 in cluster accuracy**, no multiplies added. Thresholds alone are not enough: four thresholds with the same bit count as the shipped code give 87.74, so the centre-surround on/off channels carry more than extra grey levels. Shirt recall stays about 0.64 and Shirt AP rises by 0.01.
- **Cost (ESTIMATED from the counts):** active bits per image rise from 589 to 855 (x1.45) and 1,125 (x1.9) and the front end runs 7 or 10 banks instead of 4, so table reads grow with active bits and the front end with channels (about x1.45 to x1.9 for the table, x1.75 to x2.5 for the front end). By comparison the clause layer routed to 30% of images gave +0.9 at x1.85 L's energy.
- Not yet tested: combining multi-threshold input with the clause layer; a two-level output code on L itself (the stand-in suggests +0.5 to +0.9); the gain on EMNIST; a second seed (the spread between identical runs is about 0.3).

## Test 4: two-level output code on L itself (27 Oct 2026; `two_level_L.py`, `two_level_L.log`)

L reports each detector per 4 by 4 pooled window as one bit ('won at some position in the window'). The second bit added here says 'won at T or more of the 16 positions in the window' (a count and a compare; levels shown as the thresholds used). Same detectors, same table; sanity check passed (the recomputed one-level code equals L's cached code exactly).

| channels, levels | bits | active bits | accuracy | cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|---|---|
| shipped, level 1 (reference) | 4,608 | 589 | 88.85 | 80.6 | 0.638 | 0.753 |
| shipped, levels 1, 2 | 9,216 | 960 | 89.00 | 81.0 | 0.630 | 0.765 |
| shipped, levels 1, 3 | 9,216 | 833 | 89.07 | 81.3 | 0.613 | 0.776 |
| shipped, levels 1, 4 | 9,216 | 752 | **89.45** | 81.6 | 0.613 | 0.772 |
| shipped, levels 1, 2, 4 | 13,824 | 1,124 | 89.41 | 81.9 | 0.639 | 0.776 |
| seven channels, level 1 | 8,064 | 855 | 89.48 | 82.1 | 0.641 | 0.763 |
| seven channels, levels 1, 2 | 16,128 | 1,409 | **89.95** | 82.5 | 0.669 | 0.777 |
| seven channels, levels 1, 3 | 16,128 | 1,228 | 89.73 | 82.5 | 0.659 | 0.786 |
| seven channels, levels 1, 2, 4 | 24,192 | 1,663 | 89.70 | 82.4 | 0.650 | 0.781 |

- **The second level helps, by a small amount:** +0.6 on the shipped channels with levels 1 and 4 (accuracy 89.45, Shirt AP +0.02, 1.28 times the active bits) and +0.47 on top of seven channels (89.95, Shirt recall 0.669, AP 0.777). It does not stack to the ten-channel result (89.82 with level 1 only was reached by adding channels, 1.9 times the active bits).
- **Best cost for gain so far:** shipped channels with levels 1 and 4: +0.6 accuracy for +163 active bits per image (x1.28), better than adding three channels (+0.63 for +266 active bits and three more banks). Seven channels with levels 1 and 2 reach 89.95 (+1.1) at x2.4 active bits.
- Caveats: one seed (spread about 0.3); table size doubles with a second level (9,216 bits shipped; 16,128 for seven channels); the energy cost is ESTIMATED from active-bit counts only, not simulated. Not tested: EMNIST, combination with the clause layer (clauses on top of this richer code), a smaller pooled window.
- Housekeeping: disk allowance ran out during the first run (cached count files); intermediate caches of the earlier threshold test were deleted (regenerable by `multi_threshold_L.py`), nothing else.

Related: [Foundations study](foundations_study.md), [Results index](INDEX.md), [Own methods](own_methods_routing.md)
