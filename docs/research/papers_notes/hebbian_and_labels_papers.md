---
title: Paper notes - Hebbian coding and label quality
tags: [l, research, papers]
---

# Paper notes - Hebbian coding and label quality

Scope: decide (a) how much of the Shirt / T-shirt-top confusion on Fashion-MNIST is label overlap no model can fix, and (b) which
encoding tricks move a one-layer unsupervised feature layer plus linear/counting readout from 89 toward 92 percent.

Method: PDFs downloaded from arxiv.org and converted with pdftotext on 24 Oct 2026; every number below was read in that text unless
tagged. Tags: **VERIFIED** (read in the paper text), **UNVERIFIED** (not read in the primary text: from memory or from a search
snippet), **INFERENCE** (my reasoning, not a paper claim).

Access limits met: proceedings.mlr.press, cs.stanford.edu, cleanlab.ai, github.com (HTML), semanticscholar and the web archive were
blocked by the proxy (HTTP 403 or DNS failure). So the Coates and Ng paper (section 5) could NOT be read and its numbers are
UNVERIFIED. raw.githubusercontent.com worked (Fashion-MNIST README read). Hugging Face was also blocked.

Files kept in the scratchpad: /tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/pdfs/ (txt of each paper).

## 0. Bottom line for the reader

1. **No primary paper audits Shirt vs T-shirt/top label overlap on Fashion-MNIST.** Northcutt et al. do NOT include Fashion-MNIST
   (the word never appears in the paper text; their 10 datasets are MNIST, CIFAR-10, CIFAR-100, Caltech-256, ImageNet, QuickDraw,
   20news, IMDB, Amazon Reviews, AudioSet). The Fashion-MNIST paper gives no T-shirt vs Shirt guidance. The only primary
   measurement of label ambiguity on Fashion-MNIST that I found is Ishida et al. (ICLR 2023, arXiv 2202.00395), which re-annotated
   all 10,000 test images (~67 Mechanical Turk labels each) and estimated a Bayes error, but only for a binary regrouping that does
   not contain the Shirt/T-shirt confusion (details in section 2b).
2. **INFERENCE for (a):** the best published CNNs reach 0.963 test accuracy (README row, WRN-28-10 + Random Erasing, submitter
   claim, untested by the authors). That caps the total irreducible error at roughly 3.7 percent for ALL class pairs together, so
   label overlap cannot be what blocks 92 percent. Shirt/T-shirt is likely the largest single slice of that residual, but the share
   is not measured anywhere I could read. A 89 to 92 gap (about 3 points) is mostly a feature/readout gap, not label overlap.
3. **(b) No paper in this set reports an encoding ablation on Fashion-MNIST.** The only Fashion-MNIST Hebbian rows are: BCPNN
   88.9 percent (linear readout, 40,000 hidden units), and SoftHebb's old fully connected 75.14 percent. SoftHebb (deep) and the
   Hebbian-CNN paper 2501.17266 report no Fashion-MNIST at all. Transferable ablations come from CIFAR-10 (section 3 to 5) and must be
   re-measured on clothing.

## 1. Fashion-MNIST dataset paper (Xiao, Rasul, Vollgraf, arXiv 1708.07747v2)

