# Matrix-free SPARK: a predictor with no matrices and no multipliers (SIMULATED)

> **Second correction (see section 8):** a paired analysis shows the network's contribution is small but real (+0.6 points pooled, +1.2 when the network arbitrates), not "a few tenths". Section 7's "adds at most a few tenths" is superseded.
>
> **Correction (see section 7).** Sections 1, 2, 5 and 6 compared SPARK against a lookup design that used a weak XOR hash (tables answered only ~87% of prose bytes vs ~96% for a good hash).
> That understated the lookup design by about 4 points on prose and produced a false "the network adds ~3 points" reading. With a good multiplier-free hash (CRC-32 or tabulation), the lookup design matches the hybrid on both code and prose.

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

## 7. Corrected comparison: multiplier-free hash (CRC-32), lookup design vs the hybrid (SIMULATED)

`hw/system/hash_study.py` and `crc_sweep.py`; data in `hash_study.json`, `crc_sweep.json`, `hash_ablation_prose.json`, `hybrid_eval.json`.

Hash study (orders 2,3,4,6; 2^12 entries; hysteresis counters), code accuracy / prose mean accuracy:
multiplicative 75.0% / 44.1%; XOR-fold 73.4% / 39.7%; tabulation (XOR of ROM words) 75.1% / 43.6%; **CRC-32 75.4% / 43.9%**. Table coverage on prose: 96% (multiplicative), 82-87% (XOR-fold), 95-96% (tabulation, CRC).

Size sweep with CRC-32 (entry = 22 bits):

| Orders | Entries per table | Memory | Code | Prose (4-book mean) |
|---|---|---|---|---|
| 2,4 | 1024 | 5.5 KB | 69.8% | 36.5% |
| 2,4 | 4096 | 22.0 KB | 73.1% | 41.4% |
| 2,3,4,6 | 1024 | 11.0 KB | 73.6% | 39.2% |
| 2,3,4,6 | 2048 | 22.0 KB | 74.9% | 42.0% |
| 2,3,4,6 | 4096 | 44.0 KB | 75.4% | 43.9% |
| 1,2,3,4,6 | 2048 | 27.5 KB | 75.3% | 42.2% |
| 1,2,3,4,6 | 4096 | 55.0 KB | 75.8% | 44.0% |

Hybrid (recall tables 44 KB + 64/32 network 25-33 KB), hysteresis recall, exit off: code 75.6% (agreement with the GPU stand-in 61.7%), prose 44.2%. With a binary main head: 75.4% / 44.3%. Networks trained on prose: 75.1-75.2% / 44.5%.

Reading:
1. **The network adds at most a few tenths of a point** in the hybrid on both code and prose, regardless of head format or training domain. In this configuration the tables answer about 95% of bytes.
2. **A 44 KB multiplier-free lookup design matches the hybrid** (75.4% vs 75.6% on code, 43.9% vs 44.2% on prose) at about 57% of its memory.
3. **27.5 KB** (orders 1,2,3,4,6; 2048 entries) keeps code within 0.3 points and loses about 2 points on prose.
4. This is simulated byte-level accuracy on 20,000-byte slices (code from one corpus, four old-English books). It has not been checked on real-model drafting, novel domains, or token-level accuracy.

## 8. Paired analysis after the outside critique (SIMULATED)

`hw/system/paired_stats.py`, `hw/results/paired_stats.json`. Same positions for both predictors; per-byte correctness; documents: 20,000 bytes of code and four 20,000-byte book slices; the hybrid is the 64/32 network (code-trained for code, prose-trained for prose) with the hysteresis table update and the exit head off.
Mode 0: a table hit answers directly (the network decides only on table misses). Mode 2: the network arbitrates (it overrides a table hit when its main-head margin is at least the arbitration threshold) and runs on every byte.

Accuracy difference, hybrid minus lookup-only (points):

| Document | Mode 0 | Mode 2 | Bytes the network decides (mode 0) | Network accuracy there | Lookup accuracy on the same bytes |
|---|---|---|---|---|---|
| Code | +0.22 | -0.04 | 5.1% | 22.6% | 13.5% |
| Alice | +0.52 | +1.15 | 4.3% | 27.1% | 19.2% |
| Moby Dick | +0.35 | +1.30 | 3.9% | 30.2% | 17.8% |
| Hamlet | +1.17 | +1.80 | 4.3% | 26.9% | 15.9% |
| Emma | +0.74 | +1.85 | 4.0% | 27.7% | 18.9% |
| **Pooled (100k bytes)** | **+0.60, 95% CI [+0.40, +0.79]** | **+1.21, 95% CI [+0.97, +1.47]** | | | |

Confidence intervals are from a block bootstrap (250-byte blocks) and only capture within-document variation. With five documents, document-to-document variation is not captured, so the true uncertainty is wider.

Reading:
1. **The network's contribution is real but small.** About +0.6 points when it only handles table misses, +1.2 when it arbitrates. It helps most on prose (up to +1.9) and is about zero on repetitive code. My earlier statements ("a few tenths", "adds almost nothing") understated this.
2. **Where it helps:** on the 4-5% of bytes where no table answers, the network is right 23-30% of the time against 13-19% for the lookup fallback. That is its main contribution in mode 0.
3. **Cost of the extra point:** mode 2 runs the network on every byte (about 2,000+ cycles per byte instead of about 5, from earlier measurements), so the extra +0.6 over mode 0 costs about two orders of magnitude more time.
4. **Equivalence:** against a one-point worthwhile margin, lookup-only is within the margin in mode 0 (the upper bound is +0.79) and not in mode 2 (+1.47). A worthwhile margin for the real goal (drafting speed or energy) has not been defined or measured.
5. This is still byte-level next-byte accuracy, which is not agreement with a target model's tokens.
