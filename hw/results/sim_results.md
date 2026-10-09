# SPARK core v0 — simulation results (MEASURED in RTL simulation)

Input: 527 bytes (built-in Python-like text with repeated passages). Weights: random sparse int4 demo weights (not trained).
Every configuration is checked token-by-token against the bit-exact golden model (prediction, path and per-stage event counts).

| Configuration | Golden mismatches | Cycles/token | vs dense | Weight words read/token | vs dense | Events/token | Paths full / exit / recall | Next-byte accuracy |
|---|---|---|---|---|---|---|---|---|
| dense (GPU-style, every input) | 0 | 4536 | 1.0x fewer | 3584 | 1.0x fewer | 320.0 | 527 / 0 / 0 | 0.6% |
| event-driven (skip silent) | 0 | 968 | 4.7x fewer | 544 | 6.6x fewer | 56.0 | 527 / 0 / 0 | 0.6% |
| event-driven + change-only | 0 | 1361 | 3.3x fewer | 875 | 4.1x fewer | 86.9 | 527 / 0 / 0 | 0.6% |
| event-driven + early exit | 0 | 1761 | 2.6x fewer | 1119 | 3.2x fewer | 91.9 | 527 / 0 / 0 | 0.6% |
| event-driven + recall | 0 | 646 | 7.0x fewer | 351 | 10.2x fewer | 36.5 | 367 / 0 / 160 | 29.3% |
| event-driven + energy cap 16 | 0 | 658 | 6.9x fewer | 287 | 12.5x fewer | 29.9 | 527 / 0 / 0 | 0.4% |
| all think-less, always on (change-only + exit + recall) | 0 | 1684 | 2.7x fewer | 1169 | 3.1x fewer | 95.8 | 367 / 0 / 160 | 29.3% |
| ADAPTIVE controller (recall + chooses change-only/full + adaptive exit) | 0 | 725 | 6.3x fewer | 371 | 9.7x fewer | 37.3 | 367 / 0 / 160 | 29.3% |
| ADAPTIVE controller, exit always succeeds (stress test) | 0 | 658 | 6.9x fewer | 411 | 8.7x fewer | 28.2 | 0 / 367 / 160 | 28.9% |
