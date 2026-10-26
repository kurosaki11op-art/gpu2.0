---
title: Real depth - a second clause layer over clause bits
tags: [spark, results, clauses, depth]
---

# Real depth: a second clause layer over clause bits (26 Oct 2026)

SIMULATED, Fashion-MNIST, one seed. Piece 4 of the plan. Layer 2 is the same local clause learner (no error passing, no backprop) with 400 clauses per class (4,000 total), reading L's detector code, the raw pixel bits and the 8,000 firing bits of the frozen layer-1 bank (14,176 bits), T 40, s 3, 6 epochs. Scripts `tm_faithful.py` (INPUT=deep), `run_deep.sh`, `clause_routed2.py` (INPUT=deep); logs `tm_deep_c400.log`, `clause_routed2_deep.log`, `clause_routed2_deep_l1all.log`.

| | accuracy | cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|
| layer 1 alone (800 per class, 4 epochs) | 87.0 | 76.2 | 0.35 to 0.66 | 0.66 to 0.69 |
| layer 2 alone (400 per class, 6 epochs) | 87.9 | 79.7 | 0.56 | 0.70 |
| L alone | 88.85 | 80.6 | 0.638 | 0.753 |
| L + best 4,000 layer-1 clauses (two seeds) | 89.73 / 89.76 | 82.1 / 82.4 | 0.649 / 0.667 | 0.780 / 0.786 |
| L + 2,000 layer-2 clauses | 89.64 | 82.5 | 0.670 | 0.785 |
| L + 4,000 layer-2 clauses | 89.90 | 82.4 | 0.665 | 0.788 |
| L + 4,000 layer-2 clauses + all 8,000 layer-1 bits | 89.81 | 82.4 | 0.665 | 0.789 |

- **Depth helps the clause layer by itself** (+0.9 points, cluster +3.5), with half the clauses per class, so conjunctions of clause bits carry real information.
- **In the system it adds almost nothing**: 89.90 against 89.73 to 89.80 for layer 1 (+0.1 to +0.2, inside the seed spread). L's counting table over any clause bits tops out near 89.8 to 89.9; depth does not move the ceiling.
- **It costs more**: a layer-2 decision first needs the layer-1 clauses evaluated (8,000 firing bits), then the layer-2 clauses, so the energy is above the x3.8 of L measured for layer 1 alone (not measured).
- Verdict: real depth works as a mechanism (local rule, no error passing) but is not worth its cost here. Weight sharing (piece 5) not started.

Related: [Tsetlin-style clause learner](tsetlin_clause_learner.md), [Our own methods](own_methods_routing.md), [Energy and tiles](best_version_energy_tiles.md), [Results index](INDEX.md)
