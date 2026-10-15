#!/bin/sh
# cochlea alone, then the sound encoder alone (stat with the SKY130 liberty)
LIB=/opt/eda_pdk/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
yosys -q -l synth_cochlea.log -p "read_verilog -I../../rtl/cortex ../../rtl/cortex/cortex_cochlea.v; synth -top cortex_cochlea -flatten; memory_map; opt; dfflibmap -liberty ../syn/hd_tt_dontuse.lib; abc -liberty ../syn/hd_tt_dontuse.lib; opt_clean; tee -o stat_cochlea.txt stat -liberty $LIB"
yosys -q -l synth_encoder.log -p "read_verilog ../../rtl/cortex/cortex_encoder_gen.v; chparam -set NCH 10 -set F 64 -set LF 6 -set THR 80'h0808E6C8AA8C6E503214 -set KIND 20'h90000 cortex_encoder_gen; synth -top cortex_encoder_gen -flatten; memory_map; opt; dfflibmap -liberty ../syn/hd_tt_dontuse.lib; abc -liberty ../syn/hd_tt_dontuse.lib; opt_clean; tee -o stat_encoder.txt stat -liberty $LIB"
grep -h "Chip area" stat_cochlea.txt stat_encoder.txt
