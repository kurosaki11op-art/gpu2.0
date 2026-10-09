# SPARK architecture: learning from the weaknesses of existing AI chips

Framing for judges: **"SPARK combines the strengths of existing brain-inspired and AI chips and is designed around their documented weaknesses."** Avoid "we fixed Intel/IBM" — we fix specific, published weak points, at prototype scale.

## 1. Weakness → SPARK design answer

| # | Documented weakness (who) | Evidence | SPARK design answer | Prototype? |
|---|---|---|---|---|
| W1 | Computes everything, can't skip zeros except fixed 2:4 (GPU); lockstep array idles on sparse work (TPU) | NVIDIA 2:4 docs; FlexTPU (U. Michigan) | **Event-driven engine**: work is a queue of active neurons only; no lockstep, so no idle units waiting on zeros | ✔ |
| W2 | Data movement up to 84% of dynamic energy (GPU) | A100 energy study | **Weight- and state-stationary tiles**: weights, neuron state, fast-weight state live in on-chip SRAM beside the compute | ✔ (small model) |
| W3 | Benefit vanishes on standard dense networks (Loihi: "modest if any") | Davies et al. 2021 | **Hybrid datapath**: a small dense mode for layers that are dense (projections, output head) + event-driven mode for sparse layers; each layer uses whichever is cheaper | ✔ (output head dense) |
| W4 | Neuron-state memory access cancels spike savings | arXiv 2306.15749 | **Lazy updates**: idle neurons untouched; decay applied in one step from a lookup table when next used | ✔ |
| W5 | Same effort on every input; no notion of "easy" (all chips) | Overthinking / routing studies | **Metacognitive controller in hardware**: integer confidence gate picks instinct / flag / deliberate path; power-gates unused units | ✔ (gate + early exit) |
| W6 | No procedural memory / instinct (all) | Voyager (skills live outside the model) | **Skill-memory unit**: hash table with saturating counters; compiled habits answer without waking deep layers; periodic audit | Stretch |
| W7 | No on-chip learning while running (NorthPole: inference only; GPUs: separate training job) | IBM; Loihi supports programmable plasticity but not language-model fast weights | **Fast-weight (delta-rule) learning unit**: rank-1 update per token, state stays on chip | Stretch |
| W8 | No associative / content-addressable memory (GPU, TPU) | Our L measurements | **Hippocampus recall unit**: hash/CAM lookup in 1–2 cycles; recall-bypass skips deep layers on confident hits | ✔ |
| W9 | Model must fit on chip; big models need hundreds of chips (NorthPole, Groq: ~300–576 chips for 70B) | IBM; arXiv 2503.09650 | **Constant-size state** (L has no growing KV cache) + **sparse weight fetch**: only active weight rows are streamed from external memory | ✔ (SDRAM streaming) |
| W10 | Transformer lock-in (Etched) | The Register 2024 | **Configurable, not hard-wired**: layer sizes, neuron rule constants, thresholds, path policies in registers/microcode; FPGA first | ✔ |
| W11 | Special models needed, hand conversion ("software gap") (Innatera, Akida, neuromorphic in general) | Review arXiv 2603.26722 | **Co-designed toolchain**: L trained in PyTorch → automatic integer export → bit-exact golden model → chip | ✔ |
| W12 | Analog noise and chip-to-chip mismatch (Innatera) | arXiv 2106.10382 | **Fully digital, deterministic, bit-exact** | ✔ |
| W13 | General-purpose cores cost more energy per op (SpiNNaker2) | SpiNNaker2 papers | **Fixed-function units** for the hot loops; a tiny controller only for configuration | ✔ |
| W14 | Heat concentrated in one place (Cerebras ~23 kW wafer) | Introl | **Low activity → low power density**; clock-gated idle units; hard **energy cap per token** bounds worst-case heat | ✔ |
| W15 | Kernel launches, global synchronisation; one failure stops a big synchronous job | NVIDIA; Meta Llama 3 | **Hard-wired dataflow pipeline per token**, no launches; tiles work independently (a failed tile can be mapped out — proposal) | ✔ pipeline / proposal |
| W16 | Closed access (Loihi via research programme) | Lava/INRC | **Open design**: RTL, toolchain and measurements published | ✔ |
| W17 | Big-chip cost and e-waste | Gen-AI e-waste 1.2–5 Mt | **Add-on tile beside existing GPUs** extends their useful life; low-cost FPGA → small ASIC path | Proposal |

