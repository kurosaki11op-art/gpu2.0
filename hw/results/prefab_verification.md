# SPARK pre-fabrication verification (software only, no silicon)

Goal: prove the chip works before paying for fabrication. Every level is checked against the Python
reference model (`hw/golden/spark_golden.py`): same inputs, same weights, the hardware must give the same
answer for every token. All results are SIMULATED (Icarus Verilog; SkyWater sky130 cell models; OpenRAM SRAM models).

| # | Design level | Test | Result |
|---|---|---|---|
| 1 | SPARK core RTL (FPGA build) | 100 tokens, all effort modes | 0 mismatches |
| 2 | FPGA board top | UART testbench, 40 tokens | PASS |
| 3 | ASIC core + 44 OpenRAM SRAM macros | memories start unknown; 2 configs × 20 tokens | 0 mismatches |
| 4 | ASIC core, gate level (101,799 sky130 cells) | flip-flops power up 0 and 1 | 0 mismatches |
| 5 | SPARK chip top, pins only, RTL | 448 weight words written over UART and read back; 20 tokens | all words correct, 0 mismatches |
| 6 | SPARK chip top, pins only, gate level (95k cells + 44 SRAMs) | power-up 0 and power-up 1; 448 words; 6 tokens each | all words correct, 0 mismatches, PASS both |
| 7 | Chip evaluation PCB (KiCad 7) | DRC, schematic ERC, PCB-vs-schematic parity | 0 errors / 0 warnings / 0 unconnected; 168 pads, 0 mismatches |
| 8 | Physical design (OpenROAD) | placement, clock tree, global route done; detailed route in progress | see `hw/asic/README.md` |

## Bugs found by the software tests (each would have cost a fabrication run)
1. **Memories have no power-on contents on silicon.** Gate-level sim gave all-X outputs. Fix: 1,024-cycle
   zero-fill sequencer after reset (`ready` pin), start requests held until it finishes.
2. **UART TX line low at power-up.** With flip-flops waking up as 0, the TX pin was low until the first clock
   edge in reset; the host read a garbage 0xFF byte and every reply shifted by one (one weight word lost).
   Fix: `uart_tx = tx_line | rst` (rst is set asynchronously by `rst_n`). Found by test 6 with power-up 0;
   re-run passes.

## Still needed before tape-out (not done yet)
- Detailed routing to zero violations, then sign-off DRC/LVS in Magic/KLayout/Netgen.
- Static timing at slow/typical/fast corners with parasitics (current numbers: typical corner, 50 MHz target).
- I/O pad ring and the chip-top (spark_chip) layout; the routed block is the core.
- Optional: run the same RTL on a low-cost FPGA board first for real-hardware proof.

Logs: `hw/results/chip_gl/`. Re-run: `cd hw/asic/chipsim && sh build_and_run.sh`.
