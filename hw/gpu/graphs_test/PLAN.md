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

## Limits

Two machines (one a laptop GPU with a slow memory system, one a shared cloud GPU); small models only; the floor ignores the cache and the output layer; engines change quickly.

Files: [`graphs_test.py`](graphs_test.py).

Related: [Research 02 summary](../../../docs/reviews/research_02_summary.md), [Test G1 result](../energy_predict/RESULT.md), [Restart 2 study](../../../docs/restart_2_weakness_study.md), [Hardware index](../../HARDWARE_INDEX.md)
