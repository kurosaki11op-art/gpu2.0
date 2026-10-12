# Activation sparsity on a real model: Qwen2.5-Coder-3B (MEASURED on the team's PC)

Source: a ChatGPT agent on the team's PC ran `hw/system/activation_sparsity.py` and summarised it; this table is transcribed from a screenshot of that summary.
The raw JSON (`hw/results/activation_sparsity.json`) is on the PC and has not been checked here.
Setup: all 36 layers, 8 samples x 256 tokens, run time 2 h 3 min. Metric: mean relative L2 error of each layer's MLP down-projection output
when only the kept fraction of its input entries (weight columns) is used. Lower is better.

| Kept | Oracle (top-k of the current token) | Previous-token set | Leaky trace (SPARK-style state) |
|---|---|---|---|
| 50% | 0.098 | 0.413 | 0.338 |
| 30% | 0.193 | 0.533 | 0.459 |
| 20% | 0.271 | 0.606 | 0.539 |
| 10% | 0.399 | 0.705 | 0.653 |

Reading:
1. **Oracle sparsity exists but is not free:** keeping half the columns costs ~10% relative error per layer; keeping 30% costs ~19%. The effect on end-to-end text quality is not measured here and is the next number needed.
2. **A cheap stateful predictor does not capture it.** Predicting the active set from the previous token or a leaky trace gives 34-41% error at 50% kept, 3.5-4x the oracle's. The trace beats the previous-token set at every level, so a leaky state helps, but nowhere near enough.
3. **Correction to my earlier description:** for the down-projection, the oracle set IS directly usable without prediction. Compute gate and up first, then read only the down-projection columns whose input is large. That is the TEAL-style route. It saves only down-projection weight bytes (about a third of the MLP), and needs no predictor. Prediction is only needed to also skip the gate and up matrices, which is what Deja Vu trains a predictor for.
4. **Not yet compared:** a static "always keep the globally most active neurons" mask, and a trained small predictor. Either may beat the leaky trace and must be tried before concluding anything about SPARK's role.

Status: the premise "SPARK's leaky state predicts which parts of the big model to read" is NOT supported by this first test.
