---
title: Thinking research 5 - symbols and composition
tags: [spark, research, papers]
---

# Thinking research 5: symbols and composition (binding, roles and fillers, systematic generalisation)

Written 26 Oct 2026. Question: how does published work get composition (new wholes from known parts) out of simple
operations, does it stay matrix-free and multiply-free, how is it learned, how does it scale, and what can L
(sparse binary code of local detectors + clauses = AND of literals + counting tables) take from it without copying?

Rules applied (from the project instructions): no dense matrix-vector products, no multipliers, no backprop in the
chip design. Allowed: scans, event-driven sparse lookups, table and hash lookups, counters, small state, local rules,
clauses, sparse binary codes. All numbers below are "as reported by the authors" (their MEASURED or SIMULATED results
on their own hardware or data); we reproduced nothing. Numbers about L come from `docs/PROJECT_MEMORY.md`
(SIMULATED). Numbers marked ESTIMATED are our arithmetic on stated assumptions. Paper text is treated as data.

How the papers were read: PDFs from arXiv, converted with `pdftotext`, read in the terminal. Only two papers were read
end to end (the main text, not the reference lists): Kleyko et al. Part I and Frady et al. resonator networks part 1.
Every other paper was read **partly** (abstract, introduction, method and the main result sections; appendices and
many tables skipped); the table says which parts. Things NOT read at all and used only through the surveys:
Plate's HRR book, Kanerva 2009, Smolensky's tensor product paper, Gayler's work, the Numenta HTM papers, and the
neuroscience literature on binding by synchrony and hippocampal conjunctive coding (blocked or not on arXiv).
Statements about those are marked "via survey".

## (a) Papers read

| # | Citation | Year | Read fully? | What was read |
|---|---|---|---|---|
| 1 | Kleyko, Rachkovskij, Osipov, Rahimi. A Survey on Hyperdimensional Computing aka Vector Symbolic Architectures, Part I: Models and Data Transformations. arXiv 2111.06077 | 2021/23 | **Yes** (main text, all sections 1-5) | everything except references |
| 2 | Kleyko, Davies, Frady, Kanerva, Kent, Olshausen, Osipov, Rabaey, Rachkovskij, Rahimi, Sommer. Part II: Applications, Cognitive Models, and Challenges. arXiv 2112.15424 | 2021/23 | Partly (about 85 %: sections 1 to 4.2.5) | applications, analogy, cognitive architectures, interplay with neural nets; end of discussion and references not read |
| 3 | Frady, Kent, Olshausen, Sommer. Resonator networks for factoring distributed representations of data structures (part 1). arXiv 2007.03748 | 2020 | **Yes** (main text) | all |
| 4 | Kent, Frady, Sommer, Olshausen. Resonator networks outperform optimization methods at solving high-dimensional vector factorization (part 2). arXiv 1906.11684 | 2020 | Partly | abstract, intro, operational capacity, search speed, non-convergence; benchmark algorithm derivations and appendices skipped |
| 5 | Lake, Baroni. Generalization without systematicity: SCAN. arXiv 1711.00350 | 2018 | Partly | tasks, experiments 1 to 4 results; appendix grammar skimmed |
| 6 | Lake. Compositional generalization through meta sequence-to-sequence learning. arXiv 1906.05381 | 2019 | Partly | abstract, method, experiments 1 to 4, table 3 numbers |
| 7 | Mao, Gan, Kohli, Tenenbaum, Wu. The Neuro-Symbolic Concept Learner. arXiv 1904.12584 | 2019 | Partly | abstract, model overview, experiments 4.1 to 4.3 |
| 8 | Locatello et al. Object-centric learning with Slot Attention. arXiv 2006.15055 | 2020 | Partly | abstract, method, object discovery results, generalisation to more objects |
| 9 | Hersche, Zeqiri, Benini, Sebastian, Rahimi. A neuro-vector-symbolic architecture for solving Raven's progressive matrices. arXiv 2203.04571 | 2023 | Partly | abstract, results, the supplementary note on held-out attribute combinations (read closely) |
| 10 | Saha, Granmo, Zadorozhny, Goodwin. A Relational Tsetlin Machine with applications to natural language understanding. arXiv 2102.10952 | 2021 | Partly | abstract, TM background, "detaching from constants" (read closely); QA experiments only skimmed |
| 11 | Petersen, Borgelt, Kuehne, Deussen. Deep differentiable logic gate networks. arXiv 2210.08277 | 2022 | Partly | sections 1 to 4, result summary |
| 12 | Petersen, Kuehne, Borgelt, Welzel, Ermon. Convolutional differentiable logic gate networks (LogicTreeNet). arXiv 2411.04732 | 2024 | Partly | abstract, method, CIFAR-10 headline |
| 13 | Ellis et al. DreamCoder: growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning. arXiv 2006.08381 | 2020 | Partly | abstract, introduction, text-editing result |
| 14 | Chollet. On the measure of intelligence (ARC). arXiv 1911.01547 | 2019 | Partly | core-knowledge priors, ARC definition, solution strategies |
| 15 | Karunaratne et al. In-memory hyperdimensional computing. arXiv 1906.01548 | 2020 | Partly | abstract, operations, energy table |
| 16 | Renner et al. Visual odometry with neuromorphic resonator networks. arXiv 2209.02000 | 2022/24 | Partly | abstract, results summary |

