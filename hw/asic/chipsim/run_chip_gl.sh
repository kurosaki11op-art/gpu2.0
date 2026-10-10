#!/bin/sh
for v in 0 1; do (cd gl$v && vvp -n ../chip_gl_p$v.vvp +n=6 > run.log 2>&1; echo "power-up $v:"; grep -E "PASS|FAIL|ERROR|words written" run.log | head -9; python3 chk_chip.py ../../../train/out_qat_sp0.05/spark_v0_model.npz 0 128) > gl$v/result.txt 2>&1 & done; wait; cat gl0/result.txt gl1/result.txt
