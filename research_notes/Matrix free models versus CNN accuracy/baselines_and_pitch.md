# Efficiency baselines a new inference chip must beat, and what a credible pitch needs

Method note: direct page fetches were blocked in this session (egress proxy refused arxiv.org, iea.org, mlcommons.org, gwern.net etc.). Every figure below comes from WebSearch result summaries that quoted the cited pages; none was read from the full primary document. Items marked UNVERIFIED are not confirmed by any source read. The report writer should re-check key numbers against the primary links before publishing.

## (a) Edge hardware: MLPerf Tiny and tiny-chip energy per inference

### Takeaway
MLPerf Tiny CIFAR-10 image classification has an 85% top-1 target and energy is reported per inference in microjoules (optional). Published numbers I could verify are: Syntiant NDP120 keyword spotting 31.5-49.6 uJ, Cortex-M4/M7 ResNet-8 in the mJ range, and tiny MNIST chips from 633 pJ (95%) through 8.6 nJ (97.4%) to 0.36 uJ (98.4%). No verified Fashion-MNIST chip energy figure was found.

### Cited Findings
- MLPerf Tiny has four benchmarks (keyword spotting, visual wake words, image classification, anomaly detection), chosen by 50+ organisations, measuring accuracy, latency and energy — [MLPerf Tiny paper (search result)](https://arxiv.org/pdf/2106.07597)
- v0.5 image classification: CIFAR-10, ResNet of about 96 KB, quality target 85% top-1 — [ar5iv MLPerf Tiny](https://ar5iv.arxiv.org/html/2106.07597)
- Reference implementation on STM32 Nucleo-L4R5ZI (Cortex-M4): 7.9 ms for image classification at 77% accuracy, below the 85% target; energy is optional and the reference energy scores were the only energy scores in round 1 — [EE Times India](https://www.eetindia.co.in/mlperf-launches-tinyml-benchmark-for-smallest-ai-systems/). A different source lists 704.23 ms reference latency for this task; the two conflict and I could not resolve which applies — [Embedded Computing](https://embeddedcomputing.com/technology/ai-machine-learning/ai-dev-tools-frameworks/mlperf-tiny-inference-benchmark-lays-foundation-for-tinyml-technology-evaluation-commercialization)
- Official MLPerf energy method needs separate setups for latency, accuracy and energy; a 2025 third-party study ran each model 1000 times on an STM32N6; energy is reported per inference in uJ — [arXiv 2505.15622](https://arxiv.org/html/2505.15622v1)
- Independent ResNet-8 / CIFAR-10 measurement: Cortex-M4 Nucleo-32 about 298 ms and 8.9 mJ per frame; Cortex-M7 59.6 ms and 17.2 mJ per frame (third-party, arXiv ID as returned by search, not checked) — [arXiv 2609.11939](https://arxiv.org/pdf/2609.11939)
- Syntiant NDP120, v0.7 keyword spotting: 1.80 ms and 49.59 uJ at 1.1 V/100 MHz; 4.30 ms and 35.29 uJ at 0.9 V/30 MHz (system energy) — [EE Asia](https://www.eetasia.com/syntiant-leads-tinyml-benchmark-results/)
- Syntiant Core 2, v1.1 (vendor release, July 2023): 1.5 ms and 43.8 uJ per inference; low-energy point 31.5 uJ and 4.4 ms — [Syntiant press release repost](https://jotup.co/node/2463850)
- MLPerf Tiny v1.3 released 17 Sep 2025: 70 results, five tests, four submitters (Kai Jiang, Qualcomm, ST, Syntiant), new 1D DS-CNN streaming wake-word test — [GlobeNewswire](https://www.globenewswire.com/news-release/2025/09/17/3151817/0/en/MLCommons-New-MLPerf-Tiny-v1-3-Benchmark-Results-Released.html)
- GreenWaves claims GAP9 has the lowest energy on all four MLPerf Tiny v1.0 benchmarks (vendor claim, no numbers retrieved) — [GreenWaves](https://greenwaves-technologies.com/?p=8192)
- Alif DK-E8 (Cortex-M55 + Ethos-U85) DeiT-Tiny: 81.59 ms p50 (vendor model card, not an MLPerf result) — [Arm model card](https://huggingface.co/Arm/deit-tiny-int8-ethos-u-executorch)
- Jetson Orin Nano: up to 40 TOPS, power modes 7-15 W — [NVIDIA datasheet](https://static6.arrow.com/aropdfconversion/b4f120a8c52d5dd5e59875b129c4f94b77c7c3b6/jetson-orin-nano-datasheet-web.pdf)
- Coral Edge TPU 4 TOPS at about 2 W (about 2 TOPS/W, secondary and disputed by Hailo); Hailo-8 26 TOPS, 3 TOPS/W claimed — [CNX Software](https://www.cnx-software.com/2020/10/02/hailo-8-m-2-and-mini-pcie-ai-accelerator-cards-deliver-up-to-26-tops/)
- Tiny MNIST chips: 28 nm sparse DNN engine 98.36% at minimum 0.36 uJ/inference — [IBM Research listing](https://www.research.ibm.com/publications/dnn-engine-a-28-nm-timing-error-tolerant-sparse-deep-neural-network-processor-for-iot-applications); 65 nm all-digital Tsetlin machine 8.6 nJ/frame, 97.42% MNIST at 27.8 MHz — [arXiv 2501.19347](https://arxiv.org/html/2501.19347v2); 130 nm in-SRAM classifier 633 pJ per 10-way classification at 50 MHz, above 95% accuracy — [Princeton listing](https://collaborate.princeton.edu/en/publications/a-machine-learning-classifier-implemented-in-a-standard-6t-sram-a/)

### Inferences
- A matrix-free chip claiming "nJ per MNIST/Fashion inference" competes with the Tsetlin machine chip (8.6 nJ, 97.4%), a counting/logic-based, multiplier-free design. That is the closest published peer for L, and should be the first baseline cited.
- MLPerf Tiny energy (tens of uJ for KWS) is system-level (includes MCU, memory), so a bare-core nJ figure is not like-for-like; state the boundary.

### Gaps
- Exact current MLPerf Tiny v1.3 per-device energy/latency tables (GAP9, Ethos-U55/U85, Hailo, Edge TPU): not retrieved; the MLCommons results page was unreachable. Cortex-M reference energy beyond the third-party figures above: not found.
- No verified Fashion-MNIST tiny-chip energy number found.

## (b) SRAM-on-chip / in-memory accelerators

### Takeaway
Wafer-scale and SRAM-centric designs hold tens to hundreds of MB on chip and draw kW (Cerebras) or hundreds of W; none approach the nJ-per-inference scale of tiny chips. All figures are vendor numbers.

### Cited Findings
- Cerebras WSE-3: 4 trillion transistors, 900,000 cores, 44 GB on-chip SRAM, TSMC 5 nm, 125 PFLOPS peak; a CS-3 system draws 23 kW (system, not bare chip) — [Cerebras press release](https://www.cerebras.ai/press-release/cerebras-announces-third-generation-wafer-scale-engine), [DCD](https://www.datacenterdynamics.com/en/news/cerebras-unveils-four-trillion-transistor-giant-chip-targets-generative-ai). The 21 PB/s on-chip bandwidth I expected was NOT confirmed (UNVERIFIED).
- Groq GroqChip: 230 MB SRAM per chip, up to 80 TB/s on-die bandwidth, 14 nm, up to 750 TOPS INT8 / 188 TFLOPS FP16 at 900 MHz — [GroqChip product brief v1.7](https://groq.com/wp-content/uploads/2024/08/GroqChip™-Processor-Product-Brief-v1.7.pdf)
- Graphcore GC200 (Colossus MK2): 1,472 cores, 900 MB on-chip SRAM, no DRAM, 250 TFLOPS FP16, SRAM bandwidth 47.5 TB/s (TechRadar) vs 45 TB/s (Flopper) — conflicting; power of 250 W NOT confirmed (UNVERIFIED); C600 card is 185 W — [TechRadar](https://www.techradar.com/news/this-tiny-uk-startup-chipmaker-targets-intel-and-nvidia-with-monster-ai-cpu), [Flopper](https://flopper.io/gpu/graphcore-gc200)
- Axelera Metis AIPU: four cores, digital in-memory computing, peak 214 TOPS INT8, about 15 TOPS/W claimed, 6.65 TOPS/mm2; implied roughly 14 W is my arithmetic, not a spec; no independent measurements found — [Axelera](https://axelera.ai/axelera-ai-announces-metis-ai-platform), [Wikipedia](https://en.wikipedia.org/wiki/Axelera_AI)

### Inferences
- These chips still use dense matrix units (Groq 320x320 MAC array per secondary source; Axelera in-memory matrix-vector multipliers), so L's matrix-free design differs categorically; the comparison axis is energy per task and memory, not TOPS/W.

### Gaps
- Cerebras 21 PB/s, Graphcore power: unconfirmed. Digital IMC academic chips (ISSCC) not searched.

## (c) Energy cost hierarchy (Horowitz ISSCC 2014)

### Takeaway
At 45 nm, arithmetic costs fractions of a pJ to a few pJ while a DRAM access costs hundreds of pJ, so data movement dominates. No updated newer-node table was found.

### Cited Findings
- Horowitz, "Computing's Energy Problem (and what we can do about it)", ISSCC 2014 — [Gwern mirror](https://www.Gwern.net/doc/cs/hardware/2014-horowitz-2.pdf) (PDF not readable here; values below via secondary reproductions)
- 8-bit integer add 0.03 pJ; 8-bit integer multiply 0.2 pJ; 32-bit float add 0.9 pJ; 32-bit float multiply 3.7 pJ — [patent 11886973](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11886973), [patent 12632704](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12632704)
- 32-bit SRAM read 5 pJ (8 KB, 64-bit cache access about 10 pJ) — [patent 12632704](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12632704), [PMC8934428](https://pmc.ncbi.nlm.nih.gov/articles/PMC8934428/table/T3)
- 32-bit DRAM read 640 pJ (45 nm, 16-bit operands per another table; 2560 pJ for 64-bit) — [patent 11972137](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11972137), [arXiv 1602.04183](https://arxiv.org/pdf/1602.04183)
- A later Horowitz seminar slide: DRAM about 1 nJ per 32-bit word (about 30 pJ/bit) — [EPFL seminar slides](https://si2.epfl.ch/~demichel/si.epfl.ch/files/content/sites/si/files/shared/Seminar_Horowitz161209.pdf) (via search summary)

### Inferences
- DRAM:SRAM:add ratio is roughly 640 : 5 : 0.03 (about 20,000x between 8-bit add and 32-bit DRAM read), supporting a pitch built on avoiding DRAM and multiplies.

### Gaps
- The 1.3-2.6 nJ 64-bit DRAM range: UNVERIFIED (memory only). Newer-node (7 nm and below) equivalents: not found.

## (d) Data-centre power, water, e-waste

### Takeaway
IEA: data centres used about 415 TWh in 2024 (1.5% of world electricity) and reach about 945 TWh by 2030. Water and e-waste studies give large but scenario-dependent numbers.

### Cited Findings
- IEA Energy and AI (Apr 2025): 2024 about 415 TWh, about 1.5% of world electricity; 2030 Base Case about 945 TWh, just under 3%; 2035 about 1,200 TWh (range 700-1,700) — [IEA executive summary](https://www.iea.org/reports/energy-and-ai/executive-summary), [IEA energy demand](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai)
- AI-optimised data-centre demand to more than quadruple by 2030; US about 45% and China 25% of 2024 use; 2024-2030 increase about 530 TWh, about 8% of projected total demand growth — [PublicPower](https://www.publicpower.org/periodical/article/electricity-demand-data-centers-worldwide-set-more-double-2030-iea), [Carbon Brief](https://www.carbonbrief.org/ai-five-charts-that-put-data-centre-energy-use-and-emissions-into-context)
- Li et al., "Making AI Less Thirsty" (arXiv 2304.03271): v1 says about 500 ml of water per 20-50 questions-and-answers; "10-50 responses" appears only in secondary press; GPT-3 training water: 700,000 L directly evaporated (v2 abstract) vs 3.5 million L (v1 text) vs 5.4 million L (Domus); versions differ — [arXiv v2](https://arxiv.org/abs/2304.03271v2), [Domus](https://domusweb.it/en/news/2024/10/11/chatgpt-consumes-more-water-than-expected.html)
- Wang et al., Nature Computational Science, Oct 2024: generative-AI e-waste 1.2 to 5.0 million tonnes accumulated by 2030 (window 2020-2030 per publisher, 2023-2030 per some press); about 2,600 t in 2023 to 0.4-2.5 Mt per year in 2030; circular measures could cut up to 86%; based on DGX H100 benchmark — [Scimex](https://www.scimex.org/newsfeed/generative-ai-could-create-1-000-times-more-e-waste-by-2030), [Cosmos](https://cosmosmagazine.com/technology/ai/generative-ai-e-waste)

### Inferences
- Quote the IEA 415/945 TWh pair with year labels; flag the Li water numbers by paper version.

### Gaps
- IEA 2026 update, GPU cooling-water figures per rack/MW, and the Li et al. global withdrawal projection: not retrieved.

## (e) How reviewers judge efficiency-accuracy claims, and continual-learning baselines

### Takeaway
Reviewers expect a stated measurement boundary, a named benchmark with a quality floor (MLPerf Tiny style: meet an accuracy target, then compare latency/energy), and matched memory budgets. For continual learning, replay and joint-training bounds are mandatory; EWC/SI/LwF are expected as weak regularisation baselines.

### Cited Findings
- MLPerf Tiny structure: quality target first, latency and energy second, energy optional with separate measurement setups — see (a) sources.
- Split MNIST (van de Ven et al., 20 seeds), average accuracy Task-IL / Domain-IL / Class-IL: EWC 98.64 / 63.95 / 20.01; Online EWC 99.12 / 64.32 / 19.96; SI 99.09 / 65.36 / 19.99; LwF 99.57 / 71.50 / 23.85; generative replay (DGR) 99.50 / 95.72 / 90.79; DGR+distill 99.61 / 96.83 / 91.79; iCaRL (budget 2000) class-IL 94.57; none (fine-tune) class-IL 19.90 — [Three scenarios for continual learning](https://arxiv.org/pdf/1904.07734) (table text partially garbled in extraction)
- Later study, same protocol: EWC 18.9, SI 16.4, naive 18.7, LwF 24.2, replay with 200 stored samples per task 85.9 (class-IL) — [arXiv 2603.07415](https://arxiv.org/pdf/2603.07415)
- Regularisation methods fail in class-incremental; replay seems required — [van de Ven et al.](https://arxiv.org/pdf/1904.07734)
- Fair-comparison practice: fine-tuning as lower bound, joint training as flagged upper reference; huge replay buffers are unfair to regularisation methods; give memory in MB as a common unit; sweep buffer budgets (5/10/25/50% in one paper; 2000 default for Split CIFAR in another) — [CL survey](https://arxiv.org/pdf/1909.08383), [LibContinual](https://arxiv.org/pdf/2512.22029), [Flashbacks](https://arxiv.org/pdf/2506.00477), [drone replay paper](https://arxiv.org/pdf/2602.13440)

### Inferences
- A convincing win for L: (1) meet an accuracy floor on a named task (MNIST/Fashion/KWS), then show lower energy with the boundary stated; (2) accuracy at fixed memory in MB, counting stored replay/dream state; (3) class-incremental Split-MNIST/Fashion against replay with equal bytes, not only EWC/SI which sit near 20% and make weak baselines. Beating EWC/SI alone would not impress.
- Staged learning should be reported as average accuracy plus forgetting (backward transfer) per scenario, with the scenario (task/domain/class-IL) named.

### Gaps
- No explicit reviewer checklist found (ISSCC/NeurIPS guidelines were not located); the above is inferred from papers' own practices. Split-Fashion and Split-CIFAR typical numbers: not retrieved. Accuracy-at-iso-energy conventions: no source found.
