#!/bin/sh
# Rebuild the chip netlist and run the pin-level checks against the golden model:
#   RTL (20 tokens) and gate-level with flip-flops powering up as 0 and as 1 (6 tokens each).
set -e
M=../../train/out_qat_sp0.05/spark_v0_model.npz
V=/opt/eda_pdk/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/verilog
(cd ../syn_chip && yosys -q -l synth_sim.log synth_sim.ys)
iverilog -g2012 -o chip_rtl.vvp ../../rtl/spark_core.v ../../rtl/spark_chip.v ../../board/uart_rx.v ../../board/uart_tx.v \
  ../spark_mem_sky130.v ../spark_ram_asic.v ../models/sky130_sram_2kbyte_1rw1r_32x512_8.v tb_chip_rtl.v 2>&1 | grep -iv warn || true
mkdir -p gl0 gl1
for v in 0 1; do
  iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 "-DPWRUP=1'b$v" -o chip_gl_p$v.vvp ../glsim/primitives_pwrup.v $V/sky130_fd_sc_hd.v \
    ../models/sky130_sram_2kbyte_1rw1r_32x512_8.v ../syn_chip/spark_chip_syn_sim.v tb_chip_gl.v 2>&1 | grep -iv warn || true
done
(vvp -n chip_rtl.vvp +n=20 > chip_rtl.log 2>&1; python3 chk_chip.py $M 0 128 >> chip_rtl.log 2>&1) &
sh run_chip_gl.sh > chip_gl.log 2>&1
wait
cat chip_rtl.log | grep -E "PASS|FAIL|ERROR|mismatch"; cat chip_gl.log
