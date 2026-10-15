# Diagnostic: ONE detailed-routing pass of cortex_cts.odb to get the violation report (types, layers, places).
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
set f [open diag/macro_locs.txt w]
set dbu [[ord::get_db_block] getDefUnits]
foreach inst [[ord::get_db_block] getInsts] {
    if {[[$inst getMaster] isBlock]} {
        set b [$inst getBBox]
        puts $f "[expr [$b xMin]/double($dbu)] [expr [$b yMin]/double($dbu)] [expr [$b xMax]/double($dbu)] [expr [$b yMax]/double($dbu)]"
    }
}
close $f
puts "== detailed routing"
detailed_route -output_drc diag/route_drc_pass1.rpt -verbose 1 -droute_end_iter 1
estimate_parasitics -global_routing
puts "== after detailed routing"
report_wns
report_tns
report_worst_slack -max
report_worst_slack -min
report_design_area
puts "SPARK Cortex routing done"
