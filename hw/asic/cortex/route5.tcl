# (route5: as route4 plus SIGL = signal routing layers, TOPL = top detailed-routing layer; env: OUT, GRA = layer adjustment (0 = none), MEXT = macro extension (0 = none), CLKL = clock layers, ITER)
# Routing of an existing clock-tree database in one go (floor2b/cortex_cts.odb by default; OUT=<dir>): global route with
# a guide and a light layer adjustment (GRA, default 0.1), then detailed routing on met1-met5 only (no li1), or_seed 42,
# up to ITER passes. Added after the heavy global-route settings of flow3.tcl (100 iterations, adjustment 0.3) did not
# finish in over two hours.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 3
set OUT [expr {[info exists ::env(OUT)] ? $::env(OUT) : "floor2b"}]
set GRA [expr {[info exists ::env(GRA)] ? $::env(GRA) : 0.1}]
set MEXT [expr {[info exists ::env(MEXT)] ? $::env(MEXT) : 2}]
set CLKL [expr {[info exists ::env(CLKL)] ? $::env(CLKL) : "met3-met5"}]
set ITER [expr {[info exists ::env(ITER)] ? $::env(ITER) : 30}]
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
set SIGL [expr {[info exists ::env(SIGL)] ? $::env(SIGL) : "met1-met5"}]
set TOPL [expr {[info exists ::env(TOPL)] ? $::env(TOPL) : "met5"}]
set_routing_layers -signal $SIGL -clock $CLKL
if {$GRA > 0} { foreach l {met1 met2 met3 met4 met5} { set_global_routing_layer_adjustment $l $GRA } }
if {$MEXT > 0} { set_macro_extension $MEXT }
puts "== global routing [clock format [clock seconds]]"
global_route -guide_file $OUT/route.guide -congestion_iterations 30 -allow_congestion
write_db $OUT/cortex_groute.odb
puts "== detailed routing [clock format [clock seconds]]"
detailed_route -guide $OUT/route.guide -bottom_routing_layer met1 -top_routing_layer $TOPL -or_seed 42 \
    -droute_end_iter $ITER -output_drc $OUT/route_drc.rpt -verbose 1
write_db $OUT/cortex_routed.odb
puts "SPARK Cortex $OUT routing done [clock format [clock seconds]]"
