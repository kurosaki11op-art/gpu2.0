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

Version note. First version of this note (26 Oct 2026) read most papers only partly. This is the revised version after
the founder's full-text requirement: nine papers were then read through page by page (main text, algorithms and
appendices that carry method; reference lists skipped), and the findings that changed are marked "REVISED" below.

How the papers were read (honest statement). PDFs were downloaded from arXiv (and, for Keramati and Gutkin 2011 and the
Tsetlin contextual-bandit paper, from the NeurIPS proceedings site, which the proxy allowed), converted to text with
`pdftotext`, and read in page-range chunks. "Fully" means: every page of the main text, algorithms and method
appendices read, reference list and pure-proof appendices skipped. "Partly" means: abstract, introduction, method and
main results read, the rest skipped or grepped. All numbers are REPORTED by the authors; none were reproduced by us.

## (a) Papers read

| # | Citation (id) | Year | Read fully? |
|---|---|---|---|
| 1 | Da Costa, Parr, Sajid, Veselic, Neacsu, Friston, "Active inference on discrete state-spaces: a synthesis" (arXiv 2001.07203) | 2020 | Yes (all main text and appendices A-C; references skipped) |
| 2 | Matiisen, Oliver, Cohen, Schulman, "Teacher-student curriculum learning" (arXiv 1707.00183) | 2017 | Yes (all pages incl. algorithm and training-detail appendices) |
| 3 | Forestier, Portelas, Mollard, Oudeyer, "Intrinsically motivated goal exploration processes with automatic curriculum learning" (arXiv 1708.02190) | 2022 | Yes (sections 1-6, results and figures captions; references skipped) |
| 4 | Dulberg, Dubey, Berwian, Cohen, "Modularity benefits RL agents with competing homeostatic drives" (arXiv 2204.06608) | 2022 | Yes (whole paper) |
| 5 | Gerstner, Lehmann, Liakoni, Corneil, Brea, "Eligibility traces and plasticity on behavioral time scales: neoHebbian three-factor rules" (arXiv 1801.05219) | 2018 | Yes (sections 1-4.5; references skipped) |
| 6 | Hadfield-Menell, Dragan, Abbeel, Russell, "The off-switch game" (arXiv 1611.08219) | 2017 | Yes (all main text; proofs only as sketched in the paper) |
| 7 | Turner, Hadfield-Menell, Tadepalli, "Conservative agency via attainable utility preservation" (arXiv 1902.09725) | 2020 | Yes (all main text and appendix A) |
| 8 | Keramati, Gutkin, "A reinforcement learning theory for homeostatic regulation" (NeurIPS 2011 conference version; no arXiv) | 2011 | Yes (all 9 pages; supplementary proofs are not in the PDF) |
| 9 | Everitt, Hutter, "Avoiding wireheading with value reinforcement learning" (arXiv 1605.03143) | 2016 | Mostly yes: sections 1-9 in full; appendices A-C (consistency construction, proofs) skipped |
| 10 | Sajid, Ball, Parr, Friston, "Active inference: demystified and compared" (arXiv 1909.10863) | 2020 | Mostly: introduction, expected free energy, frozen-lake results, preference learning, discussion start read; middle matrix derivations (about 400 lines) skipped |
| 11 | Bazhenov, Dewasurendra, Krishnan, Delanois, "Unsupervised replay strategies for continual learning with limited data" (arXiv 2410.16154) | 2024 | Mostly: abstract, methods, results sections A-D read; discussion and references skipped |
| 12 | Seraj, Sharma, Granmo, "Tsetlin machine for solving contextual bandit problems" (NeurIPS 2022; proceedings PDF) | 2022 | Mostly: sections 1-6 read in full; interpretability, conclusion and appendices skipped |
| 13 | Schmidhuber, "Driven by compression progress" (arXiv 0812.4360) | 2009 | Partly (abstract, sections 1-2) |
| 14 | Pathak, Agrawal, Efros, Darrell, "Curiosity-driven exploration by self-supervised prediction" (arXiv 1705.05363) | 2017 | Partly (method, VizDoom/Mario, noise test) |
| 15 | Burda, Edwards, Storkey, Klimov, "Exploration by random network distillation" (arXiv 1810.12894) | 2018 | Partly (sections 1-3.2) |
| 16 | Mohamed, Rezende, "Variational information maximisation for intrinsically motivated RL" (arXiv 1509.08731) | 2015 | Partly (abstract, introduction, planning experiments) |
| 17 | Laurencon, Segerie, Lussange, Gutkin, "Continuous homeostatic RL for self-regulated autonomous agents" (arXiv 2109.06580) | 2021 | Partly (abstract, background, drive definitions) |
| 18 | Miconi, Clune, Stanley, "Differentiable plasticity" (arXiv 1804.02464) | 2018 | Partly (abstract, plastic-synapse equation) |
| 19 | Wheeldon, Yakovlev, Shafik, "Self-timed reinforcement learning using Tsetlin machine" (arXiv 2109.00846) | 2021 | Partly (feedback stages only; it is a TM learning datapath, not RL) |
| 20 | Granmo, "The Tsetlin machine - a game theoretic bandit driven approach to optimal pattern recognition" (arXiv 1804.01508) | 2018-21 | Partly (abstract, sections 1.1-1.4 on the automaton as a bandit and the vanishing signal-to-noise problem) |
| 21 | Salimans, Ho, Chen, Sidor, Sutskever, "Evolution strategies as a scalable alternative to RL" (arXiv 1703.03864) | 2017 | Partly (abstract, algorithm, tricks) |
| 22 | Schaul, Quan, Antonoglou, Silver, "Prioritized experience replay" (arXiv 1511.05952) | 2016 | Partly (sections 1-3, tuned exponents) |
| 23 | Krakovna, Orseau, Kumar, Martic, Legg, "Penalizing side effects using stepwise relative reachability" (arXiv 1806.01186) | 2019 | Partly (abstract, introduction, baseline/deviation split) |

