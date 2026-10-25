---
title: Paper notes - neurogenesis, expert gates and expandable representations
tags: [l, research, papers]
---

# Paper notes - neurogenesis, expert gates and expandable representations

Question behind these notes: when a chip grows new nodes for a new class and freezes the old ones, who decides, at
inference, whether an input belongs to the old part or the new part? Our own test: frozen old nodes plus new nodes
removed overwriting, but the new nodes were not selective (they fired on old-class images), so old classes were lost
to new ones. This is the old-versus-new decision problem.

Papers read in full from the arXiv PDFs (text extracted with pdftotext; ids checked against the title page of each
PDF): Draelos 1612.03770, Aljundi 1611.06194, Yan 2103.16788, Wang (FOSTER) 2204.04662. For paper 4 I chose
**FOSTER** (MEMO 2205.13218 was downloaded and its title page checked, but NOT read: UNVERIFIED). The DER appendix and the FOSTER supplementary material are in the PDFs and were read. Numbers below are copied from the papers (they are the authors' MEASURED
numbers, not ours).

## 1. Neurogenesis Deep Learning (NDL), Draelos et al., arXiv 1612.03770

**(a) Mechanism.** A stacked autoencoder (AE) is pre-trained on a few classes. For a new class, per-level
reconstruction error (RE, squared error between input and reconstruction through that level) is computed on every
new-class sample. Samples whose RE exceeds a per-level threshold (set from the RE statistics of previously seen
classes) are "outliers". If the number of outliers exceeds MaxOutliers and fewer than MaxNodes_L new nodes have been
added, new nodes are added to that level (Procedure 1). Plasticity step: train on the outliers, only the encoder
weights of the new nodes at full learning rate LR; old encoder weights fixed; decoder weights from old nodes at LR/100.
Stability step: train the whole level on new data plus "intrinsic replay" (IR) at LR/100. IR stores, per old class,
the mean and the Cholesky factor of the covariance of the top encoder layer, samples a Gaussian
(mu + N(0,1)*Chol) and decodes it to make pseudo-old images. A new node is also added when the level below added one.
Nodes are added only when the AE cannot represent the data, never by label.
**Decision between old and new: there is none.** The network is a single autoencoder; "novelty" is detected only
at training time through RE (outlier test). There is no inference-time gate and no classifier in the paper.

**(b) Decision needs and accuracy.** The novelty test needs a trained AE and RE thresholds taken from old-class
statistics; the paper itself lists "better ways of establishing and using RE thresholds" and the choice of
MaxOutliers as open. No accuracy of an old/new decision is reported (UNVERIFIED that none exists elsewhere; none in
the text read).

**(c) Results.** Protocol: neither task- nor class-incremental classification. It is **reconstruction only**: no
classification accuracy is given anywhere. MNIST: AE 784-200-100-75-20-75-100-200-784 pre-trained on digits 1 and 7,
then digits 0,2,3,4,5,6,8,9 added one class at a time. Controls: CL (fixed size, no IR), NDL (no IR), CL+IR (fixed
size, IR), NDL+IR. Reported only as plots (Fig. 4-6): CL and NDL without IR barely improve reconstruction; NDL+IR is
"slightly" better than CL+IR on new and old digits; the network size at the end is shown in Fig. 4F (no number in the
text). NIST SD 19: AE 784-1000-500-250-50-250-500-1000-784 trained on digits 0-9, then upper and lower case
letters; in that test training data (not IR) was used for replay. Fig. 6: final RE of NDL+IR is lower than CL+IR for
all classes and lower than the initial RE for all classes. Fig. 8: 20 random class orders, mean number of new neurons
per class with standard deviation (values only in the plot). Note a limitation of the evidence: the control CL+IR
starts larger than NDL+IR (same size as the grown net), and the text says initial RE of CL+IR is lower because the
initial NDL+IR net is smaller.

