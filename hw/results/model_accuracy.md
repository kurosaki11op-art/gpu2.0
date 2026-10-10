# SPARK model accuracy — from 41% to 74% (MEASURED)

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

## Recall effort dial — "think less when you can, think hard when you need to" (golden model, 2,000 held-out bytes)
On a recall hit the chip can trust memory at three effort levels. Implemented in the golden model **and** the RTL;
RTL verified bit-exact (0 mismatches, 5 configurations × 300 tokens); board UART testbench still passes.
`arb_th` (effort 2) was chosen on the calibration split (128), never on the test split.

| Effort on a recall hit | sparsity 0 | sparsity 0.05 | Work, events/token (sp0 / sp0.05) |
|---|---|---|---|
| Low (0): answer from memory, skip the network | 69.2% | 68.1% | 87 / 59 |
| Medium (1): answer from memory, update neurons (fresh state) | 71.6% | 70.5% | 198 / 147 |
| High (2): also run the main head; network overrides memory when confident | **73.8%** | **72.6%** | 237 / 172 |

Dense processing ≈ 448 events/token. All settings use the adaptive controller (change-only vs full recompute, adaptive early exit).

## Longer, harder test (20,000 bytes) — honest check
The 2,000-byte test happens to be an easier stretch. On 20,000 held-out bytes (fast exact simulator, 0 mismatches vs golden):

| | sparsity 0 | sparsity 0.05 |
|---|---|---|
| Network alone | 59.5% | 56.6% |
| Chip today: one recall memory, effort 2 (arb_th 64) | 66.6% | 65.3% |
| **Prototype: four memories (2/3/4/6-byte context) that "prime" the network** | **68.3%** | **67.4%** |

Memory priming = every memory that recognises the context adds a confidence-weighted boost to its byte's score
(memory biases perception) instead of an either/or switch. Settings tuned on the calibration split only. Needs
4 × 1,024 recall slots (≈ 3 more block RAMs with 16-bit tags) — not yet in RTL.

## On-chip learning — what we tried (20,000-byte calibration stream, sparsity-0.05 model, network alone 49.2%)
| Brain-like learning rule | Accuracy | Verdict |
|---|---|---|
| Error-driven plasticity on the int4 output weights (pre-spike × error) | 41–49% | Hurts: int4 steps are too coarse, overwrites what was learned |
| Intrinsic plasticity (per-output bias) | 33–48% | Hurts |
| Fast synapses beside fixed slow weights, with forgetting | 46–49.7% | No real gain |
| Learned memory-vs-network arbiter (counters per confidence bucket) | +0.1 to +0.7 points over a fixed threshold | Small gain |
| **One-shot memory (the recall unit) + priming** | **+19 points over the network alone** | **Works** |

Finding: on this chip the learning that pays off is the brain's *fast one-shot memory* (hippocampus-like recall
table, written every token) plus a slow, fixed network — the "complementary learning systems" split. Online weight
updates chase unpredictable bytes. Scripts: `hw/train/experiments/`.

## Other ideas tested to raise accuracy (3,000-byte eval, sparsity 0; network alone / with 4-memory priming)
| Idea (brain analogy) | Network alone | With memory | Verdict |
|---|---|---|---|
| Baseline (same recipe, retrained) | 62.4% | 72.8% | — |
| Memory-aware training (cortex learns what hippocampus misses) | 41.6% | 72.1% | No gain (20,000-byte: 67.7% vs 68.4%) |
| Word-chunk inputs: current word (reading in chunks) | 61.7% | 73.3% | +0.5, within noise |
| Word-chunk inputs: current + previous word | 61.4% | 73.3% | +0.5, within noise |
| Recurrent layer 1 (cortical recurrence) | 61.1% | 72.6% | No gain |
| Adding exit-head scores to the main head | +0.3 | ±0.2 | No gain |
| Bigger memory: 2,048 × 4 / 4,096 × 6 slots (20,000-byte test) | — | 68.8% / 69.4% (vs 68.4%) | **Works, scales with SRAM** (needs a bigger FPGA/ASIC) |

Conclusion: at this size (128 neurons/layer, int4) the network saturates at ~62%; accuracy gains come from
memory (more slots, more context lengths, priming), which is cheap SRAM rather than compute.

## Bigger network? (exact-integer, 3-byte context, 3,000-byte eval)
| Neurons per layer | Main-path accuracy |
|---|---|
| 128 | 62.3% |
| 192 | 62.4% |
| 256 | 63.0% |

Doubling the network barely helps; memory and how it is combined with the network matter far more.

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
