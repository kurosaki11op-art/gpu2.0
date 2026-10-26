---
title: Thinking research 1 - imagination and generation without backprop
tags: [spark, research, papers]
---

# Thinking research 1: "a model it can run forward" (imagination / generation)

Date: 26 Oct 2026. Scope: how to make the chip dream so that dreams keep HOW features combine (Shirt vs T-shirt vs Coat),
using only counting, clauses, sparse codes and local rules (matrix-free, multiplier-free, no backprop in the chip).
Rule for this note: for each paper we say what the mechanism is, what transfers to our rules, what does not, and then invent our own method.
All numbers in sections (a) and (b) are **as reported by the authors** (not re-measured by us). Numbers in (d) are ESTIMATED by us.

Honesty about reading (revised 26 Oct 2026 after the founder asked for full-text reads): PDFs were downloaded from arXiv. "Yes" in the
table means I read every page of the main text and appendix text of that paper (page images through the PDF reader, or the extracted
full text where the image reader hit a request limit; in that case figures were not inspected, only captions and text). "Main text" means the main
paper read fully and the long appendix only partly. "Partly" means selected sections only. Numbers marked "read off a figure" are approximate.
Classics not reachable from this sandbox (the proxy returned 403 or DNS failure for toronto.edu, nature.com, biorxiv.org, ncbi.nlm.nih.gov,
export.arxiv.org): Hinton wake-sleep and RBM/DBN papers, Olshausen-Field sparse coding, Tadros et al. Nature Commun. 2022, Golden et al.
2022, McClelland complementary learning systems. They were NOT read. Substitutes that were reachable and read: the Poon-Domingos sum-product
network paper (arXiv 1202.3732, it compares against DBN/DBM and describes them), the 2019 arXiv preprint of the Bazhenov-group sleep algorithm
(arXiv 1908.02240) and a 2026 follow-up from the same group (arXiv 2606.08447).

## (a) Papers read

| # | Citation | Year | Read fully? |
|---|---|---|---|
| 1 | Shin, Lee, Kim, Kim. Continual Learning with Deep Generative Replay (arXiv 1705.08690) | 2017 | Yes |
| 2 | van de Ven, Tolias. Generative replay with feedback connections (arXiv 1809.10635; preprint of "Brain-inspired replay", Nat. Commun. 2020, journal version not read) | 2018/2019 | Yes (extracted text incl. appendix text; figures not inspected) |
| 3 | Liu et al. Generative Feature Replay for Class-Incremental Learning (arXiv 2004.09199) | 2020 | No (partly) |
| 4 | Krotov, Hopfield. Dense Associative Memory for Pattern Recognition (arXiv 1606.01164) | 2016 | Yes (all 12 pages) |
| 5 | Ramsauer et al. Hopfield Networks is All You Need (arXiv 2008.02217) | 2020/2021 | No (abstract, introduction; 94 pages, mostly appendix) |
| 6 | Santos, Niculae, McNamee, Martins. Sparse and Structured Hopfield Networks (arXiv 2402.13725) | 2024 | Yes (all 21 pages incl. proofs skimmed) |
| 7 | Bricken, Pehlevan. Attention Approximates Sparse Distributed Memory (arXiv 2111.05498) | 2021 | Main text yes; 57-page appendix partly |
| 8 | Hinton. The Forward-Forward Algorithm (arXiv 2212.13345) | 2022 | Yes (extracted text, all sections; figures not inspected) |
| 9 | Millidge et al. Predictive Coding: Towards a Future of Deep Learning beyond Backpropagation? (arXiv 2202.09467) | 2022 | Yes (all 10 pages) |
| 10 | Peharz et al. Einsum Networks (arXiv 2004.06231) | 2020 | Yes (all 12 pages) |
| 11 | Bhattarai, Granmo et al. Tsetlin Machine Embedding (arXiv 2301.00709) | 2023 | Yes (extracted text incl. result tables; figures not inspected) |
| 12 | Hawkins, Ahmad. Why Neurons Have Thousands of Synapses (arXiv 1511.00083) | 2015 | Mostly (theory, learning rules, capacity, discussion, methods; figures and tables only by text) |
| 13 | Kleyko et al. Survey on Hyperdimensional Computing / VSA, Part I (arXiv 2111.06077) | 2021 | No (partly) |
| 14 | Poon, Domingos. Sum-Product Networks: A New Deep Architecture (arXiv 1202.3732) | 2011 | Yes (all 10 pages) |
| 15 | Krishnan, Tadros, Ramyaa, Bazhenov. Biologically inspired sleep algorithm for artificial neural networks (arXiv 1908.02240) | 2019 | Mostly (methods, results 3.1-3.4; later sections and supplement not read) |
| 16 | Bazhenov, Delanois, Krishnan. Not Just After One: Sleep-Inspired Replay Prevents Catastrophic Forgetting After Sequential Tasks (arXiv 2606.08447) | 2026 | Yes (all 4 pages) |
| 17 | van de Ven, Tolias. Three scenarios for continual learning (arXiv 1904.07734) | 2019 | No (downloaded; used only through paper 2) |

