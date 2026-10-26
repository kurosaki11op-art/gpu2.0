---
title: Thinking research 2 - working memory and steps over time
tags: [spark, research, papers]
---

# Thinking research 2: working memory and steps over time

Question: what is a matrix-free recurrent core, a small state carried between steps, updated by local rules and lookups,
that can hold a hypothesis, revise it and check it, and is trained without backprop-through-time?
Rules in force: no dense matrix-vector products, no multiplies, no backprop in the chip design. Allowed: scans,
event-driven sparse lookups, hash and table lookups, counters, small state, local rules, clauses (AND of literals),
sparse binary codes. All numbers below are **as reported by the authors** unless marked otherwise. Nothing here was run by us.

Revision note (second pass): the first version of this note read most papers only partly. This version re-read nine papers
through their whole main text and corrected four claims that the full text showed to be wrong or too strong (TRM
gradients, Loihi 2 arithmetic, the Hopfield capacity statement, the NG-RC task type). The corrections are marked
"(corrected)" below.

## (a) Papers read, and how much

PDFs were downloaded from arXiv and converted to text; every page of the main text of the "Yes" papers was read.
"Main text" means everything up to the references; appendices are listed separately. No PDF failed to download.

| # | Citation | Year | Read fully |
|---|---|---|---|
| 1 | Hawkins, Ahmad. Why Neurons Have Thousands of Synapses (arXiv 1511.00083) | 2015/16 | **Yes**, main text, methods and references. The figures and the S1 supplement are not in the PDF text. |
| 2 | Gauthier et al. Next Generation Reservoir Computing (2106.07688) | 2021 | **Yes**, main text and references. The supplementary material is not in the PDF. |
| 3 | Orchard et al. Efficient Neuromorphic Signal Processing with Loihi 2 (2111.03746) | 2021 | **Yes**, all of it. |
| 4 | Kumar, Raj, Shafik, Roy. Compressed Recurrent Feedback in Tsetlin Machines (2609.06133) | 2026 | **Yes**, all of it. |
| 5 | Bhattarai et al. Tsetlin Machine Embedding (2301.00709) | 2023 | **Yes**, main text. |
| 6 | Jolicoeur-Martineau. Less is More: Recursive Reasoning with Tiny Networks (2510.04871) | 2025 | **Yes**, main text and conclusion. Failed-ideas list and hyperparameter appendix not read. |
| 7 | Liu et al. Infini-gram (2401.17377) | 2024 | **Yes** for sections 1-7 and appendix A (engine). Appendices B-E (decontamination, evaluation details, extra related work) not read. |
| 8 | Schlag, Irie, Schmidhuber. Linear Transformers Are Secretly Fast Weight Programmers (2102.11174) | 2021 | **Mostly**: sections 1-4, 6, 7 read; the kernel section 5 and the appendices only skimmed. |
| 9 | Bricken et al. Sparse Distributed Memory is a Continual Learner (2303.11934) | 2023 | **Main text** (sections 1-5, start of 6); appendices (about two thirds of the PDF) not read. |
| 10 | Ramsauer et al. Hopfield Networks is All You Need (2008.02217) | 2020/21 | **No**: sections 1-4 up to the start of the experiments read; the remaining experiments and the long proof appendix not read. |
| 11 | Geiping et al. Scaling up Test-Time Compute with Latent Reasoning, recurrent depth (2502.05171) | 2025 | **No**: sections 1-4 and the exit-criterion and saturation passages read; the rest of the evaluation and applications skimmed. |
| 12 | Gu, Dao. Mamba (2312.00752) | 2023/24 | **No**: sections 1-3.3 (start) and the synthetic-task results read; architecture, other experiments and appendices not read. |
| 13 | Bricken, Pehlevan. Attention Approximates Sparse Distributed Memory (2111.05498) | 2021 | **No**: introduction and the SDM review (section 1) read only. |
| 14 | Goyal et al. Coordination Among Neural Modules Through a Shared Global Workspace (2103.01197) | 2022 | **No**: sections 1-2 read; experiments only skimmed. |
| 15 | Krotov, Hopfield. Dense Associative Memory for Pattern Recognition (1606.01164) | 2016 | **No**: abstract and introduction only. |

