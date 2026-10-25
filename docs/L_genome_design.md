---
title: L-Genome - a connected, append-only structure of detectors that grows (design, 25 Oct 2026)
tags: [l, design, neurogenesis, connected-structure, continual-learning]
---

# L-Genome: connected structure plus neurogenesis, designed from the failures

Founder's idea (25 Oct 2026): layers and detectors form a connected structure like DNA, new nodes are grown (neurogenesis), connected information is shared, errors are found and fixed through the connections, and nothing is overwritten. Status: DESIGN, parts being tested. No claim that it works; every part has a kill test below.

## Each past failure becomes a rule

| Failure (evidence) | Rule in the design |
|---|---|
| Overwriting shared weights: old classes 0.0% ([staged growth](../hw/results/local_growth_staged.md)) | **Append-only**: new nodes and new table entries are added, existing ones never change; refinement splits a table entry, it does not rewrite it |
| New nodes fire on old inputs, 89% of old images lost: one-vs-rest needs negatives that a no-stored-images learner lacks | **Generative per-class models** compared by likelihood (each class built only from its own data); no negatives anywhere |
| Unsupervised features follow the biggest variation, not the class difference ([difference layers](../hw/results/shirt_difference_layers.md)) | Where to connect and where to grow is decided by **information inside each class** (counted mutual information between a node and its candidate partners) and by **surprise** (a node its connections cannot predict), so differences that matter inside a class are what the structure captures; the class difference appears as the **disagreement between class models** |
| Independent bits lose: 67.5 against 83.6 once bits are connected ([connected structure](../hw/results/connected_structure.md)) | **Every node is judged given its connections** (spatial neighbours, same-cell partners, later parents in a higher layer) |
| Fixed, hand-chosen connections plateau near 85% | **Learned wiring per class**: each class chooses its own parents for each node by counted information; Shirt and T-shirt get different structures |
| Frozen encoder blocks new learning; plastic encoder forgets | **Growth, not change**: a new class gets a new genome that may connect to any existing node (information shared) and never edits them |
| Learning rule needed backprop | Counting only (adds, compares, table lookups); the integer error learner stays available for later deep layers |
| Error fixing | (a) learning: a node's mismatch with what its connections predict is its local error and triggers growth where it persists; (b) inference: consistency repair, replacing bits that contradict a confident neighbourhood under the winning class model |

## Closest published relatives (so we do not claim novelty we lack)
Bayesian-network classifiers (tree-augmented and k-dependence naive Bayes), Chow-Liu trees, generative classifiers, sparse associative memories (FlyModel), predictive coding. What we add is the combination: per-class learned structure over learned detector bits, append-only growth by surprise, no stored examples, counting only.

## Kill tests, cheapest first (success criteria set beforehand)
1. **Learned wiring**: per-class parents chosen by counted information against (a) the same number of fixed spatial parents and (b) parents chosen by information on pooled all-class data, equal table budget. Pass: class-specific beats both by at least 1 point accuracy and 0.03 Shirt AP.
2. **Growth by surprise**: add context bits only where surprise is highest, against adding the same number at random. Pass: at least +1 accuracy at equal entries.
3. **Hierarchy**: parent bits from a coarser layer as extra context. Pass: at least +1 accuracy.
4. **Consistency repair** at inference under noise and shifts. Pass: at least +2 accuracy on shifted or noisy test images, no loss on clean.
5. **Staged learning** (0-4 then 5-9): old classes unchanged by construction; pass: all-class accuracy equal to joint training within 0.5.
6. **Whole**: clothing accuracy at least L's table (88.6) at at most 3 times its bytes, Shirt AP at least 0.80.

## Results so far (25 Oct 2026, SIMULATED, Fashion-MNIST, one seed)

**Kill test 1, learned wiring** ([genome_test1.py](../hw/brain/experiments/month5/genome_test1.py), [log](../hw/brain/experiments/month5/genome_test1.log); 3 parents per bit, 8 contexts per bit per class, same table budget):

| Wiring | Accuracy | Cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|
| A fixed spatial parents | 0.8098 | 0.695 | 0.422 | 0.473 |
| B parents chosen by counted information, pooled data | 0.8332 | 0.727 | 0.491 | 0.536 |
| C parents chosen by information per class | 0.8384 | 0.730 | 0.487 | 0.556 |

- **Learning the wiring from counted information pays**: B over A is +2.3 accuracy and +0.063 Shirt AP at the same table budget.
- **Class-specific wiring adds little**: C over B is +0.5 accuracy and +0.020 AP, short of the criterion (at least +1 and +0.03). 87% of bits get different parents for Shirt and T-shirt, yet the likelihood ratio gains only a little. Verdict: test 1 half passed (learned wiring yes, class-specific no, one seed).
- Still far from the whole-system criterion (88.6 and Shirt AP 0.80): 83.8 and 0.556 at 3 parents.

Related: [Docs index](INDEX.md), [Lessons from the failures](lessons_from_failures_25oct.md), [Connected structure](../hw/results/connected_structure.md), [Journal](journal.md)
