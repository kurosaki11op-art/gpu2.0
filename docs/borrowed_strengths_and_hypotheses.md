# What SPARK borrows from GPUs and other chips, and new hypotheses to test

Principle: **keep what makes GPUs and other AI chips strong, adapt it to event-driven, think-less computing, and drop what wastes energy.**

## 1. GPU strengths and how SPARK adapts them

| GPU strength | Why it works on GPUs | SPARK adaptation | Prototype? |
|---|---|---|---|
| **Latency hiding with many warps** (zero-overhead switching between thread groups) | While one warp waits on memory, another computes (Little's law) ([GPU fundamentals](https://icl.utk.edu/~bosilca/classes/cosc462/2016/pdf/GPU_Fundamentals.pdf)) | **Multi-stream contexts**: 2–4 independent input streams (users or sensor channels) interleave in the pipeline, each still batch-1, so SDRAM waits are hidden without batching penalties | ✔ (2 streams) |
| **Memory coalescing** (neighbouring threads' accesses merged into one transaction) | Few large transfers instead of many small ones | **Address-sorted spike queue**: active neurons sorted/bucketed by weight address so sparse fetches become SDRAM burst reads | ✔ |
| **Shared memory scratchpad** (programmer-managed fast SRAM) | Data reused on chip, fewer DRAM trips | **Compiler-managed SRAM** with **hot/cold neuron split**: frequently firing neurons' weights pinned on chip, rare ones streamed (PowerInfer's hot/cold idea, [arXiv 2312.12456](https://arxiv.org/html/2312.12456v2)) | ✔ |
| **Tensor Memory Accelerator + warp specialization** (Hopper: a copy engine runs ahead while compute warps work; producer–consumer pipeline) ([NVIDIA Hopper](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/)) | Data movement overlaps compute | **Predictive prefetch engine**: predicts the next token's active neurons from the current ones and prefetches their weights into a double buffer | ✔ |
| **Tensor cores** for dense maths | Very efficient dense MACs | **Small dense MAC array** for the dense parts (projections, output head); hybrid with the event engine | ✔ (output head) |
| **Microscaling formats (MXFP4/NVFP4)**: blocks of 16–32 values share one scale; ~4.25 bits per value ([MX paper](https://ar5iv.labs.arxiv.org/html/2310.10537)) | Near-8-bit accuracy at 4-bit cost | **Block-scaled 4-bit integer weights with a power-of-two scale per block** (scale = a shift, no multiplier) | ✔ |
| **Transformer Engine** (precision chosen per layer, dynamically) ([NVIDIA Blackwell](https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/)) | Low precision where safe | **Precision on demand**: instinct path at 4-bit, deliberate path may use 8-bit; precision becomes part of "effort" | Stretch |
| **2:4 structured sparsity** | Structured patterns are cheap in hardware; random sparsity costs "drastic" overheads ([S2TA, arXiv 2107.07983](https://arxiv.org/pdf/2107.07983v1.pdf)) | **Block-structured spikes**: neurons fire/stay silent in small groups (4–8) to cut control overhead | ✔ (option) |
| **Thread-block clusters + multicast** (one load broadcast to many SMs) | Shared data fetched once | **Spike multicast** between tiles on an on-chip network | Proposal |
| **CUDA graphs / static scheduling** | Removes launch overhead | **Fixed per-token pipeline** (already in SPARK) | ✔ |
| **Decompression engine** (Blackwell) | Fewer bytes moved | **Compressed weights in SDRAM** (sparse/entropy-coded), decompressed on the fly | Stretch |
| **RAS engine** (fault prediction, diagnostics) | Fewer failures and downtime | **Mini-RAS**: SRAM parity, health counters, ability to map out a failed tile | ✔ counters / proposal |
| **Power management (DVFS, clock gating)** | Lower power when idle | **Controller-driven clock gating per unit**; DVFS per tile in the chip proposal | ✔ |

## 2. Strengths of other chips SPARK also adopts

| Chip | Strength | SPARK use |
|---|---|---|
| Intel Loihi 2 | Asynchronous mesh, graded (integer) spikes, programmable neuron microcode, on-chip learning | Graded 4-bit spikes; configurable neuron constants; learning unit |
| IBM NorthPole | Memory interleaved with compute, deterministic | Weight/state-stationary tiles; bit-exact design |
| Groq LPU | Compiler-scheduled, deterministic, no caches | Fixed pipeline with predictable per-token timing |
| Google TPU SparseCore | Small specialised unit beside the main engine, 5–7× on sparse work for ~5% area/power ([arXiv 2304.01433](https://arxiv.org/pdf/2304.01433)) | SPARK as an add-on tile beside the GPU |
| AMD 3D V-Cache | Stacked SRAM, <1/3 energy per bit vs microbump links, 2 TB/s ([WikiChip](https://fuse.wikichip.org/?p=5531)) | Proposal: SPARK tile with stacked SRAM |
| Chiplets (UCIe) | Mix dies from different vendors in one package ([arXiv 2509.18355](https://arxiv.org/pdf/2509.18355)) | Proposal: SPARK chiplet in the same package as a GPU |
| IBM HERMES analog in-memory chip | 9.76 TOPS/W peak, but only 3–4-bit effective precision ([arXiv 2212.02872](https://www.arxiv.org/pdf/2212.02872)) | Proposal: L's 4-bit spikes may suit analog in-memory compute |
| Asynchronous (clockless) circuits | Clock tree can use ~10–50% of dynamic power; TrueNorth used asynchronous circuits | Aggressive clock gating now; clockless tiles as a proposal |
| Energy-proportional computing (Barroso & Hölzle 2007) | Servers mostly run at 10–50% utilisation, where efficiency is poor ([paper](https://www.cs.princeton.edu/courses/archive/spring13/cos598C/Barroso07_EnergyProp-clean.pdf)) | Design goal: **energy proportional to work done** |

## 3. New hypotheses we can test (software first, then on the FPGA)

| # | Hypothesis | How we test it | Where |
|---|---|---|---|
| H1 | **Energy proportionality**: SPARK's energy per token grows with work done (easy → little, hard → more) with a low idle floor; a GPU's does not | Plot energy/token vs work counters on easy vs hard text, both platforms | FPGA + GPU |
| H2 | **Predictable activity**: the set of neurons active at token t+1 overlaps strongly with the set at t, so weights can be prefetched | Measure overlap (Jaccard) of consecutive active sets in L; simulate prefetch hit rate | Software |
| H3 | **Hot neurons**: a small fraction of neurons does most of the firing (power-law), so pinning them in SRAM covers most fetches | Firing-frequency histogram per layer; coverage of top-k% neurons | Software |
| H4 | **Block-structured spikes** keep ≥80% of the sparsity saving with far less control overhead | Train L with group sparsity (4–8 neurons); compare bits/byte, operations, memory bursts | Software + FPGA |
| H5 | **Address-sorted spike queues** raise SDRAM burst efficiency (coalescing for events) | Count bursts and bytes with/without sorting on the FPGA | FPGA |
| H6 | **Block-scaled 4-bit weights with shift scales** keep L's quality within seed noise of 8-bit | Quantisation-aware training, 3 seeds | Software |
| H7 | **Precision on demand**: the instinct path tolerates lower precision than the deliberate path | Measure accuracy per path at 4 vs 8 bits | Software |
| H8 | **Multi-stream interleaving** hides memory latency without batching | Throughput and latency per stream with 1, 2, 4 streams on the FPGA | FPGA |
| H9 | **Controller-driven clock gating** cuts idle power by a large share of clock power | Board power with gating off vs on, idle and loaded | FPGA |
| H10 | **(Long-term) L's 4-bit spikes match analog in-memory precision limits (3–4 bits)**, making L a natural fit for analog compute | Simulate L with 3–4-bit noisy matrix-vector products | Software (proposal) |

## 4. Proposed additions to SPARK (prioritised)
- **Prototype (add to MVP if time allows):** hot/cold neuron memory split (H3), predictive prefetch with double buffer (H2), address-sorted spike queue (H5), block-scaled 4-bit weights (H6), 2 interleaved streams (H8), controller-driven clock gating and an energy-vs-work curve (H1, H9), parity and health counters.
- **Chip proposal only:** spike multicast on an on-chip network, stacked SRAM, SPARK chiplet beside a GPU, compressed weights + decompression, clockless tiles, analog in-memory tiles for spike layers (H10), tile mapping-out for fault tolerance.

## 5. What we keep from GPUs, and what we drop
- **Keep:** latency hiding, coalescing, scratchpad SRAM, async copy engines, structured formats, block scaling, static scheduling, reliability engines, power management.
- **Drop:** computing every value, fixed effort per token, synchronous lockstep across the whole chip, constant trips to off-chip memory, general-purpose flexibility where a fixed circuit is cheaper.