## (b) Per paper

### 1. Kleyko et al., survey Part I (read fully)

Mechanism. A hypervector (HV) is a long random vector; random HVs are quasi-orthogonal, so each acts as an atomic
symbol. Three operations make structure: superposition (bundling: add, then majority/threshold or OR), binding
(a multiplication-like operation: XOR for binary spatter codes, element-wise product for MAP, circular convolution for
HRR, outer product for tensor product representations, AND/context-dependent thinning for sparse binary codes,
block-wise index addition for sparse block codes) and permutation (a fixed shuffle, usually a cyclic shift, that
marks position or role). Role-filler records are the bundle of bind(role, filler); sequences are bundles of permuted
items; images are bundles of bind(position, pixel feature); graphs are bundles of bind(node, node). Reading a part
out is unbinding followed by clean-up: the noisy result is matched against an item memory (nearest neighbour, i.e. a
table lookup of the best stored vector). Binding must not be associative with bundling, otherwise the "superposition
catastrophe" (a+b, b+c cannot be told from a+c, b) returns.

Key numbers (survey text). Capacity of an HV is predicted by a Gaussian detection formula; best known decoding
reaches 1.2 to 1.4 bits per component. For sequence recovery the formula matched simulation closely (D = 256,
N = 64 symbols). Dense HV dimension in practice 1,000 to 10,000. A sparse binary HV keeps M of D components active.
The survey says plainly that raw-pixel HDC "is, in fact, lower" than a kNN or a two-layer network on MNIST and that
features or a network front-end are needed.

Transfers to L. (1) L's 4,608-bit code is already a **sparse binary distributed representation** (SBDR-style), and the
survey says sparse codes allow inverted indexing and event-driven similarity search: this is exactly L's decision
rule (add counter rows for active bits). (2) The bit position in L's code is already "role (pooled location) x
filler (detector id)" in a localist form: the role is implicit in the index. (3) Bloom filter = OR-bundle of sparse
HVs; L's dream memory and the hashed lookup core (CRC hash, XOR and shift only) are the same family. (4) The
sparse block code binding is **integer addition of indices modulo block size**, a few small adders, no multiplier.
(5) XOR binding on dense bits needs only XOR gates.

Does not transfer. Dense bipolar or real HVs (HRR, FHRR, MAP with integer sums) need multiplies or FFT for binding
or dot-product clean-up over thousands of components: a dense matrix-vector product against the item memory, which
our rule excludes. Tensor product representations (outer product) grow as D^k: they are matrices by definition.
Matrix binding (MBAT) is excluded outright. Clean-up against N prototypes of a dense 10,000-bit vector costs N x 10,000
XNOR-and-count operations per query; only with a sparse code and event-driven row addition does it fit our rule.
Also: binding "does not need training" but the encoder from pixels to HVs does, and the survey admits there is no
principled way to build it.

### 2. Kleyko et al., survey Part II (partly read)

Mechanism. Reviews uses: finite-state machines as bundles of bind(input, state, permute(next state)), robot
controllers as bundles of sensor-set bound to action-set, string matching, language identification by bundled n-gram
vectors (permute-and-bind per letter), classification by class centroids (bundle of training HVs, refined by
perceptron-like updates), analogical retrieval and mapping (Plate's HRR episodes, sparse-code versions), "holistic
transformations" (a transformation HV learned from a few example pairs, then applied to new structures without
decomposing them), Raven's matrices, visual question answering, and cognitive architectures (Spaun, associative-
projective networks on sparse codes, HTM shown to support binding and bundling of sparse HVs).

Key numbers (as reported in the cited works). HRR transformation HVs learned by gradient descent from a few pairs
generalised to new elements and to structures more complex than in training (Plate/Neumann line). A visual-analogy
demo on binary HVs from a CNN: 98 % correct on unseen automobile images. A trainable visual question answering model:
100 % on five trained questions, 60 to 72 % on unseen questions. Classification tables show centroid classifiers with
binary HVs on MNIST/Fashion-MNIST, always with weak baselines or feature extractors.

