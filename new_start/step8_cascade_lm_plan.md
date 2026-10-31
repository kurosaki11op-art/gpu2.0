---
title: Live test plan and pre-set bars - confidence-gated cascade of a small and a large language model (31 Oct 2026)
tags: [spark, new-start, cascade, language-model, test-plan, bars]
---

# Cascade on real language models: bars and test plan (31 Oct 2026)

**Written before any run.** Nothing below is a result. Script: [`cascade_lm_test.py`](experiments/lm_cascade/cascade_lm_test.py) (checked end to end on CPU with two tiny models, only to confirm the code runs; those numbers are not quoted anywhere).

## The claim under test

A small model answers every token; when its confidence margin (top-1 minus top-2 probability) is low, a large model of the same family answers instead. The claim: **quality close to the large model at a fraction of its cost, and the margin is a better trigger than chance.** This claim does not depend on our chip, so a laptop test is a real test of it. It says nothing about our chip's speed, energy or cost, which stay modelled.

## Setup

- **Pair A (fits the 6 GB RTX 3050 in half precision, dry run):** a 0.5B and a 1.5B model of one open-weight family. Weight ratio about 3x.
- **Pair B (the real test):** the same 0.5B model and a 3B or 7B model of the same family in 4-bit (needs `bitsandbytes`; the 3B fits, the 7B may). Weight ratio at least 6x.
- Both models of a pair must share a tokenizer (the script checks). Text: the WikiText-2 test set, or any file passed with `--text`; 40 windows of 512 tokens (about 20,000 tokens) for stage A; 12 prompts of 48 tokens, 160 new tokens each, greedy decoding, for stage B.
- **Stage A (teacher-forced):** per-token log-probabilities of both models; cascade at escalation fractions 5% to 100% by lowest small-model margin; controls: random gating (mean of 5 draws) and an oracle (escalate where the large model gains most). Cost counted in weight bytes read per token: `(small bytes + r x large bytes) / large bytes`, one large-model weight read per escalated step (the large model's catch-up over skipped tokens is one batched pass merged into that step).
- **Stage B (live generation, real cascade):** the small model decodes each token; on a low-margin step the large model runs one batched pass over the tokens it has not seen (KV cache kept) and its greedy token is used. Baselines: large alone, small alone. Measures tokens per second, joules per token (NVML power at 20 Hz; **valid only on an otherwise idle GPU**, which must read about 6 W before the run), the share of tokens that needed a large-model pass, agreement of each generated token with the large model's own greedy choice, and the generated text's negative log-likelihood under the large model.

## Pre-set bars

| id | bar | applies to |
|---|---|---|
| **P1** (precondition) | the large model's NLL is at least 8% lower than the small model's on the held-out text; otherwise the pair says nothing | both pairs |
| **P2** (precondition) | large-to-small weight bytes at least 5x, so the bytes bar is evaluable | pair B only |
| **C1** quality | at an escalation fraction of 30% or less, cascade NLL is within 1% of the large model's | both |
| **C2** cost in bytes | at the C1 operating point, weight bytes read per token are at most 0.5x the large model alone | pair B (pair A is reported; with a 3x ratio it cannot pass at 30%: 0.33 + r) |
| **C3** the signal is real | at 30% escalation margin gating closes at least 2x the NLL gap that random gating closes | both |
| **C4** live fidelity | at the C1 operating point greedy agreement with the large model is at least 90% and the NLL of the generated text under the large model is within 5% of the large model alone | both |
| **C5** live speed | tokens per second at least 1.3x the large model alone, batch 1 | pair B |
| **C6** live energy | joules per token at most 0.75x the large model alone (gross and idle-subtracted both reported) | pair B, idle GPU |

**Any miss is reported as a miss; thresholds are not changed after the run.** If C1 fails but a larger escalation fraction passes, that fraction is reported with its bytes ratio, and the claim is restated at that point, with a new bar written before another run.

## Limits stated in advance

One text domain and perplexity-style quality, not downstream task accuracy (a follow-up test: a multiple-choice benchmark with the same gating); greedy decoding only; one model family; the GPU runs both models, so the energy figures measure the cascade logic on a GPU, not our chip; bytes read ignore the key-value cache traffic.

## How to run (on the laptop, PowerShell)

1. Close all other GPU jobs; `nvidia-smi` must read about 6 W and near 0% load (a shared GPU makes C5 and C6 invalid, as in the earlier baseline).
2. `pip install transformers datasets nvidia-ml-py bitsandbytes` (and a CUDA build of PyTorch).
3. Pair A: `python cascade_lm_test.py --small <0.5B model> --big <1.5B model> --out pairA.json`
4. Pair B: `python cascade_lm_test.py --small <0.5B model> --big <3B model> --big-4bit --out pairB.json`
5. Send me the printed table and the two JSON files; I compare them with the bars above and record the result, failures included.

Related: [New start charter](README.md), [Workload map](../docs/gpu_workload_map.md), [Step 7 cost result](step7_cost_basis_result.md), [Docs index](../docs/INDEX.md)
