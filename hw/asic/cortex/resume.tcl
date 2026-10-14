# Resume the estimate flow from the saved clock-tree database (cortex_cts.odb): global routing, timing repair with
# global-route parasitics, then timing / area / power reports. report_design_area prints to the log only.
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
puts "== after global route"
report_wns
report_tns
repair_timing -setup
repair_timing -hold -slack_margin 0.05
estimate_parasitics -global_routing
report_checks -path_delay max -format full_clock_expanded > timing_setup.rpt
report_checks -path_delay min > timing_hold.rpt
report_wns > timing_summary.rpt
report_tns >> timing_summary.rpt
report_worst_slack -max >> timing_summary.rpt
report_worst_slack -min >> timing_summary.rpt
puts "== final"
report_wns
report_tns
report_worst_slack -max
report_worst_slack -min
report_clock_skew
report_design_area
set_power_activity -global -activity 0.1
report_power > power.rpt
report_power
puts "SPARK Cortex estimate flow done"
