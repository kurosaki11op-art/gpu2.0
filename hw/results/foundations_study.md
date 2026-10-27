---
title: Foundations study - why standard networks multiply, and what replacing it costs
tags: [spark, results, foundations]
---

# Foundations study: multiplication, matrices and what we lose by replacing them (27 Oct 2026)

SIMULATED, Fashion-MNIST, numpy reference models trained for the study (not our chip), one seed each, run-to-run spread about 0.3 points. Scripts in `hw/brain/experiments/month5/`: `foundations_study.py` (E1 to E4, log `foundations_study.log`), `foundations_raw.py` (E5, logs `foundations_raw*.log`), `foundations_e6.py`, `foundations_e7.py`. Founder's question: why do GPUs multiply and use matrices instead of compare, shift, add, subtract, and could not knowing that be the reason for our failures. Method: test each property in isolation before building anything.

## Why the standard method exists (reasoning, not a measurement)

A weight times an input is a graded vote; a matrix is many votes at once and fits dense hardware; **smooth weights make gradients exist, so backprop can assign credit to every weight in one backward pass**; stacked layers compose features; weights interpolate between inputs. Binary inputs or ternary weights turn the multiply into an add or subtract. Data movement, not the multiply, dominates energy.

## Results

**E1 precision ladder, on L's own 4,608-bit code (reference points):**

| model | test accuracy |
|---|---|
| our counting table L (integer counters, margin rule) | 88.85 |
| softmax regression, float | 89.11 |
| one-hidden-layer network (256), float, backprop | 89.15 |
| linear model, weights quantised AFTER training to 8 / 4 / ternary / 1 bit | 89.17 / 88.21 / 85.91 / 83.51 |
| network, weights quantised after training to 8 / 4 / ternary / 1 bit | 89.23 / 88.51 / 86.31 / 79.76 (2 bit collapses to 22 to 25%) |
| network with ternary weights trained with the constraint (straight-through) | 89.47 |
| ternary weights AND binary hidden units (add-only inference) | 89.40 |

**E2 credit assignment (same network, same code):** backprop 89.15; feedback alignment (random fixed backward weights, no weight transport) 88.94; **frozen random hidden layer 80.97**.

**E3 interpolation (models trained on clean data, tested after removing and re-adding active bits):**

| damage | counting table | float linear | float network | ternary network | add-only network |
|---|---|---|---|---|---|
| 10% of active bits | 88.08 | 87.60 | 86.98 | 87.18 | 88.06 |
| 20% | 86.86 | 84.50 | 84.94 | 84.30 | 86.28 |
| 30% | **84.36** | 80.18 | 80.10 | 80.20 | 83.58 |
| blank a 3 by 3 block of positions | 85.64 | 85.30 | 83.78 | 84.64 | 86.76 |

**E4 energy per image (ESTIMATED, Horowitz 45 nm, 100 pJ per 64-bit weight word for all, 589 active bits of 4,608):**

| model | multiplies | adds | energy |
|---|---|---|---|
| dense float network | 1,182,208 | 1,182,208 | 64.5 uJ |
| float network, event-driven (skip zero inputs) | 153,265 | 153,265 | 8.4 uJ |
| ternary weights + binary hidden, event-driven | 0 | 151,985 | 0.49 uJ |
| our counting table | 0 | 5,887 | 0.074 uJ |

**E5 raw 28 by 28 pixels (small numpy networks, 6 epochs unless stated):** softmax 84.00; MLP 86.90; MLP ternary 86.31; CNN 16 shared 3 by 3 filters 89.00; CNN ternary 86.35. With 32 filters and 20 epochs: **CNN float 91.28**, all-ternary 88.52, conv filters 4-bit with ternary readout 88.30, conv ternary with float readout 89.99, conv float with ternary readout 90.46.

**E6 front end:** the CNN's pooled responses binarised (sparse code like L's) and read by OUR counting table: learned filters 88.0 to 89.0 (best 89.00 at 30% active), random untrained filters 85.4 to 88.1 (88.05 at 10% active, equal to the learned filters there). L's Hebbian code with the same table: 88.85.

**E7 what the dense network uses:** the CNN's own readout 91.28; a float readout retrained on its frozen pooled responses **89.62**; float readout on the binarised responses 89.58; our counting table on the 1-level code 89.00, 2-level 89.85, 3-level 89.70, 4-level 89.67.

## What this says (our own measurements)

1. **On L's code, multiplication, float precision and depth add nothing.** Float linear 89.11, network 89.15, ternary 89.47, add-only 89.40 against our counting table 88.85: the readout operation is not where L loses (about 0.3 to 0.6 points to float). Our integer counters are trained inside their constraint; the same weights quantised after training lose 3 points (ternary) or collapse (2 bit): a constraint must be present during learning.
2. **Learning the hidden layer matters, exact gradients do not.** Frozen random hidden layer 81.0, learned 89.1; feedback alignment 88.9 is as good as backprop. So error-driven shaping of features is what counts, and a random fixed feedback path may be enough (random connections, not weight transport).
3. **Counting and binary codes are more robust, not less.** Under 30% corrupted active bits the table keeps 84.4, float models fall to 80.1 to 80.2, the add-only network to 83.6. The assumption that multiplication gives smoother generalisation does not hold on this sparse binary code.
4. **Sparsity and constraints are where the energy goes.** Event-driven skipping of zero inputs cut the float cost 7.7 times, ternary add-only 17 times more, and the counting table another 6.7 times, with accuracy 89.4 against 88.85 for the table.
5. **Where our ceiling is: the features, shaped end to end.** The CNN reaches 91.28, +2.4 over L, but only when features and readout are trained together: its frozen features with a retrained float readout give 89.62 (+0.8 over L's table, equal to our table on the same features: 89.85). Binarising the responses loses nothing for a linear readout (89.58 against 89.62), and graded multi-level codes lift our table by +0.85 (89.00 to 89.85). Random filters with our table are almost as good as learned ones at sparse thresholds. So: (i) our counting readout equals a float readout on any given features; (ii) the remaining +1.7 comes from shaping the feature layer with the readout's error, end to end (the property backprop provides and that feedback alignment suggests can be approximated); (iii) L's Hebbian detectors are unsupervised and not shaped by the task, which matches the single-layer ceiling near 89 to 90.
6. **Ternary costs about a point per layer in a convolutional network** (conv filters ternary -1.3, readout ternary -0.8, both -2.8), but nothing in a wide readout over a sparse binary code.

## Implications for our failures (hypotheses to test, not conclusions)

- The deep and shared-weight attempts (L-Deep, convolutional clauses) tried to replace end-to-end error-driven feature learning without a replacement for it. The readout never needed replacing; the credit path to the features did.
- Next tests before building: (1) shape L's detectors with a task error signal through a random fixed feedback path (feedback alignment on a sparse binary front end) and see if the table gains toward 91; (2) a graded, multi-level code on L's own responses (the +0.85 gain seen on CNN features); (3) a CNN feature layer trained by feedback alignment instead of backprop, to see how much of 91 survives.

Related: [Results index](INDEX.md), [Thinking synthesis](../../docs/research/thinking_synthesis.md), [L-Deep attempts](ldeep_attempts.md), [Boolean error transport](boolean_error_transport.md)
