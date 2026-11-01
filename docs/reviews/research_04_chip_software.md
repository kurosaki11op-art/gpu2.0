---
title: Research 04 item 7 - do chip makers pay for compiler, runtime and kernel work, and how much of the CUDA moat is the low-level layer (1 Nov 2026)
tags: [spark, review, research, compiler, runtime, kernels, chip-makers, acquisitions]
---

# Research 04, item 7: software for hardware makers

Labels: MEASURED, PUBLISHED, VENDOR CLAIM, THIRD-PARTY ESTIMATE, DERIVED (my arithmetic), UNKNOWN. Read depth: **[V]** verbatim text read on a primary page; **[S]** only a search summary or a fetch tool's own summary. Accessed 1 Nov 2026. I describe models by size and tier, not by name.

## The finding in one paragraph

**Chip makers do pay for software, but the evidence is acquisitions of whole teams, not contracts with small outside teams.** I found four large deals in 13 months that bought a compiler or runtime team (Qualcomm and Modular, AMD and Untether's engineers, Nvidia and Groq, Intel and Codeplay earlier) and **no evidence at all of recurring paid work from chip makers to outside teams of two.** The one services firm that sold "silicon enablement" to chip vendors (Codeplay) was bought by Intel. For the founder's idea, that is a strong sign that the layer is valuable and a warning that I could find no market for the freelance version.

## Evidence of payment

| deal or case | what was bought | price and date | label and source |
|---|---|---|---|
| **Qualcomm buys Modular** (compiler and runtime company, language and model-serving software) | The company; Qualcomm says it adds "a silicon-agnostic compute layer" and a software base for its data-centre plans; the products continue; the chief executive becomes a Qualcomm executive vice president | Announced **24 Jun 2026**, completed **29 Jul 2026**. **Price: not stated in either release.** Press reports say $3.9B all-stock | Releases PUBLISHED [V] (reproduced on [Modular's blog](https://www.modular.com/blog/qualcomm-to-acquire-modular) and [completion note](https://www.modular.com/blog/qualcomm-completes-acquisition-of-modular)); price THIRD-PARTY, [S] [Quartz](https://qz.com/qualcomm-acquires-modular-ai-software-stock-deal-062426) |
| Modular before the deal | $250M round at a $1.6B valuation (Sept 2025), about $380M raised in total | | THIRD-PARTY aggregators, [S] [Sacra](https://sacra.com/c/modular/). **DERIVED:** if the press price is right, the valuation rose 2.4x ($3.9B / $1.6B) in about nine months |
| AMD takes the engineering team of Untether AI | "a talented team of AI hardware and software engineers", to advance compiler and kernel work; Untether's products were discontinued | June 2025; **price not disclosed** | [S] [SiliconANGLE](https://siliconangle.com/2025/06/05/amd-bags-team-behind-ai-chipmaker-untether-ai-third-acquisition-two-weeks/). Untether had receivers appointed in Feb 2026 ([S] [tracker](https://killedbyai.net/funding/)) |
| Nvidia and Groq | A licence and the team (see [Research 02](research_02_buyers.md)) | reported $17B to $20B, Dec 2025; I could not find Nvidia's own announcement | THIRD-PARTY [S] |
| Intel buys Codeplay (compiler and SYCL company) | A company that sold porting, support and "silicon enablement" to chip vendors | 2022; price UNKNOWN to me | [S] [Next Platform](https://www.nextplatform.com/code/2022/06/01/to-cure-iron-anemia-with-sycl-intel-buys-codeplay/1645775); Codeplay's own page lists professional services and porting ([S](https://codeplay.com/solutions/ecosystem/)); a 2020 analyst note names Intel and Renesas as silicon-enablement customers ([S](https://codeplay.com/portal/blogs/2020/09/24/abbott-451-report)) |
| Public-sector work for a vendor's chips | Argonne and Oak Ridge labs awarded Codeplay a contract to support AMD GPUs in a compiler | date UNKNOWN | [S] [Khronos](https://www.khronos.org/news/permalink/argonne-ornl-award-codeplay-contract-to-strengthen-sycl-support-for-amd-gpus) |
| Chip makers hiring in-house | Tenstorrent lists open roles for AI compiler and kernel development; headcount by function is not public | | job-board listings, [S] |

**What I did not find:** a price list, a services page with a day rate, a customer list, or a funded company whose business is selling compiler or kernel work to chip startups. **Whether any chip maker buys such work from a team of two: UNKNOWN.** Who could answer: software leads at chip companies; the founder's conversations are the only test.

## How software maturity limited challenger chips

| evidence | label and source |
|---|---|
| A reviewer's measured test of a challenger workstation (Nov 2025): a setup script failed, the compiler was in beta, converting one model took about 45 minutes, and the tested models seemed to leave about half the cores idle (the reviewer's inference) | MEASURED by an independent reviewer, [P] [The Register](https://www.theregister.com/on-prem/2025/11/27/blackhole-quietbox-tenstorrents-ai-workstation-reviewed/2113269), from [Research 01](research_01_software.md) |
| AMD's software doubled throughput in under two months on one benchmark | MEASURED by SemiAnalysis, [P] [InferenceX v2](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs) |
| AMD's own 2024 training study reached within 75% of Nvidia only with AMD engineers helping | [S] [SemiAnalysis](https://semianalysis.com/2024/12/22/mi300x-vs-h100-vs-h200-benchmark-part-1-training/) |

These show software is a real limit and that engineering effort moves it fast. They do not show that anyone outsources it.

## How much of the CUDA moat is the low-level layer

**No measured study quantifies it. UNKNOWN.** What the evidence says:

- The popular serving engines are a thin layer over a PyTorch-and-kernels base: their speed comes from vendor kernels and libraries (cuBLAS, FlashAttention-class kernels, NCCL); a GPU-cloud vendor's blog and a trade analysis say so ([S] [orchestrator.dev](https://orchestrator.dev/blog/2026-05-24-gpu-compute-platforms-comparison/), [S] [clusterbid](https://clusterbid.com/blog/nvidia-cuda-vs-amd-rocm-ecosystem-2026)). Library calls have only partial equivalents on other chips; multi-GPU communication is the hardest to port (same sources). Blogs, not studies.
- **What the high-level layer already covers, from the projects' own pages [V]:**

| project | hardware named on its own pages | note |
|---|---|---|
| vLLM (install page dated 11 May 2026, a developer preview) | Nvidia CUDA, AMD ROCm, Intel XPU, Apple (via a Metal plug-in); CPUs (x86, Arm, IBM Z) | "vLLM supports third-party hardware plugins that live **outside** the main repository"; "If you want to add new hardware, please contact us" |
| SGLang (docs, news to 29 Oct 2026) | "Native support across hardware platforms including Nvidia, AMD, Intel Xeon, Google TPU, Ascend NPU, and Moore Threads" | A Trainium plug-in beta was announced 22 Oct 2026 |
| the ggml engine (ggml-org repository README) | 17 backends including CUDA, HIP (AMD), Metal, SYCL, Vulkan, OpenCL, CANN (Ascend), Hexagon (Snapdragon), Moore Threads, WebGPU | README does not say who maintains each |
| Triton | Nvidia GPUs and AMD GPUs; CPUs "under development" | no documented path for other chips in the README |
| Modular (vendor claim, 2026) | "CPU, GPU, NPU and custom ASIC"; the same code runs on Nvidia and AMD GPUs; Qualcomm cloud parts integrated; the Qualcomm and TPU plug-in sources promised "in the coming months" | VENDOR CLAIM, [V] [Modular blog](https://www.modular.com/blog/modcon-qualcomm) |

- **Reading (DERIVED):** the top layer is already portable by plug-in on three major open engines, and the vendors named are the ones writing the plug-ins. **What a new chip needs from outside is therefore what these pages leave to the hardware maker: a backend that maps operators and attention to its own instructions, tuned kernels, and testing on its silicon.** Nothing says that is work an outsider can do without the vendor's documents and hardware.

## What a team of two could deliver in weeks

An honest answer is inference from the structure above, not evidence:

- **Could:** a plug-in or backend for one of the open engines running one named decoder on a chip or its simulator, with a performance report against a stated bar. The plug-in doors exist (vLLM's hardware plug-in route, the ggml engine's backend table, SGLang's plug-in).
- **Could not:** tune kernels for a chip without the chip or an accurate simulator, support multi-chip communication, or match a vendor's years of in-house kernel work.
- **Blockers I cannot size:** access to documents and hardware (likely under NDA), who owns the code, and whether the vendor has already decided to build it in-house. All UNKNOWN.

## India

I could not reach the government's own scheme pages (both returned access errors), so this is secondary.

| item | value | label |
|---|---|---|
| Design Linked Incentive scheme | Up to 50% of eligible design cost, capped near ₹15 crore per application; plus sales-linked incentives | THIRD-PARTY, [S] [India Briefing](https://www.india-briefing.com/news/india-design-linked-incentive-scheme-semiconductor-sector-supply-chain-40767.html/); figures conflict across sources |
| Scale | 105 startups developing chips; 24 projects supported; 105 companies given design tools; 23 tapeouts (a government statement, relayed) | [S] [EE Times India](https://www.eetindia.co.in/india-eyes-50-fabless-chip-firms-as-dli-scheme-gains-traction/) |
| An edge-AI chip example | Netrasemi: an edge-AI SoC at 12 nm that has reached silicon bring-up; one of the first four selected for ₹15 crore support in 2023 | [S] [Engineers Garage](https://www.engineersgarage.com/indias-top-semiconductor-startups-of-2026/) |
| Software those startups say they lack | **Not found: UNKNOWN** | Who could answer: the startups' software leads |
| Status of a larger follow-on programme | Reported as both proposed and launched | sources conflict |

Related: [Research 04 summary](research_04_summary.md), [Research 04 categories](research_04_categories.md), [Research 01 software](research_01_software.md), [Reviews index](README.md)
