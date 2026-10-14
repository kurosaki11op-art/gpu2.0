# Power of the clock-gated build when the gated clocks are told how often they run (OpenSTA otherwise assumes every
# gated clock toggles like the main clock; pin activities on clock nets are ignored). GATED=N models each of the four
# gated clocks as a generated clock running 1 cycle in N.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
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
estimate_parasitics -placement
set icg [get_cells -filter "ref_name == sky130_fd_sc_hd__dlclkp_1" *]
puts "ICG cells: [llength $icg]"
set_power_activity -global -activity 0.1
puts "== gated clocks as the main clock"
report_power
set g $::env(GATED)
set k 0
set rdiv [expr {[info exists ::env(READDIV)] ? $::env(READDIV) : $g}]
foreach c $icg {
  # SRAM read-port gates (".g1.") run when their bank is read: 1 cycle in READDIV (9 banks share each array's reads);
  # write-port and encoder gates run 1 cycle in GATED
  set d [expr {[regexp {\.g1\.} [get_full_name $c]] ? $rdiv : $g}]
  create_generated_clock -name gck$k -source [get_ports clk] -divide_by $d [get_pins [get_full_name $c]/GCLK]
  incr k
}
set_propagated_clock [all_clocks]
puts "== gated clocks modelled as running 1 cycle in $g (SRAM read ports: 1 in $rdiv)"
report_power
if {[info exists ::env(BREAKDOWN)]} {
  set f [open power_cells.txt w]
  foreach c [get_cells *] { puts $f "[get_full_name $c] [get_property $c ref_name]" }
  close $f
  report_power -instances [get_cells *] > power_instances.txt
}
