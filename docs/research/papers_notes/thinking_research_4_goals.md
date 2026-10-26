---
title: Thinking research 4 - Goals and drives for an autonomous learner
tags: [spark, research, papers]
---

# Thinking research 4: how an autonomous learner gets its own drives, and how to keep them safe

Question: today every target in the chip (stream mix, number of stored images, when to stop, share-balance monitor) is
typed in by a person. Can a small matrix-free "motivation layer" choose what to learn or rehearse next from unlabeled
self-monitoring signals, with guard rails? Rules in force: no dense matrix products, no multipliers, no backprop in the
chip design; allowed: scans, event-driven sparse lookups, hash/table lookups, counters, small state, local rules,
clauses = AND of literals. The aim is to LEARN from published work, not copy it.

How the papers were read (honest statement). 19 papers were downloaded as PDFs from arXiv and converted to text
(`pdftotext`). I read the abstract, introduction, the method sections and the main results or discussion of each, and the
specific equations used below. I did NOT read every page: appendices, related-work sections, proofs, hyper-parameter
tables and most figure captions were skipped or only grepped. "Read" below therefore means "method and results read",
which is stated in the table. All numbers in this note are REPORTED by the authors; none were reproduced by us. Two
requested topics have no arXiv full text I could fetch (Keramati-Gutkin 2014 eLife original; Tsetlin-machine
reinforcement learning, only a paywalled journal paper and a thesis): this is stated where it matters.

## (a) Papers read

| # | Citation (arXiv id) | Year | Read fully? |
|---|---|---|---|
| 1 | Da Costa, Parr, Sajid, Veselic, Neacsu, Friston, "Active inference on discrete state-spaces: a synthesis" (2001.07203) | 2020 | Partly: sections 1-2, 7-8 (expected free energy, learning), appendix C (novelty term) read; structure learning, appendix A-B skimmed |
| 2 | Sajid, Ball, Parr, Friston, "Active inference: demystified and compared" (1909.10863) | 2020 | Partly: abstract, frozen-lake experiments and non-stationary results read; derivations skimmed |
| 3 | Schmidhuber, "Driven by compression progress" (0812.4360) | 2009 | Partly: abstract, sections 1-2 (interestingness = first derivative of compressibility) read; the art/music/jokes parts skipped |
| 4 | Pathak, Agrawal, Efros, Darrell, "Curiosity-driven exploration by self-supervised prediction" (1705.05363) | 2017 | Partly: method, VizDoom/Mario results and the noise-robustness test read |
| 5 | Burda, Edwards, Storkey, Klimov, "Exploration by random network distillation" (1810.12894) | 2018 | Partly: sections 1-3.2 read, appendices skipped |
| 6 | Forestier, Portelas, Mollard, Oudeyer, "Intrinsically motivated goal exploration processes with automatic curriculum learning" (1708.02190) | 2022 | Partly: abstract, the goal-space policy (4.2.3) and the learning-progress analysis read |
| 7 | Matiisen, Oliver, Cohen, Schulman, "Teacher-student curriculum learning" (1707.00183) | 2017 | Mostly: main text sections 1-4 read, appendix pseudo-code skipped |
| 8 | Mohamed, Rezende, "Variational information maximisation for intrinsically motivated RL" (1509.08731) | 2015 | Partly: abstract, introduction, planning experiments (lava maze, key-door) read; variational bound derivation skipped |
| 9 | Laurencon, Segerie, Lussange, Gutkin, "Continuous homeostatic reinforcement learning for self-regulated autonomous agents" (2109.06580) | 2021 | Partly: abstract, background on drive reduction and the drive function read (definitions of the Keramati-Gutkin reward are quoted from here); continuous-time maths skimmed |
| 10 | Dulberg, Dubey, Berwian, Cohen, "Modularity benefits RL agents with competing homeostatic drives" (2204.06608) | 2022 | Yes (short paper, whole text) |
| 11 | Gerstner, Lehmann, Liakoni, Corneil, Brea, "Eligibility traces and plasticity on behavioral time scales: neoHebbian three-factor rules" (1801.05219) | 2018 | Partly: abstract, section 2 (formal rule, eq. 1), surprise/novelty section, consolidation comment read; the four experiments skimmed |
| 12 | Miconi, Clune, Stanley, "Differentiable plasticity" (1804.02464) | 2018 | Partly: abstract and the plastic-synapse equation read (training uses backprop, which we cannot use) |
| 13 | Wheeldon, Yakovlev, Shafik, "Self-timed reinforcement learning using Tsetlin machine" (2109.00846) | 2021 | Partly: the three-stage feedback (type I/II, clause-level, automaton-level) and the random-bit generation read. It is a Tsetlin-machine learning datapath, not an RL algorithm; no arXiv Tsetlin-RL text was found |
| 14 | Salimans, Ho, Chen, Sidor, Sutskever, "Evolution strategies as a scalable alternative to RL" (1703.03864) | 2017 | Partly: abstract, algorithm and the tricks (mirrored sampling, rank shaping, weight decay) read |
| 15 | Schaul, Quan, Antonoglou, Silver, "Prioritized experience replay" (1511.05952) | 2016 | Partly: sections 1-3 (sampling rule, rank and proportional variants, sum-tree) and the tuned exponents read |
| 16 | Bazhenov, Dewasurendra, Krishnan, Delanois, "Unsupervised replay strategies for continual learning with limited data" (2410.16154) | 2024 | Partly: abstract, methods, and the sequential-task results read (sleep = unsupervised local Hebbian phase) |
| 17 | Hadfield-Menell, Dragan, Abbeel, Russell, "The off-switch game" (1611.08219) | 2017 | Partly: abstract, model, incentive result (sections 1-4) read; proofs skipped |
| 18 | Krakovna, Orseau, Kumar, Martic, Legg, "Penalizing side effects using stepwise relative reachability" (1806.01186) | 2019 | Partly: abstract, introduction, baseline/deviation decomposition read; gridworld table skimmed |
| 19 | Turner, Hadfield-Menell, Tadepalli, "Conservative agency via attainable utility preservation" (1902.09725) | 2020 | Partly: abstract, penalty definitions (eq. 1-3), design discussion, ablation list read |

