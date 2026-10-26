---
title: Thinking research 2 - working memory and steps over time
tags: [spark, research, papers]
---

# Thinking research 2: working memory and steps over time

Question: what is a matrix-free recurrent core, a small state carried between steps, updated by local rules and lookups,
that can hold a hypothesis, revise it and check it, and is trained without backprop-through-time? Rules in force:
no dense matrix-vector products, no multiplies, no backprop in the chip design. Allowed: scans, event-driven sparse
lookups, hash and table lookups, counters, small state, local rules, clauses (AND of literals), sparse binary codes.
All numbers below are **as reported by the authors** unless marked otherwise. Nothing here was run by us.

## (a) Papers read

Reading depth is stated honestly. PDFs were downloaded from arXiv and converted to text. "Fully" means the whole method
and results text was read. "Partly" means the abstract, introduction, method and the key results or theorems were read, and
appendices and long experiment sections were skimmed or searched, not read line by line.

| # | Citation | Year | Read fully |
|---|---|---|---|
| 1 | Hawkins, Ahmad. Why Neurons Have Thousands of Synapses, A Theory of Sequence Memory in Neocortex (arXiv 1511.00083) | 2015/16 | Partly (theory, network model and Fig. 6 text read; methods equations skimmed) |
| 2 | Ramsauer et al. Hopfield Networks is All You Need (2008.02217) | 2020/21 | Partly (abstract, intro, update rule, theorems; experiments skimmed) |
| 3 | Krotov, Hopfield. Dense Associative Memory for Pattern Recognition (1606.01164) | 2016 | Partly (abstract and intro only) |
| 4 | Bricken, Davies, Singh, Krotov, Kreiman. Sparse Distributed Memory is a Continual Learner (2303.11934) | 2023 | Partly (abstract, intro) |
| 5 | Bricken, Pehlevan. Attention Approximates Sparse Distributed Memory (2111.05498) | 2021 | Partly (abstract, intro) |
| 6 | Gauthier, Bollt, Griffith, Barbosa. Next Generation Reservoir Computing (2106.07688) | 2021 | Partly (abstract, method, training-size passages) |
| 7 | Schlag, Irie, Schmidhuber. Linear Transformers Are Secretly Fast Weight Programmers (2102.11174) | 2021 | Partly (abstract, capacity and delta-rule sections) |
| 8 | Gu, Dao. Mamba: Linear-Time Sequence Modeling with Selective State Spaces (2312.00752) | 2023/24 | Partly (abstract, intro, selection mechanism and synthetic tasks) |
| 9 | Orchard et al. Efficient Neuromorphic Signal Processing with Loihi 2 (2111.03746) | 2021 | Partly (abstract, intro) |
| 10 | Kumar, Raj, Shafik, Roy. Compressed Recurrent Feedback in Tsetlin Machines: A Reproducible Boolean-FSM Study (2609.06133) | 2026 | **Yes** (all sections) |
| 11 | Liu, Min, Zettlemoyer, Choi, Hajishirzi. Infini-gram (2401.17377) | 2024 | Partly (abstract, intro, definition of the unbounded n-gram model) |
| 12 | Geiping et al. Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach (2502.05171) | 2025 | Partly (abstract, architecture, training-recipe passages) |
| 13 | Jolicoeur-Martineau. Less is More: Recursive Reasoning with Tiny Networks (2510.04871) | 2025 | Partly (abstract, method with the code listing, ablation passages) |
| 14 | Goyal et al. Coordination Among Neural Modules Through a Shared Global Workspace (2103.01197) | 2022 | Partly (abstract only) |