Nine papers (1-9) are read through the whole main text, which meets the "at least 8" target; papers 8 and 9 and 7 keep
unread appendices as listed. Papers 10-15 are still partial and are used here only for claims that sit in the parts I read.

**Not obtainable or not read at all:** the original Recurrent Tsetlin Machine paper (Xu, Duan, Shafik, Yakovlev, ISTM 2025)
that paper 4 builds on: a web search found only its citation, no full text, so everything about the recurrent Tsetlin
machine here comes from paper 4's description. Jaeger's echo state network and Maass's liquid state machine originals
(reservoir computing is represented by paper 2 only); Kanerva's 1988 book (represented by papers 9 and 13); hippocampal
replay and episodic-memory models; Soar and ACT-R chunk papers (paper 14 stands in for the global-workspace idea).
No claim is made from these.

## (b) Per paper

### 1. HTM sequence memory (Hawkins, Ahmad), read fully

- **Mechanism.** Input is a sparse set of active mini-columns (2%: 40 of 2048). Each column has 32 cells; the same input
  always activates the same columns, and **which cells in a column fire encodes the temporal context**. A cell has up to 128
  distal (basal) dendrite segments; a segment is a coincidence detector: it lists up to 40 synapses onto cells that were
  active at the previous step and fires if more than a threshold theta (about 15) of them are active. A cell with an active
  segment becomes "predicted". When the input arrives, predicted cells in a winning column fire alone and inhibit the rest;
  if no cell in the column was predicted, **all cells burst**, which marks surprise.
- **Learning rule (methods).** Each synapse has a scalar permanence in [0, 1] and counts as connected above 0.5 (weight 1,
  otherwise 0). If a predicted cell becomes active: its active segment gets p+ on synapses to active cells and p- on the
  others (both below 0.1). If a column bursts: choose the cell whose segment had the most input even though it was below
  threshold, reinforce it; if none matches, create a new segment on a random cell and sample its synapses from the currently
  active cells. A very small decay applies to segments that predicted a cell which did not become active.
- **Key numbers (reported).** A network of 2048 x 32 cells with 200 patterns per cell stores about 320,000 transitions
  ((32/0.02) x 200); capacity scales linearly with cells per column and patterns per cell. Doubling the synapses to give 50% noise
  tolerance raises the false-positive probability only to 1.6e-18 under sparse codes. In the toy test (maximum possible
  accuracy 50%) the high-order network reaches 50% and a first-order one about 33%; about 40% of cells can die with little loss; after the
  sequences change it re-learns online. The paper states plainly that it is "a memory of transitions", not of sequences.
- **Transfers.** (i) A segment is an AND over up to 40 literals (cells of the previous step) with an m-of-n threshold: it is
  a Tsetlin-style clause, and the permanence (counter with a connection threshold) is the clause's automaton state. HTM
  sequence memory is therefore a clause bank over the previous step's sparse code, which is matrix-free. (ii) The
  "same columns, different cell" trick gives a state that is the current input plus its context, with no learned dynamics.
  (iii) Burst = surprise = our "write only when wrong". (iv) New segments are allocated only on a miss, from the current active set.
- **Does not transfer.** Scalar permanences with small float increments (replace by small saturating counters). Evidence
  is only on an artificial stream; no language or image benchmark, no hardware cost. Cell competition is described, not costed.

### 2. Next Generation Reservoir Computing (Gauthier et al.), read fully

- **Mechanism.** A classic reservoir is a fixed random recurrent network with only a linear readout trained (ridge
  regression). The paper shows (building on proofs it cites) that a linear reservoir with a nonlinear readout equals a
  nonlinear vector autoregression: the feature vector is the last k observations (spaced by s) plus polynomial products of
  them (all unique quadratic monomials, or cubic), and a ridge-regression readout is the only trained part.
  No random matrix, no reservoir.