Not covered with full text (no fetchable arXiv text or paywalled): Keramati and Gutkin eLife 2014 (reached only through
paper 9 and 10, which restate its drive function), the Tsetlin-machine RL journal paper, Orseau-Armstrong safe
interruptibility, mild optimisation / quantilizers, hypergradient learning-rate methods, neuromorphic sleep scheduling
hardware. These are gaps, not conclusions.

## (b) Per-paper notes

### 1. Active inference on discrete state-spaces (Da Costa et al. 2020)
Mechanism. The agent holds a small generative model over discrete states: a likelihood A (observation given state),
transitions B, preferences C over outcomes. Perception minimises variational free energy; action selection picks the
policy with the lowest expected free energy G. G splits into "risk" (KL between predicted and preferred outcomes) plus
"ambiguity" (expected entropy of observations), or equivalently extrinsic value (log-probability of preferred outcomes)
plus intrinsic value: salience (information gain about states) and novelty (information gain about the parameters of A).
Learning is just Dirichlet counting: a = a + sum of (outcome x state) co-occurrences, which the authors note is formally
identical to Hebbian plasticity (eq. 21). The novelty term has a closed form in the counts: W = 1/2 (1/a - 1/a0)
(appendix C), a pure function of how often each (state, outcome) pair has been counted.
Key numbers (reported): the paper is theory and a synthesis; no benchmark numbers.
Transfers. (i) Counts as beliefs: our tables already are Dirichlet-like counters. (ii) Novelty as a function of counts:
the bonus 1/a (or 1/a - 1/(a+k)) needs one table read and one small reciprocal lookup, no multiply on chip if kept in a
ROM. (iii) Preferences C as set-points: a homeostatic target expressed as a preferred distribution over a few observed
variables (class share, doubt rate), risk = distance of the predicted next value from the preferred one. (iv) The clean
split "pragmatic term + epistemic term" is a good template for the selection rule.
Does not transfer. Policy enumeration with matrix products A.s and log of matrices; the full softmax over policies with a
precision parameter; the continuous-state parts. Their matrices are small and sparse in the discrete case, but the
formulas as written are matrix-vector products, which our rule forbids; we only borrow the count-based terms.

### 2. Active inference: demystified and compared (Sajid et al. 2020)
Mechanism. Same discrete active-inference agent compared with Q-learning and a Bayesian model-based RL agent on a 3x3
frozen lake, 200 trials of 500 episodes. With no preferences the agent explores epistemically; with preferences it
exploits. When the reward location is swapped (episodes 21, 121, 141, 251, 451) the active-inference agent recovers
after a single episode because the model has a context factor, while Q-learning needs about 40 episodes and Bayesian
RL needs ever more episodes because pseudo-counts accumulate and must be unlearned.
Key numbers (reported): recovery after the swap in about 1 episode vs about 40 for Q-learning; learning of the
fixed task in fewer than 10 episodes.
Transfers. The lesson about counts: plain accumulating counts adapt slowly after a change, which matches our "known
limit" (domain shift). A drive layer should use forgetting counts (halve on fill, as our dream memory already does) or an
explicit context flag. The comparison also shows that a prior preference alone can be a null model when the preference
is flat: our set-points must not be flat.
Does not transfer. Belief propagation over hidden states; the cost of exact planning.

