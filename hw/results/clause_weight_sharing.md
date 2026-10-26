---
title: Weight sharing across positions (convolutional clauses)
tags: [spark, results, clauses, weight-sharing]
---

# Weight sharing across positions: convolutional clauses (26 Oct 2026)

SIMULATED, Fashion-MNIST, one seed. Piece 5 (the original L-Deep idea of sharing across positions), built with the local clause learner instead of gate trees: no error passing, no backprop, no matrix, no multiply. A clause reads a W by W window and the same clause is tried at every window position; it fires if it matches at any position; feedback goes to a randomly chosen matching position; row and column bits let a clause stay position-specific if it needs to. Script `hw/brain/experiments/month5/tm_conv.py`, evaluation `conv_eval.py`, logs `tm_conv_w3_c400.log`, `conv_eval_w3.log`, `tm_conv_raw_w5_c200.log`.

| variant | clauses | epochs | standalone accuracy | with L's table |
|---|---|---|---|---|
| flat clauses on L's code (reference) | 3,200 to 8,000 | 4 to 5.5 | 86 to 87 | 89.7 to 89.8 (4,000) |
| shared, 3 by 3 window over L's 6 by 6 detector map | 4,000 | 5 | 83.9 (cluster 73.7) | 1,000: 88.99; 2,000: 89.24; 4,000: 89.07 (L alone 88.85) |
| shared, 5 by 5 window over raw pixel bits (stride 2) | 2,000 | 3 | 68 to 75, unstable (Shirt recall jumps 0.0 to 0.97) | not evaluated |

- **No gain on this data.** On L's code the shared clauses add only +0.2 to +0.4 to L (against +0.9 for flat clauses). On raw pixels sharing is far worse than flat clauses on the same bits (about 84%).
- **Why:** Fashion-MNIST items are centred and aligned, so where a feature sits is part of the answer, and an OR over positions throws it away; L's detector code is already pooled over positions (stride 1, pool 4), so there is little translation left to share. The shared clauses are small and cheap (tens of literals, no position copies), but the accuracy cost outweighs it here.
- Not tested: data where position really varies (shifted or unaligned images, natural photos, sound with time shifts), where sharing should pay. That is where this belongs, not on aligned clothing.

Related: [Real depth](clause_depth_layer2.md), [Tsetlin-style clause learner](tsetlin_clause_learner.md), [L-Deep attempts](ldeep_attempts.md), [Results index](INDEX.md)