**Not read (be careful with anything said about these):** Jaeger's echo state network and Maass's liquid state machine
originals (only represented here through paper 6); Kanerva's 1988 book on sparse distributed memory (papers 4 and 5
stand in for it); hippocampal replay and episodic-memory models (no paper downloaded; nothing is claimed from them);
Soar and ACT-R chunk papers (no paper downloaded; only the global-workspace deep-learning paper 14 was opened); the
Recurrent Tsetlin Machine original that paper 10 cites (not found as a full text, only reached through paper 10's
description); the Tsetlin machine word-embedding paper (2301.00709: downloaded, not read). These gaps are real: a second
pass is needed before any of these topics is used in a claim.

## (b) Per paper

### 1. HTM sequence memory (Hawkins, Ahmad)

- **Mechanism.** A sequence is held as sparse activity over mini-columns (2% active: 40 of 2048). Each mini-column holds
  several cells. The same input activates the same columns, but which cells fire inside a column encodes the
  *context* in which it occurred. Cells have dendritic segments that act as coincidence detectors (threshold on the number of active
  synapses). If a segment sees a learned pattern of the previous step's active cells, the cell becomes "predicted"
  (depolarised); a predicted cell wins the competition in its column, so a correctly predicted input is very sparse. An
  unpredicted input makes the whole column fire ("burst"), which signals surprise and lets the network start learning a
  new transition. Learning is local: a segment's potential synapses have a scalar permanence that is nudged up or down by a
  Hebbian rule; a synapse counts as connected above a threshold (weight is then binary).
- **Key numbers (reported).** Segments recognise patterns with 15-40 synapses; doubling the synapses to a 50% noise
  tolerance raises false-positive probability only to 1.6e-18 under sparse codes. In the artificial test the maximum possible
  accuracy is 50%; a high-order network reaches it, a first-order one (one cell per column) about 33%. About 40%
  cell death has minimal effect; after a change of sequences the network re-learns. Capacity scales linearly with synapses per neuron.
- **Transfers.** (i) The two-representation trick (the same sparse code plus a context choice inside it) is exactly "state
  carried between steps" as a sparse bit set. (ii) Surprise = burst is the same signal as our "write only when wrong". (iii) Prediction
  is a lookup of the previous active set against stored sets (a table or hash keyed by set), no matrix. (iv) Multiple
  simultaneous predictions are just a set of candidates. (v) Online learning with only local rules.
- **Does not transfer.** Permanence is a scalar updated per synapse (we would replace it with a small counter, fine);
  the paper reports only toy sequences, no standard language or image benchmark; no hardware numbers; the cell
  competition is described rather than costed.

### 2. Modern Hopfield networks (Ramsauer et al.)

- **Mechanism.** An energy function with an exponential interaction stores exponentially many patterns; one update of the
  state toward a softmax-weighted mixture of the stored patterns retrieves a pattern (a stored one, a mixture of a subset, or the
  global average). The update is mathematically the transformer attention rule. They use it as a differentiable "Hopfield
  layer" inside deep networks.
- **Key numbers (reported).** Storage up to 2^(d/2) for binary patterns in the modern binary version (the classic binary
  Hopfield network stores about 0.138 d); retrieval in one update with exponentially small error for well-separated patterns.
- **Transfers.** The idea of retrieval as a minimum of an energy that is "Hamming mismatch to stored items" and of three kinds of
  fixed point (single memory, mixture of a few, global average). Our counting table is already a stored-pattern memory;
  an iterative "settle" loop that re-reads the table with the current guess is the binary analogue and needs only popcount,
  compare, add.
- **Does not transfer.** The softmax over all stored patterns and the continuous states are dense real-valued products.
  Everything they do around the layers is trained with backprop.

### 3. Dense associative memory (Krotov, Hopfield)

- **Mechanism (abstract/intro only).** Higher-order interactions let a memory store far more patterns than neurons; a one-hidden-layer feed-forward net
  with rectified-polynomial activations is dual to this memory; the family interpolates between feature matching and
  prototype modes. Tested on XOR and MNIST.
- **Transfers.** The prototype versus feature-matching view supports our clause layer (features) and prototypes (counts) as two modes of one memory.
- **Does not transfer.** The practical form is a trained dense layer. Not read beyond the intro: no further claim.

