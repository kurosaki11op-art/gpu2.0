---
title: Dispatch research - early exit and power gating (reference reading, abstract level only)
tags: [spark, research, references, dispatch]
---

# Dispatch research (28 Oct 2026)

Question: can a small always-on stage decide early whether to wake a larger stage, and when does gating a block pay (break-even idle time, wake-up cost)? Rule: read abstract and conclusion first, full read only if useful. **Status: the abstracts and conclusions could not be read.** A fetch of the two arXiv papers failed ("arxiv.org" does not resolve from this session, so it is outside the allowed network domains). What follows comes only from search-result summaries, which are second-hand; treat them as pointers to read later, never as evidence of our results.

| reference | what the search summary says (not verified) | use for us |
|---|---|---|
| [BranchyNet, early exit](https://arxiv.org/pdf/1709.01686) | side classifiers at several depths; softmax entropy as confidence; confident samples exit early; reports lower time and energy and sometimes higher accuracy on LeNet, AlexNet, ResNet; a follow-up notes thresholds and branch positions are tuned by hand | the concept behind rule 2 and rule 3; it is a CNN method, so a concept reference only (the project rule: no CNN as a component of L). Our version uses the counting table's own margin, not entropy |
| [ReGate, power gating in NPUs](https://arxiv.org/pdf/2508.02536) | power gating in neural processing units; a longer wake-up delay lowers savings by lengthening break-even time | the break-even idea for the dispatcher's wake test |
| Retention SRAM with header and footer switches (found by search, source not opened) | a retention mode cuts leakage by about 98% with a break-even time of 1.5 us for an 8 KB macro (a paper's claim) | the retention-versus-off decision; used as an ASSUMED figure in the dispatch tests |
| Break-even time concept (several DATE and other papers in the search) | gating pays only if the idle time exceeds the time whose saved leakage equals the wake-up energy; state-retentive modes shorten it at the cost of residual leakage | definition used in test (c) |

Next reading, once arXiv is reachable: the BranchyNet abstract, conclusion and the confidence-threshold section; ReGate abstract and conclusion; then decide on a full read. The founder can allow the domain in the environment's network settings; I will not change settings myself.

Related: [Docs index](INDEX.md), [One chip, three layers](../../hw/results/one_chip_three_layers.md), [Dispatch tests](../../hw/results/dispatch_tests.md)
