---
title: Paper notes - local learning rules and forgetting
tags: [l, research, papers]
---

# Paper notes - local learning rules and forgetting

Four papers read in full from the extracted PDF text (pdftotext -layout; main text, algorithm boxes, hyperparameter
tables, results tables, appendices). Question behind them: can an L-style network (integer, gate-based, no matrices
in the chip, no backprop across layers) learn with local rules, how far behind end-to-end error passing do local rules
fall, and do they forget less?

Context from our own tests (MEASURED, earlier work in this repo): each layer fixing only its own error with a local
readout was 8 to 15 points worse than end-to-end error passing on a gate network; integer error passing with sign-step
counters matched float backprop. Numbers below are copied from the papers (labelled "paper-reported", i.e. MEASURED by
the authors, not by us). Nothing here was re-run by us.

Papers and ids (all verified by downloading arxiv.org/pdf/<id> and reading the title page):

| # | Paper | arXiv id | Version read |
|---|---|---|---|
| 1 | Hinton, The Forward-Forward Algorithm: Some Preliminary Investigations | 2212.13345 | v1 (27 Dec 2022) |
| 2 | Terres-Escudero, Del Ser, Garcia-Bringas, A Contrastive Symmetric Forward-Forward Algorithm (SFFA) for Continual Learning Tasks (CoLLAs 2024) | 2409.07387 | v2 (9 Jan 2025) |
| 3 | Lassig, Aceituno, Sorbaro, Grewe, Bio-Inspired, Task-Free Continual Learning through Activity Regularization | 2212.04316 | v1 (8 Dec 2022) |
| 4 | Belilovsky, Eickenberg, Oyallon, Greedy Layerwise Learning Can Scale to ImageNet (ICML 2019) | 1812.11446 | v3 (23 Apr 2019) |

Choice of paper 2: a search for Forward-Forward in continual / class-incremental learning returned several
forward-only papers; SFFA is the one that applies the Forward-Forward family to class-, domain- and task-incremental
learning with a full table (the others, e.g. F-OAL 2403.15751 and FoRo 2509.01533, are analytic or gradient-free but not
Forward-Forward, and were NOT read: UNVERIFIED).

---

## 1. Hinton, The Forward-Forward Algorithm (arXiv 2212.13345)

### (a) Mechanism exactly

Two forward passes replace forward plus backward. Each layer has its own objective: high "goodness" on positive
(real) data, low goodness on negative data. No error signal crosses layers.

- Goodness of a layer: sum of squared ReLU activities. Probability that an input is positive:
  p(positive) = sigmoid( sum_j y_j^2 - theta ), with y_j the activity before normalisation and theta a threshold
  (Eq. 1). Training pushes the goodness above theta for positive data and below theta for negative data (logistic loss
  on the layer's own goodness). Other goodness functions are listed as future work: minus the sum of squares (works
  slightly better on CIFAR, Table 1), and the sum of unsquared activities (footnote 22; then the layer normalisation
  must normalise the sum, not the sum of squares).
- What is passed between layers: only the orientation of the activity vector. The vector is divided by its length
  (layer normalisation without mean subtraction) so the next layer cannot read the previous goodness and must use the
  relative activities. The length is used for the layer's own decision, the direction goes up.
- Negative data, by experiment:
  - Unsupervised (Section 3.2): hybrid images, one digit times a mask of large blobs plus another digit times the
    inverse mask. Masks are made from random bits blurred repeatedly with [1/4, 1/2, 1/4] in both directions and
    thresholded at 0.5. Short-range statistics stay right, long-range shape statistics are wrong.
  - Supervised (Section 3.3): the label is written into the first 10 pixels (one-of-N). Positive = image with correct
    label, negative = same image with a wrong label. A forward pass with a neutral label (ten entries of 0.1) picks hard
    negative labels (wrong labels chosen in proportion to predicted probability); this cut the epochs to about a third.
  - Recurrent video version (Section 3.4): static image treated as video, 8 synchronous iterations, damping 0.3 old +
    0.7 new pre-normalised state; negatives chosen among incorrect classes in proportion to their predicted probability.
  - Section 5 (sleep): separating positive and negative phases in time (many positive updates then many negative) only
    worked with very low learning rate and very high momentum. An early draft claimed otherwise; the author now suspects
    a bug. This is flagged as the most important open question for FF as a biological model.
- Inference: either one forward pass with the neutral label and a softmax on the normalised activities of all but the
  first hidden layer (fast, worse), or run once per candidate label and add up the goodness of all layers except the
  first, pick the highest (better, costs one pass per class).
- Section 7 (learning fast and slow): with full connectivity, a weight update that changes a layer's goodness for input x
  does not change that layer's layer-normalised output for x. Update for neuron j:
  Delta w_j = 2 * eps * d log p / d (sum_j y_j^2) * y_j * x (Eq. 3). So all layers can be updated simultaneously and one
  step can reach a target goodness S* with learning rate eps = sqrt(S*/S_L) - 1 (Eq. 4), when the input and normalised
  hidden vectors have length 1. Not exploited in the experiments (mini-batches are still used). Also: FF still learns if
  an unknown black box sits between layers.
