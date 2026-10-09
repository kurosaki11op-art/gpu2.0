# SPARK hardware — claims sheet for the pitch

Labels: **MEASURED** (our RTL simulation, synthesis/place-and-route, or golden-model evaluation, which is bit-exact with the RTL) · **CITED** (published source) · **MODELLED** (calculation with stated assumptions) · **VISION** (proposal, not built).

Sources: `hw/results/model_accuracy.md` (trained model), `hw/results/sim_results.md` (mechanism study, demo weights), `hw/results/synthesis.md` (fit and timing).

## 1. Claims you CAN make now

| # | Claim (say it like this) | Number | Label |
|---|---|---|---|
| C1 | "We designed, built and verified a working event-driven AI chip core in Verilog." | RTL + golden model + testbench; UART board design | MEASURED |
| C2 | "It runs a trained brain-inspired spiking model, bit-exact with our reference model." | 0 mismatches (trained model, 3 configurations; demo weights, 9 configurations × 527 tokens) | MEASURED |
| C3 | "The chip design fits a ₹4,199 FPGA and meets timing." | Tang Nano 20K (GW2AR-18): 67% logic, 41/46 block RAM, max clock 53 MHz vs 27 MHz needed | MEASURED (place-and-route) |
| C4 | "Our spiking model predicts the next byte of real Python code with 66% accuracy — better than a 4-byte lookup table (64.9%) and a plain neural network of the same size (61.9%)." | 66.0% on 2,000 held-out bytes | MEASURED |
| C5 | "It does that with about 4× less work than processing every neuron, GPU-style." | 111 vs ~448 events per token (sparsity-0.05 model, recall + adaptive controller) | MEASURED |
| C6 | "A brain-like recall memory answers about a third of the bytes on its own, without running the network — and it also raises accuracy." | 739 of 2,000 bytes; accuracy 59.9% → 66.2% | MEASURED |
| C7 | "Switching every 'think-less' trick on at once made things worse, so we built an on-chip controller that decides when each trick pays off." | Demo study: always-on 3,031 cycles/token vs adaptive 1,273 (dense 8,296) | MEASURED |
| C8 | "Skipping silent neurons cut work 4.9× and weight reads 6.6× vs dense in our mechanism study." | 8,296 → 1,688 cycles; 7,168 → 1,088 weight reads (demo weights) | MEASURED |
| C9 | "Fewer firing neurons means less work but lower accuracy — we measured that trade-off and pick the balance point." | 55% firing → 66.9%; 26% → 66.0%; 16% → 51.5%; 12% → 47.6% (main path) | MEASURED |
| C10 | "All weights and the recall memory live on the chip, beside the compute." | 41 of 46 block RAMs | MEASURED |
| C11 | "Moving data costs far more energy than computing: up to 84% of a GPU's dynamic energy is data movement." | — | CITED |

## 2. Claims to make CAREFULLY (say the label)

| Claim | Why careful |
|---|---|
| "Less work should mean less energy." | Work (events, cycles, memory reads) is a proxy. Watts are not measured yet — the board kit is ready (`hw/board/`). Say "work" until then. |
| "At 27 MHz the core processes ~5,000–8,000 bytes per second." | MODELLED from cycle counts (3,474–5,216 cycles/byte for the trained model); UART and host overhead not included. |
| "Our debugging found a 41% → 66% jump." | True and a good due-diligence story, but say it was a training bug we found by comparing against a plain network, not a new invention. |

## 3. Claims NOT to make
- Any watts, joules, litres of water or tonnes of CO₂ saved — not measured yet.
- "Faster or more efficient than a GPU" — our dense baseline is our own core in dense mode, not a GPU.
- "Solves GPU limitations" / "replaces GPUs".
- "As smart as an LLM" — this is a small byte-level model for Python code, ~130 KB of weights.
- Energy cap as a win — it cuts work but collapses accuracy (9.3% on the earlier trained model).

## 4. The hardware story in 30 seconds
> "GPUs compute every neuron for every input. We built a chip core that computes only what matters: it skips silent neurons, recalls what it has already seen, and an on-chip controller decides when thinking less actually saves work. It runs our trained spiking model bit-exact, fits a ₹4,199 FPGA, predicts real Python code with 66% accuracy — better than a lookup table or a plain network of the same size — and does it with about 4× less work than processing everything. Next: real watts and temperature on the board."

## 5. Likely judge questions — hardware

| Question | Answer |
|---|---|
| "Isn't 'dense' a strawman?" | It is the same core doing what a GPU does — every input, every weight — so it isolates the effect of event-driven processing. The GPU comparison comes from measured GPU energy (software track). |
| "66% sounds low." | It's next-byte prediction on code by a tiny model (~130 KB). The best lookup table we built gets 64.9%, a plain neural network of the same size 61.9%. Accuracy grows with model size; this proves the principle. |
| "Why did accuracy jump from 41% to 66%?" | We found two training bugs (learning rate for integer weights, far-too-strong sparsity penalty) by comparing against a plain network; we also added a 3-byte context window and firing thresholds. Documented step by step. |
| "Cycles aren't energy." | Agreed. Energy follows switching and memory reads; the INA219 measurement kit is ready for the board. |
| "Why did 'all tricks on' do worse?" | Each mechanism has a cost when it doesn't pay off; hence the adaptive controller. |
| "What's novel vs Loihi / NorthPole?" | A brain-like language model co-designed with its chip: recall unit, adaptive think-less controller and event-driven engine, with measured accuracy and a measured accuracy–sparsity trade-off. |

## 6. Vision claims (label as VISION)
SPARK as a chiplet beside a GPU; many tiles on an on-chip spike network; stacked SRAM; near-threshold "instinct" mode; warm-water closed-loop cooling; long-term analog in-memory, photonic and reversible logic. See `docs/spark_full_stack_hardware_proposal.md`.