Transfers to L. (a) The classification recipe (centroid = bundle, then perceptron-like refinement) is what L's
counting table with surprise-gated writes already is; no gain. (b) Role-filler **database query by unbinding**
(slide on "what is the age of Lee who is female"): answers composed from parts without having seen the whole record.
(c) "Holistic transformation": learn a single mapping A->B from examples by XOR/bind; for self-inverse XOR binding the
mapping is a single bit pattern T = bind(a,a') bundled over examples: counting in the XOR domain, matrix-free. (d) The
analogy hierarchy (literal similarity > surface features > true analogy > relations only) gives a ready measuring stick.
(e) The associative-projective-network text lists "cores and fringes" (bits that co-occur in many members = category
prototype core; rare bits = instance): this is what L's dream counts already store.

Does not transfer. Learning the transformation HV by gradient descent is backprop. Most results assume that a front
end hands over symbols. The survey itself says analogical mapping has "not been shown to scale". Spaun is a
large spiking network built on HRR convolution.

### 3. Frady et al., resonator networks part 1 (read fully)

Mechanism. Composite vector s = x_i * y_j * z_k (Hadamard product of codewords from three codebooks). Decoding by
trying all D^3 combinations is the "combinatorial search problem" that blocked VSAs from deep structures. The
resonator keeps one estimate per factor, initialised to the **superposition of all codewords**; each step it unbinds
the other estimates from s, cleans up with the codebook (x_hat = sign(X X^T (s * y_hat * z_hat))) and repeats. Search in
superposition tests many combinations at once; the clean-up removes cross-talk; the correct factors "resonate" and the
state settles. Scenes: several objects (colour x digit x vertical x horizontal) are bundled; the net decodes one
object, subtracts it ("explaining away", like tensor deflation), resets and decodes the next.

Key numbers (authors). 23 atomic symbols describe 630 object types and 250,444,530 possible 1 to 3 object scenes;
N = 500 suffices (fewer than 630). A two-hidden-layer network trained with backprop on 100,000 images produced the scene
vector; test on 10,000 images; the resonator corrects encoder errors, accuracy as a function of cosine similarity
shown as logistic curves (exact values not in the text). Tree search with five factors worked.

Transfers to L. The idea of **peeling**: find one part, remove the evidence it explains, look again at what is left.
In L this is AND-NOT of the explained bits against the dream memory of the winning class and a second sparse scoring pass.
Also: "unbinding is the real problem of perception" (Feldman, quoted): sensors give mixtures, the task is to separate.
Also: the expected value of a clean-up memory is to project noisy estimates onto known items: L's class table plays that part.

Does not transfer. The update uses X X^T (a dense D x D product, as outer-product Hopfield weights) and bipolar
element-wise products; a feed-forward network trained by backprop produced the input vector. A sparse-code resonator
(authors' reference to a sparse variable-binding paper, not read) would be needed to stay in our rules. Convergence is
not guaranteed (see paper 4).

### 4. Kent et al., resonator networks part 2 (partly read)

Mechanism. Same dynamics, analysed. "Operational capacity" = largest search space M = D^F that is solved with p >= 99 %
success within k = 0.001 M iterations. Compared with alternating least squares, gradient methods and soft thresholding.

Key numbers (authors). Capacity is about two orders of magnitude higher than all the benchmark algorithms for F = 3 and
F = 4; it scales as a **quadratic function of vector dimension N**, for F = 2 to 7; iterations to convergence are a tiny
fraction of M below capacity; in a speed test (N = 1500, F = 3, D_f = 40, 5,000 trials) the resonator always found the
answer while the benchmarks solved about 70 %; per-iteration cost about 5x lower than benchmarks. Not guaranteed to
converge (no Lyapunov function), non-convergent regimes appear above capacity.

Transfers to L. Planning number: the search space we can untangle grows with N^2, not N, so a code of a few thousand
bits suffices for the few-hundred-combination attribute spaces we care about (clothing: well under 1,000 combinations).
Failure above capacity is a hard cliff: we must measure it, not assume graceful decay.

Does not transfer. All experiments are dense bipolar; capacity numbers do not carry over to sparse codes without
re-measurement.

### 5. Lake and Baroni, SCAN (partly read)

Mechanism. Navigation commands ("jump twice and walk left") mapped to action sequences. Tests zero-shot generalisation
of recurrent seq2seq networks to systematically new combinations. Splits: random, longer outputs, new primitive.

Key numbers (authors, MEASURED). Random split 99.8 % (best overall net), but as the fraction of commands in training
falls to 2 % it drops to about 54 % and 1 % gives about 5 %. Length split: best net 13.8 % overall, up to about 20 %
with oracle length. "Add jump" (new primitive seen only alone): best top-performing hyper-parameter setting 1.2 %,
overall-best 0.08 %, while the equivalent "turn left" split reaches 90.3 % because "turn left" appears composed in
training. With 32 distinct composed training commands containing "jump" the net reaches 88.4 % (8 commands: 38.3 %).

Lessons for L. (i) Recognition-style statistics do not give systematicity: generalisation appears only when the
primitive was seen **in compositions** during training (turn-left versus jump contrast). (ii) The benchmark gives a
template for our own test: hold out combinations, keep primitives seen elsewhere. (iii) Quantitative target: any
method must beat about 1 % on the add-jump type of split.

Does not transfer. The networks are LSTMs trained by backprop; the test is language-like and not directly usable for
images. We should reuse the split design, not the data.

### 6. Lake, meta seq2seq (partly read)

Mechanism. A memory-augmented network gets, in every episode, a **support set** of input-output examples with a freshly
random mapping of primitives (e.g. "dax" means JUMP in this episode) and a query; the decoder attends to the support
set. Training over many random episodes forces it to learn the composition rules and to look primitives up in memory.

Key numbers (authors). Mutual-exclusivity task 100 % (SD 0). SCAN add-jump 99.95 % (SD 0.08) versus plain seq2seq 0.03 %
and syntactic attention 78.4 %; length split 16.64 % versus 7.71 % for the base net and 15.2 % for syntactic
attention; ablations (no support loss, no decoder attention) collapse to 5 to 12 %.

Transfers to L. The **training distribution does the work**: the same machinery that fails on one fixed mapping succeeds
when primitives are randomly re-assigned across episodes, so the model is forced to separate "which symbol" from "how
combined". A counting-table analogue: during the day, randomise the bit-to-detector identity or re-label parts
across episodes so tables must store relations, not identities (see design 3). And the support set is a lookup memory.

Does not transfer. Encoder-decoder LSTM with attention, backprop through episodes. The 16 % length result shows the
method does not solve productivity either.

### 7. Neuro-Symbolic Concept Learner (partly read)

Mechanism. A perception module gives per-object feature vectors; each concept (red, cube, left-of) is an operator that
maps an object vector into an attribute-specific embedding space and compares it with the concept embedding; a parser
turns the question into a program of fixed operators (filter, count, relate, exist) executed softly over the objects.
Curriculum learning starts with simple questions.

Key numbers (authors). 5K images (less than 10 % of CLEVR's 70K) and no program annotations; concept classification about
99 % for all object properties; on CLEVR-CoGenT (cubes and cylinders with swapped colour sets) 98.8 % on split A and
98.9 % on split B after treating attributes as separate operators; CLEVR VQA state of the art among models with zero
program labels, within a few points of a model that used 700K programs.

Transfers to L. **Attributes are separate spaces.** When colour and shape live in separate attribute spaces the
network no longer uses colour to decide shape, and the held-out combination works (98.9 %). The mirrored failure for
joint classes is the CoGenT overfit. This directly motivates design 1 (separate tables per attribute, fixed small
program on top). The executor (filter/count/relate) is a lookup-and-count program: matrix-free in principle.

Does not transfer. Perception is a pretrained CNN with object proposals from Mask R-CNN; concept embeddings and
parser are trained by gradient descent; operators use cosine/dot products.

### 8. Slot Attention (partly read)

Mechanism. K interchangeable slot vectors compete (softmax over slots) for the input features through T = 3 rounds of
attention with a recurrent update; each slot ends up binding one object. Slots share one format, so any slot can hold
any object.

Key numbers (authors). Unsupervised object discovery on CLEVR6: ARI near 98.8 +/- 0.3 % in the results table (the exact
row for each variant was not checked); a greyscale CLEVR6 variant gives 98.5 %; generalises to CLEVR10 and to more slots at test time with only a mild drop; trains in about 24 h on
8 GPUs versus about 7 days for the earlier IODINE; supervised set prediction generalises to unseen object counts.

Transfers to L. Exchangeable, competing slots = "winner-take-all with inhibition between detectors", which L's
competitive detectors already do at the pixel-patch level. The idea of **explaining away by competition** parallels the
resonator's subtract-and-reset. Slots bind by competition, not by a separate binding operator: a different route to
the same goal.

Does not transfer. Attention is dot product plus softmax plus a GRU plus an MLP, trained end-to-end by backprop and
with a CNN encoder; none of these are available. The scores are for synthetic scenes only.

### 9. Hersche et al., neuro-vector-symbolic architecture (partly read; supplement read closely)

Mechanism. A CNN front end is trained to output, for each panel, a **superposition of bound attribute vectors**
(bipolar). A backend turns attribute distributions into sparse block codes (binary vectors with one 1 per block;
binding = block-wise circular convolution = index addition) and applies rule detectors (progression, arithmetic,
distribute-three, logic) in the vector domain by unbinding; probabilistic abduction without exhaustive symbolic search.

Key numbers (authors). RAVEN 87.7 %, I-RAVEN 88.1 % (a new record when published); reasoning back end about 244 times faster
on CPU than the earlier symbolic PrAE back end; PGM 68.3 %. **The supplement's held-out-combination test is the most
important result for us:** with purely multiplicative binding of quasi-orthogonal attribute vectors the front end gets
**0 %** on every held-out attribute-value combination (all six attribute pairs). The authors explain why: each entry of
the output corresponds to one memorised combination, and training and test combinations are mutually exclusive. With
a **multiplicative-additive** encoding (bundle of role x value pairs, so each attribute can be unbound on its own) plus
hyperspherical regression for ordinal values, held-out pairs reach 34.8 % (position, colour), 15.1 % (position, size),
29.3 % (colour, size), 72 % (colour, type); position-type and size-type stay at 0 %, which the authors suspect comes from
the spatial structure of CNN filters. Training on panels with 2 objects then testing on 3 or 4 objects gives 97.1 to 97.3 %.

Transfers to L. This is the cleanest published evidence for the central design rule: **a conjunction-only code
(clause, hash binding, product of vectors) memorises combinations and cannot generalise to unseen ones; an additive
bundle of role-bound single-attribute parts can.** It also shows the limit: the gain was 0 to 72 %, not 100 %, and two attribute pairs
stayed at zero.

Does not transfer. Front end is a trained CNN; the rule search is run on GPU in float; hyperspherical regression uses
cosine. We keep the **encoding principle** and the sparse-block-code arithmetic (index addition, a small adder per block).

### 10. Relational Tsetlin Machine (partly read)

Mechanism. A Tsetlin machine learns conjunctive clauses with one Tsetlin automaton per literal (include/exclude) using
local reinforcement; clauses vote with polarity. The relational version treats ground atoms such as parent(Bob, Mary)
as propositional inputs, and **replaces constants by variables in order of appearance** ("Mary becomes Z1, Bob
becomes Z2") before learning, so clauses like child(Z1,Z2) <- parent(Z2,Z1) never see names and apply to any constants. Several
possible variable assignments are handled by a convolution over assignment permutations. The number of inputs is
bounded by O(z^w) (z variables, relation arity w), independent of the number of constants.

Key numbers (authors). In closed-domain question answering the first-order representation gives knowledge bases about
10x more compact and raises answering accuracy from 94.83 % to 99.48 %; robust to erroneous, missing and superfluous
facts.

Transfers to L. This is the clause-system way to composition: **rename the parts into role slots before the clause
sees them.** The literal "parent(Z2, Z1)" is a relation between two slots, and the clause is true for any pair that
stands in that relation. In our setting, the matrix-free version is a relation literal such as XNOR(bit_i of part A,
bit_i of part B): it says "A and B agree here" without naming the content. All TM operations are local counters and
bit logic (the paper's Type I/II feedback is automaton state counting), within our rules.

Does not transfer. It needs symbolic atoms from a parser; the convolution over variable permutations multiplies the
cost by the number of assignments; it handles non-recursive Horn clauses only; no pixel-level experiments; the paper
reports no systematic held-out-combination test beyond the QA gain.

### 11. Differentiable logic gate networks (partly read)

Mechanism. Network of 2-input gates with fixed pseudo-random wiring; each gate chooses one of the 16 Boolean functions of its
two inputs. Training relaxes the choice to a softmax over 16 real numbers and the logic to real-valued (product) form,
by gradient descent; after training each gate is hard-coded to its most probable function. Output class score = bit
count over several neurons per class.

Key numbers (authors). More than one million MNIST images per second on one CPU core at above 97.5 % accuracy; about
12x faster than the best binary networks at 98.4 %; scaled to about 5 million parameters (gate choices); the MONK's
problems (logical structure) are among the benchmarks (exact score not checked); the paper also builds adders from gates. The related work they quote, Chatterjee's
"memorization" with binary lookup tables built by counting conditional frequencies, reached 90 % on MNIST 0-4 versus 5-9.

Transfers to L. Inference is only AND, OR, XOR, NOT, popcount, fixed sparse wiring: perfect fit with our rules. A
gate layer that can pick XNOR is a **relation detector** between two code bits (design 3). The 16-function view says a
learned clause literal could be a 2-input function of two code bits, not just a bit or its negation.

Does not transfer. Training is backprop through real-valued relaxations with multiplications (GPU only; for our
long-term on-chip goal this is the part we must replace). No paper in this family tests systematic generalisation to
held-out combinations; "logical structure" there means Boolean functions on given inputs.

### 12. Convolutional logic gate networks, LogicTreeNet (partly read)

Mechanism. Same training as paper 11 but with convolution as **shared logic-gate trees** (a depth-2 tree of three
learnable gates per kernel, applied at every position), OR pooling and residual initialisation.

Key numbers (authors). CIFAR-10 86.29 % with 61 million gates, 29x smaller than the previous best at its accuracy; the earlier plain
gate network stopped at 62 %.

Transfers to L. Weight sharing across positions with a boolean tree kernel plus OR pooling is the same idea as our
earlier "convolutional clauses" (+0.2 to +0.4 on L's code, fail on raw pixels, `hw/results/clause_weight_sharing.md`).
It confirms that without sharing, depth and shared parts are what scale. Gate count (not parameter count) is the
hardware cost measure.

Does not transfer. Same GPU backprop training; still no composition benchmark.

### 13. DreamCoder (partly read)

Mechanism. Wake: search programs (in a typed lambda calculus) that solve tasks. Sleep (abstraction): find recurring
sub-programs in the solutions and add them as library functions, shrinking future programs. Sleep (dreaming): sample
programs from the library, run them to make fantasy tasks, and train a neural recogniser that guides search.

Key numbers (authors). Text editing, 108 SyGuS problems: before learning 3.7 % solved within 10 min; after learning 79.6 %
(average 40 s instead of 235 s); the best synthesiser in the competition solved 82.4 % with 1 h and 8 CPUs, and
DreamCoder reached 84.3 % under that budget; list processing and graphics domains reach near 100 % of held-out tasks while
other models stay below 60 %.

Transfers to L. **Library learning = counting repeated sub-structures and promoting them.** L already counts: a frequent
conjunction of literals can be promoted to a new literal (a "chunk") exactly as a repeated sub-program becomes a library entry. The
wake-sleep rhythm matches L's day/night, and "dreams" that are generated from the learned library and used to train
the guide mirror L's dream replay. Compression as the criterion (shorter description = higher prior).

Does not transfer. Programs are lambda terms searched with a neural recogniser trained by gradient descent; search is
combinatorial and slow (minutes per task on CPUs).

### 14. Chollet, On the measure of intelligence / ARC (partly read)

Mechanism / content. ARC tasks are small coloured grids (400 training and 400 evaluation tasks in the public set) where a
few input-output pairs define a transformation; the solver must apply it to a new grid. The paper lists the innate
priors it assumes: objectness (cohesion, persistence, contact), goal-directedness, numbers and counting, and elementary
geometry and topology. Suggested route: a domain-specific language of small primitives plus program search, with
library growth.

Transfers to L. A precise list of **what must be built into the sensing layer** for composition: object segmentation,
counting, symmetry, simple geometry. ARC-style grids are small enough (up to 30x30, 10 colours) to be a bit-plane code and a
test of rule induction by counting, but such a goal is far from our six-month horizon (see section d, "out of reach").

Does not transfer. Evaluation is of program-synthesis systems; no matrix-free method is known to us that reaches meaningful ARC scores.

### 15. In-memory hyperdimensional computing (partly read)

Mechanism. Binary HDC (XOR bind, majority bundle, one-bit shift permutation) mapped to phase-change memory crossbars: encoder
and associative memory computed in the array.

Key numbers (authors). 760,000 PCM devices; three tasks (language, news, EMG gesture) at accuracy comparable to software;
over 6x end-to-end energy and 3.7x area improvement against a dedicated digital CMOS design.

Transfers to L. Confirms the **hardware cost model** of HDC: XOR, shift, majority counters, associative lookup, nothing else. The
associative memory is a content-addressable lookup. Analogue crossbars are out of scope for us; the digital
blocks are not.

Does not transfer. The associative-memory search is a (binary) matrix-vector product in the array, which is
the "dense matrix" our rule forbids unless read as a sparse event-driven table.

### 16. Neuromorphic resonator networks for visual odometry (partly read)

Mechanism. A VSA scene representation as working memory; a resonator network factorises position and rotation; designed for Loihi.

Key numbers (authors). 0.53 % relative position error on the event-camera set, similar to the best event-only
visual-inertial methods, and no training of the network itself (only calibration).

Transfers to L. Proof that a resonator-style factoriser can be hardware-light and event driven; "no training" parallels our
no-backprop rule. Does not transfer: analogue/complex phasors, a Loihi implementation we cannot reproduce.

## (c) Synthesis

### c1. What the minimal set of operations is

| Operation | Role | Cheapest digital form | Cost | Matrix? Multiply? |
|---|---|---|---|---|
| **Bind (conjunction)** | glue part to role/other part so the pair differs from the parts | binary XOR (dense), AND (sparse, loses nothing but density), index addition mod B (sparse block code), hash(a,b) into a table (L's CRC hash) | D XOR gates; K small adders; one hash | no / no |
| **Permute** | mark position or order, protect against interference | wiring (fixed shuffle) or cyclic shift | free or a barrel shifter | no / no |
| **Bundle (superpose)** | hold several bound items in one vector | OR (sparse; Bloom filter), per-bit up-down counter plus threshold (majority) | one counter per bit | no / no |
| **Unbind** | recover a part from a bundle | XOR again (self-inverse), inverse index subtraction, inverse permutation | same as bind | no / no |
| **Clean-up** (item memory) | snap a noisy vector to a stored symbol | nearest-neighbour over N stored vectors; in a sparse code: for each active bit add the row of N counters, take the maximum | active bits x N additions | dense matvec if the code is dense; **event-driven lookup if sparse** |
| **Peel / factorise** | split a product of several parts | resonator loop: unbind, clean up, repeat; or serial peeling: pick best, mask, re-score | a few passes of clean-up | dense in the paper; sparse-lookup version is ours to test |

In every VSA model the binding is a non-linear, cheap, **similarity-destroying** step (bound vectors are not similar
to their inputs, except in sparse AND/CDT), the bundle is **similarity-preserving**, and the clean-up restores
discreteness. Multiplications appear only in HRR (convolution), FHRR (complex product), MAP/bipolar (which is XOR in
bits), tensor products and matrix binding; the binary and sparse block variants avoid them.

### c2. Where composition breaks (as found in the papers)

1. **Conjunction-only codes memorise combinations** (paper 9: 0 % on held-out attribute pairs; paper 5: 1 % on the
   new primitive). Generalisation requires the parts to be separately readable: bundle of role-bound parts, or one
   table per attribute.
2. **Capacity.** Bundling more than a few bound pairs makes cross-talk exceed the signal; with N-dimensional dense
   bipolar vectors the resonator solves search spaces of order N^2 (paper 4); beyond, a cliff, not graceful decay.
   1.2 to 1.4 bits per component is the best decoding rate known to the survey authors. Sparse codes have lower
   capacity per bit but allow cheaper lookup.
3. **Noise.** Clean-up fixes moderate noise (resonator corrected encoder errors, paper 3); HDC is robust to hardware
   faults (paper 15). But the front end that turns pixels into HVs is the weak point in every paper: trained by backprop,
   imperfect, and the survey says raw-pixel HDC is below a kNN.
4. **Depth.** Nested binding cuts similarity multiplicatively (similarity of bound pairs is the product of the part
   similarities); the sparse AND/CDT density shrinks with depth ("thinning depth"). Practical depth is 2 to 3 levels;
   deeper structures need factoring or explicit storage.
5. **Position and sharing.** Bound-to-position codes do not generalise over shifts unless partial permutations or
   correlated position codes are used (survey sections 3.3, 3.4); weight sharing is the alternative (paper 12).
6. **Search and productivity.** Length/productivity generalisation stays hard even with meta-learning (paper 6: 16.6 %).
7. **Symbol grounding.** Nobody learns the symbols (attributes, objects) without labels or a supervised front end; the
   papers hand them over.

### c3. Matrix-free and multiply-free verdict, short

Inside our rules: XOR/AND/OR binding, index-addition binding, hash binding, permutation, OR or counter bundling,
event-driven clean-up in a sparse code, serial peeling, clause literals that are XNOR relations, Tsetlin-style
automaton counters, library promotion by counting. Outside: HRR/FHRR convolution and phasor products, tensor and
matrix binding, dense Hopfield or resonator weights X X^T, slot attention, softmax-based concept operators, all
gradient training (logic gate networks included, until a local rule replaces it).

### c4. How learning works in these systems

Only the VSA operations are training-free. Everything that maps raw input to symbols (CNN front ends in papers 3, 7, 8,
9) is trained by backprop. The Tsetlin route (paper 10) and counting tables are the only learners in this set that are
local, but they use symbolic input. L's advantage: its front end is already label-free, local and sparse; its gap:
no attribute structure.

## (d) Our own method sketch

Starting facts about L (PROJECT_MEMORY, SIMULATED): 4,608-bit sparse code from 32 label-free detectors per channel,
2x2 pooling; counting table of 5-bit signed counters per (class, bit) = 10 classes x 4,608 x 5 bit = 28.8 KB
(ESTIMATED from those sizes); clothing 83 to 86.5 depending on staged or one-pass; best system L + about 4,000 flat
clauses 89.7 to 89.8; depth and weight sharing add little. The code is already position-specific, so "bound to
position" is free; what is missing is (i) separate readable attributes, (ii) reading several parts from one mixed
code, (iii) relations between parts that do not name the parts.

Design principle taken from papers 5, 7, 9 and 10: **parts must be separately readable and must be able to refer to each
other by role, not by identity.** Conjunction (a clause, a hash, a class row) memorises; additive role-tagged votes
and relation literals generalise.

### Design 1: role-tagged attribute tables with a block-code signature clean-up (held-out attribute combinations)

Idea. Replace "one table row per class" by "one table per attribute", trained with the same surprise-gated rule on the
same code. A class is not learned as a row but described by a **signature**: one chosen value in each attribute (a
short list of small integers, or a K-block sparse code where block k holds the index of attribute k's value; binding
two attribute values = adding indices modulo the block size, one small adder per block). Recognition = read each attribute table
(sum counter rows over active bits, take the best value per attribute), form the predicted signature, snap it to the
nearest known signature in a tiny item memory (an 8-row lookup, XOR and popcount of a few dozen bits). Unseen classes
are recognised if their signature is in the item memory, even though no image of them was seen: composition from parts.
Why this is ours: it uses L's own table rule, no vector algebra over thousands of components; the item memory is the
only "clean-up" and it is tiny.

Attributes for Fashion-MNIST (hand-assigned from the class names, DERIVED; to be checked and frozen before running so we do not tune on test results):

| Class | sleeve | length | front |
|---|---|---|---|
| T-shirt | short | hip | closed |
| Pullover | long | hip | closed |
| Dress | short | long | closed |
| Coat | long | long | open |
| Shirt | long | hip | open |

Every value of every attribute occurs in at least two classes, so each class can be held out while all its attribute
values stay present in training (leave-one-class-out, five runs). Footwear and bags can be added later as a separate
"type" attribute; trousers need a "legs" value.

Minimal experiment (SIMULATED, host Python on the existing encoder and table code, 3 seeds):
1. For each of the five held-out classes: train three attribute tables on the other four classes' images with their
   attribute labels (same one-pass surprise-gated rule).
2. Test on the held-out class's test images plus the four trained classes. Predict the three attributes, snap the
   signature to the 5-row item memory.
3. Baselines: (a) flat 4-class table (cannot name the held-out class, 0 % by construction; measures what it does
   with it); (b) conjunction-only: one table over the signature as a single symbol (expect about 0 % like paper 9);
   (c) attribute tables without the item memory (attribute accuracy only).
Success criterion. Held-out-class images correctly named in the 5-way zero-shot test: mean over the five runs >= 50 %
(chance 20 %; target to beat: 0 % for the flat and conjunction baselines), and the four trained classes lose at most
3 points against a flat 4-class table. Also report per-attribute accuracy on held-out images (chance 50 %) to see which attribute (sleeve length is the likely
weak one) fails. A result below 30 % is a negative result to be recorded as such.
Expected memory/op cost (ESTIMATED): 7 attribute-value rows (2+2+2 values plus one spare) x 4,608 bits x 5 bit =
about 20 KB, less than the 10-class flat table of 28.8 KB; inference = 3 reads of the active-bit rows (the same
active bits, 2 rows per attribute) plus an 8-row match: about 6/10 of the current decision's counter additions plus
a few XORs; no multiplier. Learning: same writes as today.
Uncertainty, stated plainly: the attribute labels are perfectly correlated with the class in the training set, so an attribute table can learn
"this is a coat" instead of "this has long sleeves"; held-out classes decide it. Sleeve length and collar are
not pixel-local in a 28x28 grey image; paper 9 shows that even with the additive encoding two pairs stayed at 0 %.
Standing caution applies: the labels (attribute values) are used in training only, never at test time.
Second dataset to test the same code: EMNIST letters with hand-assigned stroke attributes (closed loop, ascender, descender, vertical bar),
leave-one-letter-out; same criterion.

### Design 2: serial peeling for superposed parts (the binding problem, matrix-free)

Idea. Make the code answer "what are the parts?" when two objects share the picture, using the mechanism of the
resonator (find one factor, explain it away, look again) in the form of L's own memories. Procedure: (1) score the
mixed code against the class table with the usual sparse lookup, take the best class c1; (2) from c1's dream counts
build the mask of bits that c1 explains (bit count above half the class count: a comparator, no division); (3) clear
those bits (AND-NOT on a 576-byte register) and score again to get c2; (4) optionally re-score c1 with c2's explained bits cleared and repeat once or twice
(resonator-lite). The dream memory (10-bit per-class on-counts) already exists on chip, so no new storage.
Minimal experiment (SIMULATED): build two-item scenes by overlaying two different Fashion-MNIST items (pixelwise maximum
with a horizontal offset of 0, 4, 8 pixels to vary overlap), encode with the existing encoder. Methods: top-2 of
the plain table (baseline); peel; peel with re-score; and a "pair-trained" conjunction table trained on 30 of the 45
class pairs and tested on the 15 held-out pairs (expected to fail on held-out pairs). Success criterion: both classes
named correctly (unordered) at offset 8: peel >= 20 points above top-2 and held-out-pair accuracy of peel not worse than
seen-pair accuracy by more than 5 points; at offset 0 (heavy overlap) we only record the cliff. Single-item accuracy must not fall (no-regression rule).
Cost (ESTIMATED): two to four sparse scoring passes instead of one (2 to 4 times the energy per decision for mixed
scenes only; single items unaffected if a "surprise" signal triggers the second pass), plus a 4,608-bit AND-NOT.
Uncertainty: overlapping garments erase each other's evidence (the paper's occlusion remark); the hash-free
code may not separate classes sharing most bits (shirt/T-shirt/pullover). A negative result gives us the capacity
cliff for our code, which is useful in itself.

### Design 3: relation literals for abstract "same/different" (variable detachment without symbols)

Idea (from the relational Tsetlin machine and the logic gate view). Give clauses a new literal type: the agreement of a
code bit between two parts, XNOR(bit_i of part A, bit_i of part B), possibly also with shifts of one cell to tolerate
misalignment. A clause made of such literals fires when A and B agree on many positions, **regardless of what they are**.
It is the pixel-level counterpart of child(Z1,Z2) <- parent(Z2,Z1): the clause never names the content.
Minimal experiment (SIMULATED): pairs (left, right) of Fashion-MNIST items; target same class or different. Train on pairs from classes 0-5 only;
test on pairs from the unseen classes 6-9 (and on mixed pairs). Baselines: clause learner on the concatenated 2 x 4,608 literals
(learns the seen classes, expected near chance on unseen); popcount of XNOR with a single threshold (no learning).
Compact form: split the 4,608 bits into 36 regions, quantise each region's match count into 4 levels, and learn clauses over
these 72 relation literals plus their negations.
Success criterion: unseen-class same/different accuracy >= 85 % (flat expected below 65 %) with seen-class accuracy >= 90 %.
Also try the "episode randomisation" borrowed from meta seq2seq: during training randomly permute class identities so no class-specific bit is
useful beyond the relation.
Cost (ESTIMATED): 4,608 XNOR gates plus a region popcount; literal state about 72 x 2 bits per clause; 100 clauses is
under 2 KB; no multiplier.
Uncertainty: same-class pictures differ in shape; strict bit agreement on a shifted garment may be low (so the region quantisation
and tolerance shifts matter); the task is easy in the sense that a similarity threshold already may reach 80 %, so the
claim to test is only that learned relation clauses beat both baselines and that the same relation literals can be reused for a third task
(odd-one-out in a triple). If the plain threshold already hits the target, the design shows only that matching is
cheap, not that clauses compose.

### Run order and ranking

1. Design 3 first: cheapest, one afternoon, tests whether clause literals can be relations.
2. Design 1 next: the core capability (held-out attribute combinations), uses the existing table rule.
3. Design 2 if Design 1 shows that attributes are separable; it is the route to scenes with several parts.
Proposed top method: **Design 1** (additive, role-tagged attribute tables plus a small signature clean-up), because
paper 9 gives direct evidence for exactly this contrast, it costs less memory than today's flat table, and a pass would be the first
composition result for L.

### What is out of reach under our rules (and why)

- Dense-vector VSA with circular convolution, phasors or tensor products (HRR, FHRR, TPR, MBAT): multiplies or matrices.
- A resonator network in its published dense form; a sparse-block-code resonator exists in the literature (not read) and is the next thing to read before Design 2 is extended.
- Systematic generalisation on language-like tasks (SCAN) with a sequence model: needs recurrent state and attention; a counting system has no
  published result there.
- Learning the symbols themselves (object parts, attributes) from pixels without labels: no matrix-free method known to us.
- ARC-level rule induction and DreamCoder-style program search: combinatorial search with a learned guide; only the
  "promote a frequent conjunction to a new literal" step (library learning by counting) is a candidate, and it is a
  longer project than the six to eight month horizon allows.
- Anything that depends on binding by synchrony, or on hippocampal conjunctive coding, as a mechanism: not read here; the survey's own
  judgement is that synchrony needs many time steps and cannot be stored in long-term memory directly, which fits
  our need for a static, countable code.

### Honest summary of uncertainty

The strongest evidence is negative and cautionary: conjunction-only codes do not generalise to unseen combinations (0 % in
paper 9, 1 % in paper 5), and even the additive repair reached only partial scores (up to 72 %, two pairs at 0 %). No paper in
the logic-gate or Tsetlin families measures held-out-combination generalisation, so any success of Designs 1 to 3 would be
new evidence, and a failure is likely enough that each design must report negative results. All design numbers above are
targets and ESTIMATED costs, not results. Fashion-MNIST attribute labels are our own assignment from class names.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