**(d) Operations and memory.** Per class: mean vector and Cholesky factor of the top layer covariance (n^2/2 values for
top width n, e.g. n=20 for MNIST: 20 + 210 values, n=50 for NIST) plus n^3/6 operations once. Dense matrix
multiplications everywhere (y = s(Wx+b)). Training cost: the paper argues NDL is a "constant factor" over normal
training but gives no measured cost (ESTIMATED by the authors, not measured).

**(e) Limitations.** Stated by the authors: tested only on gray-scale objects on a blank background; optimal number of
IR samples unknown; thresholds and MaxOutliers not principled; adaptation might also be obtained with a larger fixed
net with restricted learning rates. No classification result, so selectivity of new nodes (our problem) is never
tested. No exemplars are needed, but IR needs a generative statistic per class and a decoder. Does not give
class-incremental accuracy.

**(f) Fit to L.** The idea that fits: grow a node only when a counted novelty statistic says the existing nodes
cannot represent the input, and keep per-class summary statistics (mean and covariance of the top code) instead of
images. It does NOT solve the old-versus-new decision. Small test: replace RE by a counted statistic: for each
sample count how many of the active old nodes fired (or the sum of match scores); if below a threshold fitted to the
old-class distribution (e.g. a low percentile), flag as novel and allocate a new node on those samples only. Measure
how often old-class test images are flagged (false novelty) and how often new-class images are flagged (true
novelty); that is exactly the missing selectivity measurement.

## 2. Expert Gate, Aljundi, Chakravarty, Tuytelaars, arXiv 1611.06194

**(a) Mechanism.** One expert network per task (AlexNet-based), one under-complete one-layer autoencoder per task as
gate. Input to the gate: activations of the last convolutional layer of an ImageNet-pre-trained AlexNet,
standardised with ImageNet statistics (same for all gates so that errors are comparable) then a sigmoid. Encoder: one
fully connected layer to 100 units plus ReLU; decoder: fully connected plus sigmoid; trained with cross-entropy
reconstruction loss; test-time error = Euclidean distance. Hidden size tried: 10, 50, 100, 200, 500; 100 chosen. At
test time a softmax over negated reconstruction errors, p_i = exp(-er_i/t)/sum_j exp(-er_j/t), t = 2; the expert whose
autoencoder has the lowest error is loaded (only one expert in memory); optionally more than one expert when
p_i > a threshold (0.1 tested). Training of a new task: train its autoencoder on the new task data only; no old data
is touched, old experts and old gates are frozen. Relatedness Rel(Tk,Ta) = 1 - (Er_a - Er_k)/Er_k, with Er_a the error
of the old autoencoder on the new data (validation data of the new task); the most related old model is used as the
start for the new expert, with Learning without Forgetting if Rel > 0.85, otherwise fine-tuning.
Decision between old and new: the gate by lowest reconstruction error. This is a **task-incremental** setting in
which the gate predicts the task id.

**(b) Gate accuracy (quoted).** Table 3, discriminating between 6 tasks: Expert Gate (no access to previous data)
Scenes 94.6, Birds 97.9, Flowers 98.6, Cars 99.3, Aircrafts 97.6, Actions 98.1, average **97.6%**; discriminative task
classifier trained on all tasks' data: 97.0, 98.6, 97.9, 99.3, 98.8, 95.5, average **97.8%**. In the 3-task
experiment the gate selects the right model for **99.2%** of test samples. Discriminative classifier with stored
samples per task (10 to 2000, Fig. 5) approaches the gate only at 2000 samples per task. With a probability
threshold of 0.1 for multiple experts, 3.7% of test samples go to more than one expert and the average rises by 0.9
point to 68.2%. Confusions are among tasks that overlap (people in Scenes versus Actions). Important caveat: the
tasks are different datasets (scenes, birds, flowers, cars, aircraft, actions) on top of a strong pre-trained feature
extractor; the gate separates datasets, not neighbouring classes inside one dataset. Not tested by the paper.

