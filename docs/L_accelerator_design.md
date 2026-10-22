---
title: Accelerator for L, a skeptical design review
date: 2026-10-22
tags: [L, accelerator, architecture, review]
---
# Accelerator for L: profile, microarchitecture, staged path, fair comparison, risks

Scope: this note is about **L** (the brain-inspired, attention-free language model), not L Cortex. Labels: **MEASURED** = from the numbers you gave me; **MODELLED** = computed here, formula shown, assumptions listed; **ESTIMATED** = from a source I name (recalled from the literature, not looked up live: verify before quoting). I have not run L; the only L facts I have are your message and `prompts/L_architecture_changes_prompt.md` in this repo.

## 0. Things in your numbers that a reviewer will question first

1. **Which model do the GPU numbers belong to?** You give L5 (d=128, 4 layers, ~0.94M params) and a 9M-parameter bits/byte result. The same 0.84 mJ/token means very different things for the two. MODELLED, training FLOPs ~ 6 x params per token: 0.94M params -> 5.6 MFLOP/token -> 4,096 tokens in 114 ms = **0.20 TFLOP/s** (149 pJ/FLOP); 9M params -> **1.94 TFLOP/s** (15.6 pJ/FLOP). Neither says how close a 3050 is to its peak (I do not have its datasheet peak in front of me; look it up). Tell me which model was timed.
2. **Power is consistent, good.** MODELLED: L = 0.84 mJ x (4,096 / 0.114 s = 35,930 tokens/s) = **30.2 W**; transformer = 0.41 mJ x 84,107 tokens/s = **34.5 W**. Both are plausible laptop-GPU draws, so the energy ratio (2.05x) is almost entirely the time ratio (2.34x): L is slower, not hungrier per second.
3. **"1,298 kernels" is not by itself the cause.** MODELLED: 114 ms / 1,298 = **88 us per kernel** (transformer: 155 us). Launch overhead is a few us, so the kernels are not launch-bound; they are tiny, serial or poorly occupied (the earlier prompt in this repo names ~1,000 tiny 64x64 triangular solves per layer, the one-thread-per-neuron recurrence and sort-based hashing). That is a software problem a fused kernel may fix. **The claim "GPU is unsuitable" is not established until the Phase 2 fixes of `prompts/L_architecture_changes_prompt.md` (chunked delta rule via WY/UT, parallel scan, CUDA graphs, real GPU hash table) have been measured.** Do that before spending money on silicon.
4. **Training energy is the wrong metric for an inference chip.** L trains at 2x the transformer's energy/token (MEASURED). Your inference claim (2-30x less energy at long context and batching) is on a GPU, small models. A chip's case rests on inference energy per token against a *fused* GPU baseline and against a transformer on custom hardware (section E).
5. **0.872 vs 0.913 bits/byte** is a 4.5% relative gap (MODELLED: (0.913 - 0.872)/0.913). Number of seeds and variance: unknown to me. Without 3+ seeds at 2-3 sizes it is an anecdote.

## A. Profile model

### A.0 Assumptions (change them when you give me the real code)

| Item | Assumption | Source |
|---|---|---|
| Layers, d, heads | 4, 128 (and 192), 4 heads, head dim = d/4 (32 and 48) | your message; head count at d=192 assumed |
| Parameters | 0.94M total | your message |
| Embedding / head | byte vocabulary 256, tied: 256 x d | assumption |
| Matmul parameters per layer | (0.94M - 32,768) / 4 = 226.8k = 13.8 d^2; I do not know the split between mixer and FFN | MODELLED |
| d=192 | same structure, so matmul params x (192/128)^2 = 2.04M (+49k embedding); the real wide variant may differ | MODELLED |
| Spike counts | integers in [-8, 8] (4 bits signed) | repo prompt |
| Fast-weight matrix | dk x dv per head = 32 x 32 (d=128). The repo prompt says 64 x 64 "today": check | your message vs repo prompt |
| Activity | 2-10% of FFN neurons fire per token | repo prompt (measured there) |
| Hippocampus | hash table; slots, key width and value width **unknown** (parameters N, Kb, Vb below) | unknown |

