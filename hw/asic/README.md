# SPARK chip in SkyWater SKY130 (open-source ASIC flow)

The SPARK core (the same Verilog that runs on the FPGA) implemented as a silicon layout in the SkyWater
130 nm open PDK, with open-source tools:

| Step | Tool | Result |
|---|---|---|
| Memories | OpenRAM SRAM macros `sky130_sram_2kbyte_1rw1r_32x512_8` (VLSIDA/sky130_sram_macros, Apache-2.0) | 44 macros (683 × 417 µm each) hold embeddings, weights and the recall table; small state RAMs become flip-flops |
| RTL with SRAMs | Icarus Verilog, `tb_asic.v` (weights written through the `ld_*` port) | **0 mismatches** vs the golden model, 20 tokens, 2 configurations (recall + effort dial + early exit; plain event-driven) |
| Synthesis | Yosys 0.33 → `sky130_fd_sc_hd` (typical corner) | 94,147 standard cells (21,853 flip-flops) + 44 SRAM macros, 13.4 mm² |
| Gate-level simulation | synthesized netlist + SKY130 cell models + SRAM models | see `glsim/gl_check.log` |
| Place and route | OpenROAD (`pnr/flow.tcl`): floorplan, macro placement, power grid, placement, CTS, global + detailed routing | see `pnr/` reports |
| GDSII | KLayout (`gds/def2gds.py`): routed DEF + real cell and SRAM layouts | see `gds/` |

## Floorplan
6.3 × 3.6 mm die; 44 SRAM macros in 6 rows × 8 columns with 150 µm horizontal channels and 100 µm
vertical gaps (the macros have their write port on the bottom edge and read port on the top edge, met4 pins);
standard cells in the channels. Power: met1 rails, met4/met5 straps (56 µm pitch), macro grid on met4/met5.
Clock target 50 MHz (20 ns), typical corner.

## Reproduce
```
micromamba create -p /opt/eda_or -c litex-hub -c conda-forge openroad
micromamba create -p /opt/eda_pdk -c litex-hub -c conda-forge open_pdks.sky130a magic netgen
git clone https://github.com/VLSIDA/sky130_sram_macros /opt/sky130_sram_macros
cd syn && yosys synth.ys            # needs hd_tt_dontuse.lib (TT lib with lpflow/probe cells marked dont_use) and th*.hex
cd ../pnr && openroad -no_init -exit flow.tcl
cd ../gds && klayout -b -r def2gds.py -rd def=../pnr/spark_final.def -rd out=spark_chip.gds
```

## Limits
- Typical corner only; no multi-corner sign-off, no IR-drop analysis, no pad ring (this is the core macro).
- Thresholds (th0/th1) are baked in as constants from the trained model; weights are loadable.
- OpenRAM macros are used as published by VLSIDA; their own DRC/LVS status is per that repository.
