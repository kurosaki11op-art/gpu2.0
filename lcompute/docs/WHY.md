---
title: Why CUDA exists, what it is used for, what people need from it, and what that means for our design (2 Nov 2026, from my knowledge, to be checked against primary sources)
tags: [spark, lcompute, cuda, why, requirements, study]
---

# Why CUDA exists and what people need (2 Nov 2026)

Founder's method: see what CUDA is and what it does, why it was built, what it is used for, then build what people need. **Everything here is from my own knowledge of public history and use; it has not been checked against primary documents in this session, and Vision's CUDA research ([task 05](../../docs/vision_research_task_05.md)) is still the independent check.**

## Why it was built

- Graphics chips were fast at the same arithmetic done many times at once. Before CUDA (introduced by NVIDIA around 2007), people who wanted that speed for other work had to disguise their problem as graphics (pixel shaders and textures), which was awkward and fragile.
- CUDA gave general programmers a **C-like language for the GPU**, a model of threads and memory, a compiler, and libraries, so the GPU became a general parallel computer.

## What it is used for

Scientific and engineering simulation, graphics and video, finance, and since about 2012 **deep learning**: neural networks are mostly large matrix operations, which GPUs do well, and CUDA's matrix and neural-network libraries (and later the frameworks built on them) made GPUs the default machine for training and, increasingly, running models.

## What people need from it (requirements, as I read them)

1. **Write parallel code without learning the hardware's graphics origin:** a clear model of threads, blocks, memory spaces and barriers.
2. **Speed without hand-tuning for every chip:** libraries that are already tuned, and code that keeps working on the next GPU generation.
3. **Ready-made building blocks:** matrix multiply, convolution, attention, communication between GPUs, with their gradients for training.
4. **Tools to find mistakes and slowness:** debuggers, memory checkers, profilers.
5. **Stability:** old programs still run; documentation; a large community.
6. **Memory:** enough of it, and control over moving data.

## Where it falls short (flaws, from public criticism and use)

Locked to one vendor's hardware; the best parts are closed; build and version friction; performance cliffs that need expert knowledge; debugging parallel code is hard; the licence restricts translating its output to other hardware (see the [CUDA study](../../docs/cuda_study_jarvis.md)).

## What this means for L Compute

| need | our design answer | where it stands |
|---|---|---|
| clear model | an open [SPEC](SPEC.md) with an exact reference interpreter | step 1 |
| find mistakes | the interpreter checks bounds and barrier errors by construction; every kernel has a reference | step 1 |
| building blocks | libraries written in our own language, tested against PyTorch | step 6 |
| runs on more than one vendor | back ends for CPU, PTX and a non-NVIDIA route from one IR | steps 3 to 5 |
| training | gradients as IR transforms | step 7 |
| speed | **not yet addressed**: warps, coalescing, tiling choices, tensor-core instructions must be learnt from NVIDIA's public documents and measured on real GPUs | before step 4 |
| open and stable | open spec, versioned IR | ongoing |

## Not claimed

That our platform is better than CUDA; that people will switch; that I know all of CUDA's details. The first test of "what people need" is whether the existing model code (our engine's model, then a small trainer) runs correctly and reasonably fast on it.

Related: [README](../README.md), [SPEC](SPEC.md), [ROADMAP](ROADMAP.md), [CUDA study](../../docs/cuda_study_jarvis.md), [Docs index](../../docs/INDEX.md)