- **Key numbers (reported).** Lorenz63 forecasting: k=2, s=1, 28 features, **400 training points per variable**, training
  under 10 ms on one core, forecasts well out to about 5 Lyapunov times; double-scroll circuit: 62 features (cubic); inference of
  an unseen variable: 45 features. Warm-up is only s x k steps (for example 2), against 1,000 to 100,000 for a classic reservoir.
  Estimated 33-162 times cheaper than a typical efficient reservoir (8-41 times for the cubic case). Noise needs a larger ridge
  parameter.
- **Task type (corrected).** All tasks are noise-free continuous chaotic dynamical systems with low dimension, not symbols or images.
- **Transfers.** (i) The state can simply be **a window of delayed inputs plus nonlinear features of them**. For binary
  codes the polynomial monomials are exactly ANDs of window literals, i.e. clauses: a Tsetlin clause bank over a windowed
  code is a binary NG-RC, with a clause-feedback readout instead of ridge regression. (ii) A tiny warm-up is a real advantage
  for a chip that must start working immediately. (iii) Feature count grows as (dk)^p, which tells us to learn which clauses to keep.
- **Does not transfer.** The ridge solve is a matrix inversion. The theory assumes bounded-orbit dynamical systems with
  real values.

### 3. Loihi 2 stateful neurons (Orchard et al.), read fully

- **Mechanism.** Loihi 2 neurons run short programs on fixed-point state. Resonate-and-fire (RF) neurons implement a damped
  oscillator z[t] = lambda e^{i omega dt} z[t-1] + a[t], which equals a sliding-window Fourier coefficient with an exponential
  window and no stored history. A spike is emitted at zero crossings above a threshold, which makes the output temporally sparse.
- **Key numbers (reported).** RF spiking STFT: 47 times less output bandwidth; 94% reconstruction correlation from 5,000
  spikes where a thresholded conventional STFT keeps about 63% with the 5,000 largest values. Optical flow on event data: better
  endpoint error than the baseline network, less than half the neurons, over 10 times fewer synapses and **93 times fewer synaptic operations**.
  A hybrid RF/LIF net trained with a backprop-based tool: 92.14% on a spiking digit-audio set with 226K parameters against 91.25% for an LSTM with
  643K; 88.97% on a keyword task with 238K parameters (91.74% with a convolutional version). A cascade of Hopf resonators gives
  a self-normalising gain control (output held within about 3 dB over several orders of magnitude of amplitude).
- **Arithmetic (corrected).** The first version said "event-driven, no multipliers". The full text says the neural engine has
  **hardware multipliers** and an RF neuron update costs 4 multiply-accumulates. The matrix-free part is the sparse event-driven synapse
  traffic, not the neuron update. The trained speech networks are feed-forward, not recurrent, and use surrogate-gradient backprop.
- **Transfers.** Stateful units with a decaying state and temporally sparse output are the right shape for a carried
  state; our shift-add resonator cochlea already does this. The Hopf self-normalising gain is a candidate for our noise floor.
- **Does not transfer.** The multiplies, the complex arithmetic, and the backprop training.

### 4. Compressed recurrent feedback in Tsetlin machines (Kumar et al.), read fully

- **Mechanism.** A Recurrent Tsetlin Machine feeds its clause outputs of step t back as extra literals at step t+1. Raw
  feedback is as wide as the clause bank (480 bits). They XOR-fold the clause outputs into 48 bins (fixed random assignment),
  keep two moving averages (coefficients 0.3 and 0.9), threshold each at 0.5, giving a 96-bit state; five ensemble members vote.
  Training is one causal predict-then-update per step with ordinary Tsetlin feedback, no gradient through time.
  Benchmark: hidden Boolean finite-state machines (64 and 256 states); label = parity of the next state.