### 4. Sparse Distributed Memory as a continual learner (Bricken et al.)

- **Mechanism.** A modified MLP following the cerebellum-like SDM: top-k activation, no bias, L2-normalised and
  non-negative weights and data. All components were found necessary for avoiding forgetting. Two fixes: a "GABA switch"
  style fix for dead neurons under top-k, and removal of stale optimiser momentum for sparse updates.
- **Key numbers (reported).** Strong continual learning without replay or task labels; with EWC it reaches (as they say) state of the art on
  CIFAR-10 continual learning (exact figures not read).
- **Transfers.** Confirms our own design: sparse k-winner codes plus local writes keep old memories safe. The dead-neuron problem
  has a twin in our world: hash slots that are never used.
- **Does not transfer.** Weights are real and trained by SGD.

### 5. Attention approximates SDM (Bricken, Pehlevan)

- **Mechanism.** SDM reads by summing the contents of storage locations whose address is within a Hamming radius of the query;
  the number of addresses in the intersection of two hyperspheres falls off roughly exponentially with distance, which
  approximates the softmax. So attention is SDM's read in disguise; checked in pre-trained GPT2 with query-key
  normalisation.
- **Transfers.** The binary SDM read is the original matrix-free form: hash or address match by Hamming distance, then
  sum of stored counters. A working memory read in our chip is one SDM read over a few thousand slots, with popcount and add only.
- **Does not transfer.** The attention view uses real keys and values.

### 6. Next Generation Reservoir Computing (Gauthier et al.)

- **Mechanism.** The classic reservoir is a fixed random recurrent network; only a linear readout is trained. They show that
  nonlinear vector autoregression, a state made of the last k observations (spaced by s) and their polynomial products,
  with a linear readout, matches it, with no random matrices.
- **Key numbers (reported).** Training with only 400 data points per variable for Lorenz-type tasks; warm-up of only s*k steps (for
  example 2) versus thousands to hundreds of thousands of points for a classic reservoir; fewer metaparameters.
- **Transfers.** This is the strongest hint for us: a "state" can be *just a window of the recent past plus nonlinear
  features of it*, with a trained readout. Our version: the window of last k codes, hashed (AND combinations are
  clauses) and a counting readout. The finding also warns us: see paper 10.
- **Does not transfer.** The readout is ridge regression, a matrix solve. Ours must be counters per (feature, class).
  The random reservoir itself is a dense random matrix.

### 7. Fast weight programmers (Schlag, Irie, Schmidhuber)

- **Mechanism.** Linear attention is a fast-weight memory: at each step add an outer product of key and value to a matrix.
  They show a capacity limit (overcapacity when the sequence length exceeds the key dimension) and replace the purely additive write by
  the delta rule: read what the memory currently returns for the key and write only the *difference* from the desired value, with a
  learned rate. This corrects wrong associations instead of piling up.
- **Transfers.** The delta rule's *idea* is exactly our "write only when wrong, by the error": a sparse key (hash) addresses a
  small counter vector, read it, compare with what actually came, add the error as a clipped integer step. This is
  a write-with-correction working memory with no matrix: a hash table of small counters.
- **Does not transfer.** Keys and values are dense vectors, the memory is a dense matrix, the slow net that produces keys and
  rates is trained by backprop. This is the "L model" style design that the founder's rule asks us to replace.

### 8. Mamba selective state spaces (Gu, Dao)

- **Mechanism.** A linear recurrence h_t = A h_{t-1} + B x_t with output C h_t, whose parameters depend on the current
  input (selection), so the state can keep or forget content-dependently. Solves selective copying and induction heads
  that fixed linear recurrences cannot. A hardware-aware parallel scan computes it.
