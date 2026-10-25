---
title: Paper notes - generative and feature replay
tags: [l, research, papers]
---

# Paper notes - generative and feature replay

Read on 25 Oct 2026 from arXiv PDFs (pdftotext). Numbers are copied from the papers (their own measurements, on GPUs); nothing here was run by us. Label for everything below: reported by the authors (MEASURED by them), not reproduced.

Paper status:

| Paper | Source | Read |
|---|---|---|
| Shin et al., Continual Learning with Deep Generative Replay | arXiv 1705.08690v3 | main text in full; the supplementary (architectures, hyperparameters) is NOT in the PDF: UNVERIFIED |
| Liu et al., Generative Feature Replay For Class-Incremental Learning | arXiv 2004.09199 | in full, with appendices |
| van de Ven, Siegelmann, Tolias, Brain-inspired replay (Nat. Commun. 11, 4069, 2020) | nature.com only; the page and PDF were blocked (HTTP 403 through the proxy); no arXiv or bioRxiv version found by search | NOT READ. Everything about the final method (context gates, soft targets with internal replay, "replay through feedback" with CIFAR-100 class-IL numbers) is UNVERIFIED. Read instead the two earlier arXiv papers by the same first author, below |
| van de Ven & Tolias, Three scenarios for continual learning | arXiv 1904.07734v1 | in full |
| van de Ven & Tolias, Generative replay with feedback connections (RtF) | arXiv 1809.10635v2 | in full; this is the precursor of the Nat. Commun. paper, and the source for the replay-through-feedback mechanism |

## 1. Deep Generative Replay (Shin et al., 1705.08690)