## 2. What SPARK cannot fix (say it before judges do)
- **Training** stays on GPUs (dense backprop is what GPUs are good at).
- **Very large models** still need external memory; SPARK reduces traffic, it doesn't remove capacity limits.
- **FPGA is several times less efficient than a custom chip**; full benefits need silicon.
- **New risks we introduce**: event-queue load imbalance, hash-table capacity/collisions, wrong "habits" in skill memory (handled by audits), and confidence gates that are miscalibrated (handled by thresholds tuned on held-out data).

## 3. SPARK core block diagram

```
                ┌──────────────────────── SPARK CORE ─────────────────────────┐
 byte in ──────►│ [Input encoder]                                              │
                │       │                                                      │
                │       ▼                                                      │
                │ ┌───────────────────────────┐   hit + confident              │
                │ │ METACOGNITIVE CONTROLLER  │──────────────► INSTINCT PATH   │
                │ │ confidence gate (integer) │   [Hippocampus recall unit]    │
                │ │ path select + power gates │   [Skill-memory unit]* ──┐     │
                │ └──────┬──────────┬─────────┘                          │     │
                │  unsure│          │ deliberate                         │     │
                │        ▼          ▼                                    │     │
                │   FLAG path   DELIBERATE PATH (per layer, until exit)  │     │
                │   (uncert.    [Membrane + homeostasis unit, lazy decay]│     │
                │    signal)    [Spike encoder → active-neuron queue,    │     │
                │               change-only]                             │     │
                │               [Event-driven sparse engine, 4-bit]      │     │
                │               [Fast-weight learning unit]*             │     │
                │               [Early-exit check]                       │     │
                │                         │                              │     │
                │                         ▼                              ▼     │
                │               [Output head, dense mode] ──────► byte out     │
                │                                                              │
                │ On-chip SRAM: weights (hot) · neuron state · fast weights ·  │
                │ hash table · skill table      External SDRAM: cold weights   │
                │ Control: config registers · energy cap · clock gating ·      │
                │ cycle/energy counters · sparsity & path on/off switches      │
                └──────────────────────────────────────────────────────────────┘
 * = stretch goal on the prototype
```

### Data flow for one byte
1. Controller checks the hippocampus (and skill memory). Confident hit → output directly; deep units stay clock-gated.
2. Otherwise each layer: lazily catch up decay for touched neurons → update membranes → emit only changed, non-zero spikes into the queue → sparse engine fetches only those weight rows → fast-weight unit updates (stretch) → early-exit check.
3. Output head (dense mode) → byte out. Counters record work done and path taken.

## 4. Number formats and memory
- Spikes: 4-bit signed (−8..8). Weights: 4–8-bit with power-of-two scales (shifts). State: 16-bit integer with saturation.
- No floating point, exp, divide or softmax on the chip; nonlinearities via small lookup tables.
- Tang Nano 20K budget: ~828 Kbit on-chip RAM, 8 MB SDRAM, 48 18×18 multipliers, 20,736 LUTs → small L-Edge model (~0.3–1M params); hot state on-chip, cold weights streamed sparsely.

## 5. Prototype scope
- **MVP (must have for cluster finals):** event-driven sparse engine, membrane unit with lazy decay, change-only spikes, hippocampus recall-bypass, confidence gate + early exit, energy cap, counters, power/heat measurement.
- **Stretch:** fast-weight learning unit, skill-memory unit, second tile.
- **Proposal only:** multi-tile chip with on-chip network, tile mapping-out for fault tolerance, ASIC tape-out.

## 6. How we prove it
Same output as the GPU (bit-exact); energy/token vs RTX 3050 (batch 1 and batch 64, honestly); every mechanism switched off vs on; easy vs hard input; board watts and °C.