Tried and NOT reachable (said plainly): Keramati and Gutkin eLife 2014 full version (PubMed Central and eLife fetches
failed: no connection through the proxy; the 2011 NeurIPS version above was reached instead); Orseau and Armstrong,
"Safely interruptible agents" (not on arXiv; the PMLR PDF failed; known here only through its description in paper 6
and a search summary); Taylor, "Quantilizers" (not on arXiv; the MIRI PDF failed; known only from search summaries, so
nothing below depends on it); the Tsetlin-machine reinforcement-learning journal paper (Springer, failed) and the Agder
thesis (failed). Papers 20 and 12 are the closest Tsetlin material I could read. Nothing in this note cites those
unreachable papers for facts.

## (b) Per-paper notes

### 1. Active inference on discrete state-spaces (Da Costa et al. 2020), read fully
Mechanism. The agent keeps a small generative model: likelihood A (outcome given state), transitions B, and preferences C
over outcomes. Perception minimises variational free energy; planning picks policies by a softmax over negative
expected free energy G. G is unpacked as risk (KL between predicted and preferred outcomes) plus ambiguity (expected
observation entropy), or as extrinsic value (log-probability of preferred outcomes) plus intrinsic value: salience (information gain
about states) and novelty (information gain about the parameters of A). Learning is Dirichlet counting, a = a + sum of
outcome-state co-occurrences (eq. 21), which the authors call formally identical to Hebbian plasticity. The novelty term
has a closed form in the counts, W = 1/2 (1/a - 1/a0) (eq. 58, derived in appendix C via a digamma approximation).
Key numbers (reported): none; the paper is a theory and synthesis paper with no benchmarks.
REVISED, new from the full read:
- Preferences are innate and frozen. Section 9: agents are "born" with fundamental preferences (body temperature, glucose
  ranges) whose priors have infinitely precise hyperpriors, so experience cannot update them. Design rule for us: set-points
  live in a table the layer cannot write.
