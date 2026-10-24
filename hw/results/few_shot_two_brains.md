---
title: Learning with few examples - two brains (24 Oct 2026)
tags: [l, few-shot, results, design]
---

# Few labelled examples per class, and the two-brain design (SIMULATED/MEASURED on CPU, Fashion-MNIST, 3 to 4 random draws of the labelled examples, accuracy on all 10,000 test images)

Scripts `hw/brain/experiments/month5/learning_curve.py`, `learning_curve2.py`, `learning_curve3.py` (logs `learning_curve_fashion.log`, `learning_curve2_fashion.log`, `learning_curve3_f32.log`). All methods see the same labelled examples. **Caveat:** L and the code baselines learn their detectors from 12,000 unlabelled training images (no labels); the CNN gets no unlabelled data, so the CNN is handicapped.

## 1. Finding: L's counting table is the weak part with few examples (failure)

| Examples per class | L counting table | L + IMPRINT + short sleep | Class means on L's code | CNN (raw pixels, flip/shift) |
|---|---|---|---|---|
| 1 | 27.2 | 48.4 | 51.8 | 42.1 |
| 5 | 46.8 | 58.6 | 66.3 | 64.3 |
| 10 | 55.9 | 55.9 | 70.0 | 69.6 |
| 50 | 73.9 | 73.9 | 75.2 | 75.8 |
| 300 | 83.7 | 83.7 | 75.8 | 77.5 |

The code is good (class means on it beat the CNN at 1 to 5 examples); the counting table needs many examples, IMPRINT (made for up to 4 examples per class) rescues only 1 to 5 and is inert beyond, and the table is erratic in the middle (72.5 +- 5.4 at 100).

## 2. Design: two brains (as in complementary learning systems)

- **Fast brain (hippocampus-like, episodic):** one write per example, no training. Two forms: class-mean codes (cost: 10 x 4,608 counters, about 46 KB) and stored exemplars (about 590 active-bit indices per image, about 1.2 KB each at 16-bit indices; 300 per class = 3.5 MB: a replay-like memory, so state that cost).
- **Slow brain (cortex-like, statistical):** L's existing counting table with consolidation (slow table, dreams).
- **Arbitration:** below about 10 examples per class the fast brain alone; above, a z-scored sum of the three scores (class means, best exemplar match, counting table).

| Examples per class | Fast: class means | Fast: exemplars | Slow: counting table | **Two brains: sum of 3** | CNN |
|---|---|---|---|---|---|
| 1 | 52.2 | 52.2 | 29.7 | 48.9 (use fast alone: **52.2**) | 42.1 |
| 2 | 59.3 | 58.8 | 41.0 | 53.8 (fast alone **59.3**) | 52.6 |
| 5 | 65.7 | 66.9 | 51.8 | 62.0 (fast alone **66.9**) | 64.3 |
| 10 | 68.7 | 69.8 | 61.9 | 69.4 (fast alone **69.8**) | 69.6 |
| 20 | 71.6 | 72.9 | 63.5 | **72.9** | 73.4 |
| 50 | 74.8 | 76.0 | 74.7 | **79.1** | 75.8 |
| 100 | 75.4 | **78.7** | 72.5 | 77.3 | 75.5 |
| 300 | 75.6 | 81.1 | 83.7 | **84.0** | 77.5 |

(Detectors fitted on 12,000 unlabelled images of all classes, 32 per channel; fitting on all classes instead of only classes 0 and 1 changed the fast brain by under 0.5 points.)

## 3. Reading

- Few examples: the two-brain rule (fast brain alone) gives 52, 59, 67% at 1, 2, 5 examples per class, **9 to 10 points above the CNN at 1 example and 2 to 7 points at 2 and 5**; from 10 to 20 examples it is level with the CNN; at 50 it is **+3.3** and at 300 **+6.5** above it (84.0 against 77.5).
- This is a modest advantage, not a breakthrough: with 1 example per class still only 52% (the best published prototype-style few-shot methods use pretrained deep features; not compared here), and the arbitration rule is picked from the same 3 draws (needs a validation protocol).
- The chip implication: the "fast brain" is cheap (class means: one add per active bit per example, no training), the "slow brain" is what L has. The z-score uses a division and a standard deviation; a hardware version needs shifts and an approximation (not yet designed).

