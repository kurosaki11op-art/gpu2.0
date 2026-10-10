#!/bin/sh
# Rebuild the trained Tang Nano 20K bitstream (model: out_qat_sp0.05, RTL with recall effort modes).
set -e
yosys -q -l synth2.log synth_board2.ys
/tmp/nextpnr/build/nextpnr-himbaechel --json board2.json --write pnr2.json --device GW2AR-LV18QN88C8/I7 \
  --vopt family=GW2A-18C --vopt cst=../board/tangnano20k.cst --freq 27 -l pnr2.log > /dev/null 2>&1
gowin_pack -d GW2A-18C -o spark_tangnano20k_trained.fs pnr2.json
gzip -f spark_tangnano20k_trained.fs
grep -i "max frequency" pnr2.log | tail -2