### Data and labels (VERIFIED)
- 70,000 images, 28 x 28 grayscale, 10 classes, 7,000 per class; train 60,000 (6,000 randomly chosen per class), test 10,000.
- Source: Zalando front-look thumbnails (51 x 73) of 70,000 unique products; men, women, kids, neutral; white-colour products
  excluded (low contrast to the #fdfdfd background).
- Conversion pipeline: (1) convert to PNG; (2) trim edges within 5 percent of max RGB intensity of the corner-pixel colour; (3)
  resize longest edge to 28 by subsampling pixels (rows/columns skipped); (4) sharpen with a Gaussian operator radius and
  standard deviation 1.0; (5) extend shortest edge to 28 and centre; (6) negate intensities; (7) convert to 8-bit grayscale.
- Label rule, verbatim idea: "we use the silhouette code of the product. The silhouette code is manually labeled by the in-house
  fashion experts and reviewed by a separate team at Zalando. Each product contains only one silhouette code." So labels come
  from the product catalogue (full-resolution, multi-view context), not from looking at the 28 x 28 thumbnail.
- Classes (paper Table 2 / README, README says "Sandal", paper says "Sandals"): 0 T-shirt/Top, 1 Trouser, 2 Pullover, 3 Dress,
  4 Coat, 5 Sandals, 6 Shirt, 7 Sneaker, 8 Bag, 9 Ankle boots. Files are sorted by label.
- **Shirt vs T-shirt/top guidance: NONE in the paper.** No class definitions beyond names and example images. No label-noise
  estimate, no inter-annotator figure. (grep for shirt/ambig/noise in the paper text finds only the class table.)

### Benchmark (VERIFIED, paper Table 3, scikit-learn defaults, mean of 5 shuffles, Fashion / MNIST)
Best row per classifier family:
| Classifier | Parameters | Fashion | MNIST |
|---|---|---|---|
| SVC | C=10 kernel=rbf | 0.897 | 0.973 |
| SVC | C=10 kernel=poly | 0.891 | 0.976 |
| GradientBoosting | n_estimators=100 max_depth=10 | 0.880 | 0.969 |
| RandomForest | n_estimators=100 entropy max_depth=100 | 0.873 | 0.970 |
| MLP | relu hidden=[100] | 0.871 | 0.972 |
| KNeighbors | distance n=5 p=1 | 0.854 | 0.959 |
| LogisticRegression | C=1 ovr l1 | 0.842 | 0.917 |
| LinearSVC | hinge C=1 ovr l2 | 0.836 | 0.917 |
| DecisionTree | entropy depth=10 best | 0.798 | 0.873 |
| GaussianNB | uniform priors | 0.511 | 0.524 |
Linear models sit at 0.83 to 0.84, so a good unsupervised layer has about 5 points of head-room before reaching the RBF-SVC 0.897.

### README leaderboard rows relevant to ceilings (VERIFIED as README text; the authors state they have NOT tested submissions)
Human performance 0.835 (crowd-sourced, no fashion expertise, 1000 random test images, 3 labels each, majority); HOG+SVM 0.926;
2 Conv <100K params 0.925; 2 Conv+pooling (TF doc) 0.916; WRN-28-10 0.959; WRN-28-10 + Random Erasing 0.963; WRN40-4 0.967.
Note: humans see only the 28 x 28 image and score 0.835, far below the catalogue-derived labels, which tells you the labels are
informed by information absent from the thumbnail (INFERENCE).

## 2. Label-quality papers

### 2a. Northcutt, Athalye, Mueller - Pervasive Label Errors in Test Sets (arXiv 2103.14749)
Method (VERIFIED): confident learning (CL) estimates the joint Q(noisy label, true label) from out-of-sample predicted
probabilities, flags candidates, then each flagged example is shown to 5 Mechanical Turk workers (choices: given label, CL-guessed
label, both, neither). An example is a validated error if a majority (3 of 5) say the given label is not right (categories:
correctable, multi-label, neither, non-agreement).
Table 1 (VERIFIED; columns: dataset, size, model used for CL, CL-guessed, MTurk-checked, validated errors, estimated, percent):
| Dataset | Size | Model | CL guessed | MTurk checked | Validated | Estimated | % error |
|---|---|---|---|---|---|---|---|
| MNIST | 10,000 | 2-conv CNN | 100 | 100 (100%) | 15 | - | 0.15 |
| CIFAR-10 | 10,000 | VGG | 275 | 275 | 54 | - | 0.54 |
| CIFAR-100 | 10,000 | VGG | 2,235 | 2,235 | 585 | - | 5.85 |
| Caltech-256 | 29,780 | WRN-50-2 | 2,360 | 2,360 | 458 | - | 1.54 |
| ImageNet (val) | 50,000 | ResNet-50 | 5,440 | 5,440 | 2,916 | - | 5.83 |
| QuickDraw | 50,426,266 | VGG | 6,825,383 | 2,500 (0.04%) | 1,870 | 5,105,386 | 10.12 |
| 20news | 7,532 | TFIDF+SGD | 93 | 93 | 82 | - | 1.09 |
| IMDB | 25,000 | FastText | 1,310 | 1,310 | 725 | - | 2.90 |
| Amazon Reviews | 9,996,437 | FastText | 533,249 | 1,000 (0.2%) | 732 | 390,338 | 3.90 |
| AudioSet | 20,371 | VGG | 307 | 307 | 275 | - | 1.35 |
Abstract: "an average of at least 3.3% errors across the 10 datasets" and "at least 6% of the ImageNet validation set" (the table
prints 5.83; the text says 2,916, 6 percent).
Table 2 (VERIFIED) shows the MTurk split of the CL flags for MNIST: 85 non-errors, 15 errors (2 non-agreement, 10 correctable,
0 multi-label, 3 neither). The same table is given for each dataset; none is Fashion-MNIST.
Practical findings (VERIFIED): the authors say benchmark ranking can flip (ResNet-18 beats ResNet-50 on ImageNet if the share of
originally mislabeled test examples rises by 6 percent; VGG11 beats VGG19 on CIFAR-10 at +5 percent). Datasets with more careful
human curation had lower error; MNIST is lowest at 0.15 percent.
**Fashion-MNIST: absent. Shirt vs T-shirt: not mentioned.** Reproduction code: github.com/cleanlab/label-errors (not reachable
here), browsable at labelerrors.com (not reachable here).

### 2b. Fashion-MNIST-specific audits found
1. **Ishida, Yamane, Charoenphakdee, Niu, Sugiyama, ICLR 2023, "Is the performance of my deep network too good to be true? A direct
   approach to estimating the Bayes error in binary classification" (arXiv 2202.00395). Primary, VERIFIED.**
   - They collected "Fashion-MNIST-H": Amazon Mechanical Turk, all 10,000 test images, 10 randomly chosen images per task, 10-way
     multiple choice, a few example images per category shown first, $0.06 or $0.08 per task, annotations under 30 seconds
     dropped, mean/median answering time ~147 s / 78 s after filtering. About 67 annotations per image (min 53, max 79).
   - Task actually evaluated: binary. ResNet-18 trained 100 epochs, batch 128, learning rate 0.001, original labels, no
     augmentation; 10-class output regrouped with positive = {shirt, dress, coat, pullover, t-shirt/top}, negative = the other 5.
   - Result: classifier error 3.852 percent (+/- 0.041 standard error) against a label sampled from the annotators; estimated
     Bayes error 3.478 percent (+/- 0.079, 95% CI). They conclude ResNet-18 is "approaching the estimated Bayes error".
   - They note the 28 x 28 grayscale images are ambiguous while the original 51 x 73 image is much clearer (Fig. 1 of Xiao et al.).
   - **Limits for our question:** the positive group contains Shirt and T-shirt/top together, so the Shirt-vs-T-shirt confusion
     is inside the positive class and is NOT counted in 3.478 percent. That number comes from tops/dresses/coats versus
     trousers, footwear and bags, measured against crowd labels (not the original Zalando labels). No per-class table is
     printed in the text I read. Whether the Fashion-MNIST-H annotation file is published: they promise code and labels
     ("will upload"); not verified.
   - INFERENCE: merging classes can only lower Bayes error, so the 10-class Bayes error (vs crowd labels) is at least 3.478 percent,
     i.e. a ceiling near 96.5 percent. That matches the best README claims (0.959 to 0.967).
2. **Cleanlab blog "The Fashion MNIST Dataset (cited in 2,200+ papers) contains Hundreds of Miscategorized Items"
   (cleanlab.ai/blog/learn/csa/csa-4/). UNVERIFIED (page blocked; only a search-result summary seen):** Cleanlab Studio reportedly
   flagged more than 100 images labelled Shirt as likely T-shirt/top and more than 40 as Dress, plus some Sneaker/Ankle boot
   mislabels. The summary did not say whether counts are train or test or the denominator. Vendor blog, not peer reviewed.
   A community README (github.com/timothylimyl/FASHION-MNIST) says most CNN mistakes involve classes 0 and 6 (search snippet,
   UNVERIFIED, anecdotal).
3. Weiss, Gomez, Tonella (arXiv 2207.10495, "Generating and Detecting True Ambiguity") built "Fashion-MNIST-ambiguous" by
   generating images that admit two classes (HF dataset mweiss/fashion_mnist_ambiguous, example labels like Pullover/Shirt
   0.54/0.46 per a search snippet). It is a synthetic ambiguity set, not an audit of the original labels. I read the text:
   it contains no count of natural label errors. Not used further.
4. Noisy Prediction Calibration (arXiv 2205.00690) qualitatively notes Sneaker/Ankle boot ambiguity (search snippet, UNVERIFIED).
**Gap:** no source found giving a measured fraction of wrong/ambiguous Fashion-MNIST labels in total, nor per-class numbers, nor a
Shirt-vs-T-shirt-specific count in a primary document. The reader should measure it: take the project's own confusion matrix,
and for the 0/6 pair compute the fraction of test errors, then relabel a sample of ~200 by hand at full resolution.

### Answer to (a), with honesty about uncertainty
- Measured (VERIFIED): binary-regrouped crowd-label Bayes error 3.478 percent; best claimed CNN accuracy 0.963 to 0.967.
- INFERENCE: total irreducible error is of order 3 to 4 percent; Shirt/T-shirt is one slice of it. A unsupervised-features +
  linear/counting readout at 89 percent has 11 percent error, so at least ~7 points of error are model-fixable and the 92 percent
  target (8 percent error) sits well above the label floor. Do not budget more than the Shirt/T-shirt share of ~3.5 points as
  unfixable, and treat even that as an upper bound until measured.

## 3. BCPNN (Ravichandran, Lansner, Herman; arXiv 2406.04733, "Unsupervised representation learning with Hebbian synaptic and structural plasticity in brain-like feedforward neural networks")

### Method (VERIFIED)
- Two layers. Input layer: H_inp hypercolumns (one per input attribute/pixel), each with M_inp minicolumns that code the
  attribute value as a discrete probability distribution. Hidden layer: H_hid hypercolumns of M_hid minicolumns each.
- Activation: support s_jk = b_jk + sum_i sum_m pi_im * w_imjk * c_ij; pi_jk = softmax over the M_hid minicolumns of hypercolumn j
  (Eq. 1 and 2). This is soft winner-take-all per hypercolumn, no top-k threshold. c_ij is a binary patchy-connectivity mask.
- Learning (Hebbian-Bayesian, online, no batching): p-traces with exponential averaging rate alpha:
  p_im <- (1-alpha) p_im + alpha pi_im; p_jk <- (1-alpha) p_jk + alpha pi_jk; p_imjk <- (1-alpha) p_imjk + alpha pi_im pi_jk.
  Bias b_jk = log p_jk; weight w_imjk = log( p_imjk / (p_im p_jk) ) (pointwise mutual information). Gaussian noise of amplitude
  lambda added to the support.
- Structural plasticity: usage U_ij = sum_{m,k} p_imjk w_imjk / sum_k c_ik (normalised mutual information of the hypercolumn
  pair); every T_swap iterations, per hidden hypercolumn, the lowest-usage active connection is swapped with the highest-usage
  silent one if U_silent > rho * U_active; fan-in kept constant. This finds localized receptive fields.
- Input coding for greyscale (MNIST) uses M_inp = 2 minicolumns per pixel (Table 3, MNIST). For F-MNIST the paper does not
  print a separate parameter table; the exact F-MNIST input encoding and number of unsupervised epochs are UNVERIFIED
  (INFERENCE: same M_inp = 2 intensity/complement coding). Colour/other data use GMM population coding (posterior of k Gaussian
  components with identity covariance, one GMM per attribute) or DoG filtering (3x3 and 5x5 Gaussians, sigmoid-normalised).
- Parameters printed for MNIST (Table 3): H_inp 784, M_inp 2, H_hid 30, M_hid 100, fan_in 78, alpha 0.0001, lambda 0.001,
  N_unsup 5 epochs, N_swap 100, T_swap 500, rho 1.1. Reported comparison model: H_hid = 400, M_hid = 100, fan_in = 78
  (N_hid = 40,000 minicolumns, ~10 percent connectivity).
- Readout (VERIFIED): linear softmax classifier on the hidden activities, cross-entropy, minibatch 100, 25 epochs, Adam (lr 0.001,
  beta1 0.9, beta2 0.999, eps 1e-7); mean +/- std over n = 5 runs. Test set is the unused test split.
- Hardware context: C++ with OpenACC on one A100; 30 min per run for 400 x 100.

### Exact Fashion-MNIST rows (VERIFIED)
Table 8 / Table A2 (linear classification on hidden representations, accuracy %):
| Model | F-MNIST |
|---|---|
| Linear classifier on raw pixels | 83.5 +/- 0.08 |
| Feedforward BCPNN (400 x 100, fan_in 78) | 88.9 +/- 0.04 |
| RBM (3000 binary units) | 88.3 +/- 0.05 |
| AE (3000 units, L1 sparse) | 87.6 +/- 0.11 |
| 3-layer MLP | 89.5 +/- 0.14 |
Table 6 (ablation of connectivity, F-MNIST): random connections 85.6 +/- 0.08; local pre-defined 9x9 receptive fields
86.7 +/- 0.05; structural plasticity 88.9 +/- 0.04. So learned receptive fields add +3.3 over random and +2.2 over fixed local
patches.
MNIST for scale (Table 7): linear 91.3, BCPNN 98.6, RBM 98.2, AE 98.3, MLP 98.6.
Other facts: hidden activities are sparse (most near 0, some near 1, "intermediate values mostly absent"); entropy table shows
F-MNIST S_activity 0.646 +/- 0.012 and S_usage 3.770 +/- 0.014 (Table 4 extract; hypercolumns are nearly winner-take-all).

### Dictionary-size / architecture effect (VERIFIED text; plots not readable)
Grid: N_hid in {1000, 10000, 100000}, M_hid in {10, 20, 50, 100, 200, 500, 1000}, fan_in in {0.01, 0.02, 0.05, 0.1, 0.2, 0.5} x H_inp.
Body text: performance better with higher N_hid; U-curve in M_hid with best near 200 (preferred 50 to 200); U-curve in fan_in best
near 50 (preferred 50 to 200 inputs). **Inconsistency:** Appendix D says classification error "was consistently lower with lower
N_hid", contradicting section 6.6; the figures are images so I could not settle it. No per-dataset F-MNIST numbers for the grid are
given in text.
Convergence: BCPNN reached 98 percent on MNIST in ~1e4 to 1e5 iterations (1 to 2 epochs) versus 1e6 iterations (20 epochs) or more for MLP/RBM/AE.

### Take-away for the project
Closest published analogue to a soft-k-winner unsupervised layer with a linear readout: 88.9 percent on F-MNIST with a very wide
code (40,000 units, exactly one soft winner per 100). That is the same ~89 as the reader's current number; the paper does not
show how to pass 89. The MLP reference (89.5) shows the linear readout is not the main limit, the feature set is.

## 4. Sparse-coding / Hebbian-CNN paper (Jimenez Nimmo, Mondragon; arXiv 2501.17266, "Advancing the Biological Plausibility and Efficacy of Hebbian Convolutional Neural Networks")
**The paper reports NO Fashion-MNIST results** (VERIFIED: the string "fashion" never occurs in the text; datasets are CIFAR-10,
MNIST, STL-10 only). Notes kept because it is the nearest soft-versus-hard competition ablation:
- Compared mechanisms: hard WTA ("Optimal-HardWTA", Journe architecture, cosine-similarity activation, Grossberg Instar update),
  SoftWTA (SoftHebb of Journe et al.), Lagani-HardWTA, plus presynaptic competition, Gaussian lateral inhibition, homeostatic,
  temporal competition, depthwise/residual variants, BCM rule, Dale's principle.
- Table 4, CIFAR-10 test, mean over last 10 epochs (5 seeds): Backprop 0.752; Optimal-HardWTA 0.752; **SoftWTA 0.775** (median
  0.781, max 0.795); Lagani-HardWTA 0.597. Abstract: hard-WTA reaches 75.2 percent, +10.6 over the earlier hard-WTA result 64.6.
- Table 5, MNIST: Backprop 0.9853; Optimal-HardWTA 0.9829; SoftWTA 0.9787; Lagani-HardWTA 0.9468.
- INFERENCE: on a simple dataset (MNIST) a good HARD WTA beats SoftWTA by ~0.4 points; on a harder one (CIFAR-10) SoftWTA beats the
  same hard WTA by ~2.3 points. Soft coding is not uniformly better; it helps more as the data get less separable (Fashion-MNIST is
  in between). The key to the hard-WTA gains was the learning-rule and activation choices, not the soft/hard switch alone.
- I did not find "sparse coding" with an explicit dictionary-learning readout in this paper despite the framing; it is a CNN with
  Hebbian competition.

## 5. SoftHebb (Journe, Rodriguez, Wang, Moraitis; ICLR 2023, arXiv 2209.11883)

### Rule (VERIFIED)
- Soft winner-take-all with temperature tau (base b): y_k = exp(u_k/tau) / sum_l exp(u_l/tau); u_k = total weighted input.
  Hidden-layer biases omitted (uniform prior).
- Update: dw_ik = eta * y_k * ( x_i - u_k * w_ik ). All terms local to the synapse; provably performs Bayesian inference of hidden
  causes (Moraitis et al. 2021).
- Soft anti-Hebbian term (new here): the same update negated for every neuron except the maximally activated one.
- Per-neuron adaptive learning rate: eta_i = eta * (r_i - 1)^q with r_i the norm of the neuron's weight vector (goes to 0 as the
  weights reach the unit sphere); q is a power hyperparameter. This is what allows 1 unsupervised epoch.
