---
title: Prompt for Ultron - research CUDA layer by layer with sources, and say what you do not know (2 Nov 2026)
tags: [spark, cuda, prompt, research, ultron]
---

# Prompt for Ultron (copy everything below the line)

---

You are helping a one-person startup research how NVIDIA's CUDA is built and what a tiny team could build as its own alternative inference stack. Rules for your answers: **cite a source link for every factual claim**, prefer NVIDIA's own documentation, academic papers and project repositories over blogs, **write "I do not know" instead of guessing**, mark every number as published, vendor claim, estimate or unknown, do **not** make claims about what the user has already built, and do **not** open with praise or agreement; challenge weak ideas. Answer in separate sections.

1. **Layers of CUDA.** For each layer (programming model, language and compiler, PTX, SASS and the assembler, runtime and driver, math and deep-learning libraries, collective communication, profilers and debuggers, packaging and compatibility): what it does, whether its specification is public, and what is proprietary.
2. **Where the lock-in really sits.** How much comes from hand-tuned library kernels, from the compiler, from the hardware, from developer habit? Give evidence, not opinion; say where there is none.
3. **Documented flaws** of CUDA that a new design could fix, with sources and the strongest rebuttal of each.
4. **Existing alternatives**: HIP/ROCm, SYCL/oneAPI, OpenCL, Vulkan compute, Triton, XLA, MLIR-based compilers, Mojo and its engine, ggml and llama.cpp, tinygrad. For each: which layer it replaces, who built it, team size and years if public, supported hardware, published inference performance against CUDA, and why it succeeded or stalled.
5. **Legal boundary** (not legal advice): what the CUDA licence forbids for a new implementation, what is safe to build from public specifications such as PTX, and precedents for clean-room work. List what a lawyer must check.
6. **What two people could build in 3 to 6 months** for one narrow family (decoder language-model inference in a few precisions): examples of small projects that did something similar, their size, and what they never reached.
7. **Hardware for development**: what a team without money can test on (consumer GPUs, free cloud GPUs, CPUs, simulators).
8. **The three strongest objections** to the plan "build our own inference software first, a chip later", with evidence.

End with a list of everything you could not verify.

---

Related: [CUDA study (first pass)](cuda_study_jarvis.md), [Research task 05](vision_research_task_05.md), [Docs index](INDEX.md)
