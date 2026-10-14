# OpenSTA: timing and an ESTIMATED power figure for the synthesized SPARK Cortex (typical corner, no wires/parasitics).
read_liberty /opt/eda_pdk/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib
read_verilog cortex_syn.v
link_design cortex_board_top
create_clock -name clk -period 20.0 [get_ports clk]
set_input_delay 2.0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 2.0 -clock clk [all_outputs]
report_checks -path_delay max -format end -group_count 3
report_wns
report_tns
set_power_activity -global -activity 0.1
report_power