- Counting makes the agent overconfident ("becomes increasingly confident ... as long as the environment remains
  constant"), and the cure is Bayesian model reduction, a sleep-like step that simplifies priors over counts at the end
  of a trial. This is a direct analogue of our count halving and night.
- Policy search is kept cheap by an "Occam window": stop evaluating a policy as soon as its expected free energy is much
  worse than the best one found so far. Costs nothing in a loop over a short list of candidate actions.
- The softmax precision gamma is read as dopamine-like confidence; high gamma turns the average into winner-take-all.
Transfers. Counts as beliefs (our tables already are Dirichlet-like); novelty as a function of counts, 1/(2a) - 1/(2a0)
(one ROM lookup of a reciprocal, no multiplier); preferences C as read-only set-points on a few observed variables;
risk as distance of a predicted monitor value from its set-point; the pragmatic plus epistemic split as the template
for the selection rule; Occam-window pruning; model reduction as a trigger for the night.
Does not transfer. Matrix products A.s and log of matrices, softmax over policies (needs exp; replace with threshold
plus LFSR-based winner-take-all), continuous or hierarchical models, policy trees.

### 2. Teacher-student curriculum learning (Matiisen et al. 2017), read fully
Mechanism. A teacher picks which subtask the student trains on, rewarded by the change of the student's score on that
subtask (learning progress). Tasks are sampled by the ABSOLUTE value of the expected progress, so a task whose score
falls (forgetting) is revisited. Four estimators: Online (moving average Q <- alpha*r + (1-alpha)*Q with epsilon-greedy
or Boltzmann choice), Naive (K trials, regression slope), Window (FIFO of the last K scores with timesteps, regression
slope) and Sampling (keep the last K rewards of each task, draw one at random from each buffer, pick the task with the
largest absolute draw; in the batch version mix in a uniform share epsilon). Scores are accuracies on a separate
validation set that contains a uniform mix of all tasks.
Key numbers (reported): settings alpha 0.1, epsilon 0.1, K 10, Boltzmann temperature 0.0004; metric = steps until 99%
validation accuracy on decimal addition. The automatic curricula outperformed uniform sampling and the best published
hand curriculum for 9-digit one-dimensional addition; in the two-dimensional version "the manual curriculum is hard to
beat and uniform sampling is competitive"; in the 5-step Minecraft maze the Window teacher matched a carefully tuned
manual curriculum, while training on the last task only made no progress at all and uniform mixing was slow.
REVISED, new from the full read: (i) "there is no universal best algorithm"; (ii) "uniform sampling is surprisingly
efficient, especially in 2D", so every experiment of ours must include a uniform-sampling baseline, not only the hand
controller; (iii) taking the absolute value of the progress boosted almost all variants, confirming that forgetting
protection matters; (iv) the score is measured on a held-out labelled validation set, and the teacher needs several
repetitions of a task to see a slope (Window works because it re-uses a buffer); (v) in Minecraft only the Window
variant was run because the others need a score change per step, a warning that progress estimates can be hard to get
when scoring is expensive.
Transfers. Tasks = classes or stages, student = the counting table, score = a proxy accuracy; the slope by two counters
(score now minus score at last visit) with a shift-based moving average; the Sampling variant with a fixed uniform mix
and no tuned exploration constant; |slope| for forgetting protection.
Does not transfer. Labelled validation sets (we must replace them by an unlabeled proxy and prove the proxy tracks the
real accuracy), LSTM and PPO students, linear regression (use differences instead).

### 3. IMGEP with automatic curriculum learning (Forestier et al. 2022), read fully
Mechanism. The agent invents goals (parameterised fitness functions), samples a goal SPACE by a progress bandit, then a
goal inside it, tries it, and reuses every outcome for all other goals (computed in hindsight, no new action needed). The
goal-space policy keeps a running average of intrinsic reward r = fitness of this outcome minus fitness of the outcome
for the most similar earlier (goal, context); it picks a space with probability proportional to that average in 80% of
iterations and uniformly in 20%. In 80% of iterations the agent explores with noise and does NOT update progress; in
20% it runs without noise and updates progress (a clean measurement). Two learners run side by side: a fast,
incremental memory-based explorer and a slower batch learner trained on the same database (the authors compare this to
complementary learning systems).
Key numbers (reported): in the 2D tool-use environment (100 seeds) median exploration of the tool space 62% for the
progress-driven agent against 37% for random choice of goal space (Random Model Babbling), 13% for a single flat goal
space; magnet toy 3.3% against 0.5%. A hand-designed curriculum (20k iterations per object in the right order) gave a
median slightly better than the autonomous agent on the same measure, and in Minecraft the hand curriculum had higher
medians on every space; in the robot setup the autonomous agent beat the hand curriculum on right joystick and sound.
With distractors (2 random movers, 8 static objects) the progress-driven agent did not lose exploration while random
choice did; without distractors random choice was as good. Distractor interest stayed at or near zero.
REVISED, new from the full read: the honest summary is "learning-progress choice approximately equals a carefully
hand-designed curriculum and beats random choice only when there are distractors or the hard goals must be reached in
order". For us: the success criterion "equal to the hand controller with no human schedule" is exactly what the paper
itself achieves; do not promise to beat it. Also: modular goals (one space per object) were much better than one flat
goal space (60% against 10%), which supports one counter-module per class or per drive.
Transfers. Progress bandit with a fixed uniform share; a separate clean-evaluation share where progress is measured
without exploration noise; hindsight reuse (a rehearsed code also updates the progress of every class whose rows it
touched); the nearest-previous comparison can be a count: compare the outcome with the stored outcome of the same
hashed cell.
Does not transfer. Continuous goal spaces, Gaussian mutation, kd-tree nearest neighbour, Poppy robot.

### 4. Modularity with competing homeostatic drives (Dulberg et al. 2022), read fully
Mechanism. N internal "stats" (here 4), each with a set-point (5) and constant decay (0.004 per step). The reward is the
drop of a drive function D = (sum |h* - h|^n)^(1/m) with (n, m) = (4, 2). A monolithic deep Q-network gets the summed reward;
a modular agent (greatest-mass Q-learning) has one Q-learner per stat with its own reward and adds Q-values over modules
to choose the action.
Key numbers (reported): 30,000 steps in a single episode, 10 to 50 models per condition, equal total parameters (1.09e6)
and the same discount (0.5) found best for the monolithic net. The modular agent performed as well with one annealing step
as the best monolithic agent after careful tuning (no hand-set exploration schedule); it reached homeostasis sooner; and
when stat 4 was clamped to an unseen value (20) at step 15,000, the other three stayed regulated while the monolithic
agent was disturbed without clear recovery.
REVISED, new from the full read: one toy grid world; the authors predict, not demonstrate, larger gains in complex
worlds; summing Q-values is a simple arbitrator and they flag better arbitration as open.
Transfers. One small module per drive, additive vote at selection time; exploration appears as a by-product of
disagreement; a stuck or corrupted monitor harms only its own module. Auditable: each module's vote can be logged.
Does not transfer. Deep Q-networks, annealed epsilon.

### 5. Eligibility traces and three-factor rules (Gerstner et al. 2018), read fully
Mechanism. A synaptic flag e_ij is set by local coincidence, de/dt = eta x_j g(y_i) - e_ij / tau_e (eq. 1); the weight
changes only when a global third factor arrives: dw/dt = e_ij * M(t) (eq. 2). M has no neuron index, is defined as the
deviation from a running average (so it can be positive or negative: it changes both speed and direction of learning),
and can carry reward, punishment, surprise or novelty; the same maths covers TD(lambda) and policy-gradient rules.
Reviewed experiments (striatum, cortex, hippocampus): the third factor works if it arrives while the flag is set, with
windows of about 1 s (striatal dopamine; no effect at 4 s), 5 s for noradrenaline-gated LTP and 2.5 s for serotonin-gated
LTD (separate flags for LTP and LTD), seconds to a minute in hippocampus.
Key numbers (reported): the flag time constant should match the delay from action to reinforcement: much shorter links
nothing, much longer "reinforces the wrong attempts nearly as strongly as the right one"; consolidation tags last about an
hour and need a further factor to become permanent.
REVISED, new from the full read: (i) specificity comes from the flags (only coincident synapses are eligible) not from
the broadcast, and a fourth, attention-like gate can restrict eligibility further; (ii) novelty or surprise can serve as
the third factor with no reward at all; (iii) the paper says explicitly that precise predictions for surprise-modulated
plasticity "are not yet available", so any surprise-gated rule of ours is our own construction; (iv) a computational study
cited in the review found ACh during exploration enabled fast relearning after a reward move (with 2 s traces).
Transfers. The existing "write only when wrong or close" rule is the local coincidence part; the motivation layer supplies
the signed global factor as (monitor now) - (running mean of monitor), with a flag of a few steps per touched row; two
flags (raise, lower) per row are the LTP/LTD analogue; a second, slower tag for the night (consolidation).
Does not transfer. Spiking biophysics; real time constants in seconds (ours are counts of decisions).

### 6. The off-switch game (Hadfield-Menell et al. 2017), read fully
Mechanism. A robot R may act (a), ask the human H first (w(a)), or switch itself off; H may press the off switch. R
maximises H's utility U_a but is uncertain about it. If H is rational R never gains from disabling the switch; the
incentive to let H decide is delta = sigma^2 E[dpi/dU] - |mu| Pr(correction) (Theorem 2), nonnegative for a rational human,
strictly positive when R is uncertain, and it falls to zero as R's uncertainty sigma goes to zero. If H is noisy
(Boltzmann with rationality parameter beta) the incentive can turn negative: an overconfident robot facing a very noisy
human prefers to act or to switch itself off.
Key numbers (reported): theorems and plots only. New in section 5: the uncertainty is not free: value generated falls when
R is made more uncertain than the true posterior, and falls faster when R has more action options (|A| = 1, 4, 8).
REVISED, new from the full read: Remark 2: "an agent that is overconfident in its utility evaluations will be difficult to
correct; an agent that is under-confident will be ineffective". The earlier note called the stop path a pure hardware
matter; the paper's lesson is subtler: the incentive to accept a stop comes from the agent treating the stop as evidence,
and it has a price. The model is one-shot with one human as the only information source, which the authors list as a limit.
Transfers (as design rules, not as maths). (a) A stop must never be a cost to any drive: it is an external one-bit event that
sets plasticity to a safe value and is logged, never counted as a drive error. (b) Keep the number of actions the layer can
choose among small, which also keeps the price of oversight low. (c) Treat a human override as a signal that lowers the
layer's confidence (increase its uniform share), not as an error to be avoided.
Does not transfer. Bayesian belief maths; there is no human model in a counter.

### 7. Attainable utility preservation (Turner et al. 2020), read fully
Mechanism. R_AUP(s,a) = R(s,a) - lambda * Penalty(s,a) / Scale(s), with Penalty = sum over auxiliary reward functions i of
|Q_i(s,a) - Q_i(s, no-op)| (absolute change in the ability to optimise each auxiliary goal) and Scale = the same sum for
the no-op or a mild action. Q-learning on this converges (theorem 1). Design choices ablated: baseline (starting state,
inaction, stepwise inaction) and deviation (decreases only versus absolute change).
Key numbers (reported): five gridworld tests (Options, Damage, Correction, Offset, Interference), 50 trials, defaults gamma
0.996, lambda 0.67, 30 randomly sampled auxiliary reward functions; "merely five sufficed" to get side-effect-free behaviour.
Ablation table: full AUP passes all five; relative reachability 3 of 5; model-free AUP 4 of 5 (fails Correction);
starting-state AUP 3 of 5; inaction AUP 4 of 5; decrease-only AUP 4 of 5.
REVISED, new from the full read: (i) model-free AUP fails the shutdown (Correction) test because the effect of
disabling the switch is delayed; it needs a 9-step model rollout; (ii) a decrease-only penalty fails the same test
because avoiding shutdown does not decrease the auxiliary values, so the deviation must be absolute; (iii) if lambda > 1
the agent never finishes the task (reward 1 - lambda); small lambda lets side effects reappear; (iv) the authors
speculate, not show, that the idea scales to partially observable settings.
Transfers. The probe idea: a handful of fixed anchor tasks (random hash-defined tasks or stored anchor codes whose margins
are tracked) form the "auxiliary set"; the penalty is the absolute change of probe margins caused by a step relative to the same step with no
update (stepwise baseline). Because the test must see delayed effects, check the probes again after the next night, not
only after the step.
Does not transfer. Learned auxiliary Q-functions, discounted planning.

### 8. A reinforcement learning theory for homeostatic regulation (Keramati and Gutkin 2011), read fully
Mechanism. Internal state H with set-point H*; drive d(H) = (sum |h*_i - h_i|^n)^(1/m); reward of an outcome = d(H) - d(H +
K) (drive reduction); proposition 1: maximising discounted reward equals minimising discounted drive. For m > n > 1 (the
text writes m > n > 2) the reward (i) rises with outcome dose, (ii) rises with the deprivation of the relevant drive,
(iii) is inhibited by deprivation of an irrelevant drive (competition between drives), (iv) is concave in dose (risk
aversion). A discount below 1 is what produces anticipatory action (optimal anticipatory shivering = half the expected
drop); with discount 1 reactive and anticipatory strategies tie. Habitual (cached) values are rescaled by d(H1)/d(H0) after a
motivational shift, exact only when the new state is a proportional rescaling of the old.
Key numbers (reported): none; analytical plus qualitative behavioural predictions.
REVISED, new from the full read: the competition and risk-aversion properties DEPEND on the drive being non-linear
(n > 1). My earlier suggestion "use n = 1 so it is matrix-free" would remove drive competition and make each drive
independent; the fix is a small power ROM (lookup of |x|^n for integer |x| up to 32 or so, no multiplier), and an
integer root replaced by a monotone ROM or by the max-norm. The authors also warn that the formula is for ingestible
physiological variables and "should not be extended" to novelty-induced reward: novelty is a separate term in our layer.
Transfers. Drive = lookup-table power of deviations; reward = drop in drive between windows; one set-point per variable;
discounting by a short horizon (a few windows) to enable anticipatory acts such as starting a night before doubt rises.
Does not transfer. The d(H1)/d(H0) rescaling of cached values (a division and a multiplication).

### 9. Avoiding wireheading with value reinforcement learning (Everitt and Hutter 2016), read (main text)
Mechanism. A reward-maximising agent is incentivised to corrupt its reward sensor ("wireheading"): in the model the
observed reward r = d_s(inner reward) where d_s is a self-delusion function the agent might set. In value reinforcement
learning the agent uses r as evidence about an unknown utility function and only allows "consistency preserving" actions
for which its belief about the observed reward equals the belief induced by its utility prior; then its value reduces to
the expected utility of states, not of evidence (theorem 14). A toy with 20 states and 10 utility functions: the RL agent
always chose the delusional state with reward 3, the consistency-preserving agent mostly stayed non-delusional.
Key numbers (reported): the toy result above only. The authors state it is one-shot, tentative, and that a robust way of
specifying the consistent prior is an open question.
Transfers. For our layer wireheading looks like making a monitor look good by changing the measuring instrument: raising
the margin threshold lowers the doubt count; storing only easy cases; shrinking the validation buffer. Count-based
analogue of consistency preservation: keep several independent monitors (doubt rate, probe margin, dream-versus-table
agreement) and refuse any action that improves one monitor while another moves the other way; keep the monitor code and
thresholds read-only.
Does not transfer. The Bayesian machinery over utility functions.

### 10. Active inference demystified and compared (Sajid et al. 2020), read mostly
Mechanism. The same discrete active-inference agent compared with Q-learning and Bayesian model-based RL on a 3x3 frozen
lake (200 trials of 500 episodes), including reward removed, reward moved, and preferences learned.
Key numbers (reported): average score deterministic / stochastic environment: Q-learning (epsilon 0.1) 97.79 / 66.08;
Q-learning decaying epsilon 80.44 / 65.13; Bayesian RL 99.76 / 64.39; active inference 99.88 / 98.90; active inference
with flat preferences 50.03 / 50.22. After the goal and hole are swapped, Q-learning needs about 40 episodes to recover;
Bayesian RL recovers slowly because accumulated pseudo-counts must be unlearned; active inference recovers after one episode
since the model carries a context factor. With no reward at all, belief-based agents keep exploring in a directed way
(average 40 to 45) while the Q-learner locks into a circular policy.
REVISED, new from the full read (important for safety): when the agent LEARNS its preferences from its own behaviour
(Dirichlet counts over preferred outcomes), it can drift into odd preferences: because holes are absorbing the agent
observes itself falling in holes, learns to prefer them and "hides in holes"; another run learned to prefer the Frisbee.
The authors treat this as coherent self-evidencing ("I am the sort of creature that enjoys holes") and note it may be
"counter-intuitive from the reinforcement learning perspective". For a chip this is a failure mode, not a feature.
Transfers. (a) Never let the layer learn its set-points from its own history; set-points stay read-only (also paper 1).
(b) Accumulating counts adapt slowly after a change: use halving counts or an explicit context flag. (c) Flat set-points
make the layer a pure explorer: the set-points must be non-flat.
Does not transfer. Belief propagation, exact planning over hidden states.

### 11. Sleep replay for continual learning with limited data (Bazhenov et al. 2024), read mostly
Mechanism. After supervised training, the network is turned into a spiking one and driven by random spike trains whose
rate equals each input's mean intensity over earlier training; local rules adjust weights (up when pre and post both fire,
down when post fires and pre does not); the output layer is untouched; sleep activity decays across the sleep and gives
sparser hidden representations. Hyper-parameters (scales, thresholds, increment 7.49e-4, decrement -1.87e-4, decay 0.97)
were found by a genetic algorithm on the validation set.
Key numbers (reported): MNIST 3% subset 0.32 -> 0.60 and Fashion-MNIST 3% subset 0.38 -> 0.59 accuracy; in two-task
sequential learning mean accuracy rose 15 to 30% (MNIST) and 5 to 15% (Fashion-MNIST) and the first task was rescued
unless the second task had much more data than the first; with more than about 10% of the data sleep lowered accuracy by 10
to 15%, mitigated by one fine-tuning epoch.
REVISED, new from the full read: sleep parameters are tuned on a labelled validation set, so "when to sleep and how much"
is not self-governing there; this is the gap a drive layer should fill from unlabeled signals.
Transfers. Direct support for the night; the data-regime dependence (helps when data are scarce or unbalanced, hurts when
plentiful) is a reason to gate the night by a monitor; the input noise statistics = mean input intensity, which our dream
memory (per-bit on-counts) already is.
Does not transfer. ANN-to-SNN conversion, floating-point scales, a genetic search on labels.

