---
title: Test B - does a good engine close the batch-1 decode gap on the founder's GPUs (plan and bar, 1 Nov 2026)
tags: [spark, gpu, weakness, decode, plan, vision-research-02]
---

# Test B: how close to the memory floor does batch-1 decode get with the incumbents' own fixes

Why: [Vision research 02](../../../docs/reviews/research_02_summary.md), weakness B. Our earlier runs used the library's default decode in eager mode (no CUDA graphs, no compile; checked in `measure.py`, which calls `generate` with defaults), so "launch-bound" was never established. **Question:** with CUDA graphs and the best engine available on each machine, how close does batch-1 decode get to the weights-only memory floor? **Labels:** MEASURED once run; the floor is DERIVED (weight bytes divided by the measured copy bandwidth, which counts read plus write bytes, so the floor is approximate; the spec-sheet bandwidth is reported beside it).

## What we already know (from the earlier runs, eager mode, batch 1)

Fraction of the floor reached: RTX 3050 laptop: 20% (0.16 GB model), 28% (0.99 GB), **78%** (2.2 GB); Colab T4: 11%, 11%, 27% ([RESULT](../energy_predict/RESULT.md)). So the 1.1-billion-parameter model on the laptop was already close to memory-bound and the "launch-bound" reading was **overstated** for it; the small models are far from the floor in eager mode.

## Runs (same three models, batch 1, prompt 256, 128 new tokens)

1. eager (baseline, as before).
2. static cache plus `torch.compile(mode="reduce-overhead")` (CUDA graphs) through the library's own options, if it works on the machine (the script reports failure and carries on; compile may be unavailable on Windows).
3. On the Colab T4 (Linux): a serving engine with graphs on by default (vLLM), batch 1; instructions in the script header.

## Bars (fixed now, from Vision's proposal)

- **B-kill:** if the best run on a machine reaches **at least 70% of the weights-only floor** for a model, the batch-1 gap is closed on that machine for that model and the launch-bound story is dropped for it.
- **B-open:** if the best run stays **below 50%** for the 0.99 GB and 2.2 GB models, the gap survives the incumbents' fixes on that machine and weakness B stays on the shortlist (cause still unknown; do not claim launch overhead without a profile).
- Between 50% and 70%: reported as partly closed.
- Every machine and model reported, including failures to run.

## First results (1 Nov 2026, MEASURED, from console output pasted by the founder; JSON files not yet received)

- **RTX 3050 laptop (Windows), 0.5B-class model, eager:** 26.1 ms per token, 31% of the floor. Graphs mode: could not run (Triton not installed on Windows). The 1.1B-class model failed to load in both modes (CUDA out of memory, then Windows paging-file error 1455).
- **Colab T4, eager:** 0.5B-class 32.5 ms per token, **12.8% of the floor** (floor 4.15 ms); 1.1B-class 29.2 ms, **31.2%** (floor 9.11 ms).
- **Colab T4, the library's static cache plus `torch.compile(reduce-overhead)`:** **no valid CUDA-graphs run.** The compiler printed `skipping cudagraphs due to mutated inputs (72 instances)` (cause: the cache update mutates a counter tensor) for the 0.5B-class model, and the 1.1B-class run ended in `RuntimeError: accessing tensor output of CUDAGraphs that has been overwritten by a subsequent run`. So this path did **not** test graphs; it failed on library incompatibility.
- **Verdict on bars:** B-kill and B-open are **not decided**. The eager fractions (13% to 31%) leave a large gap, but the question (does the incumbents' own best engine close it) needs an engine with working graphs. Next run: [`graphs_vllm.py`](graphs_vllm.py) on the T4, graphs on against graphs off on the same engine (vLLM), then the same bars.

### vLLM on the Colab T4 (1 Nov 2026, MEASURED, console output)

vLLM 0.32.0 starts on the T4 (it uses the Triton attention backend because the T4 is too old for FlashAttention 2). **0.5B-class model, eager mode (graphs off), batch 1: 26.8 ms per token, 37.3 tokens per second.** With the 0.99 GB weights and the measured 240.6 GB/s copy bandwidth the floor is about 4.1 ms, so **about 15% of the floor** (weight bytes taken from the earlier run, 988,065,536; the engine did not report them). The graphs-on run has not been done yet. Script fixed afterwards (main-guard for the engine's helper processes; weight bytes read from the downloaded files).

## Result of test B (1 Nov 2026, MEASURED on one Colab T4; [numbers](results/vllm_T4.txt))

| model | graphs off | graphs on | floor | fraction of floor (graphs on) |
|---|---|---|---|---|
| 0.5B-class | 26.8 ms per token | **5.72 ms** (174.9 tokens/s) | 4.13 ms | **72%** |
| 1.1B-class | 24.5 ms | **9.69 ms** (103.2 tokens/s) | 9.19 ms | **95%** |

- **B-kill is met on this machine:** with the engine's graphs on, batch-1 decode reaches **72% and 95% of the weights-only floor** (bar: at least 70%). The 'launch overhead' gap is **closed by the incumbents' own engine** on the T4, for both models. Graphs make the same engine 4.7x and 2.5x faster.
- **What this overturns:** the earlier reading that small-model decode is stuck at 1.0 to 1.5 ms per layer on GPUs is a property of the default library path in eager mode, not of the GPU. With graphs the 0.5B-class model needs about 0.24 ms per layer. **Weakness B (batch-1 gap from launch overhead) is dead as a differentiator** for this size on this machine; a statically scheduled machine would not beat a well-configured GPU on launch cost.
- **What it leaves standing:** with a good engine, batch-1 decode on a GPU sits at **95% of its memory-bandwidth floor** for the larger model. So the limit is how fast weights can be read (bandwidth and energy per bit), which is the argument for on-chip memory, and also the same limit that Cerebras and the others already attack. Weakness A (idle compute) is the same fact seen from the compute side.
- **Useful by-product for the measurement idea:** a default eager setup is 2.5x to 4.7x slower than a graphs-enabled engine on the same GPU, so a report that tells a GPU owner 'switch the engine and settings' has real value. The first predictor rule (bytes over bandwidth) failed on eager runs but would be close to right for graphs runs (72% and 95%); not tested as a prediction.
- **Limits:** one GPU (a T4, old, with a slower attention backend in this engine); one engine; two small models; batch 1; the 3050 laptop could not run graphs (no Triton on Windows; the 1.1B-class model also hit a Windows virtual-memory limit); the engine's weight size for the 0.5B eager row was taken from the other run.

## Limits

Two machines (one a laptop GPU with a slow memory system, one a shared cloud GPU); small models only; the floor ignores the cache and the output layer; engines change quickly.

Files: [`graphs_test.py`](graphs_test.py), [`graphs_vllm.py`](graphs_vllm.py).

Related: [Research 02 summary](../../../docs/reviews/research_02_summary.md), [Test G1 result](../energy_predict/RESULT.md), [Restart 2 study](../../../docs/restart_2_weakness_study.md), [Hardware index](../../HARDWARE_INDEX.md)
