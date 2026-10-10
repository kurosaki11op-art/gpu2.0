# SPARK hardware — claims sheet for the pitch

Labels: **MEASURED** (board) · **SIMULATED** (switching-activity power simulation of the real RTL) · (our RTL simulation, synthesis/place-and-route, or golden-model evaluation, which is bit-exact with the RTL) · **CITED** (published source) · **MODELLED** (calculation with stated assumptions) · **VISION** (proposal, not built).

Sources: `hw/results/model_accuracy.md` (trained model), `hw/results/sim_results.md` (mechanism study, demo weights), `hw/results/synthesis.md` (fit and timing).

## 1. Claims you CAN make now

| # | Claim (say it like this) | Number | Label |
|---|---|---|---|
| C1 | "We designed, built and verified a working event-driven AI chip core in Verilog." | RTL + golden model + testbench; UART board design | MEASURED |
| C2 | "It runs a trained brain-inspired spiking model, bit-exact with our reference model." | 0 mismatches (trained model, 3 configurations; demo weights, 9 configurations × 527 tokens) | MEASURED |
| C3 | "The chip design fits a ₹4,199 FPGA and meets timing." | Tang Nano 20K (GW2AR-18): 76% logic (LUT4), 41/46 block RAM, max clock 54 MHz vs 27 MHz needed (final RTL with effort dial) | MEASURED (place-and-route) |
| C4 | "Our brain-inspired chip predicts the next byte of real Python code with up to 74% accuracy — better than a 4-byte lookup table (64.9%) and a plain neural network of the same size (61.9%)." | 73.8% (sparsity-0 model) / 72.6% (sparsity-0.05), 2,000 held-out bytes, effort setting "high" | MEASURED (bit-exact golden model; RTL bit-exact) |
| C5 | "It has an effort dial, like a brain: easy inputs are answered from memory with ~7.6× less work; hard ones get more thought." | Low effort 68.1% at 59 events/token (7.6× less than dense ~448); high effort 72.6% at 172 (2.6× less) | MEASURED |
| C6 | "A hippocampus-like recall memory learns in one shot while running and answers about two-thirds of the bytes without the full network." | 1,366 of 2,000 bytes on low effort; +12 points over the network alone | MEASURED |
| C6b | "On a 10× longer, harder test the chip still gains 7–9 points over the network alone, and accuracy keeps rising as we add memory, which is cheap SRAM, not compute." | 20,000 bytes: network 59.5% → chip 66.6% → 4-memory prototype 68.4% → larger memory 69.4% | MEASURED (prototype memories not yet in RTL) |
| C6s | "We simulated the real chip design switching on real text: 2.4× less energy per byte at high effort (72.6% accuracy) and 6.2× less at low effort — and the raw count of switching wires drops just as much." | 147 / 56 vs 362 nJ per byte (read-enable); bit flips 1.45 M / 0.56 M vs 3.45 M | SIMULATED (switching-activity, `hw/results/power_simulation.md`) |
| C6c | "We estimate 2.5× less energy per token at 72.6% accuracy, and 7.9× less on easy input at 68.1% — versus computing every neuron at 59.9%." | 22.6 / 7.3 vs 57.3 nJ per token; robust to ±2× per-operation energy (7.5–8.1×) | MODELLED from MEASURED counts (`hw/results/energy_estimate.md`) |
| C6d | "Cooling water follows energy: that is a projected 60–87% less cooling water per token." | proportional projection | PROJECTED |
| C7 | "Switching every 'think-less' trick on at once made things worse, so we built an on-chip controller that decides when each trick pays off." | Demo study: always-on 3,031 cycles/token vs adaptive 1,273 (dense 8,296) | MEASURED |
| C8 | "Skipping silent neurons cut work 4.9× and weight reads 6.6× vs dense in our mechanism study." | 8,296 → 1,688 cycles; 7,168 → 1,088 weight reads (demo weights) | MEASURED |
| C9 | "Fewer firing neurons means less work but lower accuracy — we measured that trade-off and pick the balance point." | 55% firing → 63.9%; 26% → 59.9%; 16% → 51.5%; 12% → 47.6% (network alone) | MEASURED |
| C10 | "All weights and the recall memory live on the chip, beside the compute." | 41 of 46 block RAMs | MEASURED |
| C11 | "Moving data costs far more energy than computing: up to 84% of a GPU's dynamic energy is data movement." | — | CITED |

