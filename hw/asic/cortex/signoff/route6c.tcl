# floor2h final flow: hold repair (pre-route, large margin) -> global route -> antenna diodes -> detailed route (met1-met4) -> checks
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set OUT floor2h
set_thread_count 3
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_db $OUT/cortex_cts.odb
read_sdc cortex.sdc
set_propagated_clock [all_clocks]
set_wire_rc -signal -layer met2
set_wire_rc -clock -layer met5
set_routing_layers -signal met1-met4 -clock met1-met4
estimate_parasitics -placement
puts "PRE hold [sta::worst_slack -min] setup [sta::worst_slack -max]"
repair_timing -hold -slack_margin 0.35
estimate_parasitics -placement
puts "AFTER hold repair: hold [sta::worst_slack -min] setup [sta::worst_slack -max]"
puts "== global routing [clock format [clock seconds]]"
global_route -guide_file $OUT/route.guide -congestion_iterations 30 -allow_congestion
puts "== detailed routing [clock format [clock seconds]]"
detailed_route -guide $OUT/route.guide -bottom_routing_layer met1 -top_routing_layer met4 -or_seed 42 \
    -droute_end_iter 40 -output_drc $OUT/route_drc.rpt -verbose 1
write_db $OUT/cortex_routed.odb
estimate_parasitics -placement
puts "POST ROUTE hold [sta::worst_slack -min] setup [sta::worst_slack -max]"
puts "SPARK Cortex $OUT final routing done [clock format [clock seconds]]"
