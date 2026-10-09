# SPARK core v0 — simulation results (MEASURED in RTL simulation)

Input: 527 bytes of Python-like text with repeated passages. Demo weights (random, sparse int4), not trained L weights.
Every configuration is checked token-by-token against the bit-exact golden model (prediction, path and per-stage event counts).

| Configuration | Golden mismatches | Cycles/token | vs dense | Weight words read/token | vs dense | Events/token | Paths full / exit / recall |
|---|---|---|---|---|---|---|---|
| dense (GPU-style, every input) | 0 | 4347 | 1.0x fewer | 3584 | 1.0x fewer | 320.0 | 527 / 0 / 0 |
| event-driven (skip silent) | 0 | 779 | 5.6x fewer | 544 | 6.6x fewer | 56.0 | 527 / 0 / 0 |
| event-driven + change-only | 0 | 1172 | 3.7x fewer | 875 | 4.1x fewer | 86.9 | 527 / 0 / 0 |
| event-driven + early exit | 0 | 1477 | 2.9x fewer | 1119 | 3.2x fewer | 91.9 | 527 / 0 / 0 |
| event-driven + recall | 0 | 514 | 8.5x fewer | 351 | 10.2x fewer | 36.5 | 367 / 0 / 160 |
| event-driven + energy cap 16 | 0 | 469 | 9.3x fewer | 287 | 12.5x fewer | 29.9 | 527 / 0 / 0 |
| all think-less (change-only + exit + recall) | 0 | 1486 | 2.9x fewer | 1169 | 3.1x fewer | 95.8 | 367 / 0 / 160 |
