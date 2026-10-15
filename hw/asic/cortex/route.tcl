# Detailed routing of the current clock-tree database (cortex_cts.odb: pipelined, clock-gated core, lighter clock tree):
# global route -> detailed route -> parasitics from the routed wires -> timing, area, power, DRC count.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 3
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_db cortex_cts.odb
read_sdc cortex.sdc
set_propagated_clock [all_clocks]
set_wire_rc -signal -layer met2
set_wire_rc -clock -layer met5
set_routing_layers -signal met1-met5 -clock met1-met5
global_route -congestion_iterations 30 -allow_congestion
estimate_parasitics -global_routing
repair_timing -hold -slack_margin 0.05
detailed_placement
global_route -congestion_iterations 30 -allow_congestion
puts "== detailed routing"
detailed_route -output_drc route_drc.rpt -verbose 1 -droute_end_iter 10
write_db cortex_routed.odb
estimate_parasitics -global_routing
puts "== after detailed routing"
report_wns
report_tns
report_worst_slack -max
report_worst_slack -min
report_design_area
puts "SPARK Cortex routing done"
