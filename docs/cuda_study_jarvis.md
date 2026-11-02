---
title: CUDA study, Jarvis first pass while Vision is unavailable (2 Nov 2026, web-search summaries, unverified)
tags: [spark, cuda, study, software-stack, restart]
---

# CUDA study, first pass (2 Nov 2026)

Vision's [task 05](vision_research_task_05.md) is pending because Vision is unreachable; this is my own pass from web searches (summaries, many blogs; every item is a lead until a primary page is read) and a prompt for the third assistant, Ultron ([prompt](ultron_prompt_cuda.md)). Method (CLAUDE.md): study each layer (why it exists, how it is built, where it is used, flaws), then design our own and test before building.

## Layers and what is public

| layer | what it is | public or proprietary (from the search) | open implementations |
|---|---|---|---|
| Programming model and language | threads, blocks, grids, memory spaces, streams, graphs; C++ extensions | model documented | HIP (AMD, source-compatible), SYCL and oneAPI (Intel and others), OpenCL, Vulkan compute |
| Compiler | the front end compiles to PTX, a **virtual instruction set** | **PTX specification is public**; the compiler (nvcc, NVVM) is closed, though an open **NVPTX backend** exists in LLVM (not confirmed by this search) | LLVM-based stacks; tinygrad renders PTX itself ([LocalAI commit note](https://gitea.varghacsongor.hu/GithubMirror/LocalAI/commits/commit/6f0051301b8e65d4f86cd5eea5a1d8cfd02cf7dd)) |
| Machine code | **SASS**, the native instructions, produced from PTX by the assembler `ptxas` | **not documented**: opcodes are listed but semantics are not defined; reverse-engineering efforts exist ([Purdue framework](https://engineering.purdue.edu/tgrogers/publication/avalos-asplos-2027/), [SASS study](https://arxiv.org/pdf/2502.15999)) | none official |
| Runtime and driver | memory allocation, launch, synchronisation, forward compatibility (the driver JIT-compiles embedded PTX for a newer GPU) | closed driver; PTX forward compatibility documented ([overview](https://modal.com/gpu-glossary/device-software/streaming-assembler)) | AMD's driver stack is open; NVIDIA publishes open kernel modules but closed firmware (my recollection, not confirmed here) |
| Libraries | dense linear algebra, deep-learning primitives, collective communication, template kernels, inference optimiser | closed, tuned per architecture | rocBLAS and others (AMD), vLLM and SGLang as engines, ggml backends |
| Tools | profilers, debuggers, memory checkers | closed | partial |

## Findings relevant to a new stack

- **Only PTX is specified; SASS is not.** A new stack can target PTX on NVIDIA hardware and the driver finishes the job; going below PTX means reverse engineering the undocumented machine code. For non-NVIDIA hardware the vendor's own ISA documentation decides.
- **Licence clause:** the CUDA licence restricts reverse engineering *output* of its SDK elements to convert it for a platform other than NVIDIA (quoted as subsection 8 of the restrictions; press calls it a translation-layer ban; present in the documentation from CUDA 11.6, possibly 2021 online) ([Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/nvidia-bans-using-translation-layers-for-cuda-software-to-run-on-other-chips-new-restriction-apparently-targets-zluda-and-some-chinese-gpu-makers), [The Register](https://www.theregister.com/2024/08/09/amd_zluda_take_down/), [TrendForce](https://www.trendforce.com/news/2024/03/11/news-nvidias-eula-amendments-tighten-grip-suppressing-third-party-cuda-emulation/)). Recompiling existing CUDA programs is described as legal; the ZLUDA project was taken down after AMD's legal team took back code. A clean implementation of our own programming model is outside that clause; **not legal advice, a lawyer must check**.
- **Small projects exist that do not use the vendor libraries:** tinygrad generates its own kernels for several back ends and never links vendor libraries (one source); ggml supports many back ends (BLAS, Vulkan, WebGPU and others; fork mirror source). Team sizes, years and performance against vendor libraries were **not found**.
- **Gap of the closest alternative:** ROCm and HIP are source-compatible; blogs report production workloads 5% to 15% behind NVIDIA and one gives vLLM on MI300X at 85% to 92% of H200; sources conflict and are low quality; one says the NVIDIA inference optimiser has no ROCm support (April 2026) ([comparison blog](https://gpuperhour.com/blog/rocm-vs-cuda), [The Register on ROCm 7](https://www.theregister.com/2025/09/17/amd_rocm_7_chases_nvidia_cuda/)).
- **Where the moat sits (my synthesis, not sourced):** the tuned libraries look more defensible than the compiler, because frameworks call the libraries directly. No source quantifies it.
- **Not found:** NVVM and the NVPTX backend's documentation; engineer-years of CUDA or HIP; contributor counts of the small projects; any head-to-head against cuBLAS.

## Consequences for our own design (hypotheses to test)

1. **Do not clone CUDA** (licence risk, ecosystem size). Define our own small programming model for one family: decoder language-model inference in a few precisions.
2. **Targets we can reach:** CUDA GPUs through PTX or an existing back end, the Vulkan path, CPU, and our own simulated accelerator (the existing instruction set and simulator).
3. **The part of the stack worth owning first** is the layer between a model graph and the kernels: a compiler and runtime that schedules weights and cache across memory tiers (the small-GPU problem, candidate 2), using generated kernels or existing ones.
4. **Kill criteria before building:** a defined model family, a pre-set bar (speed against the best free tool on the founder's laptop GPU), a date, and a stop rule.

## Open items for Vision (when reachable) and Ultron

[Task 05](vision_research_task_05.md) in full; the missing items above; and checking this note.

Related: [Research task 05](vision_research_task_05.md), [Ultron prompt](ultron_prompt_cuda.md), [Restart 2 study](restart_2_weakness_study.md), [Small GPU plan](../hw/gpu/small_gpu/small_gpu_plan.md), [Docs index](INDEX.md)