### 12. Tsetlin machine for contextual bandits (Seraj, Sharma, Granmo 2022), read mostly
Mechanism. One Tsetlin machine per arm; clauses are ANDs of literals; each literal has a Tsetlin automaton (bounded integer
state, include above the midpoint). Feedback type I (reinforce frequent patterns) and type II (make clauses discriminative)
are given with probability set by the vote sum against a margin T. Clauses carry integer weights moved by +1 / -1 (a
searching-on-the-line automaton), which can switch a clause off at weight 0 without multiplications. Arm choice by
epsilon-greedy over the per-arm TM vote, or Thompson sampling by fitting a TM to a bootstrap sample of each arm's history.
Key numbers (reported): on nine datasets (Iris, Breast Cancer, Adult, Covertype, Statlog, MNIST, Noisy XOR, MovieLens,
Simulated Article), 10 independent runs each, the Thompson-sampling TM beat the other base learners on eight of nine (not
Linear UCB on Covertype) and the TM learned faster; robust to the number of bits per feature.
REVISED: rewards are label-correctness, i.e. supervised data turned into bandits, and the Thompson variant refits a TM per
step on a bootstrap sample: not usable on chip. The epsilon-greedy variant and the integer clause weights are usable.
Transfers. The bandit loop over a bit-only learner shows that a counting/Tsetlin learner can sit under an epsilon-greedy
selector with no floating point; integer weight +1/-1 is a fine progress counter.
Does not transfer. Bootstrap Thompson sampling; label reward.