- **Key numbers (reported).** 5x higher inference throughput than Transformers; Mamba-3B beats same-size Transformers and matches ones twice its size.
- **Matrix-free or not.** Matrix-free part: the *scan* (a fixed-size state, constant memory per step, one update per token) and the
  diagonal form of A (elementwise). Not matrix-free: B, C and the input projections are dense layers, the selection
  is a learned dense map, and training is backprop. What we take: the *selection* idea (the input decides keep, overwrite, or
  ignore) can be a lookup: hash of the current token chooses an action from a small table.
- **Does not transfer.** The learned dense projections and gradient training.

### 9. Loihi 2 stateful neurons (Orchard et al.)

- **Mechanism (abstract and intro only).** Programmable stateful spiking neurons, for example resonate-and-fire neurons, process streams; a bank of them
  replaces a Fourier transform.
- **Key numbers (reported).** Resonate-and-fire STFT with 47x less output bandwidth than a conventional STFT; optical flow with
  over 90x fewer operations than a DNN solution. Classification results were trained with backprop.
- **Transfers.** Stateful event-driven units with a few state variables per unit support our existing shift-add resonator cochlea (already
  bit-exact in our RTL). A step-carried state in hardware can be a few integers per unit that decay by shifts.
- **Does not transfer.** The trained recurrent networks need surrogate gradients; I did not read how they cost the connectivity.

### 10. Compressed recurrent feedback in Tsetlin machines (Kumar et al.), read fully

- **Mechanism.** A Recurrent Tsetlin Machine feeds its own clause outputs of step t back as extra input literals at step t+1. Raw
  feedback makes the state as wide as the clause bank (480 bits here). They fold the clause outputs with XOR into 48 bins through a
  fixed random assignment, keep two exponential moving averages (coefficients 0.3 and 0.9), threshold each at 0.5 back to bits, giving a 96-bit state. Each
  member of a 5-member ensemble votes. Training is one causal predict-then-update per step with ordinary Tsetlin feedback: no gradient through time.
  Benchmark: hidden Boolean finite-state machines (64 and 256 states), label is the parity of the next state.
- **Key numbers (reported).** 144 TM runs and 90 neural runs. Compressed model 61.47 +/- 6.74% and 62.94 +/- 9.92% on the two families. Raw feedback is higher by
  only 0.72 and 0.58 points (intervals include zero) at 10x the state width and 3.7-4.4x host time. GRU and LSTM were
  4-6.6 points better; the Transformer 4.6-5.5 points worse. **The no-feedback control (only the last two symbols plus the previous prediction)
  was slightly better (+0.43 and +0.89 points): clause feedback did not help.** A nearest-centroid probe showed the 96-bit state does *not*
  identify the hidden state (top-1 and top-5 recovery below random). Ensembling was the only part with a clear gain
  (-1.77 and -2.29 points when removed).
- **Transfers.** (i) The honest warning: fed-back clause bits carried no usable memory on this task; a design that says "clauses
  give recurrence" must be tested against a window-only control from day one. (ii) XOR folding plus fast and slow counters is cheap
  and matrix-free, a candidate way to keep a state of fixed width. (iii) Training by local feedback with no BPTT works at the level of "does not crash", but does not yet learn to
  use the state. (iv) Their predict-then-update ordering is the right causal protocol for our tests.
- **Does not transfer.** The EMA uses real coefficients (we would use shifts: m += (q*K - m) >> 2). Threshold 0.5 on
  a mean is fine. The weak result means we should not copy the design as is; the likely reason (my reading, not
  proved): a clause bank trained only on next-label feedback has no pressure to put useful memory into its outputs.

### 11. Infini-gram (Liu et al.)

- **Mechanism.** An unbounded-order counting language model. The prediction uses the longest suffix of the prompt that appears at
  least once in the corpus (back off only when the denominator is zero), with the counts read from a suffix array rather than a
  precomputed table.