### 3. Driven by compression progress (Schmidhuber 2009)
Mechanism. A learner with a compressor/predictor of its history. The intrinsic reward at time t is not the prediction
error (which is high for noise) but the improvement of the compressor after learning from the data: the first derivative
of compressibility ("interestingness" is the steepness of the learning curve). Pure noise is boring because it never
becomes compressible; fully known data is boring because nothing improves. The controller is rewarded for steering
toward data on which the compressor will improve.
Key numbers (reported): none; this is a principle paper.
Transfers. This is the central idea for us: use a PROGRESS signal (change in a self-monitor), not the level of the error.
It solves the "noisy TV" trap that level-based surprise has. Our compressor is the counting table; "compression
progress on a class" can be measured without labels as the drop of the table's running surprise (best clause wrong) on a
held buffer of recent unlabeled codes, or as the drop in doubt rate.
Does not transfer. Kolmogorov-style compressors, and the general RL controller; we only keep the "derivative" idea.

### 4. Intrinsic curiosity module, ICM (Pathak et al. 2017)
Mechanism. Curiosity is the error of a forward model that predicts the next state's features. The features come from an
inverse-dynamics network trained to predict the action from (state, next state), so only features that the agent can
influence are kept and uncontrollable noise is ignored. Intrinsic reward is added to the policy's reward.
Key numbers (reported): in sparse-reward VizDoom the ICM agent reaches the goal 100% (median 100%) at convergence while a
baseline A3C gets 0% and TRPO 26%; with 40% of the pixels replaced by white noise, ICM still succeeds in most runs while
the pixel-prediction variant struggles; random-noise "curiosity" never reaches the goal (sanity check against degenerate
solutions).
Transfers. The principle "ignore what you cannot influence": our surprise measure can be restricted to bits/clauses that
have been predictive at least once (a learnt mask of "learnable" features). The random-noise control is a good audit
test for our layer.
Does not transfer. Convolutional feature learner trained by backprop; policy gradients.

### 5. Random network distillation, RND (Burda et al. 2018)
Mechanism. The bonus is the error of a trained predictor against a fixed, randomly initialised target network on the
current observation. The error is high for rarely seen inputs and falls as similar inputs are seen, with no dependence on
action stochasticity (the target is deterministic). Intrinsic and extrinsic returns have separate value heads so the
non-stationary bonus does not corrupt the stationary one; intrinsic rewards are divided by a running estimate of their
standard deviation; observations are whitened and clipped to [-5, 5].
Key numbers (reported): on Montezuma's Revenge, pure exploration finds more than half the rooms; best agent often finds
22 of 24 rooms of level 1; MNIST toy: predictor error on a class falls with the number of training examples of that class.
Transfers. A count-based version of RND is natural for us: a fixed random hash maps a code to a small table cell; the
"predictor" is the counter in that cell; novelty = 1/(count+1). This is exactly the classic count-based bonus the paper
cites (1/n and 1/sqrt(n) of Bellemare et al.). Normalising the bonus by a running scale, and clipping, are cheap guard
rails we can keep (shift-based running mean, saturating bonus).
Does not transfer. The two networks, PPO, whitening with floating-point statistics.

### 6. IMGEP with automatic curriculum (Forestier, Portelas, Mollard, Oudeyer 2022)
Mechanism. The agent generates its own goals (parameterised fitness functions), picks a goal space by learning progress,
tries to reach a goal there, and reuses every outcome for all other goals. The goal-space policy keeps a running average
of the intrinsic reward r = competence now minus competence on the most similar previous (goal, context), and samples a
space with probability proportional to that average, mixed with 20% uniform random choice (a non-stationary bandit). In
only 20% of iterations the agent runs without exploration noise and updates its progress estimates. Distractors
(static objects, random objects) end with zero or very low progress and are ignored by themselves.
Key numbers (reported): in 2D simulation, Minecraft and a real robot the learning-progress agents produce a curriculum
(hand, then sticks, then toys); random-goal-space controls are worse; distractors get interest strictly zero in the
Minecraft runs.
Transfers. This is a ready-made selection rule: one counter of progress per module, selection proportional to progress,
a fixed 20% uniform share (a guard rail against collapse), and a separate 20% "clean evaluation" share so progress is
measured without exploration noise. Maps directly to "which class or stage to rehearse".
Does not transfer. Population-based policy search with Gaussian mutations; continuous goal spaces.

