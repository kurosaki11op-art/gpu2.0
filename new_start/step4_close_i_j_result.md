---
title: Closing rows I and J - a calibrated latency model and the thresholds that decide cost, power and heat (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, power, latency, wafer, model, closure]
---

# Closing rows I and J (31 Oct 2026)

**MODELLED, not measured.** Rust model [`step4_wafer_latency_model.rs`](experiments/step4_wafer_latency_model.rs), [log](experiments/step4_wafer_latency_model.log), [uncalibrated first run](experiments/step4_run1_uncalibrated.log). Bars were written at the top of the source before the first run. It replaces the two largest assumptions of [step 3](step3_cost_power_result.md) (the 0.5 ms step latency, the $150k hardware cost) by a latency model and by thresholds. Case: the 1T mixture-of-experts model (32B active), 4-bit, 64 sequences, context 4,096.

## The latency model, and how far to trust it

Each layer's weights stay in their own region of the wafer; a token passes through the layers one after another, and tokens of different sequences fill the pipeline. Per layer: six dependent fabric phases (broadcast or reduction across the region, 1 ns per hop, 0.05 mm2 tiles), compute at the region's share of peak, weight and cache reads at the region's share of SRAM bandwidth; 1 microsecond per wafer-to-wafer crossing. Every constant is ASSUMED.

**Calibration (not an independent test).** The uncalibrated model was 1.7 to 1.8 times faster than the vendor-reported per-user speeds for the cited wafer at 16-bit weights, batch 1: it gave 3,772 tokens per second for a 70B model (vendor claim about 2,100, launch-era late 2024) and 1,635 for 405B (vendor claim 969). Sources: [Cerebras 405B](https://www.cerebras.ai/blog/llama-405b-inference), [TechRadar](https://www.techradar.com/pro/nvidias-closest-rival-once-again-obliterates-cloud-giants-in-ai-performance). I applied one correction factor of 1.8 to all latencies; the model then gives 2,095 and 908 tokens per second against 2,100 and 969. That fit uses the same two points it is checked against, so it shows the model is the right order of size, not that it is right; and it assumes our wafer behaves like theirs.

## Results against the pre-set bars

| bar | result |
|---|---|
| **L1:** token latency at most 2 ms | **Pass.** 0.274 ms (3,655 tokens per second per sequence, 223,000 per system); the GPU cluster takes 17.4 ms per token (57 per sequence) |
| **I2':** bottom-up price at most 0.5x GPU cost per million tokens | **Pass.** $0.065 against $1.336 for the GPU cluster, and the same wafer at the **cited** $2.5M price costs $0.89 (the cited wafer in the same model, charged its quoted 23 kW throughout, $2.73) |
| **I2' threshold:** the highest hardware cost per wafer that still passes | **about $1.8 million** at the central GPU assumption (350 W, $25k per GPU), $1.1M at the cheapest GPU assumption in the 220 to 700 W range ($15k, 220 W); the break-even system price is about $3.7M (central). The unsourced $150k used in the bottom-up price is far under that threshold |
| **J2':** facility energy at least 5x below the GPU cluster for GPU decode power 220 to 700 W | **Pass.** 5.9x at 220 W, 7.9x at 350 W, 13.3x at 700 W (cooling overheads 1.4 for the GPU hall, 1.15 for liquid cooling, both assumed). **At a 100 W GPU it is 4.0x, a fail**; 100 W is only a floor, but the real GPU decode power is still unmeasured |
| **J1':** heat density at most 1.0 W/mm2 | **Pass.** 0.164 W/mm2 while serving (average; hot spots not modelled), against 0.62 for the assumed GPU boards. About 38 kW across five wafers, 7.6 kW per wafer, against the cited system's 23 kW |

## What is closed and what is not

- **Closed on the model:** rows I and J pass every pre-set bar at the central assumptions, with margin on cost per token (about 10x between the bottom-up price and the bar) and on facility energy (7.9x against 5x).
- **Not closed, and why it matters.** Three items stand between this model and a claim, each one a number to obtain, not a test to invent:
  1. **GPU decode power.** J2' fails below about 200 W per GPU. It must be measured (idle and under decode load on the RTX 3050 gives the ratio; an H100-class power figure would still need a source).
  2. **System hardware cost per wafer.** The threshold is about $1.8M; the assumed $150k is unsourced. Supplier quotes for power delivery (a wafer at the modelled 7.6 kW needs about 7,600 A at 1 V), a cold plate and packaging are the evidence needed. I could not source any.
  3. **Whether an SRAM-heavy wafer with 80% of its area as memory can be built and routed** at all, with the remaining 20% carrying compute and the fabric. The model assumes it can; the cited vendor's own memory share is not known.
- **What this does not claim:** that the chip beats a GPU. It says that under the stated assumptions a pipelined SRAM wafer would serve very large existing models at lower cost per token and lower facility energy than a GPU cluster, and it names the three numbers that would break the claim. Water is not modelled and no water figure is claimed. Accuracy is inherited from the model being served (row A) and is not tested here.

## Next

Rows I and J are closed on the model. The next row is K (training), unless you want the layer-latency or power-delivery items checked first. The GPU decode-power measurement waits for an idle GPU.

Related: [Workload map](../docs/gpu_workload_map.md), [Step 3 result](step3_cost_power_result.md), [Step 2 result](step2_wafer_sram_result.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
