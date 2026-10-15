# Detailed routing of the FLOOR3 floorplan (floor3/cortex_groute.odb, guide floor3/route.guide), with the settings the
# 2022 OpenROAD flow scripts used for sky130hd: signals on met1-met5 only (no li1 routing), clock on met3-met5,
# or_seed 42, up to ITER passes (default 64). Writes floor3/route_drc.rpt and floor3/cortex_routed.odb.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 3
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_db floor3/cortex_groute.odb
read_sdc cortex.sdc
set_propagated_clock [all_clocks]
set ITER [expr {[info exists ::env(ITER)] ? $::env(ITER) : 64}]
detailed_route -guide floor3/route.guide -bottom_routing_layer met1 -top_routing_layer met5 -or_seed 42 \
    -droute_end_iter $ITER -output_drc floor3/route_drc.rpt -verbose 1
write_db floor3/cortex_routed.odb
puts "SPARK Cortex floor3 routing done"
