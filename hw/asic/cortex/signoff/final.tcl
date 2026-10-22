# Routed layout (floor2e/cortex_routed.odb): timing, power and DEF export. Parasitics estimated from placement (not extracted from the routed wires).
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_db floor2e/cortex_routed.odb
read_sdc cortex.sdc
set_propagated_clock [all_clocks]
set_wire_rc -signal -layer met2
set_wire_rc -clock -layer met5
estimate_parasitics -placement
puts "== TIMING at 20 ns clock"
report_worst_slack -max
report_worst_slack -min
report_tns
report_clock_skew
write_def floor2e/cortex_routed.def
set icg [get_cells -filter "ref_name == sky130_fd_sc_hd__dlclkp_1" *]
set_power_activity -global -activity 0.1
set k 0
foreach c $icg {
  set d [expr {[regexp {\.g1\.} [get_full_name $c]] ? 9 : 1000}]
  create_generated_clock -name gck$k -source [get_ports clk] -divide_by $d [get_pins [get_full_name $c]/GCLK]
  incr k
}
set_propagated_clock [all_clocks]
puts "== POWER gated clocks, 10% activity"
report_power
