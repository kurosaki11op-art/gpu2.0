---
title: Paper notes - state size, recall and throughput in efficient sequence models (Stanford)
tags: [l, research, papers, memory]
---

# State size, recall and throughput in efficient sequence models

Papers: H3 (arXiv 2212.14052), Zoology (2312.04927), Based (2402.18668), Mamba (2312.00752). Ids and titles were checked against the first page of each downloaded PDF on 25 Oct 2026. Text was extracted with pdftotext and read; the main body, every results table and the theory statements were read in full for all four. Long proof appendices were searched and sampled, not read line by line (listed under UNVERIFIED at the end). Numbers are quoted from paper text or tables and are all MEASURED by the authors on GPUs (A100 or H100) unless tagged DERIVED (our arithmetic from paper formulas or tables) or ESTIMATED (our reading, not a paper claim). Plots (Zoology Fig 2 and 6, Based Fig 2, 3 and 8) are images: their curves could not be read as numbers, only their axes and captions.

Why this matters for L: the L accelerator is attention-free and keeps a fixed state (delta-rule fast weights, integer spikes, hash recall). The founder's question is how big that state must be to remember and recall, and how the best Stanford-linked groups trade state bytes for recall and throughput. Short answer from these papers: recall of N independent facts needs on the order of N bits of state, no architecture escapes it, and the practical question is only how many bits of that state actually carry facts. Mamba is the exception to read carefully: Gu is the first author, but the paper is Carnegie Mellon and Princeton (Gu and Dao); the Stanford link is training and the H3 and S4 lineage.

## 0. The four papers in one table

| | H3 | Zoology | Based | Mamba |
|---|---|---|---|---|
| Role | first SSM layer built to solve recall and compare tasks | diagnosis: recall explains the gap, plus theory | the state-size versus recall tradeoff as a design axis | selective SSM, input-dependent forgetting |
| State per layer | m = 64 numbers per channel (SSM state size, Appx E.2); d x 64 | none new (analyses others) | (d+1) x D' per head, D' = 1 + 3d'/2 + d'^2/2 (Appx E.2) | D x N per block with D expanded (E=2), N = 16 |
| Write rule | shift SSM then outer product k v^T into a diagonal SSM (cumulative sum when A = 1) | not applicable | s_i = s_(i-1) + phi(k_i)^T v_i | h_t = Abar_t h_(t-1) + Bbar_t x_t, with Abar, Bbar, C functions of x_t |
| Read rule | multiply by Q elementwise | not applicable | y_i = phi(q_i) s_i / phi(q_i) z_i | y_t = C_t h_t |
| Recall bound stated | none general; toy construction uses one head per key | Omega(N) bits for gated recurrences with d up to sqrt(N); model dimension must grow with N for gated convolutions | Omega(N) bits for any causal recurrent model (Thm 3.1) | none in the paper (Based Cor F.13 applies it to Mamba) |
| Main recall result | 99.8 percent associative recall (seq 20, vocab 10) | 82 percent of the Pile gap is AR tokens (6.4 percent of tokens) | SWDE 64.45 vs 76.50 Transformer++ at 1.3b/50b | induction heads perfect up to 2^20 tokens (one key-value) |
| Needs dense matmul | yes (4 d x d projections, block FFT) | yes (BaseConv, attention) | yes (projections, GEMV in window, outer products) | yes (3ED^2 projection parameters per block) |

## 1. H3: Hungry Hungry Hippos (Fu, Dao, Saab, Thomas, Rudra, Re; Stanford)

### (a) Mechanism
Background. A discrete SSM is x_i = A x_(i-1) + B u_i, y_i = C x_i + D u_i, with state x_i in R^m, stacked in d parallel channels. Linear attention keeps S_i = sum_j phi(K_j) V_j^T (a d x d matrix) and z_i = sum_j phi(K_j), output O_i = phi(Q_i)^T S_i / phi(Q_i)^T z_i.

H3 replaces phi(K) by an SSM with a shift matrix and the cumulative sum S_i by an SSM with a diagonal matrix. For head dimension 1 the layer is Q ⊙ SSM_diag(SSM_shift(K) ⊙ V). Algorithm 1: project u to Q, K, V with three d x d matrices; pass K through the shift SSM; per head take the batched outer product K V^T (N x dh x dh); pass it through the diagonal SSM; multiply by Q; concatenate heads; output projection W_O.

- Shift SSM: A_(i,j) = 1 if i-1 = j else 0, so the state is a delay line [u_i, u_(i-1), ..., u_(i-m+1)]. It detects "the previous token was the key" (event detection).
- Diagonal SSM: A diagonal, initialised from HiPPO (S4D), so it remembers over the whole sequence. In the hand-built construction A_diag is all ones, so it is a running sum (an accumulator).
- Multiplicative interaction: gate 1 (K shifted times V) lets a value through only if the previous token was the key; gate 2 (Q times the diagonal SSM output) lets the stored value out only if the current token is the key.

State size per layer. SSM state size 64 for every model including the 2.7B (Appx E.2); hybrids use head dimension 1, pure H3 uses 8. So a layer holds about d x 64 numbers (DERIVED: 1024 x 64 = 65,536 for the 125M models, hidden 1024; 2560 x 64 = 163,840 for the 2.7B, hidden 2560). A hybrid also keeps two attention layers whose KV cache grows with length (layers 1 and 7 at 125M, 1 and 13 at 355M and 1.3B, 10 and 21 at 2.7B).

