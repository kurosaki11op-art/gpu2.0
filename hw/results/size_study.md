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