### A.1 Per-token inference (batch 1, every weight used once)

| Item | d=128 | d=192 | Formula |
|---|---|---|---|
| Matvec MACs (adds when ternary) | 0.907M | 2.04M | P_layers |
| Delta rule MACs | 65.5k | 147k | layers x heads x 4 x dk x dv (S k, decay a S, rank-1 update, read S q) |
| Scan MACs | 0.5k | 0.8k | layers x d (diagonal) |
| Conv (4 taps) MACs | 2.0k | 3.1k | layers x d x 4 |
| Total MACs/token | ~0.98M | ~2.19M | sum; delta rule is ~7% of the work |
| Weight bytes: fp16 | 1.81 MB | 4.08 MB | 2 x P_layers |
| Weight bytes: int8 | 0.91 MB | 2.04 MB | P_layers |
| Weight bytes: ternary, 2-bit packed | **227 KB** | **510 KB** | P_layers / 4 (1.58-bit packing: 179 KB / 403 KB) |
| MAC per weight byte at batch 1 | 0.5 (fp16), 1 (int8), **4 (ternary)** | same | MACs / bytes: always memory-bound at batch 1 unless weights sit on chip |

### A.2 State (never has to leave the chip)

| State | d=128 | d=192 | Formula (16-bit state unless stated) |
|---|---|---|---|
| Scan membrane h | 1.0 KB | 1.5 KB | layers x d x 16 b |
| Delta-rule S | **32 KB** (int8 16 KB, fp32 64 KB) | **72 KB** (int8 36 KB) | layers x heads x dk x dv x 16 b |
| Conv delay line | 1.5 KB | 2.25 KB | 3 past tokens x d x layers x 8 b |
| Hippocampus | N x (Kb + Vb) bits | same | unknown; e.g. N = 4,096, Kb = 32, Vb = 128 would be 80 KB (assumption, not a recommendation) |
| **Total without hippocampus** | **~34.5 KB** | **~76 KB** | independent of context length |

For comparison, a transformer with the same dims needs a KV cache of 2 x layers x d x 8 b = 1 KB per token (MODELLED, int8): 0.26 MB at T = 256, 4.2 MB at T = 4,096, 33.6 MB at T = 32,768. This constant-state property is L's structural advantage over a transformer chip at long context; at T = 256 there is none.

### A.3 Sparsity (event-driven) bound

Only the FFN down-projection can skip inactive neurons unless the firing set is predicted before the up-projection (Deja Vu-style, extra hardware). If the down-projection is a fraction f of matmul parameters and a fraction rho of neurons fire, the saving is f (1 - rho). With f = 1/3 (standard 4x FFN; **assumption**) and rho = 5%: **31%** fewer adds (MODELLED). It is a modest gain, not an order of magnitude; do not quote "sparsity saves 20x" without a measured firing rate per layer.

### A.4 One training step (B = 16, T = 256 = 4,096 tokens)

| Item | Value | Formula |
|---|---|---|
| Matmul FLOPs | 23 GFLOP (0.94M) / 221 GFLOP (9M) | 6 x params x 4,096 (forward + 2x backward) |
| Optimizer memory (fp32 master + Adam m, v) | 11.3 MB at 0.94M | 12 B x params |
| Saved activations, int8, 6 linears per layer | 768 KB per sequence, 12.3 MB per B = 16 | T x d x layers x 6 |
| Scan states, all steps stored (16 b) | 256 KB per sequence | T x d x layers x 2 B |
| Scan states, checkpoint every 64 + recompute | 4 KB + 64 KB working | |
| Delta-rule S per token stored (fp16) | **8.4 MB per sequence** | T x 16,384 x 2 B: do not store; checkpoint S per chunk instead: 128 KB per sequence |

## B. Microarchitecture (inference)

Clock assumptions: ASIC 200 MHz at a mature node; FPGA 100 MHz. Both are placeholders until a synthesis run gives timing.

