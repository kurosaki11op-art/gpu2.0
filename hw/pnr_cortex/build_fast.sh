#!/bin/sh
# Optional fast-UART variant (921,600 baud) of the SPARK Cortex bitstream. Use it only if the board's BL616 bridge
# answers the ping at this rate; otherwise use cortex_tangnano20k.fs.gz (115,200 baud).
set -e
NEXTPNR=${NEXTPNR:-/tmp/nextpnr/build/nextpnr-himbaechel}
yosys -q -l synth_fast.log -p "read_verilog -DFAST_UART ../rtl/cortex/cortex_core.v ../rtl/cortex/cortex_encoder.v ../board/uart_rx.v ../board/uart_tx.v ../board/cortex_board_top.v; synth_gowin -top cortex_board_top -json cortex_fast.json"
$NEXTPNR --json cortex_fast.json --write cortex_fast_pnr.json --device GW2AR-LV18QN88C8/I7 \
  --vopt family=GW2A-18C --vopt cst=../board/tangnano20k.cst --freq 27 -l pnr_fast.log > /dev/null 2>&1
gowin_pack -d GW2A-18C -o cortex_tangnano20k_921600.fs cortex_fast_pnr.json
gzip -kf cortex_tangnano20k_921600.fs
grep -i "max frequency" pnr_fast.log | tail -1
