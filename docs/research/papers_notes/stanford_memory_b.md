---
title: Paper notes - IO-aware algorithms and memory hierarchy at scale (Stanford)
tags: [l, research, papers, memory, energy]
---

# Paper notes - IO-aware algorithms and memory hierarchy at scale (Stanford)

Read from the arXiv PDF text (25 Oct 2026). Numbers are quoted as printed and are **REPORTED by the authors, not
reproduced by us**. "DERIVED" = computed by us from printed numbers. "MODELLED" = our own cost model with stated
assumptions (section 6). "UNVERIFIED" = not found in, or not readable from, the paper text. Ids were checked against the
PDF headers:

| # | Paper | arXiv id | Header check |
|---|-------|----------|--------------|
| 1 | FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness (Dao, Fu, Ermon, Rudra, Re) | 2205.14135 | Stanford CS, v2 23 Jun 2022 |
| 2 | FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning (Dao) | 2307.08691 | Princeton + Stanford, v1 17 Jul 2023 |
| 3 | Monarch: Expressive Structured Matrices for Efficient and Accurate Training (Dao, Chen, Sohoni, Desai, Poli, Grogan, Liu, Rao, Rudra, Re) | 2204.00595 | Stanford + Buffalo + Michigan, v1 1 Apr 2022 |
| 4 | SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts (Prabhakar et al.) | 2405.07518 | SambaNova authors, v2 5 Nov 2024 |

What was read: papers 1, 2 and 4 in full (main text, algorithm boxes, tables, appendices; figure-only data is flagged).
Paper 3: all of the main text, Appendix A (related work), Appendix B (notation) and Appendix E (experiment details) were
read; the long proofs in Appendices C and D (general block sizes, rectangular matrices, expressiveness and projection
theory) were only skimmed and are **UNVERIFIED** by us. Paper 4 is a SambaNova paper; the Stanford link is through its
co-authors (the task brief says "Stanford co-authors"), and the author block in the PDF text shows company e-mail
addresses only, so the Stanford affiliation of individual authors is **UNVERIFIED** from the text.

**A finding that matters for the founder's question: none of the four papers contains an energy figure.** A text search
for "energy", "pJ", "joule" and "watt" finds nothing relevant in any of them. Their evidence is **bytes moved, kernel
launches, wall-clock time, achieved fraction of peak bandwidth or FLOPs, and machine footprint**. So "data movement
dominates energy" is, in these papers, an argument by bandwidth and time, not a measurement in joules. Any energy claim for
L has to come from our own per-byte constants (see section 6, left as parameters, not invented).

## 0. Bottom line for L (read this first)

1. **The unit that the best Stanford groups optimise is bytes crossing a tier boundary, not arithmetic.** FlashAttention
   makes attention 7.3 ms instead of 41.7 ms while doing *more* arithmetic (75.2 vs 66.6 GFLOPs) because HBM traffic falls
   from 40.3 GB to 4.4 GB (Fig. 2 left, REPORTED, A100, GPT-2 medium, N=1024, d=64, 16 heads, batch 64). Time tracked bytes,
   not FLOPs. That is the whole case for designing L around a bytes-per-decision budget.
2. **Three techniques transfer to a matrix-free chip:** (a) tile so that a block is loaded once into fast memory and
   *all* work on it is done there (FlashAttention loop order); (b) fuse the steps of one decision so intermediates never
   leave fast memory (FlashAttention kernel fusion, SN40L spatial fusion, 13x on its most fusable benchmark); (c) keep a
   small hot set in the fast tier and the large cold set in a capacity tier, swapping at the granularity of one
   "expert" (SN40L: 520 MiB SRAM / 64 GiB HBM / 1.5 TiB DDR; 150 experts of 7B parameters; only one expert's weights are
   moved per request).