- Peer normalisation (footnote 9, local-receptive-field net): a regulariser pulls each unit's running mean activity
  toward the mean over all units of the layer, and dead ReLUs receive a pretend derivative so their weights grow.

### (b) Accuracy against backprop (paper-reported, no seeds or error bars given)

MNIST (50,000 train, 10,000 validation for hyperparameters, official 10,000 test):
- Backprop reference, permutation-invariant, ReLU nets: about 1.4% test error, about 20 epochs; about 1.1% with dropout
  or label smoothing. Sensible CNNs: about 0.6%.
- FF unsupervised (hybrid-image negatives), 4 hidden layers x 2000 ReLU, 100 epochs, softmax on the last three layers
  (using layer 1 made it worse): 1.37% test error. With local receptive fields without weight sharing (hidden layers:
  4x4 grid stride 6, 10x10 field, 128 channels; 3x3 grid 220 channels; 2x2 grid 512 channels; about 2000 units per
  layer), 60 epochs, peer normalisation: 1.16%.
- FF supervised (label in the input), 4 x 2000 ReLU, 60 epochs: 1.36%. Doubling the learning rate and training 40 epochs
  gave 1.46%. With jitter augmentation (up to 2 pixels each way, 25 shifts), 500 epochs: 0.64%, stated as similar to a
  CNN trained with backprop (but no longer permutation-invariant).
- FF recurrent (Section 3.4), 60 epochs, 8 iterations, goodness averaged over iterations 3 to 5: 1.31%.
- Footnote 7: papers on bio-plausible alternatives with MNIST error above 2% either do not work as well as backprop or
  were not tuned properly.

CIFAR-10 (Table 1, non-convolutional nets with local receptive fields 11x11, 3072 ReLUs per hidden layer arranged as a
32x32 map with 3 units per location, weight decay for both; hidden units in the last layer get 10 top-down inputs, others
up to 363). Training % error / test % error:

| Procedure | Test procedure | Layers | Train err | Test err |
|---|---|---|---|---|
| BP | - | 2 | 0 | 37 |
| FF min ssq | goodness for every label | 2 | 20 | 41 |
| FF min ssq | one-pass softmax | 2 | 31 | 45 |
| FF max ssq | goodness for every label | 2 | 25 | 44 |
| FF max ssq | one-pass softmax | 2 | 33 | 46 |
| BP | - | 3 | 2 | 39 |
| FF min ssq | goodness for every label | 3 | 24 | 41 |
| FF min ssq | one-pass softmax | 3 | 32 | 44 |
| FF max ssq | goodness for every label | 3 | 21 | 44 |
| FF max ssq | one-pass softmax | 3 | 31 | 46 |

Gap to backprop on CIFAR-10: best FF (minimise ssq, per-label goodness) is 4 points worse with 2 layers (41 vs 37) and 2
points worse with 3 layers (41 vs 39); one-pass readout is 5 to 8 points worse. The text says the gap does not grow with
more layers, and that backprop reduces training error much faster. FF train error stays at 20 to 33%, so it underfits
here while BP overfits (0 to 2%).

### (c) Forgetting

Nothing. The paper has no continual-learning experiment. UNVERIFIED claims about forgetting must come from papers 2 and 3.
One indirect statement: the "sleep deprivation" remark and Section 7 (fast single-example updates) are speculation, not
measurements.

### (d) Operations and memory

Weight matrices and dense dot products throughout (ReLU units, squared activities, layer normalisation needs a square
root and a division; the learning-rate formula needs a square root). Two forward passes per example (positive and
negative), and one extra pass per class at test time in the best readout. Memory: no stored activities for a backward
pass; the paper stresses pipelining video without storing activities. Section 8 argues analog hardware (voltages times
conductances) is the target; digital cost is not analysed. Footnote 14: the local-receptive-field connectivity was
simulated with a full weight matrix and a mask, which is inefficient.

### (e) Limitations (stated by the author)

Somewhat slower than backprop and generalises slightly worse on the toy problems; does not scale beyond a few million
connections here (a later paper is promised); the negative-data source for unsupervised learning is hand-made; the
positive and negative phases cannot be separated in time with the sum-of-squares goodness; greedy layer learning means
later layers cannot change earlier ones (the recurrent top-down version is the proposed fix); CIFAR-10 networks underfit.
Single-run numbers, hyperparameters tuned on a validation split.

### (f) Fit to L

Integer version: plausible for the counting part, awkward for the squared sum. A gate-network goodness would not be a sum
of squares: use the count of firing gates in a layer, G = number of active output gates (equivalent in spirit to the
unsquared-activity goodness of footnote 22 with binary activities), with threshold theta an integer. Local rule per layer:
on positive data, if G < theta then raise the firing of the gates that are almost firing (increase counters of the
winning gates); on negative data, if G > theta, lower the counters of the gates that fire. This is a perceptron-style
integer step (sign step), no multiply. Layer normalisation becomes a fixed-count k-winners-take-all (always pass exactly k
active gates up), which removes goodness from what the next layer sees, exactly the job the normalisation does in FF.
Label as one-hot bits in the input (class embedded in the first bits), negative = wrong label bits, as in Section 3.3.
Inference needs one pass per class (or one neutral pass to shortlist). Our own 8 to 15 point gap for per-layer readout
warns that greedy layers lose accuracy; FF's own CIFAR gap of 2 to 4 points (paper-reported) is smaller, but it uses
real-valued layers of 3072 units.

