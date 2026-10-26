---
title: Thinking research 5 - symbols and composition
tags: [spark, research, papers]
---

# Thinking research 5: symbols and composition (binding, roles and fillers, systematic generalisation)

Written 26 Oct 2026, revised the same day after a second, full-text pass (founder's rule: read page by page, not abstracts).
Question: how does published work get composition (new wholes from known parts) out of simple operations, does it stay
matrix-free and multiply-free, how is it learned, how does it scale, and what can L (sparse binary code of local
detectors + clauses = AND of literals + counting tables) take from it without copying?

Rules applied (project instructions): no dense matrix-vector products, no multipliers, no backprop in the chip design.
Allowed: scans, event-driven sparse lookups, table and hash lookups, counters, small state, local rules, clauses, sparse
binary codes. All numbers about papers are "as reported by the authors" (their MEASURED or SIMULATED results on their own
hardware or data); we reproduced nothing. Numbers about L come from `docs/PROJECT_MEMORY.md` (SIMULATED). Numbers marked
ESTIMATED are our arithmetic on stated assumptions. Paper text is treated as data, not instructions.

## How the papers were read (honest statement)

PDFs from arXiv, converted with `pdftotext`, read in the terminal in line ranges. "Full" below means the whole main text and
the appendices that carry text were read; references, long result tables of numbers and figure contents were not.
"Main text" means the body was read in full but an appendix (grammar, hyperparameters, extra tables) was only searched.
"Partly" means abstract, introduction, method and the main result section only.

Unreachable, even after a second try: Plate's HRR papers and book (not on arXiv; publisher hosts), Kanerva's 2009
"Hyperdimensional computing: an introduction" (the only copies found were on `cs.uwaterloo.ca` and
`redwood.berkeley.edu`; the proxy returned 403 for both, so I did not retry or bypass), Smolensky's 1990 tensor product
paper (not on arXiv), Gayler's 1998/2003 papers (not on arXiv). Substitutes that are on arXiv and were read in full:
Smolensky et al. 2022 for tensor product representations (TPR), the two Kleyko surveys and Frady et al. for Plate/Kanerva/
Gayler content, Hawkins and Ahmad 2015 for HTM. Not read at all: the neuroscience literature on binding by synchrony and
hippocampal conjunctive coding (statements about it come only through the surveys and are marked "via survey").

## (a) Papers read

| # | Citation | Year | Read fully? | What was read |
|---|---|---|---|---|
| 1 | Kleyko, Rachkovskij, Osipov, Rahimi. HDC/VSA survey Part I. arXiv 2111.06077 | 2021/23 | **Yes** | all sections 1 to 5 (references excluded) |
| 2 | Kleyko et al. HDC/VSA survey Part II. arXiv 2112.15424 | 2021/23 | **Yes** (main text) | sections 1 to 5 incl. open issues; first ~120 lines (table of contents, comparison table) skimmed |
| 3 | Frady, Kent, Olshausen, Sommer. Resonator networks part 1. arXiv 2007.03748 | 2020 | **Yes** | all |
| 4 | Kent, Frady, Sommer, Olshausen. Resonator networks part 2. arXiv 1906.11684 | 2020 | **Yes** | all incl. appendices A to J (derivations read, not re-derived) |
| 5 | Frady, Kleyko, Sommer. Variable binding for sparse distributed representations. arXiv 2009.06734 | 2020/21 | **Yes** | all incl. appendices |
| 6 | Hersche, Zeqiri, Benini, Sebastian, Rahimi. Neuro-vector-symbolic architecture for Raven's matrices. arXiv 2203.04571 | 2023 | **Yes** (main text and Supplementary Notes 1 to 5) | tables of per-constellation numbers only skimmed |
| 7 | Saha, Granmo, Zadorozhny, Goodwin. Relational Tsetlin machine. arXiv 2102.10952 | 2021 | **Yes** | all incl. complexity section and experiments |
| 8 | Lake, Baroni. Generalization without systematicity (SCAN). arXiv 1711.00350 | 2018 | Main text yes | experiments 1 to 4, discussion; appendix grammar not read |
| 9 | Lake. Compositional generalization through meta sequence-to-sequence learning. arXiv 1906.05381 | 2019 | Main text yes | all experiments; appendix figures not read |
| 10 | Petersen, Borgelt, Kuehne, Deussen. Deep differentiable logic gate networks. arXiv 2210.08277 | 2022 | Main text yes | sections 1 to 7; supplementary material is not in the PDF |
| 11 | Petersen, Kuehne, Borgelt, Welzel, Ermon. Convolutional differentiable logic gate networks (LogicTreeNet). arXiv 2411.04732 | 2024 | Main text yes | sections 1 to 6; appendix not read |
| 12 | Smolensky, McCoy, Fernandez, Goldrick, Gao. Neurocompositional computing. arXiv 2205.01128 | 2022 | **Yes** | all (stand-in for Smolensky 1990) |
| 13 | Hawkins, Ahmad. Why neurons have thousands of synapses (HTM sequence memory). arXiv 1511.00083 | 2015/16 | Main text yes | through Discussion; Materials and Methods (formal learning rules) not read |
| 14 | Mao, Gan, Kohli, Tenenbaum, Wu. Neuro-Symbolic Concept Learner. arXiv 1904.12584 | 2019 | Main text yes | all of sections 1 to 5; appendices not read |
| 15 | Locatello et al. Slot Attention. arXiv 2006.15055 | 2020 | Partly | abstract, method, object-discovery results |
| 16 | Ellis et al. DreamCoder. arXiv 2006.08381 | 2020 | Partly | abstract, introduction, text-editing result |
| 17 | Chollet. On the measure of intelligence (ARC). arXiv 1911.01547 | 2019 | Partly | core priors, ARC definition, solution strategies |
| 18 | Karunaratne et al. In-memory hyperdimensional computing. arXiv 1906.01548 | 2020 | Partly | abstract, operations, energy table |
| 19 | Renner et al. Visual odometry with neuromorphic resonator networks. arXiv 2209.02000 | 2022/24 | Partly | abstract, results summary |

Papers 15 to 19 are the ones still only partly read; none of the three designs below rests on them.

## (b) Per paper

### 1. Kleyko et al., survey Part I (read fully)

Mechanism. A hypervector (HV) is a long random vector; random HVs are quasi-orthogonal and act as atomic symbols. Three
operations make structure: superposition/bundling (add then threshold, or OR), binding (a multiplication-like operation
that destroys similarity to its inputs: XOR for binary spatter codes, element product for MAP, circular convolution for
HRR, outer product for TPR, AND/context-dependent thinning for sparse binary codes, block-wise index addition for sparse
block codes) and permutation (fixed shuffle for position/role). Records are bundles of bind(role, filler); sequences are
bundles of permuted items; images are bundles of bind(position, feature); graphs are bundles of bind(node, node). Reading
out = unbinding followed by clean-up (nearest neighbour in an item memory). Binding must not be associative with bundling,
or the superposition catastrophe returns. The survey separates unstructured similarity (kept by bundling) from structured
similarity (kept by binding, multiplicatively: similarity of two bindings is the product of the part similarities).

Key numbers (survey text). Capacity by a Gaussian detection formula, best decoding 1.2 to 1.4 bits per component; sequence
recovery matches theory at D = 256, N = 64. Dense HV dimension 1,000 to 10,000. The survey states that HDC on raw MNIST
pixels is below a kNN or a two-layer network.

Transfers to L. (1) L's 4,608-bit code already is a sparse binary distributed representation (SBDR); the survey says
sparse codes allow inverted indexing, which is L's event-driven decision. (2) The bit position is already role (pooled
location) x filler (detector id) in localist form. (3) Bloom filter = OR-bundle; hash binding of L's lookup core is the same
family. (4) Sparse block code binding is integer index addition modulo the block size. (5) XOR binding needs only gates.
(6) Fractional power / correlated "level" codes (thermometer-like flips) give similarity-preserving scalars.