### 7. Teacher-student curriculum learning (Matiisen et al. 2017)
Mechanism. A teacher chooses which subtask the student practises, using the slope of the student's learning curve on
each task as reward, i.e. learning progress. It samples tasks by the ABSOLUTE slope, so a task whose score falls
(forgetting) is practised again. Four estimators: Online (exponentially weighted average of score change with epsilon-
greedy or softmax choice), Naive (K trials then a regression slope), Window (FIFO of the last K scores, slope), and
Sampling (draw one recent reward from each task's buffer and take the largest; Thompson-like, no exploration constant).
Scores are held-out validation accuracy per task.
Key numbers (reported): on decimal addition it beat uniform sampling and the best hand-made curriculum of earlier work;
in a Minecraft maze it solved a task that direct training could not and learned about an order of magnitude faster than
uniform subtask sampling.
Transfers. Very close to our setting: tasks = classes or stages, student = counting table, score = accuracy on a
validation buffer. The slope can be computed without regression by two counters (score now minus score at last visit),
with an exponential moving average done by a shift. Absolute value of the slope = built-in forgetting protection.
The "Sampling" variant has no tunable exploration constant, attractive for a no-human-schedule goal.
Does not transfer. The scores come from labelled validation sets; in our case they must be replaced by unlabeled
proxies (see section d). LSTM students and the POMDP view.

### 8. Variational information maximisation for empowerment (Mohamed and Rezende 2015)
Mechanism. Empowerment is the channel capacity from an agent's actions to its future observations, a drive for staying
in states where the agent has many distinguishable controllable futures. They estimate it with a variational lower bound
and neural networks, and plan by one-step greedy choice of the action leading to the highest-empowerment state.
Key numbers (reported): qualitative; the agent builds a wall to stop lava, collects a key and goes to the door, avoids
a predator, all driven by empowerment alone.
Transfers. As a drive for a counting chip the useful reading is "keep options open": prefer to keep free capacity (free
table rows, unsaturated counters, memory headroom). A cheap count proxy for empowerment is the number of distinct
cells reachable, i.e. a count of non-saturated entries. Empowerment is also cited by the safety literature (paper 19) as a
penalty idea.
Does not transfer. Mutual-information estimation with neural networks; it also makes the system seek power, which is a
safety concern (see section on safety).

### 9. Continuous homeostatic RL (Laurencon et al. 2021; restating Keramati and Gutkin)
Mechanism. The agent has internal variables x with set-points x*. The drive is d(x) = (sum |x*_i - x_i|^n)^(1/m); the
reward for a transition is d(x_t) - d(x_t+1), so maximising discounted reward equals minimising discounted drive; the
paper shows this keeps the theoretical results of the discrete theory and extends it to continuous time and space.
Key numbers (reported): none central; the paper is a theoretical and simulation extension.
Transfers. The whole drive function is two lines for our chip: absolute differences (shift-add, no multiply when n=1),
reward = drop in total drive. Using n=1 (or small integer n with a lookup table for the power) keeps it matrix-free.
The reward is a difference, so it is bounded by the size of the variables, which gives bounded motivation for free.
Does not transfer. Continuous-time RL machinery.

### 10. Modularity with competing homeostatic drives (Dulberg et al. 2022)
Mechanism. N internal "stats" each with a set-point (here 5) and a constant decay (0.004 per step). A monolithic DQN
gets the summed HRRL reward; a modular agent has one Q-learner per stat with its own reward, and chooses the action by
summing the Q-values (greatest-mass Q-learning).
Key numbers (reported): in a four-resource grid world over 30,000 steps with 50 runs, the modular agent was
insensitive to the epsilon-annealing time (even one step of annealing performed as well as the best monolithic runs),
reached homeostasis faster, and when one stat was clamped at an unseen value (20) at step 15k, the other stats stayed
regulated, whereas the monolithic agent was disturbed without clear recovery.
Transfers. One small counter-module per drive, an additive vote at selection time: exploration appears as a side effect
("exploitation for one drive is exploration for another"), no extra epsilon. Robustness to a broken sensor: a stuck
monitor affects only its own module. Gives a design where each drive is auditable alone.
Does not transfer. Deep Q-networks; the claim of generality is from one toy grid world.

### 11. Eligibility traces and three-factor rules (Gerstner et al. 2018)
Mechanism. Local co-activity of pre- and post-synaptic units sets a decaying flag (eligibility trace) on the synapse:
de/dt = eta x_j g(y_i) - e/tau. The weight changes only when a third, global factor arrives (reward, punishment,
surprise, novelty; dopamine, noradrenaline, acetylcholine), while the flag is still set. Traces last about a second;
surprise or novelty can act as the third factor with no reward at all; the same scheme describes synaptic tagging and
consolidation.
Key numbers (reported): eligibility time constants of about 0.5 to 2 s in the cited experiments.
Transfers. This is the brain-correct form of our existing rule "write only when wrong or close": the local part is the
coincidence (class, bit) active, the third factor is a one-bit global broadcast (surprise), and a small decaying flag
lets a late signal reach recent cells. In the chip: a flag bit or 2-bit counter per recently touched row, decayed by
shift, committed when the global signal fires. The global signal comes from the motivation layer, so drives can raise or
lower plasticity without anyone writing a schedule.
Does not transfer. Spiking neuron biophysics; the review has no learning-rate numbers for our tables.

### 12. Differentiable plasticity (Miconi et al. 2018)
Mechanism. Each connection has a fixed weight plus plastic weight alpha_ij times a Hebbian trace, trace(t+1) = a*x_i*x_j +
(1-a)*trace; alpha and the decay are learned across lifetimes by gradient descent, so the network learns how to learn.
Key numbers (reported): networks with more than two million parameters memorise and reconstruct sets of novel natural
images where non-plastic recurrent nets fail; competitive on Omniglot; better than a non-plastic net on a maze task.
Transfers. The conceptual point: plasticity rate itself can be a per-synapse variable with its own meta-level
(per-row learning-rate state). We could keep a small per-row "plasticity" counter moved by a local rule (up on surprise,
down when stable) instead of gradient descent.
Does not transfer. The meta-training by backprop, which is exactly what the chip must not use, and the dense recurrent
matrices.

### 13. Self-timed Tsetlin machine learning hardware (Wheeldon et al. 2021)
Mechanism. Tsetlin automata (state counters) decide include/exclude for each literal; feedback is decomposed into three
stages: TM-level (choose type I or type II feedback from the label), clause-level (probabilistic gate from the clause
vote against a threshold), automaton-level (reward / penalty / inaction using random bits from a hardware generator).
Key numbers (reported): a trained example on a Boolean task reaches 96% after 50 epochs (81% after 4); the main claim is
energy and latency from asynchronous design.
Transfers. It shows that a global gate plus per-clause probabilistic gates are cheap in hardware and fully local,
matching our "global scalar broadcast plus local rule" shape. Random bits from an LFSR already exist in our dream
engine; the same generator can drive epsilon-style uniform shares.
Does not transfer. This is supervised Tsetlin learning; there is no reward-driven or goal-driven component. I did not
find an arXiv Tsetlin RL paper to read; the Tsetlin-RL claims stay UNVERIFIED in this note.

### 14. Evolution strategies (Salimans et al. 2017)
Mechanism. Black-box policy search: perturb the parameters with noise, evaluate returns, move the parameters toward
perturbations that scored higher. Tricks: antithetic (mirrored) pairs +eps and -eps; rank-transform the returns so
outliers cannot dominate; weight decay; only scalar returns need to be communicated; invariant to action frequency and
delayed reward.
Key numbers (reported): 3D humanoid walking in 10 minutes and competitive Atari after one hour of training, using over
a thousand workers.
Transfers. It is the gradient-free route for tuning the few motivation parameters themselves (set-points, shares):
random perturbations of a handful of integers, pairs of mirrored candidates, rank-based acceptance. Our hill-climbing
of controller constants offline on the PC could use exactly this, no backprop.
Does not transfer. Neural network policies; large populations.

### 15. Prioritized experience replay (Schaul et al. 2016)
Mechanism. Replay transitions with probability P(i) = p_i^alpha / sum p_k^alpha, where the priority p is the absolute
temporal-difference error plus a small epsilon (proportional) or 1/rank (rank-based). alpha = 0 is uniform. Bias from the
non-uniform sampling is corrected by importance weights annealed with beta. A sum-tree gives O(log N) sampling and update;
rank-based sampling uses equal-probability segments.
Key numbers (reported): outperformed uniform replay in DQN on 41 of 49 Atari games; best settings alpha=0.7, beta0=0.5
(rank) and alpha=0.6, beta0=0.4 (proportional).
Transfers. The surprise-weighted replay rule: replay items or classes in proportion to a power of their recent error,
with an epsilon so nothing starves; for us stratified sampling over classes (one pick per segment) is natural. The
priority is an unlabeled signal for us if "error" = doubt or best-row-wrong rate.
Does not transfer. Importance-sampling weights (a multiplication); TD errors.

### 16. Sleep replay for continual learning with limited data (Bazhenov et al. 2024)
Mechanism. After normal training, a "sleep" phase converts the network to a spiking one and drives it with noisy
Poisson input while a local Hebbian rule changes weights (increase when pre and post both fire, decrease when only
post fires). No labels, no stored data.
Key numbers (reported): significant accuracy gains in the low-data range (about 0.2 to 10% of MNIST/Fashion-MNIST) and a
rescue of earlier tasks after sequential training, with example accuracies of 0.60 (MNIST 3% subset) and 0.59 (Fashion-
MNIST 3% subset) after sleep; a slight decrease (10 to 15%) when more than about 10% of the data were used, which a short
extra training step mitigated.
Transfers. Direct support for our night phase and a warning for its scheduling: sleep helps when data are scarce or
unbalanced and can hurt when data are plentiful. So WHEN to sleep and how long is a quantity the drive layer should
control from an unlabeled signal (rising doubt on old classes, low-data regime), not a constant.
Does not transfer. ANN-to-SNN conversion and floating-point scaling factors.

### 17. The off-switch game (Hadfield-Menell et al. 2017)
Mechanism. A human may switch the robot off; the robot may act, switch itself off or wait for the human's decision. A
robot that is certain of its objective has no incentive to let the human switch it off. A robot that is uncertain about
the utility and treats the human's action as evidence has a non-negative (strictly positive when uncertain) incentive to
allow the switch; the incentive weakens if the human is noisy (the paper's example of the toddler in the car).
Key numbers (reported): theorems and plots of the incentive versus the robot's belief; no benchmark.
Transfers. Design rule for our layer: the chip must never gain from blocking an interruption. Make interruption a
cheap, external, unconditional hardware path that the motivation layer cannot see, and keep the layer's objective
uncertain/bounded: no internal variable's value can be improved by being stopped or by preventing a stop (a stop sets no
drive to a better value).
Does not transfer. Bayesian belief maths; real preference learning.

### 18. Stepwise relative reachability (Krakovna et al. 2019)
Mechanism. Splits a side-effect penalty into a baseline state and a deviation measure. Using the start state as baseline
gives bad incentives (the agent will offset or block changes by other agents); the stepwise inaction baseline (what would
have happened if the agent did nothing at this step) plus a relative-reachability deviation (penalise only the loss of
reachability of states relative to the baseline) avoids the tested bad incentives in gridworlds where simpler variants
fail.
Key numbers (reported): qualitative pass/fail on a set of gridworld tests; no scores to quote.
Transfers. The conceptual recipe is easily made count-based: compare "what the memory would look like if this step had
not happened" with what it looks like, and penalise irreversible loss (overwritten rows, saturated counters, deleted old
classes). A counter of "rows destroyed" per decision is cheap.
Does not transfer. Value-function based reachability over the whole state space.

