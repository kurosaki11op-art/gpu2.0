---
title: Paper notes - frozen features with prototypes and random projections
tags: [l, research, papers]
---

# Paper notes - frozen features with prototypes and random projections

Scope: four papers on exemplar-free class-incremental learning (CIL) with a frozen (or first-session-adapted) feature extractor and a closed-form, order-invariant head built from per-class statistics. Read in full from the arXiv PDFs on 25 Oct 2026 (ids verified from the title page of each PDF). All numbers are copied from the papers (reported by the authors, not reproduced by us); the label for every number is therefore REPORTED. L-side statements are labelled ESTIMATED or PROPOSED. Where the text extraction scrambled a table, that is said and the cell is marked UNVERIFIED.

| id | paper | what it adds |
|---|---|---|
| 2307.02251 | RanPAC (McDonnell et al., NeurIPS 2023) | frozen random expansion + nonlinearity, then ridge/Gram-decorrelated class prototypes |
| 2303.07338 | APER / SimpleCIL (Zhou et al., IJCV) | prototype-only head on a frozen pre-trained model; adapt once, concatenate, freeze |
| 1909.01520 | Deep Streaming LDA (Hayes and Kanan, CVPRW 2020) | per-class running mean + one shared covariance, per-sample streaming update |
| 2303.13199 | First Session Adaptation (Panos et al., ICCV 2023) | LDA head + adapt the body only in session 1 (FiLM or full), shown to beat replay and FSCIL methods |

Shared skeleton of all four: (1) a feature extractor that is frozen after at most one adaptation phase; (2) per-class sums or means; (3) optionally one shared second-order statistic; (4) a closed-form classifier computed from those statistics. The statistics are sums over samples, so they do not depend on the order of arrival and nothing stored for an old class is ever overwritten. That is the whole "no forgetting" argument.

---

## 1. RanPAC: Random Projections and Pre-trained Models for Continual Learning (arXiv 2307.02251)

### (a) Mechanism, exactly

- **Frozen parts.** A pre-trained transformer (mainly two ViT-B/16 models: one pre-trained on ImageNet-21K, one additionally fine-tuned on ImageNet-1K) gives a feature vector f in R^L (L = 768). Optionally, in Phase 1 only, a parameter-efficient adapter (AdaptFormer/AdaptMLP, SSF or VPT) is trained on the first task with SGD and a temporary linear softmax head, then frozen and the head discarded. Phase 2 (the continual part) uses no SGD at all.
- **Random expansion.** One frozen random matrix W in R^(L x M), entries drawn i.i.d. N(0,1) (Algorithm 1), created once. M = 10000 in all main results (CDDB-Hard uses M = 5000). The expanded vector is h = phi(f^T W), phi an element-wise nonlinearity (Fig. 3 compares ReLU and squaring; both help; no nonlinearity gives no gain). Section 4.5 states the weights "can be bipolar instead of Gaussian and, if stored using a single bit for each element, contribute only a tiny fraction" of memory.
- **Statistics per class and shared.** For H = the M x N matrix of all expanded training vectors and Y the N x K one-hot labels (Eq. 4):
  - Gram matrix G = sum_t sum_n h_tn h_tn^T (M x M, shared by all classes);
  - class sums C = sum_t sum_n h_tn y_tn^T (M x K); c_y is the un-averaged sum of h over class y (the mean is deliberately dropped, Eq. 16).
  - Both are sums over outer products, so they are identical for any order of tasks or samples.
- **Classification.** Eq. (2) without expansion: s_y = f_test^T G^-1 c_y. With expansion and ridge, Eq. (5): s_y = phi(f_test^T W) (G + lambda I)^-1 c_y; in matrix form y_pred = h_test W_o with W_o = (G + lambda I)^-1 C. Prediction = argmax over y.
- **Lambda.** After each task the current task's data is split 80:20, lambda swept over {1e-8, 1e-7, ..., 1e8} (17 orders of magnitude), G and C built from the 80 percent, lambda chosen by lowest mean squared error on the 20 percent (Appendix C.1). Only current-task data is used, so it stays continual. Table A5 uses constant lambda = 100.
- **Theory the authors give.** (i) Eq. (11)-(14): W_o is the exact minimum mean-squared-error solution of the l2-regularised linear regression onto one-hot labels, i.e. what joint SGD with MSE loss and weight decay lambda would converge to. (ii) Appendix B.4: with ZCA whitening D_Z = S^-0.5, LDA is Euclidean distance after whitening; the Gram version differs by using G (uncentred second moment) instead of covariance S, and equals LDA only if features have zero mean and classes are equiprobable. Using G removes the bias terms of LDA and the outer products of means. (iii) Section 4.2 and Chernoff bounds (Eqs. 6-9): as M grows, norms of projected vectors concentrate and inner products between distinct inputs spread, so the distribution is a better fit to the Gaussian assumption behind Eq. (2). Expected projected inner product is M sigma^2 f^T f'. A Taylor expansion of phi(W^T f) gives higher-order feature interactions that would be too many to enumerate directly (Fig. 3b: pair-wise product features on the first 100 feature dimensions are mostly recovered by RP + nonlinearity).
- **NCM baseline.** Cosine similarity f_test^T cbar_y / (norm norm) (Eq. 1/17) using plain class means.

### (b) What the base features need