Does not transfer. HRR convolution, FHRR complex product, tensor products, matrix binding (MBAT): multiplies or matrices.
Dense clean-up is an N x D dense matrix-vector product; only event-driven row addition over a sparse code fits our rules.
The encoder from pixels to HVs is outside HDC and is the weak point.

### 2. Kleyko et al., survey Part II (read fully)

Mechanism. Reviews uses. Finite-state machines as bundles of bind(input, state, permute(next)); controllers as bundles of
bind(sensor set, action set); n-gram language identification (permute-bind per letter, class centroids); database records
and "holistic transformations" (one transformation HV from a few example pairs, applied to new records without decomposing
them, "Dollar of Mexico"); analogical retrieval and mapping; Raven's matrices; visual question answering; Spaun, associative-
projective networks (SBDR, cores and fringes), HTM, LIDA. The closing section lists open problems.

Key numbers (as cited). Visual analogy on CNN-derived binary HVs: 98 % correct on unseen automobile images. Trainable VQA
model: 100 % on five trained questions, 60 to 72 % on unseen ones. Text and sensor classification tables: centroid classifiers,
mostly small gains over weak baselines, always with a feature front end.

Statements that matter for us (all from the open-issues section). (i) "Similarity: in many models the result of binding
is not similar as soon as a single input is dissimilar ... the price is weak or no similarity in the resultant HV that
includes the same HVs in slightly different combinations." This is the mechanism behind the 0 % held-out result of paper 6.
(ii) "List memories provide reliable retrieval, but are problematic for generalization." (iii) "Parsing: how to parse raw
sensory input into a part-whole hierarchy" and "Learning the transformation of input data into HVs" are open; the survey
says that when HDC transforms data to HVs "machine learning is used rarely, if at all". (iv) HDC and neuro-symbolic AI are
"rather separate fields".

Transfers to L. (a) Centroid + refinement classification = L's counting table with surprise-gated writes; no gain. (b)
Record query by unbinding, holistic transformation as a single XOR pattern bundled over examples: counting in the XOR domain.
(c) Cores and fringes of associative-projective networks = bits common to many instances (prototype) versus rare bits:
what L's dream counts store. (d) The analogy hierarchy gives an evaluation ladder.

Does not transfer. The transformation HV in the cited HRR work is learned by gradient descent; most demos assume symbols are
given; no demonstration scales to large analogical episodes.

### 3. Frady et al., resonator networks part 1 (read fully)

Mechanism. A composite s = x * y * z (element products of codewords from codebooks) is factored by keeping one estimate per
factor, initialised to the superposition of its whole codebook; each step unbinds the other estimates from s, cleans up
against the codebook and re-thresholds: x_hat = sign(X X^T (s * y_hat * z_hat)). Search in superposition tests all
combinations at once; the right ones "resonate". Scenes bundle objects (colour x digit x vertical x horizontal); decoded one
at a time with explaining away (subtract the found object, reset).

Key numbers (authors). 23 atomic symbols give 630 object types and 250,444,530 possible 1-3 object scenes; N = 500 is
enough; a two-hidden-layer network trained with backprop on 100,000 images produced scene vectors, tested on 10,000. Tree
search with five factors works.

