---
title: Research 02 - CUDA and the software moat - licence clause, regulators, alternatives, controversies and complaints (1 Nov 2026)
tags: [spark, review, research, cuda, licence, antitrust, controversy]
---

# Research 02: CUDA, the licence, regulators and the debate

Labels and read depth as in [hardware](research_02_hardware.md). Accessed 1 Nov 2026. **I am not a lawyer; legal readings below are what the text says, not advice.**

## 1. What the licence says

Source read verbatim, partly: the [CUDA EULA](https://docs.nvidia.com/cuda/eula/index.html), header "v13.4", last updated 26 Jan 2026. About 39,000 of 87,800 characters were read; the back half was not [V].

| clause | text (short quotes) | reading |
|---|---|---|
| 1.2 item 8 | may not reverse engineer, decompile or disassemble "any portion of the output generated using SDK elements for the purpose of translating such output artifacts to target a non-NVIDIA platform" | The words concern **reverse engineering output in order to translate it**. They do not contain the phrase "translation layer" |
| 1.2 item 1 | may not reverse engineer or decompile "any portion of the SDK" | General |
| 2.1 | the SDK "is licensed for you to develop applications only for use in systems with NVIDIA GPUs" | A scope limit on development |

- **Jarvis's first pass says the licence "bans translation layers".** That is the trade-press headline ([Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/nvidia-bans-using-translation-layers-for-cuda-software-to-run-on-other-chips-new-restriction-apparently-targets-zluda-and-some-chinese-gpu-makers), March 2024; I could not read its body: the page returned only navigation, so its dates and any Nvidia response are **UNKNOWN**). The clause as written is narrower. Whether it covers a runtime that runs unmodified binaries on other hardware is a legal question I cannot settle; commenters disagree, and I found no ruling.
- One outlet reports that the clause first appeared in the online licence and later in the installed files, and that it dates from CUDA 11.5 or 11.6 ([S] [Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/nvidia-bans-using-translation-layers-for-cuda-software-to-run-on-other-chips-new-restriction-apparently-targets-zluda-and-some-chinese-gpu-makers), [S] [Wikipedia](https://en.wikipedia.org/wiki/CUDA)); versions disagree.
- ZLUDA (a CUDA-on-AMD layer) reached v6 in June 2026, and its developer says it is no longer commercially funded ([S] [byteiota](https://byteiota.com/cuda-amd-windows-zluda-2026/)). One outlet calls commercial use a violation of Nvidia's terms; that is opinion, not a finding.

## 2. Regulators: what is real

I tried primary pages; most were unreachable. **Nothing I could confirm shows a current regulatory action about CUDA.**

| action | status | read depth |
|---|---|---|
| US Justice Department and FTC probes of Nvidia, Microsoft and OpenAI, reported June 2024 | Reported by CNBC (headline only; article not opened); outcome **UNKNOWN**; not CUDA-specific in what I saw | [S], via Wikipedia's reference list |
| French competition authority search of Nvidia's French offices, 26 Sept 2023, "graphics card sector" | Listed in Wikipedia's summary only; the authority's own front page (checked 1 Nov 2026) shows no Nvidia item; outcome **UNKNOWN**. **Jarvis's note says "one site reports it and nothing else does": the better statement is that it is listed on Wikipedia with a citation I did not open, and is a 2023 search, not an announced CUDA case** | [S] |
| European and UK reviews of the Arm purchase, 2021 to 2022 | Deal abandoned Feb 2022; about Arm, not CUDA | [S] |
| China: any competition action on Nvidia's Mellanox conditions | **Not found** (I did not reach the regulator's site) | UNKNOWN |
| Reported 2025 Chinese restriction on buying Nvidia chips | A purchasing restriction, not an antitrust case, in what I saw | [S] |

Could answer: the regulators' public case registers; I had no working route to them.

## 3. What holds users in

| layer | evidence |
|---|---|
| Libraries and kernels | Attention and serving kernels tuned for Nvidia have no equivalent elsewhere in one secondary account; kernel quality varies 3.4x between 4-bit kernels on the same GPU ([fixes](research_02_fixes.md)) |
| Tooling | Nvidia's profiler was unavailable on the rented cloud used in arXiv 2605.30571 [S]; tools differ in availability |
| Skills and habit | Lattner's conference bio describes the advantage as "hardware, libraries, tooling, research practices, and developer familiarity" [S] |
| Licence | clause above |
| What is *not* lock-in | The user-facing serving engines are open source and run on other hardware ([Research 01 software](research_01_software.md)) |

**How much inference no longer needs hand-written CUDA: UNKNOWN.** No source gave a share. Open options exist (Triton, an MLIR-based language, XLA, SYCL, OpenCL). One source reports that Nvidia and the Triton authors announced same-day support for the 2025 Blackwell chips ([S] [comparison](https://safeguard.sh/resources/blog/gpu-programming-models-compared-cuda-hip-sycl-opencl-metal-vulkan-compute-and-triton)); a performance claim for Mojo comes from one secondary source. Each of these needs checking at the primary source.

## 4. The debate, with the strongest rebuttals

- **"A swamp, not a moat."** Jim Keller, posts on X, 17 Feb 2024; he added that "basically nobody writes CUDA" and what you write is probably not fast ([S] [Wccftech](https://wccftech.com/jim-keller-calls-nvidia-cuda-a-swamp-says-x86-was-a-swamp-too/amp/)). **An opinion, not a measurement.** Keller runs a rival chip company.
- **Strongest rebuttal found:** after Nvidia's CUDA Tile release (CUDA 13.1, Dec 2025), Keller said it might end the moat because tile code ports more easily; Wccftech argues the opposite, that the tile intermediate language is tuned to Nvidia and deepens the moat ([S] [Wccftech](https://wccftech.com/nvidia-might-end-the-cuda-moat-with-its-latest-update-says-jim-keller/amp/)). Unresolved.
- **Measured evidence about the moat:** AMD reached within 75% of Nvidia in one 2024 training study only with its own engineers helping; in the 2026 inference benchmark AMD is competitive at FP8 on an open engine and not at FP4 ([Research 01 software](research_01_software.md)). **The moat is thinner for serving a few popular models than for the rest.**

## 5. What practitioners complain about

Evidence is thin: no ranked count, and no forum threads reached. What I found is **the open-source serving engine's issue tracker and how-to guides** [S]:

- **Driver and CUDA-version mismatch** is described as the most common start-up failure, e.g. prebuilt wheels requiring CUDA 12.9 or newer while a pinned older driver cannot run it ([S] [vLLM issue](https://github.com/vllm-project/vllm/issues/19542), [S] [guide](https://dev.to/jovan_chan_9500711396d4e6/vllm-wont-start-every-fix-for-the-engine-init-cuda-and-oom-errors-2026-3ia9)).
- **Memory errors** at start-up: "no available memory for the cache blocks" means the cache does not fit after weights load.
- Security advisories forcing engine upgrades (an old version deprecated for a remote-code issue).

**Reading:** the visible pain is deployment friction on Nvidia hardware, not slowness. Whether this is a wedge is **UNKNOWN**; the same projects keep improving.

Related: [Research 02 summary](research_02_summary.md), [Incumbent fixes](research_02_fixes.md), [Research 01 software](research_01_software.md), [Reviews index](README.md)
