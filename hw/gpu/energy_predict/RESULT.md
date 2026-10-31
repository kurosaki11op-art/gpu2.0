---
title: Test G1 result so far - the predictor failed on a different GPU (0 of 9 points), batching saves 8x or more energy (31 Oct 2026, MEASURED)
tags: [spark, gpu, wedge, energy, result, vision-research]
---

# Test G1 result so far (31 Oct 2026)

**MEASURED** on two machines (board power from `nvidia-smi`, one run per point, same script, same three models, half precision): the founder's RTX 3050 6 GB laptop (reference; [results](results_3050/)) and a free Colab Tesla T4 ([results](results_colabT4/)). Protocol and bars: [PROTOCOL](PROTOCOL.md). Friends' machines are not in yet; the 4060 is still to come.

## The pre-registered test: rule v2 on a different GPU

Rule v2 was fitted on the reference runs and committed ([fit2.json](results_3050/fit2.json)); its predictions for the T4 were committed from the T4's info file alone, before the T4 model runs were compared (the files arrived together; the comparison was made after the commit). Result ([table](results_colabT4/comparison.txt)):

- **G1-speed: 0 of 9 points within 20%** (bar 7 of 9). The T4 was predicted 2 to 4 times faster than measured (errors +121% to +289%).
- **G1-energy: 0 of 9 points within 20%** (errors -53% to -76%: predicted energy far too low because the predicted speed was too high).
- **Kill rule of the protocol:** "if the speed or energy prediction fails on most target GPUs, withdraw the planner idea as stated". One different GPU has been measured and it failed on every point, so the rule as stated is **withdrawn as a predictor**. The 4060 result will still be recorded when it arrives.

## Why it failed (what the data shows)

- Time per layer (milliseconds), by model and batch 1/4/16: 3050 laptop: 1.11/0.78/1.05 (small), 1.19/1.16/1.09 (medium), 1.04/1.20/1.69 (large). T4: 0.99/1.06/1.04, 1.54/1.53/1.69, 1.55/1.88/2.77. The T4 has a **lower** launch cost per tiny operation (about 9 microseconds against 27 on the laptop) yet runs the two larger models **slower per layer**. So a tiny-kernel launch benchmark does not predict decode speed: the real per-layer time includes Python and library overhead on that machine's CPU, which differs per model and per machine by factors that no single scale number captured (ratio T4 to laptop 0.9, 1.3, 1.5 for the three models).
- Decode of small models on this stack is **software and CPU bound**, not memory bound, on both machines. Neither hardware spec (bandwidth, matrix rate) nor a micro-benchmark predicted it.

## What the measurements do show

| model | machine | batch 1 J per token | batch 16 J per token | saving | batch 1 tokens/s per user | batch 16 |
|---|---|---|---|---|---|---|
| 0.5B-class | 3050 laptop | 0.756 | 0.055 | 14x | 35.1 | 38.1 |
| 0.5B-class | T4 | 1.622 | 0.163 | 10x | 27.1 | 24.7 |
| 1.1B-class | 3050 laptop | 0.792 | 0.096 | 8x | 43.6 | 26.8 |
| 1.1B-class | T4 | 2.111 | 0.246 | 8.6x | 29.4 | 16.4 |

- **Batching saves 8 to 14 times the energy per token on both machines**, at the cost of 20% to 45% of each user's speed (batch 16 against batch 1 for the larger models).
- **The datacentre-class T4 is slower and less efficient than the gaming laptop on these small models** (2 to 3 times the joules per token at batch 1), because it idles at 33 to 37 W and draws 44 to 65 W while decoding at lower speed. It also shows that board power at idle matters: gross energy at batch 1 is mostly idle power.
- This is evidence for a **measurement tool** (cheap, 5 minutes per model) not for a predictor: the number a GPU owner needs is cheap to measure and not cheap to predict.

## Limits

One run per point; two machines only; the T4 is a shared cloud machine whose CPU and load vary; board power is not wall power; one decode implementation; half precision; small models only. No claim about large models, where decode is more likely memory bound.

Related: [Protocol](PROTOCOL.md), [Guide](README.md), [Research 01 summary](../../../docs/reviews/research_01_summary.md), [Hardware index](../../HARDWARE_INDEX.md)
