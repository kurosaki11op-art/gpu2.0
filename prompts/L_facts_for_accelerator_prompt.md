---
title: Prompt to collect the facts for the L accelerator
date: 2026-10-22
tags: [L, accelerator, prompt]
---
# Prompt: collect the facts the L accelerator design needs

> Paste everything below the line into a coding agent opened inside the **L model repository** (not this one). It only reads, measures and reports; it must not change the model's behaviour.

---

You are helping design a dedicated, **matrix-free** accelerator for the language model **L** (brain-inspired, attention-free). The founder's rule: no matrix, especially no heavy matrix, on the chip. Training stays on a GPU. I need exact facts, not summaries. **Read the code and measure; do not guess. If something does not exist, write "does not exist". Cite the file and line for every statement about the code. Label every number MEASURED (you ran it, say the command and seed) or REPORTED (from an old log, say which).** Do not tune anything to make L look better. Write all results to `docs/L_facts.md` and machine-readable files to `results/accel_facts/`.

## 1. Architecture table (read the code)
For the L5 config (d=128, 4 layers, 4 heads) and the wide config (d=192): list **every learned tensor** with name, shape, dtype, which layer, and whether it is used as a dense matrix-vector/matrix-matrix product, an elementwise scale, a table/embedding lookup, or a convolution. Give parameter counts per module (mixer in/out projections, q/k/v/gate projections, FFN up/down, embedding, head, norms, decay/threshold parameters, conv taps, hippocampus parameters) and the share of total parameters and of per-token MACs in dense products. State the vocabulary, whether embedding and head are tied, the norm type, activation functions, and the FFN width.

## 2. The per-token computation, exactly
Write the exact equations for one token, one layer, in the order the code runs them, with shapes: spike quantiser (round/clamp range, where applied, straight-through gradient), membrane/scan recurrence (`h_t = a_t * h_{t-1} + b_t`: how `a_t` and `b_t` are computed, whether they depend on `h_{t-1}` or on the emitted spike, so whether it is linear in `h`), the delta-rule memory (`S` shape per head today: 32x32 or 64x64; `beta`, decay `a`, key normalisation), the 4-tap depthwise conv, homeostasis / adaptive thresholds, the energy budget. Say which parts are in fp32/bf16 and which are integers.

## 3. Activity and sparsity (the key number for a matrix-free chip)
On the eval set, for batch 1 and for the training batch, MEASURE for **every tensor that is the input of a dense product**: the fraction of non-zero entries (mean and per-layer), the distribution of spike counts, and the fraction of neurons that are non-zero for at least one sequence in a batch of 16 (the union). Also measure, per layer, the input sparsity if only the top 5%, 10% and 25% of entries by magnitude are kept (keep-top-k, no retraining) and report bits/byte for each setting; then repeat with a short fine-tune (state its length) so I can see whether event-driven (sparse-row) execution keeps quality.

## 4. Ablations of each block (bits/byte, 3 seeds, same budget)
Full L; without the delta-rule memory; without the hippocampus; without the conv; with ternary weights (which tensors, what scale factors per tensor/channel: scale factors need multipliers, say so); with the spike range limited to [-1, 1] and to [-4, 4]. Report mean and std of bits/byte, and the copy-task accuracy for the hippocampus ablation.

## 5. Hippocampus (hash recall)
Key construction (how many previous bytes, how combined), hash function, table size in slots, slot layout (tag, value, counters), update and eviction rule, probes per lookup, lookups and writes per token, how the result boosts the logits (formula), and the measured share of time and memory it takes.

## 6. Results and measurement method
For each model size you have (0.94M L5, ~9M, any other): parameters, training config (tokens, steps, batch, sequence length, learning rate, optimizer), bits/byte for L and the matched transformer with **every seed you ran**, plus the transformer's config and how "matched" was defined. Energy: how it was measured (NVML counter, sampled power, wall meter), idle subtraction, warm-up, and the raw numbers for training and for inference at batch 1, 8, 64 and context 256, 4k, 16k. Which of the GPU fixes in `prompts/L_architecture_changes_prompt.md` Phase 2 have been done and which have not, with the before/after table.

## 7. Profile
One training step and one batch-1 inference step with `torch.profiler` (and Nsight Systems if available): time per module (scan, delta rule, FFN, hippocampus, quantiser, homeostasis, other), kernel launches per step, average kernel duration, GPU utilisation.

## 8. Golden vectors for a bit-exact simulator
Export (a) the trained fp checkpoint of the L5 model as `.npz` with the tensor names of section 1, (b) the same weights ternarised if a ternary variant exists, and (c) for 1,000 evaluation bytes, the per-layer intermediate values of one forward pass at batch 1: spike outputs (integers), scan state, delta-rule state `S` after each token, conv state, hippocampus lookup results and the final logits, as `.npz`. Add `results/accel_facts/README.md` describing every array (name, shape, dtype, meaning).

## Rules
1. Read-only for model behaviour; new scripts go in `bench/accel_facts/`.
2. One GPU job at a time. If a measurement takes longer than 30 minutes, say what you reduced.
3. Failures and "not available" are valid answers; write them plainly.
4. End `docs/L_facts.md` with a table of anything you could not determine and why.

Related: [L accelerator design](../docs/L_accelerator_design.md), [Docs index](../docs/INDEX.md)