- Forward activation (propagation to the next layer) is NOT the softmax: it is RePU combined with Triangle (below). Softmax is
  only the post-synaptic variable of the plasticity rule.
- Triangle (introduced by Coates et al. 2011): subtract the mean activation across channels at each position, then rectify:
  Triangle(u_j) = RePU(u_j - mean(u)), RePU(u) = u^p for u > 0 else 0. Power p tuned (CIFAR layer 1: 0.7, layer 2: 1.4, layer 3: 1).
- Training: batch norm (non-trainable gamma = 1, beta = 0) -> SoftHebb conv (stride 1, same padding) -> pooling (stride 2) ->
  activation; layers trained greedily, frozen; ~5000 weight updates optimum on CIFAR-10 (one epoch, mini-batch 10 for CIFAR/MNIST,
  20 for STL-10 unlabeled); width factor fw = 4 (each layer has 4x the filters of the previous, first layer 96, ImageNet 48);
  pooling stride 2 until output <= 4 x 4. Readout: linear classifier with dropout 0.5, mini-batch 64, 50 epochs for MNIST and
  CIFAR-10 (100 STL-10, 200 ImageNet), initial lr 0.001 halved at 20, 35, 50, 60, 70, 80, 90 percent of epochs.
- CIFAR-10 hyperparameters found (Table 3): layer 1: eta 0.08, q 0.5, kernel 5, 1/tau 1, MaxPool kernel 4, Triangle, power 0.7;
  layer 2: eta 0.005, q 0.5, kernel 3, 1/tau 0.65, MaxPool 4, Triangle power 1.4; layer 3: eta 0.01, q 0.5, kernel 3, 1/tau 0.25,
  AvgPool 2, Triangle power 1. Architecture (Table 4, MNIST/CIFAR): 5x5 conv96 -> 3x3 conv384 -> 3x3 conv1536, 4x4 MaxPool x2
  then 2x2 AvgPool, Triangle each.