- The limitations paragraph states that the value of Eqs. (4)-(5) is "completely reliant on supply of a good generic feature extractor" and is "unlikely to be as powerful" for networks trained from scratch.
- Weak or different-domain features: VTAB (mixed domains per task) and DIL benchmarks show PETL Phase 1 adds little where tasks come from different domains (DomainNet: No Phase 1 64.7 vs full 66.6). If the first task has too little data diversity, Phase 1 helps little: Table A4 shows T = 20 (few classes in session 1) "often on par with not using the PETL method at all". One outlier: VPT with the ImageNet-21K backbone "failed badly" on VTAB (Fig. A7).
- Backbone choice is dataset-dependent (Fig. A7/A8): IN-1K fine-tuned best on ImageNet-A, IN-21K best on CIFAR100 and OmniBenchmark. Other backbones work with RP: ResNet-50, ResNet-152 (ImageNet), CLIP ViT-B/16 (Tables A6-A10). ResNet-152 with RP was worse than ResNet-50 on CUB, OmniBenchmark and VTAB (M not tuned).
- The correlation analysis (Fig. 2, Split ImageNet-R, 200 classes, ViT-B/16): raw class means have very high off-diagonal Pearson correlation, mean more than twice that of the original ImageNet-1K data treated the same way, which the authors read as the size of the domain shift. Training-set accuracy: joint linear probe 82 percent; NCM with cosine 64 percent; Eq. (2) 75 percent; Eq. (2) with RP M = 2000 87 percent.

### (c) Results

Protocol: class-incremental, T = 10 equal tasks (VTAB T = 5), no rehearsal, final Average Accuracy A_T (mean over tasks of accuracy on the classes of each task, Eq. 26); seed 1993; about +-1 percent variation across seeds for PETL runs; without Phase 1 the final accuracy is essentially seed- and task-split-invariant because G and C are order invariant (Fig. A2).

Table 1 (ViT-B/16, final accuracy), columns CIFAR100 / IN-R / IN-A / CUB / OmniBench / VTAB / Cars:
- Joint linear probe: 87.9 / 72.0 / 56.6 / 88.7 / 78.5 / 86.7 / 51.7.
- L2P: 84.6 / 72.4 / 42.5 / 65.2 / 64.7 / 77.1 / 38.2. DualPrompt: 84.1 / 71.0 / 45.4 / 68.5 / 65.5 / 81.2 / 40.1. CODA-Prompt: 86.3 / 75.5 / 44.5 / 79.5 / 68.7 / 87.4 / 43.2. ADaM: 87.6 / 72.3 / 52.6 / 87.1 / 74.3 / 84.3 / 41.4.
- **RanPAC (Algorithm 1): 92.2 / 77.9 / 62.4 / 90.3 / 79.9 / 92.2 / 77.5.** Relative error reduction vs ADaM: 36, 20, 21, 25, 22, 53, 62 percent.
- Ablations: No RPs: 90.6 / 73.9 / 57.7 / 86.6 / 74.3 / 90.0 / 73.0. No Phase 1: 89.0 / 71.8 / 58.2 / 88.7 / 78.2 / 92.2 / 66.0. No RPs, no Phase 1: 87.0 / 67.6 / 54.4 / 86.8 / 73.1 / 91.9 / 62.2. NCM with Phase 1: 87.8 / 70.1 / 49.7 / 85.4 / 73.4 / 88.2 / 40.5. NCM only: 83.4 / 61.2 / 49.3 / 85.1 / 73.1 / 88.4 / 37.7.
- Error reduction from adding RP (with Phase 1): 17, 15, 11, 28, 22, 22, 17 percent; (without Phase 1): 15, 13, 8, 14, 19, 4, 10 percent. VTAB is the exception: RP adds little (4 percent) without Phase 1, and the no-RP no-Phase-1 number is already 91.9.

**Effect of the expansion size** (Table A5, split CIFAR100, T = 10, no Phase 1, lambda = 100, IN-21K): M = 100: 71.6; 200: 80.3; 400: 83.9; 800: 86.2; 1250: 86.8; 2500: 87.7; 5000: 88.4; 10000: 88.8; 15000: 89.0. Text: to beat the no-RP number (87.0), M must exceed 1250. Fig. 3a (ImageNet-R): with ReLU or squaring accuracy rises with M; with no nonlinearity, accuracy is no better than not using RP even for very large M, and a no-nonlinearity projection to 500 dimensions falls below the no-RP case.

**Effect of Gram whitening vs plain means** (from the rows above, no RP): second-order statistics without RP vs NCM, with Phase 1: CIFAR 90.6 vs 87.8; IN-R 73.9 vs 70.1; IN-A 57.7 vs 49.7; CUB 86.6 vs 85.4; OB 74.3 vs 73.4; VTAB 90.0 vs 88.2; Cars 73.0 vs 40.5. Without Phase 1: 87.0 vs 83.4; 67.6 vs 61.2; 54.4 vs 49.3; 86.8 vs 85.1; 73.1 vs 73.1; 91.9 vs 88.4; 62.2 vs 37.7. So decorrelation gives a larger gain than expansion on most sets, and expansion adds roughly another 8 to 28 percent of the remaining error.

**Centering / normalisation.** The paper does not run a centering ablation. It drops the class-mean division (Eq. 16), uses the uncentred Gram matrix, and uses no bias term; NCM uses cosine (length) normalisation. Pre-trained ResNets and CLIP need input image normalisation (App. F.7, F.8).

Table 2 (vs fine-tuning, final accuracy; CIFAR / IN-R / IN-A / CUB / OB / VTAB / Cars): Joint full fine-tuning 93.8 / 86.6 / 70.8 / 90.5 / 83.8 / 92.0 / 86.9; SLCA 91.5 / 77.0 / - / 84.7 / - / - / 67.7; RanPAC 92.2 / 78.1 / 61.8 / 90.3 / 79.9 / 92.6 / 77.7. Within 2 percent of joint full fine-tuning on three datasets, larger gap on IN-R, IN-A and Cars.

