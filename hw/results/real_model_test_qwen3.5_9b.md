# SPARK beside a real 9B model (qwen3.5:9b, Ollama, user's PC) — MEASURED

Test: `hw/system/local_llm_test2.py` (v2: prompts end at word-piece boundaries; the 9B model writes 12 tokens per call;
SPARK v2 bit-exact reference model runs on the same PC and drafts its own continuation from the same point).
150 test points spread over 20,000 bytes of held-out Python code. Model ran 43 % CPU / 57 % GPU (6.1 GB), so GPU
power was not a valid energy measure (not reported).

| Measurement | Result |
|---|---|
| Next-token accuracy vs real code | 9B model **66.0 %**, SPARK 29.3 % |
| SPARK's next token agrees with the 9B model | 23.3 % |
| **Draft mode (lossless greedy speculative decoding)** | **1.51 tokens per 9B pass → 1.5× fewer big-model passes, output identical** |
| Answer mode, conf ≥ 0.9 | SPARK answers 6 % of tokens, 77.8 % agreement, system accuracy unchanged (66.0 %) |
| Answer mode, conf ≥ 0.5 | SPARK answers 42 % of tokens but agrees only 36.5 % → accuracy drops to 56.0 % |
| Router (10 groups) | SPARK's easiest groups: SPARK 40–44 % vs 9B 67–73 % → not usable as a whole-request router |

## What this changes
* **Draft mode is the validated win**: lossless, measured with a real 9B model, 1.5× fewer big-model passes.
* **Answer mode is only safe at a very high threshold** (~6 % of tokens). SPARK's whole-token answers agree with the
  9B model far less than its byte-level calibration predicted (byte-level calibration does not carry over to
  autoregressive whole-token drafts). The earlier simulated 2.1–2.4× answer-mode savings assumed SPARK's answers were
  acceptable; with a real model they are not, except in the high-confidence zone.
* **Request routing to SPARK alone does not hold** against a real model.
* Earlier comparisons used a small GPU-side model weaker than SPARK; that is why simulations looked better.
