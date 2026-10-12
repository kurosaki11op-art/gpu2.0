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

## 5. Non-code text (public-domain prose), the test that decides whether the network earns its place (SIMULATED)

Data: four 20,000-byte slices at 40% of each book (NLTK Gutenberg set: Alice in Wonderland, Moby Dick, Hamlet, Emma). All memories start empty at the slice start.
The SPARK network was trained on code only, so this is out-of-domain for it. Scripts: `hw/system/nontext_probe.py`; the size-matched check is in `hw/results/nontext_lookup_size.json`.
Metric: accuracy vs the true next byte. A "predict a space" baseline scores 16.8%.

| Predictor | Memory | Alice | Moby Dick | Hamlet | Emma | Mean |
|---|---|---|---|---|---|---|
| Matrix-free lookup, 2^11 entries | 27.5 KB | 39.9% | 32.1% | 32.7% | 34.4% | 34.8% |
| Matrix-free lookup, 2^12 entries | 55 KB | 45.4% | 36.7% | 37.1% | 39.8% | 39.7% |
| Matrix-free lookup, 2^13 entries | 110 KB | 48.1% | 39.8% | 40.0% | 43.2% | 42.8% |
| Matrix-free lookup, 2^14 entries | 220 KB | 49.8% | 42.0% | 42.2% | 45.8% | 45.0% |
| SPARK full (network + recall, replace rule) | about 120 KB | 47.3% | 39.2% | 39.9% | 43.3% | 42.4% |
| SPARK full, hysteresis recall update | about 120 KB | 49.1% | 41.1% | 41.7% | 45.0% | 44.2% |

(SPARK memory = 76 KB network weights + about 44 KB recall tables.)

Reading:
1. **On prose the network does help:** the 55 KB lookup is 2.7 points behind SPARK full and 4.5 behind SPARK with the hysteresis update, even though the network never saw prose. The earlier "network adds nothing" conclusion was specific to code.
2. **But memory-matched, the gap closes.** A 110 KB lookup scores 42.8%, equal to SPARK full (42.4%) at about the same memory; SPARK with hysteresis keeps a 1.4-point edge. A 220 KB lookup beats both. So on this test, spending the memory on bigger tables is about as good as spending it on network weights.
3. **Honest verdict:** not a clear win for either. The network earns a small edge only with the better recall rule, and we have not tried a network trained on prose.
4. Caveats: old-English books, 20,000 bytes each, one start (empty) condition, byte-level accuracy not token-level, no real-model comparison.

## 6. Networks retrained on prose (SIMULATED)

Trained on 4.3 MB of other public-domain books (Persuasion, Sense and Sensibility, three Chesterton books, Parents' Assistant, Bryant stories, Buster Brown, Julius Caesar, Macbeth, Paradise Lost, shuffled in 200 KB chunks); none of the four test books is in the training set (Emma shares an author with two training books, so style leakage is possible).
Same recipe as the code-trained 128/64 (3,000 steps). Evaluated on the same four 20,000-byte slices with the golden model. `nontext_models.py`, `nontext_models.json`.

| Network | Weights | Recall rule | Mean accuracy on prose |
|---|---|---|---|
| Trained on code, 128 / 64 | 76 KB | replace | 42.4% |
| Trained on code, 128 / 64 | 76 KB | hysteresis | 44.2% |
| **Trained on prose**, 128 / 64 | 76 KB | replace | 42.9% |
| **Trained on prose**, 128 / 64 | 76 KB | hysteresis | 44.7% |
| **Trained on prose**, 64 / 32 | 33 KB | replace | 42.8% |
| **Trained on prose**, 64 / 32 | 33 KB | hysteresis | 44.6% |

Every SPARK row also includes the 44 KB of recall tables.

Reading:
1. **Training on prose adds almost nothing** (+0.5 points over the code-trained network). The network's value on prose is mostly domain-general, not domain-specific.
2. **The 33 KB network matches the 76 KB one** on prose (44.6% vs 44.7%), as it did on code. The smaller design is the right one.
3. **Does the network earn its memory?** SPARK 64/32 totals about 77 KB (33 KB network + 44 KB tables) and scores 44.6%. A lookup-only design at the same memory is not directly measured; interpolating between 55 KB (39.7%) and 110 KB (42.8%) gives about 41%. So on prose the network adds roughly **3 points at matched memory** (an interpolation, not a measurement). The advantage shrinks as memory grows: the 220 KB lookup (45.0%) beats it.
4. **On code the network added nothing** (section 1). Summary: the network is worth a few points on prose at small memory, nothing on repetitive code.

Caveats: byte-level accuracy; old-English prose; 20,000-byte slices; interpolated comparator; no real-model drafting test on prose.
