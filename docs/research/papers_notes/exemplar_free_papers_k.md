---
title: Paper notes - sparse associative memories and incremental learning in weightless networks
tags: [l, research, papers]
---

# Paper notes - sparse associative memories and incremental learning in weightless networks

Read from the arXiv PDF text (pdftotext, 25 Oct 2026). Numbers are quoted as printed and are **REPORTED by the authors, not reproduced by us**. "DERIVED" = our arithmetic. "UNVERIFIED" = not found in the text we read. The arXiv ids were checked by search of the arXiv API before download.

Papers (id, role):
1. **SDM-CL**: Bricken, Davies, Singh, Krotov, Kreiman, "Sparse Distributed Memory is a Continual Learner", ICLR 2023, arXiv **2303.11934**. Main paper; the cerebellum-inspired sparse associative memory (request 1 and, for the cerebellum, request 4).
2. **FlyModel**: Shen, Dasgupta, Navlakha, "Algorithmic insights on continual learning from fruit flies", arXiv **2107.07617**. Read in full (main text, methods, perceptron variants); its Supplement (Lemmas 2-4, Theorems 5, 8, 9) is **not in the PDF**, so the proofs are UNVERIFIED and only the statements in the main text are used. It is the sparse-expansion circuit that SDM-CL compares against and wins/loses to (request 4, expansion circuit; it is also touched by [forgetting_free_adaptation_papers.md](forgetting_free_adaptation_papers.md), here read for the mechanism and the ablations).
3. **CLS-VAE+MHN** (request 2, the paper picked): Jun, Marupudi, Shah, Varma, "A Neural Network Model of Complementary Learning Systems: Pattern Separation and Completion for Continual Learning", arXiv **2507.11393**. A short CogSci-style paper (a snippet was in [continual_and_benchmark_papers.md](continual_and_benchmark_papers.md); now read in full).
4. **HiCL** (request 4, dentate gyrus; also a hippocampal dual-memory design): Kapoor, Mackey, Aloimonos, Lin, "HiCL: Hippocampal-Inspired Continual Learning", arXiv **2508.16651** (v3, AAAI 2026 version).
5. **TM-FPGA** (request 3): Prescott, Wheeldon, Shafik, Rahman, Yakovlev, Granmo, "An FPGA Architecture for Online Learning using the Tsetlin Machine", arXiv **2306.01027**. Note: the earlier note called this "AdaTM"; the paper itself has no such name.

No paper found by search for: a cerebellum-specific continual-learning paper other than SDM-CL; a WiSARD/RAM-neuron continual-learning paper on arXiv (searches "WiSARD incremental", "weightless neural continual" returned only an AI-education paper, a recommender short paper 2511.05499 and TsetlinWiSARD 2603.24186, which is on-chip training, not class-incremental; 2511.05499 was only skimmed, UNVERIFIED for anything beyond "per-user online table-lookup learning on MovieLens").

## 0. Bottom line for L (read this first)

