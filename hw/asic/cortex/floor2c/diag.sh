#!/bin/sh
# One detailed-routing pass of floor2c/cortex_groute.odb (guide floor2c/route.guide), met1-met5, or_seed 42, writing the
# violation report floor2c/route_drc_pass1.rpt; then diag/drc_summary.py. Lost in a container restart at 60% of pass 1
# of the 30-pass run (116k violations at 60%); this gets the report.
cd "$(dirname "$0")/.."
cat > floor2c/diag_pass1.tcl <<'TCL'
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
TCL
timeout 7000 /opt/eda_or/bin/openroad -no_init -exit floor2c/diag_pass1.tcl > floor2c/diag.log 2>&1
python3 diag/drc_summary.py floor2c/route_drc_pass1.rpt diag/macro_locs.txt > floor2c/drc_summary.txt 2>&1
echo "diag finished" >> floor2c/diag.log