3. **Two techniques conflict with the founder's rule:** Monarch matrices and the dense GEMMs inside FlashAttention are
   matrix products (block-diagonal batched matmul, QK^T and PV). They are not usable in L. Their *lesson* (structure that
   matches the hardware's block size beats unconstrained sparsity that does not) transfers; their *operator* does not.
4. **One concrete rule for L (section 6):** put the counting table in tiers by hotness, make the unit of movement a
   *class row* (or a clause list), and budget bytes per decision. With our stated assumptions, a flat scan costs
   41 KB, 410 KB and 4.1 MB per decision at 10, 100 and 1,000 classes (MODELLED); a hash-recalled top-8 candidate scheme costs
   about 41 KB, 34 KB and 41 KB (MODELLED), i.e. flat in the number of classes.

## 1. FlashAttention (2205.14135)

### 1a. Mechanism

**Problem.** Standard attention computes S = QK^T (N x N), P = softmax(S), O = PV. Algorithm 0 (standard): load Q,K by
blocks, write S to HBM; read S, write P to HBM; load P,V, write O. S and P are N x N and live in HBM, so memory is
O(N^2) and HBM traffic is Theta(Nd + N^2) (Theorem 2). Softmax, masking and dropout are elementwise or reduction
operations, which are memory-bound, so extra passes over the N x N matrix dominate the time.

**Memory hierarchy model used (Fig. 1 left, A100).** SRAM 19 TB/s, 20 MB total (192 KB per SM, 108 SMs); HBM 1.5 TB/s,
40 GB (the text gives 1.5-2.0 TB/s and 40-80 GB for A100 variants); CPU DRAM 12.8 GB/s, more than 1 TB. SRAM is about an
order of magnitude faster than HBM and many orders smaller.

**Algorithm 1 (tiling).** Block sizes B_c = ceil(M/4d), B_r = min(ceil(M/4d), d), where M is SRAM size in elements. Outer
loop over column blocks j of K,V (load K_j,V_j into SRAM); inner loop over row blocks i of Q (load Q_i, O_i, l_i, m_i);
on chip compute S_ij = Q_i K_j^T, the row max m~_ij, P~_ij = exp(S_ij - m~_ij), row sum l~_ij; merge into running
statistics m_new = max(m_i, m~_ij), l_new = e^(m_i - m_new) l_i + e^(m~_ij - m_new) l~_ij; write back
O_i = diag(l_new)^-1 (diag(l_i) e^(m_i - m_new) O_i + e^(m~_ij - m_new) P~_ij V_j), then l_i, m_i. The trick that makes
tiling exact is that softmax can be decomposed: keeping (m, l) per row, the softmax of a concatenation is a rescaled
combination of the softmax of the parts ("algebraic aggregation"). The N x N matrix is never written to HBM.

**Recomputation.** The backward pass needs S and P. Instead of storing them, the forward pass stores only O and the
statistics (m, l) (O(N) memory), and the backward pass recomputes S_ij and P_ij from Q,K,V blocks in SRAM. This is
"selective gradient checkpointing", but unlike usual checkpointing it is *faster*, because the extra FLOPs cost less than
the saved HBM reads. Dropout masks are not stored either: the pseudo-random generator state is saved and the mask is
regenerated (Appendix B.4). The softmax-gradient term D_i = P_i:^T dP_i: is rewritten as dO_i^T O_i (a length-d dot
product) so no length-N reduction is needed (Eq. 4).

**Kernel fusion.** Because the work is tiled, the whole sequence matmul - softmax - mask - dropout - matmul is one CUDA
kernel: inputs read once from HBM, result written once. The paper notes naive fusion alone is not enough in training
because intermediates must still be saved for backward; recomputation is what makes fusion pay.

**Block-sparse FlashAttention (Algorithm 5).** Same loop, skip blocks where the block mask M is zero. Butterfly sparsity
pattern used in experiments.

### 1b. The numbers

IO complexity (all proofs in Appendix C; REPORTED):

| Quantity | Standard attention | FlashAttention |
|----------|-------------------|----------------|
| HBM accesses, forward (Theorem 2) | Theta(Nd + N^2) | Theta(N^2 d^2 M^-1) |
| HBM accesses, backward (Theorem 5) | Theta(Nd + N^2) | Theta(N^2 d^2 M^-1) |
| Extra memory beyond inputs and outputs (Theorem 1) | O(N^2) | O(N) |
| FLOPs | O(N^2 d) | O(N^2 d) |
| Block-sparse (Proposition 4) | - | Theta(Nd + N^2 d^2 M^-1 s), s = fraction of nonzero blocks |

Proposition 3 gives a lower bound: no exact-attention algorithm achieves o(N^2 d^2 M^-1) HBM accesses for all M in
[d, Nd]. For d = 64-128 and M about 100 KB, d^2 is far smaller than M, hence "up to 9x fewer" HBM accesses (introduction).
Why the proof works: K,V are loaded in blocks of size Theta(M); for each block Q is streamed once (Theta(Nd) elements),
and there are Theta(Nd/M) such passes. Sparse note: with s = N^-1/2 the cost is Theta(N sqrt(N)); with s = N^-1 log N it is
Theta(N log N).

Measured (REPORTED unless noted):

| Result | Value |
|--------|-------|
| Fig. 2 left: GPT-2 medium attention, fwd+bwd, A100 | standard 66.6 GFLOPs, 40.3 GB HBM R/W, 41.7 ms; FlashAttention 75.2 GFLOPs, 4.4 GB, 7.3 ms |
| Fig. 2 middle: block size 64 -> 512 | HBM accesses fall, runtime falls until about 256, then limited by arithmetic; larger blocks do not fit SRAM |
| Fig. 2 right (N=4K): block-sparse | runtime improves in proportion to sparsity |
| Fig. 1 right: attention on GPT-2 | 7.6x speedup over PyTorch attention |
| BERT-large to 72.0% MLM accuracy, 8xA100, 10 runs (Table 1) | Nvidia MLPerf 1.1 20.0 +/- 1.5 min; FlashAttention 17.4 +/- 1.4 min (15% faster) |
| GPT-2 small, OpenWebText, 8xA100 (Table 2) | HuggingFace 9.5 d (1.0x), Megatron-LM 4.7 d (2.0x), FlashAttention 2.7 d (3.5x); perplexity 18.2 for all |
| GPT-2 medium (Table 2) | HuggingFace 21.0 d, Megatron-LM 11.5 d (1.8x), FlashAttention 6.9 d (3.0x); ppl 14.2 / 14.3 / 14.3 |
| Longer context (Table 4, GPT-2 small) | Megatron 1k ctx 4.7 d, ppl 18.2; FlashAttention 1k 2.7 d (1.7x); 2k 3.0 d, ppl 17.6; 4k 3.6 d (1.3x), ppl 17.5 |
| Long-Range Arena average accuracy (Table 3) | Transformer 59.3; FlashAttention 59.8 (2.4x); block-sparse 59.6 (2.8x); Linformer 54.9 (2.5x); Performer 58.9 (1.8x); Reformer 57.6 (1.3x) |
| Long documents (Table 5, micro F1) | MIMIC-III 52.8 (512) -> 57.1 (16K); ECtHR 72.2 (512) -> 80.7 (8K), 79.2 (16K) |
| Path-X (16K tokens) / Path-256 (64K) (Table 6) | FlashAttention 61.4 / fails; block-sparse 56.0 / 63.1 |
| Attention memory (Table 21, MB, N=1024 / 4096 / 65536) | PyTorch 1184 / 17024 / out of memory; FlashAttention 209 / 836 / 13376 |
| Attention runtime, fwd+bwd with dropout+mask, N=1024 (Table 11 partial) | PyTorch 8.29 ms; Megatron 4.21 ms; FlashAttention fused |
| Forward runtime N=65536 (Table 9) | FlashAttention 2682.35 ms; block-sparse FlashAttention 13.34 ms; Linformer 52.39 ms |
| Versus Apex FMHA, short sequences (Table 7) | FlashAttention about 4% slower at N=128, 8% faster at 256, 5% faster at 512 overall; faster forward, slower backward because FMHA stores the matrix and FlashAttention recomputes |
| Speedup by GPU (Appendix E.5) | A100 2-4x; RTX 3090 2.5-4.5x (lower bandwidth, about 900 GB/s vs 1.5 TB/s); T4 less (smaller SRAM, smaller blocks) |

Observations: the A100 speedup is larger with dropout and masking (more fusion); at head dimension 128 blocks are smaller
so speedup is smaller; the T4 result "matches the IO complexity analysis" (smaller M, more passes). Memory is linear in N
(up to 20x better than exact baselines, Fig. 3). The ratio of FlashAttention to approximate methods crosses over between
N=512 and 1024 (approximations win beyond), but block-sparse FlashAttention beats all of them at every length.

### 1c. What it says about the memory wall

"On modern GPUs, compute speed has out-paced memory speed, and most operations in Transformers are bottlenecked by
memory accesses." Operations are classed by arithmetic intensity: compute-bound (large matmul, many-channel
convolution) vs memory-bound (elementwise, softmax, reductions, norms). The paper's central claim: approximate-attention
papers reduced FLOPs but "tend to ignore overheads from memory access (IO)", so many show no wall-clock speedup. HBM
access count is "the primary factor affecting runtime" (Fig. 2 caption). Appendix A cites the older lineage: external-memory
I/O complexity (Aggarwal-Vitter), working-set model, data locality, Roofline.