Table 3 (domain-incremental, ViT-B/16; CORe50 / CDDB-Hard / DomainNet): L2P 78.3 / 61.3 / 40.2; S-iPrompts 83.1 / 74.5 / 50.6; ADaM 92.0 / 70.7 / 50.3; **RanPAC 96.7 / 86.2 (M = 5K) / 66.6**; ablations No RPs 94.8 / 84.2 / 55.2; No Phase 1 94.3 / 81.6 / 64.7; neither 92.4 / 80.7 / 54.1; NCM with Phase 1 91.4 / 73.2 / 51.3; NCM only 80.4 / 69.8 / 46.4. DomainNet shows the largest RP gain (55.2 to 66.6 with Phase 1). Appendix Fig. A4: on CDDB-Hard, accuracy on some domains ('wild') falls after later tasks, and the "san" domain stays under 60 percent, so average accuracy can mislead; Fig. A5: DomainNet per-domain accuracy generally rises as tasks are added.

Other backbones (final accuracy, T = 10, no Phase 1; CIFAR / IN-R / IN-A / CUB / OB / VTAB / Cars): ResNet-50 with RP 75.5 / 56.5 / 35.5 / 70.9 / 68.0 / 88.6 / 48.5; without RP 73.3 / 54.8 / 36.6 / 62.7 / 60.2 / 87.7 / 42.6; NCM 61.5 / 43.1 / 25.8 / 55.4 / 57.4 / 82.2 / 26.3. ResNet-152 with RP 79.7 / 58.7 / 40.9 / 66.7 / 65.8 / 90.0 / 45.1; no RP 77.8 / 56.9 / 39.9 / 59.4 / 58.0 / 87.9 / 38.8; NCM 70.1 / 47.5 / 32.1 / 50.6 / 56.1 / 82.6 / 25.2. CLIP ViT-B/16 with RP 85.0 / 76.1 / 39.7 / 79.4 / 75.1 / 89.6 / 90.4; no RP 80.9 / 67.0 / 36.8 / 72.8 / 66.3 / 89.8 / 85.8; NCM 77.1 / 68.0 / 32.5 / 73.7 / 67.8 / 79.4 / 85.6. DIL with ResNet-50: RP 88.5 / 75.9 / 52.7 (no RP 86.7 / 75.6 / 41.9; NCM 73.1 / 65.1 / 32.9); CLIP DIL: 92.9 / 84.4 / 68.7 (no RP 90.2 / 81.7 / 59.1; NCM 83.9 / 66.9 / 51.0).

Number of tasks (Table A4, with AdaptMLP Phase 1, T = 5 / 10 / 20 / No Phase 1): CIFAR100 92.4 / 92.2 / 90.8 / 89.0 (NCM 88.6 / 87.8 / 86.6 / 83.4); IN-R 79.9 / 77.9 / 74.5 / 71.8; IN-A 63.0 / 58.6 / 58.9 / 58.2; CUB 90.6 / 90.3 / 89.7 / 89.9; OB 79.6 / 79.9 / 79.4 / 78.2; Cars 69.6 / 67.4 / 67.2 / 67.1 (NCM 41.0 / 38.0 / 37.9 / 37.9).

Task-agnostic (App. F.4): Gaussian-scheduled CIFAR-100 with 200 micro-tasks of 5 batches of 48; G and C are updated per batch, final accuracies match the T = 10 CIL results; lambda is the hard part. Regression targets (App. F.9): replacing one-hot targets by CLIP text embeddings (CIFAR100, M = 5000, T = 10) gives 77.5 percent against CLIP zero-shot 68.6 and 71.4 without RP.

### (d) Operations and memory

- Training per sample: forward through the backbone; h = phi(f^T W) is a dense L x M matrix-vector product (768 x 10000 = 7.7 M multiply-adds per sample, ESTIMATED from the stated sizes); G += h h^T is M^2 = 100 M multiply-adds (dense); C += h in column y.
- Per task: matrix inverse of (G + lambda I), M x M; for M = 10000 about 1 minute per task on a CPU (Appendix C.3), and this includes the 17-value lambda search. W_o = (G + lambda I)^-1 C is an M x K matrix product. Inference: h_test W_o is M x K multiplies (K = 200: 2 M), plus the expansion.
- Memory: class prototypes grow by a factor 1 + (M - L)/L; with K = 200 and M = 10000 about 2 to 2.5 M trainable parameters (Section 4.5, depends on PETL method) against 0.3 to 0.5 M for L2P/DualPrompt/ADaM; plus L x M = about 7.7 M frozen random weights (the paper says 10 M untrained); one-bit bipolar storage possible. The M x M Gram matrix (100 M entries at M = 10000) is needed during training only, and is smaller than SLCA's K covariance matrices of size L x L when M < sqrt(K) L. Per-class storage at inference: one column of W_o (M numbers) or, equivalently, one summed prototype c_y (M numbers) with the shared inverse.

### (e) Limitations (authors and ours)

Reliance on a strong generic extractor; many more parameters than prompting; the matrix inverse and the dense M x M statistic; lambda chosen from current-task data only (possibly sub-optimal, the paper says); PETL Phase 1 gains vary by +-1 percent by seed and by method (no best PETL method across datasets, VPT-21K outlier); benefit smaller on VTAB where tasks come from different domains; DIL average accuracy can mislead (CDDB-Hard); the Taylor / Gaussian argument is heuristic (the Chernoff statements are about norms and inner products, not a proof of the accuracy gain).

---

## 2. Revisiting Class-Incremental Learning with Pre-Trained Models: Generalizability and Adaptivity are All You Need (APER, arXiv 2303.07338)

### (a) Mechanism

