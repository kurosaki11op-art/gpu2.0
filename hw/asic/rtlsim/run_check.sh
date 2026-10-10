#!/bin/sh
# SRAM-macro RTL simulation vs the golden model (weights loaded through the ld_* port)
M=../../train/out_qat_sp0.05/spark_v0_model.npz
for cfg in "+sparse=1 +recall=1 +conf_th=0 +rmode=2 +arb_th=128 +adapt=1 +exit=1 +exit_th=2" "+sparse=1"; do
  vvp -n asic.vvp $cfg +thr=1 +n=20 | grep -v "^$" | tail -1
  python3 chk_v2.py "$cfg" $M | tail -2
done
