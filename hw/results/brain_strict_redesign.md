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
| Knowing the context on its own (test 2): stages blend in one stream, no stage boundary, no told class list, sleep from pressure | all-labelled control on the same blended stream: digits 94.6 | context = classes rewarded among the last 30 / 60 rewards; 10 % labelled 92.7 / 93.1, 5 % labelled 91.8 (precision of own labels 84-93 %) | partly solved: about 1.5-2 points below the control with no stage information. Digits only, 3 seeds, one blend (stage index + uniform noise of +-0.8) |
| Few labels, agreement gate (the fast table must name the same class as the slow table before a pseudo-label is used) | no gate: digits 10 / 5 / 2 % = 93.1 / 91.3 / 90.7, clothing 10 / 2 % = 78.3 / 78.1 | digits 93.65 / 91.6 / 91.1, clothing 79.7 / 77.5 (3 seeds) | small gain; at 10 % labels the gap to full labels is 0.5 (digits) and 1.1 (clothing); at 2 % clothing is 0.6 lower than without the gate |
| Novelty from inside (measurement, not yet a recruitment rule) | none | trained on 8 digits, the chip's own margin between its top two classes separates unseen from known digits with AUROC 0.88 (best score 0.84, score per active bit 0.85); 60 % of unseen examples flagged while keeping 90 % of known ones | the signal exists; building a new class slot on it is the next step |
| Learn only from view-consistent examples (every label present; run on the user's PC) | digits 94.1; clothing 80.8 | digits 94.9 (95.15 / 94.65 / 94.80); clothing 78.9 | digits: +0.8, every seed above the best baseline seed; needs both the gate and the 5 shifted views (gate alone 92.1, views alone 92.0). Clothing: no win (78.9 vs 80.8) |
| Memory (test 6, brain: synaptic pruning) | all synapses | zero the weakest slow-table synapses after the last night | digits 94.0 -> 93.5 with 19 % of synapses nonzero; clothing 80.35 -> 80.35 at 30 %, 79.6 at 21 %. The saving is ESTIMATED from the nonzero count (a sparse store also needs indices), 2 seeds |

## Failures (recorded, not adopted)

| Idea | What happened |
|---|---|
| Self-labelling over all known classes | 10 % labels 63-65, 25 % labels 73-78 on digits (precision of own labels 64-71 %). Fixed only by the context limit above |
| Rewards scattered through the stream instead of first | digits 10 / 5 / 2 % = 91.1 / 91.4 / 88.6, no better than rewards first |
| Unsupervised category layer + sparse naming (competitive Hebbian assemblies, novelty and error-driven recruitment, homeostasis) | 53-66 % on a small test, fills every slot; a penalty for missing expected bits made it worse (12-37 %). Not tuned further |
| Cascade synapses (metaplasticity, 3 extra bits per synapse) | clothing staged 80.8 -> 80.6 / 80.1 / 80.3, all at once 86.0 -> 85.3 / 84.5 / 84.1 |
| Dreams with lateral inhibition (at most K drawn features per spot) | staged worse, more so with stronger inhibition: clothing 80.8 -> 79.9 / 78.6 / 74.7, digits 94.1 -> 93.7 / 93.0 / 90.4 for K = 4 / 3 / 2; all at once level |
| Causal onset triggers (fixed loudness 800 / 1600, adaptive 3 x running average) instead of the shipped alignment | 20 words: threshold 800 clean 60.7, threshold 1600 clean 65.1, against 68.5 for the shipped alignment (equal at 5 dB, last-stage words 51.3 vs 50.6, first-stage words 71.4 vs 77.5); not adopted, adaptive variants running |

## Sound (20 words of the 35-word subset, 5 stages of 4 words, 414 test clips, so about +-3 points of noise)

| Arm | clean | 20 dB | 10 dB | 5 dB | first-stage words | last-stage words |
|---|---|---|---|---|---|---|
| shipped alignment (peak) | 68.5 | 62.2 | 47.3 | 33.3 | 77.5 | 50.6 |
| fixed-loudness onset 800 | 60.7 | 54.2 | 41.6 | 27.9 | 64.5 | 45.2 |
| fixed-loudness onset 1600 | 65.1 | 61.1 | 45.8 | 33.3 | 71.4 | 51.3 |
| adaptive onset (3 x running average + 400 / + 1200) | 57.4 / 62.4 | 55.2 / 55.3 | 42.7 / 45.0 | 30.0 / 32.1 | 63.2 / 67.5 | 41.0 / 38.3 |
| shipped alignment + look again (3 test windows, control) | 69.2 | 61.5 | 48.8 | 34.2 | 79.2 | 50.2 |
| fixed-loudness onset 1600 + look again | 66.3 | 61.7 | 47.8 | 36.2 | 74.5 | 50.2 |
| noisy night dreams, drop 1/8 of bits | 70.5 | 62.6 | 47.9 | 35.9 | 75.3 | 51.0 |
| noisy night dreams, drop 1/4 | 68.8 | 62.3 | 48.6 | 35.8 | 75.3 | 51.0 |
| noisy night dreams, drop 1/8 + add len/16 random bits | 68.5 | 61.5 | 46.9 | 33.7 | 78.8 | 42.5 |

Reading (about +-3 points of noise on 414 clips): every causal onset trigger is below the shipped alignment, so the hand-made word alignment is NOT clearly fixed (the shipped rule needs the whole clip's loudest frame). Noisy night dreams that only drop bits are within noise
(clean +0.3 to +2.0, 5 dB +2.4 to +2.6) but first-stage words fall 2.2, which breaks the guard "old words must not get worse"; adding spurious bits hurts new words by 8. Not adopted. With the same look-again at test time (three windows), the onset trigger (1600) is near parity with the shipped alignment: 2.9 points lower clean (about the size of the test noise), 0.2 higher at 20 dB, 1.0 lower at 10 dB, 1.9 higher at 5 dB, 4.7 lower on first-stage words. Not a clear win and not a clear loss; it needs a larger speaker-disjoint test set to settle (`brain_strict_sound_la.log`, `brain_strict_sound_pla.log`).

## Sound, 35 words (717 test clips, about +-2 points), run on the user's PC

| Arm | clean | 20 dB | 10 dB | 5 dB | first-stage words | last-stage words |
|---|---|---|---|---|---|---|
| shipped alignment + look again | 64.2 | 55.3 | 37.5 | 25.2 | 71.2 | 44.9 |
| onset trigger 1600 + look again | 60.7 | 52.8 | 36.6 | 26.1 | 68.6 | 42.6 |

The causal onset trigger is about 3 points lower on clean speech; the 20-word near-parity (66.3 vs 69.2) does not hold on the larger test. The shipped rule stays and is described as an echoic buffer with retrospective attention (the chip holds the one-second window and attends to the loudest part).

New spoken words with time-shifted views (base 15 words, 3 draws, k = 1 / 2 / 5 recordings): new-word accuracy 24.4 / 39.3 / 51.2 (shipped embedding path) against 24.1 / 40.9 / 50.8 with three views per recording; no gain, old words 0.2-1.3 lower. Not adopted.

## Still open

Few labels on sound, novelty from inside (the chip noticing a new class itself), a context signal for fully mixed streams with no rewards at all (the tested one needs recent rewards), a temporal layer for twin words, neighbour-conditioned dreams (needs several times the dream memory), and the RTL for sleep pressure and context-limited self-labelling (both are host-level logic in these tests).

Related: [Results index](INDEX.md), [Brain principles audit](../../docs/brain_principles_audit.md), [Journal](../../docs/journal.md), [Project memory](../../docs/PROJECT_MEMORY.md)
