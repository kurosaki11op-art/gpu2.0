# SPARK core v0 — trained model format and exact integer semantics

Any model loaded into SPARK core v0 must match this architecture and these integer rules exactly. The reference implementation is `hw/golden/spark_golden.py`; the RTL is bit-exact with it.

## Architecture (fixed sizes in v0)
| Name | Shape | Meaning |
|---|---|---|
| `emb` | [256, 64] | Byte embedding. Row = input byte. Values are used directly as input spikes. |
| `w0` | [128, 64] | Layer 0 weights [out, in] |
| `w1` | [128, 128] | Layer 1 weights [out, in] |
| `w_exit` | [256, 128] | Exit head on layer-0 spikes → 256 byte logits |
| `w_main` | [256, 128] | Main head on layer-1 spikes → 256 byte logits |

All five arrays: **integers in [-8, 7]** (int4), saved together in one `.npz` file with exactly those keys.

## Model constants (`config.json`)
```json
{"a": 230, "acc_sh": 2, "s_sh": 4, "exit_th": 64, "conf_th": 1}
```
- `a`: membrane decay in Q8 (0–256), i.e. decay = a/256.
- `acc_sh`: right shift from accumulator to membrane input.
- `s_sh`: right shift from membrane to spike count.
- `exit_th`: early-exit margin (top-1 minus top-2 exit logit).
- `conf_th`: recall-table confidence needed to bypass (0–3).

## Exact per-token integer semantics (normal mode)
For input byte `b` (all integers; `>>` is arithmetic shift, floor):
1. `x = emb[b]` (64 values).
2. Layer 0, for each neuron i: `acc = sum_j w0[i,j] * x[j]`
   `h = sat16(((h * a) >> 8) + (acc >> acc_sh))`
   `mag = min(|h| >> s_sh, 7)`; `s = sign(h) * mag` (spike in [-7, 7]); `h = h - s * 2^s_sh` (reset by subtraction).
   `sat16` clamps to [-32768, 32767]. Membrane `h` persists across tokens.
3. Exit head (if enabled): `logit_e = w_exit @ s0`; `margin = top1 - top2`; if `margin >= exit_th`, predict `argmax` (lowest index wins ties) and skip steps 4–5.
4. Layer 1: same as step 2 with `w1` and input `s0`.
5. Main head: `logit = w_main @ s1`; predict `argmax`.

Change-only, adaptive, recall and energy-cap modes change **how much work** is done; with no cap they produce the same accumulators as normal mode (the recall bypass and early exit change which path answers).

## Accumulator range
SPARK v0 uses 16-bit accumulators. With int4 weights and spikes (|w| ≤ 8, |s| ≤ 8) the worst case is 128 × 8 × 8 = 8,192, so overflow is impossible by construction.

## How to load trained weights
```
python3 hw/run_sim.py --weights model.npz --cfg-json config.json --text sample.txt --tag _trained
```
This checks shapes and ranges, writes the memory files, runs every configuration in RTL simulation, compares each token with the golden model, and reports work per token and next-byte accuracy in `hw/results/sim_results_trained.md`.