### Accuracy and depth (VERIFIED)
- Deep SoftHebb (3 hidden conv layers for MNIST/CIFAR, 4 for STL-10, 5 for ImageNet 160 px), 1 unsupervised epoch:
  MNIST 99.35 +/- 0.03; CIFAR-10 80.31 +/- 0.14 (Table 1: 80.3, 4 layers); STL-10 76.23 +/- 0.19; ImageNet 27.3 (top-1);
  ImageNette 80.98 +/- 0.43. Same nets with end-to-end backprop (ReLU): MNIST 99.45, CIFAR-10 83.97, STL-10 74.51, ImageNette 85.30.
- Single conv layer + linear readout on CIFAR-10 (VERIFIED): **SoftHebb 71.10 +/- 0.06, hard WTA 62.69 +/- 0.47, random
  weights 63.93 +/- 0.22**, backprop on the same two-layer network 72.42 +/- 0.24. Best regime at temperature tau ~ 1 where "R1"
  (unit-norm) and non-R1 features co-exist.
- Activation ablation on CIFAR-10 (App. B.3): ReLU 70.68 +/- 1.07; tanh 56.13 +/- 0.34; RePU 79.08 +/- 0.13; softmax 54.05
  +/- 0.55; **RePU + Triangle 80.31 +/- 0.14**. So triangle adds +1.23 over RePU alone and +9.63 over ReLU in the deep net
  (the other hyperparameters were not re-tuned per case).
