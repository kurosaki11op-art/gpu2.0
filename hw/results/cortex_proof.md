# SPARK Cortex: first proof results (SIMULATED, bit-exact chip logic on CPU)

Brain core = sensory layer that learns its own feature detectors without labels (5x5 receptive fields,
winner-take-all, Hebbian counters) + cortex memory that counts which features fire for which class and decides
by adding table scores. No multiplies, no backprop, no gradients. Features were learned once, from images of
the first two classes only. Baseline: a standard neural network (784-256-10 MLP, backprop, Adam).
Scripts: `hw/brain/proof_suite.py`; raw numbers: `cortex_proof_mnist.json`, `cortex_proof_fashion.json`.

## T3 Learning in stages (5 stages of 2 new classes; old data never shown again)

Accuracy on all classes seen so far, after each stage.

| Stage | MNIST brain core | MNIST neural net | MNIST net + replay* | Fashion brain core | Fashion net | Fashion net + replay* |
|---|---|---|---|---|---|---|
| 1 | 99.8 | 99.9 | 99.9 | 96.1 | 98.6 | 98.6 |
| 2 | 98.6 | 48.2 | 56.2 | 87.8 | 48.4 | 48.2 |
| 3 | 98.4 | 31.0 | 57.8 | 82.2 | 33.3 | 60.9 |
| 4 | 97.3 | 24.7 | 62.8 | 72.3 | 25.5 | 35.6 |
| 5 | **95.6** | 19.5 | 51.6 | **74.6** | 20.0 | 40.1 |

\* replay keeps 20 stored images per old class and mixes them into each new stage (a standard fix).
The brain core stores no images. Its final accuracy is exactly what it gets when trained on everything at once:
learning only adds counts, so new learning never overwrites old learning.

## T4 Memory transfer between chips (merge by adding counts, no retraining)

| | MNIST brain | MNIST net | Fashion brain | Fashion net |
|---|---|---|---|---|
| Chip A alone / chip B alone (different halves of the data) | 95.6 / 95.5 | 97.0 / 97.0 | 74.7 / 74.3 | 84.4 / 86.6 |
| Merged (brain: add counts; net: average weights) | **95.64 = trained on all** | 92.5 | **74.62 = trained on all** | 76.3 |
| A knows classes 0-4, B knows 5-9, then merged | **95.6** | 82.8 | **74.6** | 62.0 |

## T1 Accuracy and cost

| | MNIST | Fashion | Memory | Work per decision |
|---|---|---|---|---|
| Brain core | 95.6 | 74.6 | 0.4 KB detectors + 45 KB class table (8-bit) | 18,432 25-bit match counts + ~600 small adds, 0 multiplies |
| Neural net | 97.7 | 87.5 | 199 KB (8-bit) | 203,264 multiply-adds |
| Brain core, 2 brightness levels + surprise-gated correction table (probe) | n/a | 83.6 | ~90 KB | same kind of operations |

## T2 Few-shot (1 / 5 / 20 examples per class): the brain core loses here

| | MNIST | Fashion |
|---|---|---|
| Neural net | 38.6 / 67.2 / 81.1 | 43.6 / 62.6 / 73.8 |
| Brain episodic recall (best stored match) | 37.3 / 56.8 / 72.1 | 39.6 / 54.1 / 63.5 |
| Brain counting memory | 16.8 / 34.5 / 77.4 | 37.7 / 52.7 / 65.5 |

## What this proves and what it does not

- Proven (simulated): a matrix-free, gradient-free core learns new classes in stages **without forgetting**, and two
  chips' memories **merge exactly**. Today's networks lose most old knowledge in the same test, even with replay.
- Not yet: plain accuracy is 2 points behind on digits and 9-13 points behind on clothing images. Few-shot is worse.
  The surprise-gated correction table closes most of the clothing gap but, as tested, it can forget; making it stable
  (consolidation during idle "sleep") is the first work item.
- Not measured: energy. Operation counts are ESTIMATED; board power comes after the RTL.
- Earlier variant (random wiring, no learned features, `cortex_core.py`): 96.1% MNIST but forgot like the network
  (15.9% on the first classes after 5 stages). Learned features + counting memory is what removed forgetting.

Related: [SPARK Cortex redesign](../../docs/cortex_redesign.md), [Brain code](../brain/README.md), [Results index](INDEX.md)
