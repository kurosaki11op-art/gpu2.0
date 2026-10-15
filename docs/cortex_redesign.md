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

| Problem | Today | SPARK Cortex (status 15 Oct 2026) | Label |
|---|---|---|---|
| Training cost | backprop on GPUs, many passes | counting on the chip, each example seen once; senses learned on chip without labels (`ENC_LEARN`, 94.5 / 80.0 vs 95.0 / 79.2 with PC detectors) | SIMULATED |
| Forgetting | a network keeps ~20% after 5 learning stages | 5 stages: digits 94.6, clothing 78.3, sound 71.2 (with the cochlea noise floor) vs network 19.5 / 20.0 / 15.9; new conditions of known classes: context memory 85% vs 45% (in RTL) | SIMULATED |
| Memory / knowledge transfer | weights cannot be merged cleanly | two chips' memories merged: 91.4% after one night (bit-exact board design) | SIMULATED |
| Efficiency | ~203k multiply-adds per decision (small net) | 0 multiplies; 9.4 nJ per decision by operation count; SKY130 layout ~0.18-0.26 uJ per decision with clock gating and the pipelined core | ESTIMATED |
| E-waste | a new task means a new model, often new hardware | the same chip keeps learning new classes and conditions in the field (above); what it knows exports to a replacement chip (memory transfer, bit-exact over UART); it learns its own sensory detectors, so a new sensor does not need a PC retrain; one design senses images and raw sound | SIMULATED (each part); lifetime saving not measured |
| Accuracy | 97.7% digits / 87.5% clothing (network, all at once) | all at once 96.6 / 83.7 / 71.1; behind a network few-shot at 5 examples | SIMULATED, gaps remain |

What it is not: it does not replace large language models, and we will not say it does. The claim is narrower and
provable: a chip that learns continuously, locally and transferably, which today's AI chips cannot do.

## Status

- Month 1 (accuracy gap): done in simulation, see `hw/results/cortex_month1.md`. The best brain component is within
  1.6 points of the network on digits, clothing and spoken words, and keeps that accuracy when learning in stages
  (network falls to 16-20%). Open: memory size (MB, must reach ~100 KB) and one decision rule for all tasks.

- Month 2 (memory, one rule): done in simulation, see `hw/results/cortex_month2.md`. Images 84 KB (137x smaller), one
  rule for every task, self-regulated sleep; accuracy in stages 94.6 / 78.7 / 69.7; few-shot still behind.
- Month 3 (RTL): done early. Integer chip model, core and Tang Nano top bit-exact (0 mismatches), bitstream built with
  timing met. Month 4 (real board run, measured power) needs the user's board.

## 6-8 month plan (each step ends with a measured result)

| Month | Work | Proof at the end |
|---|---|---|
| 1 | Close the accuracy gap: stable correction table (sleep consolidation), 2-level inputs, more detectors; add a third dataset (spoken keywords, Speech Commands) | table: brain core within 3 points of the network on 3 datasets, still no forgetting |
| 2 | Shrink memory ~100x (4-bit stochastic counters, fewer cells); one confidence-gated decision rule; few-shot via episodic memory | fits ~100 KB with under 2 points lost; few-shot at least equal to the network |
| 3 | RTL: feature layer, cortex memory, learning logic; bit-exact against the Python model | 0 mismatches over the test sets |
| 4 | Tang Nano 20K: learn live on the board over UART; measure power with a USB meter | board learns new classes in front of judges; joules per decision and per learning step, MEASURED |
| 5 | Two boards learn different things; merge memories over UART | merged board = combined knowledge, MEASURED |
| 6 | Sequence memory (existing lookup core) joins the cortex: learns streams (sensor logs, text) live | streaming prediction demo |
| 7-8 | SKY130 synthesis for area and power estimates (no fabrication), write-up, demo video, pitch | finished, documented project |

## Prior art we must cite

Weightless / RAM-based neural networks (WiSARD, 1981; BTHOWeN, 2022; ULEEN, 2023), Tsetlin machines,
Numenta's hierarchical temporal memory, competitive Hebbian feature learning, complementary learning systems.
Our contribution is the combination: label-free feature learning + additive count memory + surprise-gated
correction + merge-by-addition, in one small chip that learns after deployment. Novelty checked in
`docs/prior_art_cortex.md`: continual learning chips without backprop exist (HDC accelerators, Loihi 2), so "first" is
not claimable; generative dreams from counters with self-regulated sleep, multiplier-free, on a $25 FPGA is what we add.

Related: [Project memory](PROJECT_MEMORY.md), [First proof](../hw/results/cortex_proof.md),
[Month 1](../hw/results/cortex_month1.md), [Month 2 log](../hw/results/cortex_month2_log.md),
[Brain principles](brain_principles_for_spark.md), [Token lookup result that triggered it](../hw/results/token_lookup_real.md)
