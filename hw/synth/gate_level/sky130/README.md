---
title: Gate-level checks of the core (SKY130 cells and generic gates)
tags: [l, hardware, verification, gate-level]
---

# Gate-level checks of the L Cortex core (SIMULATED, small size)

Same test as `../run_gate.py` (NB = 64 code bits, 24 commands, 95 output lines compared with the integer model).

| Netlist | Cells | Result vs the integer model |
|---|---|---|
| RTL | - | 0 mismatches |
| Yosys generic gates (AND, NAND, MUX, DFF) | 42,778 | 0 mismatches |
| **SKY130 `sky130_fd_sc_hd` cells + OpenRAM macro models (the ASIC build, clock gates in)**, flops power up 0 | 11,228 (7 SRAM macros, 14 clock gates) | **0 mismatches** |
| same, flops power up 1 | same | **0 mismatches** |
| Gowin-primitive netlist (`../run_gate.py`) | - | HANGS at the first LEARN; suspect the hand-made cell models (block-RAM model), not the design; see the journal |

Reproduce: `yosys -q synth_core_sky130.ys` (paths inside point at the PDK, the OpenRAM macros and `hd_tt_dontuse.lib` as in `hw/asic`), then `iverilog -g2005 -DFUNCTIONAL -DUNIT_DELAY=#0 -s tb_cortex_core -Ptb_cortex_core.NB=64 -Ptb_cortex_core.AW=9 ... netlist_sky.v tb_gate.v primitives.v sky130_fd_sc_hd.v <sram macro .v>`. For the power-up test the flip-flop and latch primitives in `primitives.v` get `initial Q = 1'b0` (or 1'b1). Limit: the core only, NB = 64; the full 4,608-bit chip has not been simulated at gate level.

Related: [Hardware index](../../../HARDWARE_INDEX.md), [Pre-fabrication verification](../../../results/prefab_verification.md)
