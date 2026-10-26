---
title: Energy and tile mapping of the best-accuracy version
tags: [spark, results, energy, tiles]
---

# Energy and tile mapping of the best-accuracy version (26 Oct 2026)

Version: L's detector code + 4,000 best clauses over detector and raw-pixel literals, read by one counting table. Counts MEASURED on 5,000 test images, both seeds; energies ESTIMATED with the project's 45 nm per-operation constants (script `hw/brain/experiments/month5/clause_energy_best.py`, log `clause_energy_best.log`).

| | seed 0 | seed 1 |
|---|---|---|
| clauses read per image (keyed, of 4,000) | 2,164 | 2,219 |
| of which always-on (no positive literal) | 1,485 | 1,547 |
| clauses firing per image | 1,046 | 1,035 |
| table rows read (589 detector + clause bits) | 1,634 | 1,624 |
| store: clauses + table (8-bit entries) | 38 + 84 KB | 43 + 84 KB |
| energy per decision, L alone | 29.3 nJ | 29.3 nJ |
| L + clauses on every image | 110.7 nJ (x3.8) | 112.6 nJ (x3.8) |
| routed to 30% of images | 53.7 nJ (x1.8) | 54.3 nJ (x1.9) |

## What this says

- **Cost is x3.8 of L on every image, x1.85 with routing (ESTIMATED).** Earlier guess was 2 to 3x; keyed reading helps less than hoped because 37% of clauses are pure-negation and must be read every time (1,485 of the 2,164 reads). Against the int8 MLP (about 700 nJ, ESTIMATED) the full version is about 6x lower and the routed one about 13x lower.
- **Gain for that cost:** +0.9 points overall, +1.8 on the upper-body cluster, both seeds, SIMULATED.
- **Biggest lever:** the always-on list. Giving every clause a positive literal cost accuracy (earlier test), so the open question is a cheaper way to test pure-negation clauses (shared negation prefix, or one early-exit scan).

## Mapping onto tiles

- Everything fits in about 2 tiles of 64 KB (clauses 38 to 43 KB, table 84 KB). Spreading the clause store over 16 tiles by key literal touches all 16 on every image, so it only adds messages: with this size one tile pair is the right mapping, and the 2,164 clause reads stay on-tile (no cross-tile traffic).
- Cross-tile traffic is then only the partial class scores (10 per tile pair). The existing tile RTL is for the counting language model; a clause tile (key-literal index, clause literal lists, AND-match, fire list feeding the table) is not built. Not mapped in RTL.
- Routing needs L's margin first (a second pass through the same tile pair), already included in the 30% figure.

Related: [Our own methods](own_methods_routing.md), [Tsetlin-style clause learner](tsetlin_clause_learner.md), [Results index](INDEX.md)