- **Key numbers (reported).** Index 7 bytes per token; counting query under 20 ms, other queries under 200 ms; trained on up to 5 trillion tokens; 47%
  next-token accuracy with the infinity-gram model against 29% for conventional small-n n-grams; "sparse" estimates (only one
  possible next token) are the most predictive; interpolation with neural LMs cut perplexity by up to 73%.
- **Transfers.** For a working memory: "the longest context that has been seen before decides, and a unique continuation is
  highly reliable" is a confidence rule that costs nothing (store order of match and count). Our hashed counters can keep a
  per-order flag "seen before" and a state "longest matching order" as the carried state; that is a very small, honest memory
  of how much context the system recognises.
- **Does not transfer.** The suffix array is a big on-disk structure with a log-time search, not a chip table. We
  need the hash version: one slot per (order, hash).

### 12. Recurrent depth (Geiping et al.)

- **Mechanism.** A transformer split into prelude, a recurrent core block, and coda. At test time the core is iterated r times from a random initial
  state, with the embedded input injected at each pass; more iterations = more compute, no extra tokens. Training samples a random number
  of iterations and backpropagates only through the last few (truncated BPTT).
- **Key numbers (reported).** 3.5B parameters, 800B tokens; accuracy on reasoning benchmarks rises with the number of
  recurrences, up to a compute load equivalent to about 50B parameters; easy tasks converge earlier than GSM8K.
- **Transfers.** The *protocol*: one block reused, an adjustable number of steps, a convergence test, the input injected every step, random
  initial state for robustness. Early stop when the state stops changing is a free halting rule for a counter-based loop.
- **Does not transfer.** Everything inside is dense matrices and backprop. This does show that a *truncated* credit window (the last few steps) is considered enough.

### 13. Tiny Recursive Model (Jolicoeur-Martineau)

- **Mechanism.** A single small 2-layer network is applied recursively: it updates a latent "reasoning" state z several times and then
  updates the current answer y from z, repeating. Supervision is applied to the answer after each outer cycle ("deep supervision", the state is
  detached and carried on), and gradients flow only through the last recursion (1-step approximation to avoid BPTT). A learned halt
  head decides when to stop.
- **Key numbers (reported).** 7M parameters; 45% on ARC-AGI-1 and 8% on ARC-AGI-2; Sudoku-Extreme 55% -> 87%, Maze-Hard 75% -> 85%
  over HRM; deep supervision roughly doubled accuracy over a single supervised pass (19% to 39% in the HRM ablation they cite).
- **Transfers.** The most useful structural idea: two pieces of state, a *hypothesis* (the answer y) and a *scratch* (z);
  after every cycle the hypothesis is scored against the target, and that local score is the only teaching signal, so no BPTT is needed. For us this is
  exactly the surprise-driven write at each step. Detaching the state between supervision steps is the same as "no credit
  through time".
- **Does not transfer.** Dense layers and gradient training. Their gains are on small structured puzzles, not language or noisy images.

### 14. Global workspace (Goyal et al.)

- **Mechanism (abstract only).** Specialist modules communicate only through a small shared bandwidth-limited workspace; they
  compete for write access. Argued to help specialisation and synchronisation.
- **Transfers.** A design principle: a *small* state with a writing competition (only the k most surprised or most confident modules write). That is a
  top-k selection over counters, matrix-free.
- **Does not transfer.** Their modules use attention and learned dense maps. I did not read beyond the abstract.

## (c) Synthesis: what a matrix-free working memory needs

1. **State.** A small fixed-size bit/counter set, of three kinds: (a) a *window* of the last k sparse codes, hashed (it is what
   the reservoir paper and the no-feedback control of paper 10 both show is already strong); (b) a *hypothesis*: a k-of-n set of
   candidate labels/contexts with small saturating counters as evidence (HTM predicted cells, Hopfield mixture states,
   TRM's y); (c) a *confidence/order flag*: how long a context was recognised (infini-gram's effective n). Total target: tens of bytes per stream, plus the shared tables.