- Depth: layer-wise accuracy rises with depth only when width grows (width factors 1, 2, 4; fw = 4 needed); fully connected
  stacks get worse: 1 hidden FC layer 43.9 +/- 0.18 (CIFAR-10) and 36.9 +/- 0.19 (STL-10) versus backprop 55.7 and 50.0; two stacked
  FC layers 32.9 and 31.5.
- **Fashion-MNIST: only the inherited FC baseline** (Moraitis et al. 2021): MNIST 96.94 +/- 0.15 and Fashion-MNIST **75.14 +/-
  0.17** with 2000 hidden neurons, one hidden layer. The paper reports no deep or conv Fashion-MNIST number. This 75.14 is far
  below the BCPNN 88.9 or even raw-pixel linear 83.5, so the plain FC SoftHebb layer as published is not a competitive one-layer
  feature layer for clothing (VERIFIED as a quoted number; the setup behind it is in the earlier paper, UNVERIFIED).

## 6. Coates and Ng, "An analysis of single-layer networks in unsupervised feature learning" (AISTATS 2011) - UNVERIFIED SECTION
The paper is not on arXiv and every mirror I tried was blocked, so **all numbers in this section come from memory and are
UNVERIFIED**; re-check them against the PDF (proceedings.mlr.press/v15/coates11a.html) before using them in a decision.
Recalled design (the pipeline that SoftHebb credits as the source of "Triangle"):
- Pipeline: extract random 6 x 6 patches (stride 1 at test time), per-patch brightness and contrast normalisation, ZCA whitening
  (eps ~ 0.1), learn K dictionary elements (K-means, sparse autoencoder, sparse RBM or GMM), encode every patch, sum-pool the
  feature map over 4 quadrants of the image (so a 4 K-dimensional vector), standardise, then L2 SVM.