### 1d. Fit with the founder's rule

- **Conflicts:** the inner loop is two dense matmuls (Q_i K_j^T and P~_ij V_j); softmax needs exp and a division by l.
  Not usable as an operator. FlashAttention-the-algorithm is matrix-multiplication-in-SRAM.
- **Transfers:** (i) the I/O cost model (count slow-tier reads and writes, minimise them over fast-memory size M);
  (ii) *loop order* - hold a block of one operand resident, stream the other past it; (iii) *running summary instead of
  materialised intermediate* - the (m, l) pair is a counter-like state; L already keeps small running state; (iv)
  *recompute rather than store* when recompute is cheap and a re-read is expensive - for L, a clause vote that is a
  popcount of a few words is cheaper to recompute than to fetch from DRAM; (v) *block sparsity* - only touch nonzero
  blocks; cost scales with the fraction s (Proposition 4: Theta(Nd + ... s)). The "Nd" floor in Proposition 4 is the
  lesson that the output itself must still be written; L's output per decision is a few bytes, so the floor is tiny.
- The paper also writes (Appendix D.2) that sparse MLP layers are often memory-bound and not faster in proportion to
  sparsity, and that IO-aware implementations should fix this. That is the closest statement to L's use case.

### 1e. Limitations (stated and observed)

Requires a hand-written CUDA kernel per variant, not portable across GPU generations (Section 5, "Compiling to CUDA");
only attention is IO-optimised, other layers remain; single-GPU analysis, no multi-GPU tier; the lower bound is only over
a range of M, not parameterised; block size is bounded by SRAM, and speedup falls where SRAM is small (T4) or d is large.
Not measured: energy.

## 2. FlashAttention-2 (2307.08691)

### 2a. Mechanism

FlashAttention reaches only 25-40% of A100 peak FLOPs/s (forward 30-50%, backward 25-35%); well-tuned GEMM reaches
80-90%. FlashAttention-2 keeps the same I/O pattern and changes the *work partitioning*, in three ways:

1. **Fewer non-matmul FLOPs.** A100 peak is 312 TFLOPs/s for FP16/BF16 matmul but 19.5 TFLOPs/s for non-matmul FP32, so a
   non-matmul FLOP costs 16x more. Two changes: keep the output *un-scaled* during the loop and divide by l once at the end
   (Algorithm 1 lines 10 and 12), and store only the logsumexp L = m + log l instead of both m and l for backward.
2. **Parallelism over sequence length.** The loop order is swapped: the *outer* loop is over row blocks (Q_i), the inner
   over K_j,V_j (Algorithm 1). Row blocks are independent, so one thread block per row block (forward) is scheduled across
   SMs; the earlier version used one thread block per (batch, head), which under-fills the 108 SMs for long sequences with
   small batch. In backward, one thread block per column block, with atomic adds to update dQ (the only shared state).
3. **Warp-level split.** Within a thread block, FlashAttention split K,V across 4 warps ("split-K"), requiring every warp
   to write partials to shared memory, synchronise and add. FlashAttention-2 splits Q across warps, keeping K,V visible
   to all, so no cross-warp communication in the forward pass.