## 2. Claims to make CAREFULLY (say the label)

| Claim | Why careful |
|---|---|
| "Less work should mean less energy." | Work (events, cycles, memory reads) is a proxy. Watts are not measured yet — the board kit is ready (`hw/board/`). Say "work" until then. |
| "At 27 MHz the core processes ~5,000–8,000 bytes per second." | MODELLED from cycle counts (3,474–5,216 cycles/byte for the trained model); UART and host overhead not included. |
| "Our debugging found a 41% → 74% jump." | 41% → 64% was fixing training bugs (found by comparing with a plain network); 64% → 74% is the recall memory and the effort dial. Say both. |
| "74% accuracy." | On a 2,000-byte test. On a 20,000-byte harder test the same chip gets 66.6%; quote both if asked. |
| "On-chip learning." | Say "one-shot memory learning while running" (the recall unit). We tested weight-update learning on the chip; it did not help at int4 precision — honest finding, documented. |

## 3. Claims NOT to make
- Measured watts, or absolute litres / tonnes saved — not measured yet. Say "estimated" for energy (C6c) and "projected" for water (C6d).
- "Faster or more efficient than a GPU" — our dense baseline is our own core in dense mode, not a GPU.
- "Solves GPU limitations" / "replaces GPUs".
- "As smart as an LLM" — this is a small byte-level model for Python code, ~130 KB of weights.
- Energy cap as a win — it cuts work but collapses accuracy (9.3% on the earlier trained model).

## 4. The hardware story in 30 seconds
> "GPUs compute every neuron for every input. We built a chip core that computes only what matters: it skips silent neurons, recalls what it has already seen, and an on-chip controller decides when thinking less actually saves work. It runs our trained spiking model bit-exact, fits a ₹4,199 FPGA, predicts real Python code with up to 74% accuracy — better than a lookup table or a plain network of the same size — and has an effort dial: easy inputs answered from memory with 7.6× less work, hard ones get full thought. Next: real watts and temperature on the board."

## 5. Likely judge questions — hardware

| Question | Answer |
|---|---|
| "Isn't 'dense' a strawman?" | It is the same core doing what a GPU does — every input, every weight — so it isolates the effect of event-driven processing. The GPU comparison comes from measured GPU energy (software track). |
| "74% sounds low." | It's next-byte prediction on code by a tiny model (~130 KB). The best lookup table we built gets 64.9%, a plain neural network of the same size 61.9%. We measured that more memory raises it further; this proves the principle. |
| "Is it really brain-like?" | Spiking neurons that fire only when needed, change-only updates, leaky membranes, a hippocampus-like one-shot memory, and an effort dial (instinct vs deliberation). We say "brain-inspired", not "a brain". |
| "Why did accuracy jump from 41% to 74%?" | Two training bugs fixed (learning rate for integer weights, far-too-strong sparsity penalty), a 3-byte context window, a better recall hash, and the effort dial. Documented step by step, including what did not help. |
| "Cycles aren't energy." | Agreed. Energy follows switching and memory reads; the INA219 measurement kit is ready for the board. |
| "Why did 'all tricks on' do worse?" | Each mechanism has a cost when it doesn't pay off; hence the adaptive controller. |
| "What's novel vs Loihi / NorthPole?" | A brain-like language model co-designed with its chip: recall unit, adaptive think-less controller and event-driven engine, with measured accuracy and a measured accuracy–sparsity trade-off. |

## 6. Vision claims (label as VISION)
SPARK as a chiplet beside a GPU; many tiles on an on-chip spike network; stacked SRAM; near-threshold "instinct" mode; warm-water closed-loop cooling; long-term analog in-memory, photonic and reversible logic. See `docs/spark_full_stack_hardware_proposal.md`.
