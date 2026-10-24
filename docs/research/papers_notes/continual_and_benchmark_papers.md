---
title: Paper notes - continual learning and benchmarks
tags: [l, research, papers]
---

# Paper notes - continual learning and benchmarks

Written 24 Oct 2026. Source texts were downloaded from arxiv.org and read as extracted PDF text. Numbers are copied from the paper text or tables. Anything not found in the paper text is marked **UNVERIFIED**. Nothing here is a number from the L project; the question is what a reviewer would compare L against.

**Access limits.** nature.com, ebi.ac.uk and cam.ac.uk were blocked by the proxy (HTTP 403). So the Nature Machine Intelligence 2022 paper "Three types of incremental learning" (van de Ven, Tuytelaars, Tolias, vol 4, pp 1185-1197, doi 10.1038/s42256-022-00568-3) and the Nature Communications 2022 sleep-replay paper could not be read. arXiv 2201.00766 given in the brief is NOT that paper: it is "Class-Incremental Continual Learning into the eXtended DER-verse" (X-DER, CIFAR-100 / miniImageNet / NTU-60). I found no arXiv posting of the NMI paper. All van de Ven numbers below come from the 2019 preprint 1904.07734 and the 2021 generative-classifier paper 2104.10093, both read in full text.

## 0. Short answer for the reader

- The claim "L learns in stages with about one tenth of the memory of replay, no stored examples" is credible only if the table below is produced with the same protocol and at least the rows marked REQUIRED. On Split MNIST the strongest replay-free, no-stored-data class-incremental number I could verify in a peer-reviewed-style source is the generative classifier at 93.79 (full 2,000 iterations per task, 128 batch, MLP-style VAE per class). Generative replay (DGR) gets 90.79, DGR+distill 91.79, and iCaRL with 2,000 stored exemplars gets 94.57. EWC, SI and fine-tuning sit at about 20 (chance for the last task pair).
- Split Fashion-MNIST class-IL with replay is verified in two sources (section 3): ER at buffer 200 = 72.54, 500 = 79.02, 1000 = 81.39 (full 12,000 images per task); joint training 84.47; SGD 20.11. A 2,000 images-per-stage protocol is NOT the standard one; it is a 5x smaller stream than the usual 12,000 per stage, so baselines must be re-run on it.
- "One tenth of the memory of replay" needs a stated reference: the replay buffer size that matches L's accuracy. Reference points: replay buffer of 2,000 stored images (iCaRL budget, van de Ven) vs 200 (ER+T paper smallest buffer). A tenth of 2,000 images is 200 images, and ER at B200 on Fashion-MNIST reaches 72.54 versus 81.39 at B1000, so memory-vs-accuracy curves, not a single point, are what a reviewer will ask for.
- Biggest credibility risks: (a) comparing an L state size to a replay image buffer while ignoring the model weights of the baseline; (b) hyperparameters tuned on test data across all stages (van de Ven explicitly warns about this); (c) using task identity at test time (that is Task-IL, 99% for everyone); (d) 2,000 images per stage while baselines were published with 6,000+ per class.

## 1. van de Ven and Tolias, "Three scenarios for continual learning" (arXiv 1904.07734)

Read in full (70 KB of text). Read this as the protocol that all later class-IL comparisons copy.

### 1.1 Scenarios (their Table 1, restated)

