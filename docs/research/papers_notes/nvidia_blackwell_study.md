---
title: Study - NVIDIA data-centre GPU architecture up to Blackwell
tags: [l, research, hardware, gpu, memory]
---

# Study: NVIDIA data-centre GPU architecture, Volta to Blackwell

Purpose: learn exactly how the NVIDIA data-centre GPU moves data and where it wastes energy, so that L (a matrix-free,
multiplier-free counting chip with memory inside each tile) can be designed on its own terms. Nothing here is a plan
to copy the GPU. Date of study: 25 Oct 2026.

## 0. Method, sources, and what was blocked

Label rules used in this note: **MEASURED** = a microbenchmark in a paper we downloaded and read; **VENDOR** = a number
from a vendor or third-party spec sheet (not measured); **DERIVED** = arithmetic done here on other numbers;
**ESTIMATED** = a derived number that also needs an assumption; **UNVERIFIED** = could not be read in this session
(recalled from general knowledge or seen only in a search snippet). No number below was invented.

Read in full (PDF downloaded from arxiv.org, converted with pdftotext):

| arXiv id | Paper | What it covers |
|---|---|---|
| 1804.06826 | Dissecting the NVIDIA Volta GPU Architecture via Microbenchmarking (V100) | caches, TLB, register banks, shared memory, HBM2 |
| 2208.11174 | Demystifying the Nvidia Ampere Architecture ... (A100) | instruction and memory latency, tensor core latency/throughput |
| 2402.13499 | Benchmarking and Dissecting the Nvidia Hopper GPU Architecture (H800 PCIe, A100, RTX 4090) | memory latency/bandwidth, wgmma, energy, DSM, TMA, DPX, FP8 LLM |
| 2501.12084 | Dissecting the NVIDIA Hopper Architecture through Microbenchmarking and Multiple Level Analysis | extended version: partitioned L2, wgmma energy, DSM, TMA |
| 2507.10789 | Dissecting the NVIDIA Blackwell Architecture with Microbenchmarks | **consumer** GB203 (RTX 5080) versus H100 PCIe; not B200 |
| 2512.02189 (v3) | Microbenchmarking NVIDIA's Blackwell Architecture: An in-depth Architectural Analysis | **B200**: TMEM, decompression engine, tcgen05, FP4/FP6, LLM and training runs |
| 2509.25149 | Pretraining Large Language Models with NVFP4 | FP4 formats and training recipe on Blackwell |
| 1903.04611 | Evaluating Modern GPU Interconnect: PCIe, NVLink, NV-SLI, NVSwitch and GPUDirect | NVLink v1/v2, NVSwitch (V100 era) |
| 2608.28048 | AI Hardware Accelerators for LLMs: Architectures and the Memory Wall (survey, 2026) | secondary source for specs, rooflines, Groq/Cerebras context |

Other arXiv Blackwell titles seen in the search but NOT read: 2610.20354 (Grace-Blackwell unified memory),
2605.04178 (analytical models across architectures), 2608.26575 (confidential computing on Blackwell), 2607.23402
(warp divergence Pascal to Blackwell), 2606.23969 (serialized bridge, Blackwell confidential computing). Listed so a
later session can read them; their content is UNVERIFIED here.

**Blocked.** Every request to nvidia.com, developer.nvidia.com, resources.nvidia.com (Blackwell architecture
whitepaper/technical brief, H100 and B200 datasheets, developer blog posts) returned `CONNECT tunnel failed, response
403` from the agent proxy. Third-party pages (Cornell Virtual Workshop, vendor-reseller blogs, the reseller-hosted B200
datasheet) were also 403. WebFetch could not resolve hosts. The only vendor-side information obtained is (a) what the
arXiv papers quote from NVIDIA, (b) a web-search summary that cited third-party sites, and (c) the 2026 survey. So all
"VENDOR" numbers below are second-hand and must be re-checked against the NVIDIA documents when the proxy allows.

**Quality warning about the B200 paper (2512.02189).** It is the only B200 microbenchmark paper we could read and it
is internally inconsistent in several places (details in section 11). Treat its tensor-core and LLM tables as
indicative, and treat its structural statements (TMEM size and addressing, tcgen05 being single-thread, no FP64 on
tcgen05) as more reliable because they match the PTX documentation it cites.

## 1. The machine in one page

An NVIDIA data-centre GPU is a few hundred "streaming multiprocessors" (SMs). Each SM has four sub-cores, each with
its own register-file slice, integer/float lanes, a tensor core, and a warp scheduler. All SMs share a big L2 cache and
reach HBM stacks (DRAM dies stacked in the package) through memory controllers on the compute die. The programming
model forces large amounts of work to be organised as dense tiles so tensor cores can consume them. Performance comes
from (1) tensor cores doing matrix multiply-accumulate on small tiles, (2) a deep memory hierarchy that tries to keep
those tiles close, and (3) enough threads in flight to hide latency.

Generation list used in this note (all names from the papers): Volta V100 (2017), Ampere A100 (2020), Hopper H100/H800
(2022), Blackwell B200 (2024). Per generation the mechanism for feeding tensor cores changed: Volta/Ampere `mma`
(registers, warp-synchronous), Hopper `wgmma` (operands from shared memory, warp-group asynchronous, plus the Tensor
Memory Accelerator TMA and thread-block clusters with distributed shared memory), Blackwell `tcgen05.mma` (single
thread issues, accumulator in a new on-chip Tensor Memory, TMEM).

