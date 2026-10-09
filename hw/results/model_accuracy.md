# SPARK model accuracy — from 41% to 66% (MEASURED)

Task: predict the next byte of Python source code (held-out files from the local CPython standard library; 2.7 MB training text). All "chip" models use the exact integer rules of the SPARK core and are verified bit-exact (0 mismatches) between PyTorch and the golden reference model; the RTL is verified bit-exact against the golden model.

## Baselines on the same held-out text
| Predictor | Next-byte accuracy |
|---|---|
| Always predict the most common byte (space) | 36.2% |
| 1-byte lookup (bigram) | 42.9% |
| 2-byte lookup (trigram) | 63.8% |
| 4-byte lookup | 64.9% (best lookup) |
| Plain float neural network (3-byte context, 128 hidden, no spikes, no integer rules) | 61.9% |

## What was wrong and what fixed it
| Step | Change | Accuracy | Finding |
|---|---|---|---|
| 1 | First model: 1 byte in, symmetric spikes, 500 steps | 40.0% (44.2% with recall) | Barely above "always predict a space" |
| 2 | Train 6× longer | 41.4% | Not undertrained |
| 3 | 3-byte context window | 45.2% | Helps a little |
| 4 | Relaxed (no-rounding) training | ~40% | Integer rules are **not** the bottleneck |
| 5 | Threshold (one-sided) spikes, L-like 8–11% firing | 37–41% | Not the main cause either |
| 6 | Plain float network on the same data | 61.9% | The data and the context are fine → the bug is in our training setup |
| 7 | Learning rate matched to integer-unit weights + sparsity penalty removed | **61.9%** (relaxed) | **Root cause: the sparsity penalty was far too strong and the learning rate ~30× too small** |
| 8 | Exact-integer models (relaxed pre-training, then integer QAT) — sparsity sweep | see below | Accuracy vs. firing trade-off |

## Exact-integer models (chip-runnable), 3-byte context, threshold spikes
| Sparsity penalty | Neurons firing | Main path | Full system: recall + adaptive controller | Work (events/token) |
|---|---|---|---|---|
| 0 | 55% | 63.9% | **66.9%** | 163 |
| 0.05 | 26% | 59.9% | **66.0%** | **111** |
| 0.2 | 16% | 51.5% (3,000-byte eval) | — | — |
| 0.5 | 12% | 47.6% (3,000-byte eval) | — | — |

The full system (2,000 held-out bytes) beats the best lookup table (64.9%) and the plain float network (61.9%), because the recall unit copies repeated code exactly. Dense processing of this model would be ~448 events per token; the sparsity-0.05 system does ~111 (≈4× less work) at 66.0%.

## Recall unit v2 (3-byte context, multiplicative hash, confidence ≥ 0) — same 1,024-slot table
Analysis showed the recall table was losing accuracy to hash collisions and an over-long context. Changing the hash and the context length costs no extra memory.

| Model | Full system before (recall v1) | Full system after (recall v2) | Work (events/token) | Recall answers |
|---|---|---|---|---|
| sparsity 0 | 66.9% | **69.2%** | 87 (≈5.2× less than dense ~448) | 68% of bytes |
| sparsity 0.05 | 66.0% | **68.1%** | **59 (≈7.6× less than dense)** | 68% of bytes |

RTL updated and verified bit-exact (0 mismatches); board UART testbench passes (40 tokens, 5 configurations).

## What did NOT help (network alone, exact-integer, 3,000-byte eval)
| Change | Main-path accuracy |
|---|---|
| 3-byte context, longer training (5,000 steps, batch 64) | 62.3% |
| 4-byte context (shared embedding) | 62.0% |
| 6-byte context (shared embedding) | 61.8% |
| 6-byte context + light sparsity (30% firing) | 61.4% |

The network itself plateaus at ~62–64% at this size (128 neurons per layer, int4); further gains need more capacity or memory.

## Honest limits
- Small model (~130 KB of int4 weights), byte-level, one domain (Python code). Larger models and other text are untested.
- There is a real accuracy–sparsity trade-off: fewer firing neurons cost accuracy (table above).
- Accuracy on short samples varies (e.g. first 300 bytes: 53–60%); quote the 2,000-byte figures.
