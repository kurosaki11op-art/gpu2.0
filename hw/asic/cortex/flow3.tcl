# SPARK Cortex on SkyWater SKY130 (sky130_fd_sc_hd + 63 OpenRAM 2 KB SRAM macros), OpenROAD estimate flow:
# floorplan -> macro placement -> power grid -> placement + fanout repair -> clock tree -> timing repair ->
# global routing -> timing and power with global-route parasitics. No detailed routing (an estimate, not sign-off).
# FLOOR3 (partial redesign of the floorplan, from docs/research_openroad_sram_routing.md): the 63 SRAM macros sit in two
# 4-column arrays, left and right, with the logic in ONE block between them (no standard cells in the macro channels:
# a placement blockage covers each array); all macros R0 so their met4 pins (bottom edge) face a row channel; the
# power grid keeps PDN_HALO um (default 20) away from the macros; the router guide and layer adjustment as in the 2022
# OpenROAD flow scripts. Output: $OUT/cortex_cts.odb and $OUT/route.guide (OUT default floor3).
# GPD = global placement target density (default 0.45); SKIPGR = stop after the clock tree (route with route4.tcl).
# FLOOR2B: OUT=floor2b BLOCK=0 LW=0 = the old 8 x 8 grid (floor2) with only the router / power-grid fixes.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
set_thread_count 3
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_liberty ../syn/hd_tt_dontuse.lib
read_liberty ${SRAM}_TT_1p8V_25C.lib
read_verilog cortex_syn.v
link_design cortex_board_top
read_sdc cortex.sdc

set DW [expr {[info exists ::env(DW)] ? $::env(DW) : 6450.0}] ; set DH [expr {[info exists ::env(DH)] ? $::env(DH) : 4800.0}]
initialize_floorplan -die_area "0 0 $DW $DH" -core_area "10 10 [expr $DW-10] [expr $DH-10]" -site unithd
make_tracks li1  -x_offset 0.23 -x_pitch 0.46 -y_offset 0.17 -y_pitch 0.34
make_tracks met1 -x_offset 0.17 -x_pitch 0.34 -y_offset 0.17 -y_pitch 0.34
make_tracks met2 -x_offset 0.23 -x_pitch 0.46 -y_offset 0.23 -y_pitch 0.46
make_tracks met3 -x_offset 0.34 -x_pitch 0.68 -y_offset 0.34 -y_pitch 0.68
make_tracks met4 -x_offset 0.46 -x_pitch 0.92 -y_offset 0.46 -y_pitch 0.92
make_tracks met5 -x_offset 1.70 -x_pitch 3.40 -y_offset 1.70 -y_pitch 3.40

# macros: 8 x 8 grid with routing channels between rows (CH, default 150 um) and columns (GX, default 100 um);
# die size DW x DH (defaults 6450 x 4800 um) - all overridable from the environment
set block [ord::get_db_block]
set dbu [$block getDefUnits]
set MW 683.1 ; set MH 416.54
set GX [expr {[info exists ::env(GX)] ? $::env(GX) : 100.0}] ; set CH [expr {[info exists ::env(CH)] ? $::env(CH) : 150.0}]
set LW [expr {[info exists ::env(LW)] ? $::env(LW) : 1100.0}]
set OUT [expr {[info exists ::env(OUT)] ? $::env(OUT) : "floor3"}]
set BLOCK [expr {[info exists ::env(BLOCK)] ? $::env(BLOCK) : 1}]
set i 0
foreach inst [$block getInsts] {
    if {[[$inst getMaster] getName] ne "sky130_sram_2kbyte_1rw1r_32x512_8"} { continue }
    set col [expr $i % 8] ; set row [expr $i / 8]
    set x [expr 80.0 + $col * ($MW + $GX) + ($col >= 4 ? $LW : 0.0)]
    set y [expr $CH + $row * ($MH + $CH)]
    $inst setLocation [expr int($x * $dbu / 10) * 10] [expr int($y * $dbu / 10) * 10]
    $inst setOrient R0
    $inst setPlacementStatus FIRM
    incr i
}
# logic block between the arrays: placement blockages over each macro array (channels included)
set ax1 [expr 80.0 + 4 * ($MW + $GX) - $GX / 2.0] ; set bx0 [expr 80.0 + 4 * ($MW + $GX) + $LW - $GX / 2.0]
if {$BLOCK} {
odb::dbBlockage_create $block 0 0 [expr int($ax1 * $dbu)] [expr int(($DH - 10) * $dbu)]
odb::dbBlockage_create $block [expr int($bx0 * $dbu)] 0 [expr int(($DW - 10) * $dbu)] [expr int(($DH - 10) * $dbu)]
puts "logic block x [expr int($ax1)] .. [expr int($bx0)] um"
}
puts "placed $i SRAM macros"
tapcell -distance 14 -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1 -endcap_master sky130_fd_sc_hd__decap_4 -halo_width_x 6 -halo_width_y 6

