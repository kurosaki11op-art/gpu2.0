---
title: SPARK Cortex brain code
tags: [spark, cortex, code]
---

# SPARK Cortex brain code

Software model of the brain core. Chip logic is compare, count, add, XOR and table lookups; numpy products in the
simulator only add table values quickly.

- `feature_layer.py`: receptors and retina cells (`binarize`), learned feature detectors (`Features`), count memory
  (`CountMemory`), concept cells (`ConceptMemory`).
- `sleep.py`: fast surprise-gated correction table (`SurpriseTable`) and count-memory dreams.
- `cochlea.py`: sound to 28x28 sound picture (v1 one-pole cascade, v2 shift-add resonators), Speech Commands loader,
  FFT log-mel baseline features.
- `detector_learn.py`: the on-chip detector learning rule (bit-exact reference for `cortex_encoder.v` with `ENC_LEARN`).
- `rate_memory.py`: chip-honest dream memories (`RateMemory`, `ConceptRates`, `OnlineConcepts`, `ScaledCounts` = chosen).
- `cortex_int.py`: **integer chip model** (bit-exact reference for the RTL); `run_int.py` runs 5 stages; `month2_final.py` the month-2 final numbers.
- `proof_suite_v3.py`: month-2 float suite (small memory, table-only decision, few-shot).
- `cortex_core.py`: v0 random-wiring lookup neurons (superseded, kept for the first proof).
- `proof_suite.py`: first proof suite. `proof_suite_v2.py`: month-1 suite (`DATA_DIR mnist|fashion|speech`).
- `experiments/month1/`, `experiments/month2/`, `experiments/month3/`: exploration scripts and raw logs.

Related: [SPARK Cortex redesign](../../docs/cortex_redesign.md), [Month 1](../results/cortex_month1.md),
[Month 2 log](../results/cortex_month2_log.md)
- [experiments/month3/](experiments/month3/INDEX.md)