One concrete small test: on the existing gate network and the dataset used for the 8 to 15 point gap, replace the
per-layer readout loss by the FF count goodness with a wrong-label negative and k-WTA pass-up, train layer by layer with
sign-step counters, read out by summed goodness per label, and report the gap to our integer end-to-end result.

---

## 2. SFFA: Symmetric Forward-Forward for continual learning (arXiv 2409.07387, v2)

### (a) Mechanism exactly

Starts from FF. Problem identified: with p = sigmoid(G - theta) and G >= 0, p(negative) never reaches 1 (for theta = 2 the
maximum negative probability is about 0.88), so the loss is asymmetric between positive and negative samples.

SFFA splits each layer into positive neurons E and negative neurons I. Goodness is a probability that is symmetric by
construction:

  p(E, I) = (||l_E||^2 + eps) / (||l_E||^2 + ||l_I||^2 + 2 eps)   (Eq. 1),  with p(E, I) = 1 - p(I, E).

Positive neurons should be active on positive samples, negative neurons on negative samples; the ratio of the two
activities is the score. No threshold hyperparameter. Normalisation between layers (Eq. 2): each set is normalised
independently to the same squared norm so every latent has goodness 0.5 and carries no goodness information upward.
Lateral inhibition: k-winners-take-all (all neurons zero except the k most active) per layer; the paper reports the real
number of highly active neurons ends below k for most data.

Extra loss term (Eq. 3) to keep activity away from zero (gradient explodes near zero activity):
L(L_l) = (1 + exp(-alpha * ||L_l||_1)) * L_BCE(L_l), alpha a scaling hyperparameter. Appendix D analyses gradient and
update behaviour (derived for ReLU although the experiments use sigmoid).

Negatives: label embedded in the input with the "Symba" random-pattern encoding (pattern size 100, density 0.1); the
negative sample is the input with a wrong label pattern. For continual learning (Algorithms 1 and 2, Appendix A) the
negative phase forwards every known label one at a time and stores the goodness of each in a vector g; BCE is applied on
each coordinate. Class-IL: a new label is registered with a new encoding pattern when first seen, so g grows. Task-IL:
only labels of the current task are forwarded (labels of other tasks are neither positive nor negative). Domain-IL needs
no change. There is no separate classification layer: every layer is a classifier.

### (b) Accuracy against backprop (paper-reported, non-continual, Table 1, best test accuracy within 100 epochs)

| Method | MNIST | FMNIST | KMNIST | EMNIST letters |
|---|---|---|---|---|
| Backprop | 98.25 | 89.47 | 92.11 | 92.19 |
| FFA | 97.77 (-0.48) | 85.75 (-3.72) | 91.86 (-0.25) | 87.25 (-4.94) |
| SFFA | 97.87 (-0.38) | 89.39 (-0.08) | 90.47 (-1.64) | 88.63 (-3.56) |