Not read (unreachable): Hinton wake-sleep and RBM/DBN originals (only Hinton's own account in paper 8 and the DBN/DBM comparison in paper 14), Olshausen-Field sparse coding (only cited by paper 12), Tadros et al. 2022, Golden et al. 2022, complementary learning systems (only as described in paper 1).

## (b) Paper by paper

### 1. Deep Generative Replay (Shin 2017)
- **Mechanism.** A "scholar" = generator + solver. For each new task a new generator is trained (GAN, WGAN-GP) on a mix of the real current data and samples from the previous generator; the new solver is trained on real pairs plus generated inputs labelled by the previous solver's answer (loss mix ratio r). Motivated by complementary learning systems: the hippocampus as a generator, not a buffer.
- **Numbers (authors).** MNIST: a chain of five scholars each learning from the previous one: 98.81, 98.64, 98.58, 98.53, 98.56 % (Table 1). The paper itself states that the performance equals joint training only "as long as the generator recovers the input distribution".
- **Transfers.** The label of a dream comes from the OLD solver's response, not from the intended class. Replay mixes real new data with dreams of old data at a set ratio.
- **Does not transfer.** A GAN generator trained by backprop; MNIST is the easy case (the authors say high-dimensional pseudo-inputs are the hard part and that earlier pseudo-rehearsal failed there).

### 2. Replay with feedback connections / Brain-inspired replay (van de Ven and Tolias)
- **Mechanism.** Compares three scenarios (task-IL, domain-IL, class-IL). Generative replay (VAE) with distillation (the old model's soft class probabilities at temperature T as targets for the dreams) is the best method; the "Replay-through-Feedback" variant puts the generator inside the classifier as feedback connections to save time.
- **Numbers (authors), split MNIST class-IL:** fine-tuning 19.90; EWC 19.90; SI 20.04; LwF 24.17; DGR 91.24; DGR+distill 91.84; RtF 92.56; offline joint training 97.93 (Table 3). Permuted MNIST class-IL: DGR 92.19, DGR+distill 96.38, offline 97.59 (Table 4). Authors: "only replay-based methods are capable of producing acceptable results" in class-IL.
- **Key sentence for us.** They hypothesise that distillation makes replay "more robust to the quality of the replayed inputs": even when sample quality was visibly poor (permuted MNIST), replay still prevented forgetting. The authors also warn that MNIST is easy to generate and scaling is open.
- **Transfers.** Soft targets: a dream is labelled with the whole score vector of the old model, not a hard class; this carries boundary information even if the dream picture is poor. Our fast table already produces a 10-score vector per input, so a "distilled dream" costs nothing extra to label.
- **Does not transfer.** VAE trained with backprop; temperature softmax (needs exp/divide; we would use integer score differences).

### 3. Generative Feature Replay (Liu 2020)
- **Mechanism.** Split the net into feature extractor and classifier; replay is done in feature space, where each old class is a Gaussian (mean and covariance) from which features are sampled; feature distillation protects the extractor. Argument: feature generation is far easier than image generation; replay in feature space removes the new-class bias of the last layer.
- **Numbers.** I did not record the benchmark table values; the authors report state of the art on CIFAR-100 and ImageNet-subset with a fraction of exemplar memory.
- **Transfers.** Our 6,176-bit code is already a feature space (detectors + pooling). Dreaming there instead of at pixel level is what we do; the lesson is that per-class independent statistics in feature space were enough for them because their feature layer was deep and compressed, while ours is shallow, so independent bits are not enough.
- **Does not transfer.** Gaussian with full covariance (matrix).

### 4. Dense Associative Memory (Krotov and Hopfield 2016)
- **Mechanism.** Replace the Hopfield quadratic energy by E = -sum over memories F(overlap). With a sharp F (power n, or rectified polynomial) the network stores far more patterns than neurons (capacity about N^(n-1) for polynomial energy; they derive K_max = alpha_n N^(n-1)). Retrieval = clamp the visible part, update the unknown part. The power n slides from feature-matching (low n: many memories contribute) to prototype regime (high n: the single best-matching memory dominates). The associative memory is mapped to a one-hidden-layer net with a rectified-polynomial activation.
- **Numbers (authors).** MNIST test error below 1.6 % for n=3 with K=2000 memories; the n=2 case is about 1.6 %; XOR solved with 4 memories in 3 neurons for odd n >= 3.
- **Transfers.** The idea that a SHARP similarity kernel over stored memories separates confusable memories, and that "which memory dominates" is a dial between blurred feature averaging and exact prototype recall. Pattern completion by clamping known bits is a natural generator: clamp class bits and a seed region, let the rest settle.
- **Does not transfer.** Memories are learned by backprop and are real-valued; the energy uses products of overlaps. In binary we can replace overlap by popcount of XNOR and F by a table lookup on the popcount (no multiply).

### 5. Hopfield Networks is All You Need (Ramsauer 2020)
- **Mechanism.** Continuous modern Hopfield energy with log-sum-exp; the one-step update is softmax-attention over stored patterns. Three kinds of fixed points: global average of all patterns, metastable states that average a SUBSET of patterns, and single-pattern fixed points.
- **Numbers (authors).** Exponential storage in the dimension, retrieval in one update with exponentially small error (theory); improvements on multiple-instance learning and UCI tasks (not read in detail).
- **Transfers.** The three fixed-point types describe exactly what our dreams do wrong: independent-bit dreams are the "global average" end (blur between classes). Useful dreams must be single-pattern or small-subset states.
- **Does not transfer.** Softmax and dense float vectors.

### 6. Sparse and Structured Hopfield Networks (Santos 2024)
- **Mechanism.** Replace softmax by sparse transformations (entmax, normmax, SparseMAP); because those losses have a margin, retrieval becomes EXACT (the attractor is the stored pattern, not near it) while keeping exponential capacity. Structured variants (k-subsets, sequential k-subsets) retrieve a mixture of the top-k patterns or contiguous associations, a form of controlled recombination.
- **Numbers.** Experiments on multiple-instance learning and rationalisation; I did not record values.
- **Transfers.** (i) A margin gives exact retrieval: only memories within a Hamming margin of the best one take part, others get exactly zero weight. (ii) "Top-k subset" retrieval is a principled way to recombine k real stored items, which is what worked for us.
- **Does not transfer.** The projection onto a simplex needs sorting and division; but top-k with a popcount margin is multiplier-free.

### 7. Attention approximates Sparse Distributed Memory (Bricken and Pehlevan 2021)
- **Mechanism.** Kanerva's SDM: r fixed random binary addresses (hard locations), a pattern is written into every location within Hamming radius d of it by adding it (as +1/-1 counters) into that location's counter vector; reading sums the counters of all locations within radius d of the query and thresholds. The read weight of a stored pattern is the circle (hypersphere) intersection, which falls approximately exponentially with Hamming distance. Iterating the read (autoassociative) cleans up noisy queries. They give optimal radii for n=64 (e.g. 11 for signal-to-noise, 15 for noise tolerance).
- **Numbers (authors).** Theory plus checks in pretrained GPT2 models; the key finding is the exponential fall-off of circle intersection matching softmax.
- **Transfers.** This is the most hardware-friendly memory in the set: counters, XOR plus popcount against fixed random addresses, thresholds, no multiplies. It stores WHOLE patterns superposed in counters, so the joint structure of the bits is kept (unlike per-bit marginals). Reading with a partially corrupted cue is generation by completion.
- **Does not transfer.** Their analysis assumes random patterns; real images are strongly correlated, so superposition would blur confusable classes unless addresses are chosen (not random) or radius is small. Capacity with correlated data is the open risk.

### 8. The Forward-Forward algorithm (Hinton 2022)
- **Mechanism.** Each layer is trained locally to give high "goodness" (sum of squared activities) on positive data and low on negative data; no backward pass. Negative data can be hybrid images, wrong-label images, or generated by the net itself. In the recurrent MNIST net, negative data = run the net once, take the class probabilities, and choose among the INCORRECT classes in proportion to their probabilities; this makes training much more efficient.
- **Numbers (authors).** MNIST 1.37 % (hybrid-mask negatives), 1.36 % (label-in-input, 60 epochs), 1.31 % recurrent net; CIFAR-10 slightly worse than backprop.
- **Sleep, honestly reported by the author.** The wish was positive phase awake, negative phase generated asleep. An early draft claimed this worked for next-character prediction; Hinton says he could not replicate it and suspects a bug; separating long positive and long negative phases only works with a very low learning rate and extremely high momentum. He calls it "the most important outstanding question about FF as a biological model". He also notes that Boltzmann machine learning fails if many positive updates are followed by many negative updates.
- **Transfers.** (i) HARD negative data: dreams that the model itself finds confusing (a wrong class chosen in proportion to its score) teach the boundary. That is exactly "hard-boundary dreams". (ii) Contrast of positive vs negative with a local rule. (iii) The warning: long separated wake and sleep phases are unstable; interleave.
- **Does not transfer.** Squared-activity goodness, layer normalisation and the weight matrices.

### 9. Predictive coding survey (Millidge et al. 2022)
- **Mechanism.** Hierarchical generative model; top-down predictions cancel bottom-up input; only prediction errors travel up; inference and learning are local (error times activity). The same network works as classifier (bottom-up), generator (clamp the top, run down) and associative memory (clamp any part, relax the rest). They report close theoretical links to backprop.
- **Numbers.** Survey; benchmark values not recorded.
- **Transfers.** One structure, three uses by choosing which units to clamp; error-only updating, like our "write only when wrong". The generation by relaxation (clamp class, let the other units settle by reducing local errors) is the dream procedure we are missing.
- **Does not transfer.** Real-valued units with dense weights and a multiply in every update.

### 10. Einsum Networks / probabilistic circuits (Peharz 2020)
- **Mechanism.** A circuit of sum nodes (mixtures with non-negative weights), product nodes (factorisations over DISJOINT variable sets, "decomposability") and leaf distributions. If smooth and decomposable it supports exact marginals, conditionals (inpainting) and ancestral sampling: at a sum node pick one child with probability equal to its weight, at a product node sample all children. Learning by EM (weights are expected counts). Einsum is only an implementation trick for GPUs.
- **Numbers (authors).** EiNets match the test log-likelihood of RAT-SPNs on 20 binary datasets (Table 1); trained on SVHN and CelebA (128 x 128) with speed and memory gains of up to two orders of magnitude over prior implementations; SVHN samples "rather compelling", CelebA samples "somewhat over-smoothed".
- **Transfers.** The structural answer to our failure: a per-class independent-bit model is a single product node; a tree-structured bit model is one product with local dependence. What is missing is the SUM level: a mixture of many different product models (sub-prototypes) inside each class. Sum-node weights are counts, ancestral sampling is a counted random draw (our xorshift draw below a count), the leaves are our existing 10-bit counters. Conditioning (inpainting a missing region given the rest) is exact.
- **Does not transfer.** The GPU dense einsum formulation, and EM with log-sum-exp (a hard assignment version, "hard EM" = count each example into its best component, needs only an argmax over popcount scores).

### 11. Tsetlin Machine Autoencoder / logical embedding (Bhattarai, Granmo et al. 2023)
- **Mechanism.** Each input variable x_k has a target x_hat_k predicted from the OTHER variables: mask x_k (set it to 1 and freeze it), evaluate a pool of conjunctive clauses (AND of memorised literals; each literal has a graded memory with forgotten/memorised halves), and predict x_hat_k = [sum_j w_jk C_j >= 0] with integer weights per (clause, output). Learning: Type Ia (clause matched and target 1: memorised literals reinforce, 1-inputs step up, 0-inputs step down with probability 1/s), Type Ib (target 1 but no match: erase literals with probability 1/s), Type II (target 0 but clause fired: push zero-valued inputs toward being included so the clause stops firing and reduce the weight). The update probability is proportional to the remaining margin to T (error / 2T). The clauses are human readable ("black", "cup", "hot" define "coffee"); the embedding is sparse (each word uses under ten percent of 500 clauses).
- **Numbers.** They report outperforming GloVe on six classification tasks; I did not read the tables.
- **Transfers (the most direct fit).** A masked autoencoder of this kind is a conditional model p(bit i | all other bits) built only from AND-of-literals and integer weights; running it repeatedly (pick a bit, re-predict it from the others, flip, repeat) is pseudo-Gibbs sampling that keeps how bits co-occur, because every clause is a joint feature. The class can be added as extra literals. Learning uses only counters and random draws, matching our rules. The clause weights allow clauses that REJECT (negative weight), which gives boundary information between Shirt and T-shirt.
- **Does not transfer or is unproven.** Not demonstrated as an image generator by these authors (it was built for words). Pseudo-Gibbs from conditionals is not guaranteed to converge to a consistent joint (reported as a known weakness of pseudo-likelihood models; I have not verified it here). Cost for 6,176 inputs and many clauses needs the event-driven evaluation described in (d).

### 12. HTM sequence memory (Hawkins and Ahmad 2015)
- **Mechanism.** A neuron has many dendritic segments; a segment is a coincidence detector: it fires when at least theta of its s synapses see active cells (e.g. 10 of 2,000 active, theta around 8-10 of 20). With sparse activity the false-match probability is tiny (they give 9.8e-21 for their example). Cells predicted by a segment are primed so that in the next step they win; minicolumns burst when nothing was predicted, which selects a new context-specific cell. A neuron with 6,000 synapses can recognise about 300 patterns (rough authors' estimate).
- **Transfers.** A segment is a clause with a threshold (m-of-n AND), tolerant to noise and cheap (count of matches against a threshold). Context-specific cells inside a shared minicolumn code = the same feature with different context, which is exactly "same bit, different combination". Predicted-cell priming is a local, counter-based way to run a sequence forward (generate next from the current).
- **Does not transfer.** The sequence focus; the paper does not give a static-image generator.

### 13. HDC / vector-symbolic survey (Kleyko et al. 2021)
- **Mechanism.** Bundling (superposition by sum or majority) stores sets; binding (XOR or element-wise multiplication in bipolar form, or permutation) makes role-filler pairs that preserve structure (the "superposition catastrophe" is exactly what bundling alone suffers); unbinding recovers a filler; clean-up memory maps a noisy result to the nearest stored vector.
- **Numbers.** Survey; capacity formulas not recorded.
- **Transfers.** Binary XOR binding and majority bundling are multiplier-free. A dream as "bind(class, feature-role) bundled with ..." keeps combination, and clean-up memory is again a nearest-stored lookup. Our earlier finding that HDC was beaten on digits and sound by L Cortex means we do not need HDC for classification; its value here is the binding operation to hold pairs (position region, local pattern).
- **Does not transfer.** Random hypervectors lose the data's own statistics; generation from bundled class vectors alone reproduces the class average (the same failure as per-bit frequency).

## (c) Synthesis

### Why our generators failed
1. Per-bit class frequency = a single product distribution. Every bit is drawn independently, so pixels of a Shirt collar can disagree with the sleeves. In Hopfield terms (paper 5) it is the "global average" fixed point, in circuit terms (paper 10) a single product node with no sum node above it. A Shirt dream is then a blur lying between Shirt, T-shirt and Coat, i.e. exactly where the decision boundary is, with the wrong label.
2. The tree-structured model adds only pairwise dependence (one parent per bit). The distinctions that matter (long sleeve AND collar AND button line) are higher-order conjunctions; one parent cannot express them.
3. Clauses forced on: forcing a fixed clause on gives the right local feature but ignores the rest, and nothing says which clauses belong together; clauses have no rejecting counterpart, so there is no pressure toward the boundary.
4. Our labels are hard and intended (dream class = intended class). The best published replay (paper 2) labels dreams with the old model's soft output; a bad dream labelled "Shirt" actively teaches the wrong thing near the boundary, while the same dream labelled with the old score vector transfers the boundary.
5. Recombining real images works because it keeps all joint structure and its errors are physically plausible pieces; its problem is memory, not quality.

### What a generator must keep
- Joint structure at higher than pair order: conjunctions of bits (clauses) or whole stored patterns.
- Multi-modality inside a class (many sub-prototypes: long sleeves, short sleeves).
- Boundary pressure: samples near the confusable pair should be over-represented relative to their frequency (hard negatives, paper 8), and labelled softly (paper 2).
- Explicit conditioning: class and partial cues clamp, the rest is completed (papers 4, 7, 9, 10, 11 all give a way).

### Which published ideas fix what
| Failure | Published idea | Our matrix-free form |
|---|---|---|
| Single product, no modes | Sum nodes with count weights (paper 10), SDM stored patterns (7) | K sub-prototypes per class, chosen by counted draw |
| Pair-only dependence | Clauses as joint features, masked prediction (11); thresholded segments (12) | Clause bank predicting each bit from the others |
| Labels at the boundary | Distillation (2), self-generated hard negatives chosen by wrong-class score (8) | Keep dreams with small old-table margin, label with old score vector, update only on disagreement |
| Blur between classes | Sharp kernel / exact retrieval with a margin (4, 6) | Popcount radius with a hard cut; top-k real or stored patterns |
| Memory cost of real exemplars | Feature-space replay (3), superposed counters (7) | Prototypes in the 6,176-bit code, counters not images |

What does not work or is unproven: long positive then negative phases (Hinton's own failed replication, paper 8); GAN/VAE generators (paper 1, 2) are backprop and large; SDM's capacity analysis assumes random patterns; pseudo-Gibbs consistency; none of these papers shows a class-incremental image replay with a counting generator, so the connection to our setting is our extrapolation.

## (d) Our own method sketch

Common setup (all three): Fashion-MNIST in the existing 6,176-bit code, 10 classes, shipped settings (margin 256, 1,500 dreams, 1 night), 3 seeds, SIMULATED, compared with the no-regression rule (digits staged >= 95.5, clothing staged >= 83.3, words clean >= 73.3). Cost numbers are ESTIMATED by us from operation counts and have not been measured. Each is a hypothesis; I expect at most partial success and say where it can fail.

### Design 1 (cheapest, try first): "boundary-distilled dreams" (papers 2 and 8)
- **Idea.** Keep today's dream generator as the proposal. Run each proposal through the OLD fast table (already on chip). Keep it only if the old table's top-2 score gap is below a threshold (a hard-boundary dream), and label it with the old table's whole score vector rather than the intended class. The learning step is the existing rule: update only when the current table disagrees with the stored target (target = the old argmax, plus the old runner-up must stay within the stored gap). No new storage except one small gap counter per dream (dreams are consumed on the fly).
- **Minimal experiment.** Staged Fashion-MNIST (as the 83.3 baseline). Sweep the gap threshold {never reject, reject top 50 %, reject top 80 %}. Log the Shirt row of the confusion matrix and the rate of rejected proposals.
- **Success criterion.** Staged clothing > 83.3 AND Shirt recall up by at least 3 points AND digits >= 95.5 and words >= 73.3 (no regression). Failure is recorded as such if the gain on clothing comes with a loss on words.
- **Cost (ESTIMATED).** Memory: none beyond the existing 84 KB images. Operations: one extra table scoring per proposal (10 classes x active bits, the same cost as one decision, about 264 cycles in the pipelined core), roughly doubling night length; accepted dreams are a fraction of proposals so about 2-5x proposals per accepted dream.
- **Risk.** If every independent-bit proposal is far from the boundary or blurred toward the middle, the filter selects blur (garbage near the boundary). Then Design 1 alone cannot help; it still pairs with Designs 2 and 3.

### Design 2: "counted sub-prototypes with clean-up" (papers 5, 6, 7, 10)
- **Idea.** A two-level generator per class: a sum level of K sub-prototype slots and a product level inside each slot. Learning (hard EM by counting): compare the incoming code to the K slots of its class by popcount Hamming distance; if the best distance is below a radius, add the code to that slot's 10-bit per-bit counters and increase the slot's count; otherwise take the least-used slot and restart it from this code (competitive learning, one pass, local). Dreaming: draw a slot by its count (counted draw), draw bits from that slot's counters, then do 2-3 clean-up steps: each step recomputes which slot the dream is nearest to and re-draws the bits with the largest disagreement (event-driven: only differing bits). Optional top-k mixing: for the two nearest slots, take a contiguous block of rows from the second (the recombination that worked with real images, now from prototypes).
- **Minimal experiment.** K in {4, 8, 16} slots per class. Phase A: dreams only (no real replay) to train a fresh table on the old classes, test on real Shirt, T-shirt, Coat: compare with per-bit-frequency dreams (K=1) and with replay of N real images at the same memory. Phase B: staged accuracy.
- **Success criterion.** For K=8 (memory about 0.5 MB if all slots use 6,176 x 10 bits per slot; see cost), dream-trained accuracy on the three confusable classes within 3 points of real-image replay at the same bytes, and staged clothing above 83.3 without regression.
- **Cost (ESTIMATED).** Memory per class with K slots: K x 6,176 x 10 bits = K x 7.7 KB; K=8 gives 62 KB per class, 618 KB for 10 classes, which is 7x the present 84 KB dream memory and does NOT fit the Tang Nano block RAM (about 103 KB) as is. Reduction options to test in the same experiment: 4-bit counters (3.1 KB per slot, about 250 KB for K=8), or keep a slot only as one stored code plus 1-bit "wobble" mask (772 B per slot, 62 KB for K=8 over 10 classes). The last form is a real-image-like medoid store and is the likely winner on memory; it is close to SDM with few hard locations. Operations per learned example: K popcounts over 6,176 bits (roughly K x 97 words of 64 bits); per dream: a few hundred bit-draws plus cleanup.
- **Risk.** The experiment may show that K must be large (tens) for confusable classes, in which case the memory cost approaches storing raw images (which we already know works but is the memory problem). Then the honest conclusion is "no cheap generator beats stored medoids".

### Design 3: "clause-masked dreamer" (papers 9, 11, 12)
- **Idea.** Learn, with the TM autoencoder rules (Type Ia, Ib, II, integer clause weights, margin T, specificity s), a bank of AND clauses that predict a randomly chosen masked bit from the other bits plus the class literals. Dream: start from the independent-bit dream (or a stored cue), then run S sweeps; at each step pick a random bit, evaluate its clause sum (only clauses that contain that bit's neighbours are re-checked, event-driven: a clause keeps a count of matching literals, and flipping a bit updates those counters only for the clauses that contain that literal), set the bit to the clause-sum sign with a small random noise. Add class literals as clamped bits so the same bank serves all classes; add a contrast phase in the Forward-Forward style: clauses that fire on a dream that the old table says is "wrong class" get a Type II penalty (negative weight), which is a local, counter-only boundary rule.
- **Minimal experiment.** Start small: train only on Shirt and T-shirt (and later Coat), 2,000 images per class, a few thousand clauses with up to 8 literals chosen from the top 1,000 most informative bits (to keep the first test tractable). Measure (i) masked-bit prediction accuracy on real held-out images, (ii) after 20 sweeps, the fraction of dreams on which the old table gives the intended class with margin above 256 (a "dream quality" score), (iii) dream-trained recall on real Shirt.
- **Success criterion.** Dream quality for Shirt at least as high as the real-image-recombination dreams, and Shirt recall in staged learning above the current number (read the baseline from the current confusion matrix before the experiment) without losing on digits and words.
- **Cost (ESTIMATED).** Memory: for C clauses with L literal pointers of 13 bits and an 8-bit weight per output: C x (L x 13 + 8) bits; with C = 20,000 and L = 8 about 280 KB, plus an 8-bit active-literal counter per clause (20 KB) for event-driven evaluation. This is larger than the dream memory and probably needs the PSRAM, not block RAM. Operations per sweep step: a bit flip touches the clauses that contain that literal (average 20,000 x 8 / 12,352 literals, about 13 clauses), so about 13 counter updates plus one sum; a dream of 20 sweeps over 6,176 bits is about 1.6M counter updates ESTIMATED, about 1,000 times a plain independent-bit dream. This might be affordable only for a few hundred dreams per night.
- **Risk.** Highest. Pseudo-Gibbs may not produce coherent images; clause learning on 6,176 inputs is slow; it is untested as an image generator (the source paper is about words). It is the design with the most chance of a real jump, and the most chance of a clean negative result.

### Recommended order and top pick
1. Run Design 1 first: no new memory, a half-day experiment, and it tests the published claim (paper 2) that soft boundary labels make poor dreams useful. It also reveals whether the problem is label/targeting or picture quality, which decides the rest.
2. Run Design 2 with the medoid-plus-wobble-mask memory form: this is the structural fix (the missing sum level, paper 10) and is the best bet to get "real-image quality" at a fraction of the memory.
3. Design 3 only if Designs 1-2 show that bit combinations inside a prototype still need modelling.

Top proposed method: Design 2 with the Design 1 filter on top (counted sub-prototypes + boundary-distilled dreams).

Uncertainty, stated plainly: all three are untested; the papers support the ingredients (mixtures with count weights, soft labels, hard negatives, clause autoencoders, counter memories) but none shows a matrix-free class-incremental image generator. Our earlier negative results (frequency, tree, forced clauses) suggest that the gain, if any, may be only a few points and may not pass the no-regression rule on all three datasets at once. Run each with 3 seeds and record failures the same way as wins.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
