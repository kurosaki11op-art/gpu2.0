---
title: Research task 02 for Vision - GPU and CUDA weaknesses, controversies and unmet needs, from primary sources (1 Nov 2026)
tags: [spark, review, research, prompt, cuda, weaknesses, vision]
---

# Research task 02 for Vision (1 Nov 2026)

Founder's instruction: restart on the right path. Study GPUs and CUDA properly: their weak spots, the public controversies and complaints, and what buyers and developers cannot get today. Jarvis has done a first web pass ([restart 2 note](restart_2_weakness_study.md)); do **not** start from it. Work independently, then compare.

Repository: <https://github.com/kurosaki11op-art/gpu2.0>. Read branch `claude/sharp-davinci-wrwazg`; work on a new branch `vision/research-2`; write only in `docs/reviews/` (notes named `research_02_<topic>.md` and `research_02_summary.md`). Standing rules: label every number (MEASURED / SIMULATED / MODELLED / ESTIMATED / PROJECTED; quoted figures PUBLISHED / VENDOR CLAIM / THIRD-PARTY ESTIMATE / UNKNOWN), source link and date for each, UNKNOWN instead of guessing, no AI model identifiers in repository content (describe models by size and type).

## Questions

1. **GPU hardware weaknesses with numbers:** utilisation actually reached in LLM inference (prefill, decode, by batch size); memory bandwidth and capacity limits; launch and scheduling overhead; interconnect cost; idle power; reliability and failure rates at scale. Use primary papers, MLPerf, vendor documentation and independent measurements, not blog summaries.
2. **How far do the incumbents' own fixes go?** CUDA graphs, torch.compile, TensorRT-LLM, vLLM, speculative decoding, FP8 and FP4, disaggregated prefill and decode. For each: what it fixes, what it costs developers, what is left unfixed (give measured numbers when they exist).
3. **CUDA and the software moat:** what exactly locks users in (libraries, tooling, kernels, skills, licence terms); real porting costs and failures (AMD ROCm, Intel, others); the translation-layer licence clause and its legal reading; antitrust and regulatory actions (check whether any is real and current); open alternatives (Triton, SYCL, OpenCL, Mojo, XLA) and how much of the inference market no longer needs CUDA by hand.
4. **Controversies and complaints:** developer forum threads, GitHub issues, conference talks, and critics (including the "swamp not a moat" argument) with the strongest rebuttals; what practitioners actually complain about when serving models.
5. **Unmet needs of buyers:** what inference providers, small clouds, enterprises and edge users say they cannot get today (price, supply, power, latency, memory, privacy, on-premises).
6. **Failure and success cases:** why inference-chip startups succeeded or were absorbed or struggled (Groq, Cerebras, SambaNova, Graphcore, others): the primary reasons, with evidence.
7. **Power, heat, water:** primary data on energy per token and per prompt at the system level, cooling and water use, and what limits data-centre growth (grid, permits, water).

## Deliverables

- One note per topic above, with sources and honest uncertainty.
- A **weakness table:** weakness, evidence and its label, who suffers, what incumbents already do, how much remains, whether a small team could show a fix that incumbents cannot copy quickly, and the cheapest experiment that could kill it.
- A **ranked shortlist of weaknesses** worth attacking, and a list of weaknesses that look real but are already closed by incumbents.
- **Corrections to Jarvis's first pass,** if the independent work disagrees.

## Limits

Public sources only; do not contact companies; do not treat Jarvis's numbers as true; say who could answer any UNKNOWN.

Related: [Research task 01](vision_research_task_01.md), [Restart 2 study](restart_2_weakness_study.md), [Watch list](watch_radar.md), [Reviews index](reviews/README.md), [Docs index](INDEX.md)
