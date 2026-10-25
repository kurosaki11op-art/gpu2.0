---
title: Paper notes - minimal memory baselines and the theory of forgetting
tags: [l, research, papers]
---

# Paper notes - minimal memory baselines and the theory of forgetting

Scope: how much stored memory (examples, features, bits) a class-incremental learner needs at minimum, and what simple baselines actually achieve. Four items were requested: GDumb, Tiny Episodic Memories, GEM / A-GEM, and the Wang et al. continual learning survey. Read on 25 Oct 2026 from PDFs downloaded from arxiv.org and pdftotext (text treated as data). All numbers are copied from the papers (reported by the authors, not reproduced by us); numbers marked "computed here" are our arithmetic on the authors' tables.

## 0. Reading status and ids (what was actually read)

| Paper | Id | Status |
|---|---|---|
| Tiny Episodic Memories (Chaudhry et al.) | arXiv 1902.10486 (v4, 4 Jun 2019) | Read in full: method, Alg. 1-5, all of Sec. 5, Tables 1-8, Figs 1-7, appendix. |
| GEM (Lopez-Paz, Ranzato) | arXiv 1706.08840 (v6) | Read in full except the full evaluation matrices R of its Appendix B (figures only). Picked together with A-GEM because A-GEM restates GEM and is the one used by the later papers. |
| A-GEM (Chaudhry et al., ICLR 2019) | arXiv 1812.00420 (v2) | Read in full: protocol, metrics, Alg. 1-2, derivation (App. C), App. D-G tables. Hyper-parameter grids in App. G read only for the memory-related entries. |
| Survey: A Comprehensive Survey of Continual Learning (Wang et al.) | arXiv 2302.00487 | Read: Secs 1-3 (scenarios, metrics, theory), 4.1-4.4 (methods), 5 (class-incremental, few-shot, general CL), 7 (discussion), 8. Sections 6 (detection, segmentation, generation, RL, NLP applications) skimmed only; they are not relevant to memory budget. |
| GDumb (Prabhu, Torr, Dokania, ECCV 2020) | NO arXiv id found | **NOT READ - UNVERIFIED.** A search for the title and arxiv.org's own search for "GDumb" returned no arXiv entry for the paper itself (hits are later papers that cite it). The hosts that carry the PDF (ecva.net, robots.ox.ac.uk, ora.ox.ac.uk, semanticscholar.org) are blocked by this environment's proxy (HTTP 403). It is a Springer LNCS 12347 / ECCV 2020 paper (pages 524-540 per the survey's reference [348]; page numbers UNVERIFIED). Everything below on GDumb comes from (i) its abstract as returned by the search tool, (ii) the survey's one-line description, and (iii) the GDumb result rows and Appendix A of **RanDumb** (Prabhu et al., NeurIPS 2024, arXiv 2402.08823, read), which re-use GDumb's numbers. Items from my memory of GDumb are tagged UNVERIFIED. Action for the team: fetch the ECCV PDF by hand and re-check Section 1 below. |

## 1. GDumb: A Simple Approach that Questions Our Progress in Continual Learning (Prabhu, Torr, Dokania; ECCV 2020)

### (a) Mechanism
- From the abstract (search result) and the survey: the sampler "greedily stores samples in a fixed-size memory as they arrive" and, at test time, "trains a model from scratch using only the samples in the memory". Survey wording (Sec. 4.2): "GDumb greedily collects incoming training samples in a memory buffer and then uses them to train a model from scratch for testing"; Sec. 5.3 groups it among methods "balanced in class labels" (with CBRS and CoPE).
- UNVERIFIED (from memory, not from the text): the greedy sampler admits a sample if its class has fewer than M/(classes seen) slots, else it evicts a random item of the currently largest class, so the buffer stays class-balanced; the learner is a plain small CNN retrained from scratch with SGD, a cosine schedule and cutmix; no information from the stream is kept other than the buffer.
- RanDumb Appendix A (read) states the contrast: GDumb "dismisses the value of directly learning from online data, as GDumb does not retain or utilize information from online samples"; "in rehearsal-free settings without exemplar storage ... GDumb would inherently produce random performance due to its dependence on memory"; "GDumb excels in high-memory scenarios" and "RanDumb primarily targets low-memory environments".

### (b) Budgets and numbers (all via RanDumb tables, GDumb numbers copied from GDumb / OnPro / PEC settings; the benchmark is stated for each)
Memory is counted in samples. Raw size, ESTIMATED by us: MNIST 784 bytes (8 bit pixels), CIFAR 3072 bytes, so 500 samples is about 0.39 MB (MNIST) or 1.5 MB (CIFAR); a 1-bit MNIST image would be 98 bytes, a 1-bit CIFAR image 384 bytes.

Benchmark A (RanDumb Table 2, one class per task, "(10/1)" = 10 tasks / 1 class per task, memory 500 samples total, i.e. 50 per class for 10 classes, 5 per class for CIFAR-100):

| Method | Memory | MNIST | CIFAR-10 | CIFAR-100 (100/1) |
|---|---|---|---|---|
| Fine-tuning | all | 10.1 | 10.0 | 1.0 |
| Joint, 1 epoch | all | 98.3 | 74.2 | 33.0 |
| ER | 500 | 84.4 | 40.6 | 12.5 |
| A-GEM | 500 | 59.8 | 10.2 | 1.0 |
| iCaRL | 500 | 83.1 | 37.8 | 5.7 |
| DER++ | 500 | 91.9 | 35.6 | 6.2 |
| X-DER | 500 | 83.0 | 43.2 | 15.6 |
| **GDumb** | 500 | **91.0 +-0.2** | **50.7 +-0.7** | 8.2 +-0.2 |
| EWC, SI, LwF, LT | 0 | 10.1 to 12.7 | 10.0 to 10.6 | about 1 (chance) |
| Gen-NCM / Gen-SLDA / VAE-GC | 0 | 82.0 / 88.0 / 84.0 | 27.7 / 41.4 / 42.7 | 10.0 / 18.8 / 19.7 |
| RanDumb (no buffer) | 0 | 98.3 | 55.6 | 28.6 |

Fraction of the gap between fine-tuning and joint closed (computed here): GDumb at 50 per class closes (91.0-10.1)/(98.3-10.1) = 92% on MNIST and (50.7-10.0)/(74.2-10.0) = 63% on CIFAR-10. A-GEM at 500 samples closes only 56% (MNIST) and about 0% (CIFAR-10): gradient projection is the wrong use of a small buffer when classes arrive one at a time.

Benchmark B.1 (RanDumb Table 3, two classes per task, "(5/2)" = 5 tasks of 2 classes; buffer M total; GDumb row):
- MNIST M = 0.1k (10 per class): 81.2 +-0.5 (ER 78.7, DER++ 74.4, MIR 79.0).
- CIFAR-10 M = 0.1k (10 per class): 23.3 +-1.3; M = 0.2k (20 per class): 35.9 +-1.1 (DER++ 31.5 and 44.2; CoPE 33.5 and 37.3; DVC 35.2 and 41.6).
- CIFAR-100 (10/10): M = 0.5k (5 per class): 8.2 +-0.2; M = 1k (10 per class): 18.1 +-0.3 (DER++ 16.0 and 21.4).
- CIFAR-100 (50/2) M = 1k: 18.1 +-0.3. TinyImageNet (100/2): M = 1k 4.6, M = 2k 12.6 (best of the table at 2k).
- Column order of this table was recovered from the layout of the extracted text (ER row cross-checked against the Table 4 captions): UNVERIFIED to the extent that the column header could not be read directly.

Benchmark D (RanDumb Table 5 left, M = 1k): GDumb CIFAR-10 (5/2) 61.2 +-1.0 (100 per class), CIFAR-100 (10/10) 18.1, TinyImageNet 4.6; RanDumb text says "GDumb performs the best on CIFAR10, indicating this is already in a large-exemplar regime". Joint CIFAR-10 for reference 74.2 (Table 2).

Reading of the sweep: GDumb's accuracy rises about linearly in log of the budget and does not saturate by 100 per class; at 10 per class it is competitive with replay methods; at 5 per class on CIFAR-100 it is near chance (8.2).

### (c) Why forgetting happens, and the minimum
GDumb's claim (via abstract/survey): the continual-learning machinery (regularisers, gradient constraints, distillation) adds little over simply learning from a class-balanced stored subset; hence "progress" in the literature is measured in over-simplified settings. What it implies for the minimum: with a class-balanced buffer the learner is trained on the exact class mix it will be tested on, so there is no class-recency bias at all, and the only loss against joint training is the smaller training set. The minimum is therefore a sample-complexity question (how many examples per class a given learner needs), not a stability question.

### (d) Operations
Sampler: O(1) per arriving sample (counter per class, one random eviction). Training: a full offline training of a deep net on M samples at each query time (many epochs); no matrices needed by the sampler, but the learner is an ordinary CNN trained with backprop (not allowed on the L chip; it would run on the GPU side).

### (e) Limitations
No use of online data after it leaves the buffer; near-chance in the zero-buffer and in the very-low-buffer regime (RanDumb App. A, CIFAR-100 5 per class 8.2); needs a full retrain per evaluation; RanDumb shows a no-buffer random-feature classifier beats it on MNIST (98.3 vs 91.0), CIFAR-100 (28.6 vs 8.2) and TinyImageNet at 1k.

### (f) Fit to L and the one concrete test
Class-balanced greedy buffer is the only buffer rule that is natural for a counting chip: it is a per-class counter plus random overwrite. See Section 6 for the test.

## 2. On Tiny Episodic Memories in Continual Learning (Chaudhry, Rohrbach, Elhoseiny, Ajanthan, Dokania, Torr, Ranzato; arXiv 1902.10486)

### (a) Mechanism
Experience Replay (ER), Algorithm 1: allocate memory M of size mem_sz; for each task t and each mini-batch B_n of size K from the stream (single pass, each example seen once): sample a mini-batch B_M of the same size from M; take ONE SGD step on the stacked batch B_n union B_M (so the loss is the average of the current gradient g and the memory gradient g_ref); then update memory. Compared with fine-tuning the only changes are the memory update and a doubled mini-batch. Contrast with A-GEM: if g.g_ref >= 0 use g, else project g so g.g_ref = 0; ER uses the average of the two gradients with no projection.

Memory write rules (all assume a stream and fixed small memory, so no temporary storage of all data):
- **Reservoir sampling** (Alg. 2): keep item with probability mem_sz / n; overwrite a random slot. Not class-balanced.
- **Ring buffer** (Alg. 3): one FIFO of size mem_sz / C per class (C = total classes over all tasks); keeps the last few of every class; guarantees equal class representation; wastes unused slots early because stacks have constant size.
- **k-Means** (Alg. 4): per class online k-means in the penultimate feature space; store the example nearest each centroid (c_j <- c_j + (phi(x) - c_j)/n_j).
- **Mean of Features (MoF)** (Alg. 5, iCaRL-style): per class running mean f <- alpha f + (1-alpha) phi(x), keep the examples closest to that mean in a heap.
- **Hybrid** (Sec. 5.4, Fig. 2): reservoir until some earlier class has only one slot left, then switch to ring buffer, keeping min(n, |M|/K) random examples per class (n = examples of that class in memory, K = classes seen). Tested with 85 slots on Split CIFAR (17 tasks x 5 classes, about 1 slot per class at the end); hybrid is at least as good as reservoir (once many tasks have arrived) and ring buffer (early).

Protocol (Sec. 3): a cross-validation stream D_CV of 3 tasks (replayable as often as needed) for hyper-parameters, then an evaluation stream D_EV (17 tasks) seen once. Metrics: average accuracy A_T = (1/T) sum_j a_{T,j} and forgetting F_T = (1/(T-1)) sum_j f_j^T with f_j^i = max_{l<i} a_{l,j} - a_{i,j}.

### (b) Memory budget and numbers
Setting: **task-incremental with multi-head outputs** (an integer task id selects a task-specific classifier head). Datasets: Permuted MNIST (23 tasks; 20 evaluated, 3 for CV), Split CIFAR-100 (20 tasks x 5 classes), Split miniImageNet (20 tasks x 5 classes), Split CUB (20 tasks x 10 classes). Architectures: MLP with two 256-unit ReLU layers (MNIST); reduced ResNet18 (CIFAR, miniImageNet); ImageNet-pretrained ResNet18 (CUB). SGD, batch 10, memory batch 10 always. Hyper-parameters (Table 8): lr 0.1 on MNIST for all; 0.03 on CIFAR, CUB and miniImageNet, except ER-Reservoir lr 0.1 on CIFAR and miniImageNet and 0.03 on CUB; EWC lambda = 10; MER gamma = 0.1, s = 10 (MNIST) or 5 (others).

Tables 3-6, average accuracy A_T (%) at the end, 5 runs, samples per class 1 / 3 / 5 / larger:

| Dataset | Fine-tune | EWC | A-GEM (1/3/5/last) | ER-Ring (1/3/5/last) | ER-Reservoir (1/3/5/last) | Multi-task |
|---|---|---|---|---|---|---|
| Permuted MNIST (last = 15) | 53.5 | 63.1 | 62.1 / 63.2 / 64.1 / 66.0 | 70.2 / 73.5 / 75.8 / 79.4 | 68.9 / 75.2 / 76.2 / 79.8 | 83 |
| Split CIFAR (last = 13) | 40.6 | 41.2 | 54.9 / 56.9 / 59.9 / 63.1 | 56.2 / 60.9 / 62.6 / 64.3 | 53.1 / 59.7 / 65.5 / 68.5 | 68.3 |
| Split miniImageNet (last = 13) | 34.7 | 37.7 | 48.2 / 51.6 / 54.3 / 54.0 | 49.0 / 53.5 / 54.2 / 55.9 | 44.4 / 50.7 / 56.2 / 61.3 | 62.4 |
| Split CUB (last = 10) | 55.7 | 55.0 | 62.1 / 62.1 / 63.4 / 62.5 | 65.0 / 71.4 / 73.6 / 75.5 | 61.7 / 71.4 / 75.5 / 76.5 | 65.6 |

Other rows: ER-K-Means CIFAR 56.6 / 60.1 / 62.2 / 65.2; ER-MoF CIFAR 56.6 / 59.9 / 61.1 / 62.7; MER CIFAR 49.7 / 57.7 / 60.6 / 62.6. Headline numbers from Fig. 1: ER-Ring gain over fine-tune at 1 per class is +16.7 (MNIST), +15.6 (CIFAR), +9.3 (CUB), +14.3 (miniImageNet) points; ER gain over A-GEM on CIFAR 1.7 points at 1 per class and more than 5 points at 13 per class; abstract: "gains between 7% and 17% when the memory is populated with a single example per class" (the gain over EWC).

Fraction of the fine-tune-to-multi-task gap closed by ER-Ring (computed here): Permuted MNIST 57% at 1 per class, 69% at 3, 87% at 15; Split CIFAR 56% at 1, 73% at 3, 86% at 13; miniImageNet 52% at 1, 67% at 3; CUB 94% at 1. ER-Reservoir at 13 per class on CIFAR (68.5) and at 10 on CUB (76.5) exceeds the multi-task upper bound (68.3 and 65.6), because the multi-task baseline sees each example once. The authors state accuracy "does not saturate at 13 examples per class".

Forgetting at 1 sample per class (Table 1): fine-tune 0.29 / 0.27 / 0.13 / 0.26 (MNIST / CIFAR / CUB / miniImageNet); ER-Ring 0.12 / 0.13 / 0.03 / 0.12. Training time (Table 2): CIFAR fine-tune 87 s, EWC 159, A-GEM 230, MER 755, ER-Ring 116; CUB 194 / 235 / 510 / 277 / 255.

Absolute budget in bytes (ESTIMATED by us): 85 slots of 32x32x3 8-bit images = 261 KB; 1 per class for 100 classes of CIFAR = 307 KB; 13 per class x 100 classes = 1300 images about 4.0 MB; Permuted MNIST 15 per class x 10 classes x 20 tasks = 3000 images about 2.4 MB (the memory per task is what counts). In 1-bit pixels these shrink by 8x; the paper never tests that.

### (c) Why forgetting happens, minimum needed
- Sampling analysis (Sec. 5.4): "when the memory is tiny, sampling methods that by construction guarantee a balanced number of samples per class work the best (even better than reservoir sampling)". Below 3 per class reservoir evicts whole early classes ("often ends up evicting some of the earlier classes from the memory, thereby inducing higher forgetting"). On CIFAR at 1 per class reservoir is 3.5 points worse than k-means; ring, k-means and MoF are within 0.5 of each other. So selection beyond class balance gives almost nothing at the tiny end; the size of the budget matters more than the cleverness of the rule.
- Generalisation from a tiny memory (Sec. 5.5, App. C): repeated training on only the memory drives the memory loss to about 0 and memory accuracy to 100% (A-GEM does not reach it), yet test accuracy on the old task is better than without the memory. Mechanism claimed: training on the new task's data acts as a "strong, albeit implicit and data-dependent, regularizer" for the old task; strength is set by the number of new-task examples, effectiveness by task relatedness. Experiment on MNIST Rotations with 10 memory slots (one per class): training on M_1 alone drops task-1 accuracy from 85% to 40%; ER with D_2 beats fine-tuning at all rotation angles (20, 40, 60 degrees); for almost adversarial tasks (a rotated 2 looks like a 5) the regulariser turns harmful, 40% (memory only) falls to 30% (memory plus D_2). App. Table 7: at 1000 task-2 samples and 10 degrees ER-Ring train 85.6 / memory 100 / test 86.2 vs A-GEM 81.5 / 86.6 / 82.5; at 90 degrees ER-Ring test 69.4 vs A-GEM 52.1.
- Minimum: no minimum is derived; the paper states the learner needs at least a handful per class, with continuing gains up to 13-15 per class, and that 1 per class already removes about half of the fine-tune gap.

### (d) Operations
Per step: forward and backward on twice the batch (so about 2x the fine-tuning compute, measured +33% on CIFAR vs fine-tune 116 vs 87 s), one random-sample from the buffer, one counter or heap update. Backprop on a conventional net: not allowed on the L chip.

### (e) Limitations
Task-incremental (multi-head, task id given) so it does not measure the hardest part of class-incremental learning, cross-task class confusion; the "multi-task" bound is a single pass and is beaten; only small CNN / MLP; gains vanish when tasks are adversarial; no proof; no result below 1 per class or on the hybrid beyond one plot; k-Means / MoF depend on a learned feature space; memory counted in samples, not bits.

### (f) Fit to L
Strong support for (i) class-balanced storage at the tiny end, (ii) 1 to 5 stored examples per class recovering 50 to 75% of the gap even for a network trained by plain SGD, (iii) a counting table does not need the memory-regulariser story because its per-class counts do not interfere. See Section 6.

## 3. GEM and A-GEM (Lopez-Paz and Ranzato, arXiv 1706.08840; Chaudhry, Ranzato, Rohrbach, Elhoseiny, arXiv 1812.00420)

I read both; A-GEM is the one analysed in most detail because it restates GEM and states its memory costs.

### (a) Mechanism
Setting: stream of (x_i, t_i, y_i) triplets, each seen once, with a task descriptor t_i (integers in the experiments). Per-task episodic memory M_k holds the last m examples of task k (GEM: "the memory is populated with the last m examples from each task"; budget M total, m = M/T if T known, otherwise shrink m as tasks arrive). Loss on memory: l(f, M_k) = (1/|M_k|) sum l(f(x_i,k), y_i) (GEM Eq. 5).

GEM: minimise l(f_theta(x,t), y) subject to l(f_theta, M_k) <= l(f_theta^{t-1}, M_k) for all k < t (Eq. 6). Using local linearity this becomes the angle constraints <g, g_k> >= 0 for all k < t (Eq. 7), where g is the proposed gradient and g_k = d l(f, M_k)/d theta. If violated, project: minimise (1/2)||g - g~||^2 subject to <g~, g_k> >= 0 (Eq. 8), a QP in p variables (p = 1,109,240 for the CIFAR network). Solved through the dual: minimise (1/2) v^T G G^T v + g^T G^T v subject to v >= 0 (Eq. 11), with G = (g_1,...,g_{t-1}) and g~ = G^T v* + g; only t-1 variables. A small constant gamma >= 0 added to v* biases the update toward positive backward transfer. Algorithm 1 in GEM: per example compute g, g_k for all k < t, Project, SGD step; evaluate the matrix R_{i,j}.

A-GEM: replace the t-1 constraints by one: the average memory loss over all past tasks must not rise, l(f, M) <= l(f^{t-1}, M) with M = union of M_k (Eq. 9). With g_ref the gradient on a random batch from M: g~ = g if g^T g_ref >= 0, else g~ = g - (g^T g_ref / g_ref^T g_ref) g_ref (Eq. 11; derivation in App. C through the Lagrangian z* = g + alpha g_ref, alpha* = -g^T g_ref / g_ref^T g_ref). Memory populated by uniform random choice per task (App. B Alg. 2: s = |M|/T samples drawn from D_t).

Protocol/metrics: GEM defines ACC = (1/T) sum R_{T,i}, BWT = (1/(T-1)) sum (R_{T,i} - R_{i,i}), FWT = (1/(T-1)) sum_{i>=2} (R_{i-1,i} - b_i). A-GEM adds the cross-validation stream (3 tasks) + 17-task single-pass evaluation stream, forgetting F_k, and Learning Curve Area LCA_beta = (1/(beta+1)) sum_{b=0}^{beta} Z_b with Z_b = (1/T) sum_k a_{k,b,k}.

### (b) Memory budget and numbers
- GEM datasets: MNIST permutations and rotations (20 tasks x 1000 examples x 10 classes; MLP with two 100-unit ReLU layers) and incremental CIFAR-100 (20 tasks x 2500 examples x 5 classes; ResNet18 with 3x fewer feature maps, a linear head per task); SGD batch 10. Grid (App. A): GEM memory 5120 (CIFAR, rotations, permutations best), gamma best 0.5, lr 0.1. Memory sizes searched for iCaRL: 200, 1280, 2560, 5120.
- **GEM Table 2, CIFAR-100 ACC vs memory size** (total samples; as extracted): memory 200 -> GEM 0.487, iCaRL 0.436; 1,280 -> 0.579 / 0.494; 2,560 -> 0.633 / 0.500; 5,120 -> 0.654 / 0.508. In samples per class (100 classes): 2, 13, 26, 51. GEM ACC "is an increasing function of the size of the episodic memory". iCaRL (class-incremental, nearest-exemplar classifier) is nearly flat at 0.44 to 0.51 and always below GEM; note iCaRL is evaluated on the same task-incremental protocol here.
- GEM Table 3 (MNIST Rotations, ACC/BWT vs epochs per task, as extracted): at 1 epoch GEM 0.86/+0.05 vs EWC 0.55/-0.19 vs single 0.53/-0.08; at 2 epochs GEM 0.88/+0.02; at 5 epochs GEM 0.89/-0.02, EWC 0.61/-0.11, single 0.43/-0.40. Authors: GEM "matches the 'oracle performance upper-bound' ACC provided by iid learning" (iid shuffled single: 0.83 at 1 epoch, 0.87, 0.89 for 2 and 5 epochs). CPU time for MNIST (Table 1): GEM 135 s (permutations column; single 11, EWC 179) - column assignment UNVERIFIED from the extracted layout.
- A-GEM memory per task: 250 (MNIST), 65 (CIFAR), 50 (CUB), 100 (AWA) as listed in Sec. 6 for iCaRL, GEM and A-GEM in that order of datasets (the sentence lists "250, 65, 50, and 100" for the four streams); with 5 classes per CIFAR task, 65 = 13 per class; reference batch for g_ref: 256 / 1300 / 128 / 128.
- A-GEM Table 4 (5 runs): Permuted MNIST AT: VAN 47.9, EWC 68.3, GEM 89.5, A-GEM 89.1, Prog-NN 93.5, multi-task 95.3. Split CIFAR AT: VAN 42.9, EWC 42.4, iCaRL 50.1, GEM 61.2, A-GEM 62.3, Prog-NN 59.2, multi-task 68.3. Forgetting F_T: GEM 0.06 and A-GEM 0.06 (MNIST), 0.06 and 0.07 (CIFAR). Table 5/6 (10 runs): Split CUB A-GEM 62 (+-3.5) vs VAN 54.3, multi-task 65.6; Split AWA A-GEM 44 vs VAN 30.3, multi-task 64.8. With joint-embedding task descriptors CUB 71 vs 73.8 and AWA 50 vs 66.8.
- Compute/memory (Table 7): training time MNIST GEM 3442 s vs A-GEM 477 s, CIFAR 5238 s vs 449 s, EWC 403 / 250; memory GEM P*T + (B+M)*H vs A-GEM 2*P + (B+M)*H (P params, T tasks, B batch, H hidden state, M episodic memory per task). GEM and A-GEM are within 0.5 points on MNIST (89.5 vs 89.1) and 1.1 on CIFAR (61.2 vs 62.3). Table 2 (App. D.2): on the stored memory set GEM has accuracy 99.5 (MNIST) / 97.1 (CIFAR) with worst-case forgetting 0 / 0.05, A-GEM 99.3 / 72.1 with 0.008 / 0.15; on test data CIFAR A-GEM 62.3 vs GEM 61.2. Table 3: S-GEM (one random constraint per step) 88.2 and 56.2, worse than both.
- App. D.1: constraint violations per task; GEM violates almost every step as tasks grow, A-GEM plateaus lower (MNIST 5500 and CIFAR 250 gradient steps per task).
- App. F EWC analysis: EWC needs over-parameterised networks and several epochs; with one epoch it equals the vanilla baseline on Split CIFAR.

### (c) Why forgetting happens, and the minimum
Both define forgetting as a loss increase on old tasks along the new-task gradient, so the cure is a first-order constraint on the update direction using stored samples as a proxy for the old loss. Assumptions explicitly stated: local linearity around small steps and that "the memory is representative of the examples from past tasks". Failure modes the A-GEM authors note: GEM guarantees worst-case per-task non-increase on the memory but A-GEM only the average, and the guarantee holds only on the memory, not on the test set ("the result is confounded by the generalization error"). EWC-like regularisation cannot estimate its importance weights from a one-pass, not-converged model, and cannot give positive backward transfer. Final A-GEM conclusion: "a substantial performance gap between LLL methods, including A-GEM, trained in a sequential learning setting and the same network trained in a non-sequential multi-task setting, despite seeing the same data samples". The minimum memory is not derived; the empirical curve (GEM Table 2) shows gains up to 51 per class and no saturation.

### (d) Operations
GEM: per step t-1 backward passes (one per past-task memory) plus a QP; A-GEM: one extra backward pass on a random memory batch, one dot product, one scalar-times-vector. Both need full-network gradients: backprop, vectors of length p, and a QP solver for GEM. Not compatible with the L chip.

### (e) Limitations
Task id required at test time (multi-head); memory fixed per task, last-m rule (no class balancing, no coreset, as GEM itself states "we did not investigate advanced memory management"); relies on gradient geometry; GEM does not scale (time 3442-5238 s); A-GEM and GEM underfit the memory, which Tiny Episodic Memories shows loses the regularisation benefit; sequential training stays below multi-task.

### (f) Fit to L
No operational fit (gradients, dot products, projection). The useful items are the definitions: ACC, BWT (R_{T,i} - R_{i,i}), forgetting F and Learning Curve Area, and the single-pass cross-validation protocol (3 tasks for hyper-parameters, 17 for evaluation), which we should copy so L's thresholds are not tuned on the test stream. The memory-vs-ACC data (200 to 5120 samples) is a ready reference curve to compare with.

## 4. A Comprehensive Survey of Continual Learning: Theory, Method and Application (Wang, Zhang, Su, Zhu; arXiv 2302.00487)

### (a) Mechanism (what the survey asserts; it has no algorithm of its own)
- Scenarios (Sec. 2.2, Table 1): IIL, DIL, TIL (task id given in training and testing), CIL (task id only in training), TFCL, OCL (one-pass stream), BBCL, CPT.
- Metrics (Sec. 2.3): AA_k = (1/k) sum a_{k,j}; AIA_k; FM; BWT; intransience IM_k = a*_k - a_{k,k}; FWT; also storage and computation overhead. Single-head evaluation applies to CIL, multi-head to TIL.
- Theory (Sec. 3.1): stability-plasticity trade-off; Bayesian recursion p(theta | D_1:k) proportional to p(theta | D_1:k-1) p(D_k | theta) (Eq. 8), with the posterior approximated by online Laplace (Eq. 9-12, EWC loss L = l_k + (lambda/2)(theta - mu_{k-1})^T F (theta - mu_{k-1})) or variational inference (Eq. 13-14). "In essence, the constraint on continual learning for either replay or regularization is ultimately reflected in gradient directions": replay via <grad L(D_k), grad L(M_t)> >= 0, gradient projection without samples (NCL update theta <- theta + lambda [Lambda^{-1} grad l - (theta - mu)], Eq. 15-16). Architecture-based learners factor p(D_t | theta) = p(D_t | theta^(t)) p(ID_t = t | D_t, theta) (Eq. 17-18) so that a task-identity predictor is itself required and itself forgets.
- Generalisability (Sec. 3.2): second-order Taylor bound on the loss of task i when parameters move to task j's optimum, l_i(theta_j*) - l_i(theta_i*) <= (1/2) lambda_i^max ||Delta theta||^2 (Eq. 19-20), lambda_i^max the top Hessian eigenvalue (flatness); NTK result for multi-head networks, forgetting bounded by a sum of terms with the cosines of principal angles between task feature subspaces, the singular values, the unlearned residuals and the number of replay samples |rep| (Eq. 21), which implies that increased task similarity can increase forgetting for separate heads; the shared-solution problem is NP-hard in general (survey ref. [225]) because the feasible parameter space gets narrow and irregular, "mitigated by replaying representative old training samples [225], restricting the feasible parameter space to a hyperrectangle, or alternating the model architecture"; generalisation bound c*_t <= E l_t <= c*_t + zeta(N_t, delta) with zeta of order lambda B sqrt(|theta| log N log(|theta| k / delta)) / (2 sqrt N_t) for a learner with shared global minimiser (Eq. 22), and a K-parameter-space refinement adding a flatness term R and a task discrepancy Div(D_i, D_t) (Eq. 23).
- Replay (Sec. 4.2): experience replay (selection rules reservoir, ring buffer, mean-of-feature, k-means, plane distance, entropy "but all perform mediocrely"; gradient-based GSS, OCS, ASER, etc.; compression AQM, MRDC; stored logits DER/DER++), generative replay, feature replay (store prototypes or class statistics: IL2M, SNCL; FeTrIL replays features from a fixed extractor). Sec. 4.4: with a pre-trained backbone, a nearest-class-mean classifier on saved prototypes "has proved to be a strong baseline". Sec. 5.1: CIL splits into within-task prediction and task-identity prediction (closely tied to OOD detection); data-free CIL works through model inversion, class-wise feature statistics or pre-training.

### (b) Memory budget and numbers
The survey contains no memory-budget table, no accuracy-vs-buffer curve and no experiments; it states only qualitative budget facts: replay "extremely limited storage space" so the key challenge is how to construct and exploit the buffer; per learning theory [154] more replayed samples improve the old task but at "a linear increase in resource overhead" and privacy cost; generative replay has "a huge additional resource overhead"; Table 2 lists CIL methods that use replay; GDumb is cited as an "evaluation criterion for more advanced strategies" together with DER/DER++ ("several simple baselines of experience replay can achieve considerable performance"). Small-dataset numbers at 1 to 20 per class: none (UNVERIFIED nothing hidden; the sections were read).

### (c) Why forgetting happens, and what is unavoidable
1. Information-theoretic root (Sec. 3.1): "when learning the k-th task from D_k, the old training sets {D_1,...,D_{k-1}} are inaccessible"; a model must capture old and new distributions in balance. Two ways: approximate the old distribution (store samples, or a generative model) or propagate it in the parameters (Bayesian regularisation).
2. Parameter-sharing root (Eq. 19-20 and Fig. 2): moving to a new optimum costs old tasks at most (1/2) lambda_max ||Delta theta||^2: forgetting scales with sharpness and distance between task optima.
3. Feasibility root (NP-hardness, Fig. 2e): a single shared solution lives in a shrinking intersection of feasible sets.
4. Class-incremental root (Sec. 5.1): new classes are out-of-distribution for the old ones, so with no old samples the classifier has no training signal that separates old from new classes; the task-identity predictor (Eq. 18) is itself trained incrementally and forgets; replay supplies exactly the missing end-to-end signal while distillation on new samples is "limited to the output side with a biased distribution".
5. Without stored samples (what the survey says is available): regularisation (EWC family) and gradient projection in the null space of old inputs (needs input covariance of the old tasks), prototypes or Gaussian class statistics on a frozen pre-trained representation, model inversion or generative replay. The survey says nothing quantitative about how much can be achieved with zero samples when the representation is learned from scratch; the RanDumb tables (Section 1 of this note) fill the gap: when tasks are single classes, EWC, SI, LwF and LT stay at chance (10.1 / 12.7 / 11.8 / 10.9 on MNIST, 1.0 to 1.1 on CIFAR-100), while class-wise feature statistics (Gen-NCM, Gen-SLDA, RanDumb) reach 82 to 98% on MNIST.
6. Pre-training effect (Sec. 4.3-4.4, 7.1): pre-trained and self-supervised representations suffer less forgetting (wider basin, more orthogonal and sparse representations), benefits grow with pre-training data and model size.

### (d) Operations
The surveyed families need Fisher matrices, Hessian-vector products, gradient projection (SVD of feature covariances, e.g. GPM, Adam-NSCL), distillation or GAN training; only the sampling rules, prototype and NCM methods and buffer-with-retrain baselines use counters and means.

### (e) Limitations
Survey, not experiment: no numbers; the NTK and bound results (Eq. 21-23) are quoted from other papers under strong assumptions (NTK regime, shared global minimiser, uniform convergence) and are not tested on tiny budgets; no analysis of memory in bits; the forgetting bound is about continuous parameter drift, not about discrete counting tables. Survey admits "the merits and potential limitations of experience replay remain largely open" and that replay "risks overfitting to only a few old training samples". Sec. 6 (applications) was skimmed, not studied.

### (f) Fit to L
The theory section justifies the project's design rule directly: forgetting is parameter interference (Eq. 19-20) and OOD task-identity confusion (Eq. 17-18); a counting table that stores per-class counts in disjoint cells has no shared parameters to drift, so it removes cause 2 and 3 by construction, leaving causes 1 (the representation / binarisation / feature selection that is shared) and 4 (the cross-class decision, which needs either class-conditional statistics that are comparable across stages or a few stored samples).

## 5. Cross-paper synthesis

Smallest buffer that closes most of the gap (ESTIMATED reading across the tables above, different protocols, so only the order of magnitude is reliable):
- Task-incremental, trained net, class-balanced replay: 1 sample per class closes about 52 to 57% of the fine-tune-to-multi-task gap (MNIST, CIFAR, miniImageNet; 94% on pre-trained CUB); 3 per class about 67 to 73%; 5 per class about 70 to 80%; 13 to 15 per class 86 to 96%, and above the single-pass multi-task bound with reservoir.
- Class-incremental, GDumb-style rebuild from the buffer, from scratch: MNIST 10 per class 81.2 vs joint 98.3 (about 80% of the way from chance), 50 per class 91.0 (92% of the gap); CIFAR-10 20 per class 35.9, 50 per class 50.7 (63%), 100 per class 61.2 vs joint 74.2 (about 80%). CIFAR-100 needs more than 10 per class (18.1 vs joint 33.0).
- So: about 10 per class on easy data (MNIST), about 50 to 100 per class on CIFAR-10, to reach 80 to 90% of the way to joint. Rules: class balance first; reservoir only when more than about 3 per class are available; no benefit from k-means or mean-of-feature selection over random balanced choice at the tiny end.
- Without any stored sample: a learned representation collapses to chance (EWC / SI / LwF at 1 class per task), only per-class summary statistics on a fixed, non-learned or pre-trained representation survive (Gen-NCM, Gen-SLDA, RanDumb: MNIST 98.3 = joint, CIFAR-10 55.6 vs 74.2 joint = 75% of the gap, CIFAR-100 28.6 vs 33.0 = 87%). What is unavoidable: the cross-class decision for classes that have never been seen together cannot be learned from the new class alone (OOD argument, survey Sec. 5.1), and the representation cannot be improved after the fact without old samples (RanDumb, survey Sec. 7.1); at most a fixed encoder plus class-local statistics.

## 6. The one concrete test for L

**Staged buffered-versus-joint test on binary codes (GDumb-style).** Data: MNIST, Fashion-MNIST, CIFAR-10, binarised by the chip's own encoder. Protocol: 5 stages of 2 classes (also a 10 x 1 variant). Arms:
1. Joint: encoder (threshold, feature or hash choice) and counting table fit on all classes together (upper bound).
2. Staged, no buffer: encoder fit on stage 1 only and frozen, counting table incremented per class (the chip's native mode; expected no table forgetting, only encoder mismatch).
3. Staged with a GDumb-style greedy class-balanced buffer of binary codes: admit a code if its class holds fewer than M/(classes seen) slots, otherwise overwrite a random code of the largest class (reservoir until a class has fewer than 3 slots, then ring buffer, per the Tiny Episodic Memories hybrid); at each stage refit the encoder statistics and rebuild the counting table from the buffer only (also variant: buffer refits the encoder, table stays incremental).
4. Staged with random (non-balanced) reservoir at the same size, to reproduce the balanced-versus-reservoir finding.
Sweep k = 1, 2, 5, 10, 20, 50, 100 codes per class; code length from 64 to 784 bits so the buffer is k x classes x bits (MNIST at 784 bits and k = 10 is 100 x 98 B = 9.8 KB, CIFAR at 3072 bits k = 100 is 38 KB). Report: accuracy per stage, final accuracy, forgetting F and BWT as defined in the papers, and the smallest k at which arm 3 reaches 90% of arm 1 minus arm 2, with 5 seeds and +-std. Cross-validate thresholds on a held-out first 3 stages, as the A-GEM protocol does. Expected readings to check against: GDumb numbers in Section 1 (MNIST 81.2 at 10 per class, CIFAR-10 35.9 at 20 per class) and the 1/3/5/13 per class curve in Section 2.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