- Encoders: hard assignment (1-of-K); **soft threshold** f_k(x) = max(0, c_k^T x - alpha) with alpha ~ 0.25 (cheap, k-sparse-like);
  **triangle** f_k(x) = max(0, mean_j(z_j) - z_k), with z_k = ||x - c_k||_2, so about half of the units are exactly 0 (a
  "k-winner-ish" code that is not a hard top-1).
- Remembered findings: (i) K-means with triangle encoding (and the soft-threshold on dictionaries) beat hard K-means by a large
  margin; (ii) more dictionary elements helped monotonically up to the largest size tried (4,000); (iii) the headline CIFAR-10
  accuracies were roughly: K-means triangle 1,600 features about 77.9 percent, 4,000 features about 79.6 percent; sparse
  autoencoder about 73 percent; sparse RBM about 72 percent; hard K-means in the high 60s; NORB about 97 percent; the best results
  also needed small stride, ~6 pixel receptive field and whitening. (All UNVERIFIED.)
- Note the SoftHebb paper confirms only that Triangle comes from Coates et al. 2011 and that it "subtracts the mean activation
  calculated over all channels at each position and then applies a ReLU" (VERIFIED in section 5 above).
- No Fashion-MNIST in this paper (it predates the dataset).

## 7. Synthesis for (b): what each trick plausibly contributes on 28 x 28 clothing

