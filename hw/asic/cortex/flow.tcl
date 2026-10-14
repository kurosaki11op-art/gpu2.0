# SPARK Cortex on SkyWater SKY130 (sky130_fd_sc_hd + 63 OpenRAM 2 KB SRAM macros), OpenROAD estimate flow:
# floorplan -> macro placement -> power grid -> placement + fanout repair -> clock tree -> timing repair ->
# global routing -> timing and power with global-route parasitics. No detailed routing (an estimate, not sign-off).
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

set DW 6450.0 ; set DH 4800.0
initialize_floorplan -die_area "0 0 $DW $DH" -core_area "10 10 [expr $DW-10] [expr $DH-10]" -site unithd
make_tracks li1  -x_offset 0.23 -x_pitch 0.46 -y_offset 0.17 -y_pitch 0.34
make_tracks met1 -x_offset 0.17 -x_pitch 0.34 -y_offset 0.17 -y_pitch 0.34
make_tracks met2 -x_offset 0.23 -x_pitch 0.46 -y_offset 0.23 -y_pitch 0.46
make_tracks met3 -x_offset 0.34 -x_pitch 0.68 -y_offset 0.34 -y_pitch 0.68
make_tracks met4 -x_offset 0.46 -x_pitch 0.92 -y_offset 0.46 -y_pitch 0.92
make_tracks met5 -x_offset 1.70 -x_pitch 3.40 -y_offset 1.70 -y_pitch 3.40

# macros: 8 x 8 grid with 150 um routing channels between rows
set block [ord::get_db_block]
set dbu [$block getDefUnits]
set MW 683.1 ; set MH 416.54 ; set GX 100.0 ; set CH 150.0
set i 0
foreach inst [$block getInsts] {
    if {[[$inst getMaster] getName] ne "sky130_sram_2kbyte_1rw1r_32x512_8"} { continue }
    set col [expr $i % 8] ; set row [expr $i / 8]
    set x [expr 80.0 + $col * ($MW + $GX)]
    set y [expr $CH + $row * ($MH + $CH)]
    $inst setLocation [expr int($x * $dbu / 10) * 10] [expr int($y * $dbu / 10) * 10]
    $inst setOrient R0
    $inst setPlacementStatus FIRM
    incr i
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
define_pdn_grid -macro -name macro -cells sky130_sram_2kbyte_1rw1r_32x512_8 -starts_with POWER -halo "6.0 6.0"
add_pdn_connect -grid macro -layers "met4 met5"
pdngen

place_pins -hor_layers met3 -ver_layers met2 -min_distance 4
set_wire_rc -signal -layer met2
set_wire_rc -clock -layer met5
global_placement -density 0.45 -pad_left 2 -pad_right 2
estimate_parasitics -placement
repair_design
detailed_placement
report_design_area
puts "== after placement + repair_design"
report_wns
report_tns

clock_tree_synthesis -root_buf sky130_fd_sc_hd__clkbuf_16 -buf_list {sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8} -sink_clustering_enable
set_propagated_clock [all_clocks]
estimate_parasitics -placement
repair_clock_nets
repair_timing -setup
repair_timing -hold -slack_margin 0.1
detailed_placement
write_db cortex_cts.odb

set_routing_layers -signal met1-met5 -clock met1-met5
global_route -congestion_iterations 30 -allow_congestion
estimate_parasitics -global_routing
report_checks -path_delay max -format full_clock_expanded > timing_setup.rpt
report_checks -path_delay min > timing_hold.rpt
report_wns > timing_summary.rpt
report_tns >> timing_summary.rpt
report_worst_slack -max >> timing_summary.rpt
report_worst_slack -min >> timing_summary.rpt
report_design_area > area.rpt
set_power_activity -global -activity 0.1
report_power > power.rpt
puts "SPARK Cortex estimate flow done"
