# How brains compute and move "weights", and what L takes from it

Scope: short horizon (weeks, not years). The brain-on-a-chip concept stays our identity. Each principle below is paired
with an experiment we can run now and a number we can show. Research was via web search (excerpts, not full-paper reads);
figures are second-hand until checked. Labels: MEASURED / SIMULATED / ESTIMATED / PROJECTED.

## 1. What the brain does, in five principles

| # | Principle | What the literature says | Source |
|---|---|---|---|
| 1 | **Memory and compute are the same place.** A synapse is both the weight and the multiplier; weights are never fetched. | General neuroscience; the reason in-memory and neuromorphic hardware exist (see `brain_as_chip_research.md`). | (background) |
| 2 | **Activity is sparse because spikes cost energy.** Signalling energy is dominated by action potentials and synaptic transmission; one review argues firing much above a few spikes/s/neuron would exceed the brain's budget, which pushes toward sparse codes. | Attwell & Laughlin: ~47% of grey-matter signalling energy to action potentials, ~34% to postsynaptic effects; later work lowers the action-potential share and puts synaptic transmission near 55%. | [Attwell & Laughlin summary](https://www.citedrive.com/en/discovery/an-energy-budget-for-signaling-in-the-grey-matter-of-the-brain/), [energetics review](https://arxiv.org/pdf/1602.04019), [Harris & Attwell revision](https://discovery-pp.ucl.ac.uk/1368741/1/1368741.pdf) |
| 3 | **Only surprises travel.** Predictive coding: higher areas send predictions down, and only prediction errors go up, which removes predictable information from the signal. | The efficiency argument is largely theoretical; neural prediction-error responses are seen in rodent V1, but not energy-measured. | [predictive coding review](https://arxiv.org/pdf/2112.10048), [spiking predictive coding](https://arxiv.org/html/2409.05386v1) |
| 4 | **Fast store plus slow store.** The hippocampus learns single events fast with sparse, non-overlapping codes; the neocortex learns structure slowly; replay consolidates one into the other. | Complementary Learning Systems theory (Kumaran, Hassabis, McClelland 2016 update); ML versions pair a Hopfield-style episodic store with a slower generative model. | [CLS update](https://web.stanford.edu/~jlmcc/papers/KumaranHassabisMcClelland16FinalMS.pdf), [2025 CLS network](https://arxiv.org/pdf/2507.11393) |
| 5 | **Only the relevant neurons run, per input.** Context decides which cells fire. | The ML counterpart is *contextual sparsity*: Deja Vu finds ~85% structured sparsity per input in LLMs and, with a cheap predictor, reports >2× lower OPT-175B latency than FasterTransformer. TEAL (training-free activation sparsity) reports 40-50% model-wide sparsity and up to 1.53×/1.8× wall-clock decode speed-up on A100. The Deja Vu authors warn prediction overhead can easily make things slower. | [Deja Vu](https://arxiv.org/abs/2310.17157), [TEAL](https://arxiv.org/pdf/2408.14690) |

## 2. The direct answer to "big weights are the problem"

Principle 5 is the strongest match to what you said. The GPU's cost per token is mostly reading weights from memory. The brain avoids this by only activating a small, context-chosen set of neurons.
Published ML work shows the same trick on today's models: skip the weight columns for inactive neurons and the decode step reads fewer bytes.
That is "removing the big matrices from the critical path" in a form that has measured speed-ups, on models people already have.

L's brain-like role here: a small, stateful, event-driven unit that **predicts which parts of the big model will be needed**, ahead of time, from its own leaky state. That is a leaky integrator per hidden unit, which is L's native neuron.

## 3. Mapping to L, and what to test

| Principle | L component today | Experiment (all weeks, not years) | Number to show |
|---|---|---|---|
| 5. Contextual sparsity | none yet | `hw/system/activation_sparsity.py` on the real 3B model: output error when only a fraction f of MLP weight columns is read, using an oracle, the previous token's active set, or a leaky trace (L-style state). | Error vs fraction of weights read; whether a cheap stateful predictor stays close to the oracle |
| 2. Sparse activity | event-driven network, skips silent neurons | Existing RTL results: 2.5×-4.5× fewer cycles and weight reads than a dense pass (simulated, 600-byte sample, small model). Add the accuracy-vs-firing-rate curve. | Events per token vs next-byte accuracy |
| 3. Predictive coding | draft is the prediction, GPU verification is the error signal | Already measured: 2.2-2.3 tokens/GPU pass on real 3B and 9B models (acceptance). Extension: send the GPU only where the draft is uncertain (confidence-chosen length, simulated). | Tokens/pass and wall-clock (still needed) |
| 4. Fast + slow memory | recall hash tables (fast, one-shot, sparse) + trained network (slow) | Hysteresis update on recall entries (a synapse-like confidence count): +2.2 points agreement on the fast path (simulated). Next: replay recent recall entries into the slow network to adapt to a new domain. | Agreement before/after a domain shift |
| 1. Compute in memory | L weights sit on-chip next to the lanes | Ternary weights: weights in {-1, 0, +1}, multiply-free and smaller. Training in progress, see section 4. | Accuracy and weight size, ternary vs int4 |

## 4. Result so far on multiply-free weights

Ternary vs int4, trained from scratch under identical settings (3,000 steps): partway through training the ternary model's loss was far worse
(about 3.0 vs 1.8 at step 1,700) and its firing rate was about 0.63 vs 0.35, so it was both less accurate and less sparse. Final numbers will follow when the restarted runs finish. Interim reading only: at this network size, removing the multiplications costs quality.

## 5. What we can say to an investor today, without overclaiming

- The concept is built from five specific brain principles, each tied to a published result and a test of ours.
- Measured on real models: lossless drafting gives about 2.2× fewer big-model passes on code (acceptance, not yet wall-clock).
- Simulated on our chip: event-driven operation cuts cycles and weight reads versus a dense pass; hysteresis memory raises agreement with the GPU model.
- Not yet shown: that L beats a free software drafter, or that a predictor can cut real-model weight reads. Those are the two experiments in section 3 that decide the pitch.
- Not claimed: a human-brain-scale chip, replacing the GPU, or any silicon measurement.
