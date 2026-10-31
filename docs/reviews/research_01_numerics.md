---
title: Research 01 - numeric formats and quantisation (31 Oct 2026)
tags: [spark, review, research, quantisation, competitors]
---

# Research 01: numeric formats and quantisation

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026. **The evidence here is the weakest of the set:** mostly blogs, and no peer-reviewed multi-model test was read.

## What and why

- **Nvidia:** Blackwell has FP4 and FP8 paths, and its FP4 units are reported to give about 2x the FP8 throughput on the same chip. VENDOR-derived, [S] [guide](https://www.gmicloud.ai/en/blog/fp8-fp4-quantization-inference). It needs FP4 because bandwidth and memory are the limit.
- **Google:** Ironwood quotes 2,307 TFLOPS BF16 and 4,614 FP8. VENDOR, [S] [guide](https://www.clarigital.com/hardware/ai-chips/google-tpu/ironwood/).
- **LP30:** no FP4; LP35 adds it in 2027. VENDOR roadmap, [P] [ServeTheHome](https://www.servethehome.com/decoding-the-future-of-inference-at-nvidia-groq-lpus-join-vera-rubin-platform-for-low-latency-inference/2/).
- **Tenstorrent:** Block FP8. VENDOR, [P] [Register](https://www.theregister.com/on-prem/2025/11/27/blackhole-quietbox-tenstorrents-ai-workstation-reviewed/2113269).

## Does it really hold?

| format | quality against BF16 | label |
|---|---|---|
| FP8 | at most 0.7 points on a multiple-choice benchmark, across 16 test arms | THIRD-PARTY, one write-up, [S] [beri.net](https://www.beri.net/article/fp8-vs-nvfp4-vs-int4-awq-gguf-quantization-format-accuracy-throughput-2026) |
| INT4 (AWQ) on a 27B model | −1.5 points | same |
| FP4 on the same model | −2.4 points | same |
| FP4, general | "1 to 3 percent" | Vendor-style guide, [S] [Spheron](https://www.spheron.network/blog/fp4-quantization-blackwell-gpu-cost/) |

InferenceX checks accuracy on a math benchmark that its own authors call saturated, so it would not catch much ([P] [InferenceX v2](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs)). An older SemiAnalysis study reported that 25% of tested models failed accuracy checks on AMD ([S] [Part 1 follow-up](https://newsletter.semianalysis.com/p/amd-vs-nvidia-inference-benchmark-who-wins-performance-cost-per-million-tokens)). I did not check whether that is still true.

## Consequences for this project

1. **4-bit is not an advantage.** GPUs already run FP4 with dedicated hardware. Any 4-bit comparison must also give the GPU FP4's speed gain, which the project's GPU model, memory-bound as it is, does not include.
2. **4-bit is not known to be safe.** The 1.5 to 2.4 point drops above fit my finding V-11 ([review](vision_review_01.md)). M4-f, the 0.01-nat bar, is a sensible test, but a single loss number should be joined by task accuracy on a real benchmark.
3. **The project's design is integer; the market's 4-bit is mostly floating.** INT4 and FP4 were close in the one write-up, so integer may be fine. Whether INT4 with the project's per-row dynamic scale matches AWQ or similar calibrated methods is UNKNOWN and is testable cheaply on the founder's RTX 3050.

## The flaw, and what stops copying

A shared flaw: the quality loss at low precision is reported poorly, per model and with weak benchmarks. **Cheapest fix:** a published, repeatable table of quality loss by format, per model size, with paired intervals. This is research, not a moat: anyone can copy it. It could serve wedge 1 in the [summary](research_01_summary.md).

## What they cannot do

Nothing found says a rival cannot run 4 or 8 bits. The real limit is that a format ties checkpoints to hardware: one write-up argues that an FP4 checkpoint commits a buyer to Blackwell. THIRD-PARTY, single source; UNKNOWN how buyers treat this.

Related: [Research summary](research_01_summary.md), [Vision review 01](vision_review_01.md), [M4 plan](../../hw/gpu/M4_plan.md), [Reviews index](README.md)
