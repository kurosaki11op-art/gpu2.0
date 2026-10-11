# Round 4: SPARK's own limits and the report's decode limits (SIMULATED)

GPU stand-in: byte-level nanoGPT (4.8M parameters), lossless verification, tokens = GPT-2-style word pieces.
GPU pass cost: datasheet roofline for a 9B model. Draft length and thresholds were picked on a calibration half and are reported on a separate test half.
Scripts: `hw/system/draft_v4.py`, `rollout_draft.py`, `spark_cfg_sweep.py`.

| SPARK limit | Fix tried | Result |
|---|---|---|
| Network path is slow (~2,000 cycles/byte) | "fast draft": draft only from recall answers (~6 cycles/byte) | Keeps 1.18 of 1.19 tokens/pass. One SPARK chip serves a 9B GPU even at batch 256 |
| A fixed draft length wastes GPU work at large batch | Draft length chosen from SPARK confidence (report section 13, experiment #3) | RTX 4090, batch 256: 1.00x with best fixed length, 1.20x with confidence-chosen length. Never below 1.0x |
| Low agreement with the GPU model | Register-only settings sweep | Arbitration threshold 64: 56.5% → 59.5% agreement, run length 1.30 → 1.47. Costs network cycles on every byte |
| Must beat the free software baseline (host prompt lookup) | Tree of copy + SPARK drafts | 1.27 → 1.31 tokens/pass (+3%) |
| RL rollouts (8 samples per prompt, T = 0.8) | Recall memory shared across sibling rollouts | SPARK 1.111 → 1.133 (shared) / 1.145 (prompt seen in an earlier step). Copy from siblings + shared SPARK: 1.195 / 1.234, against 1.160 / 1.208 for the software baseline alone |

Honest reading:
- On this small stand-in model, most of the drafting gain comes from software-style copy drafting.
- SPARK adds about 3% on top of it.
- SPARK's real contribution here is the cheap fast path plus calibrated confidence, which picks the draft length so speculation never slows a busy GPU.
- The real 9B model measured 1.51 tokens/pass with SPARK alone. Whether copy drafting does as well on the 9B model is decided by `local_llm_test3.py`, which reports copy, SPARK and SPARK + copy side by side.