```
           token byte
               |
        +------v-------+     embedding (256 x d, int8) in SRAM
        |  Embed / hash|------------------------------+
        +------+-------+                              |
               | x (int spikes, 4 b)                  | key (last n bytes)
   per layer:  v                                      v
   +-----------------------------+            +--------------------+
   | TMV array: ternary add-only |            | Hash unit + bucket |
   | in-proj (q,k,v,gates,u)     |            | SRAM (tag compare) |
   +------+------+------+--------+            +---------+----------+
          |      |      |                               | recalled byte + conf
          v      v      v                               |
   +------+--+ +-+------+-----+  +---------------+      |
   | Scan    | | Delta unit   |  | Conv delay    |      |
   | unit    | | S k, a S,    |  | line (4 taps) |      |
   | h=a h+b | | rank-1, S q  |  +-------+-------+      |
   +----+----+ +------+-------+          |              |
        +-------------+------------------+              |
                      v                                  |
           +----------+-----------+                      |
           | Spike quantise       |  round, clamp, event |
           | + event queue        |  list (non-zero only)|
           +----------+-----------+                      |
                      v                                  |
           +----------+-----------+                      |
           | TMV array: out-proj, |                      |
           | FFN up -> fire -> down                      |
           +----------+-----------+                      |
                      v (next layer, 4x)                 |
               +------+-------+                          |
               | Head + logits|<-------------------------+ boost
               +------+-------+
                      v
                 next byte
```

| Block | Design | Size (d=128) | Cycles per token (MODELLED) |
|---|---|---|---|
| 1. Scan unit | one 16-bit MAC lane per channel group; decay `a` as a shift or small table so it is multiplier-free in `hw_mode`; pipelined 1 channel/cycle per lane; 16 lanes | 16 lanes, 16 b | 4 layers x 128 ch / 16 = 32 |
| 2. Delta unit | per head: S k (32 MACs per row), error, rank-1 update and S q fused in one pass over S so S is read and written once per token; 32 x 32 int8/int16 multipliers are needed (S k is activation x state, not ternary): the first real multipliers in the design | 32 MAC lanes, S in a 2-port SRAM of 32 KB (16 KB int8) | 4 x 4 heads x 4 x 1,024 / 32 = 2,048 |
| 3. TMV array | add/sub/skip lanes, one per output channel; input-stationary: activation x_j broadcast, one 128 x 2-bit weight column per cycle (256 b/cycle of SRAM); 16-bit accumulators | 128 lanes (~20-24 LUT4 per lane on an FPGA, ESTIMATE from experience; verify by synthesis) | 0.907M / 128 = **7,086** |
| 4. Event handling | the spike quantiser writes (index, value) pairs for non-zero outputs into a FIFO; the FFN down-projection reads only fired columns | FIFO 512 x 12 b | saves ~31% of adds at 5% firing (A.3) |
| 5. Hash/CAM | not a true CAM (a CAM costs far more area and power per bit than SRAM; I have no cited ratio, treat as "much more"): hash the last n bytes, index a 4-way bucket SRAM, compare tags, return value + confidence; 1-2 probes per token | N x (Kb + Vb) bits + tags | ~10-20, off the critical path if the key is known one token ahead |
| 6. SRAM layout | weights ternary 2-bit: 4 banks x 64 KB (227 KB used, d=128); S: 32 KB dual-port; h, conv, queues: 4 KB; hash: N x ...; activations: 2 KB | ~0.3 MB + hash | |
| **Total** | | | **~9.2k cycles** per token per stream: 46 us at 200 MHz = **~22k tokens/s**, 92 us at 100 MHz = ~11k tokens/s (MODELLED, no stalls, one stream) |

Weight bandwidth from SRAM: 227 KB per token / 46 us = **4.9 GB/s** (MODELLED), trivial for banked SRAM. The scan and delta units are the serial dependency across tokens, but there is only one token in flight per stream, so they hide behind the TMV array. Several streams (batch) interleave to keep the TMV array busy while the delta unit finishes.

### B.1 Energy model (MODELLED from ESTIMATED op energies)