- **SimpleCIL.** f(x) = W^T phi(x), phi the frozen pre-trained embedding (ViT-B/16 or ResNet), W set directly to class prototypes. Eq. (3): p_i = (1/K) sum_j I(y_j = i) phi(x_j), K = number of samples of class i. Classifier weights w_i = p_i. Inference uses a cosine classifier: f(x) = (W/||W||_2)^T (phi(x)/||phi(x)||_2) (argmax over classes). Nothing is trained, so no forgetting and no task identity needed.
- **APER (AdaPt and mERge).** Adapt the pre-trained model on the first task D1 only (Eq. 5, f* = F(f, D1, Theta)) with a parameter-efficient method, then concatenate adapted and original embeddings [phi*(x), phi(x)] (dimension doubles, e.g. 1536 instead of 768), freeze both, and set prototypes from the concatenation (Eq. 6) for every later task. If adaptation does nothing, APER reduces to SimpleCIL (the guaranteed lower bound).
- **Adapters (Section 4.2).** Full fine-tune (Eq. 7); VPT-Deep/Shallow (prompt length p = 5); SSF (Eq. 8, x_o = gamma (Hadamard) x_i + beta, scale/shift per op); Adapter (Eq. 9: MLP(x) + ReLU(x W_down) W_up, projection dim r = 16); for CNNs, BN statistic reset and re-estimation (forward pass only, no backprop) or SSF. Training: batch 48, 20 epochs, SGD with momentum, lr 0.01 cosine annealed; a temporary linear head is trained and dropped.

### (b) What features need

- A frozen PTM "already provides generalizable embeddings": SimpleCIL beats the previous prompt methods "even without training". But a domain gap hurts: Figure 2 (CIFAR100, 20 tasks) shows that fine-tuning is better on new classes and the frozen model is better on old classes.
- Different PTMs (Figure 6, ImageNet-R B0 Inc20; bar values are in the figure only, UNVERIFIED as numbers): ViTs are more generalizable than ResNets; larger ViTs better than small; supervised better than unsupervised; DINO-v2 best (trained on a 1.2 B-instance corpus); CLIP (image encoder) better than IN-21K ViTs; best APER variant improves over SimpleCIL for every PTM.
- Traditional ImageNet-style benchmarks overlap with pre-training data, so the authors add ImageNet-A, ObjectNet, OmniBenchmark and VTAB (large domain gap) for evaluation.
- Dimension need (Section 5.3.1, ObjectNet B100 Inc5, APER with SSF): PCA to k = 30 dims already competitive with DualPrompt (768 dims); randomly sampling 200 of the 1536 concatenated dimensions gives accuracy of the same scale as DualPrompt (curves in Fig. 5a-c, exact values UNVERIFIED).

### (c) Results (ViT-B/16-IN21K, Table 1; A-bar = mean over stages, A_B = last stage)

Columns: CIFAR B0 Inc5, CUB B0 Inc10, IN-R B0 Inc5, IN-A B0 Inc10, ObjNet B0 Inc10, OmniBench B0 Inc30, VTAB B0 Inc10 (A-bar / A_B each).
- SimpleCIL: 87.57 / 81.26; 92.20 / 86.73; 62.58 / 54.55; 60.50 / 49.44; 65.45 / 53.59; 79.34 / 73.15; 85.99 / 84.38.
- APER w/ Adapter: 90.65 / 85.15; 92.21 / 86.73; 72.35 / 64.33; 60.53 / 49.57; 67.18 / 55.24; 80.75 / 74.37; 85.95 / 84.35.
- APER w/ SSF: 87.78 / 81.98; 91.72 / 86.13; 68.94 / 60.60; 62.81 / 51.48; 69.15 / 56.64; 80.53 / 74.00; 85.66 / 81.92. APER w/ VPT-Deep: 88.46 / 82.17; 91.02 / 84.99; 68.79 / 60.48; 60.59 / 48.72; 67.83 / 54.65; 81.05 / 74.47; 86.59 / 83.06. APER w/ VPT-Shallow: 90.43 / 84.57; 92.02 / 86.51; 66.63 / 58.32; 57.72 / 46.15; 64.54 / 52.53; 79.63 / 73.68; 87.15 / 85.36. APER w/ Finetune: 87.67 / 81.27; 91.82 / 86.39; 70.51 / 62.42; 61.57 / 50.76; 61.41 / 48.34; 73.02 / 65.03; 87.47 / 80.44.
- Competitors (A-bar / A_B): L2P CIFAR 85.94 / 79.93, CUB 67.05 / 56.25, IN-R 66.53 / 59.22, IN-A 47.16 / 38.48; DualPrompt 87.87 / 81.15, 77.47 / 66.54, 63.31 / 55.22, 52.56 / 42.68; CODA-Prompt 89.11 / 81.96, 84.00 / 73.37, 64.42 / 55.08, 48.51 / 36.47; CPP 85.21 / 78.64, 86.60 / 85.27; LAE 92.47 / 87.62 on CIFAR, 83.13 / 77.78 on CUB; plain Finetune CIFAR 38.90 / 20.17; Finetune Adapter 60.51 / 49.32; LwF 46.29 / 41.07; SDC 68.21 / 63.05.
- Table 2 (ViT-B/16-IN1K, no exemplars, A-bar / A_B), ObjNet B0 Inc20 and IN-A B0 Inc20: iCaRL 33.43 / 19.18 and 29.22 / 16.16; LUCIR 41.17 / 25.89 and 31.09 / 18.59; DER 35.47 / 23.19 and 33.85 / 22.27; FOSTER 37.83 / 25.07 and 34.82 / 23.01; MEMO 38.52 / 25.41 and 36.37 / 24.46; FACT 60.59 / 50.96 and 60.13 / 49.82. The SimpleCIL / APER rows of Table 2 were not recovered by the extraction (UNVERIFIED).
- Text claims: SimpleCIL outperforms DualPrompt by 20 percent on CUB and 8 percent on ImageNet-A in A_B (IN-21K setting); Fig. 1 (VTAB, IN-1K): SimpleCIL beats L2P and DualPrompt with no tunable parameters; SSF and Adapter are more efficient than VPT; BN tuning beats full or partial fine-tuning of ResNet-18.
- Table 3 (IN-1K, A-bar / A_B), Office-Home DIL / DomainNet cross-domain CIL: L2P 71.61 / 59.48, 57.90 / 57.59; DualPrompt 70.85 / 58.26, 62.41 / 54.81; SimpleCIL 72.18 / 75.85, 54.80 / 58.14; APER w/ Finetune 75.44 / 77.47, 64.17 / 60.78; VPT-Shallow 71.44 / 63.26, 58.75 / 60.84; VPT-Deep 71.06 / 61.27, 60.38 / 58.31 (SSF and Adapter rows not recovered, UNVERIFIED).
- Ablations (Fig. 5d-f, curves only): SimpleCIL-PTM is worst; SimpleCIL-Adapted is better but forgets more; concatenation (APER) beats each sub-module; concatenating IN-21K and IN-1K PTMs (same dimension) is not as good as APER. Adapting more than the first stage (T = 0 ... 10, CIFAR100 B0 Inc10, Adapter) is worse than first-stage-only because "multi-stage tuning harms generalizability and results in incompatible features of former and new classes". Parameter counts (Fig. 5e) show APER with the same scale or fewer parameters than L2P/DualPrompt (which need a second ViT as retriever) and DER/MEMO/FOSTER.
- Second-order statistics, expansion, centring: **none.** The head is first-order only (prototype plus cosine).

