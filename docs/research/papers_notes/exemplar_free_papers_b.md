---
title: Paper notes - exemplar-free class-incremental learning B
tags: [l, research, papers]
---

# Paper notes - exemplar-free class-incremental learning B

Two papers read in full from the PDF text (arXiv 2203.06359 and 2402.03917). All numbers below are numbers reported by the papers (they are
the papers' MEASURED results on their own benchmarks, not ours). Anything not found in the text is marked UNVERIFIED.
Neither paper is matrix-free: both are deep-network (ResNet-18) methods trained with gradients and multiplies. Their value for L is the
design lesson, not the code.

## 1. SSRE - Self-Sustaining Representation Expansion (Zhu et al., CVPR 2022, arXiv 2203.06359)

### (a) Mechanism
- Setting: non-exemplar class-incremental learning (NECIL). Disjoint class sets per phase, no old samples kept. Backbone ResNet-18, linear classifier.
- Baseline loss (PASS-style): `L = L_ce + lambda*L_kd + gamma*L_proto` with lambda = gamma = 10. `L_kd` is a Euclidean (L2) feature distillation between
  the current and previous-phase feature extractors on new data. `L_proto` is cross-entropy on stored class prototypes (one feature vector per class),
  over-sampled (repeated) up to the batch size - no Gaussian noise, unlike PASS.
- Dynamic Structure Reorganisation (DSR): at each phase the old feature extractor is frozen (hat-theta) and a residual adapter (a 1x1 conv, optionally with
  BatchNorm) is added in parallel to every conv block: `f_n(Q) = f_{n-1}(Q; frozen theta (+) delta_theta)`. Gradients flow only through the adapters.
  After the phase, structural re-parameterisation (RepVGG style: zero-pad the 1x1 kernel to 3x3, fold BatchNorm linearly) merges adapter into the main
  conv losslessly, so parameter count does not grow across phases.
- Main-Branch Distillation (MBD): the distillation target is the previous main branch (the merged, frozen old model), not a continuously drifting one.
- Prototype Selection Mechanism (PSM): cosine similarity S_i between each new sample's (normalised) feature and the old prototypes. If S_i > threshold sigma
  the sample goes into the distillation loss (mask on L_kd); if below, into the cross-entropy loss for learning the new class (mask on L_ce).
  `L = Mask_ce(L_ce) + lambda*Mask_kd(L_kd) + gamma*L_proto`. Best threshold about 0.8 (Fig. 4, curves peak at 0.8).
- Stored per class: one prototype (a feature vector, 512-d for ResNet-18). Nothing else. No covariance.
- Old-class protection: frozen old weights during training + distillation to the old main branch + prototype replay for the classifier head.
- Training: Adam, lr 0.001, decay 0.0005, 100 epochs, batch size 128; plain supervised first phase (no self-supervision, they match PASS first-phase accuracy).

### (b) What base training needs
- The paper follows the PASS protocol ("followed exactly the settings in [37]"). The text of this paper never states the base-class count itself, so the
  split is UNVERIFIED from this paper. EFC's text (Section 5.1) states the standard warm-start protocol: 50 of 100 classes in the first task for CIFAR-100 and
  ImageNet-Subset (10-step), 40 for the 20-step; 100 of 200 for Tiny-ImageNet. So SSRE is a WARM-START method: it relies on a first task big enough
  to give a good frozen backbone. Phases P = 5, 10, 20 split the remaining classes.
- It never tests a small first task. Its representation-preserving design (frozen main branch, distillation) assumes the base features already separate future classes.

### (c) Results (average incremental accuracy, %, E = 0 exemplars; Table 3)
- CIFAR-100: P=5 65.88, P=10 65.04, P=20 61.70 (PASS 63.47 / 61.84 / 58.09).
- TinyImageNet: P=5 50.39, P=10 48.93, P=20 48.17 (PASS 49.55 / 47.29 / 42.07).
- ImageNet-Subset P=10: 67.69 (PASS 61.80).
- Average forgetting (Table 4): CIFAR-100 18.37 / 19.48 / 19.00 for P=5/10/20 (PASS 25.20 / 30.25 / 30.61); TinyImageNet 9.17 / 14.06 / 14.20.
- Ablation (Table 1, CIFAR-100, P=5/10/20): neither DSR nor MBD nor PSM: 61.11 / 57.08 / 51.04. DSR only: 64.86 / 63.25 / 54.09. MBD only: 62.70 / 62.60 / 58.57.
  DSR+MBD: 65.10 / 63.87 / 60.60. All three: 65.88 / 64.69 / 61.61. So DSR matters most for few phases, MBD matters most for many phases, PSM adds about 0.8-1.0 point.
  (Table 3 quotes 65.04 for P=10 and 61.70 for P=20, slightly different from 64.69 / 61.61 in Table 1; the paper does not explain it. Noted, not resolved.)
- Adapter type (Table 2): 1x1 conv about 65.9 / 65.1 / 61.6; 3x3 conv 64.3 / 63.5 / 60.8. A tiny 1x1 adapter is enough.
- Independent re-run by the EFC authors (EFC Table 1, with self-rotation first task): SSRE warm start CIFAR-100 10-step 65.78 average incremental; but COLD start
  CIFAR-100 10-step only 47.26 (20-step 32.45), Tiny-ImageNet cold 38.82 / 30.62, ImageNet-Subset cold 43.76 / 31.15. So its numbers collapse without a big first task.

### (d) Operations and memory
- Training uses gradients (backprop through adapters), convolutions, multiplies everywhere. Test time after re-parameterisation: plain ResNet-18, same cost as the baseline.
- Memory per class: one 512-d float prototype. Parameters do not grow (merged back). The old model copy is needed during training for distillation.
- No matrices of covariance; no second-order terms.

### (e) Limitations and failure modes (stated and observed)
- Authors state the error of distillation accumulates with phases (forgetting rate at least alpha^(n-1)) and that the distillation reference must be corrected.
- Old classes' prototypes are never updated, so they go stale as the backbone changes (not stated by SSRE; implied by the method). Prototype selection threshold is a sensitive
  hyper-parameter (peak at 0.8, falls off either side, Fig. 4).
- Cold start collapse is shown only by the EFC paper's re-run (above), not by SSRE itself. UNVERIFIED whether the EFC authors' setup is fully faithful.
- The paper says "source code will be made available" - no appendix, no limitations section.

### (f) Fit to L
- L is binary sparse detector code plus an integer count table, no multiplies, no dense matrices. SSRE needs a conv backbone, adapter training by gradient, L2 distillation: none of it maps.
- Transferable ideas: (1) a frozen base plus a small add-on that is later folded in without growing size ("expand then merge"); for L this is: the base detector set is frozen, new classes
  add a few new detectors (units) trained on the new data only, and old detectors never change. (2) Store one prototype per class, i.e. for L one count row per class: already how L works.
  (3) PSM idea: split new samples into "looks like an old class" (use only to keep the old classes' counts consistent) and "looks new" (use to learn the new class). For L: a new sample whose
  detector code overlaps strongly with an existing class row is not allowed to write into a new row.
- One concrete small test: with 6 base classes of 10 trained, freeze the detector bank, then learn the 4 new classes (a) by only adding counts for the 4 new class rows over the frozen detectors,
  versus (b) additionally letting a small budget of NEW detectors (e.g. 10 percent more units, trained only on new-class data and gated by "sample code overlaps no old row by more than a
  threshold"). Report old-class accuracy, new-class accuracy and the confusion between old and new. This isolates the SSRE claim: "expand in a side branch, keep the main branch fixed, gate by similarity".

## 2. EFC - Elastic Feature Consolidation for Cold Start Exemplar-free Incremental Learning (Magistri et al., ICLR 2024, arXiv 2402.03917)

### (a) Mechanism
- Setting: exemplar-free CIL (EFCIL), tasks t = 1..K with disjoint classes; ResNet-18 backbone `f_t`, linear classifier `W_t` that grows with each task (`softmax(W^T f(x))`).
- Idea: the backbone is NOT frozen. Drift in feature space is penalised anisotropically, only in directions that matter for old classes, so the net stays plastic.
- Empirical Feature Matrix (EFM): `E_f(x) = E_{y~p(y)}[ (d log p(y)/d f(x)) (d log p(y)/d f(x))^T ]`, averaged over the task data: `E_t = E_x[E_f(x)]`. It is an n x n (n = 512)
  positive semi-definite matrix, a feature-space analogue of the Fisher matrix. Closed form without backward pass: `E_f(x) = E_y[ W(I_m - P)_y (W(I_m - P)_y)^T ]` where P is the softmax
  output replicated m times (m = number of classes seen). Local second-order link: `KL(p(.|f+delta) || p(.|f)) = delta^T E delta + O(|delta|^3)`.
  Its rank equals (number of seen classes - 1) (Appendix B.2, observed rank 49, 59, ... 99 for a 50-class base and 10-class steps).
- EFM loss (replaces feature distillation): `L_EFM = E_x[(f_t(x) - f_{t-1}(x))^T (lambda_EFM * E_{t-1} + eta * I) (f_t(x) - f_{t-1}(x))]`, lambda_EFM = 10, eta = 0.1 (damping; they require
  lambda*mu_i > eta so it does not collapse into plain distillation). Feature distillation is the special case lambda_EFM = 0, eta = 10.
- Asymmetric Prototype Replay (PR-ACE) loss: `L = CE_{C_t}(x_t, y_t) + CE_{C_1:t}((p~, y_p~) union (x^_t, y^_t))`. First term: current data, only the current task's head. Second term: a batch of current data
  PLUS a batch of Gaussian prototypes, trained over ALL heads; so prototypes dominate the second term. The symmetric version (CE on current data over all heads + lambda_pr * CE on prototypes, lambda_pr = 10)
  fails when the backbone is plastic (Fig. 3).
- Prototypes: class mean `p_c` of features plus a full class covariance `Sigma_c` (512 x 512); at training time sample `p~ ~ N(p_c, Sigma_c)`.
- Prototype drift compensation (SDC-style, Eqs. 13-14): after each task, shift each old prototype by a weighted mean of the current-task feature drift `delta_i = f_t(x_i) - f_{t-1}(x_i)`,
  weights `w_i = exp(-(f_{t-1}(x_i) - p_c)^T E_{t-1} (f_{t-1}(x_i) - p_c) / (2 sigma^2))`, distances normalised to [0,1], sigma = 0.2. So current samples that the old classifier sees as similar to the prototype vote for its drift.
  Covariances are NOT updated (stated as open problem).
- Algorithm 1 (Appendix D): for each task t >= 2, per step sample batches, compute L_PR-ACE + L_EFM, SGD/Adam update; then update prototypes (Eqs. 13-14), add new prototypes, compute `E_t` with one forward pass.
- Training of incremental steps: Adam, weight decay 2e-4, lr 1e-4 (CIFAR-100, Tiny-ImageNet), 1e-5 backbone / 1e-4 heads (ImageNet-Subset), 100 epochs, batch size 64. First task: 100 epochs Adam lr 1e-3 (decay at 45, 90),
  with self-rotation (4x rotation classes) to match PASS and Fusion; ImageNet-Subset 160 epochs SGD. Five seeds with shuffled class orders.

### (b) What base training needs - the cold start case, exactly as reported
- Warm Start (WS) = large first task: 50 classes (CIFAR-100 and ImageNet-Subset, 10-step; 40 classes for 20-step), 100 classes for Tiny-ImageNet (both 10- and 20-step); rest split uniformly.
- Cold Start (CS) = all classes split uniformly over all tasks including the first. So CIFAR-100 10-step has 10 classes in the first task, 20-step has 5 classes; Tiny-ImageNet 20 and 10 classes; ImageNet-Subset 10 and 5;
  ImageNet-1K 100 and 50 (Appendix G). The ResNet-18 is trained from scratch ("random initialisation") on that small first task, with self-rotation. So EFC has actually been shown to start from 5-10 classes.
- The paper's claim: methods that freeze or strongly distill the backbone (PASS, SSRE, FeTrIL) drop sharply, because the small first task gives a poor backbone and plasticity is needed; EFC keeps the backbone plastic (anisotropic regularisation) and
  repairs old classifiers with prototype replay + prototype update.
- Important caveat for L: the first task uses self-rotation (images rotated 0/90/180/270 to make 4x the classes) to enrich features. The 4x-rotation trick is
  a source of extra diversity not available from raw classes; whether it would be used in a cold-start 10-class base for us is our choice, not the paper's finding. Also the backbone is a 512-d deep feature trained by gradient and the quoted absolute accuracies are low:
  cold start average incremental accuracy is 58.6 percent on CIFAR-100 10-step versus 68.2 percent warm start.

### (c) Results (Table 1; A_step = accuracy after last step on all classes, A_inc = average incremental accuracy; %, mean over 5 seeds)
Cold start (10 step / 20 step):
- CIFAR-100: EFC A_step 43.62 / 32.15, A_inc 58.58 / 47.36. FeTrIL 34.94 / 23.28 and 51.20 / 38.48. SSRE 30.40 / 17.52 and 47.26 / 32.45. PASS 30.45 / 17.44 and 47.86 / 32.86. LwF 32.80 / 17.44 and 53.91 / 38.39. EWC 31.17 / 17.37 and 49.14 / 31.02.
- Tiny-ImageNet: EFC A_step 34.10 / 28.69, A_inc 47.95 / 42.07. FeTrIL 30.97 / 25.70, 45.60 / 39.54. SSRE 22.93 / 17.34 and 38.82 / 30.62.
- ImageNet-Subset: EFC A_step 47.38 / 35.75, A_inc 59.94 / 49.92. FeTrIL 36.17 / 26.63, 52.63 / 42.43. SSRE 25.42 / 16.25 and 43.76 / 31.15. LwF is strong too: 37.71 / 18.64 and 56.41 / 40.23.
- ImageNet-1K (A2): EFC 42.62 / 36.32 and 56.52 / 49.80 versus FeTrIL 34.28 / 26.64 and 48.93 / 40.02.
Warm start (10 step / 20 step):
- CIFAR-100: EFC A_step 60.87 / 55.78, A_inc 68.23 / 65.90. FeTrIL 56.79 / 52.61 and 65.03 / 62.50. SSRE 57.48 / 52.98 and 65.78 / 63.11.
- Tiny-ImageNet: EFC 50.40 / 48.68 and 57.52 / 56.52. ImageNet-Subset: EFC 68.85 / 62.17 and 75.40 / 71.63.
- 5-step warm start (A1): CIFAR-100 EFC 62.57 / 69.51 versus SSRE 57.79 / 66.53; Tiny-ImageNet EFC 51.19 / 58.12.
Reading these: even the best method falls from about 61 percent final accuracy (warm) to 44 percent (cold) on CIFAR-100 10-step; the cold start gap is 15 to 23 points for the best methods, and bigger for SSRE (about 27 points on A_step).
Ablations:
- Feature distillation + symmetric loss works but equals freezing; EFM + symmetric loss fails to adapt old classifiers; EFM + PR-ACE is best (Fig. 3, 4a). The paper states feature distillation is essentially equivalent to freezing the backbone after task 1 with a good prototype rehearsal (FeTrIL-like).
- Prototype update (Table A3/Fig 4b): CIFAR-100 CS 10 step 39.28 -> 43.62, 20 step 27.28 -> 32.15; ImageNet-Subset CS 39.99 -> 47.38 and 29.62 -> 35.75; Tiny CS 31.23 -> 34.10, 25.12 -> 28.69. WS gains are smaller (about 2-3 points).
- Covariance storage (Tables 2, A4, A5): low-rank (30-50 eigenvectors, 99 percent variance) keeps accuracy; one covariance per task or just the last task costs about 1-3 points warm and nothing meaningful cold (CIFAR-100 CS 10 step: each-task 45.26, last-task 43.72, full 43.62).
- Hyper-parameters fixed (lambda_EFM = 10, eta = 0.1, sigma = 0.2); no sweep reported in the main text. UNVERIFIED whether sensitivity was studied.

### (d) Operations and memory
- Training: full backprop through ResNet-18, many multiplies, plus a 512 x 512 quadratic form per sample in the loss. EFM computation: one forward pass, then Jacobian products with W (matrix operations on an n x n and an m x m matrix). Eigen-analysis is only diagnostic.
- Memory per class: a mean (512-d) plus a covariance (512 x 512 = 262,144 values, about 1 MB in float32); low-rank 30-50 eigenvectors suffices (about 30 x 512 floats). Per task: one EFM 512 x 512. An old model copy is kept for f_{t-1}.
- Wall-clock (A5): EFC about as fast as SSRE per epoch; LwF cheapest; prototypes and exemplars add the main overhead. FeTrIL (frozen backbone + SVM) is the fastest.

### (e) Stated limitations and failure modes
- Stored class means can drift from true means and cause forgetting on long task streams; covariance drift is not estimated ("open question").
- Storage grows linearly with the number of classes (covariances).
- All design depends on prototypes that are Gaussian in feature space; accuracy in cold start remains well below warm start (above).
- The comparison reruns SSRE/PASS with its own protocol (self-rotation first task), so absolute SSRE numbers differ from the SSRE paper; the authors say so explicitly.
- First task still needs enough classes for the EFM to be informative: the EFM rank is classes minus 1, so with 5-10 base classes the protected subspace has only 4-9 dimensions at first (inference from the paper's rank result; not discussed by the paper as a limit).

### (f) Fit to L
- EFC's whole machinery (EFM quadratic form, gradients on a plastic backbone, Gaussian prototypes with covariance, Adam) is incompatible with the matrix-free, multiplier-free rule for L. Do not port it.
- Transferable lessons for a small base set:
  1. The cold-start finding says: with a poor base, freezing everything (FeTrIL, SSRE, PASS, distillation) fails (SSRE falls from 65.8 percent warm to 47.3 percent cold A_inc on CIFAR-100 10-step, and from 57.5 to 30.4 percent A_step). The feature extractor must keep learning, but only in directions that do not hurt old classes.
  2. The EFM direction idea in count terms: a detector is "important" for an old class if changing its firing changes that class's count score. L can measure this exactly with integers: for each detector, the number of old-class rows whose score margin depends on it. Protect (freeze, or forbid re-threshold) detectors with high old-class margin contribution; leave low-importance detectors free to re-tune/recruit for the new class. This is a multiply-free analogue of lambda * E_{t-1}.
  3. Prototype replay: L's count table already is a prototype (a per-class count row, no covariance). The drift-compensation step has an L analogue: if detector thresholds are ever changed, re-estimate the old-class rows from current-task samples that fire most like the old row (the SDC/EFM weight w_i is just a similarity-weighted drift vote).
  4. Asymmetric loss lesson: train new-class rows against the old-class rows with a rehearsed (stored-row) signal that is larger than the new-class signal, or the new class dominates (task-recency bias). In L: cap the new class's total count mass to the typical old-class mass.
- One concrete small test: base = 6 of 10 classes (cold-ish small base). Compare, on the frozen-detector L, three options for learning the 4 new classes: (i) freeze all detectors, add count rows only (FeTrIL-like); (ii) allow all detectors to retune (high plasticity, no protection); (iii) allow only detectors whose "old-class margin contribution" (an integer count over the 6 base rows) is below a threshold to retune/recruit. Report old-class accuracy, new-class accuracy, average incremental accuracy, and confusion between old and new, over 3 seeds and 3 base-class orders. If (iii) beats (i) and (ii) on average incremental accuracy, the EFC claim transfers; if (i) wins, the base is already good enough that plasticity is not needed.

## Summary for the decision
- SSRE: warm-start method (expects a big base, 50 of 100 classes in the PASS protocol; UNVERIFIED in its own text). Expand-and-merge adapter, prototype per class, PSM gating. Fails (by the EFC re-run) when the base is small.
- EFC: the only one of the two that is explicitly designed for a small first task (5-10 classes of 100; 100 or 50 classes on ImageNet-1K), and it works best there, but even it loses 15-23 points compared to a warm start.
- For a 6-of-10 base the advice from both papers is: do not freeze everything, do protect the directions old classes depend on, keep class prototypes (rows), and rebalance new versus old signal.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
