---
title: Paper notes - exemplar-free class-incremental learning C
tags: [l, research, papers]
---

# Exemplar-free class-incremental learning, papers C: FeCAM and ADC

Read from the arXiv PDFs (pdftotext, 25 Oct 2026): FeCAM arXiv 2309.14062v3 (NeurIPS 2023), ADC arXiv 2405.19074v1. Both read completely (main text, supplement, tables, algorithm boxes). All numbers are quoted from the papers (they are the authors' MEASURED numbers, on ResNet-18 and ViT, not on our hardware). Tags DERIVED are our own reading. UNVERIFIED = not in the text we could read. Target (L): binary sparse detector code, integer counting table, no multiplies, no dense matrices, learning on the chip.

## Paper 1. FeCAM (Goswami, Liu, Twardowski, van de Weijer)

### (a) Mechanism
- Setting: classifier-incremental. The feature extractor phi (ResNet-18, 512-d, or pretrained ViT-B/16, 768-d) is trained on task 1 only, then FROZEN. No training at all in later tasks.
- Stored per class: the prototype (mean feature) mu_y and a covariance matrix Sigma_y (D x D, after Tukey transform). "We store all the class prototypes ... we also store the covariance matrices for all classes." A cheaper variant stores ONE common covariance, updated as a class-count-weighted running mean (Eq. 6).
- Per class pipeline (Algorithm 1): mu_y = mean phi(x); Tukey ladder of powers on the features, phi~ = phi^lambda (lambda = 0.5; log if 0), only valid for non-negative (ReLU) features, so NOT applied for ViT; Sigma_y = Cov(phi~); shrinkage Sigma_s = Sigma + g1*V1*I + g2*V2*(1-I) (V1 = mean diagonal variance, V2 = mean off-diagonal covariance); correlation normalisation Sigma^(i,j) = Sigma(i,j)/(sigma(i) sigma(j)) so every diagonal is 1 (makes distances of different classes comparable).
- Classification: y* = argmin_y (phi~(x) - mu~_y)^T (Sigma^_y,s)^-1 (phi~(x) - mu~_y), the squared Mahalanobis distance (Eq. 10). Derived as the Bayes classifier under a Gaussian class model with equal priors; boundaries are quadratic, not linear.
- Drift of old class statistics: NONE to handle, because the backbone is frozen, so old statistics never move. The paper explicitly says the open problem is feature drift when the backbone is trained (future work: model covariance drift too).
- Hyperparameters: g1 = g2 = 1 (many-shot CIFAR100, TinyImageNet, ImageNet-Subset); g1 = 1, g2 = 0 (Split-CIFAR100, CoRe50 with ViT); g1 = g2 = 10 (Split-ImageNet-R); g1 = g2 = 100 (few-shot). lambda = 0.5. Base training: SGD lr 0.1, wd 1e-4, 200 epochs.

### (b) Base training needs
- Needs a STRONG feature extractor. Main benchmarks use 50 base classes of 100 (CIFAR100, ImageNet-Subset) or 100 of 200 (TinyImageNet); also 40 base + 20 steps of 3. Few-shot: 60 of 100 base classes (CIFAR100, miniImageNet), 100 of 200 (CUB).
- Key finding (Sec 3.1, Fig 4, CIFAR100 50-50): old (base-trained) classes: Euclid NCM 76.7, FeCAM common cov 75.9, FeCAM per-class 77.2 (equal within 1.3). For NEW classes and for all classes the figure shows values 26.5, 38.4, 47.0, 51.6, 57.2, 62.1; the bar-to-method mapping is UNVERIFIED from the text layer, but the paper states that Mahalanobis is far better than Euclid on new classes and per-class covariance is best. Message: base classes are fine with Euclid; NEW classes (never seen by the backbone) are spread, anisotropic, and need covariance.
- Small first task (Table 5, 20 base classes then 20 new per step): CIFAR100 Last/Avg: Euclid-NCM 30.6/50.0, FeTrIL 46.2/61.3, FeCAM 48.1/62.3. ImageNet-Subset: 35.0/54.5, 48.4/63.1, 52.3/66.4. Authors: "FeCAM still works ... average incremental accuracy is not very high ... because the representation learned in the first task is not as good."
- Pretraining with dissimilar classes (Table 7, DeiT-S/16 pretrained on 611 ImageNet classes with the CIFAR-like classes removed, Split-CIFAR100): FeCAM 68.6 last / 76.9 avg vs NCM 58.5 / 69.2 (vs 70.2/78.5 and 60.5/71.4 with full 1k pretraining). Small drop, FeCAM keeps its ~10 point edge.

### (c) Results (class-incremental, no task id, average incremental accuracy, ResNet-18, Table 1)
| Method | CIFAR100 T=5 / 10 / 20 | TinyImageNet T=5 / 10 / 20 | ImageNet-Subset T=5 / 10 / 20 |
| --- | --- | --- | --- |
| Eucl-NCM | 64.8 / 64.6 / 61.5 | 54.1 / 53.8 / 53.6 | 72.2 / 72.0 / 68.4 |
| FeTrIL | 67.6 / 66.6 / 63.5 | 55.4 / 54.3 / 53.0 | 73.1 / 71.9 / 69.1 |
| FeCAM common cov | 68.8 / 68.6 / 67.4 | 56.0 / 55.7 / 55.5 | 75.8 / 75.6 / 73.5 |
| FeCAM per-class cov | 70.9 / 70.8 / 69.4 | 59.6 / 59.4 / 59.3 | 78.3 / 78.2 / 75.1 |
| Joint upper bound | 79.2 | 66.1 | 84.7 |
(CIFAR100 and ImageNet-Subset: 50 base classes, T=5 or 10 steps, or 40 base + 20 steps; TinyImageNet: 100 base classes + 5/10/20 steps.)
- Pretrained ViT-B/16 (Table 2): Split-CIFAR100 (10x10) 85.7 (NCM 83.7, L2P 83.8, joint 90.9); Split-ImageNet-R 63.7 (NCM 55.7, L2P 61.6, joint 79.1); CoRe50 domain-IL 89.9 (NCM 85.4, L2P 78.3).
- Exemplar comparison (Table 3, CIFAR100 T=5, 11.17M params): FeCAM 70.9 avg / 62.1 last with no exemplars, versus iCaRL 65.4/56.3, WA 69.9/61.5, DER 73.2/66.2 (DER grows the model ~6x).
- Few-shot (5-shot, base model from ALICE; Avg over sessions): CIFAR100 ALICE 62.65 -> ALICE+FeCAM 64.80; miniImageNet 64.09 -> 66.88; CUB200 64.98 -> 66.78 (FACT 64.70 -> 65.80). Few-shot needs g1 = g2 = 100 (strong shrinkage).
- Ablation (Table 4, CIFAR100 T=5 Last/Avg, per-class covariance): Euclid 51.6/64.8; Euclid+Tukey 54.4/66.6; Mahalanobis full cov, no tricks 14.6/29.7 (collapses); +Tukey only 20.6/36.2; +shrinkage only 44.6/59.3; +Tukey+shrinkage 52.1/62.8; diagonal cov (variance normalised) +Tukey+shrinkage 55.2/66.9; full cov + shrinkage + correlation norm (no Tukey) 55.4/65.9; ALL: 62.1/70.9. ImageNet-Subset: Euclid 60.0/72.2; all 70.9/78.3; diagonal 64.0/74.1.
  What matters: (1) the normalisation across classes (+10 last-acc points over the same thing without it), (2) shrinkage (full-rank, CIFAR100 has 500 samples < 512 dims), (3) Tukey power transform (+1.8 to 6 points even for plain Euclid), (4) full covariance beats diagonal by about 7 (CIFAR) to 7 (ImageNet) last-acc points; the prototype with Euclid is a strong baseline already.
- Bayes quadratic vs sampling features and training a linear classifier (Fig 5, CIFAR100 T=5): Bayes 70.9 avg; linear classifier on sampled features 67.1 to 67.9 even with 20000 samples per class (curve values read from the plot, approximate).
- Speed: ImageNet-Subset T=5 incremental tasks, FeTrIL 44 min vs FeCAM 6 min on one RTX 6000.

### (d) Operations and memory
- Learning a class: one pass of forward features, a mean, a D x D covariance (outer products = multiplies), shrinkage, a power function, normalisation. No gradients in later tasks (backbone trained with backprop once on task 1).
- Inference: for each class a D x D matrix-vector product and dot product (D^2 multiplies per class), plus the matrix INVERSION at learning time. Heavy dense-matrix work. The diagonal version reduces to D multiplies per class and D numbers of storage, but still multiplies.
- Memory: per class D + D^2 floats (512-d: about 1 MB at float32; symmetric half storage halves it). Table 6, ImageNet-Subset: 53 MB after task 0 (50 classes) to 106 MB after 100 classes, versus 312 MB for 2000 stored exemplars. Diagonal: D numbers per class.

### (e) Stated limitations and failure modes
- Authors: "needs a strong feature extractor or a large amount of data in the first task ... not apt when training from scratch, starting with small tasks." Covariance drift not modelled if the backbone is trained.
- Without shrinkage and normalisation the full-covariance classifier is worse than plain Euclid (14.6 vs 51.6 last acc). Tukey transform invalid for features with negative values.
- Small first task (20 classes): gains over Euclid persist (+17 and +17 last-acc points) but absolute accuracy is low (CIFAR100 last 48.1).
- Hyperparameters per dataset (g1, g2 from 1 to 100) must be tuned. Per-class matrix storage grows linearly with classes.
- Not tested: a tiny base set like 6 of 10 classes, or a binary/quantised code. UNVERIFIED for those.

### (f) Fit to L and the one concrete test
- Fit: strong conceptual fit on the CLAIM, weak on the MECHANISM. The claim (new classes are anisotropic in a frozen feature space, per-class spread information beats a pure mean prototype, normalise across classes so scores compare) applies to us: our frozen detector code is exactly a frozen extractor that never saw the new class. The mechanism (Mahalanobis, inverse covariance, Tukey power, real-valued 512x512 matrices) is dense matrices plus multiplies and is excluded by the founder's rule. The only L-compatible members of the family are the per-dimension variance version (diagonal) and its integer-count analogue.
- Integer analogue: per class and per detector keep counts n_y(d) (how many of the class's samples fired detector d) and the class sample count N_y. A detector's log-odds or a quantised firing rate p_y(d) = (n_y(d)+a)/(N_y+2a) is the "prototype"; the per-detector variance p(1-p) is the diagonal covariance; for binary features this is a Bernoulli naive Bayes (diagonal Mahalanobis analogue). Score = sum over active detectors of a table lookup log p_y(d), normalised per class by the class's mean score on its own training samples (the analogue of correlation normalisation). DERIVED, not from the paper.
- One concrete small test: freeze the detector code trained on the 6 base classes. For the 4 held-out classes, compare three class-comparison rules on the SAME counts, with 20 / 100 examples: (i) current counting-table vote (baseline), (ii) frozen-code Bernoulli naive Bayes with Laplace shrinkage (add a pseudo-count a, the analogue of Eq. 8) and (iii) the same plus per-class score normalisation (z-score of the class's own training-score distribution, the analogue of Eq. 7; store the mean and spread of the class's own scores as 2 integers). Report new-class recall and old-class recall at the same total error. The ablation in Table 4 predicts normalisation + shrinkage matter most, so run (ii) vs (iii) as the key comparison. Also report the same on Euclid-like (plain overlap count) as the NCM floor.

## Paper 2. ADC, Adversarial Drift Compensation (Goswami, Soutif-Cormerais, Liu, Kamath, Twardowski, van de Weijer)

### (a) Mechanism
- Setting: small-start exemplar-free CIL; the backbone IS trained on every task (not frozen), so old-class prototypes drift. Model h_t(x) = softmax(W_t f_t(x)); classification at test is NCM (nearest mean) in the CURRENT feature space.
- Stored per class: ONE prototype P^k (mean embedding, 512-d for ResNet-18). No covariance, no images. Also the previous model f_{t-1} is kept during training of the new task (teacher).
- Training of task t: cross-entropy on new classes + logit distillation from the old model (LwF), L = L_ce(h_t(x), y) + lambda * L_ce(h_{t-1}(x), h_t(x)); lambda = 10 (5 for ImageNet-Subset, 20 for fine-grained), temperature 2. First task lr 0.1, 200 epochs; later tasks lr 0.05 (0.001 TinyImageNet), 100 epochs. Backbone from scratch (ImageNet-pretrained for CUB-200, Cars).
- Drift compensation after training task t (Algorithm 1), for each old class k:
  1. Pick the m = 100 current-task samples whose OLD-model embedding f_{t-1}(x) is closest (L2) to the old prototype P^k_{t-1}.
  2. Targeted adversarial attack in the old model, i = 3 iterations: loss L = mean ||f_{t-1}(x) - P^k_{t-1}||^2; x_adv = x - alpha * grad_x L / ||grad_x L||_2 (alpha = 25, no epsilon ball, pixels only clipped to the valid range).
  3. Keep only the x_adv that the old NCM now classifies as k.
  4. Drift Delta^k = mean over kept x_adv of (f_t(x_adv) - f_{t-1}(x_adv)); new prototype P^k_t = P^k_{t-1} + Delta^k (Eq. 3-5).
  5. New classes: prototype is the plain mean of f_t(x) over class data.
- Why it works: "continual adversarial transferability": the adversarial images placed near P^k in the old space remain near the true (oracle) prototype in the new space because distillation keeps the models related. SDC (the earlier method) instead averages the drift of all new samples with a Gaussian window around the old prototype and fails when few new samples are near it. ADC needs no weighting (the adversarial samples are already close to the prototype).

### (b) Base training needs
- Targets the small-start case: CIFAR-100, TinyImageNet, ImageNet-Subset split EQUALLY into 5 or 10 tasks, i.e. the first task is 20 or 10 classes of 100 (40 or 20 of 200 TinyImageNet), not half. Fine-grained: CUB-200 5/10 tasks, Cars 7/14 tasks.
- So the base set can be tiny (10 CIFAR classes), but the backbone is retrained at every task (full gradient training, 100 epochs per task), distillation required. The drift estimate quality decays with tasks: cosine similarity of the estimated vs true drift starts ~0.9 and falls to a minimum average ~0.7; SDC sits ~0.15 after the second task with some negative values (Fig 6).
- The prototype-only NCM classifier with LwF is already a strong small-start baseline (it beat PASS, SSRE, FeTrIL, FeCAM in several settings).

### (c) Results (Table 1, A_last / A_inc, small-start)
| Method | CIFAR100 T=5 | CIFAR100 T=10 | TinyImageNet T=5 | TinyImageNet T=10 | ImageNet-Subset T=5 | ImageNet-Subset T=10 |
| --- | --- | --- | --- | --- | --- | --- |
| LwF | 45.35 / 61.94 | 26.14 / 46.14 | 38.81 / 49.70 | 27.42 / 38.77 | 50.88 / 69.11 | 37.90 / 61.60 |
| NCM (LwF + NCM) | 53.53 / 66.35 | 41.31 / 57.85 | 38.69 / 50.45 | 26.56 / 41.04 | 57.74 / 71.99 | 45.86 / 65.04 |
| SDC | 54.94 / 64.82 | 41.36 / 58.02 | 40.05 / 50.82 | 27.15 / 40.46 | 59.82 / 74.10 | 43.72 / 65.83 |
| PASS | 49.75 / 63.39 | 37.78 / 52.18 | 36.44 / 48.64 | 26.58 / 38.65 | 50.96 / 66.15 | 38.90 / 54.74 |
| SSRE | 42.39 / 56.57 | 29.44 / 44.38 | 30.13 / 43.20 | 22.48 / 34.93 | 40.30 / 57.57 | 28.12 / 45.87 |
| FeTrIL (frozen) | 45.11 / 60.42 | 36.69 / 52.11 | 29.91 / 43.99 | 23.88 / 36.35 | 49.18 / 63.83 | 40.26 / 55.12 |
| FeCAM (frozen) | 47.28 / 61.37 | 33.82 / 48.58 | 25.62 / 39.85 | 23.21 / 35.32 | 54.18 / 67.21 | 42.68 / 57.45 |
| ADC | 59.14 / 69.62 | 46.48 / 61.35 | 41.0 / 50.94 | 32.32 / 43.04 | 62.40 / 74.84 | 47.58 / 67.07 |
- Key reading for us: with a 10-class first task (CIFAR100 T=10), FeCAM falls to 33.82 last-acc and 48.58 avg, BELOW the plain LwF+NCM baseline (41.31 / 57.85). The frozen-backbone family collapses when the base is small; this is the same set of frozen-extractor methods L resembles.
- Fine-grained (Table 2, A_last/A_inc): CUB-200 T=5 ADC 64.46/73.49 (LwF 58.68/71.31, FeCAM 53.47/66.39), T=10 57.97/68.91 (FeCAM 51.78/64.97, FeTrIL 49.09/62.42); Cars T=7 54.86/67.07, T=14 45.07/61.39 (FeCAM 37.50/52.78). Here frozen FeTrIL/FeCAM beat plain NCM at T=10/14 (ImageNet-pretrained features).
- Five seeds (Tables 4-6, CIFAR100): T=5 ADC 58.12 +- 1.42 / 69.29 +- 1.17 vs NCM 52.68 / 65.91, FeCAM 46.93 / 61.49; T=10 ADC 45.43 +- 3.03 / 59.59 +- 4.11, FeCAM 33.13 / 48.10.
- Versus exemplar NME (Fig 4): ADC beats NME with 20 exemplars per class on CIFAR100 T=10 (46.48) and 50 per class on TinyImageNet T=10 (32.32) (values read from the figure text).
- Hyperparameters (CIFAR100 T=10): iterations 1/2/3/5/10 give A_inc 60.94/61.23/61.35/61.25/60.93; alpha 1/10/25/50/100 give 60.46/61.14/61.35/60.83/60.93; number of samples 25/50/100/300/500/1000 give 60.19/60.89/61.35/61.54/61.64/61.47 (25 samples already beats SDC by 2.62 points last-acc). On average only 59 of 100 samples are successfully moved to the target class after 3 iterations (69 after 5).

### (d) Operations and memory
- Gradient-based throughout: backbone backprop each task; adversarial attacks need N_classes x N_iterations backward passes (1350 for CIFAR100 T=10), +3.1 percent of training cost (+2.5 percent for T=5), a floating-point gradient in the input space of a CNN.
- Memory: one prototype per class (D floats, 512 here). No covariance, no images. Needs the old model copy during the task and the new-task data present.
- Needs task boundaries and enough current data (stated).

### (e) Stated limitations and failure modes
- "Requires the access to the task boundaries ... and to a big enough quantity of current data"; harder in online CL or few-shot continual learning. Drift-estimate quality drops over tasks (0.9 -> 0.7 cosine). Still lags the joint upper bound by a lot (CIFAR100 T=10 last 46.5; joint not quoted here, UNVERIFIED). Perturbations are visible on low-resolution images. Relies on distillation keeping old and new models related.

### (f) Fit to L and the one concrete test
- Fit: poor on the mechanism (gradients through a deep network, floating point, backward passes on images, a retrained backbone), so ADC itself cannot be built on the chip and cannot be the L Cortex mechanism. It matters for L in three ways: (1) it is the cleanest evidence that a frozen extractor trained on a small base is the wrong place to bet (FeCAM drops below LwF+NCM at 10 base classes); (2) it shows that the stored state per class need only be ONE prototype plus a way to track its drift, no covariance; (3) the idea "use new-class samples that are near an old class prototype as pseudo-exemplars of the old class" is gradient-free in spirit and can be transcribed to counts.
- If the L detector layer is allowed to adapt (not frozen), the L analogue of drift is a change in which detectors fire for a given class; we would need to re-map stored per-class count rows. A transcription of ADC without gradients: when a new class arrives and the detector set is updated, take the new-class samples whose OLD code was nearest to old-class row k (by overlap count), run them through the OLD and NEW code, and add the mean change of their code to row k. DERIVED; not tested by the authors.
- One concrete small test (on our data, 6 of 10 classes as base): freeze nothing, i.e. allow the detector layer to update (e.g. add detectors or refresh thresholds) when the 4 new classes arrive. Compare old-class recall after the update for (i) no compensation (stale counts), (ii) re-built rows from SDC-style averaging (mean code change over ALL new samples, kernel-weighted by old-code overlap) and (iii) the ADC-style variant (only the m = 100 new samples with highest overlap to old row k, moved before measuring the code change; skip the gradient step, and optionally flip the few detector bits that bring the code closer to row k). Metric: old-class recall vs the oracle of re-counting from the old data (cosine of estimated vs oracle row change, as in the paper's Fig 6). If (iii) tracks the oracle with cosine above about 0.7, a no-image drift fix exists. If the detector layer stays frozen, drift is zero by construction and ADC is moot, so FeCAM-style per-class spread (Paper 1 test) is the relevant one.

## Verdict (both papers) for a tiny base set (6 of 10 classes)
- FeCAM: depends on a strong frozen base; the paper's own small-first-task test (20 classes) shows large losses and ADC's table shows it below LwF+NCM at 10 classes, so a 6-class base is expected to be too weak for a frozen extractor to carry 4 new classes (UNVERIFIED for 6 of 10, nobody tested it). Its value for L is the diagnosis and the cheap tricks (per-class normalisation, shrinkage, per-dimension variance), not the covariance machinery.
- ADC: works with tiny bases (10 of 100 classes) but only by retraining the backbone with distillation and gradient attacks, which L cannot do on-chip.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