### (d) Operations and memory

Training: first-stage SGD only (20 epochs on D1); later tasks are one forward pass per sample plus a running mean. Inference: cosine similarity of a 2d-dim (e.g. 1536) vector against K prototypes: K x 2d multiplies plus norms. Memory per class: one 2d-dim prototype (e.g. 1536 numbers) and optionally its norm. No matrix inverse, no covariance.

### (e) Limitations (authors)

The model cannot make full use of exemplars if they exist; adapting only in the first stage faces trouble when large domain gaps appear during the continual process (domain-incremental); exemplar-based CIL methods without pre-training do badly in the exemplar-free setting (Table 2). Our additions: first-order prototypes cannot repair correlated, domain-shifted features (RanPAC Table 1: Cars NCM 37.7 vs 62.2 with second-order stats); the cosine classifier does not calibrate between classes with different sample counts.

---

## 3. Lifelong Machine Learning with Deep Streaming Linear Discriminant Analysis (arXiv 1909.01520)

### (a) Mechanism

- **Frozen.** ResNet-18 body G(.) up to the penultimate pooled feature z in R^d (d = 512); only the output layer F(.) is trained, and only by closed-form statistics. Base initialisation: G (and optionally Sigma) trained offline on 100 ImageNet classes (ImageNet), or ImageNet-pretrained then fine-tuned on 1,200 CORe50 samples.
- **Per-class statistics.** Mean mu_k in R^d and a count c_k per class (Eq. 2-3): mu_y <- (c_y mu_y + z_t)/(c_y + 1), c_y <- c_y + 1. One shared covariance Sigma (d x d).
- **Covariance.** Fixed after base initialisation (estimated with the Oracle Approximating Shrinkage estimator) or plastic: Eq. (4)-(5) Sigma_{t+1} = (t Sigma_t + Delta_t)/(t+1), Delta_t = t (z_t - mu_y)(z_t - mu_y)^T/(t+1) (Dasgupta and Hsu online update, using the class mean before the update).
- **Precision and classifier.** Lambda = [(1 - eps) Sigma + eps I]^-1, shrinkage eps = 1e-4 (so identity-regularised); w_k = Lambda mu_k (Eq. 6), b_k = -0.5 mu_k . Lambda mu_k (Eq. 7); logits W z + b (Eq. 1); argmax. With the fixed variant the inverse is computed once; with the plastic variant it must be recomputed before inference (the paper notes this).
- Alternatives: Streaming QDA (a covariance per class, rejected as infeasible: 1000 classes x 512 x 512).

### (b) What features need

"SLDA is reliant on robust deep feature representations in G(.)." Fig. 3 (final ImageNet top-5 versus number of base-initialisation classes): 50 base classes suffice to beat iCaRL, 75 to beat both iCaRL and End-to-End; the standard is 100. Domain transfer (Table 3): when G is initialised on ImageNet only and applied to CORe50, results are lower than CORe50-initialised G: the largest difference for plastic Sigma is 5.6 percent (iid ordering), smallest 1.0 percent (class iid). A covariance initialised to ones (no base Sigma) was best for class orderings, hypothesised because the covariance then does not overfit the 2 base classes. The plastic covariance helps much more on CORe50 (base init only 1,200 samples; unrepresentative Sigma) than on ImageNet (about 0.5 percent).

### (c) Results (REPORTED)