(a) Mechanism. A "scholar" is a pair: generator G plus solver S. Training task i: the new generator learns the mixture of real inputs x of task i and replayed inputs x' sampled from the previous generator G(i-1); the new solver is trained on real pairs (x, y) plus replayed pairs (x', S(i-1)(x')), i.e. the old solver labels the fake inputs (hard targets). Loss: L = r * L_real + (1 - r) * L_replay, r = mixing ratio, set by the wanted importance of new versus old. No old data is kept; the old scholar is a frozen copy. Generator is a WGAN-GP; any generative model is allowed.

(b) Stored per class: nothing explicit. Only the weights of the previous generator and solver. Pseudo-samples are made at pixel (input) level, because the solver and generator are decoupled: the generated input must look like the real one so that any solver, even a new architecture, can be taught. Replayed labels come from the old solver, not from the generator (not class-conditional).

(c) Results. Only plots, no numeric tables except one: MNIST, a chain of 5 solvers each taught by the previous scholar: 98.81, 98.64, 98.58, 98.53, 98.56 % (Table 1). Other experiments are figures only (numbers UNVERIFIED): permuted MNIST tasks, MNIST to SVHN and back, LwF plus generative replay, and class-incremental MNIST (5 tasks of 2 classes, one per task). Baselines in every figure: GR (generative replay), ER (exact replay: real old inputs, old-solver labels, the upper bound), Noise (Gaussian noise inputs with old-solver labels), None (naive). Findings: GR is close to ER; Noise does not help (Noise keeps the target distribution but not the input distribution, so it forgets); None forgets completely. So the replayed input must come from the old input distribution; random noise is worthless. The approximation of the generator is the only constraint. Ablation of realism is only this ER / GR / Noise axis.

(d) Operations: a GAN plus a solver, full backprop, floating point, at every task; the generator must be retrained on its own samples each task (errors compound over tasks, not analysed). Memory: constant, two networks (sizes in the supplementary: UNVERIFIED).

(e) Limitations (authors and ours). Only MNIST/SVHN-scale; assumes the generator reproduces the input space reliably; the authors list RL and other forms as future work. Quality of the generator bounds everything.

(f) Fit to L. The scholar split (generator, solver, old-solver labels) maps cleanly to L: the "generator" is the counting table itself used backwards, and the "old solver" is the table before the update. Noise result is a warning: L must sample from the learned bit statistics, not from uniform bits.

## 2. Generative Feature Replay (Liu et al., 2004.09199)

(a) Mechanism. Split the network into feature extractor F (ResNet-18 up to the last block) and a linear classifier H (matrix V plus softmax). Algorithm 1: task 1 trains F1, H1 on D1, then trains a feature generator G1 on u = F1(x). Task t: train Ft and Ht on real current data plus generated features u' = G(t-1)(c, z) for all previous classes c; the classifier head is extended to the new classes (single head, task id unknown); a frozen copy of F(t-1) supplies an L2 feature-distillation loss ||Ft(x) - F(t-1)(x)||^2 on current images (coefficient 1) so the extractor does not drift; then train Gt on real new features plus replayed features of G(t-1). Generator variants: (i) "Gaussian class prototypes": one Gaussian per class, mean and covariance of the features; (ii) conditional WGAN with a replay-alignment loss ||Gt(c, z) - G(t-1)(c, z)||^2 so old classes keep producing the same features for the same noise z.

(b) Stored per class: either mean and covariance of the final feature vector, or class-conditioned generator weights (shared, constant size). Level: the last block's linear features (Block 4, the input of the classifier), not pixels and not conv features. Reason given: the distribution of high-level features is much simpler than the pixel distribution, so a small generator trained on little data suffices; and replaying in the head only means the classifier balance problem (bias to the latest classes) is solved for free, since the classifier sees all classes at every step.

(c) Results (all from figures; the PDF text carries no table of final accuracies, so per-point numbers are UNVERIFIED). Protocol: ImageNet-Subset (first 100 classes) and CIFAR-100; half of the classes as task 1, the rest in 5, 10 or 25 equal tasks; also ImageNet-1000 (appendix). Joint training reference: 77.6 (ImageNet-Subset), 72.0 (CIFAR-100). Findings stated in text: without exemplars it beats LwF, EWC, MAS by a large margin; the Gaussian variant already matches iCaRL-NME and beats iCaRL in the 25-task case on ImageNet-Subset; the GAN variant beats Rebalance (exemplar-based, 20 per class) in all ImageNet-Subset settings, gain grows with number of tasks; on CIFAR-100 comparable to Rebalance for 5 and 10 tasks, slightly worse for 25 tasks; on ImageNet-1000 slightly better at 5 tasks and a larger gap at 10 and 25, forgetting lower by more than 10 points.
Ablation, level of replay (Table 2, CIFAR-100, 4 equal tasks, average accuracy after task T1/T2/T3/T4; only the values readable in the text):

| Replay level | T2 | T3 | T4 |
|---|---|---|---|
| Image (MeRGAN, class-conditional GAN) | 37.7 | 17.8 | 9.7 |
| Block 1 | 41.6 | 26.5 | 20.1 |
| Block 2 | 41.0 | 26.5 | 20.0 |
| Block 3 | 51.1 | 37.0 | 26.6 |
| Block 4 (theirs) | 57.6 | 48.2 | 41.5 |

(T1 values: 82.4 for the image row, 80.7 for another row; the column-to-row alignment of T1 is garbled in the text, UNVERIFIED.) So at task 4: pixel replay 9.7 versus last-feature replay 41.5, a gap of about 32 points; shallower features lose, which the authors attribute to harder generation and to head bias. Ablation, regularizer in the extractor (Table 3, with GAN replay): feature distillation 81.9 / 58.4 / 48.8 / 42.2 against EWC+GAN 40.8 / 26.8 / 21.2 and MAS+GAN 40.2 / 26.0 / 20.9 for T2/T3/T4; (T1 for EWC, MAS not readable.) Appendix C: t-SNE of generated versus real features overlap closely. CCA analysis (Fig. 2): forgetting grows with depth; image replay leaves intermediate layers forgetting like fine-tuning.
How realistic must replayed samples be? Even a single Gaussian per class at feature level is competitive with exemplar methods; pixel-level GAN replay fails on CIFAR-100. So realism needed is a coarse class-conditional density at the level where classes are nearly linearly separable.

(d) Operations. Training: SGD/Adam backprop on ResNet-18 (201 epochs per task on CIFAR-100, 101 on ImageNet; GAN 501 / 201 epochs; lr 1e-3 classifier, 1e-4 GAN; Adam); inference needs the full CNN. Generator: two hidden layers of 512 units, LeakyReLU, input = 200-dim noise + one-hot class. Memory (Table 1): ResNet-18 about 45 MB; GAN 4.5 MB constant (equal to 24 ImageNet exemplars) versus 20 exemplars per class: 6.2 MB (CIFAR-100, 2000 images), 375 MB (ImageNet-100), 3.8 GB (ImageNet-1000, 20000 images). The head is a single linear layer, so replay training is cheap. Gaussian variant: mean and covariance per class (covariance is a d x d matrix per class: not quantified by the authors).

(e) Limitations. Needs a feature extractor that is good enough and stays stable: it is kept stable by distillation on current-task images only (so the first task, half the classes, must give good features: protocol gives 50 classes in task 1); feature drift in the extractor is not repaired by replay; weaker on low-resolution CIFAR-100 with 25 tasks; GAN stability; the Gaussian variant assumes unimodal Gaussians (as the authors say of a related method). Backprop and floating point throughout.

(f) Fit to L. This is the closest match to our design: the "feature" is our binary detector code, the "classifier" is the counting table, the Gaussian prototype is a per-class bit-rate vector (plus optional class-conditional mixtures). Result says: replay at the code level with a coarse class model gets most of the gain; pixel replay is not needed. The head-bias argument carries over: a count table updated with only new-class counts is biased toward new classes unless old classes are re-presented.
Concrete small test (proposed, not run): on the L Cortex code for a split benchmark (for example half the classes first, then classes in groups), store per class only the bit-rate vector p_c (one counter per bit) and the class count. When a new group arrives, draw synthetic codes for old classes by independent Bernoulli(p_c) per bit (variants: k-component mixture by clustering counts; sparse-code constraint that fixes the number of active bits to the class mean), and feed them as extra counted events. Compare class-incremental accuracy at the end with (1) no replay, (2) real stored codes (upper bound), (3) uniform random bits (the Noise control of Shin et al.), (4) Bernoulli from p_c, (5) the mixture. Replay budget is a number of events per class per step. Measure also the sampled code against real codes (Hamming distance to the nearest real code). Costs: counters and a random-bit source only, no multiply.

## 3. Brain-inspired replay (van de Ven, Siegelmann, Tolias, Nat. Commun. 2020)

The Nature Communications page could not be opened (403). The following comes from the abstract returned by a search plus the two earlier arXiv papers; anything not in those is UNVERIFIED.

(a) Mechanism, as far as verified from the precursor (1809.10635, "Replay-through-Feedback", RtF): no separate generator. The main network (MLP, 2 hidden layers; 400 units for split MNIST, 1000 for permuted MNIST, plus softmax output) gets feedback connections that reconstruct the input from the hidden representation, with a stochastic latent layer z of size 100 (a symmetric VAE with a classification layer on the last encoder hidden layer). Loss on current data: classification cross-entropy plus VAE loss. On replay: the replayed input is sampled from the model itself (z ~ standard normal, through the decoder), labelled by the previous model copy's soft probabilities (distillation with raised temperature), loss = generative + distillation; current and replay losses are weighted by 1/(tasks seen) and 1 - 1/(tasks seen). The Nat. Commun. paper (per its abstract in the search result, UNVERIFIED in detail) additionally replays hidden representations (not pixels) through the feedback, and uses context-modulated feedback connections; the claim is state-of-the-art class-incremental learning on CIFAR-100 without storing data. We could not verify its components, numbers or ablations.

(b) Stored per class: nothing (the model's weights only). Level: input in the precursor; hidden (internal) level in the final paper (UNVERIFIED), argued by the authors via the brain (cortical feedback, hippocampal replay).

(c) Results, split MNIST class-incremental (Class-IL; model must pick among all 10 digits, task identity not given), mean of 20 runs, from 1809.10635 Table 3: none 19.90; EWC 19.90; online EWC 19.90; SI 20.04; LwF 24.17; DGR 91.24; DGR+distill 91.84; RtF 92.56; offline joint 97.93. Permuted MNIST, Class-IL values in Table 4 of the same paper (not copied). Training time of RtF is roughly half of DGR with a separate VAE (GTX 1080; plot only).

(d) Operations: VAE-style network, backprop, floats; memory is the single model.

(e) Limitations: stated by the authors: MNIST generation is easy and scaling to harder inputs was left open; FearNet (a related method storing per-class mean and covariance of hidden features) is discussed as likely benefiting from stored summary statistics.

(f) Fit: the relevant idea for L is "the model replays itself, from its own hidden level, labelled by its own previous state." For L this is a sleep/dream pass: sample a code from the counted statistics, read the class from the current table (the old table is the "soft target"), and re-count it so that the table's class balance is preserved. Test: as in section 2, but label the dream by the table's own prediction (no stored label) and check that the table stays stable (the replay should be a fixed point) while new classes are added.

## 4. Three scenarios for continual learning (van de Ven & Tolias, 1904.07734)

(a) Mechanism. A protocol paper: Task-IL (task id given at test), Domain-IL (task id not given, not needed), Class-IL (task id not given and must be inferred, i.e. true class-incremental). Methods compared: regularization (EWC, online EWC, SI), XdG (task-gating, Task-IL only), replay: LwF (replay current inputs with the old model's soft labels), DGR (VAE-generated inputs with hard labels), DGR+distill (VAE-generated inputs with soft labels), iCaRL (exemplars, budget 2000), and offline joint training (upper bound) and none (lower bound). Replay loss is weighted by 1/(tasks so far).

(b) Stored per class: nothing for DGR; exemplars for iCaRL. Level: pixels via a VAE (symmetric, 2 hidden layers of 400 units, latent 100; 1000 units for permuted MNIST). Soft versus hard labels is the main ablation.

(c) Results (mean of 20 seeds, accuracy over all tasks). Split MNIST Class-IL: none 19.90; EWC 19.90; online EWC 19.96; SI 19.99; LwF 23.85; DGR 90.79; DGR+distill 91.79; iCaRL (2000 exemplars) 94.57; offline 97.94. Split MNIST Domain-IL: none 59.21; EWC 63.95; SI 65.36; LwF 71.50; DGR 95.72; DGR+distill 96.83; offline 98.42. Split MNIST Task-IL: all methods at or above 98.6 except none (87.19). Permuted MNIST Class-IL: none 17.26; EWC 25.04; online EWC 33.88; SI 29.31; LwF 22.64; DGR 92.19; DGR+distill 96.38; offline 97.59. Conclusions: regularization fails entirely in Class-IL; only replay works; soft targets add about 1 point on split MNIST Class-IL and about 4 points on permuted MNIST Class-IL; stored exemplars (iCaRL, 2000) are 2.8 points above DGR+distill on split MNIST. The authors note that even degraded replayed samples still prevented forgetting on permuted MNIST (1809.10635), and that LwF using real current-task inputs (not the old classes at all) reaches only 23.85 in Class-IL: the replayed input must be of the old classes.

(d) Operations and memory: iCaRL 2000 exemplars versus the VAE; all backprop, Adam (split MNIST: 2000 iterations/task, lr 0.001; permuted: 5000, lr 0.0001), batch 128 current plus 128 replayed.

(e) Limitations (authors): MNIST only; whether generative replay scales to harder inputs is open; hyperparameters tuned per method (noted that a wider search made EWC better in Task-IL than in earlier reports).

(f) Fit: gives L the right benchmark: split into groups, no task id, true class-IL. The numbers above are the yardstick for a MNIST-class test: no replay about 20 %, label-and-sample replay about 91 %, joint about 98 %.

## What this implies for L (summary)

1. Replay without stored images works when the replayed sample comes from the old class distribution; noise inputs do not work (Shin), and replay of only new-class inputs does not work (LwF 23.85 % Class-IL).
2. The level matters more than the realism: replaying the last feature layer with a single Gaussian per class gave results competitive with exemplar methods (Liu), while pixel-GAN replay reached 9.7 % versus 41.5 % at task 4 on CIFAR-100 (Table 2). L's binary code is that feature layer, and a per-class bit-rate vector is its cheapest class model.
3. Shallow, hidden-layer replay is harder than last-layer replay (Liu Table 2): for deep binary gate layers, replay the code that feeds the counting table, not intermediate gate outputs, and keep lower layers frozen (the L code is fixed, which plays the role of their feature distillation).
4. None of the methods is multiplier-free or gradient-free; only the idea transfers.
5. Not verified: the final Nat. Commun. brain-inspired replay paper (hidden-level replay, context gates, CIFAR-100 class-IL numbers).

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
