# Power sensitivity on the clock-tree database (placement parasitics). ACT=global (default): 10% on every net, as in
# resume.tcl; ACT=<a>: activity a only at the inputs, propagated by OpenSTA through the logic and registers.
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
set ACT [expr {[info exists ::env(ACT)] ? $::env(ACT) : "global"}]
if {$ACT == "global"} {
  puts "== global 0.1 on every net"
  set_power_activity -global -activity 0.1
} else {
  puts "== inputs $ACT, propagated by OpenSTA"
  set_power_activity -input -activity $ACT
}
report_power
