# SPARK core v0 — synthesis results (Yosys 0.33, `synth_gowin`, target GW2AR-18 / Tang Nano 20K)

Synthesis only (no place-and-route or timing yet). Counts from `yosys stat`.

| Build | Block RAM (BSRAM, of 46) | LUT1–LUT4 cells (chip has 20,736 LUT4) | LUT-RAM cells (RAM16SDP4) | Flip-flops | Fits Tang Nano 20K? |
|---|---|---|---|---|---|
| 1. First attempt (weights as read-only memories) | 0 — weights became logic | 63,706 | 1,312 | ~3,450 | ✘ (~3× over) |
| 2. Weight load port + block-RAM hints | 29 (27 DPX9 + 2 SDPX9) | 31,491 | 608 | ~3,360 | ✘ (~1.5× over) |
| 3. Build 2 with neuron constants fixed at build time (`spark_top.v`) | 29 | 24,372 | 608 | ~3,140 | ✘ (~1.2× over) |

## What this means
- **Memory fits**: all weights (~460 Kbit), the embedding and the recall table sit in 29 of 46 block RAMs.
- **Logic does not fit yet** on the ₹4,199 board: ~24k LUT cells vs 20.7k available. The remaining cost is the 16-lane wide datapath (16 parallel membrane updates, a 16-lane argmax chain, 384-bit-wide accumulator words held in LUT-RAM).
- **Known fixes (next pass)**: process the membrane and argmax passes 4 lanes per cycle instead of 16 (they are a small share of cycles), move accumulators to block RAM, narrow the argmax compare to 24 bits. Expected to bring logic well under the limit; to be confirmed.
- **Alternative board**: the PYNQ-Z2 (Xilinx XC7Z020, 53,200 6-input LUTs, 140 block RAMs) has ample room for build 3 as is; many college VLSI labs have one.
- Timing (maximum clock) is not known until place-and-route; any tokens/second figure is MODELLED until then.