**(c) Results.** Protocol: task-incremental, the output of the gate chooses the expert, then the expert classifies
within its own task. Table 1 (3 tasks, accuracy %): Joint training* (all data) Scenes 63.1, Birds 58.5, Flowers 85.3,
avg 68.9; multiple fine-tuned models with oracle gate 68.5; multiple LwF models with oracle gate 68.7; Expert Gate
63.5 / 57.6 / 84.8, avg **68.6**; single fine-tuned model avg 58.2 after the last task (Scenes down to 46.0, Birds
43.9); single LwF model avg 66.1. Table 2 (6 tasks): Joint training* avg 66.5; "most confident model" (take the
expert with the highest output score) avg **48.7**; Expert Gate **67.3** (Scenes 60.4, Birds 57.0, Flowers 84.4, Cars
80.3, Aircrafts 72.2, Actions 49.5). So choosing by the experts' own confidence loses about 19 points relative to the
reconstruction gate. Task relatedness (Fig. 6): LwF helps when relatedness is high (e.g. SVHN to Letters), degrades
when low (ImageNet to Letters) and can fail when very low (ImageNet or Flowers to Cars). Video prediction (Table 4,
pixel L1, lower is better): Expert Gate Highway 13.4, Residential 40.3, City 16.5, avg 23.4; joint training 23.8;
sequential fine-tuning avg 31.1.

**(d) Operations and memory.** Expert ~220 MB, autoencoder ~28 MB each (AlexNet-scale, stated by the authors). One
expert in memory at a time; all N gate autoencoders must be run for every input (cost grows linearly with the number
of tasks, each is two dense layers). Dense matrix products throughout.

**(e) Limitations.** No exemplars needed (the central claim). The gate does not cover class-incremental
within-task confusion; the paper gives no experiment where two tasks come from the same dataset with similar
classes. It relies on a good fixed pre-trained representation (ImageNet AlexNet); decisions between tasks that
share a domain are untested. One expert per task grows memory linearly. Overlapping tasks need multi-expert
activation. The relatedness threshold 0.85 is a tuned constant.

