# Real-model test 3: qwen2.5-coder:3b fully on the GPU (MEASURED acceptance; energy ESTIMATED from a measured baseline)

Setup: Ollama, `ollama ps` showed 100% GPU. 150 points in real code, `--num-gpu 99`, same protocol as the 9B run.

| Measure | Result |
|---|---|
| Next-token accuracy vs real code | big model 59.3%, SPARK 29.3%, copy 43.3% |
| Draft mode, tokens per big-model pass: SPARK | 1.70 |
| Draft mode: copy (software) | 2.16 |
| Draft mode: SPARK + copy | 2.26 |
| Draft mode: multi | **2.28** |
| Answer mode (all gates) | 0% of tokens answered |
| Big model alone | 19 ms per token, 17 W (GPU telemetry), 0.32 J per token |
| Energy with drafting | ~0.14 J per token, computed as 0.32 / 2.28 |

Caveats on the energy figure:
- The 0.14 J is a calculation, not a measurement. It assumes verifying a draft costs one normal pass.
- It also leaves out SPARK's own energy, the extra work on rejected draft tokens, and the CPU, RAM and the rest of the system.
- The 17 W is GPU telemetry only, not wall-plug power. A real number needs a speculative decoder timed end to end.

Across models (acceptance, tokens per pass): SPARK alone 1.51 → 1.58 (9B) → 1.70 (3B); copy 2.12 / 2.16; multi 2.17 / 2.28.
SPARK adds +0.10 to +0.12 tokens per pass (about 5%) on top of copy on the 3B model, against +0.04 on the 9B.
