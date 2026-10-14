# Cell mix of the clock-tree database: flip-flops, clock-tree buffers, other buffers, logic.
set PDK /opt/eda_pdk/share/pdk/sky130A/libs.ref
set SRAM /opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8
read_lef $PDK/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $PDK/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef $SRAM.lef
read_db cortex_cts.odb
array set n {}
foreach inst [[ord::get_db_block] getInsts] {
  set m [[$inst getMaster] getName]
  if {[regexp {__(df|edf|sdf|dl)} $m]} { set k flipflop } elseif {[regexp {clkbuf|clkinv} $m]} { set k clockbuf
  } elseif {[regexp {__buf|__inv|dlygate|clkdly} $m]} { set k buffer } elseif {[regexp {sram} $m]} { set k sram
  } elseif {[regexp {tap|fill|decap} $m]} { set k physical } else { set k logic }
  if {[info exists n($k)]} { incr n($k) } else { set n($k) 1 }
}
foreach k [lsort [array names n]] { puts "$k $n($k)" }