- Protocols: incremental ImageNet ILSVRC-2012 (100 base classes, then 100 classes per step, top-5, normalised by the offline ResNet-18, 89.08 percent top-5), and CORe50 (10 classes, 600 train and 225 test images per class, 1 fps, 128 x 128 crops, orderings iid, class iid, instance, class instance; batches of 2 classes for incremental batch learners; 10 runs per ordering; offline top-1 93.62 percent on iid). Metric: Omega_all = (1/T) sum_t alpha_t / alpha_offline,t.
- Text results: SLDA (output layer only) outperforms iCaRL overall and ends above End-to-End on ImageNet (Fig. 1: best final top-5 accuracy, 100 x faster, 1000 x less memory than iCaRL and End-to-End); beats iCaRL by 6 percent (ImageNet) and over 11 percent (CORe50) in Omega_all; on CORe50 plastic SLDA is "almost as good as the full offline learner" on iid and close to offline on other orderings, equal to the offline output-layer-only model; vs streaming fine-tuning, ExStream: SLDA higher on class iid and class instance.
- Table 2 (CORe50, class orderings, no task labels): SLDA without task labels: class iid fixed 0.916, plastic 0.958; class instance fixed 0.913, plastic 0.959; with task labels SLDA 0.973/0.989 (class iid) and 0.971/0.987 (class instance); regularisation methods (SI, EWC, MAS, RWALK, A-GEM) without task labels about 0.41 to 0.42, with task labels 0.89 to 0.93. Cell-level assignments of Table 1 (the main Omega_all table) were scrambled by the extraction (UNVERIFIED per cell); offline last-layer values 0.853 (ImageNet), 0.979 / 0.954 / 0.966 / 0.955 (CORe50 orderings) are legible.
- Compute (ImageNet): ExStream 31 h, iCaRL 62 h, SLDA plastic 30 min. Memory: 0.001 GB for the covariance (as stated); End-to-End and iCaRL store 20 images per class, 3.011 GB; ExStream 20 prototype vectors per class, 0.041 GB.
- Ablation of centring / whitening: SLDA vs NCM is not isolated here (iCaRL uses NCM but also rehearsal); the fixed-vs-plastic covariance comparison is the second-order ablation.

### (d) Operations and memory

Per sample: running-mean update (one division/multiply-add per dimension), covariance rank-one update (d^2 = 262,144 multiply-adds at d = 512). Inference: W z (K x d multiplies) after Lambda mu_k precomputed, i.e. d^3 (about 134 M multiply-adds for d = 512) every time the plastic covariance is re-inverted. Memory: d K floats for means + K counts + d^2 floats for Sigma (d^2 = 262,144 entries = 0.001 GB at 4 bytes), K x d for W.

### (e) Limitations

Cannot train hidden layers after base initialisation (the offline model that does is better); needs a good base representation; plastic covariance changes with class order ("at most gradual forgetting"); the Gaussian shared-covariance assumption; inverse needed at each change of Sigma; ordering effects in CORe50.

---

## 4. First Session Adaptation (FSA, arXiv 2303.13199)

### (a) Mechanism

- **Head.** LDA with shared covariance. Classifier weights (Eq. 3): w_k = S~^-1 mu_k, b_k = ln(|X(k)|/N) - 0.5 mu_k^T S~^-1 mu_k, with S~ = S + I_d (identity regularisation) and S the sample covariance. NCM (Eq. 2): w_k = mu_k, b_k = ln(|X(k)|/N) - 0.5 mu_k^T mu_k; setting S~ = I recovers NCM. Updating (Algorithm 1): running terms A = sum g(x) g(x)^T (d x d), b = sum g(x) (d), count; sample covariance S = (1/(count-1))(A - (1/count) b b^T) (Eq. 4); per-class sums and counts for means. Time O(d^3 + |Y_s| d^2) and space O(d^2 + |Y_{1:s}| d) in session s.
- **Body.** Pre-trained EfficientNet-B0 (ImageNet-1k; also ResNet-18/20, ConvNeXt-22k for comparison). FSA: adapt all body parameters in session 1; FSA-FiLM: freeze the body and train FiLM scale/shift layers (about 20.5k parameters; the last block of EfficientNet-B0 is 2.9 M parameters; FSA-LL tunes that last block). Adaptation uses a temporary linear head and cross-entropy; afterwards the head is dropped and an LDA head is fitted on adapted features. The body is then frozen for all later sessions. Optimisation: batch 256; Adam for EfficientNet (SGD momentum 0.9 for ResNets); lr 1e-4 (halved every 50 epochs) for full-body, 5e-3 for FiLM; 200 epochs full-body, 150 FiLM (200 in the high-shot setting); no data augmentation except the CIFAR/CUB few-shot+ settings which follow the FACT recipe; images scaled to 224 x 224.
- **Body-adaptation indicator (4.5).** Minimum cosine distance in the pre-trained embedding space between the downstream dataset and miniImageNet (60k-image proxy of ImageNet-1k): large distance predicts large benefit of adaptation (Fig. 2, Fig. 3).

### (b) What features need / domain difference

- Pre-trained features alone (NA = no adaptation, LDA head) are strong when the dataset is close to ImageNet (CUB200: NA is already close to FSA) and weak otherwise. FSA-FiLM's gain over NA grows with cosine distance: biggest on structured datasets (SVHN, dSprites, CLEVR, FGVC, Letters), small on natural ones (Fig. 3).
- Table 5 (few-shot CIL; CIFAR100 / SVHN / dSprites-loc / FGVC / Letters / DomainNet / iNat; the extraction scrambled the row/column alignment, so only claims are recorded): a ~4 M-parameter adapted EfficientNet-B0 beats a 348 M-parameter ConvNeXt (ImageNet-22k) without adaptation on the datasets with large cosine distance (SVHN, dSprites, FGVC, Letters); on CIFAR100 (small ConvNeXt cosine distance 0.2) the ConvNeXt NA is stronger.
- Few classes/data in session 1: FACT and ALICE overfit and fail when the first session is small (Table 3); FSA still works with 20 percent of classes and 50 shots (few-shot CIL). Table 4 (inhomogeneous sessions): FSA-FiLM CIFAR100 last-session accuracy with first session from different superclass groups 66.1 +- 1.6 (Aq), 66.2 +- 1.9 (DevF), 67.9 +- 1.2 (Veh), against NA 57.4 +- 1.0; DomainNet 70.6 +- 0.6 (El-R), 71.7 +- 0.6 (F-Clp), 72.8 +- 0.5 (Tr-Sk), against NA 69.0 +- 0.4. So adaptation on a first session that looks unlike later sessions still helps.

