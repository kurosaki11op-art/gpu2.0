set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 4
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_db spark_cts.odb
read_sdc spark.sdc
# ---------------------------------------------------------------- routing
set_routing_layers -signal met1-met5 -clock met1-met5
global_route -guide_file route.guide -congestion_iterations 30 -allow_congestion -verbose
estimate_parasitics -global_routing
detailed_route -output_drc route_drc.rpt -output_maze maze.log -verbose 1 -droute_end_iter 30
write_db spark_routed.odb
filler_placement {sky130_fd_sc_hd__fill_1 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_8}
check_antennas -report_file antenna.rpt

# ---------------------------------------------------------------- outputs and reports
write_db spark_final.odb
write_def spark_final.def
write_verilog spark_final.v
estimate_parasitics -global_routing
report_checks -path_delay max -format full_clock_expanded > timing_setup.rpt
report_checks -path_delay min > timing_hold.rpt
report_wns > timing_summary.rpt
report_tns >> timing_summary.rpt
report_worst_slack -max >> timing_summary.rpt
report_worst_slack -min >> timing_summary.rpt
report_design_area > area.rpt
report_power > power.rpt
puts "SPARK flow done"