### 19. Attainable utility preservation (Turner et al. 2020)
Mechanism. Reward = R(s,a) - lambda * Penalty(s,a) / Scale(s), where the penalty is the sum over auxiliary reward
functions of |Q_i(s,a) - Q_i(s, no-op)|: how much the action changes the ability to optimise a set of auxiliary goals.
Surprisingly, even randomly generated auxiliary rewards give conservative behaviour. Scale normalises by a mild action
or the total ability. Design choices (baseline: starting state vs inaction vs stepwise inaction; penalising decreases
only or both) are ablated; some fail the "correction" and "shutdown" tests.
Key numbers (reported): model-free AUP averaged over 50 trials on gridworlds; small lambda lets side effects appear,
larger lambda increases conservatism; some ablations fail the shutdown test.
Transfers. Keep the ability to do other things: the chip's motivation reward can be minus a penalty counted from a few
fixed random probes (for example the accuracy or margin of a handful of random hash-defined tasks or of old-class
reconstruction). If a rehearsal choice drops these probes, subtract. All counts, and only |difference|.
Does not transfer. Learned Q-functions for the auxiliary tasks.

## (c) Synthesis

Minimal ingredients of a drive system, as they appear across the papers:

1. Internal variables with set-points (homeostasis). Papers 9, 10, 1. A drive is a bounded distance d(x) = sum|x* - x|;
   reward is the drop in drive. Set-points are numbers in a preference table C, fixed by the designer once, not per
   run. In our chip: class-share error, doubt rate, surprise rate, memory fill, energy per decision, headroom.
