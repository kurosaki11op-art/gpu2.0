# Real-model test 3: qwen3.5:9b on the team's PC (MEASURED, `hw/system/local_llm_test3.py`)

Setup:
- Ollama, model split 43% CPU / 57% GPU.
- 150 token-boundary points in real code, 800-byte context, greedy decoding.
- The big model's own continuation is the reference, so draft mode is lossless.

| Measure | Result |
|---|---|
| Next-token accuracy vs real code | big model 66.0%, L 29.3%, copy 43.3% |
| Draft mode, tokens per big-model pass: L | **1.58** |
| Draft mode: copy (prompt lookup, software) | **2.12** |
| Draft mode: L + copy | **2.16** |
| Draft mode: multi (L + copy + recall alternatives) | **2.17** |
| Answer mode, token-type gate at 95% / 90% / 80% | 0% of tokens answered: no token type reached the target agreement |
| Big model alone | 72 ms per generated token |
| Energy | not measured, because the model was not fully on the GPU |

Honest reading:
1. Lossless drafting with a real 9B model reaches **2.17 tokens per pass**, so the big model needs 46% of its passes. That is an upper bound on speed-up: it assumes verifying the draft costs about one normal pass.
2. Most of that comes from **copy drafting** (prompt lookup), a known software technique. L's own drafts add +0.04–0.05 tokens/pass on top of it.
3. L alone improved from 1.51 (test 2) to 1.58.
4. Answer mode is not viable on this model and text. It is dropped from claims.
