# SPARK redesign: SPARK Cortex, a chip that learns like a brain

Decided 14 Oct 2026. Replaces the "drafting helper for GPUs" direction. Why: with a chat model, lookup drafting
gave 1.04 tokens per pass on prose and 1.7 on code (`hw/results/token_lookup_real.md`), and the chip could answer
on its own only about 6% of the time. A helper that wins at the margins is not the project.

## The idea in one line

Today's AI is trained once on GPUs and then frozen. A brain never stops learning, never needs a data centre to
learn, and does not forget yesterday when it learns today. **SPARK Cortex is a chip that keeps learning after it
ships, with brain principles only: no matrices, no multiplies, no backprop.**

## Brain principles used (and nothing else)

| Brain | SPARK Cortex | Hardware |
|---|---|---|
| Receptors fire or stay quiet | inputs become on/off spikes (brightness thresholds) | comparators |
| Neurons with local receptive fields | each feature detector sees a 5x5 patch | wires |
| Competition between neurons | only the best-matching detector fires at each spot (sparse code) | bit-match counter + max |
| Hebbian plasticity, no teacher | the winner nudges its own counters toward what it saw | small up/down counters |
| Cortex memory associates patterns with meaning | per class, count which features fire; decide by adding table scores | SRAM + adder |
| Learning only from surprise (prediction error, dopamine) | correction table written only when the answer was wrong or close | write-enable on mismatch |
| Hippocampus stores episodes, replays in sleep | episodic store for few-shot; idle-time consolidation (planned) | SRAM + replay controller |
| Memories are local and additive | knowledge = count tables; chips merge by adding | export/import over a link |
| Sequence memory (predict what comes next) | the existing lookup core (RTL done, 0 mismatches) | reused |

## Which AI problems it targets

| Problem | Today | SPARK Cortex | Status |
|---|---|---|---|
| Training cost | backprop on GPUs, many passes | counting on the chip, 1 pass (features: 3 passes, no labels) | SIMULATED |
| Forgetting (catastrophic forgetting) | network keeps ~20% after 5 learning stages | keeps 95.6% (digits), equal to learning all at once | SIMULATED |
| Memory/knowledge transfer | weights cannot be merged cleanly (92.5%, or 82.8% for different classes) | merged = trained on everything, exactly | SIMULATED |
| Efficiency | ~203k multiply-adds per decision (small net) | ~18k bit-match counts + ~600 adds, 0 multiplies | ESTIMATED |
| E-waste | new task means new model, often new hardware | same chip re-learns in the field; knowledge copies to a replacement chip | design claim, to demo |
| Accuracy | 97.7% digits / 87.5% clothing | 95.6% / 74.6% (83.6% with the correction table) | SIMULATED, gap to close |

What it is not: it does not replace large language models, and we will not say it does. The claim is narrower and
provable: a chip that learns continuously, locally and transferably, which today's AI chips cannot do.

## 6-8 month plan (each step ends with a measured result)

| Month | Work | Proof at the end |
|---|---|---|
| 1 | Close the accuracy gap: stable correction table (sleep consolidation), 2-level inputs, more detectors; add a third dataset (spoken keywords, Speech Commands) | table: brain core within 3 points of the network on 3 datasets, still no forgetting |
| 2 | Few-shot via episodic memory + learned features; on-chip-sized memory (fits ~100 KB) | few-shot at least equal to the network |
| 3 | RTL: feature layer, cortex memory, learning logic; bit-exact against the Python model | 0 mismatches over the test sets |
| 4 | Tang Nano 20K: learn live on the board over UART; measure power with a USB meter | board learns new classes in front of judges; joules per decision and per learning step, MEASURED |
| 5 | Two boards learn different things; merge memories over UART | merged board = combined knowledge, MEASURED |
| 6 | Sequence memory (existing lookup core) joins the cortex: learns streams (sensor logs, text) live | streaming prediction demo |
| 7-8 | SKY130 synthesis for area and power estimates (no fabrication), write-up, demo video, pitch | finished, documented project |

## Prior art we must cite

Weightless / RAM-based neural networks (WiSARD, 1981; BTHOWeN, 2022; ULEEN, 2023), Tsetlin machines,
Numenta's hierarchical temporal memory, competitive Hebbian feature learning, complementary learning systems.
Our contribution is the combination: label-free feature learning + additive count memory + surprise-gated
correction + merge-by-addition, in one small chip that learns after deployment. Novelty must be checked before any
claim of "first".