Also: causal masking skips blocks entirely above the diagonal (about half of blocks, 1.7-1.8x speedup versus no mask) and
applies the mask only to the diagonal block; multi-query and grouped-query attention are supported by index manipulation
instead of duplicating K,V heads. Block sizes {64, 128} x {64, 128} chosen by hand per head dimension; larger blocks cut
shared-memory traffic but raise register use, and past a point register spilling hurts.

### 2b. The numbers (REPORTED; A100 80GB SXM4 unless noted)

| Result | Value |
|--------|-------|
| Headline | about 2x over FlashAttention; 1.7-3.0x over FlashAttention, 1.3-2.5x over Triton FlashAttention, 3-10x over PyTorch |
| Peak | up to 230 TFLOPs/s (73% of 312) forward; up to 63% backward |
| Fwd+bwd, head dim 64, no causal, N=512 .. 16k | per-length TFLOPs/s are in Fig. 4 bar charts only; exact values are **UNVERIFIED** (garbled in text extraction) |
| H100, same code, no TMA or new tensor-core instructions | up to 335 TFLOPs/s (Fig. 7); authors expect another 1.5-2x with new instructions |
| End-to-end (Table 1, 8xA100) GPT3-1.3B 2k ctx | 142 TFLOPs/s without FlashAttention, 189 with, 196 with FlashAttention-2 |
| GPT3-1.3B 8k ctx | 72 / 170 / 220 |
| GPT3-2.7B 2k ctx | 149 / 189 / 205 |
| GPT3-2.7B 8k ctx | 80 / 175 / 225 TFLOPs/s (72% model FLOPs utilisation) |
| Cost framing | "train models with 16k context for the same price as previously training an 8k model" |

FLOP accounting used: forward = 4 x seqlen^2 x head_dim x heads (halved for causal); backward = 2.5 x forward (5 matmuls
vs 2, because of recomputation).

### 2c. Memory wall

This paper is about the *second* wall: after HBM traffic is fixed, the next limiter is **on-chip data movement** -
shared-memory reads/writes between warps, and idle SMs. The authors treat SRAM and registers as a tier with its own cost
and design to reduce traffic *inside* the chip. The same logic as paper 1, one level down.

### 2d. Fit with L

- **Conflicts:** everything is built on tensor-core matmul; the 16x matmul/non-matmul asymmetry is a GPU artefact. L has
  no matmul units to feed, so its equivalent bottleneck is irregular small-integer work and table lookups.
- **Transfers:** (i) *do not give two workers a shared partial result if you can partition so they never talk* (Q split
  across warps = partition the class set across lanes, each lane owns its classes' counters and only the final argmax is
  shared); (ii) *parallelise over the dimension that is long* (sequence length here; classes or clause lists for L);
  (iii) *skip dead blocks* (causal skip = skip classes pruned by the recall stage); (iv) *sum once at the end* (un-scaled
  accumulation, normalise at the end = accumulate integer votes, compare once).

### 2e. Limitations

Manual per-head-dimension tuning (auto-tuning left to future work); H100 features unused; benchmark numbers read from
bar charts; still a dense-matmul algorithm; no bytes-moved table (the I/O argument is inherited from paper 1).

## 3. Monarch (2204.00595)

### 3a. Mechanism

A Monarch matrix of size n = m^2 is M = P L P^T R, where L and R are block-diagonal with m blocks of size m x m and P is
the fixed "reshape to m x m, transpose" permutation. Multiplying x by M: view x as an m x m tensor, do a *batched* small
matmul along one axis (R), permute, batched small matmul along the other axis (L), permute back. Parameters 2n sqrt(n);
FLOPs O(n sqrt(n)) (more than the O(n log n) of a butterfly, but it maps to batch-matrix-multiply, which GPUs run well).
Derivation from butterfly matrices: multiply the first (log2 n)/2 butterfly factors into L and the last into R (inspired by
the 4-step FFT). Class MM* (products M1 M2*) represents convolution, Hadamard, Toeplitz, AFDF; (MM*)^2 represents Fourier,
sine and cosine transforms, Fastfood, ACDC (Proposition 3.2). Rectangular and larger-block versions are in Appendix C
(UNVERIFIED by us).

**Projection (Theorem 1, Algorithm 1).** Reshaped as a 4-D tensor, M_ljki = L_jlk R_kji is m^2 independent rank-1
matrices, so the closest Monarch matrix to any dense matrix A is obtained by a rank-1 SVD of each m x m slice; O(n^{5/2}),
an exact analytic optimum for a nonconvex problem (analogous to Eckart-Young). Theorem 2 factorises MM* matrices under
mild assumptions, O(n^{5/2}).

**Three training modes.** (1) End-to-end: swap the attention projections and FFN weights for Monarch (number of blocks 2
to 4, 25-50% of dense parameters). (2) Sparse-to-dense, "reverse sparsification": train with Monarch for 90% (GPT-2) or
70% (BERT) of the iterations, then multiply out L and R into dense matrices and finish densely. (3) Dense-to-sparse:
project pretrained dense weights (BERT) onto Monarch and fine-tune.

### 3b. The numbers (REPORTED; wall-clock on V100 for ImageNet and WikiText-103, A100 for BERT)