2. A progress signal rather than a level. Papers 3, 6, 7, 4. Levels of error reward noise (noisy TV). Progress is the
   change in a self-monitor after learning; it is zero for noise, zero for solved items, and negative on forgetting.
   Count-based novelty (papers 1, 5) handles the "never seen" case; progress handles the "learnable now" case.
3. A selection rule. Papers 6, 7, 15, 10. Practice what has high absolute progress; keep a fixed uniform share; sample
   with probability proportional to a power of the priority (alpha < 1); optionally let each drive vote (sum) and let
   exploration come out of the disagreement.
4. A three-factor learning path. Paper 11 and 13. The selection rule does not edit weights; it emits a global scalar
   that gates local updates with a short eligibility flag. This keeps learning local and the motivation layer separable.
5. Guard rails. See next paragraph.

How published systems keep drives safe and bounded (and where they do not):
- Bounded signal: rewards are differences of bounded quantities (9), normalised by a running scale (5), clipped, and
  made rank-based (14, 15) so outliers cannot dominate.
- Forced uniform share against collapse: 20% uniform goal-space choice in 6; epsilon in 7; epsilon in priorities in 15.
- Separation of streams: separate value heads for intrinsic and extrinsic return in 5, so a non-stationary bonus does
  not corrupt the main objective; one module per drive in 10.
- Ignore the uncontrollable: inverse-model features in 4, zero progress for distractors in 6, deterministic target in 5.
- Impact limits: penalise loss of the ability to do other things (19) or loss of reachability relative to inaction (18).
  These are tested only in tiny gridworlds, with several designs failing on shutdown or offset tests.
- Interruptibility: the robot should stay uncertain and should treat a human stop as information (17). This is a
  one-shot theoretical argument; it does not give an implementation recipe and breaks when the human is noisy.