Transfers. Peeling: find a part, remove its evidence, look again. The paper's own point: sensing is unbinding (Feldman).
Does not transfer. X X^T is a dense product; bipolar element products; backprop front end; no convergence guarantee.

### 4. Kent et al., resonator networks part 2 (read fully)

Mechanism. Same dynamics analysed. Each iteration is a "bipolarised alternating least squares" step; the sign non-linearity
keeps the state at hypercube corners and avoids spurious fixed points, which is argued (section 6.6) to be why six
optimisation baselines fail. Outer-product (OP) weights give an integer matrix, "no floating point", but still a matrix
product per iteration.

Key numbers (authors). Operational capacity (99 % total accuracy within 0.001 M iterations): about two to three orders of
magnitude above all benchmarks for F = 3 and 4; scales as a quadratic in N for F = 2 to 7; fit M_max about 8.078 N^2 / F^1.268
for F >= 3 (the authors flag this fit as noisy); highest with balanced codebooks, lower if one codebook is 10 to 20 times
larger. Speed test (N = 1500, F = 3, D_f = 40): resonator always solved, benchmarks about 70 %; per-iteration cost about 5x
lower. Brute force for F = 4, D_f = 100, N = 10,000 would need about 125 GB. With M well below capacity the network
still factors a composite with up to 30 % of bits flipped. Hopfield-like stability: OP resonators match Hopfield stability for
D_f / N <= 0.056, are less stable above (percolated noise). Three regimes: converges to the right answer; wanders (no
convergence); saturates with spurious fixed points. Not guaranteed to converge.

Transfers. Planning numbers: a code of N bits supports search spaces of order N^2 / F^1.27; for clothing (hundreds of
combinations) a few thousand bits are plenty. Capacity ends at a cliff.
Does not transfer. Dense bipolar; sparse-code capacity must be re-measured; iteration is a matrix product (cost per
iteration about F x D_f x N additions, ESTIMATED, if the two codebook matrices are kept separate as the paper advises).

### 5. Frady, Kleyko, Sommer, variable binding for sparse distributed representations (read fully)

Mechanism. Compressed sensing shows that the Hadamard product of two dense vectors equals the tensor product of the
corresponding sparse vectors (needs N > about 140 in their test), and that a "protected sum" is the concatenation of sparse
vectors; so dimension-preserving binding must reduce the tensor to a vector. Two sparsity-preserving binders: SPTP (random or
diagonal sub-sampling of the outer product with a threshold, fan-in N/K, lossy, needs coincidence detectors, i.e. AND of pairs)
and local circular convolution (LCC) on sparse block-codes: per block, add the two active indices modulo the block size.
LCC unbinding is lossless and keeps sparsity exactly; its cost is order N.

Key numbers (authors). LCC beat circular convolution, Hadamard and SPTP in unbinding correlation at all sparsities. The
"dollar of Mexico" analogy works with sparse block-codes; accuracy follows the dense-VSA capacity theory with signal-to-
noise s^2 = N/R^2 for R key-value pairs (the transformation vector contains R^2 cross terms). Classification with a block-code
VSA (random hidden layer + ridge regression readout, similarity-preserving block shifts for scalars) on 121 UCI datasets: mean
accuracy 0.80 for both dense and sparse versions, about 500 neurons sparse versus 750 dense, versus 0.82 for random forest.
Block-code entropy is K log(N/K) bits, much smaller than for unconstrained K-sparse codes; Hebbian block-code associative
memory capacity is nearly as high.