1. **What sparse associative memories store without interference.** If every class writes only into the few units that its own sparse code switches on, and *only to its own output counter*, then different classes interfere exactly in proportion to the **overlap of their active sets**. FlyModel makes this explicit: the weight vector of a class converges to the (scaled) mean of its sparse codes, and a write for class j never touches another class's counters. This is **additive, counter-style storage with no read-modify-write of other classes** (FlyModel Eq. 3; SDM Eq. 1-2 for the original SDM).
2. **What destroys it.** (a) Dense codes: FlyModel dense-coding variants ended at 0.07 accuracy vs 0.64 for sparse ones on MNIST-20. (b) Error-driven updates that *decrease* the counters of the wrongly predicted class (perceptron v1/v3): shared units get "hijacked" by the most recent class. (c) Learned addresses without competition: SDM-CL's ablations show that removing L2 normalisation, or allowing bias terms, or using Adam/RMSProp drops Split-CIFAR10 class-incremental accuracy from 0.63 to 0.20-0.23 (the same as a ReLU MLP, 0.21). (d) Dead or "greedy" units that win for every input.
3. **How it scales.** Not one clean capacity law is given by any paper. What is measured: with more units, the fixed-random FlyModel scales strongly (Split-CIFAR100, 50 tasks: 0.36 at 1K units, 0.58 at 10K; Split-MNIST 0.77 -> 0.91), the learned SDMLP does not (Split-MNIST 0.53 at 10K vs 0.69 at 1K with k=1). Accuracy falls with the number of classes (FlyModel MNIST-20: 0.86 at 10 classes, about 0.75 at 20 classes (end of training); SDM-CL Split-CIFAR100 oracle 0.72 vs best continual 0.58).
4. **For L (matrix-free counting chip).** The FlyModel is, structurally, L's design: a fixed sparse binary code (sparse random binary expansion + top-l winner-take-all), a table of integer counters, class write = add to the counters of active units of **one** class, read = sum counters over active units, argmax. No multiply is needed if the code is binary (the FlyModel's min-max normalised real values can be replaced by 1). The papers support: keep the code **fixed**, keep each class's counters **independent**, make the code **sparse and wide**, write **regardless of mistakes** (associative, not error-driven), never subtract from other classes.
5. **What the papers do not give us**: any result on a class count above 100 with sparse binary codes, any result with raw pixels or hand-built binary codes (FlyModel and SDM-CL both rely on a frozen deep encoder: ConvMixer / LeNet5 / ResNet18 features), any capacity formula for counter saturation, and any Fashion-MNIST result with a binary code. The only Fashion-MNIST data are SDM-CL Table 8 (pixels, 3 seeds): FlyModel 10K units 0.76 vs oracle 0.90.

## 1. SDM-CL (arXiv 2303.11934)

### (a) Mechanism, exactly
**Original (continuous) SDM** (Section 3, Eq. 1-2). r "neurons" with fixed unit-norm addresses X_a (n x r) and storage vectors X_v (o x r). Patterns have addresses P_a and values P_v. Write: X_v = P_v b(P_a^T X_a), b(e)=1 if e>=c else 0 (cosine threshold c), i.e. **each pattern adds its value into the storage vector of every neuron within cosine similarity c** (elementwise sum = superposition). Read: y = X_v b(X_a^T xi), i.e. the active neurons' storage vectors are summed. For classification the written value is the one-hot label. Interference arises when two patterns activate the same neuron; fidelity "is a function of vector orthogonality and dimensionality n".

