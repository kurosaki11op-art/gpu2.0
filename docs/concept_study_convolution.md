---
title: Concept study - convolution (why it exists, how it is built, where it fails, our own fix)
tags: [spark, research, concept-study, method]
---

# Concept study: convolution (28 Oct 2026)

Founder's method (28 Oct 2026): before using or replacing a standard concept, learn why it exists, how it is constructed, where it is used and where it fails; then build our own method that fixes those flaws, and test it before building. Multiplication and matrices are allowed where a test shows they pay; a CNN (or any standard GPU architecture) is not allowed as a component of L, only as a labelled reference. This note is the first concept card. Statements marked REASONING are from general knowledge of the field, not measurements; statements marked with SIMULATED / ESTIMATED are our own numbers from this repo.

## 1. Why convolution exists (REASONING)

- **Local structure:** in pictures, nearby pixels are related; a small window carries meaning (an edge, a corner, a texture).
- **The same pattern can sit anywhere:** an edge detector useful at one position is useful at all of them, so one set of weights is **shared across positions** (translation equivariance). This cuts the number of parameters by orders of magnitude against a dense layer and generalises to shifted inputs.
- **Hierarchy:** stacking layers builds edges into parts and parts into objects.

## 2. How it is constructed (REASONING)

Slide a small window of weights over the input; at each position compute a weighted sum (multiply-accumulate); apply a nonlinearity (ReLU); reduce resolution by pooling (max or average) for small-shift invariance and a smaller next layer; stack; finish with a dense layer; train every weight together by backpropagation from the final error.

## 3. Where it is used (REASONING)

Image classification, detection and segmentation; also 1D versions for audio and sequences. Transformers have taken over much of language and some vision; convolutions remain common where compute and data are limited.

## 4. Its flaws and limits, with our own evidence

| flaw | evidence in this repo |
|---|---|
| **Dense compute that ignores content:** every filter is computed at every position for every image, however simple the image | the small CNN (32 filters) needs 248,768 multiply-adds per image: est. 260 nJ at int8, 2,300 nJ at float32 (ESTIMATED), against 29.9 nJ for L (ESTIMATED) |
| **Same effort for every input:** no notion of "this one is easy" | our routing sends only the least-sure 5 to 20% of images to a stronger pass and loses nothing (SIMULATED, [routed second pass](../hw/results/routed_second_pass.md)) |
| **Pooling discards where and how parts relate** | max pooling keeps "a pattern is somewhere in this window"; the relations between parts are lost (REASONING); L's pooled bits have the same limit, a two-level count recovers a little (+0.6, SIMULATED) |
| **Needs labelled data and backprop; forgets old classes when new ones arrive** | standard networks fell to about 20% after five stages while L kept 81.5 to 94.2% (SIMULATED, [staged learning](../hw/results/staged_mlp.md)) |
| **Brittle to corrupted input** | with 30% of the active bits corrupted, float networks fell to about 80% and our counting table kept 84.4% (SIMULATED, [foundations study](../hw/results/foundations_study.md)) |
| **Float weights are expensive to move and store** | weights and activations dominate the energy, not the multiply (ESTIMATED) |
| **Opaque features** | no direct way to read why a unit fired (REASONING) |

## 5. What L already does differently (SIMULATED where numbers are given)

Shared local detectors over all positions are L's own front end too (32 learned 5 by 5 pattern finders per channel, pooled), so the useful half of the concept is kept; what differs: detectors are binary and learned without labels, only the winner fires (sparse), the readout is a table of integer counters (no gradient), learning never overwrites, work is event-driven and routed. Measured, this reaches 88.85% at 29.9 nJ and 90.35% at 40.6 nJ with a matrix-free second pass, against 91.28% for a small CNN reference (SIMULATED accuracy, ESTIMATED energy).

## 6. What is still missing relative to the concept (hypotheses to isolate, not conclusions)

From the foundations study: on L's own code multiplication and depth add nothing at the readout; the CNN's last point comes with **graded responses** and **features shaped together with the readout**. Candidate flaws of our design that match the concept's strengths:

1. **Binary winner-only detectors lose how well each pattern matched.** A detector reports "won", not "won strongly". Our own fix to test: keep the match strength as a graded (multi-level) bit, using the popcount the detector already computes (no new multiply).
2. **Pooling keeps one bit per window.** Fix already tested: the two-level count bit (+0.6, SIMULATED); a spatial-relation bit between neighbouring detectors is untested.
3. **Features are fixed after unsupervised fitting.** Fix tested in a stand-in: error sent back to the pattern finders gave at most +0.4 to +0.7 (SIMULATED); not a large lever on its own.
4. **Where fine weighting genuinely pays:** inside the confusable group (T-shirt, Pullover, Coat, Shirt), a small dense network on L's own sparse code reached 83.5% four-way against 81.1% for L's table, Shirt recall 0.739 against 0.687 (SIMULATED, [hypothesis loop note](../hw/results/hypothesis_loop.md)). This is a place where multiplication and a small matrix pay, and it is not a CNN: a group specialist over L's sparse code, run only on routed images, with an event-driven first layer (adds of weight rows for the active bits only).

## 7. Tests proposed before any build (each with its cost beside it)

1. Match-strength bit on L's detectors (graded evidence from the existing popcount): accuracy and active bits.
2. Group specialist: a small weighted layer (hidden 16 to 64, ternary or int8) over L's sparse code for the confusable group, routed images only; accuracy and estimated energy against the matrix-free second pass (90.35% at 40.6 nJ).
3. Neighbour-relation bits (two detectors firing in adjacent windows) as a cheap stand-in for part relations.

Related: [Project memory](PROJECT_MEMORY.md), [Foundations study](../hw/results/foundations_study.md), [Routed second pass](../hw/results/routed_second_pass.md), [Docs index](INDEX.md)