## 2. Memory hierarchy, level by level

### 2.1 Registers

- Volta: register file 64 KiB per processing block (Volta paper figure 3.1), so 256 KiB per SM across four blocks;
  two banks of 64-bit width (previous generations: four 32-bit banks). MEASURED (1804.06826).
- Hopper: figure in 2402.13499 shows 16384 x 32-bit per sub-core, i.e. 64 KiB per sub-core, 256 KiB per SM. Blackwell
  GB203 table in 2507.10789 also lists 256 KB register file per SM. MEASURED/quoted.
- Register access is not a latency to speak of (dependent issue 4 cycles for INT32/FP32 on Volta, Hopper and GB203;
  half precision 6, double 8 on Volta). MEASURED.
- Whole-chip register capacity, B200: 148 SMs x 256 KB = about 37 MB (DERIVED; SM count 148 from 2512.02189).

### 2.2 Shared memory and L1 (one pool per SM)

- Volta: L1 data cache plus shared memory combined, configurable 32 to 128 KiB (the L1 part), L1 hit latency 28
  cycles, line 32 B. Pascal was 82-84 cycles. MEASURED.
- Ampere A100: L1 hit 33 cycles, shared memory load 23, store 19 cycles (2208.11174); 37.9 cycles L1 and 29.0 shared
  in 2402.13499. MEASURED.
- Hopper: 256 KB combined L1/shared per SM, about 227 KB (228 unified in table) usable as shared memory
  (2507.10789 measured the dynamic shared-memory limit as about 227 KB on GH100, about 99 KB on GB203). L1 hit about
  40.7 cycles, shared 29 cycles on H800 (2402.13499). MEASURED.
- Bandwidth: 2402.13499 measured shared memory about 128 B per clock per SM on A100, RTX 4090 and H800 (127.9) and
  L1 about 124 B per clock per SM with 16-byte vector loads on H800. MEASURED. Per SM that is 128 B x 1.755 GHz
  (H800 max clock) = about 225 GB/s per SM; times 114 SMs = about 25.6 TB/s aggregate (DERIVED).
- Distributed shared memory (Hopper clusters): SM-to-SM latency 180 cycles, 32 percent below L2; peak aggregate
  3.27 TB/s with cluster size 2, falling to 2.65 TB/s at size 4 because blocks compete for the network. MEASURED
  (2402.13499, 2501.12084 gives 3.28 TB/s).
- Blackwell GB203 (consumer) has 128 KB per SM L1/shared, versus 256 KB for GH100 (2507.10789).

### 2.3 Tensor Memory (TMEM), Blackwell only

From 2512.02189 (B200), partly quoting the NVIDIA technical brief:
- 256 KB per SM, organised as a 2-D array of 128 lanes x 512 columns of 32-bit cells (128 x 512 x 4 B = 256 KiB,
  DERIVED check agrees). Addressed by lane and column, allocated and freed by software (`tcgen05.alloc`), loaded and
  stored with `tcgen05.ld/st/cp`; the old `ldmatrix`, `ld.shared`, `cp.async` cannot reach it.
- Role: holds the MMA accumulators (and optionally operand A) so accumulators stay on chip across a chain of
  multiplies instead of living in the register file. Hopper kept accumulators in registers and staged operands via
  shared memory.
- Whole chip: 148 x 256 KB = about 37.9 MB of TMEM (DERIVED).
- The paper states 16 TB/s read bandwidth and a "12 TB/s per SM of traffic avoided" - these are labelled by the
  authors as estimates under assumptions and are not a clean measurement; UNVERIFIED. The reported 61-82 percent
  "hit rate" for TMEM is also not defined clearly in the paper. UNVERIFIED.
- The paper's statement that TMEM is "10 percent of SM memory" is inconsistent with 256 KB TMEM next to 256 KB
  register file and 256 KB L1/shared; do not rely on it.

### 2.4 L2 cache

- Volta: 6144 KiB, hit about 193 cycles, line 64 B, physically indexed, unified with constants and instructions.
  MEASURED.
- Ampere A100: about 200 cycles (2208.11174); 40 MB.
- Hopper: 50 MB, partitioned in two halves joined by high-speed channels. Latency depends on which half holds the
  line: H800 264.5 to 502 cycles, A100 202.8 to 408 cycles, RTX 4090 about 284.8 (single level) (2501.12084, random
  stride test). 2507.10789 reports GH100 about 273 cycles at low footprint and about 508 when both partitions are
  involved (31 to 45 MB footprint). MEASURED. In time: 264 to 502 cycles at 1.755 GHz is about 150 to 286 ns
  (DERIVED).
- L2 bandwidth: 2402.13499 measured H800 about 3942 B per clock (vector loads) which at 1.755 GHz is about 6.9 TB/s
  (DERIVED); 4.23 times its global-memory throughput. A100 L2 was 2.01 times global throughput. MEASURED.
- Blackwell B200: dual die, four L2 partitions (double Hopper), 208 billion transistors, 148 SMs, eight GPCs
  (2512.02189 quoting the NVIDIA brief). The L2 capacity of B200 is not stated in the papers read: UNVERIFIED (not
  filled in from memory on purpose). GB203 consumer: 65 MB monolithic L2, hit about 358 cycles, slower than GH100.
  MEASURED (2507.10789).