- Honest caveats: none of these papers proves safety for a learning system in the real world. The intrinsic-motivation
  papers (3, 4, 5, 6, 8) mostly evaluate exploration quality, not harm; the safety papers (17, 18, 19) evaluate toy
  games. The count-based, tabular setting is the easiest to audit and the only one where we can enumerate every state
  the layer can touch.

What the literature gives us that fits the chip: (1) the closed-form novelty bonus in counts (1), (2) the absolute-slope
teacher with a Thompson-like sampling variant (7), (3) the 80/20 explore/clean-evaluation split and the progress
bandit (6), (4) the distance-to-set-point drive and per-drive modules (9, 10), (5) the three-factor gate with a decaying
flag (11), (6) rank/power-law replay priorities with an epsilon floor (15), (7) a "keep the other abilities intact"
penalty from random probes (19), (8) the rule that interruption must never be a cost (17), (9) derivative-free tuning of
the layer's constants offline (14).

## (d) Our own method sketch

Context. Our staged-learning controller runs the L Cortex counting chip over stages of classes (Fashion-MNIST in
stages, EMNIST letters in stages), with a day (count, practise, daydream, interleaved dreams of old classes) and a night
(dreams of all known classes, stopping after 256 dreams with more than 2 surprises). Hand-set parts today: stream mix,
how many images to store, when a night starts and ends, how a monitor flags class-share imbalance. Baseline for every
experiment below: the shipped hand-set controller (margin 256, 1,500 dreams, 1 night), 3 seeds, same encoder and
tables. Success criterion: accuracy equal or better on the held-out test set (digits staged >= 95.5, clothing staged
>= 83.3 as in the no-regression rule) with fewer total update steps and no human-set schedule. All numbers below are
ESTIMATED costs or hypotheses; nothing has been run.

Common unlabeled signals (all already in the chip or one counter away):
- share_c: fraction of recent predictions assigned to class c, against a running share kept for known classes;
- doubt_c: how often the margin (best minus second-best score) is below the margin threshold when class c wins;
- surprise_c: how often the best row/clause for class c later turns out to be wrong. Wrongness is measured without
  labels by agreement: for a code that was just rehearsed, the row that fired for it is "wrong" if after the update the
  prediction for the same code changes class, or if the dream memory (generative side) and the fast table disagree;
- fill: fraction of saturated counters / used rows; energy: operations per decision.
Progress is a difference of one of these over two windows, held in a small integer.

### Design A. "Progress-ranked rehearsal" (teacher-student on counters; the safest first try)
Variables: for each known class c (at most 10 to 26 entries) one integer P_c, the moving difference of doubt_c (or
surprise_c) between the previous window and the current window (EMA by shift), and a 3-bit age counter. Set-point: none
beyond "doubt below target"; target is one constant for all classes.
Action chosen: which class to dream or replay next, and how long to stay in the night. Selection by the Sampling rule of
paper 7: draw a recent progress value from each class's last-K buffer (K = 4 of 4-bit numbers, from the LFSR) and
rehearse the class with the largest absolute draw; 20% of picks uniform (paper 6). The night ends when the sum of
absolute progress over all classes stays below a small constant for two consecutive windows, replacing "256 dreams and
more than 2 surprises".
Learning-progress signal from unlabeled data: doubt on a held ring buffer of the last M coded inputs (M = 256 codes, no
labels): progress for class c = doubt_c(old window) - doubt_c(new window), counted on the buffer entries the table
currently assigns to c. All counts and subtractions.
Bounding and audit: |P_c| clipped to 15; the uniform share is fixed in hardware; every choice writes (step, class,
P_c, rule branch) to a small log ring buffer; a read-only register shows total rehearsal share per class so an external
check can compare it to the uniform share.
Minimal experiment: staged Fashion-MNIST (5 stages of 2 classes) and staged EMNIST (letters in 4 stages). Variant A0 =
hand controller. A1 = same day, night driven by Design A. Count total dream steps and total counted updates. Prediction
(hypothesis): equal accuracy within 0.5 point with 20 to 40% fewer night steps, since quiet classes stop being rehearsed.
Failure to expect: unlabeled doubt may be uncorrelated with the real error on confusable classes (shirt vs t-shirt),
so progress could be misattributed; then keep the old stop rule as a floor.
Cost: about 30 counters of 8 bits plus a 4-deep buffer per class, one reciprocal-free comparison per dream; PC
simulation edit of a few dozen lines in the staged driver; each run costs the same as today's staged run (minutes on
the PC). ESTIMATED.