### 13-23. Partly read papers (unchanged from the first version, still partial)
13 Schmidhuber 2009: interestingness = first derivative of compressibility (progress, not level of error); transfers as
the progress signal; no numbers. 14 ICM (Pathak 2017): forward-model error in an inverse-dynamics feature space ignores
the uncontrollable; sparse-reward VizDoom 100% success against 0% for A3C and 26% for TRPO; random-noise curiosity never
reaches the goal (a sanity test for our layer); backprop features do not transfer. 15 RND (Burda 2018): bonus = error of a
trained net against a fixed random net; the classic count bonuses 1/n and 1/sqrt(n) are named; a hashed counter is our
matrix-free version; bonus normalised by a running scale and clipped. 16 Empowerment (Mohamed and Rezende 2015): drive
toward states with many controllable futures; as "keep options open" it maps to headroom counters; it is also a
power-seeking drive, so we do not adopt it as a goal. 17 Laurencon 2021: the same drive function in continuous time.
18 Differentiable plasticity (Miconi 2018): plasticity rate is itself a per-synapse variable; its meta-training uses backprop
and cannot be used. 19 Wheeldon 2021: three-stage feedback gating and LFSR randomness in Tsetlin hardware (a datapath,
not RL). 20 Granmo 2018: a single Tsetlin automaton is a bandit solver with one integer of memory; many independent
automata driven by one noisy feedback suffer vanishing signal-to-noise (variance grows with the team size), which the TM
solves with a game of clause resource allocation. Lesson: a single global scalar must not drive many independent
counters directly; gate it by local flags (paper 5) and a margin T. 21 Evolution strategies (Salimans 2017): mirrored
perturbations, rank-transformed returns, weight decay; usable offline to tune the layer's few integers. 22 Prioritised
replay (Schaul 2016): P(i) = p_i^alpha / sum p^alpha with p = |error| + epsilon or 1/rank; 41 of 49 Atari games better than
uniform; best alpha 0.7 (rank) and 0.6 (proportional); importance weights are multiplications and are dropped.
23 Stepwise relative reachability (Krakovna 2019): the baseline-and-deviation split behind paper 7.