- The paper 2512.02189 reports L2 hit rate rising from 68 to 84 percent as precision drops from FP16 to FP4 on
  Mistral-7B (Nsight counters). MEASURED, but see the quality warning.

### 2.5 HBM (global memory)

- Latency: Volta: 375 cycles for an L2 miss with TLB hit and 1029 cycles for an L2 miss plus TLB miss (MEASURED,
  1804.06826); Ampere about 290 cycles (cache bypass, 2208.11174) or 466 (2402.13499); H800 478.8 cycles; RTX 4090
  541.5 (GDDR6X). H800 478.8 cycles is about 273 ns at 1.755 GHz (DERIVED). L2 to global ratio about 1.9 (average of
  three devices). GB203 GDDR7: about 877 cycles; GH100 PCIe (HBM2e): about 659 cycles (2507.10789, differs from the
  other paper by method). All MEASURED.
- Bandwidth, per-device peak versus achieved:
  - V100: 900 GB/s peak HBM2 (VENDOR as quoted in the Volta paper); measured achieved/theoretical ratio 83.3 percent
    (MEASURED), i.e. about 750 GB/s (DERIVED).
  - A100 PCIe 40 GB: 1555 GB/s peak; H800 PCIe 80 GB HBM2e: 2039 GB/s peak, achieved 1861.5 GB/s = 91 percent
    (MEASURED, 2402.13499; the paper reports 90 to 92 percent of theoretical on all three).
  - H100 SXM5: 80 GB HBM3, 3.35 TB/s (VENDOR via the 2026 survey). H200: 141 GB HBM3e, 4.8 TB/s (VENDOR via survey).
  - B200: 192 GB HBM3e, 8 TB/s, eight stacks of 24 GB (VENDOR via paper and search summaries; NVIDIA datasheet not
    readable). STREAM Triad measured on B200: about 4.14 TB/s = 51.8 percent of 8 TB/s at 4 and 16 GB array sizes
    (MEASURED, 2512.02189; the authors admit they could not run large arrays, so this may understate the true
    sustained figure).
  - 2507.10789 reports "15.8 TB/s read bandwidth" for GH100 PCIe and 8.2 TB/s for GB203. These cannot be HBM2e or
    GDDR7 bandwidth (the HBM2e card has about 2 TB/s peak); they are almost certainly cache-resident traffic.
    UNVERIFIED reading; do not use as HBM bandwidth.
- TLB (Volta): L1 TLB with 2 MiB pages, 32 MiB coverage; L2 TLB covering about 8 GiB. A TLB miss costs a lot (the 1029
  versus 375 cycles above). The first touch of a large footprint is expensive. MEASURED.

### 2.6 What is on the compute die and what is in the package

- On the compute die: SMs (register files, L1/shared, TMEM on Blackwell, tensor cores, FP32/INT32/FP64 lanes,
  special-function units, TMA engine on Hopper and later), the L2 and its crossbar, memory controllers and PHYs, the
  NVLink PHYs, the decompression engine on Blackwell, the copy and video engines. The SM-to-SM network lives in the
  GPC. H100 die: 4N process, 814 mm2 (VENDOR via survey table).
- In the package: HBM stacks on a silicon interposer next to the compute die(s). B200 is two reticle-limited dies
  joined by NV-HBI (NVIDIA High-Bandwidth Interface), presented as one coherent GPU with a unified 192 GB space
  (2512.02189). A search summary quotes 10 TB/s for the die-to-die link: UNVERIFIED. The paper explicitly did not
  measure cross-die latency or bandwidth ("future work"), so the cost of crossing between dies is an open number.
- Off package: host CPU through PCIe or a coherent chip-to-chip link (Grace on GB200; the Grace-Blackwell unified
  memory paper 2610.20354 was not read), NVLink to other GPUs, InfiniBand/Ethernet NICs to other nodes.

### 2.7 Summary table (what a byte costs in time)

| Level | Size (per unit) | Latency | Bandwidth | Source |
|---|---|---|---|---|
| Register file | 256 KB per SM, about 37 MB per B200 | dependent issue 4 cycles | operand fetch each cycle | MEASURED / DERIVED |
| Shared/L1 | 256 KB per SM (Hopper), about 227 KB usable | 29 to 41 cycles | about 128 B/clk/SM | MEASURED |
| TMEM | 256 KB per SM (Blackwell) | not reported in cycles in a clean form | paper claims 16 TB/s | paper claim, UNVERIFIED |
| Distributed shared (cluster) | other SMs' shared memory | 180 cycles | 3.27 TB/s peak, cluster 2 | MEASURED |
| L2 | 50 MB Hopper (two partitions); B200 UNVERIFIED | 264 to 502 cycles (H800) | about 6.9 TB/s (H800, DERIVED) | MEASURED |
| HBM | 80 GB (H100), 141 GB (H200), 192 GB (B200) | 479 cycles (H800), about 273 ns | 2.04 TB/s (H800), 3.35 (H100), 4.8 (H200), 8 (B200) peak | MEASURED / VENDOR |
| Host / other GPU | system dependent | microseconds | see section 6 | see section 6 |

Latency ratios, H800: L1 about 41 cycles, L2 about 263 (6.5 times L1), HBM about 479 (1.9 times L2), so about 12 times
from L1 to HBM. Capacity ratio, B200 (DERIVED): register + shared/L1 + TMEM about 37 + 37 + 38 = about 112 MB of
per-SM SRAM, which is about 0.06 percent of the 192 GB of HBM, before counting L2.