## 4. Not done

Consolidation from the fast brain to the slow table by replay (sleep), IMPRINT beyond 4 examples, a validation-chosen arbitration, other data sets (MNIST, real photos), unlabelled-pretrained CNN baseline.

## Round 2 (24 Oct, `learning_curve3.py` on MNIST, `learning_curve4.py`; logs `learning_curve3_mnist.log`, `learning_curve4_fashion.log`)

**A fairer CNN baseline changes the comparison (correction to section 3).** A convolutional autoencoder pretrained on the same 12,000 unlabelled images, encoder frozen, linear head on the few labels:

| Examples per class (Fashion-MNIST) | Fast brain (class means) | Slow table | Slow table + sleep | Sum of 3 (table with sleep) | AUTO (rule chosen by 2-fold CV on the labelled examples) | CNN, self-supervised encoder |
|---|---|---|---|---|---|---|
| 1 | **52.2** | 29.7 | 10.0 | 43.8 | **52.2** | 46.1 |
| 2 | **59.3** | 41.0 | 31.1 | 51.5 | **59.3** | 55.4 |
| 5 | **65.7** | 51.8 | 38.2 | 60.7 | **65.7** | 64.7 |
| 10 | 68.7 | 61.9 | 54.5 | 67.9 | 69.0 | **70.2** |
| 20 | 71.6 | 63.5 | 73.0 | **75.7** | 71.6 | 74.2 |
| 50 | 74.8 | 74.7 | 79.3 | **80.1** | 78.5 | 79.7 |
| 100 | 75.4 | 72.5 | 80.7 | **81.9** | **81.9** | 82.1 |
| 300 | 75.6 | 83.7 | 84.4 | 84.8 | 84.8 | **85.0** |

