---
title: Composition, first test - relations between two images
tags: [spark, results, thinking, composition]
---

# Composition, first test: a relation between two images (26 Oct 2026)

SIMULATED, Fashion-MNIST, one seed. Part 5 of the thinking plan, cheapest design first. Script `hw/brain/experiments/month5/relation_pairs.py`, log `relation_pairs.log`. Task: given two images (L's 4,608-bit detector codes), say whether they are the same class. Training pairs come only from classes 0 to 5; test pairs from the four unseen classes 6 to 9 (and from seen classes for reference); 60,000 balanced training pairs, 20,000 test pairs per set. All learned variants use L's own margin-trained counting table (2 outputs), no multiply.

| features | seen classes | UNSEEN classes |
|---|---|---|
| relation: bits where both are on, and where exactly one is on (9,216 bits) | 87.1 | 70.3 |
| concat: the two codes side by side (no relation) | 51.4 | 50.5 |
| pooled per detector (agreement counts as thermometer bins, 1,536 bits) | 83.1 | 71.7 |
| pooled per position | 81.0 | 73.2 |
| pooled both | 83.8 | 71.9 |
| overlap only: one number, |x AND y|, threshold chosen on seen training pairs, nothing learned | 73.2 | **79.1** |

- **The relation code generalises to classes never seen in training** (70 to 73% against chance 50%), and the side-by-side code does not (50.5%), so a relation between parts is learned by the counting table in a form that does not name the class.
- **But it does not beat the trivial baseline**: a single overlap threshold, with nothing learned, gets 79.1% on the unseen classes. Same/different on clothing is mostly solved by raw similarity, so this is a weak test of composition; the learned relation code adds nothing over it here.
- Pooling over positions (class-agnostic features) raised the unseen result by 1 to 3 points only.
- Not yet tested: held-out combinations of attributes (design 1: one counting table per attribute, leave-one-class-out), where similarity alone cannot do the job.

Related: [Thinking synthesis](../../docs/research/thinking_synthesis.md), [Hypothesis loop](hypothesis_loop.md), [Results index](INDEX.md)