## 3. How a transformer decode token moves data

Decode generates one token per step. For each token, every layer needs all of its weights and the KV cache of the
whole context.

- Weight traffic: with batch size 1, the whole model is read once per token. A 7-billion-parameter model in FP16 is
  about 14 GB, so one token reads about 14 GB from HBM (DERIVED). At the B200 peak of 8 TB/s that is at least
  1.75 ms per token, a ceiling of about 570 tokens per second for one stream (ESTIMATED upper bound, assumes
  perfect bandwidth use and ignores KV). At the measured STREAM figure of 4.14 TB/s it is about 3.4 ms (about 300
  tokens per second, ESTIMATED). In FP4 (NVFP4 is 4 bits plus an 8-bit scale per 16 values = 4.5 bits per weight,
  DERIVED from 2509.25149) the model is about 3.9 GB and the ceiling rises about 3.6 times.
- Arithmetic intensity: each weight is used for 2 FLOPs (a multiply and an add) per sequence in the batch. Intensity
  in FLOP per byte = 2 x batch / bytes per weight. FP16: 1 at batch 1; FP8: 2; NVFP4: about 3.6 (DERIVED). The 2026
  survey states the same: decode attention sits at an intensity of about 1 to 2 FLOP/byte (VENDOR-class secondary).
- Ridge point (where compute matches bandwidth): peak FLOPS divided by bandwidth. Using the B200 paper's measured FP8
  rate of 3850 TFLOPS: 3850 / 8 = about 480 FLOP/byte at peak bandwidth, or 3850 / 4.14 = about 930 at the measured
  bandwidth (DERIVED). With FP8 weights that means a batch of about 240 to 465 sequences just to reach the ridge
  (ESTIMATED), before the KV cache, which is read per sequence and does NOT amortise across the batch. Using
  recalled dense FP8 of about 4.5 PFLOPS gives about 560 FLOP/byte (UNVERIFIED vendor number).
- KV cache: size = 2 x layers x kv_heads x head_dim x tokens x bytes per element (survey equation). At long context
  it rivals the weights and is re-read every step, so "more than raw model size, sets the bandwidth ceiling on
  generation throughput" (survey, secondary). FlashAttention-2 reaches only about 35 percent utilisation on H100,
  against 80 to 90 percent for a tuned matrix multiply (survey citing prior work; secondary).
- Energy asymmetry: the survey quotes Horowitz (45 nm class, representative only) that an off-chip DRAM access costs
  100 to 1000 times the energy of an on-chip arithmetic operation or SRAM access, with a single 64-bit DRAM access of
  order 1300 to 2600 pJ (= about 20 to 40 pJ per bit). That is an old-process figure, not an HBM3e figure. No source we
  could read gives picojoules per bit for HBM3e: UNVERIFIED.
- What the Hopper paper saw: for LLM generation at small batch the decode is memory-bound, so FP8 gives no
  significant advantage in tokens per second (Llama-3B/7B/13B, batch 8, 128 tokens): e.g. 3B on H800 BF16 670.9 versus
  FP8 537.9 tokens/s in one table row set, OOM on some configurations (2402.13499 Table XII; row/column labels
  garbled in extraction so only the qualitative conclusion is used). MEASURED qualitative.

## 4. Tensor core precisions and throughput

### 4.1 Hopper (measured, H800 PCIe, 114 SMs, 350 W limit)

Dense `wgmma` m64n256, zero-initialised matrices (2402.13499 Table VIII), with peak given in the paper:
FP16 729 TFLOPS (peak 756.5), TF32 364 (peak 373-378), FP8 1448 (peak 1513), INT8 1448 TOPS (peak 1513). All about
95-96 percent of peak. MEASURED. Latency 128 cycles for all types at N=256, independent of data type; latency scales
with N (N=64: 32 cycles, N=8: 18-ish) and throughput collapses for N below 64 (N=8: 158 TFLOPS from 729) because the
shared-memory read cannot be hidden. MEASURED.

With random matrices the power limit bites: FP16 with FP32 accumulate drops to 665 TFLOPS, FP16/FP16 704.5, TF32
357, FP8 1417-1439. The H800 draws below 200 W with zero data and reaches the 350 W cap with random data
(2501.12084), and the core clock falls below the 1620 MHz in the whitepaper. MEASURED. This is a direct
demonstration that power is **data-dependent** (toggling activity), which matters for a counting design.

Sparse (2:4) `wgmma`: up to 2945 TFLOPS FP8 with zero data but only 2588-2780 with random data, and sparse `mma`
reaches only 1.42 times dense on H800 (2402.13499). MEASURED. Old-style `mma` instructions reach only 62.9 percent of
peak on Hopper (average), so legacy code leaves 37 percent unused. INT4 on Hopper is not a tensor-core instruction at
all: it compiles to a sequence of integer multiply-adds on CUDA cores. MEASURED.

### 4.2 Ampere (A100)

FP16/BF16 311-312 TFLOPS measured against 312 theoretical, TF32 132-156, FP64 tensor 19-19.5, INT8 594-624 TOPS,
INT4 1229-1248 TOPS (2208.11174; the paper labels these "GB/s" but they are TFLOPS/TOPS). MEASURED. Tensor
instruction latency about 16 cycles (FP16) and 8 (INT8), 4 (INT4).

### 4.3 Blackwell B200 (measured, 2512.02189) and Blackwell GB203 (2507.10789)