| Experiment | Dense | Monarch |
|------------|-------|---------|
| Mixer-S/16 ImageNet (Table 1) | 74.0%, 18.5M, 3.8 GFLOPs | 73.7%, 7.0M, 1.5G, 1.7x |
| Mixer-B/16 | 77.7%, 59.9M, 12.6G | 77.8%, 20.9M, 5.0G, 1.9x |
| ViT-S/16 | 79.4%, 48.8M, 9.9G | 79.1%, 19.6M, 3.9G, 1.9x |
| ViT-B/16 | 78.5%, 86.6M, 17.6G | 78.9%, 33.0M, 5.9G, 2.0x |
| GPT-2 small WikiText-103 (Table 2) | ppl 20.6, 124M, 106G | 20.7, 72M, 51G, 1.8x |
| GPT-2 medium | ppl 20.9, 355M, 361G | 20.3, 165M, 166G, 2.0x |
| GPT-2 medium OpenWebText, reverse sparsification (Table 6) | ppl 18.0, avg class. acc 38.9 | 18.0, 38.8, 2x faster |
| BERT-large pretraining total, 8xA100-40GB (Table 7) | HuggingFace 84.5 h, Megatron 52.5 h, Nvidia MLPerf 1.1 30.2 h (29.3 h with DeepSpeed) | Monarch 23.8 h |
| BERT GLUE fine-tune (Table 8) | base 78.6, 109M, 11.2G; large 80.4, 335M, 39.5G | base 78.3, 55M, 6.2G, 1.5x; large 79.6, 144M, 14.6G, 1.7x |
| Navier-Stokes, error at nu = 1e-3 / 1e-4 / 1e-5 (Table 3) | FNO 0.017 / 0.178 / 0.155 | Monarch-NO 0.010 / 0.145 / 0.136 (up to 40% lower) |
| MRI, 2x acceleration (Table 4), pSNR dB echo 1 / echo 2 | SENSE 32.8 / 35.4 | mSENSE 34.3 / 36.6, SSIM 0.886 / 0.882; mSENSE has 57.5K trainable parameters, 137x fewer than U-Net (7.8M) |
| MRI few-shot, N=1 scan (Table 5) | U-Net 29.4 / 34.4 dB | mSENSE 33.8 / 36.0 dB |

The BERT comparison uses Nvidia's MLPerf optimisations (list in Appendix E.4: compute prediction only for masked tokens,
remove padding, fused FMHA kernel, fused matmul+bias, fused dropout+residual, ZeRO stage 1), i.e. the baseline is already
a heavily fused and IO-aware stack, and Monarch still wins 23%. The paper notes its BERT number is not an official MLPerf
submission (it times both phases, MLPerf times only phase 2).

### 3c. Memory wall

Here the argument is about *hardware efficiency of sparsity*: "most sparse training methods slow down training in
wall-clock time" because entrywise sparsity has irregular memory access that does not map to block-oriented hardware;
structured matrices that "are efficient in theory" fail on GPUs because dense matmul is so well optimised (the "hardware
lottery", cited from the FlashAttention appendix). Monarch is parameterised as two block-diagonal factors precisely so that
each factor is a *batch of small dense blocks* that load into fast memory and run on the existing batch-matmul path. The
FLOP reduction (about 2.1-2.5x in Tables 1 and 2, DERIVED) and the speedup (1.7-2.0x) are of similar size, so here the saving is
in parameters read (60-65% fewer weights for ViT/Mixer, 42-54% for GPT-2) as much as arithmetic. The paper does not
break time into memory vs compute (UNVERIFIED).

### 3d. Fit with L

- **Conflict:** the operator is a matrix-vector product with learned block-diagonal factors, plus training by gradient
  descent; reverse sparsification and projection are both training-time linear algebra. Excluded by the founder's rule
  ("no dense matrix-vector products, ternary or not"; block-diagonal dense blocks still are dense matvecs inside each
  block). Do not import Monarch into the L accelerator.
- **Transfers (as principles, not operators):** (i) *match the sparsity granularity to the hardware's fetch granularity* -
  a structured sparse object whose nonzeros come in blocks that equal a memory burst or an SRAM row is fast, scattered
  nonzeros are not; L's counting rows and clause lists should be stored so that "active" means "a contiguous run of
  bytes"; (ii) *a permutation is free* (P is a fixed stride pattern) - L can use fixed hash/stride layouts to turn a
  scattered access into a streaming one; (iii) *cost scales with the number of blocks touched*, the same message as
  Proposition 4 of paper 1.

### 3e. Limitations

Needs n = m^2 (squares, shape constraint called out for MRI), the block count is tuned by hand (2 to 4); projection cost
O(n^{5/2}); speedups are measured on V100 and A100 against the dense baselines of the time; the BERT result is not an
official benchmark; D2S fine-tuning is shown only as a proof of concept on BERT and GLUE; no bytes-moved accounting.

## 4. SambaNova SN40L (2405.07518)

### 4a. Mechanism: streaming dataflow, three memory tiers, Composition of Experts

**Composition of Experts (CoE).** A router model assigns each prompt to one or a few independent expert models
(fine-tuned separately, possibly on different architectures). In the deployed Samba-CoE, router and experts are all derived
from Llama2-7B: 150 experts, over 1 trillion parameters in total. Compared with a Mixture of Experts, a CoE's experts are
trained independently and a CoE can contain MoEs. Per request: (1) run the router; (2) copy the chosen expert's weights
from DDR into HBM; (3) run the expert for many decoding steps. The expert's weights are read many times during
autoregressive decoding - "model-level temporal locality" - so one swap amortises over all generated tokens.

**What lives where (Table II, Fig. 9).**

| Tier | Capacity per socket | Bandwidth | Contents in Samba-CoE |
|------|--------------------|-----------|-----------------------|
| On-chip PMU SRAM (1040 Pattern Memory Units) | 520 MiB | "hundreds of TB/s" aggregate (figure not given as one number) | tiles of the kernel in flight, stage buffers between fused operators, intermediates |
| Co-packaged HBM | 64 GiB | 1.8 TB/s (Table II); "about 2 TB/s" in the text | router weights (always), the "current" expert(s), KV cache, activations; a software-managed cache tier between DDR and SRAM |
| DDR DRAM (pluggable DIMMs) | up to 1.5 TiB | over 200 GB/s | weights of all 150 experts (cold set) |

Chip: TSMC 5 nm, 2.5D CoWoS, two dies per socket, die size under 650 mm^2 (Table II), under 2 GHz, 638 BF16 TFLOPs, 1040 PCUs
(Pattern Compute Units: systolic or SIMD) and 1040 PMUs; PCU supports FP32, BF16, INT32 in SIMD. Both HBM and DDR are
software-managed address spaces (not caches). Eight sockets form a node; a node loads DDR to HBM at over 1 TB/s in
aggregate. Peer-to-peer links stream between sockets without touching DDR or HBM.

**Streaming dataflow and spatial fusion (Section III-A, Fig. 3, 4, Table I).** Instead of launching one kernel per
operator, the compiler maps a whole sub-graph spatially: operators become stages of a coarse-grained pipeline, each on
its own PCUs, with PMU "stage buffers" between them; tiles of the tensor stream through. Transpose is folded into the
buffer's read/write access pattern (diagonally striped bank layout lets the same tensor be read normally or transposed at
full bandwidth). Hardware needs, in the authors' list: composable memory units (programmable address interleave across
PMUs), high-bandwidth flexible address generation, systolic plus streaming compute, one-to-many / many-to-one routing with
reordering (sequence IDs in packets). On a GPU, the paper argues, full fusion fails for three reasons: a transpose forces
cross-SM data exchange through shared cache and HBM because the grid is fixed per kernel; SRAM too small, so the
transpose output goes to HBM; no way to pipeline many small (32x32x32 or smaller) matmuls.

