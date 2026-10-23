# End-to-end power of the L Cortex core + encoder in two phases, from the routed layout (gated clocks), SKY130 typical corner.
# PHASE=enc : encoder clock gates enabled every cycle, SRAM read/write gates idle (1 in 1000)
# PHASE=dec : core decision: encoder gates idle (1 in 1000), SRAM read gates 1 in 9 (each array reads 1 of 9 banks), write gates 1 in 1000
# ACT = global switching activity (guess bracket until measured), CLK period from cortex.sdc (20 ns = 50 MHz)
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
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
estimate_parasitics -placement
set icg [get_cells -filter "ref_name == sky130_fd_sc_hd__dlclkp_1" *]
set_power_activity -global -activity $::env(ACT)
set k 0; set ne 0; set nr 0; set nw 0
foreach c $icg {
  set n [get_full_name $c]
  if {[string match "*u_enc*" $n]} {
    # measured in the RTL simulation of real MNIST images (encode window of 21,378 cycles): ck_bmap pulses in 3.67% of cycles (1 in 27),
    # ck_cmap in 2.44% (1 in 41), ck_pix and ck_tm in none; pixel loading (784 cycles) runs g_pix every cycle
    set d 1000
    if {$::env(PHASE) eq "enc"} { if {[string match "*g_bmap*" $n]} { set d 27 } elseif {[string match "*g_cmap*" $n]} { set d 41 } }
    if {$::env(PHASE) eq "load" && [string match "*g_pix*" $n]} { set d 1 }
    incr ne
  } elseif {[regexp {\.g1\.} $n]} { set d [expr {$::env(PHASE) eq "dec" ? 9 : 1000}]; incr nr
  } else { set d 1000; incr nw }
  create_generated_clock -name gck$k -source [get_ports clk] -divide_by $d [get_pins $n/GCLK]
  incr k
}
puts "ICGs: encoder $ne, sram-read $nr, other $nw"
set_propagated_clock [all_clocks]
puts "== PHASE $::env(PHASE) ACT $::env(ACT)"
report_power