B200 dense tensor throughput claimed measured (Table VII): FP64 44.8 (non-tensor path, doubled FP64 units), FP32
482, TF32 964.5, BF16 1926, FP16 1930, FP8 3851, FP6 5134, FP4 7700, INT8 3928 TOPS; the paper says each is 96 to 99
percent of "theoretical peak" and gives H200 numbers for comparison (FP16 1515, FP8 3027). MEASURED but with a
consistency problem: 1515 TFLOPS for H200 FP16 is above the known dense H100/H200 peak of about 990 (survey:
"approximately 990 dense BF16 TFLOPS" for H100), so the table's H200 column and probably its notion of "dense" cannot
be trusted. Pattern kept as structural: FP8 = 2 x FP16, FP4 = 2 x FP8, FP6 between (1.33 x FP8). FP32 accumulation
halves FP16 throughput (964.8 to 482.4 at m64n8k16, MEASURED), "the accumulator datapath, not the multiply units,
limits throughput".

Latency of one `tcgen05.mma`: 11.0 to 11.4 cycles, independent of tile size (m64n64 to m256n256), versus Hopper
`wgmma` 32, 64, 128 cycles for N = 64, 128, 256 (Table V); across precisions 11.2 to 12.6 cycles (Table VI). MEASURED
(dependency chains through accumulators). The authors read this as a spatial array rather than a deep pipeline
(hypothesis).

Formats: FP4 = e2m1 (1 sign, 2 exponent, 1 mantissa); FP6 = e3m2 or e2m3; FP8 = e4m3 or e5m2. MXFP4: blocks of 32,
scale E8M0. NVFP4: blocks of 16, scale E4M3 plus an FP32 per-tensor scale (so 4.5 bits per value) (2509.25149 Table 1).
Hardware speedup versus BF16 (same table): MXFP8 2x, MXFP6 2x, MXFP4 4x, NVFP4 4x on GB200; on GB300 NVFP4 is 6x
(VENDOR via NVIDIA authors). NVIDIA authors trained a 12B hybrid Mamba-Transformer on 10 trillion tokens in NVFP4
with MMLU-pro 62.58 versus 62.62 for FP8 (MEASURED by NVIDIA), using: Random Hadamard transforms on weight-gradient
inputs, 2-D block scaling for weights, stochastic rounding for gradients, and about 16 percent of linear layers
(first 2 and last 8 blocks) kept in BF16. Lesson: FP4 is only made to work with extra machinery (outlier
spreading, scale handling, selective high-precision layers). B200 paper: FP4 weights give +7.7 to +9.1 percent
perplexity versus FP16, FP8 +1.9 to +2.4 percent (MEASURED, 2512.02189 Table VIII).

Consumer GB203 (RTX 5080) is a different part: only 2 FP64 units per SM, unified INT32/FP32 lanes, 128 KB L1/shared,
`tcgen05` not available on that chip (sm_120a). Do not read its numbers as B200 numbers. Its FP8 GEMM results in
that paper (0.233 TFLOPS at 8192^3, versus 0.887 on Hopper) are implausible as absolute rates (the matrix would take
about 4.7 ms on 1.1 TFLOP of work, giving about 0.23 PFLOPS-scale units mismatch) and look like a unit or
configuration error; UNVERIFIED, not used.

### 4.4 Cross-generation spec sheet numbers (VENDOR, via the 2026 survey)

A100: 80 GB HBM2e, about 2.0 TB/s, 312 dense BF16 TFLOPS, 400 W. H100 SXM5: 80 GB HBM3, 3.35 TB/s, about 990 dense BF16
TFLOPS. H200: same compute, 141 GB HBM3e, 4.8 TB/s. B200: 192 GB HBM3e, 8 TB/s, 5th-gen tensor cores with FP4/FP6,
NVLink 5 at 1.8 TB/s per GPU, TDP up to 1000 W (discrete) and configurable to 1200 W for liquid-cooled GB200. Survey
conclusion: A100 to B200 raised peak BF16 compute about 7 times but HBM bandwidth only about 4 times, so the machine
becomes more bandwidth-starved every generation. The search summary lists B200 FP4 dense at 9,000 TFLOPS (secondary,
differing sparse and dense figures between sites), 18-20 PFLOPS with sparsity.

## 5. Power and efficiency

- TDP (VENDOR via survey): A100 400 W; B200 up to 1000 W; GB200 up to 1200 W. H100 SXM5 700 W: UNVERIFIED (recalled).
- Instruction-level efficiency (MEASURED, 2402.13499 Table XI and 2501.12084 Table 10): `mma` energy efficiency in
  TFLOPS/W on A100 versus RTX 4090 versus H800: FP16/FP16 dense 1.79 / 1.89 / 2.62 (sparse 3.13 / 3.33 / 3.86); TF32
  dense 0.71 / 0.51 / 0.97; INT8 dense 3.41 / 3.53 / 5.92 (sparse 6.24 / 6.47 / 8.79). H800 power in those kernels
  165 to 255 W. Average H800 efficiency is 1.60 times A100 for dense instructions. `wgmma` is only 0.67 times (dense)
  as efficient as `mma` on the same chip because it runs into the power cap and a lower clock (2501.12084).
  In energy per operation, 5.92 TOPS/W is 0.17 pJ per integer op and 2.62 TFLOPS/W is 0.38 pJ per FP16 op
  (DERIVED, whole-board power, tensor core kernel on registers only).