- Task-IL: task identity is given at test time (multi-headed output; only the current task's output units active).
- Domain-IL: task identity is not given and need not be inferred (same output units for every task).
- Class-IL: task identity must be inferred; every class has its own output unit and all units of classes seen so far are active (single-headed split MNIST).

### 1.2 Split MNIST protocol (their section 4)

- MNIST split into 5 tasks of 2 classes: {0,1},{2,3},{4,5},{6,7},{8,9} (two-way classification per task in Task-IL/Domain-IL; in Class-IL the output grows).
- Standard train/test split: 60,000 training images (about 6,000 per digit), 10,000 test images (about 1,000 per digit). So about 12,000 training images per stage. No preprocessing, original 28x28.
- Network: MLP with 2 hidden layers of 400 ReLU units. Softmax output (iCaRL excepted).
- Training: 2,000 iterations per task, Adam (beta1 0.9, beta2 0.999), learning rate 0.001, batch of 128 current samples per iteration, plus 128 replayed samples per iteration when replay is used. Loss weighting 1/N_tasks_so_far for current vs (1 - 1/N) for replay.
- Generative model for DGR: symmetric VAE, 2 hidden layers of 400, latent size 100, standard normal prior, trained itself with generative replay.
- 20 random seeds; mean (+/- SEM) over runs.
- Metric: average test accuracy over all tasks at the end (for Class-IL, this equals accuracy on all 10 classes at the end, since tasks have equal test size).

### 1.3 Table 4, exact rows (Split MNIST; mean (+/- SEM), 20 seeds)

| Approach | Method | Task-IL | Domain-IL | Class-IL |
|---|---|---|---|---|
| Baseline | None (fine-tuning), lower bound | 87.19 (+/- 0.94) | 59.21 (+/- 2.04) | 19.90 (+/- 0.02) |
| Baseline | Offline (joint training), upper bound | 99.66 (+/- 0.02) | 98.42 (+/- 0.06) | 97.94 (+/- 0.03) |
| Task-specific | XdG | 99.10 (+/- 0.08) | - | - |
| Regularization | EWC | 98.64 (+/- 0.22) | 63.95 (+/- 1.90) | 20.01 (+/- 0.06) |
| Regularization | Online EWC | 99.12 (+/- 0.11) | 64.32 (+/- 1.90) | 19.96 (+/- 0.07) |
| Regularization | SI | 99.09 (+/- 0.15) | 65.36 (+/- 1.57) | 19.99 (+/- 0.06) |
| Regularization | LwF | 99.57 (+/- 0.02) | 71.50 (+/- 1.63) | 23.85 (+/- 0.44) |
| Replay (generative) | DGR | 99.50 (+/- 0.03) | 95.72 (+/- 0.25) | 90.79 (+/- 0.41) |
| Replay (generative) | DGR+distill | 99.61 (+/- 0.02) | 96.83 (+/- 0.20) | 91.79 (+/- 0.32) |
| Replay + exemplars | iCaRL (budget = 2000) | - | - | 94.57 (+/- 0.11) |

- Memory budget for iCaRL: 2,000 stored examples in total (B = 2000), shared equally over classes seen so far, m = floor(B / N_classes_so_far) exemplars per class; chosen by herding; nearest-class-mean classifier in feature space. At the final stage this is 200 per class.
- Permuted MNIST (Table 5) is a different protocol (10 tasks, 1000-unit MLP, 5,000 iterations, lr 0.0001); iCaRL (budget 2000) Class-IL = 94.85 (+/- 0.03) there. Not relevant to L's stages protocol.
- Their conclusion (quote-level): for Class-IL "currently only replay-based methods are capable of producing acceptable results"; EWC and SI "completely fail".

### 1.4 Appendix C: replay of stored data versus memory (Figure C.1; values only in a figure)

- Variants of exact replay using herding-selected stored data: replay during training, nearest-class-mean at test, both. Plotted against total stored examples for split MNIST and permuted MNIST (20 repetitions).
- Text claims: in Class-IL "even storing one example per class was enough for any of the exact replay methods to outperform all regularization-based methods", but "to match the performance of generative replay, it was required to store substantially more data". The y-values of the curve are not in the text: UNVERIFIED. Re-run or digitize the figure before quoting a buffer-versus-accuracy point.

### 1.5 Hyperparameter caveat (their Appendix D)

They warn that the usual practice of choosing hyperparameters by running the full protocol and scoring on all tasks' validation data uses information from all tasks. A reviewer will ask L to tune stage-by-stage or on a held-out validation split that does not use future-stage information.

## 2. van de Ven, Tuytelaars, Tolias 2022, "Three types of incremental learning" (Nature Machine Intelligence)

Not readable here (blocked). What I can say only from search-result summaries: it renames the scenarios to task-, domain- and class-incremental learning and compares methods on Split MNIST and Split CIFAR-100 under each. Exact table rows, replay variants (ER with budgets, A-GEM, iCaRL, BI-R) and memory budgets: **UNVERIFIED**. Recommended action for a human with journal access: copy the Split MNIST class-IL column and the budget footnotes from Table 2 of that paper before submission. Meanwhile the 2019 Table 4 above is the verified analogue (same code base, same protocol family).

### 2.1 Companion paper that IS verified: van de Ven, Li, Tolias, "Class-incremental learning with generative classifiers" (arXiv 2104.10093)

Directly relevant because storing data is not allowed in it, the same constraint as L's "no stored examples".

- Benchmarks: MNIST 5 tasks x 2 classes, 2,000 iterations per task, batch 128; CIFAR-10 5 tasks, 5,000 iterations, batch 256; CIFAR-100 10 tasks (pretrained conv layers); CORe50 5 tasks, single pass, batch 1. "For all benchmarks considered in this paper, storing data is not allowed." 10 seeds, mean (+/- SEM).
- Table 2, final test accuracy, class-incremental, no data stored:

| Method | MNIST | CIFAR-10 | CIFAR-100 | CORe50 |
|---|---|---|---|---|
| None | 19.92 (+/- 0.02) | 18.74 (+/- 0.29) | 7.96 (+/- 0.11) | 18.65 (+/- 0.26) |
| Joint | 98.23 (+/- 0.04) | 82.07 (+/- 0.15) | 54.08 (+/- 0.27) | 71.85 (+/- 0.30) |
| DGR | 91.30 (+/- 0.60) | 17.21 (+/- 1.88) | 9.22 (+/- 0.24) | - |
| EWC | 19.95 (+/- 0.05) | 18.63 (+/- 0.29) | 8.47 (+/- 0.09) | 18.56 (+/- 0.31) |
| SI | 19.95 (+/- 0.11) | 18.14 (+/- 0.36) | 8.43 (+/- 0.08) | 18.69 (+/- 0.26) |
| CWR | 32.48 (+/- 2.64) | 18.37 (+/- 1.61) | 21.90 (+/- 0.68) | 40.28 (+/- 1.13) |
| CWR+ | 37.20 (+/- 3.11) | 22.32 (+/- 1.08) | 9.34 (+/- 0.25) | 40.12 (+/- 1.06) |
| AR1 | 48.84 (+/- 2.55) | 24.44 (+/- 1.08) | 20.62 (+/- 0.45) | 45.27 (+/- 1.02) |
| Labels Trick | 32.46 (+/- 1.95) | 18.43 (+/- 1.31) | 23.68 (+/- 0.26) | 42.59 (+/- 1.03) |
| SLDA | 87.30 (+/- 0.02) | 38.35 (+/- 0.03) | 44.49 (+/- 0.00) | 70.80 (+/- 0.00) |
| Generative classifier | 93.79 (+/- 0.08) | 56.03 (+/- 0.04) | 49.55 (+/- 0.06) | 70.81 (+/- 0.11) |

- Relevance: SLDA (streaming linear discriminant analysis: running class means plus shared covariance, no backprop) at 87.30 on MNIST is the closest "counting-like" no-replay baseline with a number; a count-based learner is expected to be compared with it. SLDA does use matrix-valued statistics, so it is a baseline to beat, not a design to copy.
- Fashion-MNIST is not in this paper.

## 3. Split Fashion-MNIST class-incremental, with and without replay

### 3.1 Primary table: Boschini et al., "Rethinking Experience Replay: a Bag of Tricks for Continual Learning" (arXiv 2010.05595)

Protocol (their section V-A), verified in text:

- Split Fashion-MNIST: 5 tasks of 2 classes, 6,000 exemplars per class (so 12,000 training images per stage, 60,000 total).
- Network: fully connected, 2 hidden layers of 256 ReLU units. Trained from scratch, SGD, one epoch per task, online-style single pass, fixed batch size across methods.
- Hyperparameters by grid search on a held-out validation set of 6,000 items (taken from the training data). 10 runs, mean reported, Class-IL, final average accuracy over all tasks.
- Buffers 200 / 500 / 1000 images (reservoir for ER, ring buffer for GEM/A-GEM/HAL, herding for iCaRL).

Exact Table I, Split Fashion-MNIST column (final average accuracy, %):

| Method | B200 | B500 | B1000 |
|---|---|---|---|
| SGD (no replay) | 20.11 | - | - |
| Joint training (upper bound) | 84.47 | - | - |
| A-GEM | 49.73 | 49.47 | 50.98 |
| GEM | 69.46 | 75.91 | 79.62 |
| HAL | 72.59 | 77.59 | 80.79 |
| iCaRL | 75.46 | 77.54 | 78.13 |
| ER (reservoir) | 72.54 | 79.02 | 81.39 |
| ER+T (their tricks) | 76.07 | 80.11 | 82.46 |

Table II ablation at B200 (Fashion-MNIST): ER 72.54, +BiC 73.43, +ElrD 74.19, +BRS 74.66, +LARS (=ER+T) 76.07. For the same paper Split CIFAR-10 SGD = 19.62, Joint = 92.13 (not needed).

Memory in bytes: a Fashion-MNIST image is 28x28 = 784 bytes at 8 bits per pixel, so B200 = 156,800 bytes (about 153 KiB), B1000 = 784,000 bytes (about 766 KiB), and the 2,000-example iCaRL budget of van de Ven = 1,568,000 bytes (about 1.5 MiB). These byte counts are ESTIMATED by me from image size; the papers report example counts only.

### 3.2 Second source: Distilled Replay (Rosasco et al., arXiv 2103.15851), one pattern per class buffer

- Protocol: Split MNIST, Split Fashion MNIST, Split CIFAR-10, each 5 experiences of 2 classes; single epoch; replay buffer of ONE pattern per class (so up to 10 images); LeNet5 in the class-incremental case; Average Accuracy after each experience. UB = cumulative training, LB = naive.
- Table 1c, Split Fashion MNIST, average accuracy after experience E_k (columns UB, LB, DR = Distilled Replay, SR = simple replay with real samples, iCaRL, MIR). Column assignment read from the extracted two-column layout; the order UB LB DR SR iCaRL MIR is given by the header line:

| Experience | UB | LB | DR | SR | iCaRL | MIR |
|---|---|---|---|---|---|---|
| E2 | .93 | .50 | .84 | .74 | .82 | .76 |
| E3 | .84 | .33 | .67 | .55 | .66 | .55 |
| E4 | .76 | .30 | .63 | .54 | .59 | .55 |
| E5 | .78 | .19 | .63 | .48 | .60 | .45 |

- Same paper, Split MNIST (Table 1b, E5): UB .91, LB .20, DR .82, SR .61, iCaRL .77, MIR .59. Text quotes "iCaRL and MIR obtained 77% and 59% accuracy respectively, while Distilled Replay achieves an accuracy of 82%".
- Takeaway: with a 10-image buffer, real-sample replay on Fashion-MNIST gives 0.48 and the best method 0.63. The paper itself notes similar classes (t-shirt, shirt, coat, dress, pullover) harm single-pattern buffers.

### 3.3 Other Fashion-MNIST numbers and their reliability

- Lifelong neural predictive coding (S-NCN, Ororbia, arXiv 1905.10696), Table 2, single-head Split Fashion MNIST: EWC 0.199, SI 0.198, MAS 0.180, LwF 0.875, iCaRL 0.960, Lucir 0.950, GDumb 0.973, Mnemonics 0.968, NR+M2 (naive rehearsal with memory) 0.948, S-NCN 0.982. Caution: these single-head values (iCaRL 0.96 on Split Fashion) are far above the Boschini iCaRL values (75.46 to 78.13) and above Joint training in Boschini (84.47); the evaluation protocol (online, per-head or per-sub-task evaluation, memory sizes) is not comparable and the standard deviations in that table are implausible. Treat as NOT comparable; do not cite as a baseline.
- Sleep-like unsupervised replay (Nature Communications 2022, s41467-022-34938-7): could not be read. From a search summary only: a MNIST-then-Fashion-MNIST sequence, baseline 47% overall, with sleep replay 61%, joint about 90%; Split Fashion-MNIST class-IL numbers: **UNVERIFIED**.
- A spiking-network preprint (arXiv 2602.12236) was reported by a search summary as about 80% final accuracy with replay and about 20% without on Fashion-MNIST; I did not read it: **UNVERIFIED**.
- Neuromodulated local-error-signal network (Madireddy et al., arXiv 2007.08159 / 2308.04539) reports single-task online Fashion-MNIST 85.22 (1 epoch) but class-IL only for Split-MNIST and CIFAR; no Split Fashion class-IL number.

## 4. Brain-inspired and local-rule continual learners, with their Split MNIST numbers

All of these use backprop or gradient descent somewhere except where noted; none counts and looks up like L. They are the "brain-inspired" reviewers' list.

### 4.1 Hebbian, no replay

- HebbCL (arXiv 2207.04874), Table 2, Split MNIST (5 tasks x 2 classes), class-incremental, no replay buffer, no generative process, average of 5 runs, end of sequence, supervised: SGD 19.01 (+/- 0.04), L2 18.88 (+/- 0.18), EWC 18.90 (+/- 0.06), Online EWC 18.89 (+/- 0.07), SI 17.94 (+/- 0.57), MAS 17.38 (+/- 4.19), LwF 49.37 (+/- 0.68), EfficientPackNet 99.42 (+/- 0.15), HebbCL 93.25 (+/- 0.38). Split CIFAR-10: HebbCL 40.91 (+/- 0.30); the paper restricts comparison to regularization and parameter-isolation methods because it uses no replay. Note EfficientPackNet is parameter isolation and still reaches 99.42 on MNIST: a reviewer will ask why a count-based method is not at that level. No Fashion-MNIST number in this paper. Unsupervised table (MNIST 25 clusters 74.23 +/- 0.67 cluster accuracy, 10-NN error 6.48 +/- 0.20) is representation quality, not class-IL accuracy.
- Sparse-recurrent DFC (arXiv 2212.04316, Springer Biol Cybern 2023): a local-learning-rule network with Hebbian lateral recurrent weights evaluated on Split-MNIST in domain-IL and class-IL against BP, EWC, SI, with 5 seeds. The text says it "outperforms all other CL algorithms for the majority of accuracies" in class-IL; the final accuracy values are plotted in figures only: **UNVERIFIED** numbers.

### 4.2 Metaplastic binarized networks with engram gating

- Stochastic Engrams (arXiv 2503.21436 v2, Aguilar, Herbozo Contreras, Kavehei; text dated 29 Sep 2026): Table II, class-incremental Split MNIST (5 tasks x 2 classes), no replay, six runs: Vanilla BNN 15.83 (+/- 0.32), engramBNN 72.65 (+/- 1.42), EWC 20.05 (+/- 0.77), SI 9.76 (+/- 1.69), LwF 20.12 (+/- 3.97), XdG 19.74 (+/- 2.45), mBNN 29.94 (+/- 4.71), SDMLP 14.47 (+/- 5.90), CH-HNN 12.08 (+/- 3.17), WSN 8.94 (+/- 2.89). Their experience-replay baseline used a fixed buffer of 2,000 samples (reservoir, 1:1 mix, batch 128) but that applied to the CIFAR-100 part; no replay row for MNIST in Table II. This is a hardware-friendly binarized network so is the nearest "efficient chip" competitor; it reaches 72.65 without replay.

### 4.3 Neuromodulated local-error networks (online, memory-constrained)

- Madireddy et al., arXiv 2007.08159 "Neuromodulated Neural Architectures with Local Error Signals for Memory-Constrained Online Continual Learning". Online (1 epoch, batch 10), 2-layer 400-node MLP on Split-MNIST. Class-IL Split-MNIST, Table 3 (single run): iid-offline 95.93, Fine-Tune 19.65, Online EWC 19.66, SI 19.81, LwF 21.37, A-GEM 50.36, iCaRL 72.49, GSS 53.69, ER-MIR 87.6, CN-DPM 93.81, DER++ 92.34, Ours (transfer w/ MSE) 21.84, Ours (Opt) 78.76. Appendix Table 8 (5 repetitions, mean +/- sd, memory-based methods with buffer = 0.5k samples): iid-offline 95.82 (+/- 0.33), Fine-Tune 19.68 (+/- 0.02), Online EWC 19.92 (+/- 0.35), SI 19.76 (+/- 0.01), LwF 20.54 (+/- 0.64), A-GEM 48.57 (+/- 5.26), iCaRL 72.55 (+/- 0.45), GSS 54.14 (+/- 4.68), ER-MIR 86.60 (+/- 1.60), CN-DPM 93.81 (+/- 0.07), DER++ 92.21 (+/- 0.54), Ours (Opt w/ Split MNIST) 77.25 (+/- 1.02). The DER++ number at only 500 stored samples is an important reference: 92.21 at B=500 on Split MNIST.
- Note the contrast with van de Ven's iCaRL (94.57 at 2,000) versus this paper's iCaRL (72.55 at 500, online single epoch): iCaRL accuracy depends strongly on epochs and budget, so reviewers will not accept a result unless the iteration counts match.

### 4.4 Complementary-learning-systems replay (hippocampus / sleep)

- VAE + modern Hopfield network CLS model (arXiv 2507.11393): Split-MNIST class-IL, MLP readout accuracy: VAE (upper baseline, offline) 95.55%, untrained VAE 8.92%, control VAE sequential with no replay 67.75%, VAE+MHN with replay 89.71% ("within 6% of the UB"). The MHN replay store is a learned associative memory, i.e. memory-based replay in disguise.
- Local sleep replay without an offline phase (arXiv 2609.31630, very recent preprint, not peer reviewed): class-incremental split-MNIST 91.6 (+/- 0.3) % with K = 1000 raw samples in an episodic buffer, six seeds, no offline phase; at K = 200 it gives 83.0 (+/- 1.4) against DER++ 77.1 (+/- 0.9) and BP+ER 68.5 (+/- 2.4); local learner iid accuracy 94.1; "the advantage is largest at small episodic buffers". This still stores raw examples. Useful as the closest sleep-replay comparator and because it reports accuracy versus buffer size K (200/1000/5000).
- Sleep-like unsupervised replay (Nature Communications 2022): not readable, see 3.3.
- BCPNN-based continual learning: two searches returned no paper with Split MNIST or Fashion numbers; I found no reliable source. Gap.
- Counting-based classifier baselines with no matrix multiply in the learning step (naive Bayes, count-min, k-NN / prototype) are not benchmarked in any of these papers on Split MNIST; SLDA (87.30 on MNIST in 2104.10093) is the nearest.

## 5. MLPerf Tiny (arXiv 2106.07597), what it fixes and what counts as fair

Verified from the text.

### 5.1 Image classification task (IC)

- Dataset CIFAR-10, 32x32x3 RGB, 60,000 images, 6,000 per class (five training batches and one test batch of 10,000 each).
- Model: customized ResNetv1 with three residual stacks rather than four, no pooling after the first conv; TFLite model size 96 KB.
- Quality target: 85% top-1. Reference accuracy 86.5% on a 200-image subset of the CIFAR-10 test set, evaluated through the benchmark runner (not the full 10,000 test images). Closed-division submissions must reach the target after post-training quantization.
- Other v0.5 tasks (Table 1): keyword spotting (Speech Commands, DS-CNN 52.5 KB, 90% top-1), visual wake words (VWW 96x96, MobileNetV1 325 KB, 80% top-1), anomaly detection (ToyADMOS, FC-AutoEncoder 270 KB, 0.85 AUC).
- Reference platform: NUCLEO-L4R5ZI, TFLite Micro, bare-metal Mbed, GCC-ARM.
- MLPerf Tiny is inference-only. It has no continual-learning or on-device-training task; the 85% CIFAR-10 target is about frozen models. L's staged learning cannot be scored on it; at most its inference energy and latency can be reported using the same measurement rules.

### 5.2 Measurement rules

- Measurement window covers model inference only; pre- and post-processing are excluded.
- Latency: five runs; each downloads an input stimulus, loads the input tensor and runs inferences for a window; report the median inferences per second (IPS) of the five runs.
- Accuracy: a single inference over the entire set of validation inputs; must meet the quality target for the score to be valid.
- Energy: same as latency, but also measure total energy in the timing window; report micro-joules per inference, median of five measurements.
- Energy monitors supported: STMicroelectronics LPM01A, Jetperch Joulescope JS110, Keysight N6705. Only power delivered to the core is measured; level-shifter power is excluded as framework cost. Only one supply may power the core: "no additional energy supplies, such as batteries, supercapacitors, or energy harvesters may be used". The measurement voltage may be lowered (the paper states that the performance versus energy trade-off is dictated by the voltage and is "one of the key insights of the benchmark").
- Closed division: same model, dataset, quality target as the reference; post-training quantization with the provided calibration set is allowed, retraining and weight replacement are not. Open division: model, training scripts and dataset may change, the same test set is used, no accuracy threshold, but the deviations must be documented.

### 5.3 What counts as a fair energy comparison (derived from the above)

- Same task, same test set, accuracy at or above the quality target (closed) or reported next to energy (open).
- Whole-device energy at the supply, not die-only simulation; inference window only; median of five.
- For an RTL or simulated chip such as L, any energy figure is MODELLED or SIMULATED, not a MLPerf Tiny result. It can only be labelled "MLPerf Tiny methodology, open division, simulated" and cannot be placed in the official results table.
- Training energy is outside MLPerf Tiny; for continual-learning claims the energy of all stage updates (including GPU training for L's design, per the L accelerator rule "training on a GPU") must be reported separately and honestly.

## 6. Does the claim hold? Protocol-by-protocol checklist for the reviewer table

Claim under test: "five stages of two classes, 2,000 images per stage, final accuracy on all classes; about one tenth of the memory of replay, no stored examples."

### 6.1 Protocol the L result should declare (copy from the standards above)

- Scenario: class-incremental (single head over all classes, no task id at test), as in van de Ven. Report Task-IL only as a side remark.
- 5 stages x 2 classes: {0,1},{2,3},{4,5},{6,7},{8,9} for MNIST and the same class order for Fashion-MNIST. State the order; Fashion class pairs {0,1}=T-shirt/Trouser etc. are the ones used by Boschini and Rosasco (consecutive pairs).
- 2,000 images per stage (not the standard 12,000): about 1,000 per class, 10,000 images total, one sixth of the standard stream. State whether the 2,000 are a fixed random subset, whether every image is seen once or multiple epochs, and that the test set is the full 10,000-image standard test set.
- Final metric: accuracy on all 10 classes after stage 5 (a single number); also report the per-stage accuracy curve and per-class accuracy; mean +/- SEM over at least 10 seeds (van de Ven: 20, Boschini: 10).
- No test-set tuning across stages; a validation set from training data (Boschini: 6,000 items).

### 6.2 Rows a reviewer will expect (REQUIRED = reject-level if missing)

| Row | Why | Verified published reference |
|---|---|---|
| Fine-tuning / None (REQUIRED) | lower bound | MNIST 19.90 (+/- 0.02); Fashion 20.11 |
| Joint / offline training (REQUIRED) | upper bound on same 2,000-per-stage data | MNIST 97.94 (+/- 0.03); Fashion 84.47 (full data; must be re-run at 2,000 per stage) |
| EWC, Online EWC, SI (REQUIRED) | standard regularization | MNIST 20.01 / 19.96 / 19.99 |
| LwF | standard | MNIST 23.85 (+/- 0.44) |
| Experience replay at several buffer sizes, e.g. 100, 200, 500, 1000, 2000 (REQUIRED) | the claim is explicitly relative to replay memory | Fashion ER B200 72.54, B500 79.02, B1000 81.39; MNIST iCaRL B2000 94.57; DER++ B500 92.21 (online) |
| iCaRL, DER++, GEM/A-GEM | usual rehearsal set | see sections 1, 3, 4.3 |
| Generative replay (DGR, DGR+distill, BI-R) | no stored images, generator weights instead | MNIST 90.79 / 91.79; 91.30 with 2104.10093 |
| Generative classifier / SLDA (REQUIRED for a no-stored-data claim) | strongest no-stored-data non-replay baselines | MNIST 93.79 / 87.30 |
| Parameter-isolation / counting-like non-gradient baseline (nearest-class-mean, naive Bayes, streaming LDA, k-NN on frozen features) (REQUIRED for a counting chip) | shows the gain is not just easy MNIST | SLDA above; EfficientPackNet 99.42 MNIST (HebbCL paper) |
| Brain-inspired no-replay learners | related work | HebbCL 93.25; engramBNN 72.65; Neuromod 77.25 (opt) |
| Multiple seeds, +/- SEM | statistical | all verified sources do this |

### 6.3 Memory accounting a reviewer will challenge

- Define memory as the total persistent bytes needed to continue learning and to predict: model state plus any stored data plus any generator. Replay with B stored 8-bit images costs B x 784 bytes on MNIST/Fashion (ESTIMATED from 28x28 at 8 bits) plus the network weights (a 784-400-400-10 MLP has 784x400 + 400 + 400x400 + 400 + 400x10 + 10 = 478,410 parameters, ESTIMATED by me: about 1.9 MB as 32-bit floats). So the baseline's weights, not the images, dominate in the 2,000-image budget case; "one tenth of replay memory" must therefore compare like with like (L state vs. baseline weights + buffer), or the claim will be read as a comparison of L's counters with only the image buffer.
- Replay memory at the matched-accuracy buffer: find the smallest buffer for which a replay baseline matches L's final accuracy and state L's bytes as a fraction of that baseline's total bytes. On Fashion-MNIST at 12,000 images per stage the ER curve is 72.54 (B200) to 79.02 (B500) to 81.39 (B1000), joint 84.47: a buffer of 200 images (153 KiB, ESTIMATED) already recovers about 86% of the joint accuracy, so "one tenth" of a 2,000-image buffer (=200 images) is only a strong claim if L's accuracy is at or above ER at B200 (72.54), i.e. L must actually reach roughly 73% or more on 2,000-per-stage Fashion data, with a fair baseline re-run on the same 2,000-per-stage stream.
- Stored examples in a different form (centroids, prototypes, hashed or quantized images, replayed "dreams" generated from counts) are stored data in a reviewer's eyes if they can be inverted to images; say exactly what the sleep/replay phase regenerates from, and whether it is counted in memory.
- The distilled-replay paper shows even 1 image per class (10 images) reaches 0.63 on Fashion (E5) and 0.82 on MNIST: a "no stored examples" system must beat or match this to be interesting, and the true replay competitor at ultra-small memory is Distilled Replay / herded exemplars, not the 2,000-image iCaRL.

### 6.4 Verdict on credibility

- Credible if: L is evaluated Class-IL with single head and no task id; all baselines re-run on the identical 2,000-per-stage stream; the memory comparison includes baseline weights; and final accuracy on Split-MNIST is in the 85 to 95 range (the range occupied by generative replay at 90.79 to 91.79, the generative classifier at 93.79, DER++ at 500 samples 92.21, iCaRL at 2000 samples 94.57). A result below SLDA (87.30) would not be a headline win without a memory or energy argument.
- Not credible if: only fine-tuning, EWC and SI are shown (they all sit near 20 on class-IL and are known to fail; reviewers see them as strawmen); if buffers are compared at one size; or if Fashion-MNIST final accuracy is far above 84.47 (the joint-training ceiling at full data), which would signal a protocol error.
- Energy: no MLPerf Tiny result exists or can exist for L's learning; inference-only simulated energy can be reported next to the MLPerf Tiny rules with the label MODELLED.

## 7. Items that remain UNVERIFIED (consolidated)

- All numbers in the Nature Machine Intelligence 2022 "Three types of incremental learning" paper (blocked).
- Figure C.1 curve values (accuracy of exact replay vs stored examples) in 1904.07734.
- The Nature Communications sleep-replay paper numbers (only a search summary seen).
- The spiking Fashion-MNIST preprint (arXiv 2602.12236) numbers.
- Final class-IL accuracies of sparse-recurrent DFC (arXiv 2212.04316): figure only.
- Any BCPNN continual-learning numbers (no source found).
- The Distilled Replay column assignment in section 3.2 follows the extracted header order; the PDF layout was two-column and I did not view the page image.
- Byte counts and parameter counts in section 3.1 and 6.3 are my arithmetic (ESTIMATED), not from the papers.
- arXiv 2609.31630 and 2503.21436v2 are recent preprints (2026) and not peer reviewed as far as I could tell.

Related: [Notes index](INDEX.md)