Per-op energies (ESTIMATED, Horowitz, "Computing's energy problem", ISSCC 2014, 45 nm; scaling to a modern node is uncertain): 16-bit integer add ~0.05 pJ; 8-bit multiply ~0.2 pJ (16-bit ~0.8 pJ is my interpolation); SRAM read, 64 bits, ~10 pJ (8 KB) to ~20 pJ (32 KB); DRAM read, 64 bits, ~1.3-2.6 nJ.

| Term (d=128 ternary, batch 1) | Formula | Energy |
|---|---|---|
| Weight reads | 227 KB / 8 B x 20 pJ | 0.57 uJ |
| TMV adds | 0.907M x 0.05 pJ | 0.045 uJ |
| Delta-rule arithmetic | 65.5k x 0.85 pJ | 0.056 uJ |
| Delta-rule S traffic | 2 x 32 KB / 8 B x 20 pJ | 0.16 uJ |
| **Total, paper bound** | | **~0.83 uJ/token** |

Two sanity points. (1) The weight reads dominate (68%), so batching B streams that share the weights cuts that term by B, and the SRAM size is the real lever, not the adders. (2) 0.83 uJ is a lower bound that ignores clock tree, control, leakage, wiring, the hash unit and the head; a real first chip is typically several times worse (I do not have a cited factor; plan for 3-10x: 2.5-8 uJ). Against your 0.84 mJ/token that would be 100-340x, **but the 0.84 mJ is training on a GPU; compare with GPU inference energy per token of a fused L implementation, which you have not given me.** Do not show the 1,000x number to a reviewer.

## C. Inference first, training second