- RTX 5080 (GB203) power in an mma loop: 46 W for FP8 (both formats), 39 W FP6, 16.75 W FP4, versus about 55 W for
  Hopper FP8 (2507.10789 Table VI; labelled "power usage/performance per watt" in the caption, so the exact quantity
  is ambiguous, UNVERIFIED). Directionally, narrower operands draw less power in the same loop.
- B200 training efficiency (MEASURED, 2512.02189): GPT-1.3B 14,363 tokens/s and 20.63 tokens/s/W, which implies
  about 700 W (DERIVED: 14363/20.63 = 696 W). ResNet-50 5.09 images/s/W. Efficiency 1.32 times H200 (paper's number
  for GPT-class training). With the standard 6 x parameters FLOP per training token that is about 7.8 GFLOP per token,
  so 20.63 tok/s/W corresponds to about 160 GFLOP/s/W, about 6.2 pJ per FLOP at the system level (ESTIMATED).
  Compare 0.17 to 0.38 pJ per op at the isolated tensor-core loop above (Hopper) and a crude 1 / (9 PFLOPS dense FP4 /
  1000 W) = 0.11 pJ per FP4 op (ESTIMATED from a secondary-source rate). The gap of one to two orders of magnitude
  between "tensor core at peak" and "a real model" is the cost of data movement, idle units and non-matmul work.
- LLM tokens: the B200 paper reports Mistral-7B at batch 32 with 56,028 tok/s in FP16 and 112,800 tok/s in FP4 and
  bandwidth utilisation 67.3 and 47.6 percent. Check: 14.5 GB of FP16 weights read per step at the claimed
  5.4 TB/s allows about 370 steps/s x batch 32 = about 12,000 tokens/s if purely decode; the claimed figure is about
  4.7 times higher, and the claimed 67.3 percent exceeds the same paper's measured 51.8 percent STREAM figure. So
  these tokens/s are probably prefill-inclusive or otherwise not decode-only, and cannot be used as decode
  numbers. UNVERIFIED.
- Survey (secondary) context: Groq LPU chip holds about 230 MB SRAM at about 80 TB/s on die; serving a 70B model
  takes about 576 chips and gives about 300 tokens/s per user at about 1 to 3 J per token. Cerebras: tens of GB of
  SRAM at petabyte-per-second. Treat as secondary until the primary papers are read.

## 6. Scale-up: how many GPUs act as one

- V100 NVLink v2 and NVSwitch (MEASURED/described, 1903.04611): each V100 has 6 NVLink ports at 25 GB/s per
  direction (50 GB/s bidirectional) per link = 300 GB/s per GPU. DGX-2: two baseboards of 8 GPUs and 6 NVSwitch chips
  each; each NVSwitch is an 18-port non-blocking crossbar; 8 ports to its local GPUs and 8 to the other baseboard;
  full 300 GB/s between any pair of GPUs on a baseboard through one switch hop and across the baseboards through two
  hops; raw bisection 25 GB/s x 8 links x 6 switches = 2.4 TB/s. 16 GPUs form one NVLink domain. GPU-to-GPU latency
  over NVLink/NVSwitch is on the order of 5 to 9 microseconds (the paper's microbenchmark, including software
  overhead), versus tens of nanoseconds for an on-die access. MEASURED.
- NVLink generations after V100: Blackwell NVLink 5 gives 1.8 TB/s per GPU (VENDOR via survey and search summaries;
  some pages call this bidirectional total), 18 links at 100 GB/s each (search summary), double the Hopper NVLink 4
  (900 GB/s, search summary). A GB200 NVL72 rack is a 72-GPU NVLink domain; NVLink domains up to 576 GPUs were
  mentioned in a search summary. All of these are second-hand: UNVERIFIED against NVIDIA documents.
  NVIDIA's claim (as repeated by the survey) of about 30 times more inference tokens for GB200 NVL72 versus an
  equivalent Hopper configuration is a vendor marketing number.
- Node-to-node network (InfiniBand/Ethernet at 400 to 800 Gb/s per port): not covered by any paper actually read in
  this session beyond the V100-era Summit result; UNVERIFIED.
- Implication: moving a byte to another GPU through NVLink is an order of magnitude lower bandwidth per GPU (1.8 TB/s)
  than HBM-local (8 TB/s) but still about 4 times above the old PCIe class, and three orders of magnitude more
  latency than SRAM. Tensor/pipeline parallelism turns into synchronous all-reduce traffic every layer.

## 7. Known bottlenecks and failure modes

1. **Decode is memory-bandwidth-bound.** Covered above. NVIDIA's own response over generations: H200 added only
   bandwidth/capacity (4.8 TB/s, 141 GB) with unchanged compute; Blackwell halves weight bytes with FP4 rather than
   making memory faster per FLOP. Achieved bandwidth is 83 to 91 percent in older parts (Volta 83.3, H800 91) but only
   about 52 percent on B200 in the one STREAM test available (possible measurement limit).
2. **Batching is the cure and is also the cost.** To approach compute-bound operation the serving system must batch
   hundreds of sequences (section 3), which increases latency per token, KV cache footprint (HBM capacity) and
   tail-latency complexity. Small-batch latency is poor: B200 Mixtral-8x7B FP8 batch 1 latency 12.3 ms versus 18.7 ms on
   H200 (1.52x), and 89.3 ms at batch 32 (MEASURED, 2512.02189 Table IX; "tok/s" columns in that table are derived
   from the latency column and are not trustworthy).
