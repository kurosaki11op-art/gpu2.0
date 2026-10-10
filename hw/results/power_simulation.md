# SPARK switching-activity power simulation (SIMULATED, pre-silicon)

Method (standard pre-silicon power estimation, as in Vivado Power Analyzer / PrimeTime PX with VCD/SAIF):
the real Verilog core runs in iverilog on real held-out Python text with the trained sparsity-0.05 model.
After 240 bytes of warm-up (so the recall memory is realistic), a VCD records bytes 240–299 (60 bytes).
We count every bit flip of every net and register (clock excluded), every block-RAM / small-RAM access
(new read address) and clock cycles × 4,090 flip-flops (from place-and-route).

Energy per event (45 nm class, Horowitz ISSCC 2014 scale): 2 fJ per net bit-toggle, 5 pJ per 32-bit block-RAM
access, 0.06 pJ per bit of small-RAM access, 2 fJ per flip-flop per cycle (no clock gating).
"As built": block RAMs are clocked every cycle. "Read-enable": a block RAM spends energy only on a real access
(a one-line RTL change). Script: `hw/power/power_sim.py`; raw numbers: `hw/power/power_results.json`.

| Setting (same model, same text) | Cycles/byte | Bit flips/byte | Block-RAM accesses/byte | Energy/byte (read-enable) | Energy/byte (as built) | vs dense |
|---|---|---|---|---|---|---|
| Compute every neuron (GPU-style dense) | 10,665 | 3.45 M | 38,814 | 362 nJ | 648 nJ | 1× |
| Skip silent neurons | 5,147 | 1.71 M | 17,645 | 169 nJ | 313 nJ | 2.1× less |
| **SPARK effort LOW** | 1,714 | 0.56 M | 5,769 | 56 nJ | 104 nJ | **6.2–6.5× less** |
| SPARK effort MEDIUM | 3,584 | 1.22 M | 11,995 | 116 nJ | 218 nJ | 3.0–3.1× less |
| **SPARK effort HIGH** | 4,531 | 1.45 M | 15,055 | 147 nJ | 275 nJ | **2.4–2.5× less** |

- The raw bit-flip count alone (no energy assumptions) falls **6.2×** on low effort and **2.4×** on high effort.
- Agrees with the independent operation-count estimate (`energy_estimate.md`: 7.9× / 2.5×); the simulation is a
  little lower because it includes control logic and fixed overheads.
- Accuracy for these settings on 2,000 bytes: dense 59.9%, low 68.1%, high 72.6% (`model_accuracy.md`).

## What simulation cannot show (needs the board)
Static/leakage power (large on FPGAs, so the board-level saving will be smaller), voltage-regulator losses,
real FPGA routing capacitance, temperature. Label these results **SIMULATED**, not MEASURED.