- **Key numbers (reported).** 144 TM runs and 90 neural runs. Compressed model 61.47 +/- 6.74% and 62.94 +/- 9.92%. Raw feedback
  is higher by only 0.72 and 0.58 points (intervals include zero) at 10x the state width and 3.7-4.4x host time. GRU and LSTM were
  4-6.6 points better; the Transformer 4.6-5.5 points worse. **A no-feedback control (last two symbols and the previous
  prediction only) was slightly better (+0.43 and +0.89 points).** A nearest-centroid probe showed that the 96-bit state does not
  identify the hidden state (below random). Ensembling was the only part with a clear gain (-1.77 and -2.29 points when removed).
- **Transfers.** (i) The warning: a recurrence of clause bits showed no benefit over a window on this task; any design here
  must be compared with a window-only control and a decoding probe. (ii) XOR folding plus fast and slow counters is matrix-free
  and keeps a fixed-width state. (iii) The predict-then-update protocol is the right causal test.
- **Does not transfer.** The moving averages use real coefficients (use shifts). The design as it stands did not learn to use
  its state; my reading (not proved by the authors) is that a clause bank trained only on next-label feedback has no pressure
  to place useful memory in its outputs.

### 5. Tsetlin machine embedding (Bhattarai et al.), read fully

- **Mechanism.** A Tsetlin autoencoder over bags of words: input is a set of words (binary vector), the target is the
  presence of one **masked** word, predicted from the others. Conjunctive clauses (AND of positive literals only) are
  weighted by integers; output k = [sum_j w_jk C_j(x with word k forced to 1) >= 0]. Each clause literal has a 4-position memory
  (positions 3-4 = included). Type Ia (recognise, true positive), Type Ib (erase, false negative) and Type II (reject, false
  positive) feedback update memory and weight, each with probability (T - clipped sum)/2T; the masked variable is frozen in the update.
- **Key numbers (reported).** 600 clauses, T=1200, s=5, 2000 rounds with 25 contexts OR-ed per example. Average word-similarity
  Spearman 0.52 against 0.57 for a dense embedding method; classification with a recurrent attention network on six datasets
  comparable to dense embeddings, and a hybrid (80% logical, 20% dense) better by 2-4 points. This is not a sequence model: the
  words are an unordered set.
- **Transfers.** **Masked completion with clauses.** The same trick (predict a hidden part of a binary input from the visible
  part, with the hidden part frozen) is exactly what an occluded-image check needs, and it models dependencies between bits that our
  independent-bit dreams cannot. The weight update needs only integer add and compare.
- **Does not transfer.** No order, no time. Sums of weights times 0/1 outputs are conditional integer adds (fine), but we
  have not costed 600 clauses per class on the chip.

### 6. Tiny Recursion Model (Jolicoeur-Martineau), read fully

- **Mechanism.** One small network (2 layers) is applied recursively. State: the current answer y and a latent scratch z, both carried
  across steps. One cycle: update z n times from (question x, y, z), then update y from (y, z). T-1 cycles run without
  gradient, one with. **Deep supervision**: the answer is scored after each outer cycle (up to 16), the state is detached and carried to
  the next cycle. A halting head is trained with a binary label "answer is already correct".
- **Gradients (corrected).** The first version said TRM uses a one-step gradient. The paper does the opposite: it
  **drops** the one-step approximation used by its predecessor and back-propagates through the whole recursion of one cycle
  (n+1 evaluations). Ablation on Sudoku-Extreme: with the 1-step gradient 56.5%, with full recursion 87.4%.
- **Key numbers (reported).** 7M parameters (5M for the Sudoku version): 45% ARC-AGI-1 (44.6 with attention) and 7.8% ARC-AGI-2; Sudoku-Extreme 55.0 -> 87.4;
  Maze-Hard 74.5 -> 85.3 against the predecessor. State ablation: two features (y, z) 87.4; one feature 71.9; seven features 77.6.
  Weight moving average 79.9 -> 87.4; 2 layers beat 4 layers (79.5 -> 87.4). Data are small but heavily augmented (1000 augmentations per example).
  Tasks are fixed-size grids; the authors note the model is supervised and deterministic.
