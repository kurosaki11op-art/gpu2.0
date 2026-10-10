#!/bin/sh
M=../../../train/out_qat_sp0.05/spark_v0_model.npz
cfg="+sparse=1 +recall=1 +conf_th=0 +rmode=2 +arb_th=128 +adapt=1 +exit=1 +exit_th=2"
for v in 0 1; do (cd p$v && vvp -n ../gl_p$v.vvp $cfg +thr=1 +n=6 > run.log 2>&1 && echo "power-up $v:" && python3 chk_v2.py "$cfg" $M) & done; wait
