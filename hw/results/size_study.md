# Shrinking SPARK before fabrication: size vs accuracy (SIMULATED, trained, not RTL)

Identical settings: 1,500 training steps, 3-byte context, threshold spikes, 4-bit weights, evaluated on 3,000 held-out bytes.
These are shorter runs than the shipped model, so compare rows to each other, not to earlier numbers.
Evaluation noise is about +-1 point. "With memory" = network plus the recall memory (the fast store).

## Round 1: layer width only (embedding width fixed at 64)

| Neurons per layer | Weights at 4-bit | Network alone | Network + recall memory | Firing rate |
|---|---|---|---|---|
| 128 (current chip) | 76.0 KB | 47.1% | 67.0% | 35% |
| 64 | 48.0 KB | 42.9% | 65.8% | 39% |
| 32 | 35.5 KB | 37.0% | 64.7% | 42% |

Reading:
1. Shrinking the layers four-fold costs 10 points for the network alone but only **2.3 points with the recall memory**. The fast store absorbs most of what the smaller network loses, which is the fast-plus-slow-memory principle working.
2. The weight memory falls only 53%, because three 24 KB embedding tables stay fixed. Layer width is not the main size lever; embedding width is.
3. Firing rate rises as the network shrinks, so it gets denser, not sparser.

## Round 2: layer width and embedding width together (H = neurons per layer, D = embedding width)

Same settings as round 1. Weights at 4-bit (embeddings + layers + both heads). Not counted: recall tables and per-stream state.

| H / D | Weights | Network alone | Network + recall memory | Firing rate |
|---|---|---|---|---|
| 128 / 64 (current chip) | 76.0 KB | 47.0% | 67.0% | 35% |
| 64 / 64 | 48.0 KB | 42.9% | 65.8% | 39% |
| 32 / 64 | 35.5 KB | 37.0% | 64.7% | 42% |
| **64 / 32** | **33.0 KB** | 40.7% | **66.2%** | 40% |
| 32 / 32 | 22.0 KB | 36.9% | 64.6% | 45% |
| 32 / 16 | 15.2 KB | 33.1% | 63.8% | 49% |

Reading:
1. **64 / 32 is the sweet spot:** 43% of the weight memory for 0.8 points less than the current design with memory, inside the evaluation noise (about +-1 point).
2. **Halving the embedding width costs less than halving the layers:** 64/64 -> 64/32 saves 15 KB for a 0.4-point change; 128 -> 64 layers saves 28 KB for a 1.2-point change. Both are cheap with the recall memory present.
3. **The smallest tried, 32 / 16, is 15.2 KB, one fifth of today's weights, and still 63.8% with memory.** Without the memory it is 33%, so at that size the fast store does the heavy lifting.
4. **The network gets denser as it shrinks** (35% -> 49% firing), the opposite of the sparse brain-like regime. It is a cost to watch.

Caveats: these are trained-model results, not RTL. The golden model and RTL are built for 128 / 64, so using a smaller size needs them regenerated and re-verified. Accuracy here is next-byte accuracy on 3,000 bytes, not agreement with a GPU model.

## Agreement with the GPU stand-in model (golden model, 1,500-step weights, 6,000 test bytes, SIMULATED)

| H / D | Agree with GPU model | On copy-failure bytes | Mean agreeing run |
|---|---|---|---|
| 128 / 64 | 59.8% | 36.3% | 1.49 |
| 64 / 32 | 59.1% | 34.5% | 1.44 |
| 32 / 16 | 57.9% | 32.4% | 1.38 |

64 / 32 loses 0.7 points, about one standard error at this sample size. Reproduce with `eval_copyfail.py out_size_128 out_size_h64_d32@64,32`.

## Full 3,000-step runs, identical recipe (SIMULATED)

Both trained with `--steps 3000 --relax-steps 300 --sparsity 0.05 --ctx 3 --spike thr`. Next-byte accuracy on 3,000 bytes; GPU agreement on 8,000 bytes through the golden model.
Note: the 128 / 64 baseline here is retrained under this recipe, so it is not the shipped model (`out_qat_sp0.05`) and its numbers differ from it.

| Measure | 128 / 64 (76 KB) | 64 / 32 (33 KB) | Difference |
|---|---|---|---|
| Next-byte accuracy, network alone | 49.2% | 44.4% | -4.8 |
| Next-byte accuracy, network + recall memory | 67.5% | 66.2% | -1.4 |
| Agreement with GPU stand-in model | 59.7% | 58.6% | -1.1 |
| Agreement on copy-failure bytes | 37.4% | 34.4% | -3.0 |
| Mean agreeing run (bytes) | 1.48 | 1.42 | -0.06 |
| Firing rate | 34% | 38% | +4 |

Reading:
1. At full training the loss from halving both widths is **1.1-1.4 points with the recall memory**, a little larger than the 0.8 seen at 1,500 steps. At 8,000 bytes one standard error is about 0.55 points, and the two models see identical bytes, so the gap is probably real, but small.
2. **The loss is concentrated where copying fails** (-3.0 points): the smaller network is weaker exactly where the network has to contribute, while the recall memory covers the rest.
3. Trade: 57% less weight memory for about 1 point of agreement. Firing rises 4 points.
