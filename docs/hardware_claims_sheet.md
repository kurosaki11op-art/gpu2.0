# SPARK hardware — claims sheet for the pitch

Labels: **MEASURED** (from our RTL simulation or synthesis) · **CITED** (published source) · **MODELLED** (calculation with stated assumptions) · **VISION** (proposal, not built).
Source of measured numbers: `hw/results/sim_results.md`, `hw/results/synthesis.md`. Demo weights (random sparse int4), 527 bytes of Python-like text with repeats, same core and hardware in every configuration.

## 1. Claims you CAN make now

| # | Claim (say it like this) | Number | Label |
|---|---|---|---|
| C1 | "We designed and built a working event-driven AI core in Verilog." | 9 configurations, 527 tokens each | MEASURED |
| C2 | "It is verified bit-exact against an independent reference model." | 0 mismatches in 4,743 token checks (prediction, path and event counts) | MEASURED |
| C3 | "Skipping silent neurons cut the work per token about 6× compared with processing everything, GPU-style, on the same hardware." | 4,347 → 779 cycles (5.6×); 3,584 → 544 weight reads (6.6×) | MEASURED |
| C4 | "A brain-like recall memory answered 30% of repeated text without running the network." | 160 of 527 bytes; 514 cycles/token (8.5× less than dense) | MEASURED |
| C5 | "Turning on every 'think-less' trick at once made it worse — so we built a controller that decides when each trick pays off." | Always-on: 1,486 cycles (2.9×) vs adaptive: 589 cycles (7.4×) | MEASURED |
| C6 | "Our adaptive controller cut work 7.4× vs dense and 2.5× vs naïvely enabling everything, and reached within 15% of the best single setting without being told which one was best." | 589 vs 514 (best single) vs 1,486 (always-on) cycles/token; weight reads 9.7× fewer than dense | MEASURED |
| C7 | "Even deciding how much to think must cost less than it saves — the controller's own overhead is a few cycles of counting per stage." | Pre-scan 2 cycles per 16 inputs; exit check probed every 16th token when not paying off | MEASURED (design) |
| C8 | "All weights and the recall memory fit in the FPGA's on-chip block RAM — memory beside compute." | 29 of 46 block RAMs on the GW2AR-18 | MEASURED (synthesis) |
| C9 | "Moving data costs far more energy than computing; up to 84% of a GPU's dynamic energy is data movement." | — | CITED |
| C10 | "Weight reads are the expensive part, and our core reads 6.6–9.7× fewer of them per token than dense processing." | see C3, C6 | MEASURED + CITED reasoning |

## 2. Claims to make CAREFULLY (with the label spoken)

| Claim | Why careful |
|---|---|
| "We expect energy per token to fall roughly with work done." | Work (cycles, memory reads) is a strong proxy, but watts are not measured yet. Say "work", not "energy", until the board measurement. |
| "With L's real activity (2–10% of neurons firing) the saving should be larger than in our demo (9–28%)." | Logical, but MODELLED until trained L-Edge weights run on the core. |
| "At a 27 MHz board clock, 589 cycles/token would be ~46,000 tokens/s." | MODELLED: timing not closed; clock not confirmed. |
| "It fits a ₹4,199 FPGA." | **Not yet**: logic is ~1.2× over on the Tang Nano 20K; fits a PYNQ-Z2-class board. Say "memory fits; one logic-optimisation pass remains". |

## 3. Claims NOT to make
- Any watts, joules, litres of water or tonnes of CO₂ saved — not measured yet.
- "Faster or more efficient than a GPU" — we compared against our own dense mode, not a GPU.
- "Solves GPU limitations" / "replaces GPUs".
- Any language-model quality claim from this hardware — demo weights.
- Energy-cap results as a win — it cut work 9.3× but changes outputs; quality impact unknown.

## 4. The hardware story in 30 seconds
> "GPUs compute everything. We built a chip core that computes only what matters: it skips silent neurons, recalls what it already knows, and an on-chip controller decides when thinking less actually saves work. Verified bit-exact in simulation, it cuts the work per token 7.4× and memory reads 9.7× against processing everything — and we learned that switching every trick on at once is worse, which is why the controller matters. Next: trained weights from our model L, and real watts on the board."

## 5. Likely judge questions — hardware

| Question | Answer |
|---|---|
| "Isn't 'dense mode' a strawman?" | It is the same core doing what GPUs do — every input, every weight. It isolates the effect of event-driven processing from everything else. The GPU comparison comes separately, from measured GPU energy. |
| "Random weights — does it mean anything?" | It proves correctness and the work saved for a given activity level. Quality needs trained weights; that is our next step. Demo activity (9–28%) is higher than L's (2–10%), so the demo is conservative. |
| "Cycles aren't energy." | Agreed. Energy follows switching activity and memory reads; we report both, and the INA219 board measurement is planned. |
| "Why did 'all tricks on' do worse?" | Each mechanism has a cost: change-only sends two events when a spike moves, early-exit checks cost work when they don't fire. Hence the adaptive controller — a key finding, not a failure. |
| "Does it fit the FPGA?" | Memory yes (29/46 block RAMs). Logic is ~1.2× over on the ₹4,199 board; we know the fix (narrower post-processing lanes) and it fits a PYNQ-Z2 today. |
| "What's novel vs Loihi/NorthPole?" | Co-design for a brain-like language model: recall unit + adaptive think-less controller + event-driven engine, with the finding that adaptivity is essential. |

## 6. Vision claims (label as VISION)
SPARK as a chiplet beside a GPU; many tiles on an on-chip spike network; stacked SRAM; near-threshold "instinct" mode; warm-water closed-loop cooling; long-term analog in-memory, photonic and reversible logic. See `docs/spark_full_stack_hardware_proposal.md`.