Recall mechanism (Fig 1 middle, Appx D.1). Toy language: 4 keys, 4 values, sequence of key-value pairs ending with a key. The model uses d = 8, m = 2, H = 4 heads, one head per key (W_Q and W_K assign key k_i to head i), value encoded in binary and sent to all heads, shift SSM then gate then accumulator then gate. The output of head i is a multiple of the binary code of f(k_i). Two things to note: it recalls one value per key only if each key has its own head (state grows with the number of distinct keys) and the accumulator adds if a key appears twice (multiple of the code).

### (b) Numbers
- Synthetics, 2-layer models (Table 2; MEASURED): Induction Head (length 30, vocab 20): random 5.0, S4D 35.6, Gated State Space 6.8, H3 100.0, attention 100.0. Associative Recall (length 20, vocab 10): random 25.0, S4D 86.0, GSS 78.0, H3 99.8, attention 100.0.
- OpenWebText perplexity, 12 layers, about 125M, 50B tokens (Table 3): H3 21.0, H3 hybrid with 2 attention layers 19.6, S4D 24.9, GSS 24.0, GSS hybrid 19.8, Transformer 20.6. The hybrid beats the Transformer by 1.0 perplexity; pure H3 is within 0.4.
- Pile, OpenWebText, WikiText-103 perplexity (Table 4): hybrid H3-125M 8.8 / 20.9 / 23.7 against GPT-Neo-125M 9.4 / 22.6 / 26.3; hybrid H3-355M 7.1 / 15.9 / 16.9; hybrid H3-1.3B 6.0 / 12.4 / 12.5 against GPT-Neo-1.3B 6.2 / 13.1 / 13.3; hybrid H3-2.7B 5.4 / 11.0 / 10.6 against GPT-Neo-2.7B 5.7 / 11.7 / 11.5. Trained on 400B Pile tokens.
- SuperGLUE average, zero-shot (Table 5): hybrid H3 53.9 / 54.7 / 56.5 / 56.8 at 125M / 355M / 1.3B / 2.7B against GPT-Neo 50.8 / (none at 355M) / 52.1 / 54.6 and OPT 50.1 / 53.1 / 52.9 / 55.5. 3-shot (Table 6): hybrid 53.7 / 52.6 / 53.0 / 55.5. The authors call these promising initial results.
- Pure H3-125M is not as good: zero-shot SuperGLUE average 40.4 against 53.9 for the hybrid (Table 14, with MultiRC 4.6 and ReCoRD 15.8). Recall of the full model needs the two attention layers.
- Generation throughput on A100 80GB, 1.3B, batch 64, 128 new tokens (Table 7): Transformer 1340 / 770 / 520 tokens/s at prompt length 512 / 1024 / 1536; hybrid H3 1980 / 1580 / 1240. Ratio DERIVED 1.48 / 2.05 / 2.38. The gap widens with length because the Transformer KV cache grows and the SSM state does not (the hybrid's two attention layers still grow).
- Training speed (FlashConv): 5.8 x faster than a Transformer on Long Range Arena with S4 (Table 8), 2.4 x for FlashAttention; kernel fusion up to 3.4 x, block FFT up to 2 x, state passing 2.3 x at lengths from 16k.
- Length extrapolation (Table 12): trained on AR sequences of length 20, accuracy 99.8 at 20 and 98.4 at 40.
- Data scaling (Table 13), 125M on the Pile: 5B / 10B / 15B tokens: hybrid 11.8 / 10.7 / 10.2, Transformer 12.7 / 11.3 / 10.7.

### (c) Memory against amount to be recalled
No bound in the paper. The only statement is Proposition 1: time O(d^2 N + d N log N), space O(d N) for training with head dimension O(1). At inference the SSM state is constant in N (d x m). The toy construction shows the practical scaling: one head (one slot) per key, with state size m fixed per head. So recall capacity of H3 is limited by the number of heads times per-head state, not by sequence length, and the paper never measures where it saturates. ESTIMATED reading: H3 at m = 64 and head dimension 1 holds at most about d x 64 scalars, shared by all facts in the context.

### (d) Operations
Dense matmul / multiplies (conflict with founder's rule): Q, K, V, O projections (4 x d x d, O(d^2 N)); the FFT convolution as block-diagonal matmuls on tensor cores (FlashConv, A100 312 TFLOPs fp16 vs 20 fp32 given as the motivation); multiplicative gates (elementwise products); diagonal SSM multiply-add per step.
Lookup / scan / counter style: the shift SSM is a delay line (no arithmetic, only moves); the A = 1 diagonal SSM is a running sum (counter); the gate with a one-hot key is an AND. The hand-built associative-recall circuit is therefore a delay line, an AND, an accumulator and an AND per key, which is a counting-table operation in disguise.

### (e) Limitations
Pure H3 trails (21.0 vs 20.6 perplexity; 40.4 vs 53.9 SuperGLUE zero-shot), recall still needs two attention layers whose cache grows. Scale reached 2.7B only. Experiments of recall use a vocabulary of 10 to 20 tokens and a single query; the Zoology paper (below) shows this hides the real failure. The state size 64 was not ablated against recall.

## 2. Zoology: Measuring and Improving Recall in Efficient Language Models (Arora, Eyuboglu, Timalsina, Johnson, Poli, Zou, Rudra, Re; Stanford)

### (a) Mechanism and framework
Zoology studies gated-convolution sequence mixers (H3, Hyena, RWKV, long convolution) against attention. Convolution: y[i] = sum_j k[j] ⊙ u[i-j] with an input-independent filter k of length N; gating is elementwise multiplication. Because the filter is fixed by the weights, a gated convolution mixes tokens at fixed distances, whatever the input.

BaseConv (Definition 4.1): y = u W + b1 ⊙ (h * u) + b2 with W in R^(d x d), h in R^(N x d). Theorem 4.2: any arithmetic circuit of size s and depth Delta has an equivalent BaseConv with O~(s Delta) parameters and O~(Delta) layers; so BaseConv stands for H3, Hyena, RWKV and RetNet (Hyena and BaseConv simulate each other with constant blowup).

Task. Multi-Query Associative Recall (MQAR, Definition 3.1): a sequence of key-value pairs followed by many queries at varying positions; for each query that matches an earlier key, output the following token. The old single-query form (one query at a fixed place, vocabulary under 50) is solved by H3 and Hyena, which is why the gap was missed.

Measuring recall in real text. An "AR hit" is the last token of a bigram that appeared earlier in context and occurred at most 1,250 times in training (so it was not simply memorised). AR hits are 6.4 percent of Pile tokens. The share of the perplexity gap due to AR is delta log(ppl_AR) |T_AR| over delta log(ppl) |T|.

Fixes tested (Section 5): hybrids of BaseConv with three attention layers (6.3 percent of layers at 354M and 10 percent at 168M), where attention is applied only to selected tokens f(u)[i]: full, random (Bernoulli), programmatic (f = 1 if the token id occurred earlier, a membership test on raw token ids) or learned (sigmoid score, top-k, k = 256).

### (b) Numbers (all MEASURED, validation perplexity on the Pile, 10B tokens, ppl with NLL in parentheses in the paper)
Table 1 (and Table 4): overall / AR hits / other tokens; "% gap from AR".
- 125M scale: attention (125M) 11.01 / 2.16 / 12.45; long conv (128M) 16.98 / 25.62 / 16.46 (40.1 %); H3 (168M) 12.06 / 6.75 / 12.60 (88.4 %); Hyena (158M) 11.60 / 5.00 / 12.28 (100 %); RWKV (169M) 11.64 / 5.70 / 12.29 (100 %); RetNet (152M) 11.15 / 3.01 / 12.45.
- 360M scale: attention 9.44 / 1.98 / 10.62; long conv 13.13 / 13.27 / 13.12; H3 10.38 / 4.81 / 11.00 (65.8 %); Hyena 10.07 / 3.83 / 10.75 (98.2 %); RWKV 9.79 / 3.82 / 10.51 (100 %).
- 70M scale (Table 4): attention (73M) 12.99 / 2.41 / 14.76; H3 15.78 / 13.86; Hyena 15.13 / 9.00; RWKV 16.10 / 14.11.
- 1.4B, 50B tokens (Table 5): attention 8.19 / 1.91 / 9.86; Hyena 9.65 / 3.43 / 11.01. The 73M attention model reaches AR 2.41, better than the 1.4B Hyena at 3.43, with a model 20 x smaller.
- Gap is in rare bigrams (Appx G): at 350M, restricting to bigrams seen under 1,250 times the gap is 1.85 (Hyena) and 1.84 (RWKV) perplexity points; for bigrams seen once the gap is 12.0 and 13.2. Larger models memorise more training bigrams but do not recall better in context.
- 7B open models (Appx G, Fig 7): RWKV loses AR quality as the number of key-value pairs P grows from 16 to 256 (sequence length 1024), while Llama-2 stays flat. Plot only; values UNVERIFIED.
- Fixes (Table 2), overall / AR hits: at 360M BaseConv 11.01 / 5.98; plus programmatic selection 9.54 / 2.35; plus learned selection 9.59 / 2.61; plus full attention 8.59 / 1.95; plus random selection 12.94 / 6.17 (worse); attention 9.44 / 1.98. At 125M: BaseConv 12.90 / 8.68; programmatic 11.06 / 2.70; learned 11.06 / 3.20; random 12.13 / 5.33; full attention 9.57 / 2.01; attention 11.01 / 2.16. Programmatic selection closes 85 percent of the AR gap between BaseConv and attention at 360M; learned selection closes 72 percent with k = 256 positions; hybrid with full attention beats attention by 0.85 perplexity at 18 percent fewer FLOPs. Abstract: 97.4 percent of the gap closed.
- Appendix F (Table 4): Hyena with sliding window attention 64: AR 5.23; with window 256: AR 3.42 (Hyena alone 5.00 at 160M, so a short window barely helps and a long window helps a lot).
- Real text structure (Appx D.2): AR hits are common in ArXiv, GitHub and Stack Exchange (repeated names, commands, citations) and rarer in books and Wikipedia; the distance between a bigram and its earlier occurrence follows a power law, so most recalls are close but a heavy tail is far.

### (c) How memory must grow with what is recalled
- Gated convolution (Claim 1, Fig 2): with vocabulary 8,192, sequence lengths 64 to 512 and two layers, accuracy above 0.9 is only reached when model dimension d is at least N, so d must grow about linearly with sequence length, while attention solves MQAR with d = 64 at all lengths (plot reading from caption and text; individual points UNVERIFIED).
- Theory: attention solves MQAR with O(c^2) parameters and O(1) layers, independent of N (Proposition 4.3). A data-independent BaseConv needs O~(N log c) parameters but polylogarithmic layers (Theorem 4.4). With input-dependent filters and at most t distinct interaction distances, O(t N c) parameters and O(1) layers (Theorem 4.5).
- Recurrences: Corollary H.24 (via the one-way communication complexity of the index problem, Omega(n), Jayram et al.): a RetNet-type gated recurrence needs Omega(N) bits to solve AR when the model dimension d is at most sqrt(N). Experiment 2 (Fig 6): with N = 256 and key-value count varied through N/32, N/16, N/8, N/4, models of dimension 64, 128, 256 need more dimension as the number of pairs grows; sliding-window attention with window 32 works up to 16 pairs and degrades beyond, with window 8 it never works.
- Our reading (DERIVED): the lower bound for facts is linear in the number of independent key-value pairs; the only way to beat it is to throw information away (windows, selection), which costs recall exactly on the discarded pairs.

### (d) Operations
All mixers here use dense matrices: W in BaseConv, Q K V in attention (O(N^2 d) time), FFT convolution. Attention solves MQAR with the quadratic matrix QK^T. Pieces that match L's rules: the programmatic selector (membership test of a token id seen before) is a hash-set lookup; the sequential RAM algorithm named in Section 4.2 (N insertions and membership queries, sub-quadratic) is exactly a table lookup but needs Omega(N) layers to emulate in a feed-forward model, so a stateful chip that holds the table avoids that depth.

### (e) Limitations
This is a Dec 2023 first version: it does not test Mamba or linear attention on MQAR (Based does). The fix needs attention (full, programmatic or learned) in about 10 percent of layers, so the KV cache returns for those layers. The programmatic selector uses exact token-id matches, not fuzzy ones (synonyms, paraphrase); the paper says so. Learned selection closes only 72 percent. Scale tested up to 1.4B for pretraining.

## 3. Based: Simple linear attention language models balance the recall-throughput tradeoff (Arora, Eyuboglu, Zhang, Timalsina, Alberti, Zinsley, Zou, Rudra, Re; Stanford)

### (a) Mechanism
Based mixes three kinds of layers (about 20 percent Taylor linear attention, 20 percent sliding-window softmax attention, 60 percent short gated convolution).

Taylor linear attention. Feature map phi: R^d' -> R^(D) with phi(q)^T phi(k) = 1 + q^T k + (q^T k)^2 / 2 (second-order Taylor of the exponential), after projecting the head to d' = 16 by W_q, W_k. Features: [1, x, x ⊙ x] (the paper counts unique products with 1 + 3d'/2 + d'^2/2 entries: 45 for d' = 8, 153 for d' = 16, 325 for d' = 24, 561 for d' = 32). Recurrence: s_i = s_(i-1) + phi(k_i)^T v_i, z_i = z_(i-1) + phi(k_i)^T, y_i = phi(q_i) s_i / (phi(q_i) z_i). State per head (Appx E.2, equations 8 and 9): sizeof(s_i) = (d + 1) x D, i.e. (d+1)(1 + 3d'/2 + d'^2/2) numbers, the +1 being the K-state z. DERIVED examples (number of numbers, not bytes; the byte width is not given in the text we read): d = 64, d' = 16 gives 65 x 153 = 9,945; d = 128, d' = 24 gives 129 x 325 = 41,925; d = 48, d' = 8 gives 49 x 45 = 2,205.

Sliding window attention (TC Window): exact softmax over the last w tokens with w of 64 to 128 (multiples of 16, tensor-core sized); KV cache size 2 d min(N, w). Short convolutions (width 3). Optional per-head decay; none in the main results trained to 30B and 50B tokens.

State formulas used in the memory-recall experiment (Appx E.2): attention 2 d N; sliding window 2 d min(N, w); Mamba 2 d d_state; H3 d d_state with d_state = d/4; Hyena d N; Based as above. DERIVED examples: attention d = 64 at N = 1024 is 131,072 numbers; Mamba d = 128, d_state = 16 is 4,096; H3 d = 256, d_state = 64 is 16,384; sliding window d = 128, w = 64 is 16,384.

### (b) Numbers
Memory-recall tradeoff (Section 3.1, Fig 2, 3, 8). Task: MQAR trained at length 256 with 4 to 64 key-value pairs, evaluated at length 1,024 with 4 to 256 pairs. Six mixers: attention, sliding window, Mamba, H3, Hyena, Based; hyperparameters varied: model dimension, window width (8 to 1024), d' in {8, 16, 24}, Mamba d_state in {8, 16, 24}. Result as stated in text and captions: within every class more state gives higher accuracy almost always; across classes attention has perfect accuracy but a state that grows with N; Mamba makes the best use of a small state among prior work; H3 and Hyena sit well below the Pareto frontier; Based moves the frontier beyond Mamba; smaller windows lower accuracy about linearly. The x axis of Fig 8 spans 10^4 to 10^6 bytes (tick labels); accuracy values at each size are plotted only (UNVERIFIED as numbers). Fig 1 centre: Based with window 64 to 128 recovers 90.8 percent of full attention's recall accuracy at 1e-5 x the latency of a 4096-wide window.

Feature maps on MQAR (Fig 3): Taylor, PosELU and ReLU maps are on the Pareto frontier; the Taylor map increases state without adding parameters, other maps need more parameters for the same recall.

Pile language modelling (Table 1, MEASURED): overall / AR / other ppl; SWDE, FDA accuracy; SQuAD F1; LM-eval average.
- 1.3B, 50B tokens: Transformer++ 6.28 / 1.65 / 6.82; 76.50; 80.47; 43.47; 53.33. Based (1.35B) 6.30 / 1.71 / 6.82; 64.45; 30.40; 41.62; 53.81. Mamba (1.32B) 6.28 / 1.74 / 6.78; 52.75; 18.51; 35.92; 53.50.
- 1.3B, 10B tokens: Transformer++ 7.26 / 1.74 / 8.10; 71.92; 73.23; 36.19. Based 7.43 / 1.87 / 8.26; 48.06; 24.41; 30.46. Mamba 7.48 / 1.96 / 8.29; 34.74; 12.89; 28.20.
- 360M, 30B tokens: Transformer++ 7.68 / 1.80 / 8.40; 70.75; 63.79; 25.07. Based 7.77 / 1.93 / 8.46; 45.01; 16.45; 32.67. Mamba 7.73 / 2.02 / 8.38; 27.63; 8.71; 26.71.
- 360M, 10B tokens: H3 10.60 / 4.88 / 11.23, SWDE 6.75, FDA 0.64, SQuAD 7.87 (recall collapse); GLA 9.12 / 2.36; RWKV v5 9.79 / 2.40.
- Our arithmetic (DERIVED) on these rows: the headline "10.36 points over Mamba" equals the mean of the three recall columns at 360M with 30B tokens (17.38, 7.74, 5.96 points); at 1.3B/50B the same mean is 9.76, at 1.3B/10B 9.03, at 360M/10B 3.89. The text of the paper attributes 9.0 and 10.4 to the 1.3B scale; the table rows do not reproduce that labelling. Use the table values.
- Even so Based is far below Transformer++ on FDA (30.40 vs 80.47 at 1.3B/50B) and on SWDE (64.45 vs 76.50): the fixed state does not close the recall gap on long documents (FDA chunks are 1,920 tokens).
- Throughput on H100 (Table 1 and Fig 4): 1.3B: prefill (4,096 tokens) Transformer++ 103.50, Based 161.71, Mamba 112.22 tokens/ms; generation (2,048 tokens) Transformer++ 0.99, Based 24.28, Mamba 25.69. Ratio DERIVED 24.5 (the paper's "24 x" claim over FlashAttention-2 at batch 128, 1,024 generated tokens). 360M: prefill 207.77 / 514.57 / 267.09; generation 23.82 / 47.23 / 39.95. Based prefill is 56 percent faster than FlashAttention-2 and 44 percent faster than Mamba at 4k and 1.3B (text).
- Ablations (Table 6, 362M, 10B tokens): feature dimension d' = 8 / 16 / 24 / 32 with 45 / 153 / 325 / 561 features: AR ppl 2.18 / 2.07 / 2.02 / 2.00; SWDE 23.40 / 29.16 / 34.38 / 37.62; FDA 12.79 / 11.71 / 20.87 / 12.89. Diminishing returns beyond 24 (text). Feature map: Taylor 2.07 AR; Performer 8.53 (fails); CosFormer 16 (32 features) 2.42, 64 (128 features) 2.18. Local mixers: no window and no conv 2.29 AR (overall 9.49); window 64 only 2.11 (no conv) or 2.09; window 128 vs 64: 2.06 vs 2.07. Decay: small gain only.
- Downstream: SuperGLUE few-shot (Table 3 text): Transformer++ and Based improve with more shots, Mamba is worse at 5-shot than 0-shot. DNA (HG38) and GenomicsBenchmarks competitive.

### (c) How memory must grow with what is recalled
Theorem 3.1 (F.12): any recurrent model whose state depends causally on the input, with bounded entries, needs Omega(N) bits of state to solve MQAR. Proof by reduction from the index problem: Alice runs the model on N pairs {j, x_j} and sends the state; Bob appends a query; one-way randomised communication complexity of index is Omega(N) (Jayram et al.). Corollary F.13: causal Mamba with O(1)-bit entries needs d + d_state of order N. For gated convolutions: data-independent BaseConv needs log(2d) layers at d = log2 c (Thm 3.2); the lower bound Omega(max(log log c, log log N)) layers is tight (Thm F.30). So: memory must grow linearly with the number of facts to be recalled, in bits. DERIVED: with N pairs from a vocabulary of c values, the information content is about N log2 c bits, and the state can store at most (entries x bits per entry).

### (d) Operations
Conflicting: W_q, W_k, W_v projections; outer-product update phi(k)^T v (D x d multiply-accumulates per token); read phi(q) s (a D x d matrix-vector product); the quadratic feature q ⊗ q; softmax with exp in the window (two GEMVs with w = 64); gated convolution projections (expansion factor 4). Paper's own point: the window is sized to fill GPU tensor cores (312 TFLOP/s matmul vs 19 TFLOP/s elsewhere) and the state is kept in registers.
Compatible (DERIVED reading): the write is purely additive, s += phi(k)^T v, so with binary or integer sparse k and v it becomes a counter increment at (active feature, active value) cells; the read sums the rows of the active query features: a sparse row lookup. Exact local recall via sliding window is a small cache plus compares. No scans are needed in Based (no decay, main results), unlike Mamba.

### (e) Limitations
Recall below attention on long, information-dense tasks (FDA 30.40 vs 80.47). Quality needs the sliding window and short convolutions: removing both loses 0.18 AR ppl (2.29 vs 2.07 / 2.11). Theory covers exact recall; fuzzy recall is not bounded. Memory-recall curves are shown for a synthetic task with a small number of keys; real-text recall depends on how many distinct spans must be held. Scale 1.3B, 50B tokens at most.

## 4. Mamba: Linear-Time Sequence Modeling with Selective State Spaces (Gu, Dao; Carnegie Mellon and Princeton, Gu Stanford-trained)

### (a) Mechanism
Continuous SSM h'(t) = A h(t) + B x(t), y = C h(t), discretised (ZOH) to A_bar = exp(Delta A), B_bar = (Delta A)^-1 (exp(Delta A) - I) Delta B. Prior SSMs are linear time invariant (LTI): (Delta, A, B, C) are fixed, so the model equals a global convolution with kernel K = (C B, C A B, ...), which cannot depend on content.

Selection (Algorithm 2, "S6"): B, C and Delta become functions of the current input: s_B(x) = Linear_N(x), s_C(x) = Linear_N(x), s_Delta(x) = Broadcast_D(Linear_1(x)), tau_Delta = softplus. A stays a fixed diagonal parameter. Recurrence h_t = A_bar_t h_(t-1) + B_bar_t x_t, y_t = C_t h_t, per channel; with diagonal A each of D channels has N numbers. N = 16 in the experiments, so the state is D x N per block, where D = E x d_model with expansion factor E = 2 (Section 3.4). Theorem 1: with N = 1, A = -1, B = 1 the recurrence equals the gated RNN h_t = (1 - g_t) h_(t-1) + g_t x_t with g_t = sigmoid(Linear(x_t)); Delta is a generalised forget/input gate: large Delta resets the state to the current input, small Delta keeps the state and ignores the input. Selection therefore chooses what enters the state (B), what is read (C) and how much is kept (Delta).

Why recall becomes possible: the model can store a token when its content says so and ignore noise (Selective Copying) and can hold a key's value and answer when the same key arrives (induction heads). Efficiency: because selection breaks the convolution view, a hardware-aware parallel scan computes the recurrence in fast SRAM without materialising the (B, L, D, N) state in slow HBM (kernel fusion, work-efficient parallel scan, recomputation in the backward pass). Architecture: one homogeneous block (gated MLP with an SSM on the main branch, no attention, no separate MLP), about 3 E D^2 parameters in the linear projections (2 E D^2 in, E D^2 out).

State size per block, DERIVED: D = 2 x 2048 = 4,096 channels at the 1.3B scale (d_model 2048, Table 12) times N = 16 gives 65,536 numbers per block, independent of context length. A GPT-3-style Transformer layer at d_model 2048 stores 2 x 2048 = 4,096 numbers per token, so its cache passes one Mamba block's state at 16 tokens and the whole 24-layer model's KV cache (2 x 2048 x 24 = 98,304 numbers per token, ESTIMATED from Table 12 shapes) reaches about 201 million numbers at a 2,048-token prompt. The count of Mamba blocks at 1.3B is not in the text we read (the paper says two Mamba blocks replace one attention plus MLP pair), so a model total is ESTIMATED.

### (b) Numbers
- Selective Copying (Table 1; length 4,096, vocab 16, 16 data tokens, 2 layers, D = 64): S4 without gate 18.3, S6 without gate 97.0; H3 with S4 57.0, with Hyena 30.1, with S6 99.7; Mamba block with S4 56.4, with Hyena 28.4, with S6 99.8. Gating alone does not help; selection does.
- Induction heads (Table 2 and 11; 2 layers, vocab 16, trained at length 256, tested 64 to 1,048,576): Mamba (74K parameters, D = 64) is 100 percent at every length including 2^20 (4,000 x training length). Attention variants (137K parameters) are accurate only to about twice the training length and run out of memory above 2^14; H3 (153K) falls to chance by 2^10 to 2^11; Hyena (69M including positional parameters) the same. Table 11: MHA-xPos 100.0 at 2^8, 99.6 at 2^9, 67.6 at 2^10, 25.4 at 2^11; H3 80.9 at 2^9, 39.5 at 2^10.
- Language scaling (Fig 4): 125M to 1.3B on the Pile at Chinchilla token counts; Mamba is the first attention-free model to match Transformer++, more clearly as length grows (curves only; numbers UNVERIFIED).
- Zero-shot (Table 3): Mamba-130M average 44.7 vs Pythia-160M 40.6; Mamba-370M 50.0 vs Pythia-410M 48.2; Mamba-790M 57.1 vs Pythia-1B 51.9; Mamba-1.4B 59.7 vs Pythia-1.4B 55.2 and RWKV-1.5B 54.3; Mamba-2.8B 63.3 vs Pythia-2.8B 59.1, RWKV-3B 59.6 and Pythia-6.9B 61.7; Pile ppl 6.22 (2.8B), LAMBADA ppl 4.23 (2.8B) against 5.04 for Pythia-2.8B. Hybrid H3-2.7B averages 58.0 (the H3 paper's model, GPT-2 tokenizer).
- State size ablation (Table 10, about 350M, language modelling perplexity, N = 1 / 2 / 4 / 8 / 16): with constant B, C: 9.88 / 9.86 / 9.82 / 9.82 / 9.81; with selective B, C: 9.73 / 9.40 / 9.09 / 8.84 / 8.71; parameters rise only from 367.1M to 371.5M. "Over 1.0 perplexity improvement for 1 percent more parameters": the state only pays off when B and C are selective. Table 7: selecting nothing 10.93; B only 10.15; C only 9.98; Delta only 9.81; all three 8.71. Table 6: Mamba block with S6 8.69, with S4 (complex) 10.54, H3 block with S6 8.95, with S4 10.30.
- Speed and memory: scan up to 7 x faster than attention at length 32K (Appx D), 20 to 40 x faster than the PyTorch scan; 4 to 5 x inference throughput of a Transformer of similar size, because no KV cache allows larger batches (batch up to 128, prompt 2,048, 128 new tokens, A100 80GB); training memory comparable to FlashAttention-2 (Table 15, 125M, length 2,048): batch 1 4.6 vs 4.8 GB, batch 8 11.5 vs 12.3 GB, batch 32 34.5 vs 38.2 GB (Transformer vs Mamba).
- DNA (HG38): Mamba matches Transformer++ and HyenaDNA with roughly 3 to 4 x fewer parameters at 40M; perplexity improves with context up to 1M tokens where HyenaDNA worsens. Audio: SC09 FID 0.94 (6.1M parameters) vs SaShiMi 1.99.

### (c) Memory against amount recalled
The paper's framing (Section 3.1): "efficient models must have a small state; effective models must have a state that contains all necessary information from the context"; the state is a compression, and selectivity decides what is compressed. There is no recall-versus-N bound in the paper, and its recall tests (one key-value, 16 data tokens, vocab 16) need a very small state, which is why a 74K-parameter model solves induction heads to 2^20 tokens. This does not contradict the Omega(N) bound: the task holds one fact. The Based paper (Cor F.13) applies the bound to Mamba (state of order N for N pairs) and measures the consequence: Mamba is below Based and attention on MQAR at equal bytes, and on SWDE/FDA/SQuAD (Based Table 1).

### (d) Operations
Conflicting: Linear projections for B, C, Delta and the gated block (3 E D^2 parameters per block dominate); exp(Delta A) and the softplus/SiLU nonlinearities; elementwise multiply-add h = A_bar h + B_bar x; C-weighted sum across N for the readout. No dense D x D state matrix: A is diagonal, so the state update is elementwise, not a matrix product.
Compatible: the parallel associative scan (a prefix-scan over (A_bar, B_bar x) pairs); resetting the state when Delta is large (a clear); a constant-size state with constant time per token; recomputation instead of storing states.

### (e) Limitations
Authors state: scale limited to the small sizes (below 7B), the continuous-versus-discrete tradeoff (selectivity can hurt on continuous data such as audio), engineering needed at larger scale, unknown whether fine-tuning, prompting and in-context learning behave like Transformers. Recall limits are shown by others: Based Table 1 Mamba SWDE 52.75, FDA 18.51, SQuAD 35.92 against Transformer++ 76.50, 80.47, 43.47 at 1.3B/50B, and degraded 5-shot SuperGLUE. The paper has no MQAR test.

## 5. Putting the four together

State size, recall and throughput, side by side:

| Model family | State at inference | Grows with N? | Recall of many pairs | Generation throughput (paper) |
|---|---|---|---|---|
| Attention (Transformer++) | 2 d N per layer | yes, linear | perfect (MQAR, d = 64 is enough for N up to 512) | 0.99 tok/ms at 1.3B (Based Table 1) |
| H3 hybrid | d x 64 per layer plus two KV layers | only the attention layers | good on SuperGLUE, not measured on MQAR | 1240 vs 520 tok/s at prompt 1536 (2.4 x) |
| Gated convolution (Hyena, RWKV, H3) | d x d_state or d N | Hyena yes | model dimension must grow about linearly with N on MQAR | below the frontier at equal bytes |
| Mamba | D x 16 per block | no | best of the fixed-state prior models, still below Based at equal bytes on MQAR | 25.69 tok/ms at 1.3B (Table 1) |
| Based | (d+1) x D per head, window 2 d w | no | tunable with d' and w; FDA 30.40 vs 80.47 | 24.28 tok/ms (24 x attention) |

Scaling rule (the one thing to carry out): for a recurrent model whose state is a function of the past, exact recall of N independent key-value pairs needs Omega(N) bits of state (Zoology Cor H.24 for gated recurrences with d up to sqrt N; Based Thm 3.1 for any causal recurrent model with bounded entries; both via the index problem). Gated convolutions are worse in practice (dimension about linear in N, Zoology Fig 2). The only free parameters are how many bits per fact and how well the state is used (Mamba beats H3 and Hyena at equal bytes; Based beats Mamba).

## 6. What L can take (ESTIMATED and DERIVED; not paper claims)

1. A counting-table state is already the right kind of object: Based's write s += phi(k)^T v is a table of counters indexed by (feature, value); H3's hand construction is a delay line, AND gate and accumulator per key. With binary features the write is an increment and the read a sparse row sum; no multiplies. The matrix-free chip should not copy their projections; it must replace them with hashing or fixed sparse features.
2. Capacity is bits, so size the table by facts: Omega(N) bits for N pairs means a table with at least N cells of log2(c) bits plus collision overhead if hashed. A Taylor feature map shows the other knob: Based gains recall by raising the number of features (45 to 561) without adding parameters, at the cost of state: d' = 8 to 32 moves AR ppl 2.18 to 2.00 and SWDE 23.40 to 37.62. In L this knob is the hash table width.
3. Local exact recall needs a small exact cache: Based's window of 64 to 128 tokens, and Zoology's finding that most repeated bigrams are near their first occurrence (power law of distances) says: a short exact buffer plus a long fixed table covers most recalls. The cache is a CAM-like compare, not a matrix.
4. Selection is useful: Mamba's Delta (forget or reset) and B (write gate) beat unselected states at equal N (Table 7: 10.93 versus 8.71; Table 10). In L, a write gate (store only on a surprise or key marker) and a clear on boundary are one-bit decisions per token.
5. Throughput comes from not having a KV cache: 24 x (Based) and about 5 x (Mamba) generation throughput over attention, 2.4 x (H3 hybrid). For L the equivalent claim is fixed bytes per token independent of context.

## 7. The one concrete small test for L

Test: MQAR on the counting-table state, recall accuracy against bytes of state.
- Task: generate Zoology Algorithm 1 MQAR data: vocabulary 8,192 (first half keys, second half values), sequence length N = 256 and 1,024, number of key-value pairs D in {4, 8, 16, 32, 64, 128, 256}, second occurrence placed at a power-law distance (alpha = 0.1, as in Zoology Appx E.1). Same evaluation protocol as Based: train at 256 with 4 to 64 pairs, evaluate at 1,024 with 4 to 256.
- Model under test: the L fast-weight table with integer counters (no multiply): write = hashed increment at (hash(key), value bucket), read = row lookup at hash(query) and argmax. Sweep the table size from 2 KB to 1 MB (about 10^3 to 10^6 bytes, the span of Based Fig 8) at 8-bit counters with two or four hash functions.
- Baselines for the same axes (recompute with Zoology code; byte formulas from Based Appx E.2): attention (2 d N), sliding window (2 d w), Mamba (2 d d_state), Based (d+1)(1 + 3d'/2 + d'^2/2).
- Output: accuracy against state bytes for each model at each D; record the smallest bytes with accuracy at least 0.9 and compare to N log2 c bits (DERIVED: 256 pairs x 13 bits = 3,328 bits = 416 bytes of raw content, so a table well above 416 bytes is expected, and any result at or below it would contradict the Omega(N) bound and must be checked for leakage).
- Success criterion: the counting table reaches 0.9 accuracy at equal or fewer bytes than Based (d = 64, d' = 16: 9,945 numbers per head) for D = 64 pairs, and its accuracy declines smoothly as D passes the table's capacity rather than collapsing. Label results MEASURED (software) or MODELLED (chip); failures logged with the same weight.

## UNVERIFIED and not read line by line
- All figure curves: Zoology Fig 1, 2, 6, 7; Based Fig 1, 2, 3, 8 (accuracy against bytes), Fig 4 beyond the table values; Mamba Fig 4, 5, 6, 7, 8. Only captions, axes and surrounding text were read.
- Based Appendix F.4.3 to F.6 (layer lower bounds for AR and MQAR, p-hot encodings, sub-logarithmic upper bound, about 2,000 lines of proofs): theorem statements in the main text and the F.4.1 to F.4.2 proof of Theorem F.12 and Corollary F.13 were read; the layer-count proofs were not.
- Zoology Appendix H.2 to H.5 and H.7 to H.8 (BaseConv simulation proofs, dyadic-interval MQAR circuit, autocorrelation filters): read the summary H.1.2, H.6 in full, and the statements of Theorems 4.2 to 4.5; the construction proofs were skimmed.
- H3 Appendix B, C (linear attention derivation, state-passing algebra) and F.7 onwards were skimmed; D.1 to D.4 and E.1 to F.6 were read.
- Mamba Appendix A to C (selection discussion, extended related work, mechanics), Appendix D recomputation details and E.2.2 to E.4 ablations were skimmed; Table 11, 12, 15 and E.1 were read.
- Byte widths of state entries in Based's memory-recall plot (the plot is in bytes; formulas give counts of numbers); per-point accuracies.
- Hybrid H3 on MQAR, Mamba on MQAR in Zoology (not in these papers).

Related: [Paper notes index](INDEX.md), [Forgetting-free adaptation papers](forgetting_free_adaptation_papers.md)