## (c) Synthesis

Minimal ingredients of a drive system, as they appear across the papers:

1. Internal variables with read-only set-points (homeostasis). Papers 8, 4, 1, 10. A drive is a non-linear distance d(x)
   of the monitors from their set-points; reward is its drop. Non-linearity matters (paper 8): it creates competition
   between drives. Set-points are fixed by the designer once and must not be learnable from the agent's own history
   (papers 1 and 10: innate frozen preferences; learned ones drifted to "hole-seeking").
2. A progress signal rather than a level. Papers 13, 3, 2, 14. Levels of error reward noise; progress (change after
   learning) is zero for noise and for solved items, and negative on forgetting. Count-based novelty (papers 1, 15) covers
   the "never seen" case; progress covers "learnable now". Both TSCL and IMGEP measure progress on clean, held-out
   data; IMGEP measures it only in the 20% of steps run without exploration noise.
3. A selection rule. Papers 2, 3, 22, 4. Practise what has high absolute progress; keep a fixed uniform share (10% in
   TSCL, 20% in IMGEP); or sample by a power of the priority with an epsilon floor (22); or let each drive vote and sum the
   votes (4). Strong honest caveat from papers 2 and 3: uniform choice and a hand-made curriculum are hard to beat, so the
   target is parity without a human schedule.
4. A three-factor update path. Papers 5, 12, 20. The selector does not edit weights; it emits a signed global scalar
   (deviation from a running mean) that gates local updates of rows with a fresh flag. This also avoids the
   vanishing signal-to-noise problem of many counters driven by one noisy scalar (paper 20).
5. Guard rails. See the next paragraph.

How published systems keep drives safe and bounded (and where they do not):
- Bounded signal: rewards are differences of bounded quantities (8), normalised by running scale and clipped (15), rank-based
  (21, 22).