Transfers to L. This is the matrix-free binder we want: index addition modulo a block, or AND of two bits (coincidence).
Block structure is what competitive detectors already produce (one winner per group of detectors, "winner by XNOR + bit
count"); L's code could be read as a block code with one winner per detector group. The note "concatenation is not binding"
warns that stacking two part codes side by side does not bind them. Similarity-preserving scalar code = shift of the hot
index per block, no multiplier.
Does not transfer. The classifier uses ridge regression readout (matrix solve) and the unbinding in the implementation uses
FFT; the classification result is on tabular features, not images.

### 6. Hersche et al., neuro-vector-symbolic architecture (read fully)

Mechanism. A ResNet-18 is trained (backprop) so that its 512-d output equals the bundle of per-object vectors, where each
object vector is the Hadamard product of its attribute vectors (type x size x colour x position; a dictionary of up to 6,600
combinations, frozen). Decoding takes cosine similarities with the dictionary (a dense 6,600 x 512 matrix-vector product) and
marginalises to per-attribute probability mass functions. The backend maps PMFs to sparse block codes (d = 1024, kappa = 4
blocks), uses fractional power encoding for ordered attributes and binding/unbinding to test rules (constant, progression,
arithmetic, distribute-three) "in superposition", with an associative memory search over n codewords (O(n) instead of
O(n^3)).

Key numbers (authors). RAVEN 87.7 %, I-RAVEN 88.1 % end to end; with ground-truth attribute labels for perception 98.5 % and
99.0 %; reasoning backend 244x faster than the unrestricted symbolic one on the 3x3 grid (63.2 min against 15,408 min for
2,000 tests) and memory below 10 GB; PGM 68.3 %. Perception panel accuracy 99.76 % with the additive cross-entropy loss, 97.16
% with only 6,000 training samples. Unseen attribute-rule pairs (rule never seen on that attribute, I-RAVEN left-right): 81.7 to 100 % for NVSA
against about 22 to 39 % for LEN and CoPINet in most columns (a few baseline entries are higher; the table text was garbled by extraction). Visual analogies A:B::alpha:beta solved at 100 % by binding the
network outputs (relation = q_A * q_B, apply = * q_alpha), including one-to-many analogies.
**Held-out combination tests (Supplementary Note 1b and 1c), the key result for us:**
 - Unseen attribute-value combinations inside one object (train: objects having value in set V_i OR set V_j; test: neither):
   multiplicative binding of quasi-orthogonal vectors 0.0 % on all six attribute pairs. The authors explain it: each output
   entry encodes one memorised combination, and train and test combinations are mutually exclusive.
 - Multiplicative-additive encoding (object = bundle of key * value pairs) with hyperspherical regression for ordinal values:
   position-colour 34.8 %, position-size 15.1 %, colour-size 29.3 %, colour-type 72.0 %, position-type 0.0 %, size-type 0.0 %.
   The authors suspect the spatial structure of CNN filters for the two zeros.
 - Unseen combinations of several objects (multiplicative binding is fine here): 2x2 grid, training with single objects only
   gives 92.4 % (2 objects), 68.1 % (3), 19.3 % (4); training with 1-2 objects gives 97.1 % on all test settings (OOD average
   97.3 %). 3x3 grid, training on 1-4 objects reaches 86.3 % average, 67.8 % at 9 objects.

Transfers to L. Two compositions must be kept apart. (A) Composition of whole objects into sets (bundle of bound tuples):
generalises over object count with a little data. (B) Composition of attributes inside one object: a one-readout-per-
combination code fails completely (0 %), an additive key-value code fails partly (0 to 72 %). So a design that must recognise
new attribute combinations has to read each attribute separately (design 1). The backend shows sparse block codes at 1,024 bits
with 4 blocks are enough for rule detection.
Does not transfer. ResNet-18 + backprop + REINFORCE; softmax and cosine; a dense dictionary matrix-vector product; PMFs are
real-valued weighted superpositions (weights = multiplies). The 0 % result is for a CNN readout; whether a counting table behaves
the same is exactly what design 1 tests.

### 7. Relational Tsetlin machine (read fully)

Mechanism. A Tsetlin machine learns conjunctive clauses (AND of literals and their negations) with one Tsetlin automaton per
literal (include/exclude, local state counting); clauses vote with polarity, the sum is clipped to a target T; Type I feedback
(frequent patterns, reinforce include when clause fired and literal true, probability (s-1)/s) and Type II feedback (add
discriminating literals when the clause fires on the wrong class). The relational version maps every ground atom (for example
MoveTo(William, Office)) to a Boolean input, then **replaces constants by variables in order of appearance** (the entities
in the question are renamed first: Per1, Loc1 ...), so a clause such as Q(Per1) AND MoveTo(Per1, Loc3) never sees names.
A convolution over all permutations of the free variables handles the existential quantifier ("there exists a patch that makes
the clause true"). Atoms are bounded by O(z^w) (variables z, arity w) instead of growing with the number of constants; features
scale as r^(e+1) per sample.

Key numbers (authors). One bAbI-style task (single supporting fact, at most 3 statements, 5 locations): 94.83 % with constants,
99.48 % with entity generalisation (reported F-score 92.53 for the generalised model, which the paper does not explain); knowledge
base about 10x more compact. Noise in training data: 99.48 / 98.79 / 98.24 / 97.02 / 95.08 % at 0 / 1 / 2 / 5 / 10 % error.
Convolution over variable permutations needed up to 1.5x fewer clauses. Cost model with alpha (AND), beta (add), gamma (automaton
update): per sample (2o+1) m gamma + 2o m alpha + (m-1) beta, times v! for v free variables.

Transfers to L. The mechanism is exactly the abstraction we lack: identity-free clauses over slots. Clause logic, include/exclude
counters and voting are all within our rules. The "existential" clause evaluation is a patch scan, as in L's earlier weight-shared
clauses. The method works because the symbols were already given as atoms.
Does not transfer. Relations and entities come from a hand-built extraction pipeline; the permutation loop multiplies the cost by v!;
no experiment holds out entity combinations to separate memorising from abstracting (the paper claims unseen names work, but does not
measure it separately); toy data only; no pixels.

### 8. Lake and Baroni, SCAN (main text read)

Mechanism. Navigation commands to action sequences; 20,910 commands from a small grammar; tests zero-shot generalisation of seq2seq
RNNs. 180 architectures x 5 runs each.

Key numbers (authors). Random 80 % split 99.8 % (best), but only 5 % with 1 % of commands, 54 % with 2 %, 93 % with 4 %. Length
split: best net 20.8 %, overall-best 13.8 %, 23.6 % with an oracle for output length. "Turn left" held out as primitive: 90.3 %
(because the action LTURN appears in training in other commands); "jump" held out: best 1.2 %, overall-best 0.08 %; adding composed
"jump" commands in training: 8 gives 38.3 %, 16 gives 77.8 %, 32 gives 88.4 %. Translation: after "I am daxy" repeated 1,000 times,
1 of 8 new constructions right (22 predicates seen on average in these constructions), while "tired" (80 contexts) is 8 of 8; with
1 or 10 repetitions 0 of 8. The nearest-neighbour table shows that "jump" never became similar to "run/walk/look".
The authors' recommended routes: learning-to-learn over many environments, modular functions for modifiers, differentiable memory.

Lessons. Generalisation appears only where the part has been seen **in compositions** (turn left versus jump); sample efficiency
of systematicity is bad. The splits are a template for held-out tests.
Does not transfer. LSTMs and backprop; language not images.

### 9. Lake, meta seq2seq (main text read)

Mechanism. Training episodes each give a support set (input-output pairs, primitives randomly re-assigned to meanings) and queries;
the network stores support pairs in a key-value memory (attention) and answers queries with an LSTM decoder. After meta-training
no weight update occurs at test time. A "support loss" (also reconstruct the support items) is needed to force memory use.

Key numbers (authors). Mutual exclusivity 100 %. SCAN add-jump 99.95 % (SD 0.08) with 23 random primitive permutations in
meta-training against 0.03 % plain, 78.4 % syntactic attention; without support loss 5.43 %, without decoder attention 10.32 %;
augmented with 20 extra primitives 98.71 % (plain 12.26 %); "around right" 99.96 % (plain 0.0 %); length 16.64 % (plain 7.71 %,
syntactic attention 15.2 %). Training under 1 hour on one GPU. The author states "variables" here need familiarity with all
symbols during meta-training; genuinely new symbols and longer outputs remain unsolved.

Transfers to L. The training distribution does the work: a fixed identity mapping lets the model memorise; randomly changing
which symbol means what forces it to use relations and a lookup of the support set. The support set is a lookup memory.
Does not transfer. LSTM encoder/decoder, soft attention, backprop through episodes.

### 10. Differentiable logic gate networks (main text read)

Mechanism. Layers of 2-input gates with fixed pseudo-random wiring; each gate picks one of 16 Boolean functions. Training relaxes
each gate to a softmax over 16 real numbers and each function to a real polynomial (AND = a*b, XOR = a+b-2ab), trained with Adam;
after training the most likely function is hard-coded. Class score = bit count over a group of output gates; connections are
reproducible from one seed so only 4 bits per gate are stored.

Key numbers (authors). MNIST 97.69 % (48K gates, 625 ns CPU) and 98.47 % (384K gates); more than 1 M images/s on one CPU core above
97.5 %; more than 10x fewer binary operations than the fastest binarised net at 98.4 %. CIFAR-10 (2- to 5-bit inputs) 51.27 % to
62.14 % (48K to 5.12M gates). MONK's problems 100 / 90.9 / 97.7 % (neural network 100 / 100 / 93.5). Adult 84.8 %, Breast Cancer 76.1 %.
Training of a 5M-gate net took about 90 hours on one GPU (from paper 11). In the last layer the most frequent gates are XOR and XNOR;
implications are rare; the first layer favours AND/NAND/OR/NOR; middle layers use "pass A/B/not A/not B". The related work cites a
counting-based lookup network ("memorization") reaching 90 % on MNIST 0-4 versus 5-9.

Transfers. Inference is only bit logic: fits our rules, and XNOR/XOR as the most common learned late gate supports **relation
literals** (design 3): the net itself prefers comparing two earlier features. Bit-sliced batching (64 samples in an integer) and
"250 gates per core per cycle" are implementation facts.
Does not transfer. Training is gradient descent through real-valued multiplications; no systematic-generalisation test.

### 11. Convolutional logic gate networks, LogicTreeNet (main text read)

Mechanism. Convolution with shared logic-gate trees of depth 2-3 (each tree sees two input channels), logical OR pooling, residual
initialisation (gate "pass A" starts at 90 %). Hardware cost measured in gates.

Key numbers (authors). CIFAR-10 86.29 % with 61 M gates (29x fewer than the SOTA at equal accuracy), 84.99 % with 28.9 M, 80.17 % with
16.0 M gates at 24 ns per image on an FPGA, 71.01 % with 3.08 M. MNIST 99.35 % (1.27 M gates). Ablations (L model): no OR pooling
81.45 %, Gaussian instead of residual init 76.18 %, 8 input channels per tree 83.53 %, shallower trees 80.98 to 84.13 % (against
84.99 %). A 5M-gate plain net needed 90 h; their kernels are about 200x faster per gate.

Transfers. Position-shared boolean trees + OR pooling is the weight-sharing idea we tested (+0.2 to +0.4 on L's code). "Gates" is the right cost unit.
Does not transfer. GPU backprop; CIFAR scale; no composition test.

### 12. Smolensky et al., neurocompositional computing (read fully; stand-in for Smolensky 1990)

Mechanism. A structure is a set of filler:role bindings; in a tensor product representation each filler and each role is a vector,
binding is the outer product, aggregation is the sum, so one filler vector (for example "lock") keeps its identity in different
roles ("un-lock", "lock-able"): "TPRs disentangle what and where". Compressed TPRs give HRR, MAP and others. Second-generation models
(NECSTransformer, StoryNet, CaptionNet, ProgNet) learn role and filler vectors by backprop.

Key numbers (authors). Copy five digits with all n-in-n sequences (digit n in position n) withheld from training: of 100 trained models,
none of the LSTM variant learned the task perfectly, about one third of the Transformer variant, over two thirds of the TPR variant; the
LSTM errs by shifting neighbouring digits. StoryNet (bAbI) beat the previous state of the art more the fewer subtasks each character name
was seen in. ProgNet produced Lisp programs up to 55 commands perfectly. A GRU trained on SCAN that generalises well has an internal
encoding that is well approximated by a TPR; editing it (subtract "twice", add "thrice") changes outputs accordingly.

Transfers. (1) The held-out n-in-n copy test is a clean template: a filler never seen in a given role. (2) Evidence that networks that
generalise compositionally use additive role-bound parts. (3) "Same filler vector in different roles" is what position sharing gives.
Does not transfer. Outer products and learned continuous role vectors; backprop; compression via linear maps; the paper's own list of
limits (no embedding of structures inside structures yet).

### 13. HTM sequence memory (main text read)

Mechanism. A neuron has many dendritic segments; each segment is a coincidence detector: it fires when at least theta of its s synapses
(typically 15 to 40 synapses, theta 8 to 20) see active cells. Each segment stores one learned pattern, so a neuron with ~6,000 synapses
recognises ~300 patterns. Mini-columns (2% active, 40 of 2048) share a feedforward response; the cell chosen within the column depends on the
learned temporal context, so the same input has a different sparse code in different contexts (ABCD versus XBCY). Learning is local Hebbian
growth of "permanence" scalars that turn binary synapses on above a threshold; the model uses binary activations and binary synapse weights.
The false-match probability is the hypergeometric formula (example 9.8e-21 for 10 synapses over a 2,000-of-200,000 pattern).

Key numbers (authors). 2048 columns x 32 cells x 128 segments x up to 40 synapses; on a designed stream where 50 % is the best possible
accuracy, the high-order network reaches 50 % and a first-order one 33 %; minimal loss up to about 40 % cell death; capacity example about
320,000 transitions ((32/0.02) x 200 patterns); doubling the synapses per pattern gives 50 % noise tolerance at error 1.6e-18.

Transfers. A clause with a threshold ("at least theta of s literals true") instead of strict AND is noise tolerant and keeps false matches
negligible when the code is sparse: a drop-in variant of our clauses. Context-dependent codes through selecting a cell per column are a binding of (input, context) with no vector algebra, and a template for
role-dependent codes. Local rules, binary weights, no multiplies.
Does not transfer. It models sequences, not role-filler composition; no composition benchmark; the survey (paper 2) claims HTM can implement
HDC binding and bundling, but I did not read that source.

### 14. Neuro-Symbolic Concept Learner (main text read)

Mechanism. Detected objects get ResNet features; each attribute (shape, colour) is a separate neural operator into its own embedding space,
concepts are vectors compared by cosine; a parser (GRU, REINFORCE) turns questions into programs (filter, relate, count, exist, query)
executed softly as attention masks over objects. Four-stage curriculum: object concepts first, then relations, then complex questions.

Key numbers (authors). Trained on 5K images (<10 % of CLEVR) with no program labels; concept accuracy about 99 %; count-based concept test mean 98.7
against 90.6 to 96.5; data efficiency (10 % data): NS-CL 98.9 against 51 to 68 for baselines, which need the full data (about 99) (Table 3, row order
partly garbled by text extraction); CLEVR-CoGenT 98.8 % (A) / 98.9 % (B) once attributes are separate operators (a joint model overfits shape to
colour); learning a new colour from 100 images 93.9 %; scenes and programs larger than in training "almost perfect"; image-caption retrieval 97.0 %.

Transfers. Separate attribute spaces remove the colour-shape shortcut and make a held-out combination work. A small fixed program over parts (filter/count) is lookup
and counting. Curriculum (simple parts first) matches L's staged day.
Does not transfer. CNN features, Mask R-CNN proposals, cosine and sigmoid with learned scalars, REINFORCE.

### 15 to 19. Partly read (not load-bearing)

Slot attention (competing exchangeable slots by softmax attention + GRU; ARI about 98.8 % on CLEVR6, generalises to more objects; dot product, softmax,
backprop: out). DreamCoder (wake-sleep library learning; text editing 3.7 % to 79.6 % solved on 108 problems, best competition system 82.4 %; the idea of
promoting a frequent sub-structure to a new library entry transfers, the lambda-calculus search and neural recogniser do not). ARC (400 training tasks; priors:
objectness, goal-directedness, counting, geometry/topology; no matrix-free method with meaningful scores is known to me). In-memory HDC (760,000 phase-change
devices, over 6x energy and 3.7x area gain over digital CMOS; operations are XOR, shift, majority, associative search; the associative search is a binary
matrix-vector product in the array). Neuromorphic resonator odometry (0.53 % position error, no network training; analog/complex phasors).

## (c) Synthesis

### c1. The minimal operations and their cost

| Operation | Role | Cheapest digital form | Cost | Matrix? Multiply? |
|---|---|---|---|---|
| Bind | glue parts so the pair differs from the parts | XOR (dense bits); AND (sparse); index addition mod block size (sparse block code, lossless, paper 5); hash(a,b) into a table (L's CRC hash) | D XORs; K small adders; one hash | no / no |
| Permute | mark position or role | wiring or cyclic shift | free or barrel shifter | no / no |
| Bundle | hold several bound items in one vector | OR (sparse; Bloom filter); per-bit counter + threshold (majority) | one counter per bit | no / no |
| Unbind | recover a part | XOR again; index subtraction; inverse permutation | same as bind | no / no |
| Clean-up | snap a noisy vector to a stored symbol | nearest neighbour; in a sparse code, add the row of N counters for each active bit and take the maximum | active bits x N additions | dense matvec if code is dense; event-driven lookup if sparse |
| Peel / factor | split a product of several parts | resonator loop (dense in papers 3, 4); serial "pick best, mask, re-score" | a few clean-up passes | dense in papers; sparse version ours to test |
| Threshold coincidence | detect a pattern among many inputs | at least theta of s literals true (HTM segment, paper 13); AND of two bits (SPTP, paper 5) | popcount + compare | no / no |

Binding is similarity-destroying and cheap; bundling is similarity-preserving; clean-up restores discreteness. Multiplies appear only in HRR, FHRR, tensor
product, matrix binding and in every learned front end (papers 3, 6, 12, 14).

### c2. What gives composition, and where it breaks (from the full texts)

1. **Two different compositions.** Sets of whole objects (bundle of bound tuples): generalises over count with little data (paper 6: 97 % on 3-4 objects after training on 1-2). Attribute combinations inside one object: needs separately readable attributes (paper 6: 0 % for a one-readout-per-combination code; paper 14: 98.9 % on swapped colour/shape sets once attributes are separate; paper 8: only where the primitive was seen in compositions).
2. **Conjunction memorises, bundling generalises, but only partly.** Additive key-value bundles lifted held-out combination accuracy from 0 to 15-72 %, and two pairs stayed 0 % (paper 6). Nobody gets 100 % on held-out attribute combinations without hand-built structure.
3. **The training distribution can do it (meta-learning)**: random re-assignment of primitives across episodes gave 99.95 % on add-jump (paper 9); but longer outputs stay at 16 %.
4. **Capacity.** Bundles of R key-value pairs have signal-to-noise N/R^2 for analogy transformations (paper 5); resonator search spaces grow about N^2/F^1.27 (paper 4) and fall off a cliff above that; 1.2-1.4 bits per component (paper 1).
5. **Noise.** Clean-up plus sparse codes tolerate 30 % flipped bits (paper 4) or 50 % missing cells (paper 13); the weak point is the pixel-to-symbol front end, which every paper trains with backprop or supplies by hand.
6. **Depth.** Nested bindings multiply similarities; sparse AND thins; practical depth 2-3 (paper 1). Embedding structures in structures is open even for TPR (paper 12).
7. **Abstraction by renaming** (paper 7) turns parts into slots; the cost is hand-built symbol extraction and the v! permutation loop.
8. **Symbols are never learned unsupervised** in these papers; length/productivity and genuinely new symbols are unsolved (papers 8, 9).

### c3. Matrix-free and multiply-free verdict

Inside our rules: XOR/AND/OR binding, index-addition binding, hash binding, permutation, OR or counter bundling, event-driven clean-up in a sparse code, serial peeling,
XNOR relation literals, threshold clauses, Tsetlin automaton counters, library promotion by counting. Outside: HRR/FHRR convolution and phasor products, tensor and
matrix binding, dense X X^T resonators, slot attention, softmax concept operators, cosine dictionaries of thousands of vectors, and all gradient training (logic
gate networks included, until a local rule replaces it).

### c4. How learning works

Binding and bundling need no training; everything that turns raw input into symbols is trained by backprop (3, 6, 12, 14) or given (7). Logic gate networks learn gate choice
by backprop (10, 11). Tsetlin and HTM learn by local counters. L's front end is label-free and local; its gap is attribute structure and relations.

## (d) Our own method sketch

Starting facts about L (PROJECT_MEMORY, SIMULATED): 4,608-bit sparse code from 32 label-free detectors per channel, 2x2 pooling; counting table of 5-bit signed
counters per (class, bit) = 10 x 4,608 x 5 bit = 28.8 KB (ESTIMATED from those sizes); clothing 83 to 86.5 % depending on staged or one-pass; best system L +
about 4,000 flat clauses 89.7 to 89.8; depth and weight sharing add little. Position is already implicit in the bit index. Missing: separately readable attributes,
reading several parts from a mixed code, relations that do not name the parts.

Design rule from papers 6, 7, 8, 14: **parts must be readable separately, and clauses must be able to refer to parts by role, not identity.** Avoid one output per combination.

### Design 1: role-tagged attribute tables with a small signature clean-up (held-out attribute combinations)

Idea. Replace "one table row per class" by "one table per attribute", trained with L's surprise-gated rule on the same code. A class is a signature: one value per
attribute (a short list, or a K-block code where block k holds attribute k's value and binding two values is index addition mod block size). Recognition = for each
attribute, sum the counter rows of the active bits and pick the best value; snap the predicted signature to the nearest known signature in a tiny item memory (8 rows).
Unseen classes are recognised if their signature is in the item memory although no image was seen. It uses only counters, comparisons and a few XOR/popcounts.

Attributes for Fashion-MNIST (hand-assigned from the class names, DERIVED; freeze before running; they are our own judgement):

| Class | sleeve | length | front |
|---|---|---|---|
| T-shirt | short | hip | closed |
| Pullover | long | hip | closed |
| Dress | short | long | closed |
| Coat | long | long | open |
| Shirt | long | hip | open |

Every value occurs in at least two classes, so each class can be held out while all its attribute values remain in training (five leave-one-class-out runs). Footwear and bags
can be a separate "type" attribute later.

Minimal experiment (SIMULATED, host Python on existing encoder and table code, 3 seeds):
1. For each held-out class, train three attribute tables on the other four classes with attribute labels.
2. Test on the held-out class plus the four trained classes; predict three attributes; snap the signature.
3. Baselines: (a) flat 4-class table (cannot name the held-out class: 0 % by construction); (b) one table over the whole signature as a single symbol (the paper-6 failure,
expected about 0 %); (c) attribute tables with no item memory (attribute accuracy only).
Success criterion (revised after paper 6). Primary: mean held-out-class accuracy over the five runs >= 40 % in the 5-way test (chance 20 %); stretch >= 60 %. Secondary: the four trained classes
lose at most 3 points against a flat 4-class table; per-attribute accuracy on held-out images reported (chance 50 %), expecting the sleeve attribute to be weakest. Below 30 % is a negative result to be
recorded as such (paper 6's best additive result averaged 30 % over four pairs, two pairs at 0 %).
Cost (ESTIMATED): 6 to 7 attribute-value rows x 4,608 bits x 5 bit = about 20 KB (less than the 28.8 KB flat table); inference = reads of the same active bits for 3 tables plus an 8-row match; learning = same writes as today.
Uncertainty. Attribute labels are perfectly correlated with the class in training, so a table can learn "coat" instead of "long sleeve"; held-out classes decide it. Sleeves and collar are not pixel-local in 28x28 grey images.
Standing caution: attribute labels are used in training only, never at test time. Second test set: EMNIST letters with hand-assigned stroke attributes, leave-one-letter-out, same criterion.

### Design 2: serial peeling for superposed parts

Idea. Resonator-lite on L's own memories: score the mixed code against the class table (sparse lookup), take the best class c1, build the mask of bits that c1 explains from its dream counts (count above half the class count:
a comparator), clear those bits (AND-NOT on a 576-byte register), score again to get c2, optionally re-score c1 with c2's bits cleared (one or two rounds). The dream memory already exists on chip.
Experiment (SIMULATED): overlay two different Fashion-MNIST items (pixelwise maximum, horizontal offset 0, 4, 8 pixels), encode, test. Methods: top-2 of the plain table; peel; peel with re-score; pair-trained table (30 of 45 pairs
trained, 15 held out). Also, inspired by paper 6's multi-object result, train on single items only versus single items + pairs and test on triples at offset 8. Success: both classes named (unordered) at offset 8: peel at least 20 points above top-2, and held-out-pair
accuracy not more than 5 points below seen-pair accuracy; offset 0 only records the cliff; single-item accuracy must not fall (no-regression rule).
Cost (ESTIMATED): two to four sparse scoring passes only when a surprise signal fires, plus a 4,608-bit AND-NOT. Uncertainty: overlapping garments erase each other's evidence; look-alike classes share most bits.

### Design 3: relation literals and threshold clauses for abstract "same/different"

Idea (relational Tsetlin machine + logic gate view + HTM). Add a literal type XNOR(bit i of part A, bit i of part B) (optionally with one-cell shifts): a clause on these literals fires when A and B agree, regardless of content.
Allow clauses to be threshold clauses ("at least theta of s literals true", HTM segment) for noise tolerance.
Experiment (SIMULATED): pairs (left, right) of Fashion-MNIST items; target same class or different. Train on pairs from classes 0-5, test on pairs from unseen classes 6-9 and on mixed pairs. Baselines: clause learner on the concatenated 2 x 4,608 literals; popcount of XNOR with one threshold.
Compact form: 36 regions, each region's match count quantised to 4 levels, 72 relation literals plus negations. Optional episode randomisation (borrowed from paper 9): permute class identities during training.
Success: unseen-class same/different accuracy >= 85 % (flat expected below 65 %) with seen-class accuracy >= 90 %; if the plain threshold already hits 85 %, the result shows only that matching is cheap, so also report the odd-one-out-in-three task as the test that needs learned relations.
Cost (ESTIMATED): 4,608 XNORs + region popcounts; about 144 bits of literal state per clause; 100 clauses under 2 KB; no multiplier.

### Design 4 (cheap control, from paper 12): held-out (class, position) combinations

Two-slot images (two items side by side); train with some (class, slot) pairs never shown (for example class d never in slot d, as the n-in-n copy test), read out each slot separately. Tests whether position-shared tables (same filler table for both slots, or shifted code) generalise while per-slot tables cannot. One afternoon, no new hardware; success: held-out (class, slot) accuracy within 5 points of seen ones for shared tables.

### Run order and ranking

1. Design 3 first (cheapest, tests relation literals).
2. Design 1 next (core capability: held-out attribute combinations).
3. Design 4 as a control; Design 2 if Design 1 shows separable attributes.
Proposed top method: **Design 1** (additive, role-tagged attribute tables + small signature clean-up), because paper 6 gives the cleanest published evidence for exactly this contrast, paper 14 shows the same effect (separate attribute spaces fix CoGenT), it costs less memory than today's flat table, and a pass would be the first composition result for L.

### What is out of reach under our rules (and why)

- Dense-vector VSA with convolution, phasors, tensor products or matrix binding (HRR, FHRR, TPR, MBAT).
- The resonator network in its published dense form; a sparse-block-code resonator is plausible (paper 5 supplies the binder) but unmeasured.
- Systematic generalisation on language-like tasks (SCAN) with a sequence model, and productivity (longer outputs): unsolved even with meta-learning (16 %).
- Learning the symbols themselves (parts, attributes) from pixels without labels: no matrix-free method known; every paper supplies or backprop-trains them.
- ARC-level rule induction and DreamCoder-style search: only "promote a frequent conjunction to a new literal" is a candidate, a longer project than the six-to-eight-month horizon.
- Binding by synchrony or hippocampal conjunctive coding as mechanisms: not read; the survey judges synchrony to need many time steps and not be storable directly.

### Honest summary of uncertainty

The strongest evidence is cautionary: a one-readout-per-combination code gets 0 % on held-out attribute combinations (paper 6) and SCAN's novel primitive about 1 % (paper 8); the additive repair reached only 0 to 72 %. No paper in the logic-gate, Tsetlin or HTM
families measures held-out-combination generalisation, so any success of Designs 1 to 4 would be new evidence and a failure is quite possible. All design numbers are targets and ESTIMATED costs, not results. The Fashion-MNIST attribute table is our own assignment.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