**(f) Fit to L.** This is the closest match to our old-versus-new problem and the strongest evidence that a gate
can be learned from the new data alone (97.6% versus 97.8% with all data stored). It maps to a counting gate
without any autoencoder: per task (or per group of new nodes) keep a counted "familiarity" statistic of the input
code (for example per-bit counts of the binarised input code, with a score = number of input bits that agree with the
task's frequent-bit set, or the count-weighted agreement), and route by the highest normalised score. Concrete small
test: use the two label sets we already have (old classes versus a new class), build the per-task bit-frequency
table from the training images of that task only, score the held-out images of both with the same normalisation, and
report gate accuracy per class pair and for the "most confident node" baseline (in the paper the confident-expert
baseline lost 18.6 points on the 6-task average: 48.7 vs 67.3). If gate accuracy for neighbouring classes (digits,
CIFAR classes) falls far below the paper's 97.6%, the gate is the bottleneck, not the growing nodes.

## 3. DER: Dynamically Expandable Representation, Yan, Xie, He, arXiv 2103.16788

**(a) Mechanism.** At step t a new feature extractor F_t is created (initialised from F_{t-1}) and the feature
vector is the concatenation u = [Phi_{t-1}(x), F_t(x)]; all earlier extractors and their batch-norm statistics are
frozen. One linear classifier H_t over all seen classes takes u; weights for old features are inherited and the new
weights are random. Two-stage training: (1) representation stage: cross-entropy over new data plus memory, plus an
**auxiliary loss** L_Hat on the new feature F_t(x) alone, with an auxiliary classifier over |Y_t|+1 outputs (the new
classes plus one "other" class that merges all old classes), weight lambda_a = 1; plus a channel mask (sigmoid with
annealed sharpness s, adapted from HAT) with sparsity loss L_S, weight lambda_s, so the new extractor is pruned to
the size the new classes need (the "dynamic expansion"); (2) classifier stage: re-initialise and retrain the
classifier head on a class-balanced subset of memory plus new data, 30 epochs, temperature delta = 5 (CIFAR) or 1
(ImageNet). Decision between old and new: **none explicit at inference.** One softmax over all classes decides. The
old-versus-new separation is learned inside the classifier, with the "other" auxiliary output being the only
not-old signal, applied only to the new extractor and only while training.

**(b) Decision needs and accuracy.** Needs stored exemplars of old classes (memory) in both stages. No separate
old/new accuracy is reported. Effect of the auxiliary "new versus old-as-one-class" loss (Table 4, CIFAR100-B0, 10
steps): expandable representation off: avg 61.84 / last 40.81; expansion on, no auxiliary loss: 73.26 / 63.07;
expansion plus auxiliary loss: 75.36 / 65.34. So the not-old auxiliary output is worth +2.10 average and +2.27 last
step on top of expansion (MEASURED by the authors; expansion alone is worth most). lambda_a sensitivity (Table 6):
0.1 gives 74.12, 0.5 gives 74.41, 1 gives 74.64, 5 gives 74.52, 10 gives 73.54 (all plus or minus 0.06 to 0.33).

**(c) Results.** Protocol: **class-incremental** (no task id at inference), with exemplar memory: 2,000 total on
CIFAR-100 B0 and ImageNet-100 B0, 20 per class for B50, 20,000 for ImageNet-1000. Table 1 CIFAR100-B0 (ResNet-18,
avg accuracy over steps, 5/10/20/50 steps): DER 75.55 / 74.64 / 73.98 / 72.05 (without pruning 76.80 / 75.36 / 74.09
/ 72.41); WA 72.81 / 69.46 / 67.33 / 64.32; BiC 73.10 / 68.80 / 66.48 / 62.09; iCaRL 71.14 / 65.27 / 61.20 / 56.08;
bound (joint) about 80.4 to 81.7. Parameters at inference: 2.89M, 4.96M, 7.21M, 10.15M with pruning versus
11.2M for a single ResNet-18 baseline and 285.6M unpruned at 50 steps. Table 2 CIFAR100-B50: DER 74.57 / 72.60 / 72.45
(2/5/10 steps), PODNet 71.30 / 67.25 / 64.04. Table 3: ImageNet-100 B0 top-5 average 92.79, last-step top-1 66.06
(avg top-1 76.12); ImageNet-1000 B0 avg top-1 66.73, last 58.62, versus WA 65.67 / 55.6; ImageNet-100 B50 top-1 avg
77.73 / last 72.06. Backward transfer of the representation +1.36% versus -3.18 to -16.27% for the others; forward
transfer +1.49% (Table 5). Hyperparameters: SGD, batch 128 (CIFAR) or 256 (ImageNet), weight decay 5e-4, 10 warm-up
epochs, 160 epochs (CIFAR) or 120 (ImageNet), lr 0.1; lambda_s = 0.75 for CIFAR100-B0, 0.25 for B50, 0.75 or 0.5 for
ImageNet-100.

**(d) Operations and memory.** One forward pass runs every frozen extractor plus the new one (compute and parameters
grow with steps; pruning keeps the average at 2.89M to 10.15M parameters over 5 to 50 steps instead of 33.6M to
285.6M unpruned on CIFAR). Latency 1.07 ms per image against 0.99 ms for BiC and WA (GTX 1080Ti, ImageNet, from the
appendix). Dense convolutions and a dense linear classifier; plus the exemplar memory (herding selection).

**(e) Limitations.** Needs exemplars (memory 2,000 on CIFAR-100). Inference cost grows with the number of steps. The
paper does not test the exemplar-free case (it only mentions earlier exemplar-free work in related work). The
authors say the second stage (classifier retraining on balanced memory) reaches an "ideal" (classifier trained on all
old data) of 76.14 on CIFAR100-B0 10 steps against 74.64 for DER, i.e. the balanced head is good enough with memory.

**(f) Fit to L.** Gives the structural pattern (frozen old units, new units appended, one joint output) and the
cheap remedy for our selectivity failure: train new nodes with an auxiliary "new versus everything-old" output so
they are pushed to fire on the new class only. Caveat: DER's auxiliary loss uses exemplars of old classes as the
negative class; without exemplars the negative class must come from counted statistics or replay. Concrete small
test: add one extra "not-old" output per new group of nodes and train the new nodes on new-class images as
positives against (a) stored old-class prototypes (a few counted prototypes per old class, not images) and (b) the
old nodes' own responses as negatives; measure the firing rate of the new nodes on held-out old-class images before
and after (baseline: our current number). Result is compared against the DER ablation size: +2.1 average points from
the auxiliary loss, expansion itself +11.4.

## 4. FOSTER (chosen over MEMO), Wang, Zhou, Ye, Zhan, arXiv 2204.04662

**(a) Mechanism.** Two stages per step. Boosting: freeze the old model F_{t-1} (extractor Phi_{t-1} plus classifier);
create a new trainable extractor phi_t, concatenate features, and a new linear layer W_t = [[W_{t-1}, W_t^(o)],[O,
W_t^(n)]] (O set to zero). Old classes' logits = old logits + W^(o) phi_t(x) (the new module fits the residual), new
classes' logits = W^(n) phi_t(x). Losses: logits alignment (LA) - the old logits are scaled by gamma_1 and the new
by gamma_2 with 0 < gamma_1 < 1 < gamma_2, computed from the "effective number" E_n = (1 - beta^n)/(1 - beta) of old
and new samples (beta = 0.95 on CIFAR-100, 0.97 on ImageNet); feature enhancement (FE) - an extra classifier on the
new feature alone over all seen classes (cross entropy L_FE) plus distillation L_KD from the old model's output
distribution to the expanded model's old-class distribution; L_Boosting = L_LA + L_FE + L_KD. Compression: distil
the dual-branch model into a single backbone with balanced distillation (class-weighted by E_n, beta 0.97,
temperature 2) on the (imbalanced) current data D_t plus memory; unlabeled external data optional (not used). The
model size is thus constant over steps. Decision between old and new: one softmax over all classes, with the bias
between old and new logits corrected during training by LA (not by a gate, not by a detector).

**(b) Decision needs and accuracy.** Needs exemplars (the imbalanced set D_t plus V_t) and the E_n counts. The
old-versus-new calibration is evaluated indirectly only: LA versus post-hoc weight alignment (WA): LA is "about 4%"
higher in the last-step accuracy (Fig. 5a, reading from the plot description; value not tabulated). Feature
enhancement removal costs "more than 3%" in the last step, with more than 4% lost on old classes and essentially no
change on new classes (text of Sec. 5.3).

**(c) Results.** Protocol: **class-incremental with exemplars**. Table 1 average accuracy on CIFAR-100 (single
backbone kept; DER keeps one backbone per step): B0 10 steps 72.90 (DER 69.74, WA 67.08), B0 20 steps 70.65 (DER
67.98), B50 10 steps 67.95 (DER 66.36), B50 25 steps 63.83. Table 2: ImageNet-100 B0 20 steps 74.49 (DER 73.79), B50
10 steps 77.54 (DER 77.73, i.e. -0.19), B50 25 steps 69.34; ImageNet-1000 10 steps 68.34 (DER 66.73, WA 54.10). Note
the DER numbers in FOSTER's tables (69.74 at CIFAR B0 10 steps) differ from DER's own paper (74.64) because the
backbones differ (modified ResNet-32 here versus ResNet-18 in DER's paper); compare methods only within a table.
Exemplars (CIFAR-100 B50, 5 steps, Fig. 6b): last-step accuracy rises from 53.53% (5 exemplars per class) to 71.4%
(200 per class); above 60% with 10 per class. Robust to beta in 0.93 to 0.999 (small changes). Optimiser: SGD
momentum 0.9, lr 0.1 cosine, 170 epochs, batch 128 (CIFAR) / 256 (ImageNet), weight decay 5e-4 (boosting).

**(d) Operations and memory.** Training cost is higher than single-backbone methods (two networks in boosting plus a
distillation stage; no measured time in the text I read: UNVERIFIED). Inference cost and memory are those of one
backbone after compression (the advantage over DER). Dense convolutions and softmax.

**(e) Limitations.** Needs exemplars (2,000 total or 20 per class); the authors say the performance depends on
their number. The effective-number weights assume known sample counts per class. The compression gap to the dual
branch ("FOSTER B4") is small but non-zero (Fig. 3 and 4, values not in text). Not exemplar-free: the exemplar-free
setting is not evaluated.

**Supplementary material (read, in the same PDF).** (i) The step from "sum of softmaxes" to "softmax of summed
logits" is justified because the sum of two softmax outputs can reach 2 (0 <= p_o + p_n <= 2), while the softmax of the
sum stays in [0,1]; KL divergence is chosen over a Euclidean distance for faster optimisation and better features.
(ii) Initialisation of O (old model's output on new classes), CIFAR-100 B50 5 steps (Fig. 1, plot only): fine-tuned O
(FT) is slightly better than all-zero (AZ) and all-zero with learned bias (AZB); AZ and AZB are almost equal, so a
learned old/new bias adds little. (iii) DER is a special case of the boosting model: make O trainable and drop
feature enhancement and logits alignment. (iv) Baseline descriptions: Fine-tune (old classifier rows frozen), Replay
(herding), iCaRL (NME classifier), BiC (bias-correction layer with alpha and beta estimated on a small validation
set), WA (aligns the norm of new-class weight vectors to old ones), PODNet, DER. (v) Confusion matrices at the last
step of CIFAR-100 B50 5 steps (Fig. 3, plots, qualitative): fine-tune classifies almost everything as a new class
(strong new-class bias), iCaRL still has bright new-class columns, WA removes the bias but old-class diagonal
entries are only about 0.2 to 0.4, DER is good but a residual bias to new classes remains, FOSTER is balanced. This
is the nearest thing in these four papers to our failure (inputs from old classes being taken by new units).
(vi) t-SNE: fine-tuning scatters features, FOSTER keeps clusters.

**(f) Fit to L.** The useful part is logits alignment: an explicit old-versus-new bias correction between the
frozen-old and new scores, computed from sample counts only (effective number E_n). In the paper the two
factors satisfy 0 < gamma_1 < 1 < gamma_2 (old scaled down, new scaled up during training, so the network is pushed
to produce larger old logits); the exact normalisation of gamma from E_old and E_new as printed in the extracted
text is garbled (UNVERIFIED), so do not copy it; use a free ratio. Concrete small test: after adding a new group of
nodes, multiply old-group scores by a and new-group scores by b (a power-of-two ratio, so a shift, no multiplier),
sweep a/b over a small grid, and plot old-class accuracy versus new-class accuracy. If one constant ratio restores
old accuracy without a gate, the bias is calibration; if no ratio works, the new nodes are non-selective and a gate
(paper 2) or a not-old output (paper 3) is needed. Compare with the supplement's finding that a learned bias (AZB)
adds almost nothing once training is aligned.

## What these methods say about the old-versus-new decision

| Paper | Setting | Old-vs-new decision made by | Needs old data | Reported quality of that decision |
|---|---|---|---|---|
| NDL | reconstruction only | none at inference; RE threshold at training | no (uses class statistics for replay) | not reported |
| Expert Gate | task-incremental, dataset-level tasks | one autoencoder gate per task, lowest reconstruction error | no | 97.6% (6 tasks), 99.2% (3 tasks); confident-expert baseline avg 48.7 vs 67.3 |
| DER | class-incremental | one softmax over all classes; auxiliary "other" output for new extractor | yes (memory) | not reported; auxiliary loss +2.10 avg |
| FOSTER | class-incremental | one softmax; logits alignment by counts | yes (memory) | LA about 4% above weight alignment (plot only) |

Reading: only Expert Gate makes the decision an explicit, measured, data-free component and it works at about 97.6%
when the tasks are different datasets on top of a strong fixed feature extractor. The two class-incremental methods
avoid the decision by training one joint classifier and need exemplars. NDL says nothing about it.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