add_global_connection -net VDD -pin_pattern {^VPWR$} -power
add_global_connection -net VDD -pin_pattern {^VPB$} -power
add_global_connection -net VDD -pin_pattern {^vccd1$} -power
add_global_connection -net VSS -pin_pattern {^VGND$} -ground
add_global_connection -net VSS -pin_pattern {^VNB$} -ground
add_global_connection -net VSS -pin_pattern {^vssd1$} -ground
set_voltage_domain -name CORE -power VDD -ground VSS
define_pdn_grid -name stdcell_grid -starts_with POWER -voltage_domains CORE -pins "met4 met5"
add_pdn_stripe -grid stdcell_grid -layer met1 -width 0.48 -followpins
add_pdn_stripe -grid stdcell_grid -layer met4 -width 1.6 -pitch 56.0 -offset 2 -starts_with POWER
add_pdn_stripe -grid stdcell_grid -layer met5 -width 1.6 -pitch 56.0 -offset 2 -starts_with POWER
add_pdn_connect -grid stdcell_grid -layers "met1 met4"
add_pdn_connect -grid stdcell_grid -layers "met4 met5"
set PH [expr {[info exists ::env(PDN_HALO)] ? $::env(PDN_HALO) : 20.0}]
define_pdn_grid -macro -name macro -cells sky130_sram_2kbyte_1rw1r_32x512_8 -starts_with POWER -halo "$PH $PH"
add_pdn_connect -grid macro -layers "met4 met5"
pdngen

place_pins -hor_layers met3 -ver_layers met2 -min_distance 4
set_wire_rc -signal -layer met2
set_wire_rc -clock -layer met5
set GPD [expr {[info exists ::env(GPD)] ? $::env(GPD) : 0.45}]
global_placement -density $GPD -pad_left 2 -pad_right 2
estimate_parasitics -placement
repair_design
detailed_placement
report_design_area
puts "== after placement + repair_design"
report_wns
report_tns

# clock-tree settings can be overridden: CTS_ROOT, CTS_BUFS (space-separated), CTS_CLUSTER (sinks per cluster)
set cts_root [expr {[info exists ::env(CTS_ROOT)] ? $::env(CTS_ROOT) : "sky130_fd_sc_hd__clkbuf_16"}]
set cts_bufs [expr {[info exists ::env(CTS_BUFS)] ? $::env(CTS_BUFS) : "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"}]
if {[info exists ::env(CTS_CLUSTER)]} {
  clock_tree_synthesis -root_buf $cts_root -buf_list $cts_bufs -sink_clustering_enable -sink_clustering_size $::env(CTS_CLUSTER) -sink_clustering_max_diameter 100
} else {
  clock_tree_synthesis -root_buf $cts_root -buf_list $cts_bufs -sink_clustering_enable
}
set_propagated_clock [all_clocks]
estimate_parasitics -placement
repair_clock_nets
repair_timing -setup
repair_timing -hold -slack_margin 0.1
detailed_placement
write_db $OUT/cortex_cts.odb
if {[info exists ::env(SKIPGR)]} { puts "clock tree done, global routing skipped (SKIPGR)"; exit }

set_routing_layers -signal met1-met5 -clock met3-met5
foreach l {met1 met2 met3 met4 met5} { set_global_routing_layer_adjustment $l 0.3 }
set_macro_extension 2
global_route -guide_file $OUT/route.guide -congestion_iterations 100 -allow_congestion
estimate_parasitics -global_routing
report_checks -path_delay max -format full_clock_expanded
report_checks -path_delay min
report_wns
report_tns
report_worst_slack -max
report_worst_slack -min
report_design_area
set_power_activity -global -activity 0.1
report_power
write_db $OUT/cortex_groute.odb
puts "SPARK Cortex estimate flow done (floor3)"