- **Transfers.** (i) A **hypothesis (y) plus a scratch (z)** as two separate states is clearly better than one or many; if only
  z is kept the solution has to hide in it. (ii) A score on the hypothesis at every cycle with the state carried on is the only
  teaching signal. (iii) Halting trained from "was the answer correct": for us this is a count table of correct/incorrect by
  margin.
- **Does not transfer.** Dense layers and gradient training; the gains need backprop through a full cycle, so the credit window matters
  when gradients are used.

### 7. Infini-gram (Liu et al.), main text and appendix A read

- **Mechanism.** The model predicts with the longest suffix of the prompt that appears in the corpus (back off only when the
  denominator is zero), using counts read from a suffix array, not a table. Indexes are additive and subtractive: counts from disjoint
  datasets are added.
- **Key numbers (reported).** Index 7 bytes per token; counting under 20 ms; 47% next-token agreement overall (conventional
  small n-grams 29%); when the **estimate is "sparse" (only one possible next token), which covers over 50% of tokens, agreement is 75%**; for effective
  n >= 16 agreement is above 75%; median effective n 7, mean 9.1; interpolating with neural models cuts perplexity by up to 73%.
  The authors warn that the mix may be harmful for open-ended generation (odd mistakes make the text digress).
- **Carried state (new from the full text).** The effective n of a token is at most one more than that of the previous token; the engine uses this to
  amortise the search. So **the carried state is a single integer, the current matched order**, updated by +1 or by backing off. Binary lifting
  finds it because "a suffix seen implies every shorter suffix seen".
- **Transfers.** Matched order as state and confidence; unique-continuation as a free confidence flag; additive count merge
  (matches our table merge); a hashed version needs one seen-flag per order. Counts in our table are small saturating counters.
- **Does not transfer.** The suffix array is a large on-disk search structure. Evaluation is on web-scale text with a
  neural model next to it, not a standalone counting model for short streams.

### 8. Fast weight programmers (Schlag, Irie, Schmidhuber), mostly read

- **Mechanism.** Linear attention is a fast-weight memory (an outer-product matrix of key and value). Capacity is limited by the
  key dimension: with d_dot=64 linear attention starts to err at about 60 associations (DPFP variants at 128, 256, 384 as predicted). The
  fix is an error-correcting write: read the value currently stored for the key, interpolate with the new value using a learned rate
  beta, write only the difference.
- **Key numbers (reported).** The delta rule beats the additive rule on the synthetic retrieval test and on language
  modelling by about 1.4-3 perplexity points in both tested sizes. Without truncating context the additive model is above 260
  perplexity while the delta network reaches 27.8 / 29.4 (valid / test) with a state of 0.13M; a Transformer-XL needs a state of
  1.05M to reach 29.3 / 30.1 (about eight times smaller state at similar perplexity).
- **Transfers.** Write the difference, not the sum, and keep the state of fixed size; capacity is bounded by the key space, which
  tells us to size the hash space. A sparse-key version is a hash table of small counters with an error-driven step.
- **Does not transfer.** The memory is a dense matrix, retrieval is a matrix-vector product, and the key/value/rate networks are trained by backprop.

### 9. Sparse Distributed Memory as a continual learner (Bricken et al.), main text read

- **Mechanism.** SDM: neurons have addresses; a write adds the pattern into every neuron within a similarity threshold; a read sums
  the nearby neurons. They turn an MLP into this form: top-k activation (subtract the (k+1)th activation), no biases, L2-normalised weights
  and inputs, positive weights; a "GABA switch" (anneal k from all neurons down) against dead neurons, and plain SGD
  because momentum becomes stale under sparse updates.
