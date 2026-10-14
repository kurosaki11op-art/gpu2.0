# SPARK Cortex month 1: closing the accuracy gap (SIMULATED)

Goal set in `docs/cortex_redesign.md`: within 3 points of a standard neural network on 3 datasets, still no
forgetting. Script: `hw/brain/proof_suite_v2.py`; raw numbers `cortex_v2_mnist.json`, `cortex_v2_fashion.json`,
`cortex_v2_speech_res_L8.json`. Neural network = 784-256-10 MLP with backprop (for sound also on standard FFT
log-mel features, which our chip does not use).

## What changed since the first proof (all brain principles, still no multiplies, no backprop)

| Change | Brain principle | Effect |
|---|---|---|
| Retina centre-surround cells (on/off: brighter/darker than neighbours) beside 2 brightness levels | retina ganglion cells | clothing, fast table 82.0 -> 85.8 |
| Concept cells: 32 prototype neurons per class, each learns only inside its own class by counting | concept cells, competition | stable memory, clothing 79.7 -> 83.5; still cannot forget |
| Sleep: concept cells dream old classes, the fast table practises on new examples + dreams | hippocampal replay in sleep | fast table after 5 stages: 33.2 (no sleep) -> 77.9 / 85.9 (sleep) |
| Cochlea: shift-add resonators with hearing-shaped bandwidths instead of one-pole filters | basilar membrane resonance | network reading our sound pictures 54.7 -> 73.1 (vs 76.2 on FFT log-mel) |
| 8 loudness levels for sound | hair cells with staggered thresholds | spoken words, fast table 66.5 -> 76.1 |

## Results

All data at once (accuracy %):

| | Digits (MNIST) | Clothing (Fashion-MNIST) | Spoken words (10 commands) |
|---|---|---|---|
| Neural network | 97.7 | 87.4 | 75.5 (on our sound pictures) / 76.2 (on FFT log-mel) |
| Brain: concept cells | 97.2 | 83.5 | 61.1 |
| Brain: fast table | 97.6 | 85.8 | **76.1** |
| Brain: combined decision (concept top-2, table picks) | **97.9** | 86.2 | 69.7 |

Learning in 5 stages, two new classes per stage, old data never shown again (accuracy on all classes, end):

| | Digits | Clothing | Spoken words |
|---|---|---|---|
| Neural network, fine-tuned per stage | 19.5 | 20.0 | 15.9 / 18.8 |
| Neural network + replay of 20 stored examples per old class | 49.6 | 37.8 | 16.0 / 27.8 |
| Brain: concept cells | **97.2** | 83.5 | 61.1 |
| Brain: fast table with sleep | 95.0 | 85.9 | **71.8** |
| Brain: combined | 95.9 | **86.3** | 68.7 |

The brain stores no examples; the replay baseline does.

Memory transfer: chip A learns classes 0-4, chip B learns 5-9, then they merge (concept cells pooled, one sleep to
rebuild the fast table). Neural-network weight averaging on the same split: 82.8 (digits), 62.0 (clothing) in the
first proof.

| | Digits | Clothing | Spoken words |
|---|---|---|---|
| Chip A alone / chip B alone | 51.2 / 47.8 | 45.0 / 47.8 | 40.9 / 40.6 |
| Merged | 97.2 (concept) / 94.6 (after sleep) | 84.6 | 66.2 |

## Against the month-1 goal

- Met on all three datasets for the best brain component trained all at once: digits +0.2, clothing -1.6,
  spoken words +0.6 vs the network on the same input (-0.1 vs FFT log-mel).
- Met for learning in stages: the brain loses 0.5-4.3 points versus learning everything at once; the network
  loses 48-60 points.
- Not met: one fixed decision rule for all three. The combined rule is best on clothing but costs 1.3 points on
  digits and 7.1 on spoken words, where concept cells are weak (61%). Fix in month 2: let the fast table decide unless
  the concept cells are confident, and stronger concept cells for sound.

## Honest limits

1. **Memory is far too big for a chip right now.** Concept-cell counters: 11.5 MB (images) and 28 MB (sound) at 16 bits;
   the fast table is 180-450 KB. Month 2 must cut this by about 100x (fewer, smaller counters; 4-bit stochastic counters,
   which synapses also use).
2. Few-shot was not re-run in v2; it was the brain's losing test in the first proof.
3. The fast table on its own forgets without sleep (33% after 5 stages); sleep needs about 6,000 dreams per old class.
   Sleep time and energy are not yet counted.
4. Numbers are from one seed each. Differences under ~0.5 points should be treated as ties.
5. The simulator uses floating point and matrix products to *add* table values quickly; the chip logic is counting,
   comparing and adding. Bit-exact integer RTL is month 3.

Related: [SPARK Cortex redesign](../../docs/cortex_redesign.md), [Brain code](../brain/README.md), [Results index](INDEX.md)