**Table I (REPORTED), operation intensity of a Monarch-FFT example:** no fusion 39.5 ops/byte; Gemm0-Mul-Transpose fused
102.6; fully spatially fused 410.4. A100 balance is about 300 TFLOPS / 2 TB/s = 150 ops/byte, so the first two rows are
memory-bound and the last is compute-bound. (The example is the decomposed FFT of the FlashFFTConv work, which uses
Monarch-style factorisation; this is the link back to paper 3.)

**Software memory management (Section V).** Static symbol-lifetime analysis (no dynamic allocation, no pointer aliasing)
lets the compiler reuse HBM addresses for non-overlapping symbols (garbage collection at compile time). If it still does
not fit, symbols are spilled to DDR in order of smallest aggregate transfer size first; weights keep HBM priority, large
activations can spill. A lightweight dynamic manager runs at the boundary of an entire expert: each compiled binary
declares its HBM and DDR needs, all expert memory is allocated in DDR, "activation" copies the HBM-intended segments,
LRU eviction from HBM, read-only symbols are not copied back. A kernel-launch orchestrator in hardware (AGCU) can replace
host-software scheduling.

### 4b. The numbers (REPORTED; SN40L Node numbers measured, DGX numbers ESTIMATED by the authors from published model
latencies and "optimistic" switching estimates, because Samba-CoE was not deployed on DGX)

| Result | Value |
|--------|-------|
| Fusion speedup over unfused baseline, 8 sockets (Fig. 10) | 2x to 13x; FlashFFTConv 13x (single kernel launch); prefill, training and sparseGPT 1.5x to 3x; decode 1x to 13x (Mistral highest) |
| Hardware-orchestrated launch (Fig. 10) | decode 1.4x to 8x extra; prefill/training at most 1.1x |
| Kernel launches (Fig. 11) | llama7B-4k prefill 11x fewer when fused; ratios shown for others, some above 100 (read from a figure; exact values **UNVERIFIED**) |
| Llama 3.1 on 16 sockets, BF16, 8K sequence (Table IV) | 405B: 129 tokens/s/user; 70B: 457; 8B: 1042 |
| HBM bandwidth use | over 85% with dataflow; the paper says optimised H100 implementations rarely exceed 50% |
| Under 50 experts, 20 tokens (Table V) | SN40L Node 2.0x faster than DGX A100 and 1.5x than DGX H100 (expert execution only); 200 tokens: 3.2x and 2.3x |
| Over 50 experts, BS=8, 20 tokens | 6.6x vs A100, 3.7x vs H100 |
| BS=1, 20 tokens | 4.8x / 2.8x |
| BS=8, 200 tokens | 4.2x / 2.7x |
| BS=1, 200 tokens | 3.9x / 2.6x |
| Expert switching time | 31x faster than DGX A100 (32 GB/s host-to-GPU), 15x (abstract says 15x to 31x) faster than DGX H100 (64 GB/s) |
| Capacity | 150 experts: both DGX systems run out of memory; one SN40L Node holds up to 850 experts at TP8 latency; matching that with all experts in GPU HBM needs 19 DGX nodes (machine footprint reduced "up to 19x") |
| Per-socket capacity | about 2.5x the aggregate memory capacity per socket of NVIDIA GH200 |
| Costs quoted from outside | GPT-4 training about 78 million USD, Gemini Ultra about 191 million USD (cited from the AI Index) |