**What BPTT needs:**
- A reverse scan: for a diagonal linear recurrence the backward pass is another diagonal linear recurrence (reverse time, same coefficients), so the scan unit is reusable.
- Delta rule backward: needs S_t for every token. Storing them is 8.4 MB per sequence (A.4); recompute from chunk-boundary checkpoints (chunk 64: 128 KB per sequence) plus the WY/UT form per chunk, which brings in small triangular solves and real multipliers (the same operation that costs 55% of L's GPU forward time per the repo prompt).
- Straight-through spikes: trivial (a clamp mask).
- Activation storage: 12.3 MB per B = 16 batch at int8, or recompute per layer (cost: one extra forward).
- Optimizer: fp32 master weights + Adam = 11.3 MB at 0.94M params, and bf16 multipliers/accumulators for the gradients. That gives up the multiplier-free property of the inference chip.

**Recommendation:** train on a GPU (ideally with the fused kernels of Phase 2); move **inference** onto the chip. Reasons: (1) the chip's SRAM budget is ~0.3-0.6 MB while training needs 12-25 MB (MODELLED above); (2) training requires multipliers and fp32/bf16, so it would be a second, larger chip; (3) your measured local rules cost 14-20% bits/byte, far worse than the 4.5% quality edge you are claiming, so they cannot replace BPTT. What the chip *can* do on-device without BPTT is what L already does at inference: update the fast-weight S and write the hippocampus. That is on-device adaptation worth showing, and it is free once the inference datapath exists. Retrain-on-chip is a v3 question, only after the energy win at inference is measured.

## D. Staged path for a solo founder (costs are ESTIMATED, order of magnitude, verify current prices)

| Stage | Deliverable | Cost | Time (my judgement) | Pass / fail |
|---|---|---|---|---|
| 0. GPU baseline | fused L (Phase 2 fixes) with measured inference mJ/token at batch 1, 8, 64 and T = 256, 4k, 32k | $0 | 2-4 weeks | **Fail the chip programme if a fused GPU L is within ~3x of the paper bound x 5 overhead (i.e. the chip would win by less than ~10x)** |
| 1. Cycle-accurate simulator (Python, then C++) with the section B energy model | integer inference bit-exact with the PyTorch model (ternary weights, int spikes), op/byte counters, bit-width sweep | $0 | 4-8 weeks | integer model within 1% bits/byte of the fp model; reported pJ/token with the op table and a sensitivity analysis |
| 2a. Tang Nano 20K | d=64 variant fully on chip (ternary weights 57 KB + S 8 KB + state fit the 103.5 KB BSRAM, MODELLED); d=128 streams weights from the module's SDRAM: 227 KB per token, so 400-664 MB/s gives **1.8k-2.9k tokens/s** upper bound at batch 1 (MODELLED; part speed and width to verify) | board ~$25-35 (ESTIMATED, retail) | 6-10 weeks | bit-exact vs simulator on 1,000 tokens; measured tokens/s and board power (USB meter) |
| 2b. Bigger FPGA (if 2a is too small) | whole d=128/192 model on chip with a bigger hash table. Candidates: Lattice ECP5-85 (ULX3S, ~3.7 Mbit block RAM), Xilinx Artix-7 100T (Arty A7, ~4.9 Mbit), Sipeed Tang Mega 60K/138K (verify memory sizes) | board ~$120-300 (ESTIMATED) | 4-8 weeks more | same pass criteria at d=192 |
| 3. Silicon | Tiny Tapeout tiles are too small for a ~0.3 MB SRAM (a tile is a tiny fraction of a mm^2); a real shuttle needs an SRAM macro flow and a few mm^2 at 130 nm: order $10k-$50k for an MPW slot plus packaging and board (ESTIMATED; I have no current price list, and I recall Efabless, the open-shuttle broker, stopped operating in 2025: verify); open SRAM macros are small (the L repo's own SKY130 estimates showed memory macros dominating area) | $15k-$60k all-in (ESTIMATED) | 6-12 months | measured pJ/token within 2x of the FPGA-calibrated model; do not start unless stage 0 and 2 pass |

## E. Fair comparison and what would falsify the claim

| Comparison | What to measure | Note |
|---|---|---|
| (a) transformer on a GPU | same bits/byte target, tokens/s, mJ/token (inference), at T = 256, 4k, 32k, batch 1/8/64, fused kernels for both (FlashAttention for the transformer; fused scan + chunked delta for L) | the transformer's KV cache grows linearly; L's does not. At T = 256 expect L to have **no** structural advantage |
| (b) transformer on equally custom hardware | int8 or ternary (BitNet b1.58-style) transformer, KV cache held in on-chip SRAM up to its capacity, the same process node and the same SRAM budget | the strongest rival. At T = 4k the KV cache is 4.2 MB per sequence (int8): if the chip has only ~0.5 MB of SRAM, the transformer chip must go to DRAM and L wins; if it has ~8 MB, the transformer chip is competitive up to ~8k tokens |

**The claim "L's chip wins" is falsified if any of these hold:**
1. A fused L on the GPU is within ~3x of the chip's calibrated energy per token (the problem was software).
2. An int8/ternary transformer accelerator with the same SRAM budget matches L's energy per token at the same bits/byte for the contexts you care about.
3. At >=3 seeds and at 30M-100M parameters, L's bits/byte advantage over the matched transformer falls under its seed-to-seed noise, or ternary L loses more than ~2-3% bits/byte (my proposed thresholds, not data).
4. The hippocampus ablation shows that the exact-recall unit contributes nothing measurable outside copy tests (then drop the hash unit and its bandwidth risk).

## F. Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Hash-table bandwidth | in DRAM each lookup is a random 32-64 B burst and ~50-100 ns of latency; with generation the key depends on the byte just produced, so latency is exposed (not a throughput problem at ~10 us/token, but it breaks the "one token in flight" pipeline); a true CAM is expensive | SRAM bucketed hash with tags; confine to N slots that fit; measure recall vs N |
| Ternary or low-bit quality | BitNet b1.58 reports parity with fp16 only at larger scales (ESTIMATED, Ma et al. 2024, recalled); at 0.94M-9M parameters the capacity gap is likely larger, and I have no ternary L numbers from you | QAT sweep: ternary / int4 / int8 weights, 4/6/8-bit spikes, S at 8/12/16 b: pick the cheapest that holds bits/byte |
| Small-scale evidence | everything is <=9M parameters with mostly single runs; scaling trends of recurrent/fast-weight models against transformers at 100M+ are mixed in the literature and I cannot predict L's | 3 seeds at 3 sizes before any tape-out decision |
| SRAM area | 0.3-0.6 MB of ternary weights is only enough for tiny models; a 100M-parameter L is 25 MB of ternary weights (MODELLED: 100M weights x 2 bits = 25 MB) which needs DRAM and brings back the memory wall | the honest target is a *small, always-on* model (hundreds of KB to a few MB), not a general LLM |
| GPU catch-up | libraries already ship chunked delta-rule and scan kernels (flash-linear-attention) | stage 0 above |
| Multipliers sneak in | the delta unit and decay need real multiplies unless S k is also quantised to shifts | quantise `a`, `b` to powers of two and test; count multipliers explicitly |
| Solo founder risk | tape-out is months and tens of thousands of dollars | gate each stage on the pass/fail above |

## Prior art, and what is actually different

| Prior art | What overlaps | Reference (recalled, verify) |
|---|---|---|
| IBM TrueNorth, Intel Loihi / Loihi 2, SpiNNaker / SpiNNaker 2, BrainScaleS, BrainChip Akida, SynSense Speck / Xylo, Tianjic | event-driven spike processing, on-chip SRAM state, low-precision synapses | published chips and papers |
| Loihi 2 running language-style models | Intel and collaborators ported a ternary, recurrent MatMul-free language model to Loihi 2 (2025) | Zhu et al., "Scalable MatMul-free Language Modeling", 2024; Abreu et al., Loihi 2 demonstration, 2025 |
| Ternary LLM FPGAs | add-only ternary weight engines on edge FPGAs | BitNet b1.58 (Ma et al., 2024); TeLLMe (2025, FPGA ternary accelerator; I am not sure of the exact title) |
| SSM / Mamba accelerators | pipelined scan unit, state on chip | MARCA (MICRO 2024), LightMamba (FPGA, 2025); RWKV FPGA ports exist, I cannot name a specific paper with confidence |
| Spiking language models | integer spikes in an RWKV-like recurrence | SpikeGPT (Zhu et al., 2023) |
| Delta-rule fast weights | the algorithm | Schlag et al. 2021 (fast weight programmers); DeltaNet / Gated DeltaNet (Yang et al., 2024-2025) |
| CAM for memory-augmented networks | associative lookup in hardware | Karunaratne et al., Nature Communications 2021 (recalled) |

**What I think is genuinely different, stated skeptically:** none of the single blocks is new: ternary add-only engines, spike events, pipelined scans and CAM recall each have prior hardware. The only candidate for novelty is the **combination around a constant-size state** (delta-rule fast weights + integer spikes + exact-recall hash + ternary weights on one SRAM-resident datapath), and the one block I have not seen in a language-model accelerator is the exact-recall hash unit coupled to the output logits. Whether the combination is worth a chip depends on two things you have not shown me: ternary L quality at 100M+, and an inference energy win over a fused GPU L. If either fails, the contribution is the model, not the hardware.

## First three things to do this month

1. **Profile and fuse on the GPU (weeks 1-2).** Run `torch.profiler`/Nsight on one training step and one batch-1 inference step, get the per-module time split (scan, delta rule, FFN, hippocampus, other), then apply the Phase 2 fixes (chunked delta rule via flash-linear-attention, fused scan, CUDA graphs, GPU hash). Measure **inference** mJ/token at batch 1/8/64 and T = 256/4k/32k with NVML plus a wall meter. This number is the baseline any accelerator must beat, and it may show the GPU was fine.
2. **Write the bit-exact integer simulator of L inference with op/byte counters (weeks 2-4).** Ternary weights, 4-bit spikes, 8/12/16-bit S; sweep widths; report bits/byte versus width, bytes moved per token and the section B energy table with real counts. Pass: within 1% bits/byte of the fp model.
3. **Settle the quality evidence (weeks 1-4, in parallel).** Train L and the matched transformer at 3 sizes (for example 1M, 9M, 30M) with 3 seeds each, fp and ternary, and run the hippocampus ablation. If the 4.5% bits/byte edge is not outside the seed noise, or ternary erases it, stop here and redirect effort to the model.

Related: [Docs index](INDEX.md), [Prior art for L Cortex](prior_art_cortex.md), [Project memory](PROJECT_MEMORY.md)
