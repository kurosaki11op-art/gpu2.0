#!/bin/sh
# Build the SPARK Cortex Tang Nano 20K bitstream (open-source flow). Needs nextpnr-himbaechel with the GW2A-18C chipdb
# (NEXTPNR env var, default /tmp/nextpnr/build/nextpnr-himbaechel) and apycula's gowin_pack.
set -e
NEXTPNR=${NEXTPNR:-/tmp/nextpnr/build/nextpnr-himbaechel}
yosys -q -l synth.log -p "read_verilog ../rtl/cortex/cortex_core.v ../rtl/cortex/cortex_encoder.v ../board/uart_rx.v ../board/uart_tx.v ../board/cortex_board_top.v; synth_gowin -top cortex_board_top -json cortex.json; tee -o stat.txt stat"
$NEXTPNR --json cortex.json --write cortex_pnr.json --device GW2AR-LV18QN88C8/I7 \
  --vopt family=GW2A-18C --vopt cst=../board/tangnano20k.cst --freq 27 -l pnr.log > /dev/null 2>&1
gowin_pack -d GW2A-18C -o cortex_tangnano20k.fs cortex_pnr.json
gzip -kf cortex_tangnano20k.fs
grep -i "max frequency" pnr.log | tail -2
