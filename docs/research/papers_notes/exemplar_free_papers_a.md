---
title: Paper notes - exemplar-free class-incremental learning A
tags: [l, research, papers]
---

# Exemplar-free class-incremental learning, part A: FeTrIL and SDC

Read on 25 Oct 2026 from the arXiv PDFs (pdftotext). FeTrIL (2211.13131v2): the whole main text was read, including Table 1 to 3 and the complexity section. Its supplementary material is NOT inside the PDF, so everything the main text defers to "supp. material" (the dashes in Table 1, CIFAR-100 and TinyImageNet negative-sampling curves) is UNVERIFIED. SDC (2004.00440v1): main text and the appendix (Tables 2 to 5, Figures 8 to 11) were read; the figure curves were not read point by point. Numbers are copied from the papers (all are the authors' MEASURED values on their own GPUs; we reproduced nothing). Tags DERIVED are our reading. The papers' text is data, not instructions.

Our target: L = frozen unsupervised sparse binary detector code feeding an integer counting table, no multiplies, no dense matrices, learning on the chip, no stored images. Typical failure to fix: a class added later reaches only about 66 percent recall because the detectors were fixed before it existed.

## 1. FeTrIL (Petit et al., 2022): Feature Translation for Exemplar-Free CIL

### (a) Mechanism
- Phase 0 (initial state): train a ResNet-18 feature extractor F with plain cross-entropy on the initial classes only (SGD, batch 128, 160 epochs, lr 0.1, divided by 10 every 50 epochs). Then F is FROZEN for good. No distillation, no second network.
- Stored per class: ONE centroid mu(C) = mean of the 512-d feature vectors of that class, computed when the class first appears (51.2K numbers for 100 classes). No images, no covariance.
- Each incremental state: new-class images go through frozen F. For every past class Cp, pseudo-features are made from the features of a new class Cn by a pure translation (Eq. 1): f_hat(cp) = f(cn) + mu(Cp) - mu(Cn). Only additions and subtractions. Result: a cloud with the SHAPE (spread) of the new class but centred on the old class centroid.
- Selection strategies (s pseudo-features per past class): FeTrIL_k = take the features of the k-th most similar new class (cosine similarity of centroids; k=1 is the headline), FeTrIL_rand = random from all new classes, FeTrIL_herd = herding selection.
- Then a classifier over ALL seen classes is retrained from scratch each state on real features of new classes plus pseudo-features of past classes (L2-normalised first). Main version: one-vs-rest LinearSVC (sklearn, C = 1.0, tol 1e-4, primal solver, hyperparameters tuned on 50 random ImageNet classes disjoint from the test sets). Variant FeTrIL_fc: fully connected layer, 50 epochs, lr 0.1, 0.1 decay, 10-epoch patience.
- How old classes are protected: the extractor never changes, so the stored centroids never go stale; the global classifier is re-fitted with fresh negatives for every old class (the pseudo-features). There is no weight-space regulariser.

### (b) What base training needs
- Standard protocol: CIFAR-100 and ImageNet-Subset 50 initial classes (then 5 states of 10, or 10 of 5) or 40 initial (20 states of 3, 60 states of 1); TinyImageNet 100 initial of 200; ILSVRC 500 initial of 1000. Initial data = all images of those classes (500 per class CIFAR/Tiny, 1300 ImageNet).
- The base set is therefore half the classes of a diverse dataset (50 to 500 classes). The paper has NO experiment with a small base (for example 6 of 10 classes, or 10 of 100) and no ablation on base size. UNVERIFIED for small base; the paper says only that the method "tends to favor past classes" and that "state 4" new-class accuracy fell likely due to domain shift from the initial state. It also notes ILSVRC is more stable "since the pool of new classes available for pseudo-feature generation is larger", and that the frozen extractor is "sensitive to large domain shifts between incremental tasks" (said of transfer-learning methods in related work).
- DERIVED: quality depends on F already separating unseen classes. With a base of 6 classes F has seen almost no diversity, so features of new classes will be poor and the translated pseudo-features of old classes would be poor too. No data in the paper to quantify it.

### (c) Results (average top-1 incremental accuracy, 3-run mean, Table 1; ResNet-18; T = number of incremental states)
FeTrIL_1 (LinearSVC, k=1) vs best competitors:

| Dataset (initial classes) | T | FeTrIL_1 | Others quoted |
|---|---|---|---|
| CIFAR-100 (50 init) | 5 | 66.3 | SSRE 65.9, IL2A 66.0, PASS 63.5, DeeSIL 60.0, LUCIR 51.2 |
| CIFAR-100 (50) | 10 | 65.2 | SSRE 65.0, PASS 61.8, DeeSIL 50.6 |
| CIFAR-100 (50) | 20 | 61.5 | SSRE 61.7, PASS 58.1, DeeSIL 38.1, DSLDA 60.8 |
| CIFAR-100 (40 init) | 60 (1 class/step) | 59.8 | DSLDA 60.5 (only 2 methods can do 1-class steps) |
| TinyImageNet (100 init) | 5 / 10 / 20 | 54.8 / 53.1 / 52.2 | SSRE 50.4 / 48.9 / 48.2, PASS 49.6 / 47.3 / 42.1, DeeSIL 49.8 / 43.9 / 34.1 |
| TinyImageNet | 100 (1 class/step) | 50.2 | DSLDA 52.6 |
| ImageNet-Subset (50 init) | 5 / 10 / 20 | 72.2 / 71.2 / 67.1 | PASS 64.4 / 61.8 / 51.3, DeeSIL 67.9 / 60.1 / 50.5, DSLDA 71.3 / 71.2 / 71.0 |
| ImageNet-Subset (40) | 60 | 65.4 | DSLDA 70.8 |
| ILSVRC (500 init) | 5 / 10 / 20 | 66.1 / 65.0 / 63.8 | DeeSIL 61.9 / 54.6 / 45.8 |

The paper text says FeTrIL_1 is best in 11 of 12 configurations, but its own Table 1 includes DSLDA, which is higher in several (TinyImageNet T=100, ImageNet-Subset T=20 and T=60, CIFAR-100 T=60). The "11 of 12" count seems to leave DSLDA out; read it as a caveat (DERIVED). No MNIST-like dataset appears anywhere.

Ablations:
- Selection strategy (Table 3, T=5, CIFAR-100 / TinyImageNet / ImageNet-Subset): k=1 66.3 / 54.8 / 72.2; k=5 65.7 / 53.8 / 72.2; k=10 65.1 / 53.8 / 71.6; herding 66.2 / 53.8 / 72.1; random 65.1 / 51.5 / 70.3. Authors' conclusion: "the geometric translation toward the centroid of the past class is by far more important than the new classes features sampling policy". Closest-class source is best by 1 to 3 points.
- Translation vs none: DeeSIL (same frozen extractor, linear classifiers trained within each state only, no cross-state negatives) falls from 60.0 (T=5) to 38.1 (T=20) on CIFAR-100 and 67.9 to 50.5 on ImageNet-Subset, while FeTrIL holds 61.5 and 67.1. So the pseudo-features supplying cross-state negatives is the gain (about 23 points on CIFAR-100 T=20).
- Final layer: LinearSVC beats fully-connected, especially with many steps (numbers only in a figure/text, UNVERIFIED).
- Negative-sampling ratio r (ImageNet-Subset T=10, Figure 4): one-vs-all 71.2; r=25 70.8; r=10 70.0; r=1 67.3.
- vs exemplar methods with 20 stored images per class (Table 2, T=5 / T=10): CIFAR-100 FeTrIL 66.3 / 65.2 against LUCIR+AANets 66.7 / 65.3, Mnemonics+AANets 67.6 / 65.7, PODNet+AANets 66.3 / 64.3; ImageNet-Subset FeTrIL 71.9 / 70.8 against PODNet+AANets 77.0 / 75.6. (The ImageNet-Subset T=5 FeTrIL value is 72.2 in Table 1 and 71.9 in Table 2; the paper does not explain the difference. Noted.)
- Past vs new accuracy (TinyImageNet T=10, Fig. 5): FeTrIL stays biased to past classes (gap smaller than SSRE's bias toward new classes).

### (d) Operations and memory
- Generation: additions and subtractions only (no multiply). Centroid: a mean (one division per class, can be a shift if counts are powers of two; DERIVED).
- Classifier: LinearSVC on 512-d L2-normalised float features: dense matrix-vector products, a convex solver (multiplies, floats), retrained for ALL classes every state; cost O(n^2 s d) at the last state with one-vs-all, O(r n s d) with sampling. No backprop through F after the initial state. Initial training still uses full backprop (GPU).
- Memory: F 11.4M parameters (single model, vs 22.8M for distillation methods that keep old and new) plus 512 numbers per class. Time (ImageNet-Subset, T=10, incremental part only): 1 h 4 min 16 s on one CPU thread (Xeon E5-2620v4), 15 min 3 s with r=10; PASS needs 11 h 8 min 19 s on a V100.

### (e) Stated limitations / failure modes
- Frozen extractor: favours past over new classes; cannot adapt features to new classes.
- Pseudo-features only approximate the real old-class distribution (they copy the new class's shape, not the old one's); outliers in the source features are not filtered; authors plan to use the initial-feature distribution for better pseudo-features.
- Sensitive to domain shift between initial and later classes (state 4 of TinyImageNet).
- Needs a large and diverse base (50 to 500 classes). Small base: not tested (UNVERIFIED).
- Classifier is retrained over all classes every step (cost grows with classes).

### (f) Fit to L and the one test
- Fit: this is the closest published match to L's situation: frozen representation after base training, one stored centroid per class, no images, additive-only pseudo-sample generator. The gain it reports comes from giving the new-vs-old classifier negatives for old classes, not from adapting the features. L's frozen detectors have the same property (no adaptation), so the paper both confirms the design choice and says what it costs (new classes favour a bias toward old ones, domain shift hurts).
- Mismatches (DERIVED): (1) L's old classes already have counting tables that do not change; the open problem is a NEW class whose examples produce weak detector activations. (2) The paper's classifier is a float LinearSVC; L would need a count-based discriminator. (3) The paper's base is 50 to 500 diverse classes; ours is 6 of 10.
- One small test: freeze the detector layer after training on 6 digit classes. For each new class (7 to 10), store only a per-detector firing-rate centroid (integer counts per detector per class). Build pseudo-activations for old classes by translation in the integer domain (new-class binary code, add the per-detector firing-rate difference old minus new, re-binarise at a threshold, clip to 0/1). Train/calibrate the new class's counting table against both the real new examples and the translated pseudo-old examples, versus a baseline that uses only real new examples. Report recall of the new class at 20/50/100 examples and old-class accuracy, with k=1 nearest source class versus random source (the paper's cheapest ablation). Pass: new-class recall above 66 percent without lowering old-class accuracy; the useful result is whether translation helps when the base is only 6 classes, which the paper never tested.

## 2. SDC (Yu et al., 2020): Semantic Drift Compensation for CIL

### (a) Mechanism
- Setting: embedding network (ResNet, 512-d normalised output) trained with metric (triplet) loss, classified by Nearest Class Mean (NCM): prediction = argmin over classes of dist(z, mu_c); mu_c = mean embedding of the class (Eq. 2, 3). Triplet loss L_T = max(0, d+ - d- + m).
- Nothing is frozen: the whole network is fine-tuned on each new task's data (Adam, batch 32, lr 1e-5 to 1e-6, 20 to 50 epochs). Optional regularisers added to the triplet loss with weight gamma: E-LwF (L2 between old and current embeddings of the current data), E-EWC (Fisher-weighted penalty, weight 1e7), E-MAS (weight 1e6).
- Stored per class: one prototype (the class mean embedding at the moment it was learned). No images.
- The idea: after learning task t the stored prototype of an old class is stale because the embedding moved (the semantic drift Delta = true mean after t minus stored mean). The drift of old-class data cannot be measured, but the drift of CURRENT-task data can: delta_i = z_i^t - z_i^(t-1) (embedding after minus before training task t, Eq. 9). Estimate the drift at an old prototype by a Gaussian-weighted average of the nearby current-data drift vectors (Eq. 10, 11): Delta_hat = sum_i w_i delta_i / sum_i w_i with w_i = exp(-||z_i^(t-1) - mu^(t-1)||^2 / (2 sigma^2)), sigma = 0.3 (0.2 for CIFAR-100). Update the prototype recursively: mu_hat^t = mu_hat^(t-1) + Delta_hat^(t-1 to t) (Eq. 12, 13).
- How old classes are protected: they are not frozen; their prototypes are moved to follow the net. Regularisers (EWC, LwF, MAS) additionally limit the drift. SDC is a post-hoc correction, complementary to them.

### (b) What base training needs
- Fine-grained experiments start from an ImageNet-pretrained ResNet-18 (CUB-200 and Flowers-102, 6 tasks; CUB 200 classes, so about 33 per task) and ImageNet-pretrained "without birds" (59 classes removed, Table 2) gives almost no difference. CIFAR-100 and ImageNet-Subset: no pre-training, first task has 50 classes, then 10 tasks of 5 (eleven-task protocol of Hou et al.). Ten-task: CUB 100 classes (10 per task) and Caltech-101 split into 10.
- Small base: the paper has no study of varying the base size. Closest evidence: a toy MNIST run with a 2-d embedding and two tasks of 5 classes each (illustration only, Fig. 4, no accuracy reported); a ten-task run with about 10 classes per task. For the hard datasets the authors admit that "freezing the first model" (E-Fix) beats most non-exemplar methods and is "partially due to the large number of classes in task 1".

### (c) Results (average incremental accuracy, NCM)
- Softmax vs embedding fine-tuning (Fig. 2, text): after all tasks, metric fine-tuning E-FT beats softmax FT by absolute gains 23.9 (CUB-200), 32.6 (CIFAR-100), 42.9 (ImageNet-Subset) points. Softmax + NCM on the same backbone (FT*) forgets as badly as FT. So the loss matters.
- Table 1 (6 tasks, last-task column T6, ImageNet-pretrained): CUB-200: E-Pre 52.1, E-Fix 50.3, FT 11.4, E-FT 37.4, E-FT+SDC 49.3, E-LwF 51.4, E-LwF+SDC 52.7, E-EWC 54.2, E-EWC+SDC 56.4, E-MAS 51.9, E-MAS+SDC 54.4. Flowers-102: E-Pre 73.6, E-Fix 76.9, FT 15.3, E-FT 29.1, E-FT+SDC 35.3, E-LwF 63.5, E-LwF+SDC 69.7, E-EWC 79.6, E-EWC+SDC 83.9, E-MAS 70.9, E-MAS+SDC 76.0. First-task accuracy 84.1 (CUB) and 98.2 (Flowers).
- SDC gain on plain fine-tuning: +11.9 (CUB) and +6.2 (Flowers); on the regularised ones +1.3 to +6.2 points (E-LwF on CUB +1.3; E-EWC Flowers +4.3). SDC is neutral or slightly negative in a few cells (E-MAS T2 on CUB 72.5 to 71.9; E-LwF+SDC on CIFAR-100 eleven-task 46.1 equals E-LwF 46.1; on ImageNet-Subset E-LwF+SDC 50.5 vs E-LwF 51.5).
- Cars-196 (Table 4, T6): E-FT 17.3, E-FT+SDC 18.2, E-LwF+SDC 33.9, E-EWC+SDC 32.2, E-Fix 30.5. SDC adds under 2 points there.
- Eleven-task (Table 5, final): CIFAR-100: E-Fix 46.3, E-FT 37.4, E-FT+SDC 44.8, E-EWC 40.8, E-EWC+SDC 46.1, E-MAS 43.1, E-MAS+SDC 46.3. ImageNet-Subset: E-Fix 50.5, E-FT 47.4, E-FT+SDC 50.9, E-EWC+SDC 51.5. The text reports E-EWC+SDC beats non-exemplar competitors by at least 27.6 points on CIFAR-100 and beats iCaRL-CNN by 7.1 and iCaRL-NME by 1.1 (Fig. 7; the plotted value is not in the text).
- IMPORTANT DERIVED reading: on CIFAR-100 and ImageNet-Subset the frozen-after-task-1 baseline E-Fix (46.3, 50.5) is as good as the best SDC combination (46.1 to 46.3, 51.5). So with a large first task the frozen model needs no drift compensation, and SDC mostly rescues methods that keep training.
- Ten-task (Fig. 6): E-MAS beats LwM by 21.2 points on CUB-200 (100 classes) and 29.0 on Caltech-101; SDC adds 6.4 and 1.4 points on top.
- Other ablations: angular and multi-similarity loss give similar long-sequence results to triplet (Table 3: E-FT 40.5 angular, 50.7 multi-similarity, vs 37.4 triplet; with SDC 45.5 and 56.1). VGG16, 4 tasks on CUB: E-EWC beats EWC by 30.1 and R-EWC by 22.1 points; SDC adds 1.6. Average-prototype-distance plot (Fig. 5) shows SDC reduces the gap between stored and true mean.

### (d) Operations and memory
- Training: backprop through a whole CNN every task (triplet loss with float multiplies; EWC needs the Fisher matrix diagonal, MAS the importance estimate). Memory: the network (kept as one model) + one 512-d prototype per class. For SDC itself: the previous-task embeddings z^(t-1) of the CURRENT task's data must be recorded before training starts (current data only; no old data). Then the Gaussian-weighted mean is O(n_current x n_old_classes x d): exp (not multiplier-free), squared distances, divisions. No SVD, no covariance.

### (e) Stated limitations
- SDC estimates the drift of old prototypes only from the drift of new-task data; it can only fix what lies near the new data. It is a partial correction (Fig. 5: reduces but does not remove the gap) and is weakest when new and old classes are far apart (Cars-196 gain under 2 points; ImageNet-Subset E-LwF+SDC 1 point worse than E-LwF). With very long sequences or large first tasks, freezing is as good (see above).
- The authors state that currently "methods without exemplars do not significantly outperform" the fixed-model baseline in the hard multi-task settings, and E-Fix shows no positive forward transfer (new tasks do not improve the representation).
- Sigma is a manually fixed constant (0.3 or 0.2), not learned. Triplet-loss fine-tuning needs a learning rate of 1e-5 to 1e-6, so training is very conservative (DERIVED).

### (f) Fit to L and the one test
- Fit: weak for the chip as it is now, strong as a diagnosis. L's detectors are frozen, so there is no drift; SDC addresses a problem L deliberately avoids. Its two reusable ideas: (1) prototypes (class means) are enough for the classifier, no stored images; (2) when the representation does move, the drift near the old class can be estimated from how the new data move, using only displacement vectors, neighbour weighting by distance (could be a small lookup table of weights instead of exp) and addition. That would only matter if L ever lets detector thresholds or selections adapt on-chip. Its own data also say: with a large, diverse first stage the frozen model is competitive, which supports L's frozen design but not a tiny base.
- Not a source of a recall fix for L today. One small test if we later allow detector adaptation: let the detector thresholds shift by a few integer steps on new-class data only; record each detector's code on the new examples before and after the shift (the new-class drift vector in binary: which detectors flipped); for each old class estimate its table drift as the average flip pattern of the new-class examples whose code is within Hamming distance h of the old class's stored centroid (sigma replaced by a Hamming radius, no exp); correct the old class's stored firing-rate centroid by that integer amount; compare old-class recall with and without the correction against the fully frozen detectors. If the frozen detectors win (expected from E-Fix), keep L frozen.

## 3. Combined verdict

- Both rely on one stored mean vector per class and no stored images, and both use additions plus (in the real papers) float classifiers or backprop; neither is multiplier-free end to end. Only FeTrIL's pseudo-feature step (translation by centroid difference) maps cleanly onto an integer, add-only chip.
- Base-training demands: FeTrIL 50 to 500 diverse base classes (extractor must generalise to unseen classes); SDC 50-class first task (or ImageNet pre-training) when training from scratch; plus ImageNet pre-training for the fine-grained sets.
- Tiny base (6 of 10 classes): neither paper tests it. FeTrIL could plausibly help the new-vs-old separation (its gain is exactly the cross-state negatives) but its frozen extractor needs a rich base which we do not have, so expect poor translated pseudo-features. SDC adds nothing for a frozen detector layer. Only a direct experiment (Section 1 f) can say. UNVERIFIED for small bases.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
