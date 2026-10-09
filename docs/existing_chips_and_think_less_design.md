# Existing AI/brain chips: how they are built, where they fall short, and SPARK's "think less, work less" design

## 1. Positioning (fixed)
SPARK does **not** replace the GPU. It is an **efficiency co-processor** that sits next to (and later inside) a GPU system and takes over the work GPUs do badly: sparse, recurrent, memory-heavy, brain-like inference. The GPU keeps training and dense maths.

Precedent: Google did exactly this inside TPU v4. Its systolic array is poor at sparse, irregular lookups, so Google added a small **SparseCore** that speeds embedding-heavy models **5–7× using ~5% of die area and power** ([TPU v4 paper, arXiv 2304.01433](https://arxiv.org/pdf/2304.01433)). SPARK is the same move for brain-like AI.

## 2. Existing chips

### Neuromorphic (brain-inspired) chips
| Chip | How it is built | Proven strengths | Weak points |
|---|---|---|---|
| **Intel Loihi 2** (2021) / **Hala Point** (2024) | 128 asynchronous digital "neuro cores" per chip, up to ~8k neurons each, programmable neuron microcode, graded (integer) spikes, programmable on-chip learning rules, 6 embedded CPU cores, mesh network; Hala Point = 1,152 chips, 1.15 B neurons, ≤2,600 W ([arXiv 2111.03746](https://arxiv.org/pdf/2111.03746), [Intel](https://newsroom.intel.com/artificial-intelligence/intel-builds-worlds-largest-neuromorphic-system-to-enable-more-sustainable-ai)) | Orders-of-magnitude gains on recurrent, sparse, spike-timing workloads; a MatMul-free LM ran with ~2× less energy/token than a Jetson and ≥14× less than an H100 during generation ([arXiv 2503.18002](https://arxiv.org/pdf/2503.18002)) | Intel's own survey: feedforward deep networks show "modest if any benefit" ([Davies et al. 2021](https://proceedingsoftheieee.ieee.org/advancing-neuromorphic-computing-with-loihi-a-survey-of-results-and-outlook/)); slower on large multi-chip networks (inter-chip congestion); research-only access via INRC ([Lava](https://pypi.org/project/lava-nc/0.8.0)); LLM results small (370M) and "preliminary"; H100 beat it on prefill |
| **IBM TrueNorth** (2014) → **NorthPole** (2023) | NorthPole: 256 cores, 224 MB SRAM interleaved with compute, no off-chip memory for weights, inference only ([The Register](https://www.theregister.com/2023/10/23/ibm_says_northpole_chip_has/)) | 3B LLM on 16 chips: 28,356 tokens/s, <1 ms/token, IBM-reported 72.7× more energy-efficient than the lowest-latency GPU ([IBM](https://research.ibm.com/blog/northpole-llm-inference-results)) | Model must fit in on-chip memory → big models split across many chips ("We can't run GPT-4 on this" — IBM); inference only; no learning; dense, not event-driven |
| **SpiNNaker2** (TU Dresden / SpiNNcloud) | 152 ARM Cortex-M4F cores per chip, 128 KB SRAM each, per-core voltage/frequency scaling, 22 nm FDSOI; neurons are software on the cores ([arXiv 2401.04491](https://arxiv.org/pdf/2401.04491), [arXiv 1911.02385](https://arxiv.org/pdf/1911.02385.pdf)) | Very flexible; >10× power efficiency vs SpiNNaker 1; huge brain simulations | General-purpose CPU cores cost more energy per operation than fixed circuits; aimed at brain simulation more than language models; "18× vs GPU" is a vendor claim |
| **BrainChip Akida** | Digital event-based processor/IP for edge; Akida 2 adds 8-bit and state-space "TENN" models ([edge-ai-vision](https://www.edge-ai-vision.com/2025/08/brainchip-launches-akida-cloud-for-instant-access-to-latest-akida-neuromorphic-technology/)) | Low-power edge inference | Small models only; slow commercial traction: ~US$0.4 M customer receipts vs ~US$4.3 M spend in one quarter ([Börse Express](https://www.boerse-express.com/news/articles/brainchip-aktie-cash-burn-haelt-an-863349)) |
| **Innatera T1** | Analog mixed-signal spiking neuron-synapse array + RISC-V CPU + CNN accelerator, 384 KB memory ([EE Journal](https://eejournal.com/article/bringing-innate-intelligence-to-trillions-of-devices)) | Sub-milliwatt always-on sensing | Needs dedicated SNNs that "cannot be derived from mainstream" models; analog noise and chip-to-chip mismatch ([arXiv 2106.10382](https://arxiv.org/pdf/2106.10382)); sensor-scale only |
| **SynSense Speck** | Vision sensor + neuromorphic processor on one chip ([eeNews](https://www.eenewseurope.com/en/synsense-raises-us10-million-for-smart-vision-sensor/)) | Ultra-low-power vision | Single niche (event cameras) |

### Non-neuromorphic AI accelerators
| Chip | How it is built | Weak points |
|---|---|---|
| **NVIDIA GPU** | Thousands of SIMT threads + tensor cores + HBM | Only fixed 2:4 weight sparsity, ~1.1–1.4× real gain ([Spheron](https://www.spheron.network/blog/myth-nvidia-s-2-4-sparsity-doubles-your-inference-throughput/)); up to 84% of dynamic energy on data movement |
| **Google TPU** | Large systolic arrays: every unit computes every cycle in lockstep | Sparse/irregular work leaves units idle; zeros must be stalled on or decompressed ([FlexTPU, U. Michigan](https://tnm.engin.umich.edu/wp-content/uploads/sites/353/2023/03/2022.10.FlexTPU.pdf)) → Google added SparseCore |
| **Groq LPU** | Weights only in on-chip SRAM (230 MB/chip), deterministic compiler-scheduled pipeline, ~375 W/chip | A 70B model needs ~300–576 chips; small batches ([arXiv 2503.09650](https://arxiv.org/html/2503.09650v1), [Introl](https://introl.com/blog/groq-lpu-infrastructure-ultra-low-latency-inference-guide-2025)) |
| **Cerebras WSE-3** | One whole wafer, 44 GB SRAM, ~23 kW, liquid cooled | Extreme heat density; models larger than the wafer go to off-wafer MemoryX ([Introl](https://introl.com/blog/cerebras-wafer-scale-engine-cs3-alternative-ai-architecture-guide-2025)) |
| **Etched Sohu** | Transformer attention hard-wired in silicon | Lock-in: cannot run RNNs, CNNs or new architectures; no independent benchmarks ([The Register](https://www.theregister.com/2024/06/26/etched_asic_ai/)) |

## 3. Weak points across the whole field = SPARK's opening
| Gap in existing chips | Evidence | SPARK's answer |
|---|---|---|
| **Software gap**: models must be hand-converted or redesigned for each chip | Reviews call it "the primary bottleneck" ([arXiv 2603.26722](https://arxiv.org/pdf/2603.26722)) | Model and chip co-designed: L is trained in PyTorch and exported automatically (integer golden model, test vectors) |
| **Accuracy gap**: spiking nets trail standard ML | [Frontiers editorial 2024](https://bohrium.dp.tech/paper/arxiv/26422422) | L already beats a same-size transformer at 9M params (to be replicated with 3+ seeds) |
| **Gains vanish on dense/feedforward work** | Loihi survey; on MNIST "no or little" SNN advantage ([Plagwitz et al.](https://arxiv.org/pdf/2306.12742)); neuron-state memory access can cancel savings ([arXiv 2306.15749](https://arxiv.org/pdf/2306.15749)) | Target only the workloads where brain-style wins (recurrent, sparse, long context); lazy neuron updates (below) remove the state-access cost; prove each saving with an on/off ablation |
| **Memory capacity**: on-chip SRAM limits model size | NorthPole, Groq | L's state is constant-size per token (no growing KV cache); only active weight rows are fetched |
| **Lock-in to one model family** | Etched | Configurable core (layer sizes, neuron rules); FPGA first |
| **Heat density** | Cerebras 23 kW per wafer | Low activity → low power density by design |
| **No language-model memory**: no chip combines event-driven compute + fast-weight learning + associative recall for language | None found | SPARK's fast-weight unit + hippocampus unit |

## 4. "Think less, work less, produce more" — SPARK's design rule
**Do nothing unless something changed, matters, or is new.** Each mechanism is a hardware feature, each needs a matching change in L, and each is proven with an on/off ablation.

| # | Mechanism | What is skipped | Evidence it works | Change needed in L |
|---|---|---|---|---|
| 1 | **Silent-neuron skip** (event-driven) | Neurons that don't fire: 90–98% in L | Event-driven SNN FPGA ~15× energy efficiency vs earlier designs ([Sommer et al.](https://arxiv.org/pdf/2203.12437)) | Already in L (energy budget) |
| 2 | **Change-only (delta) messages** | Neurons whose value barely changed since the last token | Delta networks: 5–100× fewer operations, up to 10× fewer DRAM accesses ([EdgeDRNN](https://arxiv.org/pdf/2012.13600)) | Train with a delta threshold on spike/activation changes |
| 3 | **Lazy neuron updates** | Updating idle neurons every token; decay applied only when next touched (a^Δt from a lookup table) | Answers the "state memory access cancels savings" critique ([arXiv 2306.15749](https://arxiv.org/pdf/2306.15749)) | Decay must be exactly computable as a^Δt (integer/shift form) |
| 4 | **Recall instead of recompute** | The whole deep stack when the hippocampus finds an exact match (copying) | L copies at 2,048 bytes with ~95% accuracy | Add a confidence gate: on a confident hit, output directly |
| 5 | **Early exit** | Remaining layers when an early layer is already confident | Early-exit / mixture-of-depths literature ([arXiv 2404.02258](https://arxiv.org/html/2404.02258v1), [survey arXiv 2403.07965](https://arxiv.org/html/2403.07965v2)) | Train small exit heads on intermediate layers |
| 6 | **Hardware energy budget** | Any spikes beyond a per-token cap (a register sets max energy per token) | L's homeostasis already limits firing | Make the budget an integer cap the hardware enforces |
| 7 | **Low precision + clock gating** | Wide arithmetic; idle blocks are switched off | Standard low-power design | 4-bit spikes, integer state (already in the prompt's Phase 3) |

Honest caveat: on GPUs, skipping work often fails to save energy because irregular work breaks batching. That is why these mechanisms need hardware — and why each must be measured, not assumed.
