# Limitations of today's GPUs and LLMs, and research on cutting AI's power, heat and water

Core scope: **less power, less heat, less water — by making AI do only the work a question actually needs.**
Status labels: ✔ peer-reviewed or primary source · ⚠ vendor, secondary or non-peer-reviewed · (mine) = my arithmetic.

---

## 1. The "2+2 problem": AI spends the same or more effort on easy questions

| Finding | Number | Source |
|---|---|---|
| A standard transformer runs **every layer for every token**, whether the token is easy or hard | Fixed compute per token (structural) | Architecture fact; see [arXiv 2510.05364](https://arxiv.org/pdf/2510.05364) on expressivity limits |
| Reasoning ("o1-like") models **overthink trivial questions** like 2+3 | Far more tokens than normal models for the same answer; mitigation cut tokens ~45% with no accuracy loss ⚠ | ✔ [Chen et al., "Do NOT Think That Much for 2+3=?", arXiv 2412.21187](https://arxiv.org/abs/2412.21187); 45% figure via [alphaXiv](https://alphaxiv.org/overview/2412.21187v2) ⚠ |
| Reasoning models write ~14× more tokens per answer | 543.5 vs 37.7 tokens per question; up to **50× more CO₂** per query | ✔ Dauner et al., Frontiers in Communication 2025 ([coverage](https://letsdatascience.com/news/ai-reasoning-models-consume-up-to-100x-more-energy-51d9a9c9)) |
| Across 40 open models, reasoning mode used ~**100× more energy** on average | 1,000 prompts | ⚠ Hugging Face AI Energy Score, Dec 2025, not peer-reviewed ([Fortune](https://fortune.com/2025/12/05/ai-reasoning-energy-problem-data-centers-30-times-more-power)) |
| Size-matched comparison: reasoning overhead 1.7–14.3× | Shrinks with model size | ✔ [arXiv 2606.13111](https://arxiv.org/pdf/2606.13111) |
| General-purpose generative models cost **orders of magnitude** more per inference than task-specific ones, even at equal size | 88+ models, 10 tasks | ✔ [Luccioni, Jernite, Strubell 2023, arXiv 2311.16863](https://arxiv.org/abs/2311.16863) |
| Most queries don't need the big model | Router kept 95% of GPT-4 quality sending only **14–26%** of queries to it; cost −85% (MT-Bench), −45% (MMLU), −35% (GSM8K) | ✔ [RouteLLM, LMSYS 2024](https://lmsys.org/blog/2024-07-01-routellm/) |
| Energy of one chat prompt today | Gemini median **0.24 Wh, 0.26 mL water**; ChatGPT ~**0.3 Wh** (Epoch), 0.34 Wh (OpenAI) | ⚠ [Google via DCD](https://www.datacenterdynamics.com/en/news/google-median-gemini-prompt-uses-024-watt-hours-of-power-and-consumes-026ml-of-water/); [Epoch AI](https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use) |

**Takeaway:** one prompt is small; billions a day are not. Today neither the models (fixed depth, long reasoning) nor the hardware (dense, batch-oriented) can cheaply scale effort **down** for easy inputs. SPARK's rule: **effort proportional to difficulty.**

---

## 2. Every major GPU limitation today

### A. Compute model
| Limitation | Evidence |
|---|---|
| Computes every value densely; only fixed 2:4 weight sparsity, ~1.1–1.4× in practice | ✔ [NVIDIA](https://developer.nvidia.com/blog/structured-sparsity-in-the-nvidia-ampere-architecture-and-applications-in-search-engines); ⚠ [Spheron](https://www.spheron.network/blog/myth-nvidia-s-2-4-sparsity-doubles-your-inference-throughput/) |
| Batch-1 token generation runs at **~1% of peak FLOPS** (memory-bound, ~1 FLOP/byte) | ⚠ [ZeroEntropy](https://www.zeroentropy.dev/concepts/arithmetic-intensity/), [DEV](https://dev.to/ji_ai/why-llm-decoding-is-memory-bound-prefill-vs-decode-roofline-223f) |
| Poor at sequential/recurrent and tiny-matrix work; per-kernel launch ~3–7 µs | ⚠ [arXiv 2604.17861](https://arxiv.org/pdf/2604.17861), NVIDIA forums |
| Skipping work (early exit, routing) breaks batching, so FLOP savings rarely become energy savings on GPUs | ✔ [Survey arXiv 2403.07965](https://arxiv.org/html/2403.07965v2) |

### B. Memory
| Limitation | Evidence |
|---|---|
| **Up to 84%** of dynamic energy is data movement | ✔ [A100 study](https://esploro.umontpellier.fr/esploro/outputs/conferenceProceeding/Analyzing-GPU-Energy-Consumption-in-Data/9941278009311) |
| DRAM access ~1,000× an on-chip operation | ✔ [arXiv 2608.28048](https://arxiv.org/pdf/2608.28048) |
| Transformer KV cache grows with context; can reach **160× the weights** (batch 16, 262k context) | ✔ [QuantSpec, arXiv 2502.10424](https://arxiv.org/pdf/2502.10424) |
| HBM is a supply-chain chokepoint | ⚠ [Lyceum](https://lyceum.technology/magazine/what-limits-gpu-availability-hbm-cowos-and-power/) |

### C. Utilisation and idle waste
| Limitation | Evidence |
|---|---|
| Training clusters: median GPU utilisation **~45–65%** (Microsoft Philly) | ✔ [ATC'19](https://www.usenix.net/sites/default/files/conference/protected-files/atc19-slides-jeon.pdf) |
| Inference cluster: utilisation **<60% for >99% of GPUs** | ✔ [MuxFlow, arXiv 2303.13803](https://arxiv.org/pdf/2303.13803) |
| Idle GPUs still draw ~70–100 W | ⚠ [Last9](https://last9.io/blog/the-gpu-metrics-that-actually-matter) |
| **10%** of a Gemini prompt's energy is idle machines kept ready | ⚠ [Google via DCD](https://www.datacenterdynamics.com/en/news/google-median-gemini-prompt-uses-024-watt-hours-of-power-and-consumes-026ml-of-water/) |

### D. Power and heat
| Limitation | Evidence |
|---|---|
| 700 W (H100) → 1,000 W (B200) → ~1,200 W (GB200) per chip; racks ~120–132 kW | ✔ [SemiAnalysis](https://inferencex.semianalysis.com/chips/gb200-nvl72) |
| Hotspot thermal throttling silently cuts clocks | ⚠ [Netdata](https://www.netdata.cloud/guides/nvidia-gpu/nvidia-gpu-throttle-reasons/) |
| Average PUE stuck at **1.56** for five years | ✔ [Uptime 2024](https://www.datacenterknowledge.com/energy-power-supply/data-center-industry-survey-highlights-cost-ai-and-sustainability-challenges) |

### E. Reliability and lifespan
| Limitation | Evidence |
|---|---|
| 419 unexpected interruptions in 54 days on 16,384 H100s; ~52% from GPU or HBM | ✔ [Meta via DCD](https://datacenterdynamics.com/en/news/meta-report-details-hundreds-of-gpu-and-hbm3-related-interruptions-to-llama-3-training-run) |
| "1–3 year lifespan" claim | ⚠ anonymous source, disputed by Google ([TrendForce](https://www.trendforce.com/news/2024/10/31/news-datacenter-gpus-may-have-an-astonishingly-short-lifespan-of-only-1-to-3-years)) |
| E-waste: Gen-AI 1.2–5 Mt by 2030; world 62 Mt (2022), 22.3% recycled | ✔ [IEEE Spectrum](https://spectrum.ieee.org/e-waste), [UNITAR](https://unitar.org/about/news-stories/press/global-e-waste-monitor-2024-electronic-waste-rising-five-times-faster-documented-e-waste-recycling) |

### F. Software lock-in and access
| Limitation | Evidence |
|---|---|
| CUDA moat: new hardware must re-build a decade of kernels | ⚠ [The Register](https://www.theregister.com/2024/12/17/nvidia_cuda_moat/) |
| Industry has **>1,000× the compute** of universities | ✔ [Stanford HAI 2024](https://hai.stanford.edu/sites/default/files/2024-12/HAI-issue-brief-expanding-academia-role-public-sector.pdf); [Besiroglu et al., arXiv 2401.02452](https://arxiv.org/abs/2401.02452) |
| India: subsidised GPUs ~₹65–100/hour via IndiaAI (~34–38k GPUs) | ⚠ [Morung Express](https://morungexpress.com/indiaai-mission-34381-gpus-onboarded-from-14-empanelled-service-providers) |

---

## 3. Limitations of today's LLM architectures (transformers)
| Limitation | Evidence |
|---|---|
| Attention cost grows **quadratically** with context; FFN is ~half the compute | ✔ [Efficient Transformers survey](https://arxiv.org/pdf/2009.06732), [arXiv 2510.05364](https://arxiv.org/pdf/2510.05364) |
| KV cache memory grows linearly with context and dominates long-context decode | ✔ [arXiv 2502.10424](https://arxiv.org/pdf/2502.10424) |
| Fixed compute per token; limited state tracking (TC⁰ class); weak length generalisation | ✔ [arXiv 2510.05364](https://arxiv.org/pdf/2510.05364) |
| No continual learning: new knowledge overwrites old (catastrophic forgetting) | ✔ [arXiv 2404.07518](https://arxiv.org/pdf/2404.07518) |
| Tokenisation errors ("curse of tokenisation") | ✔ [arXiv 2406.11687](https://arxiv.org/pdf/2406.11687) |
| Hallucination | ✔ [Survey arXiv 2311.05232](https://arxiv.org/pdf/2311.05232) |
| Overthinking and general-purpose overkill | §1 above |

**How L answers these (to be proven at scale):** constant cost per token and no KV cache (memory doesn't grow); byte-level (no tokeniser); fast-weight memory that updates while reading (a form of continual adaptation); exact recall via the hippocampus (copying 2,048 bytes back, ~95%); 90–98% silent neurons.

---

## 4. What limits development of new architectures like L
| Barrier | Evidence |
|---|---|
| **Hardware lottery**: ideas win when they fit the chip | ✔ [Hooker 2020](https://arxiv.org/abs/2009.06489) |
| GPU kernels/libraries are built for transformers; L needed custom kernels and still trains 15% slower | Our measurements (8 problems) |
| CUDA moat for custom operations | ⚠ [The Register](https://www.theregister.com/2024/12/17/nvidia_cuda_moat/) |
| Compute divide: academia can't test at scale | ✔ [Stanford HAI](https://hai.stanford.edu/sites/default/files/2024-12/HAI-issue-brief-expanding-academia-role-public-sector.pdf) |
| Neuromorphic tooling fragmented ("Software Gap"); no standard benchmarks until NeuroBench | ✔ [arXiv 2603.26722](https://arxiv.org/pdf/2603.26722), [NeuroBench](https://www.physiologie.unibe.ch/PublicationPDF/Yik2025NeuroBench.pdf) |

---

## 5. Research on cutting power, heat and water — what works and how much

### Model / algorithm level
| Technique | Measured result | Source |
|---|---|---|
| Route easy queries to small models | −35% to −85% cost at ~95% quality | ✔ [RouteLLM](https://lmsys.org/blog/2024-07-01-routellm/) |
| Stop overthinking | ~45% fewer reasoning tokens, same accuracy | ⚠ [arXiv 2412.21187](https://arxiv.org/abs/2412.21187) |
| INT4 quantisation | −13% to −47% J/token on edge models; but +121% on one model, and +23% on a reasoning model (longer chains) | ✔ [arXiv 2504.03360](https://arxiv.org/pdf/2504.03360) |
| Speculative decoding | Up to 2.84× less energy than greedy (low batch only) | ✔ [arXiv 2407.09722](https://arxiv.org/html/2407.09722v1), [arXiv 2602.09113](https://arxiv.org/pdf/2602.09113) |
| Activation sparsity on GPUs | >2× (Deja Vu), up to 11.69× best case (PowerInfer) | ✔ [arXiv 2310.17157](https://arxiv.org/abs/2310.17157), [arXiv 2312.12456](https://arxiv.org/html/2312.12456v2) |
| Delta (change-only) networks | 5–100× fewer operations, up to 10× fewer DRAM accesses | ✔ [EdgeDRNN](https://arxiv.org/pdf/2012.13600) |

### Hardware level
| Technique | Result | Source |
|---|---|---|
| Neuromorphic (Loihi 2, MatMul-free LM) | ≥14× less energy/token than H100 in generation | ✔ [arXiv 2503.18002](https://arxiv.org/pdf/2503.18002) |
| Memory-in-compute (IBM NorthPole) | 72.7× energy efficiency vs GPU (IBM-reported) | ⚠ [IBM](https://research.ibm.com/blog/northpole-llm-inference-results) |
| Processing-in-memory (Samsung HBM-PIM) | ~2× system energy efficiency | ⚠ [Hot Chips 2023](https://hc2023.hotchips.org/assets/program/conference/day1/PIM/23_HC35_PIM_PNM_Samsung_final.pdf) |
| Small specialised co-processor (TPU SparseCore) | 5–7× on embeddings at ~5% area/power | ✔ [arXiv 2304.01433](https://arxiv.org/pdf/2304.01433) |

### Operations level
| Technique | Result | Source |
|---|---|---|
| GPU power capping | −12–15% energy for ~3% longer runs (another report: −13.7%, +6.8%) | ✔ [MIT Lincoln Lab](https://www.ll.mit.edu/news/ai-models-are-devouring-energy-tools-reduce-consumption-are-here-if-data-centers-will-adopt) |
| Full-stack software + hardware + ops (Google) | Energy per Gemini prompt −33× in 12 months | ⚠ [Google via DCD](https://www.datacenterdynamics.com/en/news/google-median-gemini-prompt-uses-024-watt-hours-of-power-and-consumes-026ml-of-water/) |
| Carbon- and water-aware scheduling | −14% water footprint | ✔ [WaterWise, arXiv 2501.17944](https://arxiv.org/html/2501.17944v2) |

### Facility level (complementary to us)
| Technique | Result | Source |
|---|---|---|
| Liquid cooling | Up to ~30% less energy than air (secondary); cold plates capture up to 94% of heat | ⚠ [Linköping](https://ecp.ep.liu.se/index.php/sims/article/download/747/652), [ACEEE 2026](https://www.aceee.org/sites/default/files/proceedings/ssb26/pdfs/372_0959_1434_001207.pdf) |
| Waste-heat reuse (district heating) | Viable; 0.6–7.3% operating cost saving in an Espoo case | ✔ [UPC/TU Wien](https://repositum.tuwien.at/handle/20.500.12708/208093?mode=full) |
| AI water footprint | GPT-3 training ~700,000 L directly evaporated; global AI 4.2–6.6 billion m³ withdrawal projected in 2027 | ✔ [Li et al., arXiv 2304.03271](https://arxiv.org/abs/2304.03271v2) |

**Where SPARK fits:** facilities remove heat better; schedulers move it to better places and times; SPARK **removes the heat at the source** by not doing unnecessary computation. These stack.

---

## 6. SPARK + L: limitation → mechanism → what we measure
| Limitation | SPARK/L mechanism | Metric on the prototype |
|---|---|---|
| Same effort for 2+2 as for hard input | Confidence-gated depth (early exit), recall-bypass via hippocampus, per-token energy budget | Average layers used per token; energy/token on easy vs hard text |
| Dense compute of silent neurons | Event-driven sparse engine | Ops/token, sparsity on vs off |
| Recomputing unchanged values | Delta (change-only) spikes, lazy updates | Messages/token, state reads/token |
| Memory wall, KV cache growth | On-chip constant-size state, no KV cache | Bytes moved/token; flat vs context length |
| Wide precision | 4-bit spikes, integer state | Bits moved/token |
| Kernel launches, idle waste | Fixed dataflow pipeline, clock gating | Idle vs active power |
| Heat | All of the above | Board power (W) and temperature rise (°C) |
| Water | Follows energy | Projected litres = kWh × PUE × WUE (labelled projection) |

## 7. Out of our scope (say it plainly)
Training-scale efficiency, facility cooling design, grid carbon, and chip manufacturing footprint. We complement those; we don't solve them.