Setup (Table 4): 2 hidden layers of 1400, learning rate 1e-4, batch 512, residual connections from the input to the hidden
layers, activity normalisation on, goodness clamp 1e-4, FFA uses ReLU, SFFA uses sigmoid, label pattern size 100, density
0.1. Accuracy is the best test accuracy during training (selection on test; MEASURED by the authors, no seeds reported
for Table 1). Datasets are 28x28 grey with uniform background; no convolutions, no CIFAR (stated limitation, "lack of
robust convolutional adaptations"). Gap to backprop is 0.1 to 1.6 points on the three 10-class sets and 3.6 points on
26-class EMNIST. Sparsity (Appendix C): Hoyer score of SFFA latents 0.97 to 0.99 (positive) versus 0.84 to 0.92 for FFA;
SFFA uses fewer than 20 highly active neurons in most cases, and aggregated activity is concentrated on a few neurons
while FFA spreads over all.

### (c) Forgetting

Protocol: Avalanche library; Split MNIST and Split FMNIST, 5 tasks of 2 classes (random partition), class-, domain-, and
task-incremental (van de Ven / Hsu definitions); 2 epochs per task, learning rate 1e-3, 10 seeds, accuracy on the joint
test data of all classes seen, plus Fgt (forgetting, lower better) and FwT. Hyperparameters (Table 5): EWC lambda 1e5; SI
lambda 1e3, epsilon 0.1; Replay buffer N = 500 samples; GEM 20 samples per task, gamma 0.5; MAS mu 1, alpha 0.5. Plain
Adam row is the no-protection baseline.

Table 2 final accuracy (%, mean +- SEM over 10 seeds), Split MNIST:

| Method | Class-IL BP | FFA | SFFA | Domain-IL BP | FFA | SFFA | Task-IL BP | FFA | SFFA |
|---|---|---|---|---|---|---|---|---|---|
| Adam | 19.81 | 18.34 | 19.85 | 67.50 | 70.87 | 69.86 | 91.40 | 90.01 | 88.44 |
| EWC | 19.77 | 26.79 | 20.32 | 72.47 | 78.54 | 74.70 | 98.33 | 96.55 | 94.48 |
| SI | 19.81 | 28.01 | 20.50 | 73.06 | 77.32 | 72.25 | 98.93 | 96.43 | 96.08 |
| MAS | 21.21 | 19.18 | 20.04 | 75.42 | 71.04 | 69.93 | 99.26 | 90.11 | 90.75 |
| Replay | 87.75 | 81.28 | 90.03 | 94.16 | 93.01 | 95.17 | 99.07 | 98.34 | 99.17 |
| GEM | 62.85 | 74.62 | 69.73 | 86.10 | 88.26 | 87.73 | 98.44 | 97.15 | 98.19 |

Split Fashion-MNIST:

| Method | Class-IL BP | FFA | SFFA | Domain-IL BP | FFA | SFFA | Task-IL BP | FFA | SFFA |
|---|---|---|---|---|---|---|---|---|---|
| Adam | 19.74 | 21.98 | 20.18 | 60.42 | 64.25 | 59.84 | 89.37 | 78.16 | 80.74 |
| EWC | 20.21 | 23.54 | 22.58 | 62.69 | 69.03 | 66.43 | 94.23 | 93.14 | 93.25 |
| SI | 20.41 | 25.84 | 23.33 | 63.24 | 68.59 | 62.91 | 96.82 | 90.59 | 90.47 |
| MAS | 21.88 | 22.17 | 21.54 | 65.38 | 64.48 | 63.15 | 96.95 | 79.97 | 82.78 |
| Replay | 78.97 | 72.85 | 79.38 | 87.69 | 86.58 | 88.42 | 97.09 | 96.83 | 97.29 |
| GEM | 60.35 | 68.07 | 64.90 | 80.40 | 82.19 | 80.93 | 96.46 | 95.62 | 96.07 |

Standard errors: backprop 0.04 to 2.8; FFA much larger (up to 10.7); SFFA in between (the paper says SFFA has lower
variance than FFA).

Forgetting measure Fgt (Table 6, lower better), Split MNIST class-IL: Adam BP 99.17, FFA 93.47, SFFA 99.26; EWC BP 99.25,
FFA 84.35, SFFA 98.48; SI BP 99.27, FFA 81.14, SFFA 98.26; MAS BP 97.77, FFA 92.31, SFFA 98.98; Replay BP 14.23, FFA
11.33, SFFA 10.91; GEM BP 45.63, FFA 21.52, SFFA 36.68. Split FMNIST class-IL Adam: BP 96.98, FFA 85.09, SFFA 94.64;
Replay BP 18.66, FFA 18.53, SFFA 18.35. Domain-IL Adam MNIST: BP 37.73, FFA 34.37, SFFA 35.74; Task-IL Adam MNIST: BP
10.94, FFA 10.97, SFFA 13.74. Forward transfer is about -16 in class-IL for all three (a property of the metric with
unseen classes) and small elsewhere.

What this says:
- Class-IL without replay: all three collapse to about 20% (one of five tasks is remembered; chance-like), including
  SFFA. The only FF-style case clearly above that is FFA with EWC or SI (26.8 and 28.0 on MNIST, 23.5 and 25.8 on FMNIST)
  with very large variance: the paper says it retained knowledge in about half the runs. So local layer-wise rules do NOT
  solve class-incremental forgetting by themselves.
- With replay, SFFA beats backprop by 2.3 points (MNIST class-IL 90.03 vs 87.75) and 0.4 (FMNIST 79.38 vs 78.97); FFA is
  below backprop with replay (81.28, 72.85). With GEM, FFA and SFFA are ahead of backprop by 12 and 7 (MNIST) and 8 and 4
  (FMNIST).
- Domain-IL: FF-style rules do about 0 to 6 points better than backprop with EWC/SI (FFA noisy), worse with MAS.
- Task-IL: backprop is better without replay (EWC 98.33 vs 96.55 / 94.48; SI 98.93 vs 96.43 / 96.08; MAS 99.26 vs 90.11 /
  90.75), because FF has no multi-head isolation; equal with replay.
- The authors' own explanation of why non-replay class-IL fails: once a class has gone, its label is still forwarded as a
  negative in later tasks (all labels are forwarded), so the layers learn to answer negatively to old labels. This is a
  failure of the negative-data design, not a representation problem.
- Claim "less forgetting" is supported only by the Fgt table in class-IL: FFA has lower Fgt than backprop in the
  non-replay rows (81 to 93 vs 98 to 99) but accuracy stays near 20 to 28, so the lower Fgt is not useful forgetting
  protection by itself. SFFA's Fgt is about the same as backprop's. Overall: modest, inconsistent.

### (d) Operations and memory

Real-valued weight matrices, sigmoid, squared norms, ratio, normalisation (division), k-WTA sort or top-k, one forward pass
per known label per example (cost grows with the number of classes: 10 or more passes per sample). Memory: layer-wise
training lets one layer be held at a time (stated motivation); replay needs a buffer (500 samples) and GEM stores 20 per
task. No hardware cost figures. EWC/SI/MAS need extra per-weight importance memory.

### (e) Limitations (authors and ours)

Authors: no convolutional version, only uniform-background grey images (no CIFAR); task-IL clash with multi-head isolation;
CL methods built on a feature layer do not apply because every layer is a classifier; MAS does not work well with FF;
FFA has high run-to-run variance. Ours: the best epoch is selected on test accuracy for Table 1; only 5 tasks of 2 classes
on two easy datasets; only 2 epochs per task; hyperparameters (EWC 1e5, SI 1e3) not tuned per model; no CIFAR continual
test. Class-IL without replay is not solved.

### (f) Fit to L

Positive/negative neuron split with a ratio goodness is natural for counting: for a gate layer, count the firing gates in
the E half (c_E) and in the I half (c_I). Goodness = c_E versus c_I, decision "positive" if c_E > c_I (integer compare, no
division, no multiply). Learning: on a positive example with c_E <= c_I, increment counters of the E gates that nearly
fire, decrement those of the I gates that fire; reverse on negatives. k-WTA is just "keep the top-k counts", which is also
a sparse code and fits our event-driven lookups. The sparse, specialised neurons (Hoyer 0.97 to 0.99) suggest a column or
address per class, which is similar to how a counting memory would store a class.

Forgetting lesson for L: do not forward all known labels as negatives when the old data are not present; restrict the
negative phase to the current classes plus a small, fixed set of replayed or synthetic negatives, or freeze the E/I
counters of old classes. The paper's own result is that this negative design makes old classes decay.

One concrete small test: Split-MNIST (or our gate-network benchmark) in 5 tasks of 2 classes, class-incremental, no
replay, counting version of SFFA with (i) negatives = all known labels (the paper's choice) versus (ii) negatives =
current-task labels only with old-class counters frozen, 10 seeds, report final accuracy and forgetting. Expect (i) to land
near 20% like the paper's Adam rows; the interesting number is (ii).

---

## 3. Lassig et al., sparse-recurrent Deep Feedback Control (arXiv 2212.04316)

### (a) Mechanism exactly

Not a Forward-Forward method. It uses Deep Feedback Control (DFC, Meulemans et al. 2022): a feedback controller sends an
error-derived control signal u(t) to every neuron through feedback weights Q_i; neuron dynamics integrate feedforward and
feedback input until a steady state (ss) is reached:

  tau_v * dv_i/dt = -v_i + v_i^ff + v_i^fb = -v_i + W_i * phi(v_{i-1}) + Q_i * u(t)   (Eq. 1),  r_i = phi(v_i).

Forward weight update (Eq. 2), local (post-synaptic target minus feedforward activity times presynaptic activity):
Delta W_i = eta * (r_{i,ss} - phi(v^ff_{i,ss})) * r_{i-1,ss}^T. In sparse-recurrent DFC, each weight update is centred to
zero mean before applying (so that no group of neurons becomes dominant in the winner-take-all). The feedback weights are
re-initialised each data point as the Jacobian of the loss with respect to the neuron activations (a simplification).

Added mechanisms:
1. Dynamic sparsity (3.2): a winner-take-all mask. At each time step a small fraction s_i(t) of neurons is set to zero,
   increased gradually until the target sparsity s_{i,ss}. Which neurons survive depends on a mix of feedforward and
   feedback (top-down) activity (Fig. 3a varies the fraction fb/(ff+fb)). Forward weights into silenced neurons are frozen.
2. Lateral recurrent gating (3.3): feedforward drive is multiplied by a gate between 0 and 1,
   v_i^ff(t) = W_i phi(v_{i-1}(t)) * sigmoid(R_i |r_i(t)|)   (Eq. 3), then the population activity is rescaled to keep
   total magnitude. Recurrent weights R_i are learned only for inactivated neurons, by a Hebbian-like rule
   Delta R_i = -eta |phi(v^ff_{i,ss})| |r_{i,ss}|^T   (Eq. 5; general form Eq. 4:
   Delta R_i = eta (|r_{i,ss}| - |phi(v^ff_{i,ss})|) |r_{i,ss}|^T), zero-mean centred. So neurons that were silenced learn
   which active neurons should inhibit them. Test time: plain feedforward pass, no feedback and no recurrence.

Task-free: no task boundary or task id at training or test time (the other methods, EWC and SI, get boundaries).

### (b) Accuracy against backprop

No non-continual accuracy table in the paper; the DFC base is cited from Meulemans et al. (UNVERIFIED, not read). All main
results are plotted in figures, with no numeric table. From the figure axes and caption (read from rendered Fig. 3 only):
the domain-IL window-averaged accuracy over combinations of layer sparsity levels lies between 0.66 and 0.77 (Fig. 3c
heatmap values 0.66 to 0.77). Other numbers (Fig. 2) could not be read as values from text: UNVERIFIED.

### (c) Forgetting

Protocol: Split-MNIST, 5 tasks (digit pairs 0/1, 2/3, 4/5, 6/7, 8/9), 5 seeds, standard deviations in plots. Domain-IL
(parity output, input digits change) and class-IL (a different class per digit) but "with task information entirely omitted
in both training and testing". Evaluate (i) fixed 4 epochs and varying learning rate, (ii) fixed learning rate and varying
early-stop training accuracy; the authors argue a single learning rate is misleading and judge both peak and robustness.
Baselines: backprop, EWC, SI (EWC and SI use task boundaries). Architecture (Appendix B Table 2): 2 hidden layers, sizes
20,20 (domain-IL) and 200,200 (class-IL), lr 0.001 outside the learning-rate sweep, batch 512, 4 epochs, Adam, Xavier
initialisation. Model-specific (Table 1): sparsity levels for the two hidden layers and output: domain-IL 0.4, 0.8, 0.5;
class-IL 0.2, 0.8, 0.0 (the numbers in the extracted table are garbled between rows; this reading is UNVERIFIED);
recurrent learning rate 40; tanh for DFC, relu for BP/EWC/SI; EWC regularisation coefficient 200 (domain) and 200 (class);
SI 10 and 100 (assignment of values to rows UNVERIFIED because of column garbling).

Results as stated in the text (qualitative; no numbers): domain-IL, sparse-recurrent DFC clearly outperforms backprop and
has a profile similar to EWC; versus SI it has lower peak accuracy but stays above 70% over a wider range of learning
rates. Class-IL: it outperforms all other methods (backprop, EWC, SI) in both peak accuracy and average accuracy, and for
most early-stop accuracies. Ablations: neither sparsity alone nor recurrence alone changes continual performance
significantly (Fig. 3b); the combination does. Using feedback to choose the silenced neurons beats feedforward-only
selection across a range of learning rates (Fig. 3a). First-layer best sparsity small but non-zero, second layer higher
(Fig. 3c). Mechanism measurements: with the combination, inter-label minus intra-label separation (Eq. 6, cosine distance
of summed absolute activity) is higher exactly where continual accuracy is higher (Fig. 3e); sparse DFC alone separates
representations but does not improve accuracy (so separation alone is not sufficient); recurrent gating makes new targets
align with the previously learned hyperplane (Fig. 4b) and moves old representations less toward it (Fig. 4c); in class-IL
it lowers effective dimensionality (effective rank) of the targets and raises the fraction of the old subspace left
unaltered (gamma, Eq. 16, Fig. 5). Appendix A Fig. 6: cumulative accuracy of first i tasks, each model at its own best
learning rate. Note: without replay, class-IL continual accuracy for backprop is the usual 20% region (Hsu et al. cited in
paper 2), so "outperforms" may be only a few tens of points; actual values UNVERIFIED (figure only).

So: yes, a local, sparse, Hebbian-gated rule can forget less than backprop without replay or task boundaries, but only
with the sparsity plus recurrent-gating pair, on a 5-task Split-MNIST, with hyperparameters tuned on that same benchmark
(stated in Appendix B), and the sparsity is chosen using top-down error information (so it is not purely layer-local).

### (d) Operations and memory

Real-valued matrices W, Q, R (R is a layer-by-layer lateral matrix per layer), sigmoid gates multiply activations, tanh,
and an iterative dynamical system (many time steps per example until convergence, plus a controller). The authors say it is
computationally less efficient than standard CL algorithms on GPU and suited to neuromorphic hardware. No exemplar memory,
no per-weight importance memory (advantage over EWC/SI), but extra lateral matrices and feedback weights.

### (e) Limitations

Only Split-MNIST; tiny networks; domain-IL net is 20-20 units; tuned sparsity per scenario; iterative convergence cost;
compared with EWC and SI that use task boundaries; no replay comparison; no numbers in text, results only in figures with
five seeds; the authors say it could be combined with replay later.

### (f) Fit to L

The useful idea is the pair: sparse winner-take-all selection of which units may learn, plus a learned lateral inhibition
(which silenced unit is blocked by which active unit) so a new class is routed to different units. In a gate or counter
network: per layer keep a k-WTA mask chosen from the input drive plus the current class signal (label bit added to the
drive, a form of top-down), update only the counters of the winners (event-driven, sparse), and keep a small integer
inhibition table R[i][j] that is incremented when unit i was silenced while unit j was active on a sample; at train time
use it to veto i when j is active. Everything is increments and compares: integer and multiplier-free. The sigmoid gate is
replaced by a veto (0/1). Test time is a plain forward pass, as in the paper, so inference cost does not change.

One concrete small test: the 5-task Split-MNIST class-IL setting on a counter network, no replay, with and without
(a) k-WTA learning mask and (b) integer lateral veto table, 2x2 ablation, 5 seeds, report final accuracy and the fraction
of old-class counters changed by a new task (our version of gamma, the unaltered-subspace fraction). The paper predicts
only the combination (a)+(b) helps.

---

## 4. Belilovsky, Eickenberg, Oyallon, Greedy layerwise learning (arXiv 1812.11446)

### (a) Mechanism exactly

Supervised layer-by-layer training with an auxiliary classifier per layer (Algorithm 1). Network of J blocks. From x_0:

  x_{j+1} = rho(W_{theta_j} P_j x_j),   z_{j+1} = C_{gamma_j} x_{j+1} in R^c   (Eq. 1)

with 3x3 convolution W, ReLU rho, P_j either identity or the invertible downsampling of Dinh et al. (2x2 spatial sub-sampling
into 4 channel groups, resolution halved, no information lost), and auxiliary classifier

  C_gamma x_j = L A x_j for k = 1 (spatial average A then a linear map L to c classes);
  C_gamma x_j = L A rho W~_{k-2} ... rho W~_0 x_j for k > 1 (k-1 extra 3x3 conv layers of constant width before A and L)  (Eq. 2).

Training: at depth j, with all earlier parameters frozen, solve (theta_j, gamma_j) = argmin of the empirical risk
(1/N) sum_n l(z(x_j^n; theta, gamma), y^n) with SGD and cross-entropy. What is passed between layers: the (detached)
feature map x_{j+1}, forward only; no gradient from higher layers. After training layer j, the auxiliary head is discarded
(except the last, which becomes part of the model) and layer j+1 is trained on the stored or recomputed x_{j+1}.
k is the auxiliary depth: k = 1 means a sequence of one-hidden-layer problems; k = 2, 3 means the layer is trained
through a 2- or 3-hidden-layer shallow CNN. Negatives: none, it is plain supervised cross-entropy with the true label at
each layer. An output ensemble Z = sum_j 2^j z_j (weighted average of all auxiliary outputs, deeper weighted more).
Theory: Prop. 3.1 (progressive improvement of the training risk with depth if P_j = Id); Prop. 3.2 (errors of the layer-wise
cascade: ||x*_J - x^_J|| = O(J^2 epsilon) for 1-Lipschitz layers); linear separability is the objective of k = 1. No
fine-tuning of the whole network is ever done.

### (b) Accuracy against end-to-end backprop (paper-reported, single runs; the separability study reports average standard
deviation 0.58% over 5 initialisations)

CIFAR-10 (Table 2, standard augmentation, SGD momentum 0.9, batch 128, lr 0.1, decay 0.2 every 15 epochs, 50 epochs per
layer; J = 5 for k = 1, downsampling at layers 2 and 3, M = 256):
- SimCNN k = 1: 88.3 (ensemble 88.4). The end-to-end version of this model: 89.7, with 5 times more GPU memory than k = 1
  training. AlexNet-reference 89.0. Gap to end-to-end 1.4 points.
- k = 2: 90.4 (90.7); k = 3: 91.7 (92.8) (J = 4, M = 128, M~ = 256, downsampling at j = 2, batch-norm used in the auxiliary
  problems for k = 2, 3). Reference end-to-end: 89 (AlexNet), 92.5 (VGG), 96.0 (WRN 28-10; has skip connections). Other
  sequential methods: BoostResNet 82.1 (the text quotes 82.0), ProvableNN 73.4, Mosca et al. 81.6, Scattering + linear 82.3,
  Feedback Alignment 62.6 [67.6 with backprop for that net].
- Pruning experiment: baseline 5-layer width-64 net end-to-end 87.5; layerwise k = 3, J = 3, M = 128 with filter pruning
  to 64 after each layer and a 20-epoch fine-tune of the auxiliary net: 87.6.

ImageNet (Table 3, single-crop validation, J = 8, 45 epochs per layer, batch 256, lr 0.1, decay 0.1 every 20 epochs, 4 GPUs;
ensemble in parentheses):

| Model | Top-1 | Top-5 |
|---|---|---|
| SimCNN k = 1 | 58.1 (59.3) | 79.7 (80.8) |
| SimCNN k = 2 | 65.7 (67.1) | 86.3 (87.0) |
| SimCNN k = 3 | 69.7 (71.6) | 88.7 (89.8) |
| VGG-11 trained with k = 3 | 67.6 (70.1) | 88.0 (89.2) |
| VGG-11 end-to-end (same 45-epoch schedule) | 67.9 | 88.0 |
| AlexNet e2e | 56.5 | 79.1 |
| VGG-13 e2e | 69.9 | 89.3 |
| VGG-19 e2e | 72.9 | 90.9 |
| ResNet-152 e2e | 78.3 | 94.1 |

(Reference rows read from the garbled table columns; the AlexNet, VGG and ResNet reference values follow the column order
and are consistent with torchvision values; flag as read-from-layout.) Alternatives to backprop: Feedback Alignment 6.6%
top-1 on ImageNet versus 50.9% for its backprop counterpart, and 63% versus 68% on CIFAR-10 (the text); target propagation
and feedback alignment from Bartunov et al. and Xiao et al. get near-chance top-1 on ImageNet in the table; Scattering +
linear 17.4. Gap to end-to-end for the same architecture: VGG-11 k = 3 is 0.3 points top-1 behind (67.6 vs 67.9) and equal
top-5 (88.0 vs 88.0); the ensemble is ahead (70.1 / 89.2). k = 1 is a large step behind the k = 3 model (11.6 points top-1).
A smaller final auxiliary net (M~f = 512 instead of 2048): top-5 88.5 vs 88.7 (Table 1); parameters 46M vs 102M (Table 7).
Downsampling choice (Table 6, CIFAR k = 1): strided conv 87.8, invertible 88.3, avg-pool 87.6, max-pool 88.0.
Per-layer accuracy rises rapidly: top-5 from about 23% at layer 1 to about 80% at layer 8 for k = 1 (Fig. 2); train accuracy
87% at the end, so the k = 1 model overfits.

Separability study (CIFAR-10, J = 5, M = 64/128/256, no downsampling): linear separability increases with depth for every k;
k = 1 rises fastest at early layers but flattens lowest; deeper auxiliary problems (k = 2, 3, 4) rise slower but end higher;
CNN-1 and CNN-2 separability improves much more for k > 1. So the shallow k = 1 objective is not the best local objective:
a layer must produce a good input for a small classifier, not only linearly separable features.

### (c) Forgetting

Nothing: no continual-learning experiment (UNVERIFIED for any forgetting property). Related only indirectly: each layer is
trained once and then frozen, so later training cannot disturb earlier layers by construction, but the paper does not use
this for incremental learning. The Caltech-101 transfer study (Appendix C.3, Table 8, linear model on k = 1 features,
30 images per class, 10 splits) gives 45.5 / 59.9 / 70.0 / 75.0 / 82.6 % accuracy at layers 1, 2, 3, 4 and 8, against
46 +- 1.7 for a ConvNet from scratch; transfer works and improves with depth.

### (d) Operations and memory

Convolutions (matrix-type operations) with ReLU, batch-norm in the k = 2, 3 version, SGD with backprop inside each
auxiliary problem (so within a layer plus its head, gradients are computed; there is no backprop across the whole network).
Memory: the paper reports 5x less GPU memory for k = 1 training than end-to-end on CIFAR-10 and says larger layerwise
models than end-to-end can be trained on the same hardware; activations of previous layers do not need to be kept for a
backward pass. Compute is not reduced (45 epochs per layer on 4 GPUs for ImageNet; VGG-11 k = 3 trained in the same
45-epoch budget as the e2e baseline). Parameter counts (Table 7): SimCNN k = 3 Mf 512: 46M; k = 3: 102M; k = 2: 64M; k = 1 J = 6:
96M; AlexNet 60M; VGG-16 138M. Most parameters of k = 2, 3 models are in the final auxiliary network.

### (e) Limitations

Layer-wise models lack skip connections and are well below ResNet-152 (78.3 / 94.1); the authors defer residual versions;
the k = 1 model overfits; they did not optimise parameter efficiency; deeper auxiliary heads (k = 3) are needed to match
end-to-end, so each layer still contains a small multi-layer learner trained by backprop (not a one-shot local rule);
no continual learning, no hardware analysis; single runs for the large tables; later layers cannot correct earlier ones
(Prop. 3.2 shows errors accumulate, O(J^2)).

### (f) Fit to L

Nearest to our own failed test (per-layer local readout, 8 to 15 points behind). The paper explains why: with k = 1 a layer
only maximises its own linear separability, which plateaus lower; with a deeper local head (k = 2 or 3) the same greedy
scheme reaches end-to-end accuracy on VGG-11 and on CIFAR-10 is within 1.4 points (k = 1) or better than the e2e AlexNet
reference (k = 3: 91.7). It is the cleanest evidence that greedy per-layer training can close the gap, and what closes it
is a richer local head, not a different goodness.

Integer or gate version: a local head is a small gate network (one or two gate layers) followed by an integer count-per-class
readout trained by sign-step counters; the local loss is the integer class-count margin (target class count minus the best
wrong class count), with a sign step when the margin is below a fixed integer margin. Invertible downsampling is a pure
reshuffle of bits (no information loss), a good fit to a bit-level chip. Spatial averaging A becomes a count of active gates
per spatial quadrant (2x2 counts, integers).

One concrete small test (directly addresses our 8 to 15 point gap): on the same gate network and dataset, keep greedy
per-layer training but give each layer an auxiliary head of k = 1 (counts readout) and k = 2 (one extra gate layer then
counts), with the head discarded after the layer is trained, and report the accuracy gap to integer end-to-end error
passing for k = 1 and k = 2. If k = 2 closes most of the 8 to 15 points, the gap came from head capacity.

---

## Summary across the four

Which local rules come within a few points of backprop (paper-reported):
- Greedy layerwise with a k = 2 or 3 hidden-layer auxiliary head: matches or beats end-to-end VGG-11 on ImageNet top-5 (88.0
  vs 88.0), 0.3 behind in top-1; CIFAR-10 k = 1 within 1.4 points. Real-valued convolutional, trained with backprop inside
  each block.
- Forward-Forward, fully connected, MNIST: 1.36% to 1.46% test error versus about 1.4% for backprop (no gap);
  CIFAR-10 with local receptive fields: 2 to 4 points worse (41 vs 37 and 41 vs 39 test error).
- SFFA: 0.1 to 0.4 points behind on MNIST and FMNIST, 1.6 on KMNIST, 3.6 on 26-class EMNIST; only grey, uniform-background images.
- Sparse-recurrent DFC: no accuracy-against-backprop number in the text.

Do local rules forget less?
- Not on their own. SFFA class-IL without replay: about 20% like backprop (SFFA 19.85 to 23.33, backprop 19.74 to 21.88);
  only FFA with EWC or SI reaches 24 to 28% with very high variance. With replay SFFA is 0.4 to 2.3 points above backprop in
  class-IL; task-IL is worse than backprop without replay.
- Lassig et al. report better-than-backprop and better-than-EWC/SI class-IL results without task boundaries when sparsity and
  learned lateral gating are combined (qualitative; figure values not extracted).
- Belilovsky et al. and Hinton report nothing on forgetting.

Integer gate network suitability: the count-based goodness with k-WTA pass-up (Hinton/SFFA), the integer lateral veto
table and learned-mask updates (Lassig), and the deeper local head (Belilovsky) can all be written with increments, compares
and top-k, with no multiply, but none has been shown in the papers as an integer or binary system (UNVERIFIED as such; our
suggestions only).

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