**SDMLP** (Section 4) turns this into an MLP trained by backprop with SGD:
- one hidden layer (1,000 neurons, or 10,000), **Top-K activation** a* = [a - I]+, with I the (k_t+1)-th largest of [a]+ (Eq. 4): the k winners stay on, **reduced by the (k+1)-th activation** (the "inhibitory interneuron"; this beats zeroing losers: "Linear Mask" 0.38 vs "Linear Subtract" 0.63);
- **k annealing as a GABA switch**: k_t = max(k_target, floor(k_max - E_t (k_max - k_target)/s_c)); start with k_max = all neurons so every neuron learns onto the data manifold, then shrink to k_target (10, also 1). Without annealing: 0.35 ("No Linear Anneal");
- **no bias terms** (hidden or output), **non-negative weights**, **L2-normalised inputs and neuron addresses** after every step (Algorithm 1: x/||x||, activations, Top-K, output, gradient step, clamp to >=0, renormalise X_a);
- **SGD without momentum**: Adam 0.23, RMSProp 0.20, SGD+momentum 0.54, SGD 0.63. Cause named "stale momentum": momentum optimisers keep updating inactive neurons from an out-of-date moving average and explode gradients when a neuron wakes up (App. D).
- Output layer X_v is reset after ImageNet pretraining; the class write is then a cross-entropy gradient step on X_v rows of the k active neurons only (App. A.6: equivalent in spirit to SDM's "add the one-hot value").

**Interference avoidance**: "a new learning task only activates and trains a small subset of neurons, leaving the rest intact" (Top-K restricts which units update; L2 norm + no bias force all neurons onto the data manifold so they tile it democratically; bias or a large norm make a few "greedy" neurons win for every input, App. H).

**Cerebellar mapping** (App. A.2): mossy fibres = input; granule cells = neurons, dendrites = address; parallel fibre contact with Purkinje cell = storage counter; climbing fibre = write signal; Golgi cell = Top-K inhibition. Cerebellum biological claims are partly UNVERIFIED by the authors themselves ("additional neuroscientific evidence required").

### (b) Results, protocol, ablations
Protocol: **class-incremental** (no task id at test; a prediction over all 10 classes), Split-CIFAR10 as 5 splits of 2 classes, 2,000 epochs per split (to induce forgetting), 5 random class splits, no replay, no task labels. Input: 256-d ConvMixer embeddings (frozen, trained on ImageNet32) + SDMLP pretrained on ImageNet32 (this is where the GABA switch happens), 300 epochs.

Table 1 (10K neurons, final validation accuracy, average of 5): SDMLP k=10 **0.71**; FlyModel k=32 **0.82**; MAS 0.67; SI 0.44; ReLU MLP 0.21; EWC 0.65; SDMLP+MAS 0.84; SDMLP+EWC **0.86**; oracle (joint training) 0.93. 1K neurons (Table 5): SDMLP k=1 0.70, k=10 0.63; Top-K without the SDM changes 0.29; FlyModel (k=64) 0.70; MAS 0.69; EWC 0.67; SI 0.34; NISPA 0.19; L2 0.23; Dropout 0.21; SDMLP+EWC 0.83; SDMLP+MAS 0.83; oracle 0.93.

Ablations of SDMLP (Table 2, 1K neurons, k=10; base = 0.63): SGDM 0.54; Adam 0.23; RMSProp 0.20; Linear Mask 0.38; No Linear Anneal 0.35; Negative Weights allowed 0.57; No L2 Norm 0.20; Hidden-layer bias 0.20; Output-layer bias 0.20. The authors state that every component is necessary.

Other datasets and settings (all class-incremental, 1K/10K neurons):
- Split-CIFAR100, 50 splits (Table 6): SDMLP 1K k=1 0.32, k=10 0.39; Top-K 0.11; FlyModel 1K 0.36; MAS 0.24; EWC 0.12; SDMLP+EWC 0.42; 10K: SDMLP 0.43, FlyModel **0.58**, MAS 0.40, EWC 0.16, SDMLP+EWC 0.51; oracle 0.72.
- Split-MNIST on raw pixels, no pretraining (Table 7): SDMLP 1K k=1 0.69, k=10 0.53; 10K k=10 0.53; FlyModel 1K 0.77, 10K 0.91; EWC 0.61/0.67; MAS 0.49/0.58; SI 0.36; NISPA 0.40; Active Dendrites 0.20; ReLU 0.21; SDMLP+EWC 0.83/0.86; oracle 0.98/0.99. The 10K SDMLP+EWC model was still learning the last task: "the model has run out of new neurons to avoid overwriting" is offered as a possible reason (capacity signal, not a measured law).
- Split-Fashion-MNIST on raw pixels (Table 8): SDMLP 1K k=1 **0.73**, k=10 0.53, 10K k=10 0.52; FlyModel 1K 0.67, 10K 0.76; EWC 0.68/0.72; MAS 0.33/0.34; Top-K 0.23; ReLU 0.21; SDMLP+EWC 0.74/0.72; oracle 0.90.
- No ConvMixer (pixels, 3,072-d; Table 3): SDMLP 1K k=1 0.33, 10K 0.42; EWC 0.19; SDMLP+EWC 1K 0.28, 10K 0.32 (did not finish); oracle 0.53. FlyModel not run (needs embeddings).
- No ImageNet pretraining (Table 4): SDMLP 1K k=1 0.56, 10K 0.77; FlyModel 1K 0.69, 10K 0.82; SDMLP+EWC 10K **0.84**; oracle 0.93. "1K neuron models lack capacity to learn the data manifold of new tasks without pretraining."

**Sparsity level (k) and capacity** (App. C.2, Fig. 13-14, text only; the curves themselves were not extractable): larger k gives better pretraining (non-continual) accuracy but worse continual accuracy and vice versa; the best k depends on the manifold and on r. With 10K neurons k=5 beat all k<=50 for continual learning, and k=1 was worst for pretraining but second best for continual; on raw pixels (1K) k=10 was best for pretraining and k=1 best for continual. Joint training with a CNN needs k>=250 to match a ReLU net, and with ImageNet32 even k=2,500 of 10,000 was too small. Sparse activations make the network "wider rather than less active": the authors' proposed fix for the sparsity/capacity trade-off is a larger r, not a larger k.

### (c) Operations and memory
Dense hidden layer 256 x r with a full matrix-vector product and a sort to find the top k (the authors admit "computing the k most active neurons requires multiplying the input with each neuron and then sorting"), then only k rows of X_v are read and updated. Weights are real-valued and only about 20% are zero. FLOPs and bytes are not tabulated: UNVERIFIED. Training is backprop (not on-chip friendly); 2,000 epochs per split.

### (d) Limitations (as stated and observed)
Needs a **static data manifold** (a frozen encoder); joint training with a CNN gave many dead neurons. k_target and the annealing length s are data dependent and "difficult". Sparse subnetworks cost non-continual accuracy. Weight pruning of the pretrained model caused catastrophic forgetting. At 10K neurons the learned SDMLP is *worse* than the fixed random FlyModel on CIFAR10, CIFAR100, MNIST and Fashion-MNIST, i.e. learning the addresses buys little over a fixed random expansion once r is large. EWC combination needs task boundaries.

### (e) Fit to L and one small test
Fit: partial. The **write/read** is the L pattern (sparse set of active units adds into per-class counters; read = sum), but the **trained, real-valued, normalised, backprop** machinery is exactly what L cannot use. The usable lessons: (1) a code must tile the data manifold, i.e. every unit must be used; "dead" or always-on units kill continual performance; (2) no biases or per-unit offsets that favour recently written classes (the output-layer bias ablation: the model "assigns large bias values to the classes within the current task"); (3) smaller k = less forgetting, larger k = better accuracy: k is a knob to sweep.
Test: take L's fixed sparse code and its integer class counters, sweep the active-set size k (for example 1, 5, 10, 32 per 1,000 units) on class-incremental Split Fashion-MNIST (2 classes per task) and report final accuracy and a dead/over-used unit histogram; check that no per-class bias or running normaliser is present. Pass: forgetting is monotone in k (as in SDM-CL C.2) and the histogram shows no unit active for more than about 10% of inputs.

## 2. FlyModel (arXiv 2107.07617)

### (a) Mechanism, exactly (Eq. 1-3)
Input x in R^d (a frozen-encoder feature vector: 84-d LeNet5 features for MNIST-20, 512-d ResNet18 features for CIFAR-100). Layer 1 (no trainable parameters): psi(x) = Theta x, with Theta a **sparse binary random** m x d matrix, m about 40d, each KC samples about 0.1 d inputs (10 of 84; 64 of 512); winner-take-all keeps the l largest positive entries (l = m/k_classes: l=160 for MNIST-20, 200 for CIFAR-100; the fly uses 5%), others 0; min-max normalised to [0,1] to give phi(x). Layer 2: weights w_ij in [0,1] from KC i to class unit j. **Update for a sample of class j: w_ij <- (1-alpha) w_ij + beta phi_i for the target j only; other classes' weights only decay by (1-alpha)**; alpha=0 in all experiments; weights capped to [0,1]. Learning rate beta 0.01 (MNIST-20), 0.2 (CIFAR-100). Prediction: argmax_j w_j . phi(x). One pass over the data. Called "partial freezing": only synapses between active KCs and the target MBON change.

### (b) Results
Protocol: **class-incremental** (test on all classes seen so far), one epoch. MNIST-20 (MNIST + Fashion-MNIST, 20 classes) as 10 tasks of 2 classes; CIFAR-100 as 25 tasks of 4 classes; 5 initialisations. m = 3200 and 20000 units. After 5 tasks (10 classes) on MNIST-20: FlyModel **0.86 +- 0.0006**, BI-R 0.77, GEM 0.69, EWC 0.58, vanilla 0.19. At the end (20 classes) FlyModel is at least 0.19 above any other method and 0.11 below the offline network (end-of-training FlyModel value of about 0.75 is implied by the ablation text "0.75 vs 0.54"). CIFAR-100: at least 0.15 above all continual methods, 0.13 below offline; the ablation text gives 0.41 for FlyModel vs 0.21 for sparse+logistic regression. Memory loss averaged over tasks: FlyModel 0.07, GEM 0.24, EWC 0.27, BI-R 0.42, vanilla about 1.
**Ablations (Fig. 3-4)**: dense vs sparse code and partial freezing vs logistic regression: sparse variants averaged 0.64 vs 0.07 for dense on MNIST-20; sparse+freezing 0.75 vs sparse+logistic 0.54 (MNIST-20) and 0.41 vs 0.21 (CIFAR-100). Perceptron variants: v1 (classic; update only on mistakes, +target, -predicted), v2 (mistakes only, +target only), v3 (always +target, -predicted on mistake), v4 = FlyModel (always +target, never minus). Result: learning regardless of mistakes (v3, v4) beats mistake-only (v1, v2); decreasing the wrong class's weights hurts (v4 > v3). Reason (Lemma 2, UNVERIFIED proof): two similar inputs with different classes share units; the minus update moves shared synapses to the latest class ("hijacked"); in the FlyModel shared units are "split" between classes and cancel out, which matters most for similar classes (3 vs 5 worse than 3 vs 4, Fig. S3).
**Theory (statements only)**: class weight vectors converge to the class mean scaled by a constant (Lemmas 3-4, Theorems 5, 8); if classes are gamma-separated (E[x_o.X] >= gamma + E[x_o.X'] across classes) the mean classifier is perfect even with O(gamma)-accurate means; sparse coding with prototypes of cosine <= xi gives separation 1/N_o - f(xi) (Theorem 2), where N_o is the largest number of prototypes in a class and f shrinks dot products (about (k/m)^(1-s) for a dense Gaussian map).

### (c) Operations and memory
Layer 1: sparse binary Theta, about 0.1d adds per unit (no multiply apart from the real-valued inputs), then a top-l selection over m; layer 2: l additions per class unit at inference (sum of l counters), l counter increments per write. Weights are in [0,1] (precision not stated; an integer version is an obvious change, UNVERIFIED). Memory m x k_classes weights (3200 x 20 = 64K; 20000 x 100 = 2M).

### (d) Limitations
Needs a good frozen encoder ("pre-processing is essential when the original data are not well separated"). With alpha=0 weights only grow; the authors report no saturation over tens of thousands of steps but say "some small alpha may be desired" (saturation is untested). No forward or backward transfer. Capacity versus number of classes is only seen through the 10 -> 20 and 25-task curves.

### (e) Fit to L and the small test
Fit: **high**. It is the L Cortex mechanism with one real-valued normalisation to remove. Test: in the L simulator, run the four perceptron variants as counter rules over L's own sparse code on class-incremental Split Fashion-MNIST (5 tasks x 2 classes): v4 (add to target only, always), v3 (add to target, subtract from predicted on a mistake), v2, v1. Expected from this paper: v4 best on forgetting, largest gap on similar pairs (shirt/T-shirt, pullover/coat). Also report the average memory loss of the paper's definition (accuracy of task i right after learning minus at the end).

## 3. CLS-VAE+MHN (arXiv 2507.11393), complementary learning systems

### (a) Mechanism
Hippocampus = a **Modern Hopfield Network (MHN)** storing a few latent codes; neocortex = a **VAE** (encoder-decoder, latent size 48 chosen). Training: task 1 (digits 0/1) on real images only. At the end of task 1 about 5% of the images (about 600) have their VAE **latent vectors stored in the MHN**. In every later task the VAE trains on new data plus **replayed samples**: a random noise vector is the retrieval cue, the MHN settles recurrently (energy minimisation, large inverse temperature beta so that single memories are recalled), and the settled latent is decoded by the VAE decoder; replay ratio 1:1 with new data. Loss = BCE reconstruction + KL, summed over current and replayed samples, backprop; 10 epochs, batch 32, lr 1e-3. Evaluation: a **separate MLP classifier** (97.58% on MNIST) labels the VAE's reconstructions, so the reported "accuracy" is the classifier's agreement with the label of the reconstructed image, not a classification head of the model itself.

### (b) Results
Protocol: **class-incremental Split-MNIST** (5 tasks x 2 classes), 5 repeats. Table 1 (via the MLP): VAE upper bound (all 10 classes offline) **95.55%**; untrained VAE 8.92%; sequential VAE with no replay (control) 67.75%; **VAE+MHN 89.71%** (the best configuration reached 91.01%). Hyperparameter study (Fig. 3, text only): storing the latent layer beats storing the fully connected layer, higher latent dimension better, replay ratio is quadratic with an optimum near 1:1. Pattern separation (mean intra-class Euclidean distance, 128 held-out images per class): MHN larger than VAE latent, UB VAE and control for all 10 classes (Bonferroni p<0.001, 30 comparisons). Pattern completion (SSIM of reconstructions after a 10x10 centre occlusion): VAE latent close to UB, MHN lower (p<0.001). Exact distance/SSIM values are in figures only (UNVERIFIED).
No ablation on the sparsity of the stored codes or on the number of stored items; the 5% buffer is the only capacity number. The "sparse" in "sparser scattered representations" refers to t-SNE spread, not to binary sparse codes.

### (c) Operations and memory
Needs a VAE (matrix multiplies, backprop, KL), a latent store of about 600 vectors x 48 floats (DERIVED about 29K floats), recurrent MHN settling for each replay sample. No FLOP numbers: UNVERIFIED.

### (d) Limitations
Split-MNIST only; the metric is indirect; replay requires training a generator at every step (backprop); stored items are real latent vectors (an exemplar-like memory, 5% of data, so not exemplar-free in the strict sense); only 10 classes; the authors list missing brain structures and no scaling test.

### (e) Fit to L
Low as a design, useful as a design rule: a **fast, sparse, separating store** (MHN, large beta, one memory per recall) next to a **slow, generalising store**. For L: counters give the fast store; a frozen shared code gives the slow one; replay is not available on chip. The only transferable test: measure intra-class vs inter-class **Jaccard overlap of L's active sets** (see HiCL) before and after each new class and check that overlap between old and new classes stays low.

## 4. HiCL (arXiv 2508.16651), dentate-gyrus pattern separation

### (a) Mechanism
A CNN backbone (LeNet-style: 2 conv + 2 FC for CIFAR-10; 4 conv 64-128-256-512 + 2 FC for TinyImageNet) gives features f. Grid-cell layer: g_m = sin(W_m f + phi_m), m=1..4 (1x1 convs with learned phases). **Dentate gyrus**: z = ReLU(W_DG g + b_DG), p_sep = TopK(LayerNorm(z), k), k = floor(0.05 dim(z)), DG size 1024 (so k=51). CA3 = two-layer MLP p_comp = LN(ReLU(W2 ReLU(W1 p_sep + b1) + b2)) (widths 512, 256); CA1 integrates u = [p_sep ; p_comp] (widths 512, 256, 128). **One expert (own DG, CA3, CA1) per task** (N = 5 on CIFAR-10, 10 on TinyImageNet). Each expert keeps a prototype u_i updated by EMA of its DG code, u_i <- (1-mu) u_i + mu p_sep^(i), mu=0.01. Inference routing: s_i = cos(p_sep^(i), u_i); soft (softmax(s/tau)), hard (argmax), top-2 or hybrid gating; the code is computed by **all N DG modules** in parallel, then only the chosen expert's CA3/CA1 runs. Training in two phases: Phase I loss L = L_cls + a_intra L_intra (push-pull on codes, margin) + a_dist L_distill + a_s L_sparsity, plus replay (200 samples per task) and EWC (lambda 0.1); Phase II freezes non-DG parameters and applies a prototype contrastive loss L = 1 - cos(p_sep^(t), u_t) + sum_{j != t} max(0, cos(p_sep^(j), u_j) - m), margin m=0.2. Adam, 10 epochs per CIFAR-10 task (20 for TinyImageNet).

### (b) Results
Protocol: training uses task identity ("we follow the task-incremental protocol"); evaluation reports **both Task-IL and Class-IL**; Class-IL inference is label-free through the DG routing. Buffer 200 or 500 per task. Split-CIFAR10 (5 tasks) and Split-TinyImageNet (10 tasks x 20 classes). Table 3 ablation (CIFAR-10, replay 200): full HiCL **92.67 Task-IL / 57.99 Class-IL**; without contrastive 91.56 / 19.19; without DG gating 91.82 / 18.39; **without top-k sparsity 55.85 Task-IL** (Class-IL value cannot be aligned to the row in the extracted text, UNVERIFIED); the remaining rows (w/o CA1, EMA, CA3, EWC) have Task-IL 92.64, 90.63, 92.29, 89.48 and Class-IL 30.71, 52.39, 56.29, 58.73, 58.92 in text order (row assignment UNVERIFIED because the table text is scrambled). Table 2 (buffer 100, 200, 300, 400, 500, 600, 1000, 5000; column order read from the text, UNVERIFIED alignment): Task-IL 90.1, 92.6, 91.5, 92.2, 92.8, 91.3, 92.5, 92.8; Class-IL 53.4, 60.6, 63.1, 64.2, 65.4, 64.6, 67.2, 63.7; routing accuracy 56.0, 63.2, 65.6, 67.7, 67.8, 67.6, 69.1, 64.1. (Class-IL at buffer 200 is 60.6 here vs 57.99 in Table 3, so the tables are not fully consistent.) Table 1 compares with SGD, LwF, SI, A-GEM, ER, DER++, iCaRL, FDR, HAL, E2Net, SparCL; the extraction of Table 1 is column-scrambled, so the HiCL rows are only read as "HiCL Small (sparsity 0.15) / Large, about 57-63 Class-IL class on CIFAR-10 at 38 and 84 MFLOPs"; the exact cell assignment is **UNVERIFIED**. Joint upper bounds 90.24-92.38 (CIFAR-10).
Pattern separation evidence: Jaccard overlap of DG codes is much lower between tasks than within tasks (Fig. 3, values only in the figure). FLOPs: Small 16.3 MFLOPs per inference (10.81 backbone + 5.48 expert) on CIFAR-10; Large 49.7; TinyImageNet 49.1 / 172.7.

### (c) Operations and memory
Backbone convolutions + dense DG projection + top-k selection + N DG passes for routing + replay buffer + EWC Fisher. Not matrix-free.

### (d) Limitations (stated)
Needs task boundaries/labels in training; hyperparameters (rho=0.05, N experts = N tasks) may not generalise; under 5% of samples confused by overlapping DG codes; small vision backbones only. Our reading: **one expert per task is a growing model**, the Class-IL numbers (about 58 on CIFAR-10, versus Task-IL 92.7) show routing, not classification, is the bottleneck, and the gate was **not** separately benchmarked against a plain nearest-prototype rule (UNVERIFIED).

### (e) Fit to L and the test
Mixed: the *signal* is relevant (top-k sparsity is essential: Task-IL falls to 55.85 without it; separation shows as low Jaccard overlap between tasks) but the architecture is dense and replay-based. The routing step (cosine of a sparse code to a running EMA prototype) is a **counting operation if the code is binary**: overlap count with each class's prototype set. Test: with L's binary codes, route each test sample to the class whose accumulated counter profile has the largest overlap, and compare with the SDM/FlyModel sum read; report routing accuracy per task and the Jaccard overlap histogram intra- vs inter-task for sparsity 1%, 3%, 5%, 15%.

## 5. TM-FPGA (arXiv 2306.01027), Tsetlin machine online learning

### (a) Mechanism
A standard Tsetlin machine (clauses = AND of Boolean literals and complements; half vote +, half vote -; majority vote; Tsetlin automata teams; hyperparameters T and s) implemented on an FPGA (Zybo Z7-20) with over-provisioned **classes and clauses** (unused classes/clauses are clock-gated and enabled at run time), run-time control of s and T through a microcontroller, accuracy-analysis block, cross-validation block memories, and a fault-injection layer (AND/OR gates forcing TA outputs). Online learning = continue to apply TM feedback on new labelled rows while inferring. A new class is "introduced" by training the over-provisioned class on its data. No new learning rule.

### (b) Results (iris only, Boolean 16 inputs, 3 classes, 150 samples)
Settings: 16 clauses, s = 1.375 offline / 1 online, T = 15, 10 offline iterations, averaged over 120 data orderings. Offline 20-30 samples, validation 60, online 60 (block sizes 30). Limited initial data: offline start accuracies 83% (offline set), 79.5% (validation), 79.5% (online set); after 16 online passes validation and online set rose about **12%**, the offline set about **5%**; authors note possible forgetting of old data (smaller gain on the offline set) and suggest replay. **Unseen class**: class 0 withheld offline and at first online (starting accuracies 75.75 / 79.66 / 79.66); without online learning, introducing it after 5 online iterations dropped accuracy (Figure 6 y-axis spans to about -26 points, exact values figure-only); with online learning accuracy dipped briefly and recovered ("significantly positive outcome"). Fault test: 20% of TAs stuck at 0: without online learning accuracy fell (up to about -8 in the plotted range); with it recovered to roughly the fault-free gain. Hardware: inference and feedback for all clauses in 2 clock cycles, one data point per clock; estimated power 1.725 W of which 1.4 W is the microcontroller (tool default activity; ESTIMATED).

### (c) Operations and memory
Clause logic and automata state counters; the number of automaton states is a design parameter (value not stated in the text read: UNVERIFIED). No memory total given.

### (d) Limitations
Iris (150 points); "one new class added to a 3-class model" is the only incremental protocol; accuracy plots only; no old-class retention measurement per class, no comparison to any baseline, no class-incremental benchmark; the oscillation of results is blamed on the dataset size. The paper does not show that a TM does not forget; it shows it re-learns quickly. UNVERIFIED whether any other TM paper measures forgetting (we did not find one on arXiv).

### (e) Fit to L
Low evidence, but it points at a **hardware pattern to copy**: reserve unused class rows (counter banks) in the silicon and enable them when a new class appears; log accuracy periodically to trigger action. Test: in the L RTL simulation, reserve R spare class rows, add a never-seen class from labelled samples only into its row, and measure that the **old classes' accuracy is unchanged to the bit** (a stronger claim than this paper's). That is the "no interference by construction" property that this paper cannot show for a TM.

## 6. Synthesis for L

| Question | Evidence |
|---|---|
| Interference-free storage | Per-class counters written only on a class's own active set (FlyModel); interference proportional to active-set overlap (FlyModel Theorem 2 statement; SDM superposition) |
| Why dense codes fail | FlyModel dense variants 0.07 vs sparse 0.64 (MNIST-20 end); SDM-CL ReLU MLP 0.21 |
| Do not do | Subtract from the wrong class; per-class biases; momentum-like state; unit-specific offsets |
| Sparsity trade-off | SDM-CL C.2: smaller k = less forgetting, worse non-continual accuracy; wider r instead of larger k |
| Scaling with units | FlyModel 10x units: +0.22 (CIFAR-100: 0.36 -> 0.58), +0.14 (MNIST: 0.77 -> 0.91); learned SDMLP does not improve (0.69 -> 0.53 on Split-MNIST, 1K k=1 vs 10K k=10) |
| Scaling with classes | FlyModel 0.86 at 10 classes -> about 0.75 at 20; CIFAR-100 50 tasks: best 0.58 vs oracle 0.72 |
| Needs a good code | Every result uses a frozen deep encoder; raw pixels cost accuracy (SDM-CL pixel CIFAR10 0.42 vs oracle 0.53) |
| Hardware reserve-a-row | TM-FPGA over-provisioned classes |

Concrete test priority: (1) FlyModel perceptron-variant ablation on L's code (Section 2e); (2) k sweep with unit-usage histogram (Section 1e); (3) Jaccard overlap and overlap-count routing (Section 4e); (4) spare-class-row bit-exactness (Section 5e). Labels for any result produced from these will be SIMULATED or MEASURED by L's own regression, not by the papers above.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
