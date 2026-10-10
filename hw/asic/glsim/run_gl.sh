#!/bin/sh
# gate-level (synthesized sky130 netlist + SRAM models) vs golden model
M=../../train/out_qat_sp0.05/spark_v0_model.npz
cfg="+sparse=1 +recall=1 +conf_th=0 +rmode=2 +arb_th=128 +adapt=1 +exit=1 +exit_th=2"
vvp -n gl.vvp $cfg +thr=1 +n=6 > gl_run.log 2>&1
python3 chk_v2.py "$cfg" $M
