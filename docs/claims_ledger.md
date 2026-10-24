---
title: Claims ledger (24 Oct 2026)
tags: [l, claims, rules, evidence]
---

# Claims ledger: every claim about L, its status, and the rules for stating one

## Rules before a claim is written or said (adopted 24 Oct 2026 after repeated corrections)

1. **The strongest baseline I can build, not the quickest.** A baseline must be trained properly (epochs, augmentation, tuning budget equal to ours) before any comparison; the result is stated with that baseline's details. If only a weak baseline exists, the claim is written as "against a weak baseline" or not made.
2. **Nothing is chosen on test data.** Thresholds, rules and hyperparameters are picked on a held-out validation split; the test set is read once.
3. **Same stream, same protocol, same memory accounting** for every method in a table, or the table says exactly how they differ.
4. **No announcement from one run.** A result is TENTATIVE until it holds on a second seed or a second data set; only then VERIFIED. Differences under 0.5 points on one seed are noise.
5. **Look at where the error goes before explaining it** (confusion rows, per-class precision and recall, ranking quality) and state the explanation as a hypothesis until tested.
6. **A gain with a cost is not a result.** Find the cause of the cost and remove it, or record it as a trade-off (user rule, 24 Oct).
7. Label every number MEASURED, SIMULATED, ESTIMATED, MODELLED or PROJECTED; record failures as clearly as wins.

## Status of claims

| Claim | Status | Basis / what is missing |
|---|---|---|
| L's deployed table of 11 KB gives 88.65% on Fashion-MNIST | TENTATIVE | one seed; compared to an MLP from another script; [l_deployed_memory](../hw/results/l_deployed_memory.md) |
| L learns in stages with about 6 times less memory than replay and no stored images (Fashion-MNIST 81.5 against replay 1,000 images 81.4) | TENTATIVE | replay numbers from the literature at 12,000 images per stage, ours at 2,000; baselines not re-run on one stream; generative classifier (93.8 on Split MNIST) is level with L on digits; [staged_replay_baselines](../hw/results/staged_replay_baselines.md) |
| L learns from 1 to 10 examples per class better than a CNN trained from scratch and an ImageNet-pretrained ResNet-18, on MNIST | TENTATIVE | 3 draws, one data set per claim; no meta-learned comparator; [few_shot_two_brains](../hw/results/few_shot_two_brains.md) |
| On Fashion-MNIST L is better than a self-supervised CNN only at 1 to 5 examples per class | TENTATIVE | 3 draws |
| Episodic replay lifts the counting table with few examples (E=20: 82.1 at 100 examples against 72.5) | TENTATIVE | one data set, 3 draws |
| L's margin confidence is as good as a CNN's at spotting its own errors; better at noticing an unseen class | TENTATIVE | four of six classes done, died twice; CNN uses plain softmax (a better novelty detector would do better) |
| A team of four codes gives 90.43% on Fashion-MNIST (single view) | TENTATIVE | one seed; Shirt unchanged |
| A stronger CNN ranks Shirt better than L (AP 0.84 against 0.75; cluster accuracy 85.1 against 80.6) | TENTATIVE | one seed; supersedes the 'equal in the cluster' reading |
| Recruiting new detectors for a new class: plain is win-lose (+19.4 recall, -9.5 old); gating by beating the old detectors cuts the cost to -1.8 at 100 examples but loses recall at 20 | TENTATIVE (not adopted) | one draw, 2 classes; tolerance sweep running |
| Blame-routed detector learning (error passed to the detectors through table rows) improves accuracy or Shirt | **FAILED** | four configurations, no test gain; validation gains were selection noise; [design note](error_transport_design.md) |
| Class-specific detector dictionary improves clothing accuracy | **FAILED** | 88.29 against 88.81 for an unsupervised dictionary of equal size |
| Error-targeted detector boosting improves accuracy or Shirt AP beyond adding unsupervised detectors | **FAILED** | four-round test; differences within noise |
| L beats a CNN on accuracy | **FALSE** (not claimed) | Fashion-MNIST: 88.9 to 90.4 against 91.1 to 91.7 for small CNNs |
| 'Second sense' from the spoken name improves recognition | **WITHDRAWN** | the name is the label (oracle test) |
| First cascade: Shirt recall +10.7 | **WITHDRAWN** | gate chosen on test data; validated version +0.9 overall, no Shirt gain |
| '+3 to +6.5 points over a CNN at 50 to 300 examples per class' | **WITHDRAWN** | weak from-scratch CNN; with a self-supervised CNN the two are level |
| 'L is 15 points behind on Shirt, mostly label overlap' | **WITHDRAWN / partly** | irreducible error is about 3 to 4% (Ishida et al.); operating point explains part; a ranking gap remains |
| '74 times less energy than a CNN' | **CORRECTED** | it was against an int8 MLP 784-256-10 by operation count (ESTIMATED), not a CNN |
| Clause learner (positive-literal Tsetlin-style) works | **FAILED** | 66% on Fashion-MNIST |
| Tile layout routed, ESP32 power measured | **NOT DONE** | routing stuck at about 300 violations; no board result yet |

Related: [Docs index](INDEX.md), [Failure analysis](failure_analysis_clothing.md), [Status report](status_report_24oct.md), [Journal](journal.md)
