# Redesign decision: what three outside reviews and our own numbers say

Inputs: three external write-ups the team collected (a cited-facts search, a design critique, a literature sweep).
I have NOT opened the cited papers myself; their figures are second-hand until checked. Our own numbers are marked.

## 1. The decisive check, with our own measurements

| Quantity | Value | Label |
|---|---|---|
| One big-model step, qwen2.5-coder:3b on GPU | 19 ms/token | MEASURED (your PC) |
| One big-model step, qwen3.5:9b (43% CPU) | 72 ms/token | MEASURED (your PC) |
| Naive software copy-match over 20 KB history, Python | 123 µs per draft | MEASURED (this container) |
| Indexed 4-gram lookup, Python dict | 0.6 µs per draft (index build 5 ms once) | MEASURED (this container) |

Even the naive Python matcher costs 0.65% (3B) and 0.17% (9B) of one big-model step. A hardware matcher can save at most that.
**So a chip that only does the copy search faster cannot win; the search is not the bottleneck.** This is the review's central point, and our numbers confirm it.

## 2. What the reviews add

1. **Our "2-5% over copy" is a tokens-per-pass number, not a wall-clock speed-up.** It assumes verifying a draft costs one normal pass. Wall-clock has not been measured. (I stated the assumption earlier; this makes it explicit.)
2. **Prior art exists.** The facts review lists HADES (ASIC, simulated 6.99× tokens/s vs A100), FSD-Acc, SPECTRA, and HeteroReason (FPGA drafts, GPU verifies: 1.01-1.42× latency, 1.25-1.57× energy efficiency, measured), plus SuffixDecoding in software. Our proposed split (external drafter, GPU verifier) is not new; unverified by me.
3. **Energy can go the wrong way.** Reported measurements: speculative decoding can use *more* energy than vanilla decoding, and +25.65% at batch 128 (vs -29% at small batch). Our 0.14 J/token figure divides by tokens per pass and ignores this; it is an optimistic estimate, not a result.
4. **Board power matters.** A 2 W board beside a 250 W GPU needs about 0.8% more throughput just to break even on energy (reviewer's arithmetic with guessed power).
5. **Sampling correctness.** RL rollouts need exact speculative sampling, not greedy exact-match. Our drafting results are greedy only.
6. **Wording.** Our "answer-mode safety threshold" was a confidence/agreement threshold; agreement is not safety.
7. **Capacity.** About 1 MB of on-chip memory over many streams leaves roughly 1-4 K tokens of history per stream; useful history may be far larger.

## 3. Where the reviews disagree, and my read

- The literature sweep suggests an FPGA co-processor, then a 130 nm tape-out within 12 months. The design critique says current evidence does not justify fabrication. I side with the critique: nothing yet shows that external hardware pays for its transport, power and integration costs.
- Human-brain synapse count: the facts review says "not found"; the sweep says 100-500 trillion. Treat as an estimate with a wide range until sourced.

## 4. Decision

1. **Do not fabricate a copy engine.** The software search is already negligible.
2. **The only defensible hardware angle:** better drafts, not faster search. That means (a) shared history across many concurrent streams, larger than one request's context, and (b) whole-system energy per useful output including the board. Both are still unproven.
3. **Prove or kill it in software first.** The oracle test: replay the same drafts at zero drafting cost and see how much throughput changes against an optimized software drafter on a real GPU. If the zero-cost drafter barely beats the software one, the silicon project stops there.
4. **Measure the real thing.** End-to-end wall-clock tokens/s and energy for plain decoding vs the best software prompt-lookup, on the 3B model fully on GPU, before anything else.
5. **Keep the AI-development angle as the buyer story**, but only for workloads where it holds: repetitive code and structured data, and sibling rollouts with exact sampling. Report valid unique outputs per GPU-hour, not just tokens per second.

## 5. Gates (guessed thresholds, to be argued with)

| Gate | Pass condition |
|---|---|
| Oracle | zero-cost drafter beats optimized software by at least 5% on a named workload |
| Throughput | at least 10% whole-job improvement over optimized software |
| Energy | at least 5% lower system energy per useful output, including the board |
| Transport | benefit survives a measured 20-100 µs round trip |
| Correctness | greedy equivalence shown; exact sampling shown before any RL claim |