Evidence level is stated per row. None of these are Fashion-MNIST ablations; they are CIFAR-10 differences or single Fashion-MNIST
rows. Treat every "expected" number as a hypothesis to measure.

| Trick | Best evidence (this set) | Size of effect there | Evidence on Fashion-MNIST |
|---|---|---|---|
| Soft (graded) instead of hard 1-of-K | SoftHebb vs hard WTA, 1 conv layer, CIFAR-10: 71.10 vs 62.69 (VERIFIED). 2501.17266: SoftWTA 77.5 vs Lagani hard 59.7, but a tuned hard WTA reaches 75.2 and wins on MNIST (98.29 vs 97.87) (VERIFIED) | +8.4 (CIFAR single layer), sign flips on MNIST | none |
| Triangle activation (subtract channel mean, ReLU) | SoftHebb App. B.3: RePU+Triangle 80.31 vs RePU 79.08 (VERIFIED); Coates recalled: triangle vs hard K-means about +9 (UNVERIFIED) | +1.2 on top of a good activation, ~+9 versus hard | none |
| Bigger dictionary | BCPNN says higher N_hid generally better (body text) but Appendix D contradicts (VERIFIED, inconsistent); SoftHebb width study: depth helps only if width x4 per layer (VERIFIED); Coates recalled +1.7 from 1,600 to 4,000 (UNVERIFIED) | small, diminishing | BCPNN F-MNIST is already at 40,000 units for 88.9 |
| 2x2 quadrant sum-pooling | Coates design (recalled, UNVERIFIED); SoftHebb uses max/avg pool 4x4 stride 2 between layers (VERIFIED); BCPNN has no pooling (uses learned patchy receptive fields) | not isolated in any paper read | none |
| Learned localized receptive fields | BCPNN F-MNIST: random 85.6 -> local 86.7 -> structural plasticity 88.9 (VERIFIED) | +3.3 over random | direct |
| Wider/learned unsupervised code vs raw pixels (linear) | BCPNN F-MNIST: 83.5 -> 88.9; RBM 88.3; AE 87.6 (VERIFIED) | +5.4 | direct |
| Nonlinear readout instead of linear | MLP 89.5 vs BCPNN linear 88.9; RBF-SVC raw pixels 0.897 (VERIFIED) | +0.6 to +1 | direct |

