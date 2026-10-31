---
title: Rows I and J - cost per token, yield, power and heat of an SRAM wafer against a GPU cluster and a Cerebras-class wafer (31 Oct 2026, MODEL)
tags: [spark, new-start, cost, power, heat, yield, wafer, model]
---

# Rows I and J: cost, yield, power and heat (31 Oct 2026)

**MODELLED, not measured.** Rust model [`step3_cost_power_model.rs`](experiments/step3_cost_power_model.rs), [log](experiments/step3_cost_power_model.log), [first run without the latency floor](experiments/step3_run1_no_latency_floor.log), [latency sensitivity](experiments/step3_latency_sensitivity.log). The bars were written at the top of the source before the first run. It extends [step 2](step2_wafer_sram_result.md) with cost, yield and heat. Case: the 1T-parameter mixture-of-experts model (32B active), 4-bit, 64 sequences, context 4,096; the dense 70B and the 671B model are in the log.

## Inputs, with what is sourced and what is assumed

| input | value | label |
|---|---|---|
| N5 300 mm wafer | about $17,000 (2020 model) to $18,500 (2026 table, range $16,000-21,300); 70,686 mm2 | third-party estimates: [Tom's Hardware](https://www.tomshardware.com/news/tsmcs-wafer-prices-revealed-300mm-wafer-at-5nm-is-nearly-dollar17000), [CSET](https://cset.georgetown.edu/article/analysts-believe-that-a-single-tsmc-5nm-wafer-costs-17000/), [Silicon Analysts](https://siliconanalysts.com/data/wafer-pricing) |
| HBM3E price | $12-17 per GB | analyst and trade-press estimates (HBM has no spot market; one dataset says its figures are modelled): [Silicon Analysts](https://siliconanalysts.com/market-data/hbm-pricing), [Stanford](https://dam.stanford.edu/memory-prices.html) |
| Cerebras CS-3 system | $2-3 million; 23 kW (23 or 27 kW in sources) | third-party estimate, vendor claim; Cerebras publishes no price: [Next Platform](https://www.nextplatform.com/2024/03/14/cerebras-goes-hyperscale-with-third-gen-waferscale-supercomputers/) |
| GPU price, power while decoding | $25,000 x 1.5 for host and network; 350 W per board | **ASSUMED** (no source found; the earlier sensitivity ran 100-700 W) |
| electricity, life, utilisation, cooling overhead | $0.10/kWh, 4 years, 50%; 1.4 (air hall) and 1.15 (liquid) | **ASSUMED** |
| defect density, spare area | 0.1 per cm2, 1% | **ASSUMED** (cited-derived tile size 0.05 mm2) |
| system hardware of our wafer (power delivery, cold plate, packaging, test) | $150,000 | **ASSUMED, no source**; it is the largest single number in the bottom-up price |
| per-step latency floor of a wafer machine | 0.5 ms (layer-to-layer synchronisation) | **ASSUMED**; added after run 1 (below) |

## Findings

1. **Silicon is not the cost problem.** One wafer of N5 silicon is about $18,500, and the cited system is priced at $2-3 million: the silicon is under 1% of the price. At the whole-wafer price, SRAM costs about **$89 per GB** of raw silicon (the project model says $174-223 per GB) against **$12-17 per GB** for HBM3E. SRAM is 5 to 15 times the price of HBM per GB, so more memory on chip costs real money, but the wafer is not what makes the system expensive. What would is power delivery, cooling, packaging, test, volume and development, none of which I can source.
2. **Yield is not the blocker in this model.** At an assumed 0.1 defects per cm2 a wafer has about 46 defects, each killing one 0.05 mm2 tile, which is 0.005% of the tiles against 1% spare. Point defects are covered by a wide margin. Clustered defects, the periphery and the fabric are not modelled, and I found no source on Cerebras's actual yield or spare figures.
3. **Cost per token (bars I1 to I3).** At the cited price ($2.5M per wafer) **I1 fails**: $1.55 per million tokens against $1.34 for the GPU cluster. With a bottom-up price (silicon plus $150,000 assumed hardware) **I2 passes**: $0.11 per million tokens, 12 times cheaper than the GPU cluster. **I3, the break-even: about $2.1 million per wafer system** at a 0.5 ms step. The result swings with two inputs that I assumed:
   - **the latency floor:** the break-even falls to $0.54M at 2 ms, $0.11M at 10 ms and $0.03M at 35 ms (the GPU's own step time). The wafer's advantage is throughput (64,000 against 1,839 tokens per second for the same 64 sequences), and it disappears if the layers cannot synchronise faster than a few milliseconds;
   - **the system price,** which decides whether a wafer machine can be built for far less than the cited one. Nobody has shown that.
4. **The cited wafer comes out worse than ours here ($4.10 per million tokens)** because I charge it the quoted 23 kW throughout each step, an upper figure; read that column as pessimistic for it.
5. **Heat and power (J1, J2).** Average heat density while serving is **0.096 W/mm2** (J1 passes against 1.0), against about 0.62 for the GPU boards at the assumed 350 W. Facility energy per token (cooling overhead included) is **7.8x below the GPU cluster** at the pessimistic SRAM energy (**J2 passes**), because the wafer machine finishes each step far faster, so static power and board power are spent over less time. It falls to 6.9x at a 2 ms floor, 4.4x at 10 ms (fail) and 2.1x at 35 ms. Two cautions: the average hides hot spots, and a 46,225 mm2 part still needs a liquid cold plate and large current delivery whatever its average density, which is a cost and a mechanical design problem this model does not cover. **Water use is not modelled and no water figure is claimed;** the model only says that less energy per token means less heat to remove.

## A correction made during this run

Run 1 (no latency floor) gave a 70-fold cost advantage and passed every bar, at over 10,000 tokens per second per sequence. That is the bandwidth bound, which no 61-layer model reaches because every layer must wait for the previous one across the wafer. I added the 0.5 ms floor, which hurts our machine and not the GPU, reran, and kept run 1's log. The bars were not changed. Run 1 should not be quoted.

## What this decides, and the next step

- **Rows I and J are "partly covered", not covered.** On the assumptions above, the wafer machine can win on cost per token and on facility energy only if (a) its step latency stays near a millisecond and (b) the system price lands far below the cited $2-3M. Neither is shown. The first needs a latency model of layer-to-layer communication on a wafer (one to two synchronisations per layer, link energy and distance); the second needs sourced costs for power delivery and cooling.
- **Proposed next step:** the layer latency model, since it decides the answer, and a measured GPU decode power on the RTX 3050 (idle first) to replace the 350 W assumption.

Related: [Workload map](../docs/gpu_workload_map.md), [Step 2 result](step2_wafer_sram_result.md), [SRAM area and cost model](../hw/results/sram_area_cost_model.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
