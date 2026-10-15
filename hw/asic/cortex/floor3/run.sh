#!/bin/sh
# Floorplan redesign (floor3, 15 Oct 2026): the 63 SRAM macros in two 4-column arrays with the logic in one block
# between them (placement blockages over the arrays), power grid 20 um from the macros, router guide and layer
# adjustment, then detailed routing with signals on met1-met5 only (no li1), or_seed 42, up to 64 passes.
cd "$(dirname "$0")/.."
DW=7800 DH=4800 GX=150 CH=150 LW=1100 PDN_HALO=20 \
  CTS_ROOT=sky130_fd_sc_hd__clkbuf_8 CTS_BUFS="sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4" CTS_CLUSTER=30 \
  timeout 9000 /opt/eda_or/bin/openroad -no_init -exit flow3.tcl > floor3/flow.log 2>&1
[ -f floor3/cortex_groute.odb ] || { echo "flow failed" >> floor3/flow.log; exit 1; }
timeout 60000 /opt/eda_or/bin/openroad -no_init -exit route3.tcl > floor3/route.log 2>&1
echo "run.sh finished" >> floor3/route.log