DERIVED check: switching a 7B BF16 expert is about 14 GB (7e9 x 2 bytes). At 32 GB/s that is about 0.44 s per switch; at
64 GB/s about 0.22 s; at the node's over 1 TB/s about 14 ms or less. The authors' 31x and 15x are in line with the bandwidth
ratios (1000/32 = 31, 1000/64 = 15.6). The speedup at BS=8 is bigger because eight prompts may need eight different
experts, so switching is a larger share of the time.

Two cautions the authors state: the DGX figures are modelled, optimistic for DGX, and assume the whole HBM and host memory
holds weights; the unfused baseline is SambaNova's own, not a tuned GPU baseline.

### 4c. Memory wall

Abstract and introduction: "The disproportionate increase in compute-to-memory ratio of modern AI accelerators has created
a memory wall." Peak ratio: an A100 does about 300 TFLOPS against about 2 TB/s, so any kernel under about 150 ops/byte is
memory-bound; small models (the CoE experts) have lower operational intensity than monolithic LLMs, so they are *more*
exposed. Autoregressive decoding "has much lower compute and operational intensity" than prefill and is dominated by loading
weights. Fusion "enables using HBM bandwidth only for streaming weights and KV cache values", i.e. the only bytes that
cross the HBM boundary during decode are the ones that must. Three requirements named in the introduction: aggressive
fusion; high-bandwidth memory for temporal locality; high-capacity memory to hold many models cheaply.

### 4d. Fit with L

- **Conflicts:** the PCUs are systolic GEMM arrays, the experts are dense 7B transformers, and the headline fusion example
  is a chain of GEMMs. The dense-matmul content is excluded by the founder's rule. The architecture is a general
  reconfigurable dataflow machine (mesh of compute and memory units) - far from a counting chip.
- **Transfers, in order of usefulness:**
  1. **Hot/cold split with a software-managed middle tier.** Cold set in the cheap, large tier; hot set resident in the fast
     tier; swap at the granularity of one self-contained unit (an expert there, a class row or domain table in L). No
     hardware cache: the compiler or runtime decides. For L the "temporal locality of an expert" has a close analogue: a
     stream of inputs from the same domain hits the same classes repeatedly.
  2. **Sparse activation in capacity terms.** CoE touches 1 of 150 experts per request, i.e. about 0.67% of 1T parameters
     (DERIVED: 1/150) in the hot tier while the other 99.3% sit in DDR. This is exactly "only a fraction of parameters is
     touched per input", and it is the reason the node holds 850 experts where HBM-only systems need 19x the machines.
  3. **Fuse the whole decision into one pass.** Decoder layers fused into a single kernel call; intermediates stay in
     PMU stage buffers; the only HBM traffic is weights and KV. For L: recall, vote accumulation and argmax in one pass,
     with only the table bytes and the input crossing a tier boundary.
  4. **Static analysis of lifetimes and of bandwidth.** Compiler-side bandwidth model (they call it "essential") and
     symbol-lifetime reuse. L's tables have no dynamic allocation, so the same static plan is possible.
  5. **A router first.** A cheap router selects the expert before any large memory is touched. For L this is the hash
     recall of candidate classes.
  6. **Bandwidth-utilisation as a metric.** 85% of peak HBM bandwidth used for useful bytes is the figure of merit;
     50% was the stated GPU practice.

### 4e. Limitations

The DGX comparison is modelled, not run; the node is a very large system (eight sockets, 520 MiB SRAM per socket, 64 GiB
HBM) with no power figure in the paper; DDR bandwidth is only 200 GB/s, so a miss in HBM is expensive (about 9x slower
than HBM at 1.8 TB/s: DERIVED 1800/200); CoE only helps if requests concentrate on a few experts at a time (the
design relies on temporal locality and LRU) and the router is accurate; CoE and MoE are orthogonal but CoE experts must be
trained and maintained separately; Table V's DGX cases rely on published latency numbers from other sources. The paper's
Figure 1 (switching vs execution breakdown) and Figures 12-13 (latency and footprint curves) are figures only: values
**UNVERIFIED**.

## 5. Cross-paper synthesis: what memory movement management looks like at scale

| Idea | FlashAttention | FlashAttention-2 | Monarch | SN40L |
|------|----------------|------------------|---------|-------|
| Unit of movement | tile of Q, K, V (block in SRAM) | same, plus per-warp slice | block of a block-diagonal factor | whole expert (about 14 GB) and tiles in a fused pipeline |
| What is kept resident | K_j, V_j block while Q streams | Q_i block while K, V stream | factor blocks | current expert in HBM; stage buffers in SRAM |
| What is never stored | N x N matrices S, P | same, plus unscaled O | the dense matrix | intermediates between fused operators |
| Recompute vs re-read | recompute S, P in backward | same | reconstruct dense by multiplying factors (reverse sparsification) | n/a |
| Metric | HBM bytes, N^2 d^2 / M | fraction of peak FLOPs, shared-memory traffic | parameters and wall-clock | HBM bandwidth fraction, switch time, machine count |
| Energy measured | no | no | no | no |

Common structure: (1) identify the tiers and their capacity and bandwidth; (2) choose a loop order so the large operand
streams once past a resident block; (3) do all work for a block while it is resident; (4) keep summaries (m, l, L)
instead of intermediates; (5) put the cold bulk in a capacity tier and swap in units that amortise over many uses.

