# Matrix-free SPARK: a predictor with no matrices and no multipliers (SIMULATED)

Scripts: `hw/system/matrix_free_probe.py`, `hw/system/matrix_free_sweep.py`. Data: 20,000 held-out bytes of code (the same slice used for all earlier agreement numbers).
Design: multi-order hashed tables (entry = 12-bit tag + 8-bit value + 2-bit count), highest-order hit answers, fallback is a space.
Learning: one pass, online, local: a hit that agrees raises the count, a miss lowers it, and the value is replaced only at count 0. No gradients, no weights, no matrices.
Operations: XOR, shifts, compares, small counters, table reads and writes. The hash in the sweep is XOR/shift only (no multiply), so the design is literally multiplier-free.

## 1. Against the full SPARK v2 (network + recall), same bytes

| Predictor | Accuracy vs true next byte | Agreement with GPU stand-in |
|---|---|---|
| Matrix-free lookup, multiplicative hash (probe) | 75.5% | 61.6% |
| **Matrix-free lookup, XOR/shift hash (sweep, 55 KB)** | **73.6%** | **59.8%** |
| SPARK v2 full (network + recall, cached) | 73.9% | 59.8% |
| GPU stand-in model (4.8M parameters) | 68.6% | n/a |

The multiplier-free lookup design matches the full SPARK on this slice. The stand-in model is itself below the lookup (68.6%), which says this slice rewards repetition, not language understanding.

## 2. Size sweep (XOR/shift hash)

| Orders | Entries per table | Memory | Accuracy | Agreement with GPU |
|---|---|---|---|---|
| 1,2,3,4,6 | 4096 | 55.0 KB | 73.6% | 59.8% |
| 1,2,3,4,6 | 2048 | 27.5 KB | 71.8% | 58.3% |
| 1,2,3,4,6 | 1024 | 13.8 KB | 69.7% | 56.8% |
| 2,3,4,6 | 4096 | 44.0 KB | 73.4% | 59.6% |
| 1,2,4 | 4096 | 33.0 KB | 70.4% | 58.1% |
| 2,4 | 4096 | 22.0 KB | 70.2% | 57.8% |
| 2,4 | 1024 | 5.5 KB | 63.9% | 53.2% |

For scale: the original chip is 76 KB of weights plus about 44 KB of recall tables (about 120 KB); the 64/32 network design is 33 KB plus the same tables (about 77 KB).

## 3. Learning curve of the local learner (accuracy vs bytes seen)

1,000 bytes: 49.9% | 2,000: 58.6% | 5,000: 66.8% | 10,000: 71.4% | 20,000: 75.5%.
One pass, in place, no optimizer state, no gradient transfer.

## 4. What this does and does not show

- It shows that **for this byte-level code prediction task, the matrices are not what carries the accuracy**. A lookup-and-counter design does as well, learns online in one pass, and is smaller.
- It does NOT show that language modelling in general can be done without matrices. This slice is repetitive code; a real LLM answers questions the tables cannot. The real-model drafting results point the same way (copy lookup 2.16 vs SPARK 1.70 tokens per big-model pass on the 3B model), but all of it is code.
- Not shown: any benefit on novel text, the RTL cost, board fit, or power.