### (c) Results (REPORTED)

- Head comparison (Fig. 1, offline, VTAB+ average, 5/10/50/all shots, NA/FiLM/full-body): LDA beats NCM and linear head at 5 and 10 shots for every adaptation; LDA about equals linear with all data; full covariance always beats the isotropic NCM; as the number of learnable parameters grows the head matters less. Meta-learned FiLM adapters (Tables 26-28, supplement) beat NA but lose to fine-tuned FiLM, with the gap growing with shots; EfficientNet-B0 beats ResNet-18 under all conditions.
- **Table 1 (high-shot CIL, last-session accuracy and PPDR in parentheses; CIFAR100 / CORe50 / SVHN / dSprites-loc / FGVC-Aircraft / Cars / Letters):** NA 68.2 (26.8) / 82.6 (14.2) / 39.9 (51.1) / 20.6 (54.0) / 41.3 (1.7) / 43.3 (40.3) / 33.6 (66.3); FSA 62.8 (34.5) / 72.8 (25.8) / 71.3 (26.6) / 68.3 (31.7) / 50.8 (6.3) / 50.3 (36.6) / 75.7 (24.2); FSA-LL 60.5 (37.2) / 82.8 (15.5) / 64.6 (33.1) / 91.5 (8.5) / 45.4 (21.7) / 45.7 (43.8) / 78.4 (21.4); FSA-FiLM 73.8 (23.4) / 85.4 (13.3) / 75.9 (23.4) / 91.3 (8.5) / 55.9 (-5.7) / 55.9 (30.2) / 79.7 (20.0); the alignment of the SVHN to Letters columns for FSA/FSA-LL in this cell list is partly scrambled by the extraction, so treat FSA and FSA-LL cells other than CIFAR100 as UNVERIFIED; the FSA-FiLM row and the Avg Diff column are consistent with the text. Avg difference to NA: E-EWC+SDC -23.3; FACT -38.0; ALICE +3.9; FSA +17.7; FSA-LL +14.2; FSA-FiLM +19.9; GDumb (1k buffer) +5.7; Offline-FiLM upper bound +30.6. Replay-free FSA-FiLM significantly beats replay-based GDumb with 1k buffer on most datasets; it reaches the best accuracy about 13.5 x faster than GDumb with a 5k buffer on CIFAR100, and on CORe50 GDumb needs at least 5k buffer and about 3 x the training time to overtake.
- **Table 3 (few-shot CIL, 50 shots per session, first session 20 percent of classes, later sessions about 10 percent each; 5 repeats):** Avg Diff vs NA: FACT -24.2, ALICE +1.7, FSA +6.6, FSA-LL +5.9, FSA-FiLM with NCM head +5.0, FSA-FiLM (LDA) +15.0. Per dataset CIFAR100: NA 57.4 (28.4), FACT 16.8, ALICE 58.0, FSA 60.3, FSA-LL 62.0, FSA-FiLM-NCM 66.4, FSA-FiLM 70.9 (20.5). Text: LDA gives about 10 percent over NCM on average in the continual setting. Offline-FiLM average reference +28.0 (CIFAR100 73.8).
- Table 2 (few-shot+ CIL, CIFAR100 and CUB200; first session about 50 to 60 percent of classes with all data, then 5/10-way 5-shot): text says FSA matches FACT on CIFAR100 with the original backbone and beats FACT by almost 10 percent and ALICE by 3.4 percent with EfficientNet-B0; FSA-FiLM has the lowest PPDR; FSA is only marginally worse than its offline counterpart; on CUB200 FSA with EfficientNet-B0 equals ALICE and NA is already good. Cell values were scrambled by the extraction (UNVERIFIED).
- Setup: 26 datasets (VTAB+ 22 plus CUB200, CORe50, iNaturalist (100 classes, 10 sessions), DomainNet (60 classes from 6 super-classes)); datasets above 120k images subsampled to 120k. Metrics: last-session top-1 and PPDR = 100 (A1 - A_S)/A1. Per-session tables (29-44) and the per-dataset head tables (11-28) are in the supplement and were not transcribed here.

### (d) Operations and memory

First session: SGD training of FiLM (cheap, 150 epochs) or of all weights. Later sessions: forward pass, additions into A, b, per-class sums; a d x d inverse (d = 1280 for EfficientNet-B0, ESTIMATED from the architecture, not stated in the paper) at update, O(d^3). Inference: K x d multiplies. Memory: d^2 + K d floats.

### (e) Limitations (authors)

If the data distribution shifts strongly between sessions (natural images then digits), first-session adaptation is unsuitable (future: combine with a GDumb-like memory). Sensitive to first-session classes (though Table 4 shows mild). Extra: needs labels and a gradient-trained first session; a covariance inverse; LDA assumes shared Gaussian covariance.

---

## 5. Cross-paper summary

