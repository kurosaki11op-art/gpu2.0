# Software vs hardware: which GPU limits need which fix

Rule used throughout: **software** = anything we can change in L's code or GPU kernels on today's GPU. **Hardware** = needs new circuits (FPGA prototype now, a chip later). **Co-design** = model changes made in software so the hardware becomes possible.

Status labels: ✔ verified source · ⚠ secondary / estimate · (mine) = my arithmetic.

## 1. L's 8 measured problems, split

| # | Problem | Software fix (do first, on the RTX 3050) | Evidence | What remains for hardware |
|---|---|---|---|---|
| 1 | Sparsity wasted | Gather only active neurons at batch 1; optional block-structured sparsity | GPU activation-sparsity systems: Deja Vu >2× vs FasterTransformer on OPT-175B ✔ [arXiv 2310.17157](https://arxiv.org/abs/2310.17157); PowerInfer up to 11.69× vs llama.cpp on RTX 4090, best case ✔ [arXiv 2312.12456](https://arxiv.org/html/2312.12456v2). GPU hardware sparsity only covers fixed 2:4 weights ✔ [NVIDIA](https://developer.nvidia.com/blog/structured-sparsity-in-the-nvidia-ampere-architecture-and-applications-in-search-engines) | Per-neuron, per-token sparsity at 2–10% density; sparsity disappears in batched training (union of active sets). **Event-driven engine.** |
| 2 | Spikes as fp32 | int8 (4×) / packed int4 (8×); int8 matmul via `torch._int_mm` | RTX 30 (SM86) tensor cores support INT8/INT4; INT4 only via CUTLASS ⚠ [CUDA_Bench](https://github.com/hibagus/CUDA_Bench), [torchao](https://docs.pytorch.org/ao/main/_modules/torchao/kernel/intmm.html) | 4-bit × weight multipliers and narrow buses are far cheaper than any GPU datapath. **4-bit spike datapath.** |
| 3 | Sequential recurrence | Parallel scan in training **if the recurrence is linear**; fused persistent kernel if not | Up to 9× from parallel linear recurrence ✔ [Martin & Cundy, ICLR 2018](https://arxiv.org/abs/1709.04057) | Token-by-token inference is inherently sequential but tiny; a GPU idles at batch 1. **Pipelined on-chip state.** |
| 4 | ~1,000 tiny triangular solves | Chunkwise delta rule (WY/UT), `flash-linear-attention` kernels; recurrent form for inference has **no** solve | DeltaNet trained at 1.3B params / 100B tokens with this algorithm ✔ [Yang et al., NeurIPS 2024](https://arxiv.org/abs/2406.06484) | Fast-weight state round-trips DRAM every token on a GPU. **Fast-weight unit with state in on-chip SRAM = on-chip learning.** |
| 5 | ~3,300 kernel launches | Kernel fusion (Triton), `torch.compile(mode="reduce-overhead")` = CUDA graphs | Each launch ~3–7 µs ⚠ [arXiv 2604.17861](https://arxiv.org/pdf/2604.17861), [PyTorch](https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html). 3,300 × ~5 µs ≈ 16 ms of overhead per step (mine) | Nothing fundamental. A hard-wired dataflow pipeline has no launches by design. |
| 6 | Hash memory via sorting | Real GPU hash table (open addressing / cuCollections) | GPU hash tables reach billions of lookups/s, e.g. DACHash 8.65 B queries/s ⚠ [SBAC-PAD](https://sol.sbc.org.br/index.php/sbac-pad/article/view/18640), [NVIDIA](https://developer.nvidia.com/blog/maximizing-performance-with-massively-parallel-hash-maps-on-gpus/) | 1–2 cycle content-addressable lookup at very low energy. **Hash/CAM unit**, only worth it if the hippocampus is a large share of time. |
| 7 | 6 GB VRAM spill | Run one job at a time, bf16, activation checkpointing, int8 spikes | Checkpointing cuts activation memory substantially at ~20–30% extra compute ⚠ (secondary blogs) | Not a hardware innovation target — every chip has finite memory. |
| 8 | L trains 15% slower | Expected to shrink a lot after 3, 4, 5 | — | Whatever gap is left after software fixes = the honest hardware motivation. **Training stays on GPUs.** |

**Bottom line:** problems 2, 5, 7 are pure software; 3, 4, 6 are mostly software for training; 1 is partly hardware; what is truly hardware is *fine-grained event-driven compute, low-bit arithmetic, on-chip state and learning, content-addressable memory, and running without launch overhead at batch 1*.

## 2. General GPU limits (not only L) — all hardware-level

| GPU limit | Evidence | Brain principle | Hardware direction | Build now (FPGA) or propose (chip)? |
|---|---|---|---|---|
| Memory wall: compute and memory far apart | Up to 84% of an A100's dynamic energy is data movement ✔ [Montpellier study](https://esploro.umontpellier.fr/esploro/outputs/conferenceProceeding/Analyzing-GPU-Energy-Consumption-in-Data/9941278009311); DRAM access ~1,000× an on-chip op ✔ [arXiv 2608.28048](https://arxiv.org/pdf/2608.28048) | Memory at the synapse | On-chip state; compute-in-memory / processing-in-memory | Build: on-chip state. Propose: CIM/PIM. Evidence: SRAM CIM macro 34.1 TOPS/W (65 nm), ~13× vs RTX 4070 on one attention op ✔ [arXiv 2511.12152](https://arxiv.org/pdf/2511.12152); HBM-PIM ~2× system energy efficiency on GPT-J ✔ [Samsung, Hot Chips 2023](https://hc2023.hotchips.org/assets/program/conference/day1/PIM/23_HC35_PIM_PNM_Samsung_final.pdf); compute-in-SRAM APU 54–118× less energy on one retrieval workload ✔ [Cornell MICRO 2025](https://www.csl.cornell.edu/~zhiruz/pdfs/apu-micro2025.pdf) |
| Dense, always-on compute | Computes zeros; 2:4 sparsity gives ~1.1–1.4× in practice ⚠ [Spheron](https://www.spheron.network/blog/myth-nvidia-s-2-4-sparsity-doubles-your-inference-throughput/) | Silent neurons cost nothing | Event-driven compute | Build. Event-driven SNN FPGA: ~15× energy efficiency vs earlier SNN designs ✔ [Sommer et al., TCAD 2022](https://arxiv.org/pdf/2203.12437). Caveat: savings do not always materialise ✔ [Plagwitz et al., "To Spike or Not to Spike?"](https://deepai.org/publication/to-spike-or-not-to-spike-a-quantitative-comparison-of-snn-and-cnn-fpga-implementations) |
| High-precision datapaths | fp16/fp32 everywhere | Low-precision signals | 4-bit spike datapath, shift-add | Build |
| Global synchronous execution, kernel scheduling | ~3–7 µs per launch; one GPU failure can restart a 16,384-GPU job (419 interruptions in 54 days) ✔ [DCD](https://datacenterdynamics.com/en/news/meta-report-details-hundreds-of-gpu-and-hbm3-related-interruptions-to-llama-3-training-run) | Local, asynchronous, fault-tolerant | Dataflow pipeline, clock gating; later asynchronous network-on-chip | Build: dataflow. Propose: asynchronous NoC |
| No on-chip learning | Training = separate huge backprop job | Local learning | Delta-rule fast-weight unit | Build |
| No content-addressable memory | Hash/sort emulation | Associative recall | Hash/CAM unit | Build (small) |
| Fixed silicon, short refresh cycles | 62 Mt e-waste in 2022, 22.3% recycled ✔ [UNITAR](https://unitar.org/about/news-stories/press/global-e-waste-monitor-2024-electronic-waste-rising-five-times-faster-documented-e-waste-recycling); GenAI 1.2–5 Mt by 2030 ✔ [IEEE Spectrum](https://spectrum.ieee.org/e-waste) | Plasticity | Reconfigurable fabric / chiplets that can be updated rather than replaced | Propose (speculative) |
| Heat and water | ~All electrical energy becomes heat; PUE 1.56 ✔ [Uptime 2024](https://www.datacenterknowledge.com/energy-power-supply/data-center-industry-survey-highlights-cost-ai-and-sustainability-challenges) | 20 W brain | Follows from energy per operation | Measure board power and temperature on the prototype; model water with PUE × WUE (projection) |

## 3. Order of work
1. Software fixes on the GPU (prompt Phase 0–2) → measure the remaining gap.
2. Co-design L-HW / L-Edge (prompt Phase 3) → integer golden model + test vectors.
3. Hardware: RTL of the Neural Processing Core on the FPGA, verified bit-exact against the golden model.
4. Compare: GPU (optimised) vs FPGA dense vs FPGA event-driven, energy/token, latency, identical outputs.

The full agent prompt for steps 1–2 is in [`prompts/L_architecture_changes_prompt.md`](../prompts/L_architecture_changes_prompt.md).