- **With a self-supervised CNN the advantage shrinks to 1 to 2 examples per class** (52.2 against 46.1 and 59.3 against 55.4, 5 against 64.7: +6, +4, +1); from 10 examples per class the CNN is level (differences 0.2 to 1.5 points, within noise). The earlier claim of +3 to +6.5 points over a CNN at 50 to 300 examples came from a CNN trained from scratch on a handful of images, which was a weak baseline. **Do not quote it.**
- **Sleep consolidation** (the slow table learns from dreams drawn from the fast brain's class means) **fails with very few examples** (10.0% at 1 example: the dreams swamp the real example) **but helps from 20 per class on** (63.5 to 73.0 at 20, 72.5 to 80.7 at 100). So it must be gated by example count.
- **The validated rule (AUTO) works as intended:** it picks the fast brain at small n, and matches the best rule at 100 to 300 (81.9, 84.8); at 50 it is 1.6 points below the best (variance).
- **MNIST** (class means / exemplars / table / sum of 3): 1 example 54.2 / 54.2 / 20.6 / 50.7; 5 examples 79.2 / 77.2 / 44.9 / 76.3; 10 examples 84.6 / 84.4 / 67.1 / 84.1; 50: 91.0 / 92.7 / 84.0 / 93.0; 300: 91.8 / 96.1 / 95.9 / 96.7. No self-supervised CNN run on MNIST yet.

**Honest summary:** on a fair baseline L's two-brain design is better only at 1 to 5 examples per class (by 1 to 6 points) and level beyond; its distinguishing properties are no gradient training, a cheap one-write fast brain and the sparse table, not a higher few-shot accuracy.

## Round 3: MNIST against both CNN baselines, and real colour photos (24 Oct)

Logs `learning_curve4_mnist.log`, `learning_curve_mnist.log`, `learning_curve_photos.log`.

**MNIST (accuracy %, 3 draws), the two-brain AUTO rule against two CNN baselines:**

| Examples per class | Two brains (AUTO) | Float logistic regression on L's code | CNN from scratch (flip/shift augmentation) | CNN with self-supervised encoder |
|---|---|---|---|---|
| 1 | **54.2** | 45.5 | 42.2 | 26.2 |
| 2 | **66.0** | 56.9 | 55.8 | 38.8 |
| 5 | **77.0** | 75.9 | 75.5 | 60.7 |
| 10 | 85.6 | **86.5** | 80.0 | 68.9 |
| 20 | 89.8 | **91.8** | 84.1 | 77.3 |
| 50 | 94.3 | **94.7** | 87.0 | 83.9 |
| 100 | 95.5 | **95.9** | 88.9 | 86.6 |
| 300 | **96.7** | (not run) | (not run) | 88.3 |

- On MNIST the two-brain design is **10 to 12 points above the best CNN baseline at 1 to 2 examples per class and 5 to 7 points above it from 10 to 100**. The frozen-autoencoder CNN is a weak baseline on MNIST; the from-scratch CNN is the stronger of the two here.
- A plain float logistic regression on L's code is as good as or slightly better than the counting-based two-brain rule from 10 examples up: **the asset is L's sparse detector code, not the counting rule.**
- Not compared: pretrained deep features or meta-learned few-shot methods (prototypical networks and similar), which would likely be stronger at 1 to 5 examples; those need external data.

**Real colour photos (4 classes: T-Shirt, Shirt, Longsleeve, Outwear, 1,720 train / 574 test photos, fixed split; balanced accuracy %, chance 25; 3 draws):**

| Labelled photos per class | Fast brain (class means) | Counting table | Sum of 2 | CNN, self-supervised encoder |
|---|---|---|---|---|
| 1 | **35.2** | 30.5 | 33.3 | 28.5 |
| 5 | **41.2** | 32.8 | 39.1 | 33.4 |
| 10 | 43.7 | 35.6 | **46.6** | 39.7 |
| 20 | **49.0** | 30.2 | 43.3 | 43.3 |
| 50 | 51.3 | 50.8 | **55.0** | 52.1 |

- On real photos with backgrounds all methods are weak (35 to 55% on four garments from 1 to 50 photos per class). The fast brain leads the self-supervised CNN by 3 to 7 points up to 20 photos per class and is level at 50. The counting table is unusable below 50 photos (Shirt recall 0 to 34%). Small test set (574 photos); the photos have backgrounds (not removed).

**Updated honest summary.** Few-shot learning is where L's code (not its counting rule) is genuinely strong on MNIST (54% from one example, 85.6% from 10, against 42% and 80% for a CNN from scratch). On Fashion-MNIST the advantage is small and only at 1 to 5 examples, on real photos moderate and absolute accuracy low. All baselines are simple CNNs; no pretrained or meta-learned comparators.

Related: [Results index](INDEX.md)

## Round 4: pretrained-feature baseline (24 Oct, `pretrained_fewshot.py`; logs `pretrained_fewshot_mnist.log`, `pretrained_fewshot_fashion.log`; MEASURED on CPU, 3 draws)

ImageNet-pretrained ResNet-18 (timm `resnet18.a1_in1k`, 1.28 M labelled images of outside data), images upsampled to 64 x 64, 512 features, labelled examples drawn from the first 20,000 training images:

| Examples per class | MNIST: class means / logistic regression / 1-NN | Fashion-MNIST: class means / logistic regression / 1-NN |
|---|---|---|
| 1 | 45.8 / 43.0 / 45.8 | 48.9 / 48.5 / 48.9 |
| 2 | 52.9 / 54.2 / 52.7 | 53.3 / 53.9 / 53.4 |
| 5 | 63.3 / 66.7 / 59.2 | 62.7 / 64.7 / 60.2 |
| 10 | 67.4 / 74.5 / 64.5 | 66.3 / 69.7 / 64.1 |
| 20 | 71.7 / 82.2 / 70.5 | 70.6 / 74.0 / 67.6 |
| 50 | 75.6 / 86.9 / 74.6 | 72.6 / 77.5 / 71.6 |
| 100 | 77.5 / 89.9 / 77.8 | 73.6 / 79.7 / 73.5 |
| 300 | (not run) | 74.7 / 82.8 / 76.7 |

**Reading.** L's label-free sparse code with its two-brain rule is **ahead of ImageNet-pretrained features on MNIST at every n (54.2 against 45.8 at 1 example, 85.6 against 74.5 at 10, 95.5 against 89.9 at 100)** and ahead or level on Fashion-MNIST (52.2 against 48.9 at 1, 65.7 against 64.7 at 5, level at 10, ahead by 2 to 4 points from 50). Limits: a 28 x 28 grey picture is far from ImageNet, and a stronger backbone or meta-learned few-shot method (prototypical or matching networks trained on a source data set) may be better; neither was tried. The pretrained network is trained with 1.28 M labels, L's detectors with none.

**Clause learner (Tsetlin-style, positive literals, `tm_sparse.py`), valid run only after the numba-cache bug fix (100 clauses per class):** 67.8% at epoch 2 and 66.7% at epoch 4 on Fashion-MNIST; still training. The earlier 40-clause and 100-clause results were invalid (cached constants) and are marked as such.

**Detector grid:** 128 detectors per channel give 89.82 against 89.89 for 64: the one-layer detector code saturates near 89.9%.

## Round 5: adding one NEW class to a trained model (24 Oct, `newclass.py`, `newclass.log`; SIMULATED, Fashion-MNIST, 3 new classes (Dress, Shirt, Boot) x 2 draws)

A model trained on the other 9 classes (54,000 images) meets the tenth class with n labelled examples. L: slow table (staged stage with imprint + sleep) and fast brain (class means). CNN (small, trained on the 9 classes, accuracy on those 9 classes in its own 9-way decision 90.7%): fine-tuned on the new images only; fine-tuned with a replay buffer of 20 old images per class.

| New examples | Method | New-class recall % | Old-class accuracy % (10-way) |
|---|---|---|---|
| 1 | L slow table (staged + imprint) | **17.9** | 86.5 |
| 1 | L fast brain | 8.0 | 78.2 |
| 1 | CNN, new images only | 86.9 | 51.7 |
| 1 | CNN + replay | 0.0 | 88.9 |
| 5 | L slow table | **47.2** | 85.7 |
| 5 | L fast brain | 39.7 | 78.0 |
| 5 | CNN + replay | 30.7 | 88.4 |
| 20 | L slow table | 51.9 | 86.4 |
| 20 | L fast brain | 59.2 | 77.4 |
| 20 | CNN + replay | **66.0** | 87.3 |
| 100 | L slow table | 72.8 | 85.2 |
| 100 | L fast brain | 69.2 | 76.5 |
| 100 | CNN + replay | **91.1** | 80.6 |
| 100 | CNN, new images only | 100 (new class predicted for everything) | 3.2 |

**Reading.** Fine-tuning a CNN on the new class alone forgets the old ones (old accuracy 52% at 1 example, 3% at 100). A CNN with a small replay buffer is the fair competitor: it learns nothing from 1 example, is behind L at 5 (30.7 against 47.2), and overtakes L from about 20 (66.0 against 51.9), reaching 91.1 against 72.8 at 100 at the cost of old-class accuracy (80.6). **L's advantage is one to five new examples without forgetting; beyond that replay wins.** L's old-class accuracy (85 to 86%) is 3 to 4 points below the replay CNN's (87 to 89%). One architecture, small samples; not compared with prototype-based or meta-learned class-incremental methods.

## Round 6: fixing the weak counting table with episodic replay (24 Oct, `few_replay.py`, `few_replay.log`; SIMULATED, Fashion-MNIST, 3 draws)

**Why the table was weak (failure analysis):** it learns by correcting its own mistakes, one pass over the data. With 1 to 20 examples there are almost no mistakes to learn from, so the counters stay near their start; the earlier "more passes" test used 60,000 images, where one pass already suffices, so it never tested this regime. Bernoulli "dreams" from class means (round 2) swamped the real examples at 1 to 10 per class.
**Fix:** re-present the stored REAL examples E times (shuffled each pass), as hippocampal replay does in sleep. Rule-compatible: the fast memory stores the codes, the slow table is trained by its usual counting update, no new operation.

| Examples per class | E=1 | E=5 | E=20 | E=20 + IMPRINT (up to 4) | Fast brain (class means) | CNN, self-supervised (round 2) |
|---|---|---|---|---|---|---|
| 1 | 29.7 | 29.7 | 29.7 | **49.2** | 52.2 | 46.1 |
| 2 | 41.0 | 47.4 | 47.4 | **55.1** | 59.3 | 55.4 |
| 5 | 51.8 | 60.0 | 60.0 | **62.0** | 65.7 | 64.7 |
| 10 | 61.9 | 70.6 | 70.6 | 70.6 | 68.7 | 70.2 |
| 20 | 63.5 | 72.3 | 73.7 | 73.7 | 71.6 | 74.2 |
| 50 | 74.7 | 79.0 | 80.0 | 80.0 | 74.8 | 79.7 |
| 100 | 72.5 | 82.0 | 82.1 | 82.1 | 75.4 | 82.1 |

**Result:** replay lifts the table by 8 to 10 points from 5 to 100 examples per class, removes the erratic dip at 100, and makes the table alone as good as the fast brain from 10 examples and level with a CNN that uses a self-supervised encoder from 10 examples up (82.1 against 82.1 at 100). At 1 to 5 examples the fast brain and IMPRINT remain better. Also fixed the earlier "table unusable below 50": it is now usable from 10.
**Limits:** one data set, 3 draws, E up to 20 (gain saturates between E=5 and E=20); the part about adding one new class (replay of the new examples) is still computing and will be added.

## Round 7: replay for a new class (24 Oct, `few_replay_part2.py`, `few_replay_part2.log`; SIMULATED, 2 new classes (Shirt, Boot), one draw)

New-class recall % / old-class accuracy % (10-way) when the new class's examples are replayed E times by the staged table:

| New examples | E=1 | E=5 | E=20 |
|---|---|---|---|
| 5 | 45.8 / 85.8 | 31.6 / 87.7 | 39.2 / 86.9 |
| 20 | 49.8 / 86.9 | 54.6 / 86.5 | 53.1 / 86.0 |
| 100 | 66.3 / 86.2 | 66.0 / 85.0 | 61.7 / 84.9 |

**Replay does not fix adding a new class** (the CNN with a 20-per-class replay buffer reaches 66.0 at 20 and 91.1 at 100). Failure pattern: the CNN adapts its features to the new class, L's detector code is fixed, so a new class must be written in detectors made for the old ones. Next design: recruit new detectors from the new class's own images (`newclass_recruit.py`).

## Round 8: detector recruitment for a new class, and the cause of its cost (24 Oct, `newclass_recruit.py`, `newclass_gated.py`; logs beside them; SIMULATED, 2 new classes (Shirt, Boot), one draw; both arms use the same stored images (20 per old class + the new examples) and 10 replay passes)

| New examples | Variant | New-class recall % | Old-class accuracy % (10-way) | New bits active per image |
|---|---|---|---|---|
| 20 | no recruitment | 54.9 | 88.4 | 0 |
| 20 | plain recruitment (8 new detectors per channel) | 64.5 | 85.7 | 397 |
| 20 | fit on novel patches only | 45.0 | 85.4 | 439 |
| 20 | gate only | 49.2 | 88.5 | 53 |
| 20 | fit on novel patches + gate | 52.0 | 87.2 | 59 |
| 100 | no recruitment | 72.2 | 86.3 | 0 |
| 100 | plain recruitment | 91.6 | 76.8 | 397 |
| 100 | fit on novel patches only | 94.0 | 78.3 | 411 |
| 100 | gate only | 83.5 | 84.7 | 37 |
| 100 | fit on novel patches + gate | 84.1 | 84.5 | 66 |

**Reading (under the win-win rule).** Plain recruitment is win-lose (+19.4 new-class recall, -9.5 old-class accuracy at 100 examples). **The cause of the old-class loss is that new detectors also fire on old-class images**: gating a new bit to fire only where it beats the best old detector cuts the loss to -1.6 to -1.8 while keeping +11.3 to +11.9 of recall at 100 examples. Still not win-win: -1.8 remains, and at 20 examples the gate is too strict (about 50 to 60 new bits per image) so new-class recall FALLS (49.2 and 52.0 against 54.9): lose-lose there. Fitting only on novel patches did not help. Next: a tolerance on the gate (`newclass_gated2.py`, margins 0, -2, -4, -6 match counts). Not adopted yet.

Related: [Results index](INDEX.md), [Few-shot imprint (month 4)](../brain/experiments/month4/fewshot_imprint.md), [Failure analysis](../../docs/failure_analysis_clothing.md), [Journal](../../docs/journal.md)
