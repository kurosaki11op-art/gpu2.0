set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 3
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_db floor2c/cortex_groute.odb
read_sdc cortex.sdc
set_propagated_clock [all_clocks]
detailed_route -guide floor2c/route.guide -bottom_routing_layer met1 -top_routing_layer met5 -or_seed 42 -droute_end_iter 1 -output_drc floor2c/route_drc_pass1.rpt -verbose 1
puts "diag pass done"
