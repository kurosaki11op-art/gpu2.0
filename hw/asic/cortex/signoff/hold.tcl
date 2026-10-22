# Hold repair on the routed layout: insert delay buffers on the failing endpoints, route only the new nets, re-check.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 3
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
set_routing_layers -signal met1-met4 -clock met1-met4
estimate_parasitics -placement
puts "BEFORE: hold [sta::worst_slack -min]  setup [sta::worst_slack -max]"
repair_timing -hold -hold_margin 0.1 -allow_setup_violations -verbose
estimate_parasitics -placement
puts "AFTER repair: hold [sta::worst_slack -min]  setup [sta::worst_slack -max]"
write_db floor2e/cortex_hold.odb
global_route -guide_file floor2e/hold.guide -congestion_iterations 30 -allow_congestion -start_incremental -end_incremental
detailed_route -guide floor2e/hold.guide -bottom_routing_layer met1 -top_routing_layer met4 -or_seed 42 -droute_end_iter 20 -output_drc floor2e/hold_drc.rpt -verbose 1
write_db floor2e/cortex_hold_routed.odb
estimate_parasitics -placement
puts "AFTER route: hold [sta::worst_slack -min]  setup [sta::worst_slack -max]"
puts "hold repair done"
