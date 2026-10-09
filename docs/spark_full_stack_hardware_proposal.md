# SPARK full-stack hardware proposal: a fix for every GPU energy, heat and water problem

## 0. Honest framing (use this in the pitch)
- Data centres used ~1.5% of world electricity in 2024 (415 TWh) and the IEA projects ~3% (~945 TWh) by 2030; they are <10% of global demand growth to 2030 ([IEA](https://www.iea.org/reports/energy-and-ai/executive-summary), [Sustainability Online](https://sustainabilityonline.net/news/data-centres-to-account-for-3-of-global-electricity-consumption-by-2030/)).
- The real danger is **local and fast-growing**: grids and water in specific places, like India's capacity rising ~2.2 GW → 12 GW by 2030, many sites in water-stressed regions.
- **Efficiency alone is not enough** — the rebound (Jevons) effect: cheaper AI drives more AI use ([Luccioni, Strubell, Crawford 2025](https://arxiv.org/abs/2501.16548v1)). So SPARK's principle is not only "do work cheaper" but **"don't do unnecessary work"** (effort proportional to need) plus a hard energy cap per token.
- Do NOT claim "AI will destroy the world" or "we solve everything". Claim: a measurable, scalable reduction at the source, which stacks with cooling and grid fixes.

## 1. Every GPU problem → SPARK hardware fix (three tiers)
Tiers: **B** = build on the FPGA prototype · **C** = chip proposal (realistic custom silicon) · **R** = long-term research direction.

| # | GPU problem | Root cause | SPARK hardware fix | Tier | Evidence |
|---|---|---|---|---|---|
| 1 | Computes every value, even zeros | Dense SIMT / lockstep design | Event-driven engine: queue of active neurons only; block-structured spikes for low overhead | B | Event-driven SNN FPGA ~15× ([Sommer](https://arxiv.org/pdf/2203.12437)); S2TA |
| 2 | Same effort for every token | No hardware notion of difficulty | Metacognitive controller: instinct / flag / deliberate paths, early exit, recall-bypass, power-gates unused units | B | Overthinking, routing studies |
| 3 | Data movement up to 84% of energy | Memory off the compute die | Weight/state-stationary tiles; hot/cold neuron split; predictive prefetch; address-sorted queues | B | [A100 study](https://esploro.umontpellier.fr/esploro/outputs/conferenceProceeding/Analyzing-GPU-Energy-Consumption-in-Data/9941278009311) |
| 4 | Memory wall at batch 1 (~1% of peak) | One fetch per multiply | No dense weight streaming: only active rows fetched; multi-stream interleaving hides waits | B | Roofline analyses |
| 5 | KV cache and quadratic attention | Transformer maths | Constant-size state (L), no KV cache; on-chip recurrent and fast-weight state | B | [QuantSpec](https://arxiv.org/pdf/2502.10424) |
| 6 | Too many bits | Fixed FP formats | 4-bit spikes; block-scaled 4-bit weights with shift scales; precision on demand | B | MX formats |
| 7 | Clock power (~10–50% of dynamic power) | Global clock tree | Fine-grained clock gating now; clockless (asynchronous) tiles later | B / C | Clock-tree studies; TrueNorth |
| 8 | Idle and leakage power; low utilisation | Not energy-proportional | Power-gating of idle tiles; per-tile voltage scaling; **near-threshold voltage mode** for the instinct path (measured 5–9× efficiency at much lower speed) | C | [NTC results](https://www.realworldtech.com/near-threshold-voltage/4) |
| 9 | Extreme power density (0.9 W/mm²) | Dense compute at high clock | Spread, low-activity tiles; **hard energy cap per token** bounds worst-case power and heat | B / C | — |
| 10 | Cooling needs water | Evaporative towers | Chip and package designed for **warm-water closed-loop liquid cooling** (no evaporation) and **heat reuse** | C | Microsoft zero-water design: >125 M L/year avoided per site (projected) ([ITPro](https://itpro.com/infrastructure/data-centres/data-center-water-consumption-is-skyrocketing-but-microsoft-thinks-it-has-a-solution-the-companys-new-closed-loop-cooling-system-consumes-zero-water-and-could-save-millions-of-liters-per-year)); two-phase immersion PUE ~1.03 ([DOE/ORNL](https://www.energy.gov/sites/default/files/2023-07/bto-peer-2023-32238m-ultr-ornl-jajja.pdf)) |
| 11 | Synchronous scale, frequent failures | Huge lockstep jobs | Independent tiles; parity and health counters; map out failed tiles | B / C | Meta Llama 3 |
| 12 | Short replacement cycles, e-waste | Monolithic big chips | Add-on chiplet beside existing GPUs (UCIe); reconfigurable tiles extend life | C | UCIe |
| 13 | Software lock-in | CUDA ecosystem | Automatic PyTorch → integer → chip toolchain; open design | B | — |
| 14 | Off-chip memory energy | Long wires to HBM | 3D-stacked SRAM on the tile (<1/3 energy per bit vs microbump links) | C | [AMD V-Cache](https://fuse.wikichip.org/?p=5531) |
| 15 | Electronic data movement heat | Copper wires | Photonic links/compute (first photonic chips ran real AI models in 2025) | R | [Nature 640, 368 (2025)](https://physics.aps.org/articles/v18/84) |
| 16 | Matrix–vector energy | Digital MACs | Analog in-memory tiles for 4-bit spike layers (9.76 TOPS/W peak, 3–4-bit precision) | R | [IBM HERMES](https://www.arxiv.org/pdf/2212.02872) |
| 17 | Energy lost on every switch | Irreversible logic | Reversible/adiabatic circuits (2025 proof of concept: ~30% less energy, ~50% recovered) | R | [IEEE Spectrum](https://spectrum.ieee.org/reversible-computing) |

## 2. SPARK at three scales
1. **SPARK core (FPGA, now):** event-driven engine, membrane unit with lazy decay, change-only spikes, hippocampus recall, confidence gate + early exit, energy cap, clock gating, counters; stretch: learning unit, skill memory, prefetch, hot/cold split.
2. **SPARK chiplet (custom silicon proposal):** many tiles on an on-chip spike network, stacked SRAM, per-tile voltage/power gating with a near-threshold "instinct" mode, warm-water cooling-ready package, UCIe link to sit beside a GPU.
3. **SPARK research directions:** clockless tiles, analog in-memory spike layers, photonic links, adiabatic logic.

## 3. The physics chain SPARK attacks at each link
- **Work:** do only needed work (event-driven, think-less, metacognition) → fewer operations.
- **Joules per operation:** low bits, short wires, memory beside compute, low voltage → fewer joules each.
- **Idle joules:** gating, energy proportionality → near-zero when nothing happens.
- **Heat:** capped power per token, low density → easier cooling.
- **Water:** warm-water closed loop, heat reuse → near-zero evaporation.

## 4. What remains outside our control
Grid carbon intensity, how much AI society chooses to use (rebound), training of giant models, and chip manufacturing footprint. We state these limits openly.
