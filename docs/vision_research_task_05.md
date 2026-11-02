---
title: Research task 05 for Vision - what CUDA really is, layer by layer, and what a small team can build as its own alternative (2 Nov 2026)
tags: [spark, review, research, prompt, cuda, software-stack, vision]
---

# Research task 05 for Vision (2 Nov 2026)

Founder's decision (2 Nov 2026): after [research 04](reviews/research_04_summary.md) found no evidence that chip makers buy from small outside teams, the founder will **build the inference software layer anyway** (software first, hardware later) and asks Vision to **research CUDA properly**. Method rule (CLAUDE.md): study the concept (why it exists, how it is built, where it is used, its flaws and limits), then build our own method that fixes the flaws and test it before building. The aim is **our own design, not a clone**. Vision's role is evidence and attack: report what CUDA is and what it costs to reproduce each part; do not propose products.

Repository: <https://github.com/kurosaki11op-art/gpu2.0>. Read branch `claude/sharp-davinci-wrwazg`; work on a new branch `vision/research-5`; write only in `docs/reviews/` (`research_05_<topic>.md`, `research_05_summary.md`). Standing rules: label every number (MEASURED / SIMULATED / MODELLED / ESTIMATED / PROJECTED; quoted figures PUBLISHED / VENDOR CLAIM / THIRD-PARTY ESTIMATE / UNKNOWN), source link and date for each, UNKNOWN instead of guessing, primary pages first (NVIDIA documentation, papers, source repositories), no AI model identifiers in repository content (describe models by size and type).

## Questions

1. **The layers of CUDA, each described from primary documentation:** the programming model (threads, blocks, grids, memory spaces, streams, graphs), the language and compiler (the front end, the intermediate language PTX and what is public about it, the machine code and what is not), the runtime and driver APIs, the libraries (dense linear algebra, deep-learning primitives, collective communication, template kernel libraries), the tools (profilers, debuggers, memory checkers), and the packaging and compatibility rules (forward compatibility, versioning). For each: what it does, whether the specification is public, and what is proprietary.
2. **Where the moat actually sits:** measured or published evidence of how much of real inference performance comes from hand-tuned library kernels versus the compiler versus the hardware; how many engineer-years the libraries represent where known; what developers actually write (high-level frameworks versus CUDA code) and how much inference code calls CUDA directly.
3. **Flaws and limits of CUDA** (for the "fix the flaws" step): documented pain (portability, build and versioning friction, performance cliffs, memory management, debugging, launch overhead and how graphs address it, closed components), with primary sources and the strongest rebuttals.
4. **Existing alternatives and how they were built:** HIP and ROCm, SYCL and oneAPI, OpenCL, Vulkan compute, Triton, XLA, MLIR-based compilers, Mojo and its engine, the ggml engine, tinygrad and similar small projects. For each: what layer it replaces, who built it, how many people and how many years where known, what hardware it supports, how well it performs against CUDA on inference (published numbers), and why it succeeded or stalled.
5. **Legal and licence boundary** (not legal advice): what the CUDA licence permits and forbids for a new implementation, what is safe to implement from public specifications (the PTX documentation, open APIs), and what the clean-room precedents say. Say what a lawyer would have to check.
6. **What a team of two could build in 3 to 6 months** as its own inference stack for one narrow family (for example decoder language models in a few precisions): candidate scopes with evidence from small projects that did something similar (lines of code, contributors, performance reached), and what they never reached. List the hardest parts with evidence, not guesses.
7. **Hardware needed to develop it:** what a team can test on (consumer GPUs, free cloud GPUs, CPU, simulators) and where an own-instruction-set simulator, such as the project's, helps or does not help.

## Deliverables

One note per topic, a summary with a **layer table** (layer, public or proprietary, effort to reproduce with evidence, existing open implementations, flaws), a **scope table** of what two people could realistically deliver and prove, the strongest **objections** to the plan, and a list of UNKNOWNs with who could answer. Public sources only; do not contact anyone; do not treat Jarvis's recollections as fact.

Related: [Research task 04](vision_research_task_04.md), [Research 04 summary](reviews/research_04_summary.md), [Restart 2 study](restart_2_weakness_study.md), [Deep study plan](gpu_deep_study_plan.md), [Docs index](INDEX.md)