- **Key numbers (reported).** Split CIFAR10, class-incremental, 5 seeds, no replay and no task labels: SDMLP (10K neurons) 71%,
  **FlyModel (fixed sparse random weights plus top-k, one epoch per task) 82%**, plain ReLU 21%, EWC 65%, SDMLP + EWC 86%, joint
  training 93%. Smaller k forgets less. Active-dendrite and similar task-incremental methods failed in the class-incremental setting.
- **Transfers.** Confirms that sparse winner-take-all codes plus local writes protect old memories; the FlyModel, which the
  authors describe as fixed weights with top-k, is the closest to our matrix-free rules (I did not read its own paper).
- **Does not transfer.** The SDMLP itself is trained by backprop with real-valued weights. Appendices (many ablations) not read.

### 10-15. Partly read (only the stated parts)

- **Modern Hopfield networks (Ramsauer et al.; sections 1-4 read).** The update xi_new = X softmax(beta X^T xi) retrieves a stored
  pattern in one step, with retrieval error exponentially small in the separation between patterns; it equals transformer attention.
  Capacity for the continuous version is proven as c^((d-1)/4); the 2^(d/2) figure belongs to the earlier **binary** exponential model (Demircigil et al.)
  whose radius of attraction vanishes (corrected: the first version attributed 2^(d/2) to this paper's model); the classical network stores about 0.138 d.
  A "HopfieldLayer" filled with (input, target) pairs gives a similarity-weighted average of targets, i.e. kNN or learning vector
  quantisation. Transfers: three kinds of fixed point (one pattern, a mixture, the global mean) as a way to read confidence. Not matrix-free: softmax over real products.
- **Recurrent depth (Geiping et al.; sections 1-4 read).** Prelude, a looped core block, a coda. The state starts as random noise and the embedded input is injected at every
  step (the paper argues this keeps the iteration stable). Training samples the number of iterations (median 29) and **backpropagates only through the last k=8**.
  Ablations: adding noise at each step did not help; conditioning the core on the step index broke extrapolation. Zero-shot exit when the difference
  between successive outputs falls below 5e-4; saturation depends on the task (easy tasks around 8 iterations). One failed
  run learned to ignore the recurrence (same accuracy at 1 or 32 iterations): the same pathology as paper 4. Dense and backprop-trained.
- **Mamba (Gu, Dao; sections 1-3 read).** A linear recurrence with a diagonal state matrix whose step size and input/output maps depend on the input
  ("selection"); solves selective copying and induction heads that fixed recurrences cannot; reported 99.8 on selective copying and perfect induction-head extrapolation to
  sequences 4000 times longer than training. The scan is matrix-free in form, but the input maps are dense projections and training is backprop. Transfer: the idea that
  the current token decides keep/overwrite/ignore can be a table lookup.
- **Attention approximates SDM (Bricken, Pehlevan; section 1).** In binary SDM a pattern's pointer can address the next pattern, so a
  heteroassociative store is a sequence memory (the paper's alphabet example); reads average the neurons within a Hamming radius, and the circle
  intersection mimics the softmax. Binary SDM read/write is popcount plus add, so it is matrix-free; the claim about attention was read only in the introduction.
- **Global workspace (Goyal et al.; sections 1-2).** Specialists write to a small number of shared slots after a (top-k) competition and the content is
  broadcast back; the paper notes that human working memory has fewer than ten slots. Matrix-free analogue: top-k winners write to a few slots; the attention itself is dense.
- **Dense associative memory (Krotov, Hopfield; abstract and introduction only).** Higher-order interactions store more patterns than neurons; used here only for the prototype/feature-matching view.

## (c) Synthesis: what a matrix-free working memory needs

1. **State, three small parts.** (a) A window of the last k sparse codes (papers 2 and 4: already strong, and k recent items
   plus their ANDs is a universal approximator for the dynamics the NG-RC paper tests). (b) A hypothesis: a k-of-n candidate set with small evidence
   counters (HTM predicted cells, TRM's y). (c) A scratch value that records how much has been used or how far the
   context has been matched, such as infini-gram's matched order or a mask of seen bits (TRM's z, but deterministic here). Separate the hypothesis from the scratch (TRM: 87.4 against 71.9 with one state).
2. **Update rule.** Hash (state, input), read counters, add evidence with shifts, take the top-k, open a write only on surprise. HTM's burst, the delta rule's
   write-the-difference and our "write only when wrong" all agree. Allocate new, longer-context entries only on a miss (HTM segments, infini-gram's longer match).
3. **Readout.** Counting tables or clause weights keyed by state features; clauses over the window are the binary NG-RC (paper 2), and an HTM segment is a clause with an m-of-n threshold (paper 1).
4. **Checking.** Compare the hypothesis with the input through a generative completion: predict hidden bits from visible ones
   with clauses (paper 5, masked completion) or by dreams, and use the mismatch as the energy that decides hold or revise
   (Hopfield view). Halt when the state stops changing (recurrent depth) or when a count table says the answer is already reliable (TRM's halting head, learned here by counting).
5. **Fixing errors without backprop-through-time.** Four tools appear in the papers: local per-step errors with a causal predict-then-update order (paper 4); truncated
   credit (k=8 in recurrent depth); deep supervision with the state detached between cycles (TRM); a state built from the inputs by fixed
   rules, so that nothing needs credit (NG-RC, window). **Important caution from the full text:** where gradients train a learned scratch, a short credit
   window costs a lot (TRM: 56.5 against 87.4), and where nothing forces the state to be useful, models ignore it (paper 4's no-feedback control; recurrent depth's failed run).
   A matrix-free design with a fixed-rule state avoids the first problem but risks the second. A candidate local substitute (my idea, untested): give each state slot
   a small *usefulness counter* that is incremented when the slot's value agreed with the later correct output and decayed otherwise, and drop or re-hash slots with low counts. This
   is a local eligibility trace and needs no gradient.
6. **Always test against the control.** Every design must beat a window-only (no carried state) baseline and show that the carried state can be decoded; paper 4 is the one fully read matrix-free recurrent learner and it failed exactly this test.
7. **Honest uncertainty.** Evidence for clause-based recurrence on language or images is zero in what I could read; the proposals below are untested, and the costs are my estimates, not measurements.

## (d) Our own method sketch

Notation: the image code is the existing 4,608-bit sensory code; the class table is the 5-bit counter table; the dream memory is the 10-bit per-class count table.
No design adds a multiplier or a matrix. Success criteria include the no-regression rule from the project memory.

### Design B (first to try). Counting sequence core with matched-order state and a clause option

- **State.** The current matched order n_t (an integer, 0 to 8); for each of 4 orders (1, 2, 4, 8) a hash of the context and a seen-flag; the
  previous prediction and whether it was right. Update: n_t <= n_{t-1} + 1, then back off until the context has been seen (infini-gram's amortised rule), using the
  seen-flags.
- **Step.** Predict from the longest seen order with a unique or dominant continuation (the sparse-estimate rule); after the true next element, increment its counter at all orders, and
  only on a wrong prediction allocate a longer-order entry (HTM burst). Optional variant B2: replace the counters by a Tsetlin clause bank over a thermometer-coded window of the last 4-8 elements
  (a binary NG-RC), trained by ordinary clause feedback.
- **Minimal experiment.** (1) Next-element prediction on label sequences from a hidden finite-state machine whose output depends on an event 6-12 steps back (beyond a window of 4), with 3 machine seeds and 3 data seeds, as in paper 4; (2) the same on our character counting model's text (bits per character). Controls: window-only (orders 1-4), first-order, and, for B2, the counter version. Decoding probe: nearest-centroid recovery of the hidden state from (matched order, hashes), as in paper 4.
- **Success criterion.** At least 2 points above the window-only control on the long-dependency machine and no loss on short-dependency tasks; no worse than the current counting model on text. A tie with the window-only control is recorded as "recurrence not needed here".
- **Expected cost (ESTIMATED).** 4 orders x 2^20 slots x 4 bits = 2 MB (512 KB with 2^18 slots and some collisions). Per element: 4 hash lookups and increments; no multiplies. Table merge between chips by adding counts (infini-gram's additive indexes).

### Design A. Glimpse loop: hypothesis set, clause-based completion check, halting by counts

- **State.** y: up to 3 candidate classes with 4-bit evidence counters; z: a mask of which code bits have been revealed (96-bit folded, as in paper 4) and a step counter. Hypothesis and scratch are separate (paper 6).
- **Step.** (1) Reveal a quarter of the code (a region or the next unmasked patch). (2) Add the table's counters for the revealed bits not yet used to each candidate's evidence, with decay by a shift. (3) Check: a clause bank trained to **predict masked code bits from visible ones** (paper 5's masked autoencoder, one pool per class) fills in the hidden region for the top candidate; the Hamming mismatch with what is later revealed is the energy. (4) If the mismatch is high demote the candidate, else keep; halt when the top candidate is unchanged for two steps or when a count table indexed by margin says "reliable".
- **Training.** The table keeps its existing surprise-driven writes. The completion clauses use paper 5's feedback. Thresholds are two-bucket histograms (mismatch of correct versus wrong hypotheses), counted.
- **Minimal experiment.** Fashion-MNIST codes (digits as a second check). Hide a random 50% of the 5x5-window positions, or flip 10% and 20% of bits. Compare (a) single pass on the visible bits, (b) the loop with 4 steps, (c) the loop with the check disabled, (d) check by independent-bit dreams instead of clauses.
- **Success criterion.** (b) at least +3 points over (a) at 50% occlusion on 3 seeds with no loss on clean images against the shipped settings; (b) above (c) by at least 1 point; clauses (b) above dreams (d) otherwise the clause bank is not worth its memory. Failure is recorded.
- **Expected cost (ESTIMATED).** State about 20 bytes per stream. Per step: table reads for a quarter of 4,608 bits x 3 candidates (about 3.5k adds) plus clause evaluation for the check (cost not yet estimated: a pool of a few hundred clauses over a few thousand literals per class is the main memory risk). About 4-5x the one-pass cost for 4 steps. Risk: a quarter of the code may already carry almost all the information, leaving nothing for the loop to gain.

### Design C. Look-predict-verify: sequence core and recogniser joined by an expectation

- **State.** The last k recognised labels (hashed), Design B's pending prediction (top-2 next labels with confidence, matched order), Design A's hypothesis set.
- **Step.** The sequence core predicts the next label before the image arrives and adds a small integer prior to the recogniser's class evidence (HTM's apical expectation). If the top class disagrees with a confident prediction, run one more glimpse (Design A) before accepting. Write (recognised label, next label) into the sequence tables only on disagreement or low margin.
- **Minimal experiment.** A stream of Fashion-MNIST items whose classes follow a Markov rule (90% rule-following), images with 0, 10, 20% bit flips. Measure recognition with and without the prior, and next-label accuracy using recognised versus true labels.
- **Success criterion.** At 20% noise at least +3 points over no prior; equal at 0% noise; no worse than no prior when the stream is random (the prior must learn to be weak). Watch for errors poisoning the sequence table through confident wrong priors.
- **Expected cost (ESTIMATED).** 10 adds per image for the prior, the sequence core as in B, an extra glimpse for a fraction of images, a few tens of bytes of state.

### Ranking

Design B first: cheapest, clearest control, and works on our character model without new image work. Design A next: it is the real "hold, revise, check" demonstration, and the clause-based completion check is the new ingredient from the full-text reading. Design C last, since it needs both. Uncertain in all three: whether the carried state is *used* (the central failure in papers 4 and 11), whether clause completion is accurate enough to verify, and whether the usefulness-counter idea in section (c) works at all. None of this has been run.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