2. **Update rule.** Event-driven: hash the (state, input) pair, read counters, add evidence with shifts (decay by `>>`),
   take the top-k, and let a surprise (prediction wrong or mismatch above a threshold) open a write. HTM's burst, delta rule's
   write-the-difference, and our existing "write only when wrong" all agree.
3. **Readout.** Counting tables keyed by (state feature, output). Not a regression solve. The readout is the only trained part, as in a reservoir,
   but trained by counts.
4. **Checking.** A hypothesis is compared with the input by a *generative check*: our dream memory produces the expected bits for the hypothesised class,
   and the Hamming mismatch with what was seen is the energy (Hopfield view, TRM's answer scoring). Low mismatch = hold, high = revise.
5. **Fixing errors without BPTT.** All sources agree on the same four tools: (i) local per-step errors (the paper-10 causal order: predict, then update);
   (ii) truncated credit: only the last 1-2 steps count (recurrent depth, TRM's 1-step); (iii) deep supervision: a label/score at each
   cycle, state detached; (iv) the state is *built from inputs*, not from learned dynamics, so there is nothing to back-propagate
   (reservoir/NG-RC: the window is the state). Our rule: the state is a deterministic function (hash and counters with
   fixed decay) and only counting tables are learned.
6. **The warning.** Paper 10 is the only matrix-free recurrent learner I read in full, and its recurrence did not beat a window. Any new design must beat a *window-only*
   control; otherwise the "memory" is a mirage. Also report whether the state can be decoded (their probe).
7. **Honest uncertainty.** Several of the papers were read partly (see table). The proposals below are untested; costs are ESTIMATED by me from the tables in the repo's design (see the project memory), not measured.

## (d) Our own method sketch

Notation: the image code is the existing 4,608-bit sensory code; the class table is the 5-bit counter table; dream memory is the 10-bit per-class count table. None of the designs adds a multiplier or a matrix.

### Design A. Glimpse loop with a hypothesis set and a dream check (image, several steps)

- **State.** H = a set of up to 3 candidate classes with a 4-bit evidence counter each (12-ish bits), plus a 96-bit XOR-folded "seen so far" mask
  (which of the 4,608 code bits have been observed) and a step counter.
- **Step.** (1) Reveal a portion of the code (an image region or the next occluded patch). (2) Add the table's counters for the revealed bits only to each candidate's
  evidence (integer add, restricted to bits not yet used); decay old evidence by a shift. (3) *Check:* dream the top candidate's expected bits on the *revealed* region (xorshift draw below the class count, as the chip already does); the mismatch is a popcount. (4) If the mismatch exceeds a threshold, demote that candidate and promote the next; if two steps in a row change nothing, halt (recurrent-depth's convergence idea).
- **Training.** Nothing new is trained for the table: the existing surprise-driven writes apply. The threshold (mismatch needed to demote) is learned by counting the mismatch of correct versus wrong hypotheses on the training set, a 2-bucket histogram per class.
- **Minimal experiment.** Fashion-MNIST codes (and digits as a check). Make test images partly hidden (random 50% of the 5x5-window positions hidden) or noisy (bits flipped at 10% and 20%). Compare (a) single pass on all revealed bits, (b) the loop with 4 steps revealing a quarter each, (c) the loop with the check disabled (ablation, plays the role of the no-feedback control).
- **Success criterion.** (b) at least +3 points over (a) at 50% occlusion on 3 seeds, and no loss on clean images against the shipped settings (no-regression rule); (b) strictly above (c) by at least 1 point, otherwise the check adds nothing and the design is recorded as failed.
- **Expected cost (ESTIMATED).** State about 20 bytes per stream. Per step: table reads of the revealed bits for 3 candidates (about a quarter of 4,608 bits x 3 = 3.5k adds) and a dream of the same quarter (about 1.2k draws and compares). About 4-5x the one-pass cost for 4 steps, still adds only. Risk: if the evidence from the quarter is nearly as informative as the whole, the loop will not gain; also dream bits are independent, a known limit.

### Design B. Counting sequence core with a longest-context state (label sequences and characters)

- **State.** For each of 4 orders (1, 2, 4, 8 previous elements) a hash of the context; a flag per order "this context was seen before"; the longest seen order (infini-gram's effective n); plus the HTM-style context choice: the hash of the *predicted-and-confirmed* previous pair.
- **Step.** Look up the 4 counters (2-bit or 4-bit, per hashed (order, context, next)); predict from the longest seen order that has a confident (unique or dominant) continuation; fall back to shorter. After the true next element arrives: increment its counter at all orders, and *only if the prediction was wrong* also allocate (burst) a new longer-order entry. This is online, one pass, delta-rule-style (write the difference).
- **Minimal experiment (the paper-10 lesson built in).** (1) Next-element prediction on sequences of class labels produced by a small hidden finite-state machine with outputs that depend on an event 6-12 steps back (beyond a window of 4); also the same on our character counting model's text. (2) Controls: the window-only model (orders 1-4 only) and a first-order model. (3) Report decodability: can the longest-order flag plus the hashes distinguish the hidden states (nearest-centroid probe as in paper 10).
- **Success criterion.** Beats the window-only control by at least 2 points on the long-dependency FSM (3 circuit seeds, 3 data seeds) and matches it on short-dependency tasks; on text, bits per character no worse than the current counting model. If it ties the window-only control, record "recurrence not needed here" as the paper did.
- **Expected cost (ESTIMATED).** 4 orders x 2^20 slots x 4 bits = 2 MB (fits PSRAM, or 2^18 slots per order = 512 KB in block RAM terms with some collisions). 4 hash lookups and increments per element; no multiplies (hash by XOR and shifts as the repo already does).

### Design C. Look-predict-verify: recogniser and counting model joined by top-down expectation

- **State.** The last k recognised class labels as tokens (hash), plus the pending prediction from Design B (the top-2 next labels with confidence), plus the hypothesis set from Design A.
- **Step.** The sequence core predicts the next label(s) before the image arrives. The prediction is added to the recogniser's class evidence as a *small integer prior* (HTM's apical expectation, one add per class). The recogniser reads the image; if the top class disagrees with a confident prediction, run one extra glimpse step (Design A) before accepting; accept and write the pair (recognised label, next) into the sequence tables. The writes happen only on disagreement or on a low margin (surprise).
- **Minimal experiment.** Build a stream of Fashion-MNIST items whose classes follow a Markov or FSM rule (for example class sequence "shirt, trouser, shoe..." with 90% rule-following), add noise to the images at 0, 10, 20% bit flips. Measure recognition accuracy with the prior versus without, and next-label accuracy using recognised versus true labels.
- **Success criterion.** At 20% noise, accuracy with the prior at least +3 points over without, equal at 0% noise (no regression), and no worse than without when the stream is random (the prior must learn to be weak: counts give low confidence). Failure mode to watch: errors in the recognised labels poison the sequence table (a confident wrong prior feeding back); the disagreement rule and the "write only on low margin" rule are the guard.
- **Expected cost (ESTIMATED).** Prior: 10 adds per image. Sequence core as in B. Extra glimpse when disagreeing (a fraction of images). State a few tens of bytes.

### Ranking and what I would do first

Best first: **Design B** (cheapest, the clearest control, and it works on our character model with no new image work), then **Design A** (the genuine "hold, revise, check" demonstration, built on the dream memory that exists), then C (needs both to work). The decisive test shared by all three is the window-only control, because the only matrix-free recurrent learner I read in full (paper 10) failed exactly that test. Uncertain: whether sparse independent dream bits are accurate enough to act as a verifier (Design A), whether the hashed context state decodes to the real hidden state (Design B), and whether noisy recognised labels destabilise the loop (Design C). None of this has been run.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