### Design B. "Homeostat with three drives and a gate" (set-points and a three-factor gate)
Variables (all small integers): D1 share-balance error = sum over classes of |share_c - target_share|, with target =
1/known_classes (the only set-point; not typed per experiment); D2 doubt rate; D3 memory fill relative to a budget. Each
drive is a module (paper 10): a module votes for an action by its sign; the three votes are added.
Actions: (i) learn rate gate: raise or lower the "write when wrong or close" margin (the existing 256) in steps;
(ii) start a night; (iii) stop learning new images for this stage (store count). Instead of a typed number of stored
images, the store gate closes when D2 stops falling (progress ~ 0) and opens when D1 rises after a stage change.
Third factor: a 1-bit global "surprise" broadcast equal to doubt above target; the existing local rule (class, bit
counters) fires only if the flag is set within a 4-step eligibility window (paper 11).
Progress signal: reward for each module = drop in its own drive over the last window; no labels.
Bounds and audit: each drive value is clipped; the margin can move only within [128, 512] and one step per window;
a watchdog counter forces the hand-set controller after N windows without a drop in total drive; the vote sheet (three
signed numbers and the chosen action) is logged per decision.
Minimal experiment: same staged tasks, plus a third test where one stage is a domain shift (rotated or inverted clothing
images) to see whether the homeostat raises plasticity on its own (hypothesis: recovery in fewer steps than the fixed
margin, which Sajid et al., paper 2, suggest is the weak point of accumulating counts). Compare accuracy, total steps,
number of nights, and the maximum fill.
Cost: three counters, three comparators, a 4-step flag register, a 3-entry log; no memory growth. Simulation edit
similar to A. ESTIMATED: under a day of PC work to implement and 3 seeds in minutes.

### Design C. "Count-novelty plus progress, with an impact probe" (curiosity with explicit harm limit)
Variables: for each coded input a hashed cell (the RND idea of paper 5 in counting form): a cell counter n_cell;
novelty = lookup table of 1/(n+1) in 4 bits; a global "novelty tide" N = EMA of novelty over recent inputs; the progress
signal from Design A; and a "probe set" of 16 fixed anchor codes (memorised on the first day, never updated; paper 19's
auxiliary tasks as random probes) whose current margin is tracked.
Actions: choose which incoming examples to store or count (selective writing), which classes to rehearse (progress
ranked), and when to stop a day. An incoming example is stored with probability proportional to novelty^alpha (alpha =
0.6 like paper 15, via lookup), so the stored-image count is not typed.
Safety term: reward = progress - lambda * (loss in probe margin versus the no-op baseline, defined as the probe margin
before the step; penalty only on decreases), as in the simplified relative-reachability and AUP ideas (18, 19). If the
probe margin drops more than a fixed amount, the step is rolled back by simply not committing the staged counter writes
(a one-step shadow write).
Audit: log of novelty, progress, probe loss per window; a hard cap on counter changes per window.
Minimal experiment: staged Fashion-MNIST with deliberately noisy inputs (random-pixel images added to 20% of the
stream, the noisy-TV test of papers 4 and 5; they must get zero reward after a few repetitions) and with a class-
imbalanced stream. Compare: hand controller, Design C without probe, Design C with probe. Metrics: accuracy, images
stored, steps, accuracy of old classes (forgetting), number of rollbacks.
Cost: a hashed table of 4k to 16k cells x 4 bits; 16 anchor codes; one extra comparison per update. Probably the
largest of the three because of the shadow write: ESTIMATED 10 to 20% more simulation time. Most speculative: novelty
could raise storage of rare corrupted images, so the noise test is the key audit.

Recommendation. Start with Design A (single mechanism, closest to a published, tested algorithm), then add B's gate and
C's novelty and probe one at a time, because the project rule says a change counts only if it passes the no-regression
triple. Offline, tune the handful of constants of the layer by evolution strategies (paper 14: mirrored pairs and rank
acceptance) on the PC; the chip runs only fixed integers.

### Honest note on safety
Giving a chip its own drives creates the possible problems the safety papers describe, in miniature:
- Specification gaming: a drive that rewards "less doubt" can be satisfied by making the memory forget hard cases so
  nothing is doubtful. Progress on one monitor must be paired with a held-out probe (Design C) and with the final
  accuracy checked by a person.
- Self-reinforcing selection: if the layer rehearses what it already does well, it narrows the memory. The fixed
  uniform share and the clipped drives limit this but do not remove it.
- Stopping and tampering: the stop path must be outside the layer. The layer must have no write access to its own
  set-points, share target or log, and no variable that improves by being stopped or by avoiding a stop (paper 17).
  These set-points should live in a read-only table loaded by the host.
- Auditability: because everything is a small integer counter and a decision log, every choice can be replayed; this is
  the main advantage of staying count-based and tabular.
- Limits of the evidence: all cited safety results are theory or toy gridworlds. We have no evidence that these guard
  rails hold in a real deployment, and our own tests will be on public image data on a PC simulator, so they show only
  that the mechanism works there. A drive layer is a controller of rehearsal, not a goal-seeking agent, and should stay
  that: it chooses among a short list of existing actions (which class to dream, when to sleep, how plastic to be), it
  cannot add actions, acquire resources or change its own rules.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