- Forced uniform share against collapse (2, 3, 22).
- Separate streams (15: separate value heads) and one module per drive (4).
- Ignore the uncontrollable: inverse-model features (14), zero progress for distractors (3), deterministic target (15).
- Impact limits: absolute change of the ability to do other things, with a no-op baseline (7, 23). In the ablation only
  the full design (stepwise baseline, absolute deviation, model rollout) passed all five tests; simpler versions failed
  the shutdown or offset tests.
- Frozen preferences (1) and the observation that learned preferences can drift into self-defeating ones (10).
- Measurement integrity: wireheading is the agent changing the evidence instead of the world (9); the proposed fix is a
  consistency condition between the agent's beliefs about the evidence and about the quantity it stands for.
- Interruptibility: an agent that is certain about its objective has no reason to accept a stop; uncertainty creates the
  incentive but costs value (6). This is a theoretical result for one-shot games; it gives no implementation recipe.
- Honest caveat: every safety result read is theory or tiny gridworlds, and the intrinsic-motivation papers evaluate
  exploration quality, not harm. The tabular, count-based setting is the only one where every state the layer can touch
  can be enumerated, which is its main safety advantage.

What fits the chip: closed-form count novelty (1); absolute-slope teacher with a Sampling-style rule (2); a progress
bandit with a clean-evaluation share (3); a power-table drive with per-drive modules (4, 8); signed three-factor gate with
a short flag (5); rank/power replay priorities with an epsilon floor (22); a probe-based absolute-change penalty with a
no-op baseline (7); an external stop that is never a cost (6); consistency across independent monitors (9);
derivative-free tuning of the layer's integers offline (21); read-only set-points (1, 10).

## (d) Our own method sketch

Context. Our staged-learning controller runs the L Cortex counting chip over stages of classes (Fashion-MNIST in
stages, EMNIST letters in stages), with a day (count, practise, daydream, interleaved dreams of old classes) and a night
(dreams of all known classes, stopping after 256 dreams with more than 2 surprises). Hand-set parts today: stream mix,
how many images to store, when a night starts and ends, how a monitor flags class-share imbalance. Baselines for every
experiment below: (B1) the shipped hand-set controller (margin 256, 1,500 dreams, 1 night), and (B2) a uniform-
rehearsal controller (every known class equally often, fixed budget), because papers 2 and 3 show uniform choice is
strong. 3 seeds. Success: accuracy equal to or better than B1 (and not below B2) with fewer total update steps and
no human-set schedule, passing the no-regression triple (digits staged >= 95.5, clothing staged >= 83.3, words (20)
clean >= 73.3). All numbers below are ESTIMATED costs or hypotheses; nothing has been run.

Common unlabeled signals (all already in the chip or one counter away):
- share_c: fraction of recent predictions assigned to class c against its running share;
- doubt_c: how often the margin (best minus second-best score) is below the threshold when class c wins;
- surprise_c: how often the best row/clause for class c is later contradicted, measured without labels by agreement
  (the row that fired for a rehearsed code no longer wins after the update, or the dream memory and the fast table
  disagree);
- fill: fraction of saturated counters / used rows; energy: operations per decision.
Progress is a difference of one of these over two windows, held in a small signed integer.
Offline check that the controller never sees: a labelled accuracy per class, logged only to test whether each unlabeled
proxy tracks the true accuracy (TSCL used a labelled validation set; replacing it by a proxy is the main risk).

### Design A. "Progress-ranked rehearsal" (teacher-student on counters; safest first try)
Variables: for each known class c (at most 10 to 26) a signed integer P_c, the moving difference of doubt_c between two
windows of a held ring buffer of M = 256 recent codes (EMA by shift), and a 4-deep FIFO of the last progress values.
Set-point: one constant doubt target for all classes (read-only).
Action chosen: which class to dream or replay next, and when the night ends. Rule = the Sampling algorithm of paper 2:
draw one value from each class's FIFO (index from the LFSR), pick the class with the largest absolute draw, with a
fixed 10% uniform share (paper 2: epsilon 0.1) and every fifth decision a "clean" step where no dream noise is added
and progress is measured (paper 3). An empty FIFO draws the maximum value (as in paper 2 algorithm 4: r = 1 if empty), so unseen classes are tried
first. The night ends when the sum of absolute progress stays under a small constant for two consecutive windows,
replacing "256 dreams with more than 2 surprises".
Bounded and auditable: |P_c| clipped to 15; the uniform share lives in hardware, not in the layer's state; a ring log
records (step, class, P_c, branch); a read-only register shows per-class rehearsal share.
Minimal experiment: staged Fashion-MNIST (5 stages of 2 classes) and staged EMNIST (4 stages). Arms: B1, B2, A. Compare
final accuracy (staged), total dream steps and counted updates, forgetting of old classes. Hypothesis: A equals B1 within
0.5 point with 20 to 40% fewer night steps. Likely failure: doubt may not track accuracy on confusable classes (shirt,
T-shirt, EMNIST I/l), then A behaves like uniform; the offline accuracy log shows this.
Cost: about 30 eight-bit counters plus a 4-entry FIFO per class, a ring buffer of 256 codes (re-used from existing
stores), one comparison per dream; a few dozen lines in the PC simulator driver; each run costs the same as today's
staged run (minutes). ESTIMATED.