| question | answer |
|---|---|
| Does a plain class mean work? | Surprisingly well if features are strong (SimpleCIL beats prompt methods), but it is the weakest variant: RanPAC NCM-only 83.4 CIFAR / 61.2 IN-R / 37.7 Cars; LDA beats NCM by about 10 percent on average in FSA few-shot CIL. |
| Does second-order whitening help? | Yes, consistently: RanPAC no-RP vs NCM +3 to +25 points (Cars +24.5 no Phase 1), FSA +10 percent average over NCM, SLDA plastic over fixed Sigma large on CORe50. |
| Does random expansion help? | Yes when it is non-linear and wide: RanPAC +1.6 to +15 points; none without nonlinearity; M must exceed about 1250 (CIFAR100) to pay off; 71.6 (M = 100) to 89.0 (M = 15000). Not tested in the other three papers. |
| Do features need adapting? | If the domain is far from pre-training, yes: first session only (APER, FSA, RanPAC Phase 1); the more diverse the first session, the better (RanPAC T = 20 gain vanishes; SLDA needs at least 50 to 75 base classes). |
| Cost | all closed-form; RanPAC and FSA/SLDA need a dense matrix inverse of size M or d; APER needs none. |

---

## 6. Fit to L (ESTIMATED / PROPOSED, not measured)

**What L has.** A frozen binary sparse detector code x (k active out of N), read by an integer counting table cnt[class][detector]; the natural score is s_y = sum over active detectors of cnt[y][j]. That is exactly an NCM / class-sum prototype dot product (x . c_y), the "first-order" head that all four papers show to be the weakest: RanPAC's c_y without the Gram inverse. Adding a class appends a row; old rows are never touched, so there is no forgetting of stored counts (same argument as in the papers). What can still hurt old classes is calibration, not storage: a new class with few counts gets smaller sums.

**Can random sparse expansion plus per-class counts reproduce the gain?**
- *Expansion:* RanPAC's h = phi(f^T W) with a ReLU is, in effect, a graded random feature code; L's binary sparse detectors are the same idea with phi = threshold and a hard sparsity constraint (k-winners-take-all). The mechanism the paper credits (nonlinear interaction features that become more linearly separable; need M well above L; Table A5) is compatible with a sparse binary expansion, and the paper says 1-bit bipolar random weights are fine. It does not show that a binary, sparse (k of M) phi works as well as ReLU; that is the open question. ESTIMATED: the loss from binarisation is the main risk.
- *Whitening:* most of RanPAC's gain over NCM in Table 1 comes from G^-1 (CIFAR100 +3.6 / IN-R +6.3 / Cars +24.5, no Phase 1, no RP), and the expansion gain is on top of it. Expansion with a plain class-sum head (no G^-1) was never tested in the papers; RanPAC Fig. 3b suggests the interactions need the decorrelating head to be exploited, since Eq. (2) is applied to the expanded features. So random expansion plus plain counts is not shown to reproduce the gain; expansion plus a cheap decorrelator might.
- *What replaces the Gram inverse (matrix-free options, all PROPOSED):*
  1. **Centring plus size normalisation** (counts, subtraction, shifts): score detector j for class y as cnt[y][j] - n_j/K_seen, with n_j = sum_y cnt[y][j]; and divide by class sample count through a reciprocal lookup or compare in the log domain. This approximates the "mean removal" that makes LDA differ from NCM and removes the shared component that makes prototypes highly correlated (RanPAC Fig. 2).
  2. **Diagonal (Jacobi) approximation of G^-1:** weight detector j by 1/(G_jj + lambda) = a lookup table indexed by the integer firing count n_j (an IDF-like or naive-Bayes log-ratio table, log2 via a LUT). Costs one table lookup per active detector, no multiply if the table stores the weighted count already.
  3. **Sparse pair statistics:** because x is binary and k-sparse, G is sparse and its update touches only k^2 pairs per sample, each an integer increment (an event-driven sparse row lookup); a truncated Neumann series G^-1 ~ D^-1 - D^-1 (G - D) D^-1 gives one correction step via sparse row lookups. This stays inside the rules (no dense matrix) but is only a heuristic approximation to the ridge solution.
  4. **Hebbian / error-driven count increments (perceptron-like, on mistakes only):** gives some decorrelation but is order dependent, so it gives up the order-invariance property that is the core argument for no forgetting; only acceptable if measured to be harmless.
- *What features need (from the papers):* strong, diverse base training and a source domain not too far from the new classes (SLDA: at least 50 to 75 of 100 ImageNet classes; RanPAC/APER/FSA: first session adaptation when the domain gap is large). For L this means the detector code must be learned (on the GPU) from a base set rich enough that new classes decompose into existing detector patterns; a code trained on a few classes will behave like SLDA with too few base classes.

**Verdict (ESTIMATED).** Random expansion plus class statistics can let a frozen binary code learn new classes with zero forgetting of stored counts, provided the base code is diverse. The accuracy gain of RanPAC is mostly from decorrelation, so plain counts will probably leave a gap; whether items 1 to 3 close it is untested.

**The one concrete small test (PROPOSED).**
1. Freeze L's code trained on a base set of classes A only (e.g. half the classes of the current benchmark); define the new classes B (disjoint). Add classes of B one at a time, counts only (and sums needed for the scorers below).
2. Score with five heads on the same frozen binary code: (H1) raw count sum (current L); (H2) centred plus size-normalised counts; (H3) diagonal-weighted counts (idea 2); (H4) sparse Neumann correction (idea 3); (H5, reference, not a chip design) float RanPAC ridge on the same code with and without a random sparse expansion, M swept over 1250, 2500, 5000, 10000 (and the no-expansion row), plus joint training on A and B as the upper bound.
3. Report accuracy on B, accuracy on A after every added class (forgetting = drop vs. before adding B), and order invariance (shuffle the class order and check identical counts and scores for H1 to H4). Success criterion proposed here: H2 to H4 close a stated share of the H1 to H5 gap on B without lowering A; threshold to be fixed before running, not after.
Label results MEASURED once run.

---

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