What none of them provides, and L must supply itself: a joule-per-byte constant. The Roofline-style comparison in
SN40L Table I (39.5, 102.6, 410.4 ops/byte) is the closest thing to a cost model in the four papers.

## 6. The one concrete test or design rule for L

### Rule

**Give every L table a tier assignment and a bytes-per-decision budget before writing RTL.** Concretely:

- **Tier 1 (on chip, hot):** the recall index (hash signatures: one small signature per class), the per-class running
  counters for the current decision, and the clause lists of the classes currently active (hot rows). Small, fixed size.
- **Tier 2 (on-package or near memory, warm):** clause lists and counting rows of recently used classes.
- **Tier 3 (capacity, cold):** all other classes' rows, fetched only when the recall stage proposes them.
- **Unit of movement = one class row** (a contiguous run holding that class's clause index lists), so "active" equals
  "contiguous bytes", the Monarch/FlashAttention lesson. Swap policy: software-managed, LRU on classes, read-only rows are not
  written back (SN40L runtime). Fuse recall, accumulation and argmax into one pass so intermediates never leave tier 1.

### Test (small, runnable before any hardware)

Write a bytes-moved counter into the existing bit-exact software model and report, per decision, bytes read from each tier
for (a) a flat scan of all classes, (b) a hash-recalled top-k, with 10, 100 and 1,000 classes, on the real data. Pass
criterion: the tier-1-resident fraction of bytes and the ratio flat/recalled agree with the model below to within a
factor 2, and the accuracy of recalled top-k equals the flat scan's within the noise of the benchmark. This costs a
counter in the simulator, not new hardware.

### Cost model (MODELLED; every constant is an assumption of ours, not from the papers, and is to be replaced by the
measured values of the L Cortex configuration)

Assumptions: K = 100 clauses per class; each clause stores A = 20 included-literal IDs of 2 bytes plus 1 byte of weight,
so S = 41 bytes per clause; input has N_lit = 2,000 literal slots with F = 200 active (10%); inverted index (literal ->
clauses containing it) with a clause ID of 2 bytes up to 65,536 clauses and 3 bytes above; recall stage reads one 8-byte
signature per class and proposes k = 8 candidate classes (or all classes when C <= 8).

- Flat scan: B_flat = C x K x S.
- Event-driven inverted index over all classes: B_inv = (F / N_lit) x C x K x A x idbytes (postings for active literals only).
- Recalled top-k, dense within candidates: B_rec = 8C + min(k, C) x K x S.

| Classes C | Clauses total | B_flat | B_inv (event-driven) | B_rec (hash-recalled top-8) | flat / recalled |
|-----------|---------------|--------|----------------------|------------------------------|-----------------|
| 10 | 1,000 | 41,000 B (41 KB) | 0.1 x 10 x 100 x 20 x 2 = 4,000 B | 80 + 10 x 100 x 41 = 41,080 B (recall off, same as flat) | 1.0 |
| 100 | 10,000 | 410,000 B (410 KB) | 0.1 x 100 x 100 x 20 x 2 = 40,000 B | 800 + 8 x 100 x 41 = 33,600 B | 12.2 |
| 1,000 | 100,000 | 4,100,000 B (4.1 MB) | 0.1 x 1000 x 100 x 20 x 3 = 600,000 B | 8,000 + 8 x 100 x 41 = 40,800 B | 100.5 |

(Per-class counters, 1 byte per clause, stay on chip: 1 KB, 10 KB, 100 KB at 10, 100, 1,000 classes; at 1,000 classes this
is the tier-1 sizing driver, not the table bytes.)

Reading the table: flat scan grows linearly with the class count (4.1 MB per decision at 1,000 classes), the event-driven
inverted index cuts bytes by roughly the active-literal fraction (10x here) but still grows linearly in C; the recalled
top-k is flat at about 34-41 KB and takes over beyond about 10-20 classes. The three techniques map to the papers: event-driven
= block sparsity (Proposition 4, bytes scale with the nonzero fraction s); recalled top-k = CoE router (touch 1 of
many); fused single pass = FlashAttention/SN40L fusion. Multiply bytes by a per-tier pJ/byte constant once we have one:
the papers give none, so no energy number is claimed here. The first expected result is the shape (flat versus linear), not
the absolute bytes.

What to record when the test is run (journal entry): bytes read per tier per decision, tier-1 hit rate for the hot set at
each class count, accuracy of recalled top-k versus flat scan, and the break-even class count where recall beats flat scan.
Label: MEASURED once run on the simulator; MODELLED until then.

## 7. Limits and honest gaps in this note

- No energy numbers exist in the four papers; this note reports bytes, time and bandwidth fractions only.
- Monarch Appendices C and D (proofs) were skimmed, not verified. FlashAttention-2 per-length TFLOPs values in the bar
  charts are partly garbled in text extraction and are not tabulated. SN40L Figures 1, 10 (per-benchmark bars), 11, 12 and 13
  are figures only; only values stated in text and tables are quoted.
- SN40L DGX comparisons are the authors' own model, not a measurement. FlashAttention and Monarch speedups are against
  baselines of 2022 and 2023 and on V100/A100 hardware; they are not guaranteed to hold on current GPUs.
- The L cost model in section 6 is a design aid built on assumed class, clause and literal sizes. It has not been run.
- Authorship check: the SN40L PDF text shows company e-mail domains; any Stanford affiliation is not visible in the text
  (UNVERIFIED), though the task context says Stanford co-authors.

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