3. **Power cap and data-dependent power.** H800 PCIe tensor cores throttle from 729 to about 665 TFLOPS with random
   inputs; wgmma dense draws up to the 350 W limit; sparse wgmma lowers the clock further so sparse speedup is under
   2 times (MEASURED). B200 is a 1000 W part (VENDOR).
4. **Utilisation losses.** Legacy `mma` reaches 62.9 percent of Hopper peak. Small `wgmma` N (below 64) reaches
   22 percent of peak at N=8. FlashAttention-2 about 35 percent on H100 (survey). Transformer Engine FP8 linear layers
   are dominated by conversion overhead at small sizes: at N=4096 the GEMM kernel is about 29 percent of the time,
   rising to about 85 percent at N=16384 (2402.13499 Fig. 3, legend order assumed); FP8 only pays off above N of
   about 8192 and at 16384 it reaches about 2x FP16. te.TransformerLayer FP8 gain is below 2x because softmax, GeLU
   and attention stay in higher precision (MEASURED).
5. **Per-generation software churn.** `wgmma` (Hopper) does not exist on Blackwell, `tcgen05` replaces it; kernels
   "must be rewritten for Blackwell" (2512.02189); `tcgen05` is absent on the consumer chip; FP6 hardware exists "but
   lacks software tooling"; FP4 required per-layer precision selection (some layers tolerate FP4, others need FP8).
   Hopper INT4 tensor-core support was dropped (falls back to CUDA cores).
6. **Accumulator and format traps.** FP32 accumulation halves FP16 tensor throughput on B200; FP64 is a separate path
   (doubled FP64 units, 44.8 TFLOPS peak-ish in the paper) not on tcgen05.
7. **Two-die package.** B200 = two dies with a die-to-die interface whose cost under load was not measured; four L2
   partitions mean latency depends on which partition holds the line (Hopper already showed a 264 to 502 cycle spread).
   The consumer monolithic-L2 variant has higher latency (358) but better throughput under full load.
8. **Latency hiding needs huge parallelism.** Hopper's L2 miss to HBM is hundreds of cycles; keeping tensor cores
   fed relies on thousands of resident threads, asynchronous copies (TMA, cp.async) and double buffering. The
   asynchronous pipeline helped small blocks (+39.5 percent at 8x8 blocks on H800) but gave -1.8 percent at 32x32 blocks
   (2402.13499 Table XIII), i.e. the machinery is only useful if software is tuned.
9. **TLB and page effects**: first-touch TLB miss triples latency on Volta (1029 vs 375 cycles).
10. **Decompression engine limits**: B200 DE is bound by decompressed output rate of about 160 to 220 GB/s for LZ4
    (Bitcomp 462 GB/s, 0.227 ms per 100 MB); compared with 8 TB/s HBM that is about 2 to 3 percent, so compressed
    weights cannot be decompressed on the fly at decode speed (DERIVED from MEASURED). It helps loading, not decode.
11. **Cost**: no price, yield or cost-per-token number was obtained from the papers read; the 208-billion-transistor
    two-die package and eight HBM3e stacks are the visible cost drivers. UNVERIFIED (no sourced cost figures).

## 8. Weak points a different design could exploit (hypotheses, not facts)

Each item is a hypothesis for L design discussion, grounded in a measured or sourced observation above.

H1. **Weights stream from DRAM every token.** For batch-1 decode the GPU reads the whole model per token (section 3)
   and pays 480 to 2100 pJ-class DRAM energy per 64 bits in old-process terms. If weights live in memory inside the
   tile where they are used (the L premise), the per-token DRAM read disappears for models that fit. Capacity is the
   price: on-chip SRAM per B200 is only about 0.06 percent of its HBM (DERIVED). Hypothesis: L must win by
   compressed/sparse/counted representations that fit more model per mm2, not by faster memory.
H2. **The GPU needs a batch of hundreds to be efficient.** Ridge about 240 to 465 sequences for FP8 weights. A
   design whose cost per token is roughly flat in batch (event-driven, no dense tile requirement) would be better at
   batch 1 to 8, which is where interactive use lives. Hypothesis: sparse, event-driven row lookups lose nothing at
   batch 1.
H3. **Compute that is mostly idle.** Tensor cores sit idle during decode; the chip pays power and die area for
   thousands of multipliers it cannot feed (A100 to B200: compute 7x, bandwidth 4x). L has no multipliers, so no
   area spent on units that stall.
H4. **Data-dependent power is large.** 200 W (zeros) versus 350 W (random) on the same tensor instruction, and 16.75 W
   (FP4) versus 46 W (FP8) per mma loop on GB203. Power follows bit activity. Hypothesis: a counting design whose
   activity is sparse and event-driven should see similar proportional savings, plus the chip can sleep idle tiles.
H5. **Distance costs.** 41 cycles (L1) to 479 cycles (HBM), and 264 to 502 cycles inside L2 depending on partition.
   Hierarchies add tag lookups and coherence traffic. A tile-local memory with explicit, short, fixed-length paths
   avoids partition-dependent latency spread.
H6. **Precision zoo and software churn.** FP64/FP32/TF32/BF16/FP16/FP8/FP6/FP4/INT8 plus MX and NV block formats,
   each with scaling rules, accumulator width traps and per-layer exceptions (about 16 percent of layers kept in
   BF16 for NVFP4 training). Counting needs small integers; one fixed format removes the whole class of problems.