### INFERENCE: path from 89 toward 92 for one unsupervised layer + linear/counting readout
1. The published ceiling for a ONE-layer, ~40k-unit soft-WTA Hebbian code with a linear readout is 88.9 (BCPNN); RBM 88.3; the
   RBF-SVC on raw pixels is 89.7. Going past ~90 with a single layer needs spatial structure, which none of these papers adds on
   Fashion-MNIST: README rows for HOG+SVM (0.926) and tiny 2-conv CNNs (0.916 to 0.925) show that local oriented-edge features plus
   pooling are what separate ~89 from ~92.
2. Therefore the most promising levers, in the order the evidence supports (not measured on this data): (i) a convolutional/patch
   encoding with 4-quadrant (or finer, e.g. 3 x 3) pooling instead of a flat code (HOG-like, ~+3 over flat pixels in the README
   comparison: HOG+SVM 0.926 vs raw-pixel SVC 0.897); (ii) a soft or triangle-style graded code in place of hard top-1 (CIFAR
   evidence: several points, sign not guaranteed on easy data); (iii) dictionary growth, with diminishing returns after a few
   thousand patch atoms; (iv) a better readout (counting readout loses to float, per the project's own F4 note, not from these papers).
3. For the Shirt/T-shirt pair specifically: sleeve length, collar and button placard are 1 to 3 pixels at 28 x 28; pooling that
   preserves vertical position (quadrants/rows) is more likely to help than a bigger flat dictionary. This is a hypothesis; no
   cited paper measures it.

## 8. Unverified and missing items checklist
- Coates and Ng: every number (section 6) UNVERIFIED; primary PDF not reachable.
- Cleanlab Shirt to T-shirt flags (>100) and Dress (>40): UNVERIFIED search summary of a vendor blog, no denominator.
- F-MNIST input coding and epochs for BCPNN: UNVERIFIED; M_inp = 2 is printed only for MNIST.
- Per-class Fashion-MNIST label-error rates: not found anywhere.
- Fashion-MNIST-H release status and per-pair disagreement matrix: not verified; the paper text I read gives only the binary
  Bayes error 3.478 percent and classifier error 3.852 percent.
- BCPNN N_hid trend contradicts itself between body (higher is better) and Appendix D (lower error with lower N_hid).
- The "Human Performance 0.835" and the 0.963 to 0.967 CNN rows are README submissions the maintainers say they have not tested.

Related: [Notes index](INDEX.md)
