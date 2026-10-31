---
title: Research task 01 for Vision - how Nvidia and Cerebras work, why, whether it is efficient, effective and cheap, and where we can beat them (31 Oct 2026)
tags: [spark, review, research, prompt, competitors, vision]
---

# Research task 01 for Vision (31 Oct 2026)

Founder's instruction: a newcomer against Nvidia and Cerebras must understand what they do, how they do it, why they do it, what it gives the buyer, whether it really does, and whether it is the efficient, effective and cheap way; where it is not, how we can do better, and what they cannot do. Vision is asked to do this broad research, independently of Jarvis.

Repository: <https://github.com/kurosaki11op-art/gpu2.0>. Read branch `claude/sharp-davinci-wrwazg`; work on a new branch `vision/research-1`; write only in `docs/reviews/` (one note per section, named `research_01_<topic>.md`, plus `research_01_summary.md`). Read first: `CLAUDE.md`, `docs/PROJECT_MEMORY.md` (header list and 30 to 31 Oct decisions), `docs/own_gpu_charter.md`, `docs/gpu_deep_study_plan.md`, `docs/watch_radar.md`, `docs/wafer_price_research_prompt.md`, `docs/reviews/vision_review_01.md` and Jarvis's response. Standing rules apply: label every number (MEASURED / SIMULATED / MODELLED / ESTIMATED / PROJECTED, and for quoted figures PUBLISHED / VENDOR CLAIM / THIRD-PARTY ESTIMATE / UNKNOWN), give a source link and date for each, never fill a gap with a guess, no AI model identifiers in repository content (describe models by size and type).

## Questions, for each of Nvidia (data-centre GPUs and their software) and Cerebras (wafer-scale systems), then for the other serious rivals (Groq, Google TPU, AMD, Tenstorrent, and others you find)

For every design choice (execution model, memory hierarchy, number formats, matrix units, interconnect, packaging, cooling, software stack, pricing and sales model):
1. **What** do they do, and **how** is it built (cite papers, whitepapers, filings, teardowns, talks)?
2. **Why** did they choose it (constraint, history, market)?
3. **What does it give the buyer**, and does it really, by independent measurement (benchmarks such as MLPerf, third-party tests, customer reports)? Separate vendor claims from independent results.
4. **Is it the efficient, effective and cheap way?** Measure against the physical limits: energy per bit moved and per operation, utilisation actually achieved (fraction of peak), cost per token, tokens per second per user, power per rack, cost of ownership including software and migration.
5. **If not**, what is the flaw and the cheapest, simplest fix a newcomer could make, and what would stop the incumbent from copying it (technical, commercial, legacy)?
6. **What can they not do**, or do badly: workloads, model sizes, contexts, precisions, latency, edge, price points, regions, supply, openness. Be specific and give evidence.

## Deliverables

- One note per topic: compute and execution model; memory (capacity, bandwidth, energy per bit, cost per GB); numeric formats and quantisation; interconnect and scale-out; packaging, power and cooling; software and lock-in (what porting to a new chip really costs); pricing, margins and buying behaviour (who buys, why, how they decide); supply chain and manufacturing access for a startup (foundry, packaging, funding).
- A **gap table**: gap, who has it, evidence, size of the gap in numbers with labels, whether our design could address it, the test we would run and a pass bar we would pre-register.
- A **ranked list of the three to five most promising wedges** for a newcomer, each with: target buyer, what they pay for now, the claim in one sentence, the evidence for and against, the cheapest experiment that could kill it.
- **Honest negatives:** things Nvidia or Cerebras do well that we should not try to beat, and claims in our own charter that this research contradicts.

## Limits

Public sources only. Do not contact companies or publish anything outside the repository. Do not take Jarvis's numbers as true; recheck any you use. If a question cannot be answered from public sources, say UNKNOWN and say who could answer it.

Related: [Vision review prompt](vision_review_prompt.md), [Deep study plan](gpu_deep_study_plan.md), [Watch list](watch_radar.md), [Reviews index](reviews/README.md), [Docs index](INDEX.md)