H7. **Programming model complexity.** Three instruction generations in four years, each needing kernel rewrites;
   TMA/TMEM allocation by hand. A fixed dataflow with a compiler-checked schedule (the Groq direction) trades
   flexibility for determinism; for a single model family (L) that trade may be right.
H8. **Scale-up cost.** Model larger than one chip forces NVLink (1.8 TB/s vs 8 TB/s HBM) with microsecond-class
   latency and synchronous collectives. A design with enough per-chip capacity, or an architecture whose parts are
   independent counters rather than synchronised matrices, communicates much less per token.
H9. **Package complexity.** Two reticle-limited dies, eight HBM3e stacks, a silicon interposer, kilowatt cooling.
   Memory-in-tile designs avoid the interposer and HBM supply dependence but must prove density (see H1).
H10. **Decode attention is a lookup problem.** The KV cache is read in full per token with very low reuse (intensity
   about 1 to 2). Retrieval-style or hashed/sparse attention that touches only a few rows per token would cut the
   dominant traffic at long context. Hypothesis; needs an accuracy study.

## 9. What to learn without copying

- Measure the way these papers do: pointer-chase for latency at every level, saturating streams for bandwidth, and
  dependency-chain versus independent-instruction tests for pipeline latency versus throughput. Apply the same
  methodology to the L RTL/FPGA numbers so L can be compared level by level (cycles, ns, bytes per cycle per tile).
- Report achieved/peak ratios, not just peaks (Volta 83 percent, H800 91, B200 STREAM 52, Hopper `mma` 63, small-N
  `wgmma` 22). Utilisation is the real figure of merit.
- Use roofline thinking (FLOP per byte versus ridge) but replace FLOP with "counts" for L: define the L equivalent
  of arithmetic intensity (counter updates per byte of state touched) and compute where L sits.
- Keep intermediates on-chip: the entire point of TMEM, DSM and shared-memory fusion is to avoid round trips to L2/HBM.
  L starts there; keep the discipline that no state leaves the tile.
- Make accumulators explicit and cheap: B200 added a separate 256 KB accumulator memory because registers were the
  limiter (FP32 accumulation halving throughput). L's counters are accumulators by nature; give them a dedicated,
  narrow store.
- Treat power as data-dependent: report power at realistic activity, not on zero data (the H800 shows the gap).
- Block-scaled low precision (NVFP4: 16 values per scale) is a reminder that groups of 16 sharing one scale is a
  good granularity; the same grouping idea may inform how L shares per-row normalisers.
- Hardware support for compression (the DE) failed to match HBM speed: avoid designs that need decompression
  throughput well below memory bandwidth in the critical path.
- Latency hiding by asynchrony and double buffering is a software burden; a design where lookups are local and
  fixed-latency needs far less of it.
- Do not copy: warp-synchronous SIMT execution, large dense tiles, the multiplier array, the register file/shared
  memory/L1/L2 cache stack, HBM-on-interposer, or the batching-dependent economics. These conflict with the L rules
  (no matrices, no multiplies, memory inside each tile).

## 10. Open items to check when the NVIDIA documents become reachable

1. B200 L2 capacity, SM shared memory size, TMEM bandwidth, NV-HBI bandwidth and latency (UNVERIFIED here).
2. Official B200 per-precision dense and sparse TFLOPS (so the 2512.02189 Table VII column can be corrected).
3. NVLink 5 per-link figures, NVL72 and NVL576 domain definition, NVSwitch generation specs.
4. HBM3e energy per bit and DRAM share of board power (no read source).
5. Read the unread Blackwell papers listed in section 0 (Grace-Blackwell unified memory, analytical models,
   warp divergence).
6. Cost per GPU and per token with sources.

## 11. Internal inconsistencies found in the B200 paper (2512.02189), so the reader knows what not to trust

- Table VI (m64n8k16 single instruction) lists FP8 at 1925 TFLOPS while Table VII lists FP8 at 3850; different tile
  shapes but not reconciled in the text. The ratio of Table VII to a stated "theoretical peak" is 96 percent but the
  peak is never listed.
- H200 FP16 1515 TFLOPS exceeds the known H100/H200 dense peak (about 990 dense, survey).
- Table VIII FP8 speedup for Mistral-7B is 1.16 times while the text says "1.57-1.59 times for both FP16 and FP8".
  The FP16 speedup is 1.97 times in the table.
- Claimed bandwidth utilisation 67.3 percent (FP16) conflicts with the measured 51.8 percent STREAM Triad.
- Transistor count comparison "208B vs 180B" for B200 versus H200 is not the commonly cited Hopper figure
  (UNVERIFIED either way).
- "TMEM is 10 percent of SM memory" does not match 256 KB TMEM beside 256 KB registers and 256 KB L1/shared.
- Throughput of the FP8 H200 benchmark in Table VIII (49,200 tokens/s) is stated for Mistral-7B but a batch-32
  decode at 2048 context cannot reach that on a 4.8 TB/s part reading 7 GB of FP8 weights per step (7 GB / 4.8
  TB/s = 1.46 ms, so at most about 680 steps/s x 32 = about 22,000 tokens/s, DERIVED).

Related: [Paper notes index](INDEX.md), [Memory at scale synthesis](../memory_at_scale_synthesis.md)
