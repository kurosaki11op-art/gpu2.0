# Brain-strict redesign tests (19 Oct 2026)

Audit and rule: [brain principles audit](../../docs/brain_principles_audit.md). Every number here is SIMULATED (exact integer chip model, `CortexSlow`, slow table K = 5, detectors learned on the chip by the one-pass rule),
digits = MNIST, clothing = Fashion-MNIST, 2,000 training examples per stage, 5 stages of 2 classes, 2,000 test images, 3 seeds unless noted. Scripts and raw logs: `hw/brain/experiments/month4/brain_strict_*`.
These are smaller training sets than the month-4 final numbers, so compare arms with each other, not with the final-numbers table.

## Wins (the process now passes its brain test, with the cost stated)

| Process (audit test) | Before | Now | Result |
|---|---|---|---|
| Detectors fitted offline on a PC (test 5) | offline fit: digits 93.5, clothing not run | one-pass on-chip rule: digits 94.1 | level or better on digits (clothing not compared in this run) |
| Host decides when the night happens (test 2) | night after every stage: digits 94.1 | chip sleeps when surprise writes since its last sleep reach a threshold: 94.1 / 94.7 / 94.6 at 200 / 500 / 1,000 (4 / 2 / 1 sleeps) | digits: level or better. Clothing: 79.3-79.7, equal to the chunked-feeding control (79.7) and 1.1 below the shipped path (80.8); the loss is from the chunked test setup, not the sleep trigger |
| A label on every example (test 3), rewards first, pseudo-labels only among classes rewarded in the current context, no confidence cut | all labels: digits 94.1, clothing 80.8 | digits 10 % / 5 % / 2 % labelled: 93.1 / 91.3 / 90.7; clothing 78.3 / 78.4 / 78.1 | close, not equal: 1-3 points below full labels on digits and about 2.5 on clothing, with 10-50x fewer labels. Best cut per label count on digits: 10 % -> cut 50 (93.4), 5 % and 2 % -> no cut |
| Memory (test 6, brain: synaptic pruning) | all synapses | zero the weakest slow-table synapses after the last night | digits 94.0 -> 93.5 with 19 % of synapses nonzero; clothing 80.35 -> 80.35 at 30 %, 79.6 at 21 %. The saving is ESTIMATED from the nonzero count (a sparse store also needs indices), 2 seeds |

## Failures (recorded, not adopted)

| Idea | What happened |
|---|---|
| Self-labelling over all known classes | 10 % labels 63-65, 25 % labels 73-78 on digits (precision of own labels 64-71 %). Fixed only by the context limit above |
| Rewards scattered through the stream instead of first | digits 10 / 5 / 2 % = 91.1 / 91.4 / 88.6, no better than rewards first |
| Unsupervised category layer + sparse naming (competitive Hebbian assemblies, novelty and error-driven recruitment, homeostasis) | 53-66 % on a small test, fills every slot; a penalty for missing expected bits made it worse (12-37 %). Not tuned further |
| Cascade synapses (metaplasticity, 3 extra bits per synapse) | clothing staged 80.8 -> 80.6 / 80.1 / 80.3, all at once 86.0 -> 85.3 / 84.5 / 84.1 |
| Dreams with lateral inhibition (at most K drawn features per spot) | staged worse, more so with stronger inhibition: clothing 80.8 -> 79.9 / 78.6 / 74.7, digits 94.1 -> 93.7 / 93.0 / 90.4 for K = 4 / 3 / 2; all at once level |
| Causal onset trigger at a fixed loudness (800) instead of the shipped alignment | 20 words: clean 60.7 against 68.5, worse at every noise level |

## Sound (20 words of the 35-word subset, 5 stages of 4 words, 414 test clips, so about +-3 points of noise)

| Arm | clean | 20 dB | 10 dB | 5 dB | first-stage words | last-stage words |
|---|---|---|---|---|---|---|
| shipped alignment (peak) | 68.5 | 62.2 | 47.3 | 33.3 | 77.5 | 50.6 |
| fixed-loudness onset 800 | 60.7 | 54.2 | 41.6 | 27.9 | 64.5 | 45.2 |

Adaptive onset and noisy-dream arms were still running when this note was written; see `brain_strict_sound.log` and `brain_strict_sound_rel.log`.

## Still open

Few labels on sound, novelty from inside (the chip noticing a new class itself), a context signal for fully mixed streams, a temporal layer for twin words, neighbour-conditioned dreams (needs several times the dream memory), and the RTL for sleep pressure and context-limited self-labelling (both are host-level logic in these tests).

Related: [Results index](INDEX.md), [Brain principles audit](../../docs/brain_principles_audit.md), [Journal](../../docs/journal.md), [Project memory](../../docs/PROJECT_MEMORY.md)
