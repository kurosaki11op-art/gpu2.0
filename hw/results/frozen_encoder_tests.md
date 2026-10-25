---
title: Tests from the 25-paper reading - feature-level dreams and an explicit old-versus-new gate
tags: [l, accelerator, continual-learning, gate-network, forgetting]
---

# Feature-level dreams and an explicit old-versus-new gate (25 Oct 2026)

Tests suggested by [the synthesis of 25 papers](../../docs/research/exemplar_free_synthesis.md). Hard-gate integer learner ([boolean_error_transport](boolean_error_transport.md)), MNIST, classes 0-4 then 5-9, no stored images, 500 + 500 hidden and 1,000 output gates unless stated, 4 epochs per stage, one seed, SIMULATED. Script [bool_local_growth.py](../brain/experiments/month5/bool_local_growth.py); logs [bool_feature_dreams.log](../brain/experiments/month5/bool_feature_dreams.log), [bool_gate_test.log](../brain/experiments/month5/bool_gate_test.log).

## Test 1: dreams at the feature level (layer 0 frozen, only upper layers grow)

Dreams are bits of the first gate layer's output, sampled from per-class counted statistics (rates, or 10 prototypes), fed through the old frozen upper layers; new nodes learn only in the upper layers.

| Setting | Old | New | All 10 |
|---|---|---|---|
| no dreams | 11.9 | 82.7 | 46.3 |
| feature dreams, independent bits | **72.9** | 53.9 | 63.6 |
| feature dreams, 10-prototype mixture | 66.1 | 64.4 | 65.3 |
| (reference) pixel dreams, every layer grows | 64.6 to 65.8 | 76.3 to 77.5 | 70.3 to 71.2 |

Reading: feature-level dreams keep more of the old classes (72.9 against 65) as the papers predict (feature replay 41.5 against pixel replay 9.7 on CIFAR-100), **but the new classes get worse (54 to 64 against 77)** because the frozen first layer offers no new features for them. The total is lower (63.6 to 65.3 against 70 to 71). This is the frozen-encoder trade-off in one table: a frozen layer protects what was learned and blocks learning what is new. One seed, TENTATIVE.

## Test 2: explicit old-versus-new gate from the raw maximum score

New nodes trained on new data only (softmax over the new classes), old nodes frozen; at test time an image goes to the old classes if the maximum raw old-group score reaches the 10th percentile of the stage-1 training images, else to the new classes.

| Stage-1 network | Closed-set accuracy (classes 0-4) | AUROC old vs new | Old | New | All |
|---|---|---|---|---|---|
| 250 + 250 gates, 4 epochs | 89.3 | 0.780 | 84.5 | 23.7 | 54.9 |
| 1,000 + 1,000 gates, 8 epochs | 92.3 | 0.819 | 87.6 | 28.9 | 59.1 |

Reading: AUROC rises with closed-set accuracy (0.78 to 0.82 for 89.3 to 92.3), the direction the open-set papers report (correlation 0.95, AUROC 0.986 to 0.993 for a 99% classifier on MNIST), but our gate network is far from that accuracy, so the gate still sends most new images to the old classes (new accuracy 24 to 29). An explicit gate would need a much stronger closed-set classifier than a few thousand random-wired gates provide. One seed.

## Answer to "with a frozen encoder our chip cannot learn continuously"

Correct. A frozen encoder lets the counting table keep adding classes and examples, but the features themselves cannot change; that is the original L Cortex limit (a new class reaches only about 66% recall because the detectors cannot adapt). The papers offer three ways out, none solved without stored samples: protect only the detectors old classes depend on and let the rest adapt (EFC, needs backprop and a covariance matrix), grow new detectors and replay old classes at the feature level (our test 1: old classes kept, new ones weaker), or keep a small buffer of old codes (class-incremental MNIST 91.0 at 50 per class against 98.3 joint). The staged buffer test is the open measurement.

Related: [Results index](INDEX.md), [Local layers and neurogenesis](local_growth_staged.md), [Frozen deep features in staged learning](frozen_deep_features_staged.md), [Synthesis of 25 papers](../../docs/research/exemplar_free_synthesis.md), [Journal](../../docs/journal.md)