### Design B. "Homeostat with three drives and a signed gate" (set-points, modules, three-factor path)
Variables (small integers): D1 = share-balance deviation sum |share_c - 1/K| (K known classes); D2 = doubt rate; D3 =
memory fill against a budget. Each drive is a module with drive value from a power ROM (|x|^2, no multiplier) so that
drives compete (paper 8), and votes for an action by the sign of its recent drop (paper 4). Set-points are a read-only table loaded by the
host; there is no code path that writes them (papers 1 and 10).
Actions: (i) raise or lower the margin of "write when wrong or close" within [128, 512], one step per window;
(ii) start a night when D2 has risen two windows in a row, or the votes sum above a threshold (anticipatory, using a
short horizon as in paper 8); (iii) close or open the store gate for new images (replaces the typed image count): close
when D2 stops falling.
Three-factor path: M = (monitor now) - (running mean of monitor), 1 bit sign plus 2 bits magnitude, broadcast; each
touched row holds a flag counter of 4 steps (paper 5) and two flags per row for raise and lower; a row is committed only if its flag is
alive when M arrives. A host command "stop" forces M = 0 and the safe margin, is not visible to the drives (paper 6).
Minimal experiment: the same staged tasks plus a domain-shift stage (inverted or rotated clothing) where B1's fixed margin
is known to lag; arms B1, B2, B. Metrics: accuracy, steps, number of nights, max fill, recovery steps after the shift.
Hypothesis: B recovers faster than B1 after the shift (paper 10 argues counts adapt slowly; halving and a plasticity gate address it) and equals B1 elsewhere.
Cost: three counters, three small ROMs, comparators, two flag counters per row (the row store is the existing table; 4
bits per row may not fit in the 46 BSRAM build, so the first test is on the PC simulator and the memory cost is
reported separately). ESTIMATED.

### Design C. "Count novelty plus progress, with a probe penalty and a consistency check" (curiosity with a harm limit)
Variables: a hashed novelty table (a fixed hash of the code to 4k to 16k cells of 4-bit counts; novelty = ROM(1/(n+1)));
the Design A progress signal; 16 anchor probe codes memorised on day one and never updated; two independent monitors
(doubt rate and probe margin) plus a third, dream-versus-table agreement.
Actions: store or skip an incoming example with probability proportional to novelty^0.6 (power by ROM; alpha as in paper 22),
which replaces the typed image count; pick the class to rehearse by progress (Design A).
Safety terms: reward = progress - lambda * sum over probes |probe margin after - probe margin with no update| (absolute change, no-op baseline, paper 7); no update is committed if
the probe change exceeds a cap (the update is staged in a shadow counter set and simply not applied); the probes are
checked again after every night because the paper-7 ablation shows one-step checks miss delayed effects; an action is refused if
one monitor improves while another worsens (paper 9's consistency idea in counts).
Minimal experiment: staged Fashion-MNIST with 20% pure-noise images added (the noisy-TV test of papers 14 and 15; the
noise must receive near-zero reward after a few repeats) and with an imbalanced stream. Arms: B1, B2, C without
probes, C with probes. Metrics: accuracy, images stored, steps, forgetting of old classes, number of refused or rolled
back updates, share of storage spent on noise.
Cost: a hashed table of 4 to 16 kilo cells x 4 bits, 16 anchor codes, a shadow counter set (about the size of one stage's changed rows),
about 10 to 20% more simulation time. ESTIMATED. Most speculative of the three; the noise test is the key audit.

Recommendation. Build Design A first (one mechanism, closest to two published and tested algorithms), then add B's gate and
C's novelty and probes one at a time, because the project rule says a change counts only if it passes the no-regression
triple. Tune the handful of integers of the layer offline with evolution strategies (paper 21: mirrored pairs, rank
acceptance) on the PC; the chip runs fixed integers.

### Honest note on safety
Giving a chip its own drives creates, in miniature, the problems the safety papers describe:
- Specification gaming and wireheading (paper 9): a drive for "less doubt" can be satisfied by forgetting hard cases or by
  changing the margin threshold. Defence: monitors and thresholds read-only, several independent monitors that must agree,
  a probe set (paper 7), and a person checking final accuracy.
- Drifting preferences (paper 10): a layer that learns its set-points from its own behaviour can settle in a
  self-defeating niche. Defence: set-points are not learnable.
- Self-reinforcing selection: rehearsing what it already does well narrows the memory. The fixed uniform share and clipped
  progress limit this, they do not remove it (paper 3 itself finds random choice equal when there are no distractors).
- Stopping (paper 6): the stop path is outside the layer, is never a drive cost, and the layer has no write access to its
  set-points, log or stop. Overconfidence makes correction harder, and making the layer under-confident makes it
  ineffective: the uniform share is the tuning knob, and its price is measurable (steps).
- Auditability: all state is small integers and a decision log, so every choice can be replayed. This is the main advantage of
  staying tabular and count-based.
- Limits of the evidence: the safety results read are theory or toy gridworlds; our tests are public image data in a PC
  simulator; they can show that the mechanism works there, not that it is safe in deployment. The layer is a controller of
  rehearsal (which class to dream, when to sleep, how plastic to be) over a short fixed list of actions; it must not gain
  actions, resources, or write access to its own rules.

Related: [Project memory](../../PROJECT_MEMORY.md), [Papers notes index](INDEX.md), [Lessons from failures](../../lessons_from_failures_25oct.md)
