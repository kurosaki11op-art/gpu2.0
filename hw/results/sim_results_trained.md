# SPARK core v0 — simulation results (MEASURED in RTL simulation)

Input: 600 bytes (hw/train/out_sparse/sample_eval.txt). Weights: hw/train/out_sparse/spark_v0_model.npz.
Every configuration is checked token-by-token against the bit-exact golden model (prediction, path and per-stage event counts).

| Configuration | Golden mismatches | Cycles/token | vs dense | Weight words read/token | vs dense | Events/token | Paths full / exit / recall | Next-byte accuracy |
|---|---|---|---|---|---|---|---|---|
| dense (GPU-style, every input) | 0 | 8296 | 1.0x fewer | 7168 | 1.0x fewer | 320.0 | 600 / 0 / 0 | 36.7% |
| event-driven (skip silent) | 0 | 3276 | 2.5x fewer | 2542 | 2.8x fewer | 123.4 | 600 / 0 / 0 | 36.7% |
| event-driven + change-only | 0 | 4712 | 1.8x fewer | 3876 | 1.8x fewer | 174.1 | 600 / 0 / 0 | 36.7% |
| event-driven + early exit | 0 | 2484 | 3.3x fewer | 1958 | 3.7x fewer | 88.8 | 10 / 590 / 0 | 38.1% |
| event-driven + recall | 0 | 2435 | 3.4x fewer | 1876 | 3.8x fewer | 91.5 | 457 / 0 / 143 | 42.6% |
| event-driven + energy cap 16 | 0 | 936 | 8.9x fewer | 402 | 17.8x fewer | 23.4 | 600 / 0 / 0 | 9.3% |
| all think-less, always on (change-only + exit + recall) | 0 | 2574 | 3.2x fewer | 2130 | 3.4x fewer | 86.1 | 11 / 446 / 143 | 44.2% |
| ADAPTIVE controller (recall + chooses change-only/full + adaptive exit) | 0 | 1845 | 4.5x fewer | 1380 | 5.2x fewer | 61.6 | 11 / 446 / 143 | 44.2% |
| ADAPTIVE controller, exit always succeeds (stress test) | 0 | 1811 | 4.6x fewer | 1357 | 5.3x fewer | 60.6 | 0 / 457 / 143 | 43.9% |
